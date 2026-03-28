from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Protocol

import httpx

from ..config import get_settings
from ..executor_protocol import ExecutorTaskContext, ExecutorTaskRequest, ExecutorTaskResult
from ..models import RunStatus, RunSummary
from ..store import RunStore


class ClaudeExecutorClient(Protocol):
    def execute(self, request: ExecutorTaskRequest) -> ExecutorTaskResult:
        ...


class HttpClaudeExecutorClient:
    def __init__(self, *, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def execute(self, request: ExecutorTaskRequest) -> ExecutorTaskResult:
        response = httpx.post(
            f"{self.base_url}/api/execute",
            json=request.model_dump(mode="json"),
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return ExecutorTaskResult.model_validate(response.json())


class ClaudeExecutorEngine:
    engine_name = "agent_executor"

    def __init__(
        self,
        *,
        store: RunStore,
        client: ClaudeExecutorClient | None = None,
    ) -> None:
        self.store = store
        self.settings = get_settings()
        self.client = client or HttpClaudeExecutorClient(
            base_url=self.settings.executor_base_url,
            timeout_seconds=self.settings.executor_timeout_seconds,
        )

    def launch(self, run_id: str) -> None:
        thread = threading.Thread(target=self.run_pipeline, args=(run_id,), daemon=True)
        thread.start()

    def _build_request(self, run: RunSummary) -> ExecutorTaskRequest:
        run_path = Path(run.run_directory)
        uploaded_dir = run_path / "request" / "uploaded_files"
        input_files = []
        if uploaded_dir.exists():
            input_files = [
                file_path.relative_to(run_path).as_posix()
                for file_path in uploaded_dir.rglob("*")
                if file_path.is_file()
            ]

        workflow_draft = run.workflow_draft
        selected_case = run.selected_case
        return ExecutorTaskRequest(
            job_id=f"job_{run.run_id}",
            run_id=run.run_id,
            stage="execution",
            goal="Execute the approved submarine CFD workflow in a controlled environment and return structured outputs.",
            run_directory=str(run_path),
            allowed_tools=workflow_draft.allowed_tools if workflow_draft else [],
            required_artifacts=workflow_draft.required_artifacts if workflow_draft else [],
            input_files=input_files,
            context=ExecutorTaskContext(
                task_description=run.request.task_description,
                task_type=run.request.task_type,
                geometry_family=selected_case.geometry_family
                if selected_case is not None
                else run.request.geometry_family_hint,
                selected_case_id=selected_case.case_id if selected_case is not None else None,
                selected_case_title=selected_case.title if selected_case is not None else None,
                reviewer_notes=run.reviewer_notes or "",
                operating_notes=run.request.operating_notes,
                workflow_summary=workflow_draft.summary if workflow_draft else "",
                workflow_assumptions=workflow_draft.assumptions if workflow_draft else [],
                linked_skills=workflow_draft.linked_skills if workflow_draft else [],
                selected_case_geometry_description=selected_case.geometry_description
                if selected_case is not None
                else "",
                selected_case_reuse_role=selected_case.reuse_role if selected_case is not None else "",
            ),
        )

    def _write_request_manifest(self, request: ExecutorTaskRequest) -> None:
        request_path = Path(request.run_directory) / "execution" / "agent_executor" / "request.json"
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(
            json.dumps(request.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _append_result_timeline(self, run_id: str, result: ExecutorTaskResult) -> None:
        for event in result.timeline:
            self.store.append_timeline(run_id, event.stage, event.message, event.status)

    def run_pipeline(self, run_id: str):
        run = self.store.get_run(run_id)
        if run.status not in {RunStatus.RUNNING, RunStatus.AWAITING_CONFIRMATION}:
            raise RuntimeError(f"Run {run_id} is not ready for execution.")

        request = self._build_request(run)
        self._write_request_manifest(request)
        self.store.append_timeline(
            run_id,
            "execution",
            "Dispatch structured execution task to the agent executor.",
            "running",
        )
        self.store.set_stage(run_id, "execution", "Running via Agent Executor")

        try:
            result = self.client.execute(request)
        except Exception as exc:
            return self.store.fail_run_with_metadata(
                run_id,
                f"claude-executor request failed: {exc}",
                summary="claude-executor request could not be completed.",
                failure_category="executor_request_failed",
                failure_source="claude_executor_client",
            )

        self._append_result_timeline(run_id, result)
        if result.status == "failed":
            return self.store.fail_run_with_metadata(
                run_id,
                result.error_message or result.summary or "claude-executor reported a failure.",
                summary=result.summary or "claude-executor reported a failure.",
                failure_category="executor_reported_failure",
                failure_source="claude_executor",
            )

        self.store.append_timeline(run_id, "completed", result.summary, "ok")
        return self.store.complete_run(
            run_id,
            artifacts=result.artifacts,
            report_markdown=result.report_markdown or "",
            metrics=result.metrics,
        )
