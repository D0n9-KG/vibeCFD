import importlib
from types import SimpleNamespace

from fastapi.testclient import TestClient


def _make_config():
    return SimpleNamespace(
        models=[
            SimpleNamespace(
                name="gpt-5.4",
                display_name="GPT-5.4",
                description="Primary OpenAI model",
                use="deerflow.models.openai_cli_provider:OpenAICliChatModel",
                model="gpt-5.4",
                supports_thinking=True,
                supports_reasoning_effort=True,
                supports_vision=False,
            ),
            SimpleNamespace(
                name="claude-sonnet-4-6",
                display_name="Claude Sonnet 4.6",
                description="Fallback Claude model",
                use="deerflow.models.claude_provider:ClaudeChatModel",
                model="claude-sonnet-4-6",
                supports_thinking=True,
                supports_reasoning_effort=False,
                supports_vision=True,
            ),
        ]
    )


def test_runtime_models_route_lists_builtin_and_runtime_models_without_echoing_secrets(
    monkeypatch,
) -> None:
    gateway_app = importlib.import_module("app.gateway.app")
    runtime_models_router = importlib.import_module("app.gateway.routers.runtime_models")
    runtime_models_config = importlib.import_module(
        "deerflow.config.runtime_models"
    )

    config = _make_config()
    registry = runtime_models_config.RuntimeModelRegistry(
        models=[
            runtime_models_config.RuntimeModelDefinition(
                name="lab-openai",
                display_name="Lab OpenAI",
                description="Custom lab endpoint",
                provider_key="openai-compatible",
                model="gpt-4.1-mini",
                base_url="https://lab.example.com/v1",
                supports_thinking=True,
                supports_reasoning_effort=True,
                supports_vision=False,
            )
        ]
    )
    secrets = runtime_models_config.RuntimeModelSecrets(
        api_keys={"lab-openai": "secret-value"}
    )

    monkeypatch.setattr(gateway_app, "get_app_config", lambda: config)
    monkeypatch.setattr(runtime_models_router, "get_app_config", lambda: config)
    monkeypatch.setattr(
        runtime_models_router,
        "get_runtime_model_registry",
        lambda: registry,
    )
    monkeypatch.setattr(
        runtime_models_router,
        "get_runtime_model_secrets",
        lambda: secrets,
    )
    monkeypatch.setattr(
        runtime_models_router,
        "resolve_model_availability",
        lambda model: (True, None),
    )

    app = gateway_app.create_app()

    with TestClient(app) as client:
        response = client.get("/api/runtime-models")

    assert response.status_code == 200
    payload = response.json()
    models = {item["name"]: item for item in payload["models"]}

    assert models["gpt-5.4"]["source"] == "config"
    assert models["gpt-5.4"]["is_editable"] is False
    assert models["gpt-5.4"]["provider_key"] == "openai"
    assert "api_key" not in models["gpt-5.4"]

    assert models["lab-openai"]["source"] == "runtime"
    assert models["lab-openai"]["is_editable"] is True
    assert models["lab-openai"]["provider_key"] == "openai-compatible"
    assert models["lab-openai"]["base_url"] == "https://lab.example.com/v1"
    assert models["lab-openai"]["has_api_key"] is True
    assert "api_key" not in models["lab-openai"]


def test_runtime_models_route_treats_codex_backed_builtin_models_as_openai_provider(
    monkeypatch,
) -> None:
    gateway_app = importlib.import_module("app.gateway.app")
    runtime_models_router = importlib.import_module("app.gateway.routers.runtime_models")
    runtime_models_config = importlib.import_module(
        "deerflow.config.runtime_models"
    )

    config = SimpleNamespace(
        models=[
            SimpleNamespace(
                name="codex-gpt-5.4",
                display_name="Codex GPT-5.4",
                description="Codex-backed OpenAI model",
                use="deerflow.models.openai_codex_provider:CodexChatModel",
                model="gpt-5.4",
                supports_thinking=True,
                supports_reasoning_effort=True,
                supports_vision=False,
            )
        ]
    )
    registry = runtime_models_config.RuntimeModelRegistry(models=[])
    secrets = runtime_models_config.RuntimeModelSecrets(api_keys={})

    monkeypatch.setattr(gateway_app, "get_app_config", lambda: config)
    monkeypatch.setattr(runtime_models_router, "get_app_config", lambda: config)
    monkeypatch.setattr(
        runtime_models_router,
        "get_runtime_model_registry",
        lambda: registry,
    )
    monkeypatch.setattr(
        runtime_models_router,
        "get_runtime_model_secrets",
        lambda: secrets,
    )
    monkeypatch.setattr(
        runtime_models_router,
        "resolve_model_availability",
        lambda model: (True, None),
    )

    app = gateway_app.create_app()

    with TestClient(app) as client:
        response = client.get("/api/runtime-models")

    assert response.status_code == 200
    payload = response.json()
    models = {item["name"]: item for item in payload["models"]}

    assert models["codex-gpt-5.4"]["provider_key"] == "openai"
    assert models["codex-gpt-5.4"]["provider_label"] == "OpenAI API"


