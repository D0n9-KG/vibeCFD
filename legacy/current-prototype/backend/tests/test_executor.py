from pathlib import Path

from app.models import RunStatus, TaskSubmission
from app.services.cases import CaseLibrary
from app.services.executor import MockExecutionEngine
from app.services.runs import RunService
from app.services.workflow import WorkflowService
from app.store import RunStore


def test_executor_creates_expected_artifacts(temp_workspace: Path) -> None:
    run_store = RunStore()
    run_service = RunService(store=run_store)
    case_library = CaseLibrary()
    workflow_service = WorkflowService(case_library=case_library, store=run_store)
    executor = MockExecutionEngine(store=run_store)

    task = TaskSubmission(
        task_description="Compute drag and pressure for uploaded hull.",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
        operating_notes="Deeply submerged.",
        geometry_file_name="suboff.stl",
    )
    run = run_service.create_run(task, None)
    workflow_service.prepare_run(run.run_id)
    run_store.confirm_run(run.run_id, "Approved")
    run_store.claim_next_queued_run()

    final_run = executor.run_pipeline(run.run_id)
    run_path = Path(final_run.run_directory)

    assert final_run.status == RunStatus.COMPLETED
    assert (run_path / "execution" / "logs" / "run.log").is_file()
    assert (run_path / "postprocess" / "images" / "pressure_distribution.svg").is_file()
    assert (run_path / "postprocess" / "tables" / "drag.csv").is_file()
    assert (run_path / "postprocess" / "result.json").is_file()
    assert (run_path / "report" / "final_report.md").is_file()
    assert (run_path / "report" / "artifact_manifest.json").is_file()
