from pathlib import Path
import time

from app.dispatcher import ExecutionDispatcher
from app.models import TaskSubmission
from app.orchestration.service import WorkflowOrchestrator
from app.services.cases import CaseLibrary
from app.services.runs import RunService
from app.store import RunStore


class ImmediateCompletionEngine:
    engine_name = "immediate-completion"

    def __init__(self, store: RunStore) -> None:
        self.store = store
        self.launched_run_ids: list[str] = []

    def launch(self, run_id: str) -> None:
        self.launched_run_ids.append(run_id)
        self.store.append_timeline(
            run_id,
            "execution",
            "Dispatcher claimed queued run and launched execution.",
            "running",
        )
        self.store.complete_run(
            run_id,
            artifacts=[],
            report_markdown="# Immediate completion\n",
            metrics={"dispatcher_launches": float(len(self.launched_run_ids))},
        )

    def run_pipeline(self, run_id: str):  # pragma: no cover - should not be used
        raise AssertionError("run_pipeline should not be called in dispatcher tests")


class FailingLaunchEngine:
    engine_name = "failing-launch"

    def launch(self, run_id: str) -> None:
        raise RuntimeError("launch failed in dispatcher test")

    def run_pipeline(self, run_id: str):  # pragma: no cover - should not be used
        raise AssertionError("run_pipeline should not be called in dispatcher tests")


def test_dispatcher_claims_queued_runs_and_launches_engine(
    monkeypatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "mock")

    store = RunStore()
    case_library = CaseLibrary()
    run_service = RunService(store=store)
    engine = ImmediateCompletionEngine(store)
    orchestrator = WorkflowOrchestrator(
        store=store,
        case_library=case_library,
        execution_engine=engine,
    )

    task = TaskSubmission(
        task_description="Queue this run and let the dispatcher claim it.",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
        operating_notes="Background queue test.",
    )
    run = run_service.create_run(task, None)
    orchestrator.prepare_run(run.run_id)

    queued = orchestrator.execute_run(run.run_id, "Approved for queued execution")
    assert queued.status.value == "queued"

    dispatcher = ExecutionDispatcher(
        store=store,
        execution_engine=engine,
        poll_interval_seconds=0.01,
    )
    dispatcher.start()
    try:
        for _ in range(40):
            latest = store.get_run(run.run_id)
            if latest.status.value == "completed":
                break
            time.sleep(0.02)
        else:
            raise AssertionError("Queued run was not completed by the dispatcher in time.")
    finally:
        dispatcher.stop()

    assert engine.launched_run_ids == [run.run_id]
    assert latest.timeline[-1].message == "Dispatcher claimed queued run and launched execution."
    attempts = store.list_attempts(run.run_id)
    assert len(attempts) == 1
    assert attempts[0].attempt_number == 1
    assert attempts[0].status == "completed"


def test_dispatcher_records_attempt_failure_metadata_when_launch_fails(
    monkeypatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "mock")

    store = RunStore()
    case_library = CaseLibrary()
    run_service = RunService(store=store)
    engine = FailingLaunchEngine()
    orchestrator = WorkflowOrchestrator(
        store=store,
        case_library=case_library,
        execution_engine=engine,
    )

    task = TaskSubmission(
        task_description="Queue this run and fail it in dispatcher.",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
        operating_notes="Dispatcher failure classification test.",
    )
    run = run_service.create_run(task, None)
    orchestrator.prepare_run(run.run_id)
    queued = orchestrator.execute_run(run.run_id, "Approved for failed dispatch.")
    assert queued.status.value == "queued"

    dispatcher = ExecutionDispatcher(
        store=store,
        execution_engine=engine,
        poll_interval_seconds=0.01,
    )
    dispatcher.start()
    try:
        for _ in range(40):
            latest = store.get_run(run.run_id)
            if latest.status.value == "failed":
                break
            time.sleep(0.02)
        else:
            raise AssertionError("Queued run was not failed by the dispatcher in time.")
    finally:
        dispatcher.stop()

    attempts = store.list_attempts(run.run_id)
    assert len(attempts) == 1
    assert attempts[0].status == "failed"
    assert attempts[0].failure_category == "dispatch_launch_error"
    assert attempts[0].failure_source == "dispatcher"
    assert attempts[0].error_message == "Execution dispatch failed: launch failed in dispatcher test"
