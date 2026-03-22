from pathlib import Path
import time

from app.dispatcher import ExecutionDispatcher
from app.execution.factory import create_execution_engine
from app.models import TaskSubmission
from app.orchestration.service import WorkflowOrchestrator
from app.services.cases import CaseLibrary
from app.services.runs import RunService
from app.store import RunStore


class LaunchOnlyEngine:
    engine_name = "launch-only"

    def __init__(self, store: RunStore) -> None:
        self.store = store
        self.launched_run_id: str | None = None

    def launch(self, run_id: str) -> None:
        self.launched_run_id = run_id
        self.store.append_timeline(run_id, "execution", "Execution dispatched asynchronously.", "running")

    def run_pipeline(self, run_id: str):  # pragma: no cover - should not be used
        raise AssertionError("run_pipeline should not be called for dispatch-based execution")


def test_orchestrator_prepare_run_reaches_awaiting_confirmation(
    monkeypatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "mock")

    store = RunStore()
    case_library = CaseLibrary()
    run_service = RunService(store=store)
    orchestrator = WorkflowOrchestrator(
        store=store,
        case_library=case_library,
        execution_engine=create_execution_engine(store),
    )

    task = TaskSubmission(
        task_description="Compute pressure distribution for a benchmark hull.",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
        operating_notes="Deeply submerged benchmark condition.",
    )
    run = run_service.create_run(task, None)

    prepared = orchestrator.prepare_run(run.run_id)

    assert prepared.status.value == "awaiting_confirmation"
    assert prepared.workflow_draft is not None
    assert prepared.selected_case is not None
    assert (Path(prepared.run_directory) / "retrieval" / "workflow_draft.md").is_file()


def test_orchestrator_execute_run_queues_execution_for_dispatcher(
    monkeypatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "mock")

    store = RunStore()
    case_library = CaseLibrary()
    run_service = RunService(store=store)
    engine = LaunchOnlyEngine(store)
    orchestrator = WorkflowOrchestrator(
        store=store,
        case_library=case_library,
        execution_engine=engine,
    )

    task = TaskSubmission(
        task_description="Dispatch execution without blocking request handling.",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
        operating_notes="Deeply submerged benchmark condition.",
        geometry_file_name="suboff.stl",
    )
    run = run_service.create_run(task, None)
    orchestrator.prepare_run(run.run_id)

    queued = orchestrator.execute_run(run.run_id, "Approved for async execution")

    assert queued.status.value == "queued"
    assert engine.launched_run_id is None
    assert queued.timeline[-1].message == "Run queued for background dispatch."


def test_orchestrator_execute_run_completes_with_mock_engine(
    monkeypatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "mock")

    store = RunStore()
    case_library = CaseLibrary()
    run_service = RunService(store=store)
    orchestrator = WorkflowOrchestrator(
        store=store,
        case_library=case_library,
        execution_engine=create_execution_engine(store),
    )

    task = TaskSubmission(
        task_description="Compute drag and pressure.",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
        operating_notes="Deeply submerged benchmark condition.",
        geometry_file_name="suboff.stl",
    )
    run = run_service.create_run(task, None)
    orchestrator.prepare_run(run.run_id)

    queued = orchestrator.execute_run(run.run_id, "Approved for execution")
    run_path = Path(queued.run_directory)
    dispatcher = ExecutionDispatcher(
        store=store,
        execution_engine=create_execution_engine(store),
        poll_interval_seconds=0.01,
    )

    assert queued.status.value == "queued"

    dispatcher.start()
    try:
        for _ in range(40):
            latest = store.get_run(run.run_id)
            if latest.status.value == "completed":
                break
            time.sleep(0.02)
        else:
            raise AssertionError("Mock execution did not complete in time.")
    finally:
        dispatcher.stop()

    assert latest.status.value == "completed"
    assert (run_path / "execution" / "logs" / "run.log").is_file()
    assert (run_path / "postprocess" / "result.json").is_file()
    assert (run_path / "report" / "final_report.md").is_file()
    assert len(latest.timeline) >= 4
