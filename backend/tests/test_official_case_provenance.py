import importlib


def test_build_run_provenance_manifest_records_per_file_official_case_sources():
    provenance_module = importlib.import_module("deerflow.domain.submarine.provenance")

    manifest = provenance_module.build_run_provenance_manifest(
        experiment_id="official-case-demo",
        run_id="cavity-baseline",
        task_type="official_openfoam_case",
        geometry_virtual_path="",
        geometry_family=None,
        selected_case_id="cavity",
        requested_outputs=[],
        simulation_requirements={},
        approval_snapshot={"confirmation_status": "confirmed"},
        artifact_entrypoints={"request": "/mnt/user-data/outputs/demo/request.json"},
        environment_fingerprint={"profile_id": "local_cli"},
        environment_parity_assessment={"parity_status": "matched"},
        input_source_type="openfoam_case_seed",
        official_case_id="cavity",
        official_case_seed_virtual_paths=[
            "/mnt/user-data/uploads/cavity/system/blockMeshDict"
        ],
        assembled_case_virtual_paths=[
            "/mnt/user-data/workspace/official-openfoam/cavity-demo/openfoam-case/system/controlDict"
        ],
        file_sources={
            "system/controlDict": {
                "source_commit": "441953dfbb4270dd54e14672e194e4a4a478afc4",
                "source_path": "tutorials/legacy/incompressible/icoFoam/cavity/cavity/system/controlDict",
                "source_kind": "synthesized_from_official_default",
            }
        },
    )

    assert manifest.input_source_type == "openfoam_case_seed"
    assert manifest.official_case_id == "cavity"
    assert manifest.official_case_seed_virtual_paths == [
        "/mnt/user-data/uploads/cavity/system/blockMeshDict"
    ]
    assert manifest.assembled_case_virtual_paths == [
        "/mnt/user-data/workspace/official-openfoam/cavity-demo/openfoam-case/system/controlDict"
    ]
    assert manifest.file_sources["system/controlDict"]["source_commit"] == (
        "441953dfbb4270dd54e14672e194e4a4a478afc4"
    )


def test_official_case_manifest_completeness_requires_case_id_seed_paths_and_file_sources():
    provenance_module = importlib.import_module("deerflow.domain.submarine.provenance")

    completeness = provenance_module.determine_provenance_manifest_completeness(
        {
            "manifest_version": "v1",
            "experiment_id": "official-case-demo",
            "run_id": "baseline",
            "task_type": "official_openfoam_case",
            "input_source_type": "openfoam_case_seed",
            "geometry_virtual_path": "",
            "requested_output_ids": [],
            "simulation_requirements_snapshot": {},
            "approval_snapshot": {"confirmation_status": "confirmed"},
            "artifact_entrypoints": {
                "request": "/mnt/user-data/outputs/demo/request.json",
                "dispatch_summary_markdown": "/mnt/user-data/outputs/demo/dispatch.md",
                "dispatch_summary_html": "/mnt/user-data/outputs/demo/dispatch.html",
            },
            "environment_fingerprint": {"profile_id": "local_cli"},
            "environment_parity_assessment": {"parity_status": "matched"},
            "official_case_id": None,
            "official_case_seed_virtual_paths": [],
            "file_sources": {},
        }
    )

    assert completeness == "partial"
