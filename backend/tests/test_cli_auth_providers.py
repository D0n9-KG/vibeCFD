from __future__ import annotations

import json
import asyncio
import types
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
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


def test_codex_provider_emits_visible_fallback_for_empty_final_response(monkeypatch):
    monkeypatch.setattr(
        CodexChatModel,
        "_load_codex_auth",
        lambda self: CodexCliCredential(access_token="token", account_id="acct"),
    )

    model = CodexChatModel()
    monkeypatch.setattr(
        model,
        "_call_codex_api",
        lambda messages, tools=None: {
            "model": "gpt-5.4",
            "usage": {
                "input_tokens": 12,
                "output_tokens": 3,
                "total_tokens": 15,
            },
            "output": [],
        },
    )

    result = model._generate(
        [
            HumanMessage(
                content=(
                    "<uploaded_files>\n"
                    "The following files were uploaded in this message:\n"
                    "- suboff_solid.stl (1.6 MB)\n"
                    "</uploaded_files>\n\n"
                    "请先对这个 STL 做几何可用性预检。"
                )
            )
        ]
    )

    assert (
        result.generations[0].message.content
        == "我先根据你刚才的输入继续推进；如果需要你补充信息，我会明确告诉你。"
    )


def test_codex_provider_does_not_inject_fallback_for_tool_call_only_response(
    monkeypatch,
):
    monkeypatch.setattr(
        CodexChatModel,
        "_load_codex_auth",
        lambda self: CodexCliCredential(access_token="token", account_id="acct"),
    )

    model = CodexChatModel()
    monkeypatch.setattr(
        model,
        "_call_codex_api",
        lambda messages, tools=None: {
            "model": "gpt-5.4",
            "usage": {
                "input_tokens": 12,
                "output_tokens": 3,
                "total_tokens": 15,
            },
            "output": [
                {
                    "type": "function_call",
                    "name": "submarine_geometry_check",
                    "call_id": "call_123",
                    "arguments": "{}",
                }
            ],
        },
    )

    result = model._generate([HumanMessage(content="Inspect this STL.")])

    assert result.generations[0].message.content == ""
    assert result.generations[0].message.tool_calls == [
        {
            "name": "submarine_geometry_check",
            "args": {},
            "id": "call_123",
            "type": "tool_call",
        }
    ]


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


def test_openai_cli_provider_emits_visible_fallback_for_empty_final_response(monkeypatch):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )
    monkeypatch.setattr(
        OpenAICliChatModel,
        "_retry_empty_response_with_alternate_model",
        lambda self, messages, stop=None, run_manager=None, **kwargs: None,
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [
                    {
                        "type": "message",
                        "content": [],
                    }
                ],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    result = model._generate([HumanMessage(content="Please keep going with the STL check.")])

    assert result.generations[0].message.content == "I'll continue based on your latest request. If I need anything else, I'll ask clearly."


def test_openai_cli_provider_retries_empty_response_with_alternate_model_text(monkeypatch):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    monkeypatch.setattr(
        OpenAICliChatModel,
        "_retry_empty_response_with_alternate_model",
        lambda self, messages, stop=None, run_manager=None, **kwargs: ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(
                        content="DEFAULT_OK",
                        response_metadata={
                            "model": "claude-sonnet-4-6",
                            "usage": {
                                "input_tokens": 11,
                                "output_tokens": 2,
                                "total_tokens": 13,
                            },
                        },
                    )
                )
            ],
            llm_output={"model_name": "claude-sonnet-4-6"},
        ),
        raising=False,
    )

    result = model._generate([HumanMessage(content="Please keep going with the skill draft.")])

    assert result.generations[0].message.content == "DEFAULT_OK"
    assert result.generations[0].message.tool_calls == []


def test_openai_cli_provider_retries_empty_response_with_alternate_model_tool_call(
    monkeypatch,
):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    monkeypatch.setattr(
        OpenAICliChatModel,
        "_retry_empty_response_with_alternate_model",
        lambda self, messages, stop=None, run_manager=None, **kwargs: ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "submarine_skill_studio",
                                "args": {
                                    "skill_name": "pipeline-check",
                                    "skill_purpose": "Verify Skill Studio end-to-end flow",
                                },
                                "id": "tool_123",
                                "type": "tool_call",
                            }
                        ],
                        response_metadata={
                            "model": "claude-sonnet-4-6",
                            "usage": {
                                "input_tokens": 21,
                                "output_tokens": 8,
                                "total_tokens": 29,
                            },
                        },
                    )
                )
            ],
            llm_output={"model_name": "claude-sonnet-4-6"},
        ),
        raising=False,
    )

    result = model._generate([HumanMessage(content="Please draft the test skill now.")])

    assert result.generations[0].message.content == ""
    assert result.generations[0].message.tool_calls == [
        {
            "name": "submarine_skill_studio",
            "args": {
                "skill_name": "pipeline-check",
                "skill_purpose": "Verify Skill Studio end-to-end flow",
            },
            "id": "tool_123",
            "type": "tool_call",
        }
    ]


