import importlib

from deerflow.agents.thread_state import merge_submarine_runtime


def test_build_runtime_snapshot_accepts_official_case_seed_metadata():
    contracts_module = importlib.import_module("deerflow.domain.submarine.contracts")

    snapshot = contracts_module.build_runtime_snapshot(
        current_stage="solver-dispatch",
        task_summary="Run official cavity seed",
        confirmation_status="confirmed",
        execution_preference="execute_now",
        task_type="official_openfoam_case",
        geometry_virtual_path="",
        geometry_family=None,
        next_recommended_stage="result-reporting",
        report_virtual_path="/mnt/user-data/outputs/submarine/reports/cavity/final-report.md",
        input_source_type="openfoam_case_seed",
        official_case_id="cavity",
        official_case_seed_virtual_paths=[
            "/mnt/user-data/uploads/cavity/system/blockMeshDict"
        ],
        assembled_case_virtual_paths=[
            "/mnt/user-data/workspace/openfoam/cavity/system/controlDict"
        ],
        official_case_profile={
            "source_commit": "441953dfbb4270dd54e14672e194e4a4a478afc4",
            "case_id": "cavity",
        },
    )

    assert snapshot.input_source_type == "openfoam_case_seed"
    assert snapshot.official_case_id == "cavity"
    assert snapshot.official_case_seed_virtual_paths == [
        "/mnt/user-data/uploads/cavity/system/blockMeshDict"
    ]
    assert snapshot.assembled_case_virtual_paths == [
        "/mnt/user-data/workspace/openfoam/cavity/system/controlDict"
    ]
    assert snapshot.official_case_profile is not None
    assert snapshot.official_case_profile.case_id == "cavity"
    assert snapshot.official_case_profile.source_commit == (
        "441953dfbb4270dd54e14672e194e4a4a478afc4"
    )


def test_merge_submarine_runtime_preserves_official_case_seed_metadata():
    existing = {
        "input_source_type": "openfoam_case_seed",
        "official_case_id": "cavity",
        "official_case_seed_virtual_paths": [
            "/mnt/user-data/uploads/cavity/system/blockMeshDict"
        ],
        "assembled_case_virtual_paths": [
            "/mnt/user-data/workspace/openfoam/cavity/system/controlDict"
        ],
        "official_case_profile": {
            "source_commit": "441953dfbb4270dd54e14672e194e4a4a478afc4",
            "case_id": "cavity",
        },
    }
    new = {
        "current_stage": "solver-dispatch",
        "runtime_status": "running",
        "artifact_virtual_paths": [
            "/mnt/user-data/outputs/submarine/reports/cavity/final-report.md"
        ],
    }

    merged = merge_submarine_runtime(existing, new)

    assert merged["input_source_type"] == "openfoam_case_seed"
    assert merged["official_case_id"] == "cavity"
    assert merged["official_case_seed_virtual_paths"] == [
        "/mnt/user-data/uploads/cavity/system/blockMeshDict"
    ]
    assert merged["assembled_case_virtual_paths"] == [
        "/mnt/user-data/workspace/openfoam/cavity/system/controlDict"
    ]
    assert merged["official_case_profile"]["source_commit"] == (
        "441953dfbb4270dd54e14672e194e4a4a478afc4"
    )
