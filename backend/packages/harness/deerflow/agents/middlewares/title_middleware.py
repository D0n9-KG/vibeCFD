"""Middleware for automatic thread title generation."""

import logging
import re
from typing import NotRequired, override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langgraph.runtime import Runtime

from deerflow.config.title_config import get_title_config
from deerflow.models import create_chat_model

logger = logging.getLogger(__name__)


class TitleMiddlewareState(AgentState):
    """Compatible with the `ThreadState` schema."""

    title: NotRequired[str | None]


class TitleMiddleware(AgentMiddleware[TitleMiddlewareState]):
    """Automatically generate a title for the thread after the first user message."""

    state_schema = TitleMiddlewareState
    _UPLOAD_BLOCK_RE = re.compile(
        r"<uploaded_files>[\s\S]*?</uploaded_files>\n*",
        re.IGNORECASE,
    )
    _UPLOAD_FILENAME_RE = re.compile(r"^\s*-\s+([^\n(]+?)\s*\([^)]*\)\s*$", re.MULTILINE)
    _TRAILING_ORPHAN_PUNCTUATION_RE = re.compile(r"[;；]+[.。!！?？]*$")
    _PLACEHOLDER_TITLES = {
        "I'll continue based on your latest request. If I need anything else, I'll ask clearly.",
        "\u6211\u5148\u6839\u636e\u4f60\u521a\u624d\u7684\u8f93\u5165\u7ee7\u7eed\u63a8\u8fdb\uff1b\u5982\u679c\u9700\u8981\u4f60\u8865\u5145\u4fe1\u606f\uff0c\u6211\u4f1a\u660e\u786e\u544a\u8bc9\u4f60\u3002",
    }

    def _normalize_content(self, content: object) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = [self._normalize_content(item) for item in content]
            return "\n".join(part for part in parts if part)

        if isinstance(content, dict):
            text_value = content.get("text")
            if isinstance(text_value, str):
                return text_value

            nested_content = content.get("content")
            if nested_content is not None:
                return self._normalize_content(nested_content)

        return ""

    def _extract_uploaded_filenames(self, content: str) -> list[str]:
        return [
            match.group(1).strip()
            for match in self._UPLOAD_FILENAME_RE.finditer(content)
            if match.group(1).strip()
        ]

    def _clean_user_message(self, content: object) -> str:
        normalized = self._normalize_content(content)
        visible_content = self._UPLOAD_BLOCK_RE.sub("", normalized).strip()
        if visible_content:
            return visible_content

        uploaded_filenames = self._extract_uploaded_filenames(normalized)
        if not uploaded_filenames:
            return ""

        visible_filenames = uploaded_filenames[:2]
        if len(uploaded_filenames) == 1:
            return f"Uploaded {visible_filenames[0]}"

        preview = ", ".join(visible_filenames)
        remaining = len(uploaded_filenames) - len(visible_filenames)
        if remaining > 0:
            return f"Uploaded {preview} and {remaining} more files"
        return f"Uploaded {preview}"

    def _sanitize_title_text(self, text: str) -> str:
        normalized = text.strip().strip('"').strip("'").strip()
        normalized = self._TRAILING_ORPHAN_PUNCTUATION_RE.sub("", normalized)
        return normalized.strip()

    def _should_generate_title(self, state: TitleMiddlewareState) -> bool:
        """Check if we should generate a title for this thread."""
        config = get_title_config()
        if not config.enabled:
            return False

        # Check if thread already has a title in state
        if state.get("title"):
            return False

        # Check if this is the first turn (has at least one user message and one assistant response)
        messages = state.get("messages", [])
        if len(messages) < 2:
            return False

        # Count user and assistant messages
        user_messages = [m for m in messages if m.type == "human"]
        assistant_messages = [m for m in messages if m.type == "ai"]

        # Generate title after first complete exchange
        return len(user_messages) == 1 and len(assistant_messages) >= 1

    def _build_title_prompt(self, state: TitleMiddlewareState) -> tuple[str, str]:
        """Extract user/assistant messages and build the title prompt.

        Returns (prompt_string, user_msg) so callers can use user_msg as fallback.
        """
        config = get_title_config()
        messages = state.get("messages", [])

        user_msg_content = next((m.content for m in messages if m.type == "human"), "")
        assistant_msg_content = next((m.content for m in messages if m.type == "ai"), "")

        user_msg = self._clean_user_message(user_msg_content)
        assistant_msg = self._normalize_content(assistant_msg_content)

        prompt = config.prompt_template.format(
            max_words=config.max_words,
            user_msg=user_msg[:500],
            assistant_msg=assistant_msg[:500],
        )
        return prompt, user_msg

    def _parse_title(self, content: object) -> str:
        """Normalize model output into a clean title string."""
        config = get_title_config()
        title_content = self._normalize_content(content)
        title = self._sanitize_title_text(title_content)
        return title[: config.max_chars] if len(title) > config.max_chars else title

    def _looks_like_placeholder_title(self, title: str) -> bool:
        normalized = title.strip()
        return any(
            normalized == placeholder
            or placeholder.startswith(normalized)
            or normalized.startswith(placeholder)
            for placeholder in self._PLACEHOLDER_TITLES
        )

    def _fallback_title(self, user_msg: str) -> str:
        config = get_title_config()
        cleaned_user_msg = self._sanitize_title_text(self._clean_user_message(user_msg))
        fallback_chars = min(config.max_chars, 50)
        if len(cleaned_user_msg) > fallback_chars:
            return cleaned_user_msg[:fallback_chars].rstrip() + "..."
        return cleaned_user_msg if cleaned_user_msg else "New Conversation"

    def _generate_title_result(self, state: TitleMiddlewareState) -> dict | None:
        """Synchronously generate a title. Returns state update or None."""
        if not self._should_generate_title(state):
            return None

        prompt, user_msg = self._build_title_prompt(state)
        config = get_title_config()
        model = create_chat_model(name=config.model_name, thinking_enabled=False)

        try:
            response = model.invoke(prompt)
            title = self._parse_title(response.content)
            if not title or self._looks_like_placeholder_title(title):
                title = self._fallback_title(user_msg)
        except Exception:
            logger.exception("Failed to generate title (sync)")
            title = self._fallback_title(user_msg)

        return {"title": title}

    async def _agenerate_title_result(self, state: TitleMiddlewareState) -> dict | None:
        """Asynchronously generate a title. Returns state update or None."""
        if not self._should_generate_title(state):
            return None

        prompt, user_msg = self._build_title_prompt(state)
        config = get_title_config()
        model = create_chat_model(name=config.model_name, thinking_enabled=False)

        try:
            response = await model.ainvoke(prompt)
            title = self._parse_title(response.content)
            if not title or self._looks_like_placeholder_title(title):
                title = self._fallback_title(user_msg)
        except Exception:
            logger.exception("Failed to generate title (async)")
            title = self._fallback_title(user_msg)

        return {"title": title}

    @override
    def after_model(self, state: TitleMiddlewareState, runtime: Runtime) -> dict | None:
        return self._generate_title_result(state)

    @override
    async def aafter_model(self, state: TitleMiddlewareState, runtime: Runtime) -> dict | None:
        return await self._agenerate_title_result(state)