def test_openai_cli_provider_ignores_hidden_only_alternate_retry_and_keeps_fallback(
    monkeypatch,
):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    class _HiddenOnlyAlternate:
        def _generate(self, messages, stop=None, run_manager=None):
            return ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(
                            content=[{"type": "thinking", "thinking": "internal deliberation"}],
                            response_metadata={
                                "model": "claude-sonnet-4-6",
                                "usage": {
                                    "input_tokens": 10,
                                    "output_tokens": 5,
                                    "total_tokens": 15,
                                },
                            },
                        )
                    )
                ],
                llm_output={"model_name": "claude-sonnet-4-6"},
            )

    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.get_app_config",
        lambda: SimpleNamespace(
            models=[
                SimpleNamespace(name="gpt-5.4", use="deerflow.models.openai_cli_provider:OpenAICliChatModel"),
                SimpleNamespace(name="claude-sonnet-4-6", use="deerflow.models.claude_provider:ClaudeChatModel"),
            ]
        ),
    )
    monkeypatch.setattr(
        "deerflow.models.factory.create_chat_model",
        lambda name, thinking_enabled=False, reasoning_effort=None: _HiddenOnlyAlternate(),
    )

    result = model._generate([HumanMessage(content="Please keep going with the skill draft.")])

    assert (
        result.generations[0].message.content
        == "I'll continue based on your latest request. If I need anything else, I'll ask clearly."
    )
    assert result.generations[0].message.tool_calls == []


def test_openai_cli_provider_ignores_invalid_tool_only_alternate_retry_and_keeps_fallback(
    monkeypatch,
):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    class _InvalidToolOnlyAlternate:
        def _generate(self, messages, stop=None, run_manager=None):
            return ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(
                            content="",
                            invalid_tool_calls=[
                                {
                                    "type": "invalid_tool_call",
                                    "name": "submarine_skill_studio",
                                    "args": "{bad json",
                                    "id": "invalid-tool-1",
                                    "error": "Failed to parse tool arguments",
                                }
                            ],
                            response_metadata={
                                "model": "claude-sonnet-4-6",
                                "usage": {
                                    "input_tokens": 10,
                                    "output_tokens": 5,
                                    "total_tokens": 15,
                                },
                            },
                        )
                    )
                ],
                llm_output={"model_name": "claude-sonnet-4-6"},
            )

    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.get_app_config",
        lambda: SimpleNamespace(
            models=[
                SimpleNamespace(name="gpt-5.4", use="deerflow.models.openai_cli_provider:OpenAICliChatModel"),
                SimpleNamespace(name="claude-sonnet-4-6", use="deerflow.models.claude_provider:ClaudeChatModel"),
            ]
        ),
    )
    monkeypatch.setattr(
        "deerflow.models.factory.create_chat_model",
        lambda name, thinking_enabled=False, reasoning_effort=None: _InvalidToolOnlyAlternate(),
    )

    result = model._generate([HumanMessage(content="Please keep going with the skill draft.")])

    assert (
        result.generations[0].message.content
        == "I'll continue based on your latest request. If I need anything else, I'll ask clearly."
    )
    assert result.generations[0].message.tool_calls == []


