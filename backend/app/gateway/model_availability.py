import os
from typing import Protocol

from deerflow.models.credential_loader import (
    load_claude_code_credential,
    load_codex_cli_credential,
)


class ModelConfigLike(Protocol):
    use: str


def resolve_model_availability(model: ModelConfigLike) -> tuple[bool, str | None]:
    provider = model.use

    if provider.startswith("deerflow.models.claude_provider:") or provider.startswith(
        "langchain_anthropic:",
    ):
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

    if provider.startswith("langchain_openai:"):
        if os.getenv("OPENAI_API_KEY"):
            return True, None
        return False, "OpenAI API credentials are not configured in this environment."

    return True, None
