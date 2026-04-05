"""Regression tests for cross-platform AIO sandbox provider imports."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_aio_sandbox_provider_module_imports_cleanly():
    """The AIO sandbox provider module should import on the current platform."""
    command = [
        sys.executable,
        "-c",
        "import importlib; importlib.import_module('deerflow.community.aio_sandbox.aio_sandbox_provider'); print('ok')",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT / "backend",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
