from pathlib import Path
import time

from app.dispatcher import ExecutionDispatcher
from app.models import TaskSubmission
from app.orchestration.service import WorkflowOrchestrator
from app.services.cases import CaseLibrary
from app.services.runs import RunService
from app.store import RunStore


class LaunchTrackingEngine:
    engine_name = "launch-tracking"

    def __init__(self) -> None:
        self.launched_run_ids: list[str] = []

    def launch(self, run_id: str) -> None:
        self.launched_run_ids.append(run_id)

    def run_pipeline(self, run_id: str):  # pragma: no cover - should not be called
        raise AssertionError("run_pipeline should not be called in this test")


def test_dispatcher_does_not_launch_cancelled_queued_runs(
    monkeypatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "mock")

    store = RunStore()
    case_library = CaseLibrary()
    run_service = RunService(store=store)
    engine = LaunchTrackingEngine()
    orchestrator = WorkflowOrchestrator(
        store=store,
        case_library=case_library,
        execution_engine=engine,
    )

    task = TaskSubmission(
        task_description="Cancel this queued run before the dispatcher claims it.",
        task_type="wake_field",
        geometry_family_hint="Joubert BB2",
        operating_notes="Cancellation test.",
    )
    run = run_service.create_run(task, None)
    orchestrator.prepare_run(run.run_id)
    orchestrator.execute_run(run.run_id, "Queue it first")

    cancelled = store.cancel_queued_run(run.run_id, "User cancelled before dispatch.")
    assert cancelled.status.value == "cancelled"

    dispatcher = ExecutionDispatcher(
        store=store,
        execution_engine=engine,
        poll_interval_seconds=0.01,
    )
    dispatcher.start()
    try:
        time.sleep(0.08)
    finally:
        dispatcher.stop()

    assert engine.launched_run_ids == []

