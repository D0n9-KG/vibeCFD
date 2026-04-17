from pathlib import Path

import pytest


@pytest.fixture
def case_seed_module():
    import importlib

    return importlib.import_module(
        "deerflow.domain.submarine.official_case_seed_resolver"
    )


def test_resolve_official_case_seed_detects_cavity_blockmesh_only(
    tmp_path: Path, case_seed_module
):
    uploads_dir = tmp_path / "uploads"
    (uploads_dir / "system").mkdir(parents=True, exist_ok=True)
    (uploads_dir / "system" / "blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    resolution = case_seed_module.resolve_official_case_seed(
        uploads_dir=uploads_dir,
    )

    assert resolution is not None
    assert resolution.case_id == "cavity"
    assert resolution.seed_virtual_paths == [
        "/mnt/user-data/uploads/system/blockMeshDict"
    ]


def test_resolve_official_case_seed_detects_flat_uploaded_cavity_blockmesh(
    tmp_path: Path, case_seed_module
):
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    resolution = case_seed_module.resolve_official_case_seed(
        uploads_dir=uploads_dir,
    )

    assert resolution is not None
    assert resolution.case_id == "cavity"
    assert resolution.seed_virtual_paths == ["/mnt/user-data/uploads/blockMeshDict"]


def test_resolve_official_case_seed_detects_nested_cavity_fixture_layout(
    tmp_path: Path, case_seed_module
):
    uploads_dir = tmp_path / "uploads"
    (uploads_dir / "cavity" / "system").mkdir(parents=True, exist_ok=True)
    (uploads_dir / "cavity" / "system" / "blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    resolution = case_seed_module.resolve_official_case_seed(
        uploads_dir=uploads_dir,
    )

    assert resolution is not None
    assert resolution.case_id == "cavity"
    assert resolution.seed_virtual_paths == [
        "/mnt/user-data/uploads/cavity/system/blockMeshDict"
    ]


def test_resolve_official_case_seed_detects_pitzdaily_seed(
    tmp_path: Path, case_seed_module
):
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "pitzDaily.blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    resolution = case_seed_module.resolve_official_case_seed(
        uploads_dir=uploads_dir,
    )

    assert resolution is not None
    assert resolution.case_id == "pitzDaily"
    assert resolution.seed_virtual_paths == [
        "/mnt/user-data/uploads/pitzDaily.blockMeshDict"
    ]


def test_resolve_official_case_seed_detects_bare_uploaded_pitzdaily_seed(
    tmp_path: Path, case_seed_module
):
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "pitzDaily").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    resolution = case_seed_module.resolve_official_case_seed(
        uploads_dir=uploads_dir,
    )

    assert resolution is not None
    assert resolution.case_id == "pitzDaily"
    assert resolution.seed_virtual_paths == ["/mnt/user-data/uploads/pitzDaily"]


def test_resolve_official_case_seed_detects_nested_pitzdaily_fixture_layout(
    tmp_path: Path, case_seed_module
):
    uploads_dir = tmp_path / "uploads"
    (uploads_dir / "pitzDaily").mkdir(parents=True, exist_ok=True)
    (uploads_dir / "pitzDaily" / "pitzDaily.blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )

    resolution = case_seed_module.resolve_official_case_seed(
        uploads_dir=uploads_dir,
    )

    assert resolution is not None
    assert resolution.case_id == "pitzDaily"
    assert resolution.seed_virtual_paths == [
        "/mnt/user-data/uploads/pitzDaily/pitzDaily.blockMeshDict"
    ]


def test_resolve_official_case_seed_flags_partial_import(
    tmp_path: Path, case_seed_module
):
    uploads_dir = tmp_path / "uploads"
    (uploads_dir / "0").mkdir(parents=True, exist_ok=True)
    (uploads_dir / "0" / "U").write_text("FoamFile{}", encoding="utf-8")

    resolution = case_seed_module.resolve_official_case_seed(
        uploads_dir=uploads_dir,
    )

    assert resolution is not None
    assert resolution.status == "partial"
    assert resolution.case_id is None
    assert "required seed file" in resolution.user_message
