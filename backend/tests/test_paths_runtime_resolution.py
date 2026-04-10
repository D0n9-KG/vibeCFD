import importlib
from pathlib import Path
from unittest.mock import patch


def test_default_base_dir_uses_process_start_dir_without_runtime_cwd_calls(tmp_path):
    paths_module = importlib.import_module("deerflow.config.paths")
    backend_start_dir = tmp_path / "backend"
    backend_start_dir.mkdir()
    (backend_start_dir / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")

    with (
        patch.object(paths_module, "_paths", None),
        patch.object(paths_module, "_PROCESS_START_DIR", backend_start_dir, create=True),
        patch.dict("os.environ", {}, clear=False),
        patch.object(Path, "cwd", side_effect=AssertionError("Path.cwd should not run at request time")),
    ):
        paths = paths_module.Paths()

        assert paths.base_dir == backend_start_dir / ".deer-flow"