def test_openai_cli_provider_injects_submarine_geometry_tool_call_for_empty_plan_only_stl_request(
    monkeypatch,
):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [
                    {
                        "type": "message",
                        "content": [],
                    }
                ],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    result = model._generate(
        [
            HumanMessage(
                content=(
                    "<uploaded_files>\n"
                    "The following files were uploaded in this message:\n"
                    "- suboff_solid.stl (1.6 MB)\n"
                    "</uploaded_files>\n\n"
                    "请先对这个 STL 做几何可用性预检，确认尺度、封闭性与是否适合做 SUBOFF 裸艇阻力基线研究；当前不要启动求解。"
                ),
                additional_kwargs={
                    "files": [
                        {
                            "filename": "suboff_solid.stl",
                            "path": "/mnt/user-data/uploads/suboff_solid.stl",
                            "status": "uploaded",
                        }
                    ]
                },
            )
        ]
    )

    assert result.generations[0].message.content == ""
    assert result.generations[0].message.tool_calls == [
        {
            "name": "submarine_geometry_check",
            "args": {
                "geometry_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "task_description": "请先对这个 STL 做几何可用性预检，确认尺度、封闭性与是否适合做 SUBOFF 裸艇阻力基线研究；当前不要启动求解。",
                "task_type": "resistance",
                "geometry_family_hint": "DARPA SUBOFF",
            },
            "id": "fallback_submarine_geometry_check_0",
            "type": "tool_call",
        }
    ]


def test_openai_cli_provider_recovers_geometry_tool_call_after_wrong_intermediate_tools(
    monkeypatch,
):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )
    monkeypatch.setattr(
        OpenAICliChatModel,
        "_retry_empty_response_with_alternate_model",
        lambda self, messages, stop=None, run_manager=None, **kwargs: None,
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [
                    {
                        "type": "message",
                        "content": [],
                    }
                ],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    result = model._generate(
        [
            HumanMessage(
                content=(
                    "<uploaded_files>\n"
                    "The following files were uploaded in this message:\n"
                    "- suboff_solid.stl (1.6 MB)\n"
                    "</uploaded_files>\n\n"
                    "Please do a geometry preflight on this STL and hold solver execution."
                ),
                additional_kwargs={
                    "files": [
                        {
                            "filename": "suboff_solid.stl",
                            "path": "/mnt/user-data/uploads/suboff_solid.stl",
                            "status": "uploaded",
                        }
                    ]
                },
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "read_file",
                        "args": {"path": "/mnt/user-data/uploads/suboff_solid.stl"},
                        "id": "call_read_file",
                        "type": "tool_call",
                    },
                    {
                        "name": "bash",
                        "args": {"command": "mesh-info /mnt/user-data/uploads/suboff_solid.stl"},
                        "id": "call_bash",
                        "type": "tool_call",
                    },
                ],
            ),
            ToolMessage(
                content="solid suboff_solid",
                tool_call_id="call_read_file",
                name="read_file",
            ),
            ToolMessage(
                content="triangles: 2048",
                tool_call_id="call_bash",
                name="bash",
            ),
        ]
    )

    assert result.generations[0].message.content == ""
    assert result.generations[0].message.tool_calls == [
        {
            "name": "submarine_geometry_check",
            "args": {
                "geometry_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "task_description": "Please do a geometry preflight on this STL and hold solver execution.",
                "task_type": "resistance",
            },
            "id": "fallback_submarine_geometry_check_0",
            "type": "tool_call",
        }
    ]


