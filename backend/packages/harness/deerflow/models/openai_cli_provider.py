"""Thin ChatOpenAI wrapper that auto-loads OpenAI API keys from Codex auth."""

import logging
from typing import Any

from langchain_openai import ChatOpenAI

from deerflow.models.credential_loader import load_openai_api_credential

logger = logging.getLogger(__name__)


class OpenAICliChatModel(ChatOpenAI):
    """ChatOpenAI with local OpenAI/Codex auth handoff support."""

    model_config = {"arbitrary_types_allowed": True}

    def model_post_init(self, __context: Any) -> None:
        from pydantic import SecretStr

        current_key = ""
        if self.openai_api_key:
            if hasattr(self.openai_api_key, "get_secret_value"):
                current_key = self.openai_api_key.get_secret_value()
            else:
                current_key = str(self.openai_api_key)

        if not current_key or current_key in ("your-openai-api-key",):
            cred = load_openai_api_credential()
            if cred:
                current_key = cred.api_key
                if cred.base_url and not self.openai_api_base:
                    self.openai_api_base = cred.base_url
                logger.info("Using OpenAI API credential (source: %s)", cred.source)
            else:
                raise ValueError(
                    "OpenAI API credential not found. Expected OPENAI_API_KEY or ~/.codex/auth.json."
                )

        self.openai_api_key = SecretStr(current_key)
        super().model_post_init(__context)
