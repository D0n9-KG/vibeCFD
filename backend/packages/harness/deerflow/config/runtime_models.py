"""Persisted runtime model registry and write-only secret store."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from deerflow.config.model_config import ModelConfig
from deerflow.config.paths import get_paths

RUNTIME_MODEL_NAME_PATTERN = r"^[A-Za-z0-9._-]+$"


def _normalize_runtime_config_path(path_value: str | Path) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return get_paths().base_dir / path


class RuntimeModelDefinition(BaseModel):
    name: str = Field(pattern=RUNTIME_MODEL_NAME_PATTERN)
    display_name: str | None = None
    description: str | None = None
    provider_key: Literal["openai", "openai-compatible", "anthropic"]
    model: str
    base_url: str | None = None
    supports_thinking: bool = False
    supports_reasoning_effort: bool = False
    supports_vision: bool = False
    max_tokens: int | None = None
    use_responses_api: bool | None = None
    output_version: str | None = None

    model_config = ConfigDict(extra="forbid")


class RuntimeModelRegistry(BaseModel):
    models: list[RuntimeModelDefinition] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def resolve_config_path(cls, config_path: str | None = None) -> Path:
        if config_path:
            return _normalize_runtime_config_path(config_path)

        env_path = os.getenv("DEER_FLOW_RUNTIME_MODELS_PATH", "").strip()
        if env_path:
            return _normalize_runtime_config_path(env_path)

        return get_paths().runtime_models_file

    @classmethod
    def from_file(cls, config_path: str | None = None) -> RuntimeModelRegistry:
        resolved_path = cls.resolve_config_path(config_path)
        if not resolved_path.exists():
            return cls()

        with open(resolved_path, encoding="utf-8") as handle:
            payload = json.load(handle)

        return cls.model_validate(payload)


class RuntimeModelSecrets(BaseModel):
    api_keys: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def resolve_config_path(cls, config_path: str | None = None) -> Path:
        if config_path:
            return _normalize_runtime_config_path(config_path)

        env_path = os.getenv("DEER_FLOW_RUNTIME_MODEL_SECRETS_PATH", "").strip()
        if env_path:
            return _normalize_runtime_config_path(env_path)

        return get_paths().runtime_model_secrets_file

    @classmethod
    def from_file(cls, config_path: str | None = None) -> RuntimeModelSecrets:
        resolved_path = cls.resolve_config_path(config_path)
        if not resolved_path.exists():
            return cls()

        with open(resolved_path, encoding="utf-8") as handle:
            payload = json.load(handle)

        return cls.model_validate(payload)


_runtime_model_registry: RuntimeModelRegistry | None = None
_runtime_model_registry_path: Path | None = None
_runtime_model_registry_mtime: float | None = None
_runtime_model_registry_is_custom = False

_runtime_model_secrets: RuntimeModelSecrets | None = None
_runtime_model_secrets_path: Path | None = None
_runtime_model_secrets_mtime: float | None = None
_runtime_model_secrets_is_custom = False


def _get_config_mtime(config_path: Path) -> float | None:
    try:
        return config_path.stat().st_mtime
    except OSError:
        return None


def _load_and_cache_runtime_model_registry(
    config_path: str | None = None,
) -> RuntimeModelRegistry:
    global _runtime_model_registry
    global _runtime_model_registry_path
    global _runtime_model_registry_mtime
    global _runtime_model_registry_is_custom

    resolved_path = RuntimeModelRegistry.resolve_config_path(config_path)
    registry = RuntimeModelRegistry.from_file(str(resolved_path))
    _runtime_model_registry = registry
    _runtime_model_registry_path = resolved_path
    _runtime_model_registry_mtime = _get_config_mtime(resolved_path)
    _runtime_model_registry_is_custom = False
    return registry


def get_runtime_model_registry() -> RuntimeModelRegistry:
    global _runtime_model_registry
    global _runtime_model_registry_path
    global _runtime_model_registry_mtime

    if _runtime_model_registry is not None and _runtime_model_registry_is_custom:
        return _runtime_model_registry

    resolved_path = RuntimeModelRegistry.resolve_config_path()
    current_mtime = _get_config_mtime(resolved_path)
    should_reload = (
        _runtime_model_registry is None
        or _runtime_model_registry_path != resolved_path
        or _runtime_model_registry_mtime != current_mtime
    )

    if should_reload:
        return _load_and_cache_runtime_model_registry(str(resolved_path))

    return _runtime_model_registry


def save_runtime_model_registry(
    registry: RuntimeModelRegistry,
    config_path: str | None = None,
) -> RuntimeModelRegistry:
    resolved_path = RuntimeModelRegistry.resolve_config_path(config_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    with open(resolved_path, "w", encoding="utf-8") as handle:
        json.dump(
            registry.model_dump(exclude_none=True),
            handle,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")

    return _load_and_cache_runtime_model_registry(str(resolved_path))


def set_runtime_model_registry(registry: RuntimeModelRegistry) -> None:
    global _runtime_model_registry
    global _runtime_model_registry_path
    global _runtime_model_registry_mtime
    global _runtime_model_registry_is_custom

    _runtime_model_registry = registry
    _runtime_model_registry_path = None
    _runtime_model_registry_mtime = None
    _runtime_model_registry_is_custom = True


def _load_and_cache_runtime_model_secrets(
    config_path: str | None = None,
) -> RuntimeModelSecrets:
    global _runtime_model_secrets
    global _runtime_model_secrets_path
    global _runtime_model_secrets_mtime
    global _runtime_model_secrets_is_custom

    resolved_path = RuntimeModelSecrets.resolve_config_path(config_path)
    secrets = RuntimeModelSecrets.from_file(str(resolved_path))
    _runtime_model_secrets = secrets
    _runtime_model_secrets_path = resolved_path
    _runtime_model_secrets_mtime = _get_config_mtime(resolved_path)
    _runtime_model_secrets_is_custom = False
    return secrets


def get_runtime_model_secrets() -> RuntimeModelSecrets:
    global _runtime_model_secrets
    global _runtime_model_secrets_path
    global _runtime_model_secrets_mtime

    if _runtime_model_secrets is not None and _runtime_model_secrets_is_custom:
        return _runtime_model_secrets

    resolved_path = RuntimeModelSecrets.resolve_config_path()
    current_mtime = _get_config_mtime(resolved_path)
    should_reload = (
        _runtime_model_secrets is None
        or _runtime_model_secrets_path != resolved_path
        or _runtime_model_secrets_mtime != current_mtime
    )

    if should_reload:
        return _load_and_cache_runtime_model_secrets(str(resolved_path))

    return _runtime_model_secrets


def save_runtime_model_secrets(
    secrets: RuntimeModelSecrets,
    config_path: str | None = None,
) -> RuntimeModelSecrets:
    resolved_path = RuntimeModelSecrets.resolve_config_path(config_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    with open(resolved_path, "w", encoding="utf-8") as handle:
        json.dump(
            secrets.model_dump(exclude_none=True),
            handle,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")

    return _load_and_cache_runtime_model_secrets(str(resolved_path))


def set_runtime_model_secrets(secrets: RuntimeModelSecrets) -> None:
    global _runtime_model_secrets
    global _runtime_model_secrets_path
    global _runtime_model_secrets_mtime
    global _runtime_model_secrets_is_custom

    _runtime_model_secrets = secrets
    _runtime_model_secrets_path = None
    _runtime_model_secrets_mtime = None
    _runtime_model_secrets_is_custom = True


def build_runtime_model_config(
    model_definition: RuntimeModelDefinition,
    *,
    api_key: str | None,
) -> ModelConfig:
    payload: dict[str, object] = {
        "name": model_definition.name,
        "display_name": model_definition.display_name,
        "description": model_definition.description,
        "model": model_definition.model,
        "supports_thinking": model_definition.supports_thinking,
        "supports_reasoning_effort": model_definition.supports_reasoning_effort,
        "supports_vision": model_definition.supports_vision,
        "max_tokens": model_definition.max_tokens,
        "use_responses_api": model_definition.use_responses_api,
        "output_version": model_definition.output_version,
        "provider_key": model_definition.provider_key,
    }

    if model_definition.provider_key in {"openai", "openai-compatible"}:
        payload["use"] = "deerflow.models.openai_cli_provider:OpenAICliChatModel"
        if model_definition.base_url:
            payload["openai_api_base"] = model_definition.base_url
        if api_key:
            payload["openai_api_key"] = api_key
    else:
        payload["use"] = "deerflow.models.claude_provider:ClaudeChatModel"
        if model_definition.base_url:
            payload["anthropic_api_url"] = model_definition.base_url
        if api_key:
            payload["anthropic_api_key"] = api_key

    return ModelConfig.model_validate(payload)


def list_runtime_model_configs() -> list[ModelConfig]:
    registry = get_runtime_model_registry()
    secrets = get_runtime_model_secrets()
    return [
        build_runtime_model_config(
            model_definition,
            api_key=secrets.api_keys.get(model_definition.name),
        )
        for model_definition in registry.models
    ]


def get_runtime_model_config(name: str) -> ModelConfig | None:
    for model in list_runtime_model_configs():
        if model.name == name:
            return model
    return None