def test_openai_cli_provider_recovers_geometry_tool_call_after_later_non_stl_attachment(
    monkeypatch,
):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )
    monkeypatch.setattr(
        OpenAICliChatModel,
        "_retry_empty_response_with_alternate_model",
        lambda self, messages, stop=None, run_manager=None, **kwargs: None,
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [
                    {
                        "type": "message",
                        "content": [],
                    }
                ],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    result = model._generate(
        [
            HumanMessage(
                content=(
                    "<uploaded_files>\n"
                    "The following files were uploaded in this message:\n"
                    "- suboff_solid.stl (1.6 MB)\n"
                    "</uploaded_files>\n\n"
                    "Please do a SUBOFF geometry preflight on this STL and hold solver execution."
                ),
                additional_kwargs={
                    "files": [
                        {
                            "filename": "suboff_solid.stl",
                            "path": "/mnt/user-data/uploads/suboff_solid.stl",
                            "status": "uploaded",
                        }
                    ]
                },
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "read_file",
                        "args": {"path": "/mnt/user-data/uploads/suboff_solid.stl"},
                        "id": "call_read_file",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content="solid suboff_solid",
                tool_call_id="call_read_file",
                name="read_file",
            ),
            HumanMessage(
                content=(
                    "<uploaded_files>\n"
                    "The following files were uploaded in this message:\n"
                    "- notes.txt (1 KB)\n"
                    "</uploaded_files>\n\n"
                    "Please continue the SUBOFF geometry preflight on the uploaded STL and hold solver execution."
                ),
                additional_kwargs={
                    "files": [
                        {
                            "filename": "notes.txt",
                            "path": "/mnt/user-data/uploads/notes.txt",
                            "status": "uploaded",
                        }
                    ]
                },
            ),
        ]
    )

    assert result.generations[0].message.content == ""
    assert result.generations[0].message.tool_calls == [
        {
            "name": "submarine_geometry_check",
            "args": {
                "geometry_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "task_description": "Please continue the SUBOFF geometry preflight on the uploaded STL and hold solver execution.",
                "task_type": "resistance",
                "geometry_family_hint": "DARPA SUBOFF",
            },
            "id": "fallback_submarine_geometry_check_0",
            "type": "tool_call",
        }
    ]


def test_openai_cli_provider_injects_confirmed_design_brief_after_geometry_confirmation_reply(
    monkeypatch,
):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )
    monkeypatch.setattr(
        OpenAICliChatModel,
        "_retry_empty_response_with_alternate_model",
        lambda self, messages, stop=None, run_manager=None, **kwargs: None,
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [
                    {
                        "type": "message",
                        "content": [],
                    }
                ],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    confirmation_text = (
        "我确认参考长度取 4.356 m，参考面积取 0.370988 m^2。"
        "请继续完成几何预检，并基于 DARPA SUBOFF 裸艇 5 m/s 阻力基线给出下一步工况草案。"
    )

    result = model._generate(
        [
            HumanMessage(
                content=(
                    "<uploaded_files>\n"
                    "The following files were uploaded in this message:\n"
                    "- suboff_solid.stl (1.6 MB)\n"
                    "</uploaded_files>\n\n"
                    "Please do a geometry preflight on this STL and hold solver execution."
                ),
                additional_kwargs={
                    "files": [
                        {
                            "filename": "suboff_solid.stl",
                            "path": "/mnt/user-data/uploads/suboff_solid.stl",
                            "status": "uploaded",
                        }
                    ]
                },
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "submarine_geometry_check",
                        "args": {
                            "geometry_path": "/mnt/user-data/uploads/suboff_solid.stl",
                            "task_description": "geometry preflight",
                            "task_type": "resistance",
                            "geometry_family_hint": "DARPA SUBOFF bare hull",
                        },
                        "id": "fallback_submarine_geometry_check_0",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content=(
                    "Geometry preflight complete.\n"
                    "Please confirm the reference length and reference area before proceeding."
                ),
                tool_call_id="fallback_submarine_geometry_check_0",
                name="submarine_geometry_check",
            ),
            HumanMessage(content=confirmation_text),
        ]
    )

    assert result.generations[0].message.content == ""
    assert result.generations[0].message.tool_calls == [
        {
            "name": "submarine_design_brief",
            "args": {
                "task_description": confirmation_text,
                "geometry_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "task_type": "resistance",
                "confirmation_status": "confirmed",
                "geometry_family_hint": "DARPA SUBOFF",
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "inlet_velocity_mps": 5.0,
            },
            "id": "fallback_submarine_design_brief_0",
            "type": "tool_call",
        }
    ]


def test_openai_cli_provider_recovers_confirmed_design_brief_after_later_non_stl_attachment(
    monkeypatch,
):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )
    monkeypatch.setattr(
        OpenAICliChatModel,
        "_retry_empty_response_with_alternate_model",
        lambda self, messages, stop=None, run_manager=None, **kwargs: None,
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [
                    {
                        "type": "message",
                        "content": [],
                    }
                ],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    confirmation_text = (
        "I confirm reference length 4.356 m and reference area 0.370988 m^2. "
        "Please continue with the SUBOFF 5 m/s baseline plan."
    )

    result = model._generate(
        [
            HumanMessage(
                content=(
                    "<uploaded_files>\n"
                    "The following files were uploaded in this message:\n"
                    "- suboff_solid.stl (1.6 MB)\n"
                    "</uploaded_files>\n\n"
                    "Please do a geometry preflight on this STL and hold solver execution."
                ),
                additional_kwargs={
                    "files": [
                        {
                            "filename": "suboff_solid.stl",
                            "path": "/mnt/user-data/uploads/suboff_solid.stl",
                            "status": "uploaded",
                        }
                    ]
                },
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "submarine_geometry_check",
                        "args": {
                            "geometry_path": "/mnt/user-data/uploads/suboff_solid.stl",
                            "task_description": "geometry preflight",
                            "task_type": "resistance",
                            "geometry_family_hint": "DARPA SUBOFF bare hull",
                        },
                        "id": "fallback_submarine_geometry_check_0",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content=(
                    "Geometry preflight complete.\n"
                    "Please confirm the reference length and reference area before proceeding."
                ),
                tool_call_id="fallback_submarine_geometry_check_0",
                name="submarine_geometry_check",
            ),
            HumanMessage(
                content=(
                    "<uploaded_files>\n"
                    "The following files were uploaded in this message:\n"
                    "- notes.txt (1 KB)\n"
                    "</uploaded_files>\n\n"
                    f"{confirmation_text}"
                ),
                additional_kwargs={
                    "files": [
                        {
                            "filename": "notes.txt",
                            "path": "/mnt/user-data/uploads/notes.txt",
                            "status": "uploaded",
                        }
                    ]
                },
            ),
        ]
    )

    assert result.generations[0].message.content == ""
    assert result.generations[0].message.tool_calls == [
        {
            "name": "submarine_design_brief",
            "args": {
                "task_description": confirmation_text,
                "geometry_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "task_type": "resistance",
                "confirmation_status": "confirmed",
                "geometry_family_hint": "DARPA SUBOFF",
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "inlet_velocity_mps": 5.0,
            },
            "id": "fallback_submarine_design_brief_0",
            "type": "tool_call",
        }
    ]


def test_openai_cli_provider_recovers_confirmed_design_brief_from_short_confirmation_reply(
    monkeypatch,
):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )
    monkeypatch.setattr(
        OpenAICliChatModel,
        "_retry_empty_response_with_alternate_model",
        lambda self, messages, stop=None, run_manager=None, **kwargs: None,
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [
                    {
                        "type": "message",
                        "content": [],
                    }
                ],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    prior_task = (
        "请先对这个 STL 做几何可用性预检，确认尺度、封闭性与是否适合做 DARPA SUBOFF 裸艇 5 m/s 阻力基线研究；"
        "当前不要启动求解。"
    )

    result = model._generate(
        [
            HumanMessage(
                content=(
                    "<uploaded_files>\n"
                    "The following files were uploaded in this message:\n"
                    "- suboff_solid.stl (1.6 MB)\n"
                    "</uploaded_files>\n\n"
                    f"{prior_task}"
                ),
                additional_kwargs={
                    "files": [
                        {
                            "filename": "suboff_solid.stl",
                            "path": "/mnt/user-data/uploads/suboff_solid.stl",
                            "status": "uploaded",
                        }
                    ]
                },
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "submarine_geometry_check",
                        "args": {
                            "geometry_path": "/mnt/user-data/uploads/suboff_solid.stl",
                            "task_description": "geometry preflight",
                            "task_type": "resistance",
                            "geometry_family_hint": "DARPA SUBOFF bare hull",
                        },
                        "id": "fallback_submarine_geometry_check_0",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content=(
                    "Geometry preflight complete.\n"
                    "Please confirm the reference length and reference area before proceeding."
                ),
                tool_call_id="fallback_submarine_geometry_check_0",
                name="submarine_geometry_check",
            ),
            HumanMessage(content="确认"),
        ]
    )

    assert result.generations[0].message.content == ""
    assert result.generations[0].message.tool_calls == [
        {
            "name": "submarine_design_brief",
            "args": {
                "task_description": f"{prior_task}\n\n用户确认：确认",
                "geometry_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "task_type": "resistance",
                "confirmation_status": "confirmed",
                "geometry_family_hint": "DARPA SUBOFF",
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "inlet_velocity_mps": 5.0,
            },
            "id": "fallback_submarine_design_brief_0",
            "type": "tool_call",
        }
    ]


def test_openai_cli_provider_prefers_design_brief_tool_summary_for_empty_follow_up(
    monkeypatch,
):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )
    monkeypatch.setattr(
        OpenAICliChatModel,
        "_retry_empty_response_with_alternate_model",
        lambda self, messages, stop=None, run_manager=None, **kwargs: None,
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [
                    {
                        "type": "message",
                        "content": [],
                    }
                ],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    result = model._generate(
        [
            HumanMessage(content="确认"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "submarine_design_brief",
                        "args": {
                            "task_description": "确认 baseline 研究简报",
                            "geometry_path": "/mnt/user-data/uploads/suboff_solid.stl",
                            "task_type": "resistance",
                            "confirmation_status": "confirmed",
                        },
                        "id": "fallback_submarine_design_brief_0",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content=(
                    "已整理 CFD 设计简报：确认 baseline 研究简报。\n"
                    "已更新 3 个设计简报 artifacts。"
                ),
                tool_call_id="fallback_submarine_design_brief_0",
                name="submarine_design_brief",
            ),
        ]
    )

    assert result.generations[0].message.tool_calls == []
    assert result.generations[0].message.content == "已整理 CFD 设计简报：确认 baseline 研究简报。"


def test_openai_cli_provider_keeps_text_fallback_for_empty_non_geometry_request(
    monkeypatch,
):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )
    monkeypatch.setattr(
        OpenAICliChatModel,
        "_retry_empty_response_with_alternate_model",
        lambda self, messages, stop=None, run_manager=None, **kwargs: None,
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [
                    {
                        "type": "message",
                        "content": [],
                    }
                ],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    result = model._generate(
        [
            HumanMessage(
                content=(
                    "<uploaded_files>\n"
                    "The following files were uploaded in this message:\n"
                    "- notes.txt (1 KB)\n"
                    "</uploaded_files>\n\n"
                    "继续整理一下这次讨论的要点。"
                ),
                additional_kwargs={
                    "files": [
                        {
                            "filename": "notes.txt",
                            "path": "/mnt/user-data/uploads/notes.txt",
                            "status": "uploaded",
                        }
                    ]
                },
            )
        ]
    )

    assert result.generations[0].message.tool_calls == []
    assert result.generations[0].message.content == "我先根据你刚才的输入继续推进；如果需要你补充信息，我会明确告诉你。"


def test_openai_cli_provider_does_not_inject_fallback_for_tool_call_only_response(monkeypatch):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [
                    {
                        "type": "function_call",
                        "name": "echo_text",
                        "arguments": "{\"text\":\"DEFAULT_OK\"}",
                        "call_id": "call_123",
                    }
                ],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    result = model._generate([HumanMessage(content="Call echo_text with DEFAULT_OK.")])

    assert result.generations[0].message.content == ""
    assert result.generations[0].message.tool_calls == [
        {
            "name": "echo_text",
            "args": {"text": "DEFAULT_OK"},
            "id": "call_123",
            "type": "tool_call",
        }
    ]


def test_openai_cli_provider_reuses_geometry_tool_summary_after_empty_post_tool_response(
    monkeypatch,
):
    monkeypatch.setattr(
        "deerflow.models.openai_cli_provider.load_openai_api_credential",
        lambda: OpenAIApiCredential(
            api_key="sk-openai-test",
            source="codex-auth-file",
        ),
    )
    monkeypatch.setattr(
        OpenAICliChatModel,
        "_retry_empty_response_with_alternate_model",
        lambda self, messages, stop=None, run_manager=None, **kwargs: None,
    )

    model = OpenAICliChatModel(model="gpt-5.4", use_responses_api=True, output_version="responses/v1")
    model.__dict__["root_client"] = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_: {
                "model": "gpt-5.4",
                "output": [
                    {
                        "type": "message",
                        "content": [],
                    }
                ],
                "usage": {
                    "input_tokens": 12,
                    "output_tokens": 3,
                    "total_tokens": 15,
                },
            }
        )
    )

    result = model._generate(
        [
            HumanMessage(
                content=(
                    "<uploaded_files>\n"
                    "The following files were uploaded in this message:\n"
                    "- suboff_solid.stl (1.6 MB)\n"
                    "</uploaded_files>\n\n"
                    "Please run a geometry preflight on this STL and hold solver execution."
                ),
                additional_kwargs={
                    "files": [
                        {
                            "filename": "suboff_solid.stl",
                            "path": "/mnt/user-data/uploads/suboff_solid.stl",
                            "status": "uploaded",
                        }
                    ]
                },
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "submarine_geometry_check",
                        "args": {
                            "geometry_path": "/mnt/user-data/uploads/suboff_solid.stl",
                            "task_description": "geometry preflight",
                            "task_type": "resistance",
                        },
                        "id": "fallback_submarine_geometry_check_0",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content=(
                    "Geometry preflight complete; confirm unit interpretation.\n"
                    "Artifacts are available in the workspace."
                ),
                tool_call_id="fallback_submarine_geometry_check_0",
                name="submarine_geometry_check",
            ),
        ]
    )

    assert result.generations[0].message.tool_calls == []
    assert result.generations[0].message.content == "Geometry preflight complete; confirm unit interpretation."


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
