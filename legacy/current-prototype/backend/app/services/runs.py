from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from ..config import get_settings
from ..models import RunStatus, RunSummary, TaskSubmission
from ..store import RunStore, utcnow


class RunService:
    def __init__(self, store: RunStore | None = None) -> None:
        self.settings = get_settings()
        self.store = store or RunStore()

    def _make_run_id(self) -> str:
        return f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"

    def _prepare_run_tree(self, run_id: str) -> Path:
        run_path = self.settings.runs_dir / run_id
        for relative in (
            "request/uploaded_files",
            "events",
            "attempts",
            "retrieval",
            "execution/solver_case",
            "execution/logs",
            "execution/raw_outputs",
            "postprocess/images",
            "postprocess/models",
            "postprocess/tables",
            "report",
        ):
            (run_path / relative).mkdir(parents=True, exist_ok=True)
        return run_path

    def _copy_uploaded_files(self, source_dir: Path, target_dir: Path) -> None:
        if not source_dir.exists():
            return

        for file_path in source_dir.rglob("*"):
            if not file_path.is_file():
                continue
            relative = file_path.relative_to(source_dir)
            destination = target_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, destination)

    def create_run(self, task: TaskSubmission, uploaded_file_path: Path | None) -> RunSummary:
        run_id = self._make_run_id()
        run_path = self._prepare_run_tree(run_id)

        if uploaded_file_path is not None and uploaded_file_path.exists():
            shutil.copy2(
                uploaded_file_path,
                run_path / "request" / "uploaded_files" / uploaded_file_path.name,
            )

        (run_path / "request" / "task.json").write_text(
            json.dumps(task.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        run = RunSummary(
            run_id=run_id,
            status=RunStatus.DRAFT,
            current_stage="request_received",
            stage_label="Request Received",
            created_at=utcnow(),
            updated_at=utcnow(),
            request=task,
            run_directory=str(run_path),
            timeline=[],
        )
        self.store.add_run(run)
        self.store.append_timeline(run_id, "request", "Run created and written to the run directory.", "ok")
        return self.store.get_run(run_id)

    def retry_run(self, source_run_id: str) -> RunSummary:
        source = self.store.get_run(source_run_id)
        if source.status in {RunStatus.QUEUED, RunStatus.RUNNING}:
            raise ValueError("Cannot retry a run that is still in progress.")

        retried = self.create_run(source.request.model_copy(deep=True), None)
        self._copy_uploaded_files(
            Path(source.run_directory) / "request" / "uploaded_files",
            Path(retried.run_directory) / "request" / "uploaded_files",
        )
        self.store.append_timeline(
            retried.run_id,
            "request",
            f"Run retried from {source_run_id}.",
            "ok",
        )
        self.store.append_event(
            retried.run_id,
            event_type="run_retried",
            stage="request",
            message=f"Run retried from {source_run_id}.",
            status=retried.status.value,
            details={"source_run_id": source_run_id},
        )
        return self.store.get_run(retried.run_id)
