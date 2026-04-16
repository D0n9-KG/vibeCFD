"""Environment fingerprint and parity helpers for submarine CFD runs."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from deerflow.config.app_config import AppConfig, get_app_config

from .models import (
    SubmarineEnvironmentFingerprint,
    SubmarineEnvironmentParityAssessment,
)

SUPPORTED_RUNTIME_PROFILES: dict[str, dict[str, object]] = {
    "local_cli": {
        "label": "Local CLI",
        "compose_file": None,
        "allowed_origins": {"host_process", "unit_test", "outputs_only"},
        "expected_mount_strategies": {"workspace_path", "outputs_only"},
        "requires_docker_socket": False,
    },
    "docker_compose_dev": {
        "label": "Docker Compose Dev",
        "compose_file": "docker/docker-compose-dev.yaml",
        "allowed_origins": {"docker_container", "unit_test"},
        "expected_mount_strategies": {"host_bind_mount"},
        "requires_docker_socket": True,
    },
    "docker_compose_deployed": {
        "label": "Docker Compose Deployed",
        "compose_file": "docker/docker-compose.yaml",
        "allowed_origins": {"docker_container", "unit_test"},
        "expected_mount_strategies": {"runtime_home_volume"},
        "requires_docker_socket": True,
    },
}


def _runtime_profile_from_config(app_config: Any) -> str | None:
    sandbox = getattr(app_config, "sandbox", None)
    sandbox_environment = getattr(sandbox, "environment", None)
    if isinstance(sandbox_environment, Mapping):
        value = sandbox_environment.get("DEER_FLOW_RUNTIME_PROFILE")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _resolve_runtime_profile(app_config: Any) -> tuple[str, list[str]]:
    profile_id = os.getenv("DEER_FLOW_RUNTIME_PROFILE")
    if profile_id:
        return profile_id.strip(), ["env:DEER_FLOW_RUNTIME_PROFILE"]

    config_profile = _runtime_profile_from_config(app_config)
    if config_profile:
        return config_profile, ["config:sandbox.environment.DEER_FLOW_RUNTIME_PROFILE"]

    return "local_cli", ["default:local_cli"]


def _detect_runtime_origin(workspace_dir: Path | None) -> str:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return "unit_test"
    if Path("/.dockerenv").exists():
        return "docker_container"
    if workspace_dir is not None:
        return "host_process"
    return "outputs_only"


def _resolve_deer_flow_home(outputs_dir: Path) -> str | None:
    explicit_home = os.getenv("DEER_FLOW_HOME")
    if explicit_home:
        return explicit_home
    for candidate in [outputs_dir, *outputs_dir.parents]:
        if candidate.name == ".deer-flow":
            return str(candidate)
    return None


def _resolve_deer_flow_root(deer_flow_home: str | None, outputs_dir: Path) -> str | None:
    explicit_root = os.getenv("DEER_FLOW_ROOT") or os.getenv("DEER_FLOW_REPO_ROOT")
    if explicit_root:
        return explicit_root
    if deer_flow_home:
        try:
            return str(Path(deer_flow_home).parent)
        except OSError:
            return None
    try:
        return str(outputs_dir.parents[2])
    except IndexError:
        return None


def _infer_host_mount_strategy(workspace_dir: Path | None) -> str:
    deer_flow_home = os.getenv("DEER_FLOW_HOME")
    host_base_dir = os.getenv("DEER_FLOW_HOST_BASE_DIR")
    if deer_flow_home and host_base_dir and deer_flow_home != host_base_dir:
        return "runtime_home_volume"
    if host_base_dir or os.getenv("DEER_FLOW_HOST_SKILLS_PATH"):
        return "host_bind_mount"
    if workspace_dir is not None:
        return "workspace_path"
    return "outputs_only"


def _docker_socket_available() -> bool:
    socket_path = os.getenv("DEER_FLOW_DOCKER_SOCKET") or "/var/run/docker.sock"
    try:
        return Path(socket_path).exists()
    except OSError:
        return False


def build_environment_fingerprint(
    *,
    workspace_dir: Path | None,
    outputs_dir: Path,
    app_config: Any | None = None,
) -> SubmarineEnvironmentFingerprint:
    config = app_config
    if config is None:
        try:
            config = get_app_config()
        except FileNotFoundError:
            config = None
    profile_id, source_hints = _resolve_runtime_profile(config)
    profile = SUPPORTED_RUNTIME_PROFILES.get(profile_id, {})
    config_sources = [*source_hints]
    try:
        config_sources.append(f"config:{AppConfig.resolve_config_path()}")
    except FileNotFoundError:
        pass

    docker_socket_env = os.getenv("DEER_FLOW_DOCKER_SOCKET")
    if docker_socket_env:
        config_sources.append("env:DEER_FLOW_DOCKER_SOCKET")
    if os.getenv("DEER_FLOW_HOME"):
        config_sources.append("env:DEER_FLOW_HOME")
    if os.getenv("DEER_FLOW_ROOT") or os.getenv("DEER_FLOW_REPO_ROOT"):
        config_sources.append("env:DEER_FLOW_ROOT")
    if os.getenv("DEER_FLOW_HOST_BASE_DIR"):
        config_sources.append("env:DEER_FLOW_HOST_BASE_DIR")
    if os.getenv("DEER_FLOW_HOST_SKILLS_PATH"):
        config_sources.append("env:DEER_FLOW_HOST_SKILLS_PATH")

    deer_flow_home = _resolve_deer_flow_home(outputs_dir)
    deer_flow_root = _resolve_deer_flow_root(deer_flow_home, outputs_dir)
    sandbox = getattr(config, "sandbox", None)

    return SubmarineEnvironmentFingerprint(
        profile_id=profile_id,
        profile_label=str(profile.get("label") or "Unknown environment profile"),
        runtime_origin=_detect_runtime_origin(workspace_dir),
        compose_file=(str(profile.get("compose_file")) if isinstance(profile.get("compose_file"), str) else None),
        sandbox_image=getattr(sandbox, "image", None),
        deer_flow_home=deer_flow_home,
        deer_flow_root=deer_flow_root,
        docker_socket_available=_docker_socket_available(),
        host_mount_strategy=_infer_host_mount_strategy(workspace_dir),
        config_sources=config_sources,
    )


def build_environment_parity_assessment(
    fingerprint: Mapping[str, Any] | SubmarineEnvironmentFingerprint,
) -> SubmarineEnvironmentParityAssessment:
    fingerprint_model = SubmarineEnvironmentFingerprint.model_validate(fingerprint)
    profile = SUPPORTED_RUNTIME_PROFILES.get(fingerprint_model.profile_id)
    assessment_seed = fingerprint_model.model_dump(
        mode="json",
        exclude={"parity_status", "drift_reasons", "recovery_guidance"},
    )

    if profile is None:
        return SubmarineEnvironmentParityAssessment(
            **assessment_seed,
            parity_status="unknown",
            drift_reasons=[f"Unsupported environment profile `{fingerprint_model.profile_id}`."],
            recovery_guidance=[
                "Set DEER_FLOW_RUNTIME_PROFILE to one of: local_cli, docker_compose_dev, docker_compose_deployed.",
            ],
        )

    drift_reasons: list[str] = []
    recovery_guidance: list[str] = []
    blockers: list[str] = []

    allowed_origins = {str(item) for item in profile.get("allowed_origins", set()) if isinstance(item, str)}
    expected_mount_strategies = {str(item) for item in profile.get("expected_mount_strategies", set()) if isinstance(item, str)}

    if allowed_origins and fingerprint_model.runtime_origin not in allowed_origins:
        drift_reasons.append(f"Runtime origin `{fingerprint_model.runtime_origin}` does not match supported `{fingerprint_model.profile_id}` execution paths.")
    if expected_mount_strategies and fingerprint_model.host_mount_strategy not in expected_mount_strategies:
        drift_reasons.append(f"Host mount strategy `{fingerprint_model.host_mount_strategy}` does not match `{fingerprint_model.profile_id}` expectations.")
    if not fingerprint_model.sandbox_image and fingerprint_model.runtime_origin != "unit_test":
        blockers.append("Sandbox image is missing from the active configuration.")
    if bool(profile.get("requires_docker_socket")) and not fingerprint_model.docker_socket_available:
        blockers.append(f"Profile `{fingerprint_model.profile_id}` requires Docker socket access for sandbox execution.")

    if blockers:
        recovery_guidance.extend(
            [
                "Mount the Docker socket and restart the DeerFlow runtime before relying on reproducible reruns.",
                "Keep DEER_FLOW_RUNTIME_PROFILE aligned with the active compose deployment path.",
            ]
        )
        parity_status = "blocked"
    elif drift_reasons:
        recovery_guidance.extend(
            [
                "Align DEER_FLOW_RUNTIME_PROFILE with the actual runtime path before treating the run as reproducible.",
                "Match the documented compose profile and host mount strategy to remove parity drift.",
            ]
        )
        parity_status = "drifted_but_runnable"
    else:
        parity_status = "matched"

    return SubmarineEnvironmentParityAssessment(
        **assessment_seed,
        parity_status=parity_status,
        drift_reasons=[*blockers, *drift_reasons],
        recovery_guidance=recovery_guidance,
    )


__all__ = [
    "SUPPORTED_RUNTIME_PROFILES",
    "build_environment_fingerprint",
    "build_environment_parity_assessment",
]
