import importlib
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient


def test_runtime_config_route_summarizes_models_stage_roles_and_provenance(
    monkeypatch,
) -> None:
    gateway_app = importlib.import_module("app.gateway.app")
    try:
        runtime_config = importlib.import_module("app.gateway.routers.runtime_config")
    except ImportError:
        runtime_config = None

    built_in_models = [
        SimpleNamespace(
            name="gpt-5.4",
            display_name="GPT-5.4",
            description="Primary Codex model",
            use="deerflow.models.openai_cli_provider:OpenAICliChatModel",
            model="gpt-5.4",
            supports_thinking=True,
            supports_reasoning_effort=True,
        ),
        SimpleNamespace(
            name="claude-sonnet-4-6",
            display_name="Claude Sonnet 4.6",
            description="Fallback Claude model",
            use="deerflow.models.claude_provider:ClaudeChatModel",
            model="claude-sonnet-4-6",
            supports_thinking=True,
            supports_reasoning_effort=False,
        ),
    ]
    runtime_model = SimpleNamespace(
        name="lab-openai",
        display_name="Lab OpenAI",
        description="Lab-hosted endpoint",
        use="deerflow.models.openai_cli_provider:OpenAICliChatModel",
        model="gpt-4.1-mini",
        supports_thinking=True,
        supports_reasoning_effort=True,
        model_extra={"provider_key": "openai-compatible"},
    )

    config = SimpleNamespace(
        models=built_in_models,
        model_extra={"channels": {"langgraph_url": "http://localhost:2024"}},
    )
    config.get_effective_models = lambda: [*built_in_models, runtime_model]
    config.get_model_config = (
        lambda model_name: next(
            (
                model
                for model in config.get_effective_models()
                if model.name == model_name
            ),
            None,
        )
    )

    monkeypatch.setattr(gateway_app, "get_app_config", lambda: config)

    availability = {
        "gpt-5.4": (True, None),
        "claude-sonnet-4-6": (False, "Anthropic credentials missing."),
        "lab-openai": (True, None),
    }

    if runtime_config is not None:
        monkeypatch.setattr(runtime_config, "get_app_config", lambda: config)
        monkeypatch.setattr(
            runtime_config.AppConfig,
            "resolve_config_path",
            staticmethod(lambda *_args, **_kwargs: Path("C:/repo/config.yaml")),
        )
        monkeypatch.setattr(
            runtime_config.ExtensionsConfig,
            "resolve_config_path",
            staticmethod(
                lambda *_args, **_kwargs: Path("C:/repo/extensions_config.json")
            ),
        )
        monkeypatch.setattr(
            runtime_config.RuntimeConfigOverrides,
            "resolve_config_path",
            staticmethod(
                lambda *_args, **_kwargs: Path(
                    "C:/repo/.deer-flow/runtime-config.json"
                )
            ),
        )
        monkeypatch.setattr(
            runtime_config,
            "resolve_model_availability",
            lambda model: availability[model.name],
        )

    app = gateway_app.create_app()

    with TestClient(app) as client:
        response = client.get("/api/runtime-config")

    assert response.status_code == 200
    payload = response.json()

    assert payload["lead_agent"] == {
        "default_model": "gpt-5.4",
        "config_source": "config.yaml:models[0]",
        "is_overridden": False,
    }
    assert payload["provenance"] == {
        "config_path": str(Path("C:/repo/config.yaml")),
        "extensions_config_path": str(Path("C:/repo/extensions_config.json")),
        "runtime_overrides_path": str(Path("C:/repo/.deer-flow/runtime-config.json")),
        "langgraph_url": "http://localhost:2024",
    }

    models = {item["name"]: item for item in payload["models"]}
    assert models["gpt-5.4"]["provider_key"] == "openai"
    assert models["gpt-5.4"]["is_available"] is True
    assert models["claude-sonnet-4-6"]["provider_key"] == "anthropic"
    assert models["claude-sonnet-4-6"]["availability_reason"] == "Anthropic credentials missing."
    assert models["lab-openai"]["provider_key"] == "openai-compatible"
    assert models["lab-openai"]["is_available"] is True

    providers = {item["provider_key"]: item for item in payload["providers"]}
    assert providers["openai"]["model_names"] == ["gpt-5.4"]
    assert providers["openai"]["is_available"] is True
    assert providers["openai-compatible"]["model_names"] == ["lab-openai"]
    assert providers["openai-compatible"]["is_available"] is True
    assert providers["anthropic"]["model_names"] == ["claude-sonnet-4-6"]
    assert providers["anthropic"]["is_available"] is False

    stage_roles = {item["role_id"]: item for item in payload["stage_roles"]}
    assert stage_roles["task-intelligence"]["subagent_name"] == "submarine-task-intelligence"
    assert stage_roles["task-intelligence"]["model_mode"] == "inherit"
    assert stage_roles["task-intelligence"]["effective_model"] == "gpt-5.4"
    assert stage_roles["task-intelligence"]["config_source"] == "builtin:subagent"


