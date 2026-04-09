"""Core behavior tests for TitleMiddleware."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from langchain_core.messages import AIMessage, HumanMessage

from deerflow.agents.middlewares.title_middleware import TitleMiddleware
from deerflow.config.title_config import TitleConfig, get_title_config, set_title_config


def _clone_title_config(config: TitleConfig) -> TitleConfig:
    return TitleConfig(**config.model_dump())


def _set_test_title_config(**overrides) -> TitleConfig:
    config = _clone_title_config(get_title_config())
    for key, value in overrides.items():
        setattr(config, key, value)
    set_title_config(config)
    return config


class TestTitleMiddlewareCoreLogic:
    def setup_method(self):
        self._original = _clone_title_config(get_title_config())

    def teardown_method(self):
        set_title_config(self._original)

    def test_should_generate_title_for_first_complete_exchange(self):
        _set_test_title_config(enabled=True)
        middleware = TitleMiddleware()
        state = {
            "messages": [
                HumanMessage(content="Help me summarize this codebase."),
                AIMessage(content="Sure, I will inspect the structure first."),
            ]
        }

        assert middleware._should_generate_title(state) is True

    def test_should_not_generate_title_when_disabled_or_already_set(self):
        middleware = TitleMiddleware()

        _set_test_title_config(enabled=False)
        disabled_state = {
            "messages": [HumanMessage(content="Q"), AIMessage(content="A")],
            "title": None,
        }
        assert middleware._should_generate_title(disabled_state) is False

        _set_test_title_config(enabled=True)
        titled_state = {
            "messages": [HumanMessage(content="Q"), AIMessage(content="A")],
            "title": "Existing Title",
        }
        assert middleware._should_generate_title(titled_state) is False

    def test_should_not_generate_title_after_second_user_turn(self):
        _set_test_title_config(enabled=True)
        middleware = TitleMiddleware()
        state = {
            "messages": [
                HumanMessage(content="First question"),
                AIMessage(content="First answer"),
                HumanMessage(content="Second question"),
                AIMessage(content="Second answer"),
            ]
        }

        assert middleware._should_generate_title(state) is False

    def test_generate_title_trims_quotes_and_respects_max_chars(self, monkeypatch):
        _set_test_title_config(max_chars=12)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.ainvoke = AsyncMock(return_value=MagicMock(content='"A very long generated title"'))
        monkeypatch.setattr("deerflow.agents.middlewares.title_middleware.create_chat_model", lambda **kwargs: fake_model)

        state = {
            "messages": [
                HumanMessage(content="Please help me write a script."),
                AIMessage(content="Sure, let me confirm the requirements first."),
            ]
        }
        result = asyncio.run(middleware._agenerate_title_result(state))
        title = result["title"]

        assert '"' not in title
        assert "'" not in title
        assert len(title) == 12

    def test_generate_title_normalizes_structured_message_and_response_content(self, monkeypatch):
        _set_test_title_config(max_chars=20)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.ainvoke = AsyncMock(
            return_value=MagicMock(content=[{"type": "text", "text": '"Structured Summary"'}]),
        )
        monkeypatch.setattr(
            "deerflow.agents.middlewares.title_middleware.create_chat_model",
            lambda **kwargs: fake_model,
        )

        state = {
            "messages": [
                HumanMessage(content=[{"type": "text", "text": "Please summarize this codebase."}]),
                AIMessage(content=[{"type": "text", "text": "Sure, I will inspect the structure first."}]),
            ]
        }

        result = asyncio.run(middleware._agenerate_title_result(state))
        title = result["title"]

        prompt = fake_model.ainvoke.await_args.args[0]
        assert "Please summarize this codebase." in prompt
        assert "Sure, I will inspect the structure first." in prompt
        assert "{'type':" not in prompt
        assert "'type':" not in prompt
        assert '"type":' not in prompt
        assert title == "Structured Summary"

    def test_generate_title_fallback_when_model_fails(self, monkeypatch):
        _set_test_title_config(max_chars=20)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.ainvoke = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        monkeypatch.setattr("deerflow.agents.middlewares.title_middleware.create_chat_model", lambda **kwargs: fake_model)

        state = {
            "messages": [
                HumanMessage(content="This is a very long prompt that should be truncated into a fallback title."),
                AIMessage(content="Received."),
            ]
        }
        result = asyncio.run(middleware._agenerate_title_result(state))
        title = result["title"]

        assert title.endswith("...")
        assert title.startswith("This is a very long")

    def test_generate_title_fallback_when_model_returns_placeholder_reply(self, monkeypatch):
        _set_test_title_config(max_chars=50)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.ainvoke = AsyncMock(
            return_value=MagicMock(
                content="I'll continue based on your latest request. If I need anything else, I'll ask clearly."
            )
        )
        monkeypatch.setattr(
            "deerflow.agents.middlewares.title_middleware.create_chat_model",
            lambda **kwargs: fake_model,
        )

        state = {
            "messages": [
                HumanMessage(content="Geometry preflight for SUBOFF STL with setup recommendations"),
                AIMessage(content="Working on it."),
            ]
        }

        result = asyncio.run(middleware._agenerate_title_result(state))

        assert result["title"] == "Geometry preflight for SUBOFF STL with setup recom..."

    def test_aafter_model_delegates_to_async_helper(self, monkeypatch):
        middleware = TitleMiddleware()

        monkeypatch.setattr(middleware, "_agenerate_title_result", AsyncMock(return_value={"title": "Async title"}))
        result = asyncio.run(middleware.aafter_model({"messages": []}, runtime=MagicMock()))
        assert result == {"title": "Async title"}

        monkeypatch.setattr(middleware, "_agenerate_title_result", AsyncMock(return_value=None))
        assert asyncio.run(middleware.aafter_model({"messages": []}, runtime=MagicMock())) is None

    def test_after_model_sync_delegates_to_sync_helper(self, monkeypatch):
        middleware = TitleMiddleware()

        monkeypatch.setattr(middleware, "_generate_title_result", MagicMock(return_value={"title": "Sync title"}))
        result = middleware.after_model({"messages": []}, runtime=MagicMock())
        assert result == {"title": "Sync title"}

        monkeypatch.setattr(middleware, "_generate_title_result", MagicMock(return_value=None))
        assert middleware.after_model({"messages": []}, runtime=MagicMock()) is None

    def test_sync_generate_title_with_model(self, monkeypatch):
        _set_test_title_config(max_chars=20)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.invoke = MagicMock(return_value=MagicMock(content='"Sync generated title"'))
        monkeypatch.setattr("deerflow.agents.middlewares.title_middleware.create_chat_model", lambda **kwargs: fake_model)

        state = {
            "messages": [
                HumanMessage(content="Please help me write tests"),
                AIMessage(content="Okay."),
            ]
        }
        result = middleware._generate_title_result(state)
        assert result == {"title": "Sync generated title"}
        fake_model.invoke.assert_called_once()

    def test_empty_title_falls_back(self, monkeypatch):
        _set_test_title_config(max_chars=50)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.invoke = MagicMock(return_value=MagicMock(content="   "))
        monkeypatch.setattr("deerflow.agents.middlewares.title_middleware.create_chat_model", lambda **kwargs: fake_model)

        state = {
            "messages": [
                HumanMessage(content="Empty title fallback test"),
                AIMessage(content="Reply"),
            ]
        }
        result = middleware._generate_title_result(state)
        assert result["title"] == "Empty title fallback test"
