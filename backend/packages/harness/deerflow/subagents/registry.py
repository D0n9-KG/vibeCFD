"""Subagent registry for managing available subagents."""

import logging
from dataclasses import replace

from deerflow.config import get_app_config
from deerflow.config.runtime_config_overrides import get_runtime_config_overrides
from deerflow.subagents.builtins import BUILTIN_SUBAGENTS
from deerflow.subagents.config import SubagentConfig

logger = logging.getLogger(__name__)


def _resolve_runtime_model_override(name: str) -> str | None:
    if not name.startswith("submarine-"):
        return None

    role_id = name.removeprefix("submarine-")
    override = get_runtime_config_overrides().stage_roles.get(role_id)
    if override is None or override.model_mode != "explicit":
        return None

    if override.model_name and get_app_config().get_model_config(override.model_name):
        return override.model_name

    if override.model_name:
        logger.warning(
            "Runtime override model '%s' for subagent '%s' is not configured; ignoring override.",
            override.model_name,
            name,
        )

    return None


def get_subagent_config(name: str) -> SubagentConfig | None:
    """Get a subagent configuration by name, with config.yaml overrides applied.

    Args:
        name: The name of the subagent.

    Returns:
        SubagentConfig if found (with any config.yaml overrides applied), None otherwise.
    """
    config = BUILTIN_SUBAGENTS.get(name)
    if config is None:
        return None

    # Apply timeout override from config.yaml (lazy import to avoid circular deps)
    from deerflow.config.subagents_config import get_subagents_app_config

    app_config = get_subagents_app_config()
    effective_timeout = app_config.get_timeout_for(name)
    if effective_timeout != config.timeout_seconds:
        logger.debug(f"Subagent '{name}': timeout overridden by config.yaml ({config.timeout_seconds}s -> {effective_timeout}s)")
        config = replace(config, timeout_seconds=effective_timeout)

    runtime_model_override = _resolve_runtime_model_override(name)
    if runtime_model_override and runtime_model_override != config.model:
        logger.debug(
            "Subagent '%s': model overridden by runtime-config (%s -> %s)",
            name,
            config.model,
            runtime_model_override,
        )
        config = replace(config, model=runtime_model_override)

    return config


def list_subagents() -> list[SubagentConfig]:
    """List all available subagent configurations (with config.yaml overrides applied).

    Returns:
        List of all registered SubagentConfig instances.
    """
    return [get_subagent_config(name) for name in BUILTIN_SUBAGENTS]


def get_subagent_names() -> list[str]:
    """Get all available subagent names.

    Returns:
        List of subagent names.
    """
    return list(BUILTIN_SUBAGENTS.keys())
