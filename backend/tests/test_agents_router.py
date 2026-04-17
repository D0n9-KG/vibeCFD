import json
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.gateway.routers import agents
from deerflow.config.paths import Paths


def _make_paths(base_dir: Path) -> Paths:
    return Paths(base_dir=base_dir)


def _write_custom_agent(base_dir: Path, name: str) -> None:
    agent_dir = base_dir / "agents" / name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "config.yaml").write_text(
        "\n".join(
            [
                f"name: {name}",
                "description: Custom workspace agent",
                "display_name: Custom Workspace Agent",
                "model: gpt-5.4",
            ]
        ),
        encoding="utf-8",
    )
    (agent_dir / "SOUL.md").write_text("You are custom.", encoding="utf-8")


def test_list_agents_includes_builtin_and_custom_agents_with_management_metadata(
    tmp_path: Path,
) -> None:
    paths = _make_paths(tmp_path)
    _write_custom_agent(tmp_path, "custom-reviewer")

    legacy_store_path = tmp_path / ".deerflow-ui" / "agents.json"
    legacy_store_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_store_path.write_text(
        json.dumps(
            [
                {
                    "name": "legacy-agent",
                    "display_name": "Legacy Agent",
                }
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    app = FastAPI()
    app.include_router(agents.router)

    with (
        patch("deerflow.config.agents_config.get_paths", return_value=paths),
        patch("app.gateway.routers.agents.get_paths", return_value=paths),
        patch.object(
            agents,
            "_resolve_legacy_agent_store_path",
            return_value=legacy_store_path,
            create=True,
        ),
        TestClient(app) as client,
    ):
        response = client.get("/api/agents")

    assert response.status_code == 200
    payload = response.json()
    by_name = {item["name"]: item for item in payload["agents"]}

    assert by_name["codex-skill-creator"]["kind"] == "builtin"
    assert by_name["codex-skill-creator"]["is_builtin"] is True
    assert by_name["codex-skill-creator"]["is_editable"] is False
    assert by_name["codex-skill-creator"]["is_deletable"] is False
    assert by_name["codex-skill-creator"]["source_path"] is None

    assert by_name["custom-reviewer"]["kind"] == "custom"
    assert by_name["custom-reviewer"]["is_builtin"] is False
    assert by_name["custom-reviewer"]["is_editable"] is True
    assert by_name["custom-reviewer"]["is_deletable"] is True
    assert by_name["custom-reviewer"]["source_path"].replace("\\", "/").endswith(
        "/agents/custom-reviewer",
    )

    assert payload["legacy_store"] == {
        "exists": True,
        "path": str(legacy_store_path),
        "agent_count": 1,
    }


def test_create_agent_rejects_reserved_builtin_name(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path)

    app = FastAPI()
    app.include_router(agents.router)

    with (
        patch("deerflow.config.agents_config.get_paths", return_value=paths),
        patch("app.gateway.routers.agents.get_paths", return_value=paths),
        TestClient(app) as client,
    ):
        response = client.post(
            "/api/agents",
            json={
                "name": "codex-skill-creator",
                "description": "Should fail",
                "soul": "Built-in collision",
            },
        )

    assert response.status_code == 409
    assert "built-in" in response.json()["detail"].lower()


def test_update_builtin_agent_is_rejected(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path)

    app = FastAPI()
    app.include_router(agents.router)

    with (
        patch("deerflow.config.agents_config.get_paths", return_value=paths),
        patch("app.gateway.routers.agents.get_paths", return_value=paths),
        TestClient(app) as client,
    ):
        response = client.put(
            "/api/agents/codex-skill-creator",
            json={"description": "Should not mutate built-ins"},
        )

    assert response.status_code == 403
    assert "built-in" in response.json()["detail"].lower()
