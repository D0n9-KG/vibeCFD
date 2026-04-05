from pathlib import Path

from app.models import TaskSubmission
from app.services.runs import RunService


def test_run_service_creates_expected_layout(temp_workspace: Path) -> None:
    service = RunService()
    task = TaskSubmission(
        task_description="Compute resistance for uploaded hull.",
        task_type="resistance",
        geometry_family_hint="Type 209",
        geometry_file_name="type209.stl",
    )

    run = service.create_run(task, None)
    run_path = Path(run.run_directory)

    assert (run_path / "request").is_dir()
    assert (run_path / "retrieval").is_dir()
    assert (run_path / "execution" / "logs").is_dir()
    assert (run_path / "postprocess" / "images").is_dir()
    assert (run_path / "report").is_dir()
    assert (run_path / "request" / "task.json").is_file()
