import importlib
from pathlib import Path


def test_build_official_case_validation_marks_cavity_as_matched_when_metrics_hit_pinned_baseline(
    tmp_path: Path,
):
    validation_module = importlib.import_module(
        "deerflow.domain.submarine.official_case_validation"
    )

    case_dir = tmp_path / "cavity"
    (case_dir / "system").mkdir(parents=True, exist_ok=True)
    (case_dir / "system" / "controlDict").write_text(
        "\n".join(
            [
                "application     icoFoam;",
                "endTime         0.5;",
                "deltaT          0.005;",
            ]
        ),
        encoding="utf-8",
    )
    (case_dir / "system" / "fvSolution").write_text(
        "\n".join(["pFinal", "PISO"]),
        encoding="utf-8",
    )

    assessment = validation_module.build_official_case_validation_assessment(
        case_id="cavity",
        solver_results={
            "solver_completed": True,
            "final_time_seconds": 0.5,
            "mesh_summary": {"cells": 400},
        },
        assembled_case_dir=case_dir,
    )

    assert assessment["parity_status"] == "matched"
    assert not assessment["drift_reasons"]
    assert assessment["observed_metrics"]["final_time_seconds"] == 0.5
    assert assessment["observed_metrics"]["mesh_cells"] == 400


def test_build_official_case_validation_marks_pitzdaily_as_drifted_when_steady_defaults_are_missing(
    tmp_path: Path,
):
    validation_module = importlib.import_module(
        "deerflow.domain.submarine.official_case_validation"
    )

    case_dir = tmp_path / "pitzDaily"
    (case_dir / "system").mkdir(parents=True, exist_ok=True)
    (case_dir / "constant").mkdir(parents=True, exist_ok=True)
    (case_dir / "system" / "controlDict").write_text(
        "\n".join(
            [
                "solver          incompressibleFluid;",
                "endTime         0.5;",
                "deltaT          0.005;",
            ]
        ),
        encoding="utf-8",
    )
    (case_dir / "constant" / "momentumTransport").write_text(
        "simulationType  laminar;",
        encoding="utf-8",
    )

    assessment = validation_module.build_official_case_validation_assessment(
        case_id="pitzDaily",
        solver_results={
            "solver_completed": True,
            "final_time_seconds": 285.0,
            "mesh_summary": {"cells": 12225},
        },
        assembled_case_dir=case_dir,
    )

    assert assessment["parity_status"] == "drifted"
    assert any("system/controlDict" in item for item in assessment["drift_reasons"])
    assert any(
        "constant/momentumTransport" in item for item in assessment["drift_reasons"]
    )


def test_build_official_case_validation_marks_pitzdaily_as_matched_when_official_defaults_are_present(
    tmp_path: Path,
):
    assembly_module = importlib.import_module(
        "deerflow.domain.submarine.official_case_assembly"
    )
    validation_module = importlib.import_module(
        "deerflow.domain.submarine.official_case_validation"
    )

    uploads_dir = tmp_path / "uploads"
    workspace_dir = tmp_path / "workspace"
    outputs_dir = tmp_path / "outputs"
    (uploads_dir / "pitzDaily").mkdir(parents=True, exist_ok=True)
    (uploads_dir / "pitzDaily" / "pitzDaily.blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    assembled = assembly_module.assemble_official_case_seed(
        case_id="pitzDaily",
        seed_virtual_paths=["/mnt/user-data/uploads/pitzDaily/pitzDaily.blockMeshDict"],
        uploads_dir=uploads_dir,
        workspace_dir=workspace_dir,
        outputs_dir=outputs_dir,
        run_dir_name="pitzdaily-validation",
        source_commit="441953dfbb4270dd54e14672e194e4a4a478afc4",
    )

    assessment = validation_module.build_official_case_validation_assessment(
        case_id="pitzDaily",
        solver_results={
            "solver_completed": True,
            "final_time_seconds": 285.0,
            "mesh_summary": {"cells": 12225},
        },
        assembled_case_dir=assembled.assembled_case_dir,
    )

    assert assessment["parity_status"] == "matched"
    assert not assessment["drift_reasons"]
    assert assessment["expected_metrics"]["final_time_seconds"] == 285.0
