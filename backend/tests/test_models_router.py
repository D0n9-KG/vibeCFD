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
        "deerflow.models.credential_loader.load_claude_code_credential",
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
