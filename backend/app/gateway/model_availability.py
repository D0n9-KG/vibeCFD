import os
from typing import Protocol

from deerflow.models.credential_loader import (
    load_claude_code_credential,
    load_codex_cli_credential,
    load_openai_api_credential,
)


class ModelConfigLike(Protocol):
    use: str


def _has_inline_secret(model: ModelConfigLike, *field_names: str) -> bool:
    for field_name in field_names:
        value = getattr(model, field_name, None)
        if isinstance(value, str) and value.strip():
            return True

    extra = getattr(model, "model_extra", None)
    if isinstance(extra, dict):
        for field_name in field_names:
            value = extra.get(field_name)
            if isinstance(value, str) and value.strip():
                return True

    return False


def resolve_model_availability(model: ModelConfigLike) -> tuple[bool, str | None]:
    provider = model.use

    if provider.startswith("deerflow.models.claude_provider:") or provider.startswith(
        "langchain_anthropic:",
    ):
        if _has_inline_secret(model, "anthropic_api_key", "api_key"):
            return True, None
        if os.getenv("ANTHROPIC_API_KEY") or load_claude_code_credential():
            return True, None
        return (
            False,
            "Anthropic / Claude credentials are not configured in this environment.",
        )

    if provider.startswith("deerflow.models.openai_codex_provider:"):
        if load_codex_cli_credential():
            return True, None
        return False, "Codex CLI credentials are not configured in this environment."

    if provider.startswith("deerflow.models.openai_cli_provider:"):
        if _has_inline_secret(model, "openai_api_key", "api_key"):
            return True, None
        if load_openai_api_credential():
            return True, None
        return False, "OpenAI / Codex API credentials are not configured in this environment."

    if provider.startswith("langchain_openai:"):
        if _has_inline_secret(model, "openai_api_key", "api_key"):
            return True, None
        if os.getenv("OPENAI_API_KEY"):
            return True, None
        return False, "OpenAI API credentials are not configured in this environment."

    return True, None
