from __future__ import annotations

import shutil
from pathlib import Path

import pytest


@pytest.fixture()
def temp_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "workspace"
    for name in ("runs", "uploads", "data", "data/cases", "data/skills"):
        (root / name).mkdir(parents=True, exist_ok=True)

    fixture_root = Path(__file__).resolve().parents[2] / "data"
    if fixture_root.exists():
        shutil.copytree(fixture_root / "cases", root / "data" / "cases", dirs_exist_ok=True)
        shutil.copytree(fixture_root / "skills", root / "data" / "skills", dirs_exist_ok=True)

    monkeypatch.setenv("SUBMARINE_DEMO_ROOT", str(root))
    return root
