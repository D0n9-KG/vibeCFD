from pathlib import Path

from app.execution.claude_executor_engine import ClaudeExecutorEngine
from app.executor_protocol import ExecutorTaskResult, ExecutorTimelineEvent
from app.models import ArtifactItem, TaskSubmission
from app.services.cases import CaseLibrary
from app.services.runs import RunService
from app.services.workflow import WorkflowService
from app.store import RunStore


class FakeClaudeExecutorClient:
    def __init__(self) -> None:
        self.last_request = None

    def execute(self, request):
        self.last_request = request
        run_dir = Path(request.run_directory)
        (run_dir / "execution" / "logs").mkdir(parents=True, exist_ok=True)
        (run_dir / "postprocess").mkdir(parents=True, exist_ok=True)
        (run_dir / "report").mkdir(parents=True, exist_ok=True)
        (run_dir / "execution" / "logs" / "run.log").write_text(
            "[claude-executor] accepted request\n",
            encoding="utf-8",
        )
        (run_dir / "postprocess" / "result.json").write_text(
            '{"status":"ok"}\n',
            encoding="utf-8",
        )
        (run_dir / "report" / "final_report.md").write_text(
            "# Stub report\n",
            encoding="utf-8",
        )
        return ExecutorTaskResult(
            job_id=request.job_id,
            run_id=request.run_id,
            status="completed",
            summary="Stub executor completed the task.",
            executor_name="fake-claude-executor",
            used_tools=request.allowed_tools[:1],
            metrics={"drag_coefficient": 0.00348},
            timeline=[
                ExecutorTimelineEvent(
                    stage="execution",
                    message="Remote executor accepted the job.",
                    status="running",
                ),
                ExecutorTimelineEvent(
                    stage="report",
                    message="Remote executor generated the final report.",
                    status="ok",
                ),
            ],
            artifacts=[
                ArtifactItem(
                    label="Execution Log",
                    category="log",
                    relative_path="execution/logs/run.log",
                    mime_type="text/plain",
                    url=f"/api/runs/{request.run_id}/artifacts/execution/logs/run.log",
                ),
                ArtifactItem(
                    label="Structured Result",
                    category="json",
                    relative_path="postprocess/result.json",
                    mime_type="application/json",
                    url=f"/api/runs/{request.run_id}/artifacts/postprocess/result.json",
                ),
                ArtifactItem(
                    label="Final Report",
                    category="report",
                    relative_path="report/final_report.md",
                    mime_type="text/markdown",
                    url=f"/api/runs/{request.run_id}/artifacts/report/final_report.md",
                ),
            ],
            report_markdown="# Stub report\n",
        )


def test_claude_executor_engine_builds_request_and_completes_run(
    monkeypatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "claude_executor")

    store = RunStore()
    run_service = RunService(store=store)
    workflow_service = WorkflowService(case_library=CaseLibrary(), store=store)

    task = TaskSubmission(
        task_description="Compute pressure distribution for a benchmark hull.",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
        operating_notes="Deeply submerged benchmark condition.",
        geometry_file_name="suboff.stl",
    )
    run = run_service.create_run(task, None)
    workflow_service.prepare_run(run.run_id)

    client = FakeClaudeExecutorClient()
    engine = ClaudeExecutorEngine(store=store, client=client)
    completed = engine.run_pipeline(run.run_id)

    assert completed.status.value == "completed"
    assert client.last_request is not None
    assert client.last_request.run_id == run.run_id
    assert client.last_request.allowed_tools
    assert (Path(completed.run_directory) / "execution" / "claude_executor" / "request.json").is_file()
    assert (Path(completed.run_directory) / "report" / "final_report.md").is_file()
    assert completed.timeline[-1].stage == "completed"
