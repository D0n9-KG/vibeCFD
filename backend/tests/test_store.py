from datetime import datetime, timezone
from pathlib import Path

from app.models import TaskSubmission
from app.services.runs import RunService
from app.store import RunStore


def test_store_persists_run_state_and_reloads_after_restart(
    monkeypatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "mock")

    store = RunStore()
    service = RunService(store=store)
    task = TaskSubmission(
        task_description="Persist this run across process restarts.",
        task_type="resistance",
        geometry_family_hint="Type 209",
        geometry_file_name="type209.stl",
    )

    run = service.create_run(task, None)
    store.confirm_run(run.run_id, "Approved for persistence test.")
    store.claim_next_queued_run()
    state_file = Path(run.run_directory) / "run_state.json"

    assert state_file.is_file()

    reloaded_store = RunStore()
    reloaded = reloaded_store.get_run(run.run_id)

    assert reloaded.run_id == run.run_id
    assert reloaded.status.value == "failed"
    assert reloaded.current_stage == "failed"
    assert reloaded.timeline
    assert reloaded.timeline[-1].message == "Recovered interrupted run after restart; manual retry is required."


def test_store_persists_structured_run_events_and_reloads_them(
    monkeypatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "mock")

    store = RunStore()
    service = RunService(store=store)
    task = TaskSubmission(
        task_description="Persist structured run events.",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
        geometry_file_name="suboff.stl",
    )

    run = service.create_run(task, None)
    store.append_event(
        run.run_id,
        event_type="workflow_prepared",
        stage="prepare",
        message="Workflow draft was prepared.",
        status=run.status.value,
        details={"source": "test"},
    )
    events_file = Path(run.run_directory) / "events" / "events.jsonl"

    assert events_file.is_file()

    reloaded_store = RunStore()
    events = reloaded_store.list_events(run.run_id)

    assert len(events) >= 2
    assert events[0].event_type == "run_created"
    assert events[-1].event_type == "workflow_prepared"
    assert events[-1].details["source"] == "test"


def test_store_persists_execution_attempts_and_reloads_them(
    monkeypatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "mock")

    store = RunStore()
    service = RunService(store=store)
    task = TaskSubmission(
        task_description="Persist execution attempts.",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
        geometry_file_name="suboff.stl",
    )

    run = service.create_run(task, None)
    started_at = datetime(2026, 3, 21, 8, 0, 0, tzinfo=timezone.utc)
    finished_at = datetime(2026, 3, 21, 8, 0, 3, 500000, tzinfo=timezone.utc)
    moments = iter([started_at, finished_at])
    monkeypatch.setattr("app.store.utcnow", lambda: next(moments))
    store.start_execution_attempt(run.run_id, engine_name="mock")
    store.finish_execution_attempt(
        run.run_id,
        status="completed",
        summary="Attempt finished successfully.",
    )

    reloaded_store = RunStore()
    attempts = reloaded_store.list_attempts(run.run_id)

    assert len(attempts) == 1
    assert attempts[0].attempt_number == 1
    assert attempts[0].engine_name == "mock"
    assert attempts[0].status == "completed"
    assert attempts[0].duration_seconds == 3.5
    assert attempts[0].failure_category is None
    assert attempts[0].failure_source is None


def test_store_marks_recovered_running_attempt_with_restart_failure_taxonomy(
    monkeypatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "mock")

    store = RunStore()
    service = RunService(store=store)
    task = TaskSubmission(
        task_description="Recover a running attempt after restart.",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
        geometry_file_name="suboff.stl",
    )

    run = service.create_run(task, None)
    store.confirm_run(run.run_id, "Queue for restart recovery test.")
    store.claim_next_queued_run()
    store.start_execution_attempt(run.run_id, engine_name="mock")

    reloaded_store = RunStore()
    attempts = reloaded_store.list_attempts(run.run_id)

    assert len(attempts) == 1
    assert attempts[0].status == "failed"
    assert attempts[0].failure_category == "service_restart_interruption"
    assert attempts[0].failure_source == "store_recovery"
    assert attempts[0].duration_seconds is not None
