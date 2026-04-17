from pathlib import Path


def test_assemble_cavity_case_preserves_legacy_execution_profile(tmp_path: Path):
    import importlib

    assembly_module = importlib.import_module(
        "deerflow.domain.submarine.official_case_assembly"
    )

    uploads_dir = tmp_path / "uploads"
    workspace_dir = tmp_path / "workspace"
    outputs_dir = tmp_path / "outputs"
    (uploads_dir / "cavity" / "system").mkdir(parents=True, exist_ok=True)
    (uploads_dir / "cavity" / "system" / "blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    assembled = assembly_module.assemble_official_case_seed(
        case_id="cavity",
        seed_virtual_paths=["/mnt/user-data/uploads/cavity/system/blockMeshDict"],
        uploads_dir=uploads_dir,
        workspace_dir=workspace_dir,
        outputs_dir=outputs_dir,
        run_dir_name="cavity-demo",
        source_commit="441953dfbb4270dd54e14672e194e4a4a478afc4",
    )

    assert assembled.execution_profile.case_id == "cavity"
    assert assembled.execution_profile.command_chain == ["blockMesh", "icoFoam"]
    assert (
        workspace_dir
        / "official-openfoam"
        / "cavity-demo"
        / "openfoam-case"
        / "system"
        / "blockMeshDict"
    ).exists()
    assert assembled.assembled_case_virtual_paths


def test_assemble_cavity_case_includes_pfinal_solver_block(tmp_path: Path):
    import importlib

    assembly_module = importlib.import_module(
        "deerflow.domain.submarine.official_case_assembly"
    )

    uploads_dir = tmp_path / "uploads"
    workspace_dir = tmp_path / "workspace"
    outputs_dir = tmp_path / "outputs"
    (uploads_dir / "system").mkdir(parents=True, exist_ok=True)
    (uploads_dir / "system" / "blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    assembly_module.assemble_official_case_seed(
        case_id="cavity",
        seed_virtual_paths=["/mnt/user-data/uploads/system/blockMeshDict"],
        uploads_dir=uploads_dir,
        workspace_dir=workspace_dir,
        outputs_dir=outputs_dir,
        run_dir_name="cavity-pfinal",
        source_commit="441953dfbb4270dd54e14672e194e4a4a478afc4",
    )

    fv_solution = (
        workspace_dir
        / "official-openfoam"
        / "cavity-pfinal"
        / "openfoam-case"
        / "system"
        / "fvSolution"
    ).read_text(encoding="utf-8")

    assert "pFinal" in fv_solution


def test_assemble_pitzdaily_case_preserves_modern_execution_profile(tmp_path: Path):
    import importlib

    assembly_module = importlib.import_module(
        "deerflow.domain.submarine.official_case_assembly"
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
        run_dir_name="pitzdaily-demo",
        source_commit="441953dfbb4270dd54e14672e194e4a4a478afc4",
    )

    assert assembled.execution_profile.case_id == "pitzDaily"
    assert assembled.execution_profile.command_chain[0].startswith("blockMesh -dict ")
    assert assembled.execution_profile.command_chain[1] == "foamRun"
    assert (
        workspace_dir
        / "official-openfoam"
        / "pitzdaily-demo"
        / "openfoam-case"
        / "system"
        / "pitzDaily.blockMeshDict"
    ).exists()
    assert assembled.assembled_case_virtual_paths


def test_assemble_pitzdaily_case_normalizes_bare_seed_filename(tmp_path: Path):
    import importlib

    assembly_module = importlib.import_module(
        "deerflow.domain.submarine.official_case_assembly"
    )

    uploads_dir = tmp_path / "uploads"
    workspace_dir = tmp_path / "workspace"
    outputs_dir = tmp_path / "outputs"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "pitzDaily").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    assembly_module.assemble_official_case_seed(
        case_id="pitzDaily",
        seed_virtual_paths=["/mnt/user-data/uploads/pitzDaily"],
        uploads_dir=uploads_dir,
        workspace_dir=workspace_dir,
        outputs_dir=outputs_dir,
        run_dir_name="pitzdaily-bare-seed",
        source_commit="441953dfbb4270dd54e14672e194e4a4a478afc4",
    )

    expected_dict = (
        workspace_dir
        / "official-openfoam"
        / "pitzdaily-bare-seed"
        / "openfoam-case"
        / "system"
        / "pitzDaily.blockMeshDict"
    )

    assert expected_dict.exists()
    allrun = (
        workspace_dir
        / "official-openfoam"
        / "pitzdaily-bare-seed"
        / "openfoam-case"
        / "Allrun"
    )
    assert "blockMesh -dict system/pitzDaily.blockMeshDict" in allrun.read_text(
        encoding="utf-8"
    )