def test_runtime_models_route_create_update_and_delete_runtime_models(
    monkeypatch,
) -> None:
    gateway_app = importlib.import_module("app.gateway.app")
    runtime_models_router = importlib.import_module("app.gateway.routers.runtime_models")
    runtime_models_config = importlib.import_module(
        "deerflow.config.runtime_models"
    )
    runtime_config_overrides = importlib.import_module(
        "deerflow.config.runtime_config_overrides"
    )

    config = _make_config()
    registry = runtime_models_config.RuntimeModelRegistry(models=[])
    secrets = runtime_models_config.RuntimeModelSecrets(api_keys={})
    overrides = runtime_config_overrides.RuntimeConfigOverrides(
        lead_agent=runtime_config_overrides.RuntimeLeadAgentOverride(
            default_model="research-gpt"
        ),
        stage_roles={
            "task-intelligence": runtime_config_overrides.RuntimeStageRoleOverride(
                model_mode="explicit",
                model_name="research-gpt",
            )
        },
    )

    monkeypatch.setattr(gateway_app, "get_app_config", lambda: config)
    monkeypatch.setattr(runtime_models_router, "get_app_config", lambda: config)
    monkeypatch.setattr(
        runtime_models_router,
        "get_runtime_model_registry",
        lambda: registry,
    )
    monkeypatch.setattr(
        runtime_models_router,
        "get_runtime_model_secrets",
        lambda: secrets,
    )
    monkeypatch.setattr(
        runtime_models_router,
        "resolve_model_availability",
        lambda model: (True, None),
    )
    monkeypatch.setattr(
        runtime_models_router,
        "get_runtime_config_overrides",
        lambda: overrides,
    )

    def _save_registry(next_registry):
        registry.models = next_registry.models
        return registry

    def _save_secrets(next_secrets):
        secrets.api_keys = dict(next_secrets.api_keys)
        return secrets

    def _save_overrides(next_overrides):
        overrides.lead_agent = next_overrides.lead_agent
        overrides.stage_roles = dict(next_overrides.stage_roles)
        return overrides

    monkeypatch.setattr(
        runtime_models_router,
        "save_runtime_model_registry",
        _save_registry,
    )
    monkeypatch.setattr(
        runtime_models_router,
        "save_runtime_model_secrets",
        _save_secrets,
    )
    monkeypatch.setattr(
        runtime_models_router,
        "save_runtime_config_overrides",
        _save_overrides,
    )

    app = gateway_app.create_app()

    with TestClient(app) as client:
        create_response = client.post(
            "/api/runtime-models",
            json={
                "name": "research-gpt",
                "display_name": "Research GPT",
                "description": "OpenAI-compatible research endpoint",
                "provider_key": "openai-compatible",
                "model": "gpt-4.1",
                "base_url": "https://research.example.com/v1",
                "api_key": "sk-live-123",
                "supports_thinking": True,
                "supports_reasoning_effort": True,
                "supports_vision": False,
            },
        )

        assert create_response.status_code == 200
        assert secrets.api_keys["research-gpt"] == "sk-live-123"
        assert registry.models[0].name == "research-gpt"
        assert create_response.json()["has_api_key"] is True
        assert "api_key" not in create_response.json()

        update_response = client.put(
            "/api/runtime-models/research-gpt",
            json={
                "display_name": "Research GPT Updated",
                "description": "Updated endpoint",
                "provider_key": "anthropic",
                "model": "claude-3-7-sonnet-latest",
                "base_url": "https://anthropic.example.com",
                "api_key": None,
                "clear_api_key": True,
                "supports_thinking": True,
                "supports_reasoning_effort": False,
                "supports_vision": True,
            },
        )

        assert update_response.status_code == 200
        assert "research-gpt" not in secrets.api_keys
        assert registry.models[0].provider_key == "anthropic"
        assert update_response.json()["display_name"] == "Research GPT Updated"
        assert update_response.json()["has_api_key"] is False

        delete_response = client.delete("/api/runtime-models/research-gpt")

        assert delete_response.status_code == 200
        assert delete_response.json() == {
            "deleted": True,
            "name": "research-gpt",
        }
        assert registry.models == []
        assert overrides.lead_agent.default_model is None
        assert "task-intelligence" not in overrides.stage_roles
