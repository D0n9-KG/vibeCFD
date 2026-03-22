from pathlib import Path

from fastapi.testclient import TestClient

from app.claude_executor_main import app


def test_claude_executor_stub_returns_structured_completion(temp_workspace: Path) -> None:
    client = TestClient(app)
    run_id = "run_stub_demo"
    run_dir = temp_workspace / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    response = client.post(
        "/api/execute",
        json={
            "job_id": "job_run_stub_demo",
            "run_id": run_id,
            "stage": "execution",
            "goal": "Run the recommended benchmark CFD workflow and write structured outputs.",
            "run_directory": str(run_dir),
            "allowed_tools": ["geometry-check.inspect", "solver-openfoam.run_case"],
            "required_artifacts": [
                "postprocess/result.json",
                "report/final_report.md",
            ],
            "input_files": ["request/uploaded_files/suboff.stl"],
            "context": {
                "task_description": "Compute pressure distribution for SUBOFF.",
                "task_type": "pressure_distribution",
                "geometry_family": "DARPA SUBOFF",
                "selected_case_id": "darpa-suboff-pressure-template",
                "selected_case_title": "DARPA SUBOFF pressure validation",
                "reviewer_notes": "Proceed with the recommended workflow.",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["executor_name"] == "claude-executor-stub"
    assert body["timeline"]
    assert body["artifacts"]
    assert (run_dir / "execution" / "claude_executor" / "request.json").is_file()
    assert (run_dir / "execution" / "claude_executor" / "response.json").is_file()
    assert (run_dir / "postprocess" / "result.json").is_file()
    assert (run_dir / "report" / "final_report.md").is_file()
