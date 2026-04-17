"""Persisted runtime overrides for lead-agent and submarine stage-role model routing."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from deerflow.config.paths import get_paths


def _normalize_runtime_config_path(path_value: str | Path) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return get_paths().base_dir / path


class RuntimeLeadAgentOverride(BaseModel):
    default_model: str | None = Field(
        default=None,
        description="Optional effective default model override for the lead agent.",
    )


class RuntimeStageRoleOverride(BaseModel):
    model_mode: Literal["inherit", "explicit"] = Field(
        default="inherit",
        description="Whether the stage role inherits the lead default or pins a model.",
    )
    model_name: str | None = Field(
        default=None,
        description="Explicit model name when model_mode='explicit'.",
    )

    model_config = ConfigDict(extra="forbid")


class RuntimeConfigOverrides(BaseModel):
    lead_agent: RuntimeLeadAgentOverride = Field(
        default_factory=RuntimeLeadAgentOverride,
    )
    stage_roles: dict[str, RuntimeStageRoleOverride] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def resolve_config_path(cls, config_path: str | None = None) -> Path:
        if config_path:
            return _normalize_runtime_config_path(config_path)

        env_path = os.getenv("DEER_FLOW_RUNTIME_CONFIG_PATH", "").strip()
        if env_path:
            return _normalize_runtime_config_path(env_path)

        return get_paths().runtime_config_overrides_file

    @classmethod
    def from_file(cls, config_path: str | None = None) -> RuntimeConfigOverrides:
        resolved_path = cls.resolve_config_path(config_path)
        if not resolved_path.exists():
            return cls()

        with open(resolved_path, encoding="utf-8") as handle:
            payload = json.load(handle)

        return cls.model_validate(payload)


_runtime_config_overrides: RuntimeConfigOverrides | None = None
_runtime_config_overrides_path: Path | None = None
_runtime_config_overrides_mtime: float | None = None
_runtime_config_overrides_is_custom = False


def _get_config_mtime(config_path: Path) -> float | None:
    try:
        return config_path.stat().st_mtime
    except OSError:
        return None


def _load_and_cache_runtime_config_overrides(
    config_path: str | None = None,
) -> RuntimeConfigOverrides:
    global _runtime_config_overrides
    global _runtime_config_overrides_path
    global _runtime_config_overrides_mtime
    global _runtime_config_overrides_is_custom

    resolved_path = RuntimeConfigOverrides.resolve_config_path(config_path)
    overrides = RuntimeConfigOverrides.from_file(str(resolved_path))

    _runtime_config_overrides = overrides
    _runtime_config_overrides_path = resolved_path
    _runtime_config_overrides_mtime = _get_config_mtime(resolved_path)
    _runtime_config_overrides_is_custom = False
    return overrides


def get_runtime_config_overrides() -> RuntimeConfigOverrides:
    global _runtime_config_overrides
    global _runtime_config_overrides_path
    global _runtime_config_overrides_mtime

    if _runtime_config_overrides is not None and _runtime_config_overrides_is_custom:
        return _runtime_config_overrides

    resolved_path = RuntimeConfigOverrides.resolve_config_path()
    current_mtime = _get_config_mtime(resolved_path)
    should_reload = (
        _runtime_config_overrides is None
        or _runtime_config_overrides_path != resolved_path
        or _runtime_config_overrides_mtime != current_mtime
    )

    if should_reload:
        return _load_and_cache_runtime_config_overrides(str(resolved_path))

    return _runtime_config_overrides


def save_runtime_config_overrides(
    overrides: RuntimeConfigOverrides,
    config_path: str | None = None,
) -> RuntimeConfigOverrides:
    resolved_path = RuntimeConfigOverrides.resolve_config_path(config_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    with open(resolved_path, "w", encoding="utf-8") as handle:
        json.dump(
            overrides.model_dump(exclude_none=True),
            handle,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")

    return _load_and_cache_runtime_config_overrides(str(resolved_path))


def reload_runtime_config_overrides(
    config_path: str | None = None,
) -> RuntimeConfigOverrides:
    return _load_and_cache_runtime_config_overrides(config_path)


def reset_runtime_config_overrides() -> None:
    global _runtime_config_overrides
    global _runtime_config_overrides_path
    global _runtime_config_overrides_mtime
    global _runtime_config_overrides_is_custom

    _runtime_config_overrides = None
    _runtime_config_overrides_path = None
    _runtime_config_overrides_mtime = None
    _runtime_config_overrides_is_custom = False


def set_runtime_config_overrides(overrides: RuntimeConfigOverrides) -> None:
    global _runtime_config_overrides
    global _runtime_config_overrides_path
    global _runtime_config_overrides_mtime
    global _runtime_config_overrides_is_custom

    _runtime_config_overrides = overrides
    _runtime_config_overrides_path = None
    _runtime_config_overrides_mtime = None
    _runtime_config_overrides_is_custom = True