def test_runtime_config_route_updates_runtime_overrides_and_returns_effective_summary(
    monkeypatch,
) -> None:
    gateway_app = importlib.import_module("app.gateway.app")
    runtime_config = importlib.import_module("app.gateway.routers.runtime_config")

    built_in_models = [
        SimpleNamespace(
            name="gpt-5.4",
            display_name="GPT-5.4",
            description="Primary Codex model",
            use="deerflow.models.openai_cli_provider:OpenAICliChatModel",
            model="gpt-5.4",
            supports_thinking=True,
            supports_reasoning_effort=True,
        ),
        SimpleNamespace(
            name="claude-sonnet-4-6",
            display_name="Claude Sonnet 4.6",
            description="Fallback Claude model",
            use="deerflow.models.claude_provider:ClaudeChatModel",
            model="claude-sonnet-4-6",
            supports_thinking=True,
            supports_reasoning_effort=False,
        ),
    ]
    runtime_model = SimpleNamespace(
        name="lab-openai",
        display_name="Lab OpenAI",
        description="Lab-hosted endpoint",
        use="deerflow.models.openai_cli_provider:OpenAICliChatModel",
        model="gpt-4.1-mini",
        supports_thinking=True,
        supports_reasoning_effort=True,
        model_extra={"provider_key": "openai-compatible"},
    )

    config = SimpleNamespace(
        models=built_in_models,
        model_extra={"channels": {"langgraph_url": "http://localhost:2024"}},
    )
    config.get_effective_models = lambda: [*built_in_models, runtime_model]
    config.get_model_config = (
        lambda model_name: next(
            (
                model
                for model in config.get_effective_models()
                if model.name == model_name
            ),
            None,
        )
    )

    saved_overrides: dict[str, object] = {}
    current_overrides = SimpleNamespace(
        lead_agent=SimpleNamespace(default_model=None),
        stage_roles={},
    )

    monkeypatch.setattr(gateway_app, "get_app_config", lambda: config)
    monkeypatch.setattr(runtime_config, "get_app_config", lambda: config)
    monkeypatch.setattr(
        runtime_config,
        "resolve_model_availability",
        lambda model: (True, None),
    )
    monkeypatch.setattr(
        runtime_config,
        "get_runtime_config_overrides",
        lambda: current_overrides,
        raising=False,
    )

    def _capture_overrides(overrides, *_args, **_kwargs):
        saved_overrides["lead_default_model"] = overrides.lead_agent.default_model
        saved_overrides["task_intelligence_model"] = overrides.stage_roles[
            "task-intelligence"
        ].model_name
        saved_overrides["task_intelligence_mode"] = overrides.stage_roles[
            "task-intelligence"
        ].model_mode

    monkeypatch.setattr(
        runtime_config,
        "save_runtime_config_overrides",
        _capture_overrides,
        raising=False,
    )

    app = gateway_app.create_app()

    with TestClient(app) as client:
        response = client.put(
            "/api/runtime-config",
            json={
                "lead_agent": {"default_model": "lab-openai"},
                "stage_roles": [
                    {
                        "role_id": "task-intelligence",
                        "model_mode": "explicit",
                        "model_name": "lab-openai",
                    }
                ],
            },
        )

    assert response.status_code == 200
    payload = response.json()

    assert saved_overrides == {
        "lead_default_model": "lab-openai",
        "task_intelligence_model": "lab-openai",
        "task_intelligence_mode": "explicit",
    }
    assert payload["lead_agent"]["default_model"] == "lab-openai"
    assert payload["stage_roles"][0]["effective_model"] == "lab-openai"