def test_assemble_pitzdaily_case_uses_official_steady_control_dict_defaults(
    tmp_path: Path,
):
    import importlib

    assembly_module = importlib.import_module(
        "deerflow.domain.submarine.official_case_assembly"
    )

    uploads_dir = tmp_path / "uploads"
    workspace_dir = tmp_path / "workspace"
    outputs_dir = tmp_path / "outputs"
    (uploads_dir / "pitzDaily").mkdir(parents=True, exist_ok=True)
    (uploads_dir / "pitzDaily" / "pitzDaily.blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    assembly_module.assemble_official_case_seed(
        case_id="pitzDaily",
        seed_virtual_paths=["/mnt/user-data/uploads/pitzDaily/pitzDaily.blockMeshDict"],
        uploads_dir=uploads_dir,
        workspace_dir=workspace_dir,
        outputs_dir=outputs_dir,
        run_dir_name="pitzdaily-official-defaults",
        source_commit="441953dfbb4270dd54e14672e194e4a4a478afc4",
    )

    control_dict = (
        workspace_dir
        / "official-openfoam"
        / "pitzdaily-official-defaults"
        / "openfoam-case"
        / "system"
        / "controlDict"
    ).read_text(encoding="utf-8")

    assert "solver          incompressibleFluid;" in control_dict
    assert "endTime         2000;" in control_dict
    assert "deltaT          1;" in control_dict
    assert "writeInterval   100;" in control_dict
    assert "cacheTemporaryObjects" in control_dict


def test_assemble_pitzdaily_case_includes_official_turbulence_fields_and_functions(
    tmp_path: Path,
):
    import importlib

    assembly_module = importlib.import_module(
        "deerflow.domain.submarine.official_case_assembly"
    )

    uploads_dir = tmp_path / "uploads"
    workspace_dir = tmp_path / "workspace"
    outputs_dir = tmp_path / "outputs"
    (uploads_dir / "pitzDaily").mkdir(parents=True, exist_ok=True)
    (uploads_dir / "pitzDaily" / "pitzDaily.blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    assembly_module.assemble_official_case_seed(
        case_id="pitzDaily",
        seed_virtual_paths=["/mnt/user-data/uploads/pitzDaily/pitzDaily.blockMeshDict"],
        uploads_dir=uploads_dir,
        workspace_dir=workspace_dir,
        outputs_dir=outputs_dir,
        run_dir_name="pitzdaily-turbulence-defaults",
        source_commit="441953dfbb4270dd54e14672e194e4a4a478afc4",
    )

    case_dir = (
        workspace_dir
        / "official-openfoam"
        / "pitzdaily-turbulence-defaults"
        / "openfoam-case"
    )

    assert (case_dir / "0" / "k").exists()
    assert (case_dir / "0" / "epsilon").exists()
    assert (case_dir / "system" / "functions").exists()

    momentum_transport = (case_dir / "constant" / "momentumTransport").read_text(
        encoding="utf-8"
    )
    fv_schemes = (case_dir / "system" / "fvSchemes").read_text(encoding="utf-8")
    fv_solution = (case_dir / "system" / "fvSolution").read_text(encoding="utf-8")
    functions = (case_dir / "system" / "functions").read_text(encoding="utf-8")

    assert "simulationType" in momentum_transport
    assert "RAS;" in momentum_transport
    assert "model           kEpsilon;" in momentum_transport
    assert "default         steadyState;" in fv_schemes
    assert "SIMPLE" in fv_solution
    assert "residualControl" in fv_solution
    assert "#includeFunc streamlinesLine" in functions


def test_assemble_cavity_case_keeps_the_pinned_legacy_defaults_while_pitzdaily_is_upgraded(
    tmp_path: Path,
):
    import importlib

    assembly_module = importlib.import_module(
        "deerflow.domain.submarine.official_case_assembly"
    )

    uploads_dir = tmp_path / "uploads"
    workspace_dir = tmp_path / "workspace"
    outputs_dir = tmp_path / "outputs"
    (uploads_dir / "system").mkdir(parents=True, exist_ok=True)
    (uploads_dir / "system" / "blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    assembly_module.assemble_official_case_seed(
        case_id="cavity",
        seed_virtual_paths=["/mnt/user-data/uploads/system/blockMeshDict"],
        uploads_dir=uploads_dir,
        workspace_dir=workspace_dir,
        outputs_dir=outputs_dir,
        run_dir_name="cavity-regression",
        source_commit="441953dfbb4270dd54e14672e194e4a4a478afc4",
    )

    case_dir = (
        workspace_dir
        / "official-openfoam"
        / "cavity-regression"
        / "openfoam-case"
    )
    control_dict = (case_dir / "system" / "controlDict").read_text(encoding="utf-8")
    fv_solution = (case_dir / "system" / "fvSolution").read_text(encoding="utf-8")

    assert "endTime         0.5;" in control_dict
    assert "deltaT          0.005;" in control_dict
    assert "application     icoFoam;" in control_dict
    assert "pFinal" in fv_solution
    assert "PISO" in fv_solution
