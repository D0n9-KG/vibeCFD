from pathlib import Path

from app.models import TaskSubmission
from app.services.cases import CaseLibrary


def test_case_library_returns_relevant_cases(temp_workspace: Path) -> None:
    library = CaseLibrary()
    task = TaskSubmission(
        task_description="Need pressure distribution and drag for a DARPA SUBOFF style hull.",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
        operating_notes="Deeply submerged benchmark condition.",
    )

    result = library.search(task)

    assert result.recommended.case_id.startswith("darpa_suboff")
    assert result.candidates[0].geometry_family == "DARPA SUBOFF"
    assert "pressure_distribution" in result.candidates[0].task_type
    assert result.candidates[0].score >= result.candidates[-1].score
