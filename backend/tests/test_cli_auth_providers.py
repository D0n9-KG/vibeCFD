from __future__ import annotations

import json
import asyncio
import types
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

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


def test_openai_cli_provider_parses_sse_text_response(monkeypatch):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")

    sse_payload = "\n\n".join(
        [
            "event: response.created\ndata: "
            + json.dumps(
                {
                    "type": "response.created",
                    "response": {
                        "id": "resp_123",
                        "model": "gpt-5.4",
                        "output": [],
                        "usage": {},
                    },
                }
            ),
            "event: response.completed\ndata: "
            + json.dumps(
                {
                    "type": "response.completed",
                    "response": {
                        "id": "resp_123",
                        "model": "gpt-5.4",
                        "output": [
                            {
                                "type": "message",
                                "role": "assistant",
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": "DEFAULT_OK",
                                        "annotations": [],
                                    }
                                ],
                            }
                        ],
                        "usage": {
                            "input_tokens": 12,
                            "output_tokens": 3,
                            "total_tokens": 15,
                        },
                    },
                }
            ),
        ]
    )

    normalized = model._normalize_responses_api_response(sse_payload)
    result = model._build_chat_result_from_response_dict(normalized)

    assert result.generations[0].message.content == "DEFAULT_OK"
    assert result.llm_output["token_usage"] == {
        "prompt_tokens": 12,
        "completion_tokens": 3,
        "total_tokens": 15,
    }


def test_openai_cli_provider_parses_sse_tool_response(monkeypatch):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")

    sse_payload = "\n\n".join(
        [
            "event: response.created\ndata: "
            + json.dumps(
                {
                    "type": "response.created",
                    "response": {
                        "id": "resp_tool",
                        "model": "gpt-5.4",
                        "output": [],
                        "usage": {},
                    },
                }
            ),
            "event: response.completed\ndata: "
            + json.dumps(
                {
                    "type": "response.completed",
                    "response": {
                        "id": "resp_tool",
                        "model": "gpt-5.4",
                        "output": [
                            {
                                "type": "function_call",
                                "name": "echo_text",
                                "arguments": json.dumps({"text": "DEFAULT_OK"}),
                                "call_id": "call_123",
                            }
                        ],
                        "usage": {
                            "input_tokens": 22,
                            "output_tokens": 8,
                            "total_tokens": 30,
                        },
                    },
                }
            ),
        ]
    )

    normalized = model._normalize_responses_api_response(sse_payload)
    result = model._build_chat_result_from_response_dict(normalized)

    assert result.generations[0].message.tool_calls == [
        {
            "name": "echo_text",
            "args": {"text": "DEFAULT_OK"},
            "id": "call_123",
            "type": "tool_call",
        }
    ]


def test_openai_cli_provider_generate_handles_sse_string_response(monkeypatch):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")

    sse_payload = "\n\n".join(
        [
            "event: response.created\ndata: "
            + json.dumps(
                {
                    "type": "response.created",
                    "response": {
                        "id": "resp_456",
                        "model": "gpt-5.4",
                        "output": [],
                        "usage": {},
                    },
                }
            ),
            "event: response.completed\ndata: "
            + json.dumps(
                {
                    "type": "response.completed",
                    "response": {
                        "id": "resp_456",
                        "model": "gpt-5.4",
                        "output": [
                            {
                                "type": "message",
                                "role": "assistant",
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": "DEFAULT_OK",
                                        "annotations": [],
                                    }
                                ],
                            }
                        ],
                        "usage": {
                            "input_tokens": 12,
                            "output_tokens": 3,
                            "total_tokens": 15,
                        },
                    },
                }
            ),
        ]
    )

    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(create=lambda **_: sse_payload),
    )

    result = model._generate([HumanMessage(content="Reply with exactly DEFAULT_OK")])

    assert result.generations[0].message.content == "DEFAULT_OK"


def test_openai_cli_provider_stream_uses_non_stream_fallback(monkeypatch):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    chat_result = ChatResult(
        generations=[
            ChatGeneration(
                message=AIMessage(
                    content="DEFAULT_OK",
                    response_metadata={
                        "model": "gpt-5.4",
                        "usage": {"input_tokens": 12, "output_tokens": 3, "total_tokens": 15},
                    },
                )
            )
        ],
        llm_output={"model_name": "gpt-5.4"},
    )

    monkeypatch.setattr(
        model,
        "_generate",
        lambda messages, stop=None, run_manager=None, **kwargs: chat_result,
    )

    chunks = list(model._stream([HumanMessage(content="Reply with exactly DEFAULT_OK")]))

    assert len(chunks) == 1
    assert chunks[0].message.content == "DEFAULT_OK"
    assert chunks[0].message.chunk_position == "last"


def test_openai_cli_provider_astream_uses_non_stream_fallback(monkeypatch):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    chat_result = ChatResult(
        generations=[
            ChatGeneration(
                message=AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "echo_text",
                            "args": {"text": "DEFAULT_OK"},
                            "id": "call_123",
                            "type": "tool_call",
                        }
                    ],
                    response_metadata={
                        "model": "gpt-5.4",
                        "usage": {"input_tokens": 22, "output_tokens": 8, "total_tokens": 30},
                    },
                )
            )
        ],
        llm_output={"model_name": "gpt-5.4"},
    )

    async def _fake_agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        return chat_result

    monkeypatch.setattr(model, "_agenerate", types.MethodType(_fake_agenerate, model))

    async def _collect():
        collected = []
        async for chunk in model._astream([HumanMessage(content="Call echo_text with text DEFAULT_OK")]):
            collected.append(chunk)
        return collected

    chunks = asyncio.run(_collect())

    assert len(chunks) == 1
    assert chunks[0].message.tool_calls == [
        {
            "name": "echo_text",
            "args": {"text": "DEFAULT_OK"},
            "id": "call_123",
            "type": "tool_call",
        }
    ]


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
