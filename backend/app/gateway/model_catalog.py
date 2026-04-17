from __future__ import annotations

from collections.abc import Iterable
from typing import Any

_KNOWN_PROVIDER_KEYS = {"openai", "openai-compatible", "anthropic"}


def get_effective_models(config: Any) -> list[Any]:
    getter = getattr(config, "get_effective_models", None)
    if callable(getter):
        resolved_models = getter()
        if isinstance(resolved_models, Iterable):
            return list(resolved_models)

    return list(getattr(config, "models", []))


def get_model_config_by_name(config: Any, model_name: str) -> Any | None:
    getter = getattr(config, "get_model_config", None)
    if callable(getter):
        model = getter(model_name)
        if model is not None:
            return model

    return next(
        (
            model
            for model in get_effective_models(config)
            if getattr(model, "name", None) == model_name
        ),
        None,
    )


def resolve_provider_key(model: Any) -> str:
    extra = getattr(model, "model_extra", None)
    if isinstance(extra, dict):
        for key_name in ("provider_key", "runtime_provider_key"):
            provider_key = extra.get(key_name)
            if isinstance(provider_key, str) and provider_key in _KNOWN_PROVIDER_KEYS:
                return provider_key

    provider_use = getattr(model, "use", "")
    if provider_use.startswith("deerflow.models.claude_provider:") or provider_use.startswith(
        "langchain_anthropic:",
    ):
        return "anthropic"

    if provider_use.startswith("langchain_openai:"):
        return "openai-compatible"

    if provider_use.startswith("deerflow.models.openai_codex_provider:"):
        return "openai"

    return "openai"


def resolve_provider_label(provider_key: str) -> str:
    if provider_key == "anthropic":
        return "Anthropic API"
    if provider_key == "openai-compatible":
        return "OpenAI-Compatible API"
    return "OpenAI API"

