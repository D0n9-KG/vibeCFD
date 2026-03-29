import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_artifact_store_resolves_and_loads_json_payloads(tmp_path):
    artifact_store = importlib.import_module("deerflow.domain.submarine.artifact_store")

    outputs_dir = tmp_path / "outputs"
    virtual_path = (
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json"
    )
    artifact_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "demo" / "study-manifest.json"
    )
    _write_json(
        artifact_path,
        {
            "selected_case_id": "demo-case",
            "study_execution_status": "completed",
        },
    )

    resolved = artifact_store.resolve_outputs_artifact(outputs_dir, virtual_path)
    loaded = artifact_store.load_json_outputs_artifact(outputs_dir, virtual_path)
    first = artifact_store.load_first_json_payload_from_artifacts(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=[virtual_path],
        suffixes=["study-manifest.json"],
    )

    assert resolved == artifact_path
    assert loaded == {
        "selected_case_id": "demo-case",
        "study_execution_status": "completed",
    }
    assert first == (
        virtual_path,
        {
            "selected_case_id": "demo-case",
            "study_execution_status": "completed",
        },
    )


def test_artifact_store_skips_unreadable_or_irrelevant_artifacts(tmp_path):
    artifact_store = importlib.import_module("deerflow.domain.submarine.artifact_store")

    outputs_dir = tmp_path / "outputs"
    run_dir = outputs_dir / "submarine" / "solver-dispatch" / "demo"
    run_dir.mkdir(parents=True, exist_ok=True)

    unreadable_virtual_path = (
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/verification-mesh-independence.json"
    )
    unreadable_path = run_dir / "verification-mesh-independence.json"
    unreadable_path.write_text("{not-json", encoding="utf-8")

    readable_virtual_path = (
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/verification-domain-sensitivity.json"
    )
    _write_json(
        run_dir / "verification-domain-sensitivity.json",
        {
            "study_type": "domain_sensitivity",
            "status": "passed",
        },
    )

    payloads = artifact_store.load_json_payloads_from_artifacts(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=[
            "/mnt/user-data/uploads/not-an-output.json",
            unreadable_virtual_path,
            readable_virtual_path,
        ],
        suffixes=[
            "verification-mesh-independence.json",
            "verification-domain-sensitivity.json",
        ],
    )

    assert payloads == [
        (
            readable_virtual_path,
            {
                "study_type": "domain_sensitivity",
                "status": "passed",
            },
        )
    ]
