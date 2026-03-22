from __future__ import annotations

import json

import httpx

from app.agent_runtime.json_utils import extract_json_object
from app.agent_runtime.provider import CompatibleAgentProvider


def test_extract_json_object_handles_markdown_fence() -> None:
    raw = '```json\n{"summary":"ok","items":[1,2,3]}\n```'

    parsed = extract_json_object(raw)

    assert parsed == {"summary": "ok", "items": [1, 2, 3]}


def test_compatible_agent_provider_posts_openai_compatible_payload(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["json"] = request.read().decode("utf-8")
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '```json\n{"summary":"规划完成","selected_skills":["geometry-check"]}\n```'
                        }
                    }
                ]
            },
        )

    provider = CompatibleAgentProvider(
        base_url="https://example.com/v1",
        model="qwen-plus",
        api_key="secret",
        timeout_seconds=15,
        transport=httpx.MockTransport(handler),
    )

    parsed = provider.complete_json(
        system_prompt="system",
        user_prompt="user",
    )

    assert parsed["summary"] == "规划完成"
    assert parsed["selected_skills"] == ["geometry-check"]
    assert captured["url"] == "https://example.com/v1/chat/completions"
    request_json = json.loads(captured["json"])
    assert request_json["model"] == "qwen-plus"
    assert captured["headers"]["authorization"] == "Bearer secret"
