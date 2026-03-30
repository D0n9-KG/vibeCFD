from __future__ import annotations

import json

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from deerflow.models.claude_provider import ClaudeChatModel
from deerflow.models.credential_loader import ClaudeCodeCredential, CodexCliCredential, OpenAIApiCredential
from deerflow.models.openai_cli_provider import OpenAICliChatModel
from deerflow.models.openai_codex_provider import CodexChatModel


def test_codex_provider_rejects_non_positive_retry_attempts():
    with pytest.raises(ValueError, match="retry_max_attempts must be >= 1"):
        CodexChatModel(retry_max_attempts=0)


def test_codex_provider_requires_credentials(monkeypatch):
    monkeypatch.setattr(CodexChatModel, "_load_codex_auth", lambda self: None)

    with pytest.raises(ValueError, match="Codex CLI credential not found"):
        CodexChatModel()


def test_codex_provider_concatenates_multiple_system_messages(monkeypatch):
    monkeypatch.setattr(
        CodexChatModel,
        "_load_codex_auth",
        lambda self: CodexCliCredential(access_token="token", account_id="acct"),
    )

    model = CodexChatModel()
    instructions, input_items = model._convert_messages(
        [
            SystemMessage(content="First system prompt."),
            SystemMessage(content="Second system prompt."),
            HumanMessage(content="Hello"),
        ]
    )

    assert instructions == "First system prompt.\n\nSecond system prompt."
    assert input_items == [{"role": "user", "content": "Hello"}]


def test_codex_provider_flattens_structured_text_blocks(monkeypatch):
    monkeypatch.setattr(
        CodexChatModel,
        "_load_codex_auth",
        lambda self: CodexCliCredential(access_token="token", account_id="acct"),
    )

    model = CodexChatModel()
    instructions, input_items = model._convert_messages(
        [
            HumanMessage(content=[{"type": "text", "text": "Hello from blocks"}]),
        ]
    )

    assert instructions == "You are a helpful assistant."
    assert input_items == [{"role": "user", "content": "Hello from blocks"}]


def test_claude_provider_rejects_non_positive_retry_attempts():
    with pytest.raises(ValueError, match="retry_max_attempts must be >= 1"):
        ClaudeChatModel(model="claude-sonnet-4-6", retry_max_attempts=0)


def test_claude_provider_applies_base_url_from_loaded_settings(monkeypatch):
    monkeypatch.setattr(
        "deerflow.models.credential_loader.load_claude_code_credential",
        lambda: ClaudeCodeCredential(
            access_token="settings-auth-token",
            base_url="https://example.invalid",
            source="claude-cli-settings",
        ),
    )

    model = ClaudeChatModel(model="claude-sonnet-4-6")

    assert model.anthropic_api_url == "https://example.invalid"


def test_openai_cli_provider_requires_credentials(monkeypatch):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: None,
    )

    with pytest.raises(ValueError, match="OpenAI API credential not found"):
        OpenAICliChatModel(model="gpt-5.4")


def test_openai_cli_provider_uses_loaded_api_key(monkeypatch):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4")

    assert model.openai_api_key is not None
    assert model.openai_api_key.get_secret_value() == "sk-openai-test"


def test_openai_cli_provider_applies_loaded_base_url(monkeypatch):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            base_url="https://gateway.example/v1",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4")

    assert model.openai_api_base == "https://gateway.example/v1"


def test_codex_provider_skips_terminal_sse_markers(monkeypatch):
    monkeypatch.setattr(
        CodexChatModel,
        "_load_codex_auth",
        lambda self: CodexCliCredential(access_token="token", account_id="acct"),
    )

    model = CodexChatModel()

    assert model._parse_sse_data_line("data: [DONE]") is None
    assert model._parse_sse_data_line("event: response.completed") is None


def test_codex_provider_skips_non_json_sse_frames(monkeypatch):
    monkeypatch.setattr(
        CodexChatModel,
        "_load_codex_auth",
        lambda self: CodexCliCredential(access_token="token", account_id="acct"),
    )

    model = CodexChatModel()

    assert model._parse_sse_data_line("data: not-json") is None


def test_codex_provider_marks_invalid_tool_call_arguments(monkeypatch):
    monkeypatch.setattr(
        CodexChatModel,
        "_load_codex_auth",
        lambda self: CodexCliCredential(access_token="token", account_id="acct"),
    )

    model = CodexChatModel()
    result = model._parse_response(
        {
            "model": "gpt-5.4",
            "output": [
                {
                    "type": "function_call",
                    "name": "bash",
                    "arguments": "{invalid",
                    "call_id": "tc-1",
                }
            ],
            "usage": {},
        }
    )

    message = result.generations[0].message
    assert message.tool_calls == []
    assert len(message.invalid_tool_calls) == 1
    assert message.invalid_tool_calls[0]["type"] == "invalid_tool_call"
    assert message.invalid_tool_calls[0]["name"] == "bash"
    assert message.invalid_tool_calls[0]["args"] == "{invalid"
    assert message.invalid_tool_calls[0]["id"] == "tc-1"
    assert "Failed to parse tool arguments" in message.invalid_tool_calls[0]["error"]


def test_codex_provider_parses_valid_tool_arguments(monkeypatch):
    monkeypatch.setattr(
        CodexChatModel,
        "_load_codex_auth",
        lambda self: CodexCliCredential(access_token="token", account_id="acct"),
    )

    model = CodexChatModel()
    result = model._parse_response(
        {
            "model": "gpt-5.4",
            "output": [
                {
                    "type": "function_call",
                    "name": "bash",
                    "arguments": json.dumps({"cmd": "pwd"}),
                    "call_id": "tc-1",
                }
            ],
            "usage": {},
        }
    )

    assert result.generations[0].message.tool_calls == [
        {"name": "bash", "args": {"cmd": "pwd"}, "id": "tc-1", "type": "tool_call"}
    ]
