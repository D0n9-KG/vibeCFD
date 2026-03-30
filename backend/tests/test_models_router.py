from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.gateway.routers import models as models_router


def test_list_models_marks_claude_model_unavailable_without_credentials(
    monkeypatch,
) -> None:
    config = SimpleNamespace(
        models=[
            SimpleNamespace(
                name="claude-sonnet-4-6",
                model="claude-sonnet-4-6",
                display_name="Claude Sonnet 4.6",
                description=None,
                supports_thinking=True,
                supports_reasoning_effort=False,
                use="deerflow.models.claude_provider:ClaudeChatModel",
            )
        ]
    )

    monkeypatch.setattr(models_router, "get_app_config", lambda: config)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(
        "app.gateway.model_availability.load_claude_code_credential",
        lambda: None,
    )

    app = FastAPI()
    app.include_router(models_router.router)

    with TestClient(app) as client:
        response = client.get("/api/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["models"][0]["is_available"] is False
    assert "credential" in payload["models"][0]["availability_reason"].lower()


def test_list_models_marks_openai_cli_model_available_with_codex_auth_file(
    monkeypatch,
) -> None:
    config = SimpleNamespace(
        models=[
            SimpleNamespace(
                name="gpt-5.4",
                model="gpt-5.4",
                display_name="GPT-5.4",
                description=None,
                supports_thinking=True,
                supports_reasoning_effort=True,
                use="deerflow.models.openai_cli_provider:OpenAICliChatModel",
            )
        ]
    )

    monkeypatch.setattr(models_router, "get_app_config", lambda: config)
    monkeypatch.setattr(
        "app.gateway.model_availability.load_openai_api_credential",
        lambda: object(),
    )

    app = FastAPI()
    app.include_router(models_router.router)

    with TestClient(app) as client:
        response = client.get("/api/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["models"][0]["is_available"] is True
    assert payload["models"][0]["availability_reason"] is None
