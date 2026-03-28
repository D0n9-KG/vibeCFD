"""Regression tests for docker sandbox mode detection logic."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "docker.sh"


def _get_bash_command() -> list[str]:
    """Resolve a working bash executable for shell-script tests.

    On Windows, `bash.exe` may resolve to the WSL launcher, which fails when a
    Linux distro is not installed. Prefer Git Bash when available.
    """
    if os.name == "nt":
        git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
        if git_bash.exists():
            return [str(git_bash), "-lc"]

    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is not available on this machine")

    bash_path = Path(bash)
    if os.name == "nt" and bash_path.name.lower() == "bash.exe" and "system32" in str(bash_path).lower():
        pytest.skip("bash resolves to the Windows WSL launcher without a usable shell")

    return [bash, "-lc"]


def _detect_mode_with_config(config_content: str) -> str:
    """Write config content into a temp project root and execute detect_sandbox_mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "config.yaml").write_text(config_content)

        command = f"source '{SCRIPT_PATH}' && PROJECT_ROOT='{tmp_root}' && detect_sandbox_mode"

        output = subprocess.check_output(
            [*_get_bash_command(), command],
            text=True,
        ).strip()

        return output


def _resolve_image_with_config(config_content: str | None) -> str:
    """Write config content into a temp project root and execute resolve_sandbox_image."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        if config_content is not None:
            (tmp_root / "config.yaml").write_text(config_content)

        command = f"source '{SCRIPT_PATH}' && PROJECT_ROOT='{tmp_root}' && resolve_sandbox_image"

        output = subprocess.check_output(
            [*_get_bash_command(), command],
            text=True,
        ).strip()

        return output


def test_detect_mode_defaults_to_local_when_config_missing():
    """No config file should default to local mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        command = f"source '{SCRIPT_PATH}' && PROJECT_ROOT='{tmpdir}' && detect_sandbox_mode"
        output = subprocess.check_output([*_get_bash_command(), command], text=True).strip()

    assert output == "local"


def test_detect_mode_local_provider():
    """Local sandbox provider should map to local mode."""
    config = """
sandbox:
  use: deerflow.sandbox.local:LocalSandboxProvider
""".strip()

    assert _detect_mode_with_config(config) == "local"


def test_detect_mode_aio_without_provisioner_url():
    """AIO sandbox without provisioner_url should map to aio mode."""
    config = """
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
""".strip()

    assert _detect_mode_with_config(config) == "aio"


def test_detect_mode_provisioner_with_url():
    """AIO sandbox with provisioner_url should map to provisioner mode."""
    config = """
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
  provisioner_url: http://provisioner:8002
""".strip()

    assert _detect_mode_with_config(config) == "provisioner"


def test_detect_mode_ignores_commented_provisioner_url():
    """Commented provisioner_url should not activate provisioner mode."""
    config = """
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
  # provisioner_url: http://provisioner:8002
""".strip()

    assert _detect_mode_with_config(config) == "aio"


def test_detect_mode_unknown_provider_falls_back_to_local():
    """Unknown sandbox provider should default to local mode."""
    config = """
sandbox:
  use: custom.module:UnknownProvider
""".strip()

    assert _detect_mode_with_config(config) == "local"


def test_resolve_sandbox_image_defaults_when_config_missing():
    """No config should fall back to the default sandbox image."""
    assert _resolve_image_with_config(None) == "enterprise-public-cn-beijing.cr.volces.com/vefaas-public/all-in-one-sandbox:latest"


def test_resolve_sandbox_image_uses_configured_aio_image():
    """Configured sandbox.image should be returned for AIO sandbox mode."""
    config = """
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
  image: deer-flow-openfoam-sandbox:latest
""".strip()

    assert _resolve_image_with_config(config) == "deer-flow-openfoam-sandbox:latest"


def test_resolve_sandbox_image_ignores_commented_image():
    """Commented image lines should not affect sandbox image resolution."""
    config = """
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
  # image: should-not-be-used:latest
""".strip()

    assert _resolve_image_with_config(config) == "enterprise-public-cn-beijing.cr.volces.com/vefaas-public/all-in-one-sandbox:latest"
