import json
from collections.abc import Callable
from pathlib import Path
from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.gateway.routers import skills
from deerflow.config.extensions_config import ExtensionsConfig
from deerflow.config.paths import Paths
from deerflow.domain.submarine.skill_studio import run_skill_studio
from deerflow.skills.loader import load_skills as load_skills_from_path
from deerflow.skills.validation import _validate_skill_frontmatter

VALIDATE_SKILL_FRONTMATTER = cast(
    Callable[[Path], tuple[bool, str, str | None]],
    _validate_skill_frontmatter,
)


def _write_skill(skill_dir: Path, frontmatter: str) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(frontmatter, encoding="utf-8")


def test_validate_skill_frontmatter_allows_standard_optional_metadata(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    _write_skill(
        skill_dir,
        """---
name: demo-skill
description: Demo skill
version: 1.0.0
author: example.com/demo
compatibility: OpenClaw >= 1.0
license: MIT
---

# Demo Skill
""",
    )

    valid, message, skill_name = VALIDATE_SKILL_FRONTMATTER(skill_dir)

    assert valid is True
    assert message == "Skill is valid!"
    assert skill_name == "demo-skill"


def test_validate_skill_frontmatter_still_rejects_unknown_keys(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    _write_skill(
        skill_dir,
        """---
name: demo-skill
description: Demo skill
unsupported: true
---

# Demo Skill
""",
    )

    valid, message, skill_name = VALIDATE_SKILL_FRONTMATTER(skill_dir)

    assert valid is False
    assert "unsupported" in message
    assert skill_name is None


def test_validate_skill_frontmatter_reads_utf8_on_windows_locale(tmp_path, monkeypatch) -> None:
    skill_dir = tmp_path / "demo-skill"
    _write_skill(
        skill_dir,
        """---
name: demo-skill
description: "Curly quotes: \u201cutf8\u201d"
---

# Demo Skill
""",
    )

    original_read_text = Path.read_text

    def read_text_with_gbk_default(self, *args, **kwargs):
        kwargs.setdefault("encoding", "gbk")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text_with_gbk_default)

    valid, message, skill_name = VALIDATE_SKILL_FRONTMATTER(skill_dir)

    assert valid is True
    assert message == "Skill is valid!"
    assert skill_name == "demo-skill"


def test_skills_router_prefers_explicit_langgraph_env_url(monkeypatch) -> None:
    monkeypatch.setenv("LANGGRAPH_PROXY_BASE_URL", "http://127.0.0.1:2127")
    monkeypatch.setattr(
        skills,
        "get_app_config",
        lambda: type("Config", (), {"model_extra": {}})(),
    )

    assert skills._get_langgraph_server_url() == "http://127.0.0.1:2127"


def test_skills_router_falls_back_to_reachable_local_langgraph_url(monkeypatch) -> None:
    monkeypatch.delenv("LANGGRAPH_PROXY_BASE_URL", raising=False)
    monkeypatch.delenv("LANGGRAPH_SERVER_URL", raising=False)
    monkeypatch.delenv("LANGGRAPH_BASE_URL", raising=False)
    monkeypatch.delenv("NEXT_PUBLIC_LANGGRAPH_BASE_URL", raising=False)
    monkeypatch.setattr(
        skills,
        "get_app_config",
        lambda: type("Config", (), {"model_extra": {}})(),
    )
    monkeypatch.setattr(
        skills,
        "_is_langgraph_url_reachable",
        lambda url: url == "http://127.0.0.1:2127",
    )

    assert skills._get_langgraph_server_url() == "http://127.0.0.1:2127"


def _build_skill_archive(
    tmp_path: Path,
    thread_id: str = "thread-1",
) -> tuple[dict[tuple[str, str], Path], dict[str, str]]:
    paths = Paths(tmp_path)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    payload, _ = run_skill_studio(
        outputs_dir=outputs_dir,
        skill_name="Submarine Result Acceptance",
        skill_purpose=(
            "Define how Claude Code and reporting subagents should decide whether a "
            "submarine CFD run is trustworthy, needs review, or should be rerun."
        ),
        trigger_conditions=[
            "the user asks whether the current CFD result is trustworthy",
        ],
        workflow_steps=[
            "review mesh, residual, and force summaries from the current run",
            "produce a Chinese acceptance conclusion with evidence and next-step advice",
        ],
        expert_rules=[
            "flag drag values that materially diverge from the baseline case family",
        ],
        acceptance_criteria=[
            "state an explicit delivery decision",
            "cite which CFD indicators support that decision",
        ],
        test_scenarios=[
            "baseline steady-state bare-hull case with stable Cd and residual decay",
        ],
    )
    skill_slug = payload["skill_name"]
    archive_virtual_path = (
        f"/mnt/user-data/outputs/submarine/skill-studio/{skill_slug}/{skill_slug}.skill"
    )
    archive_path = (
        outputs_dir / "submarine" / "skill-studio" / skill_slug / f"{skill_slug}.skill"
    )
    draft_virtual_path = (
        f"/mnt/user-data/outputs/submarine/skill-studio/{skill_slug}/skill-draft.json"
    )
    draft_path = (
        outputs_dir / "submarine" / "skill-studio" / skill_slug / "skill-draft.json"
    )
    return (
        {
            (thread_id, archive_virtual_path): archive_path,
            (thread_id, draft_virtual_path): draft_path,
        },
        {
            "archive": archive_virtual_path,
            "draft": draft_virtual_path,
        },
    )


def _create_router_client(
    tmp_path: Path,
    monkeypatch,
    resolved_paths: dict[tuple[str, str], Path],
) -> TestClient:
    skills_root = tmp_path / "skills"
    config_path = tmp_path / "extensions_config.json"
    thread_message_ids = {
        "thread-1": ["msg-1"],
    }

    async def load_thread_state(thread_id: str) -> dict:
        return {
            "values": {
                "messages": [
                    {"id": message_id, "type": "ai", "content": ""}
                    for message_id in thread_message_ids.get(thread_id, [])
                ]
            }
        }

    monkeypatch.setattr(
        skills,
        "resolve_thread_virtual_path",
        lambda thread_id, path: resolved_paths[(thread_id, path)],
    )
    monkeypatch.setattr(skills, "_load_thread_state", load_thread_state)
    monkeypatch.setattr(skills, "get_skills_root_path", lambda: skills_root)
    monkeypatch.setattr(
        skills.ExtensionsConfig,
        "resolve_config_path",
        staticmethod(lambda *_args, **_kwargs: config_path),
    )
    monkeypatch.setattr(skills, "reload_extensions_config", lambda: None)
    monkeypatch.setattr(skills, "get_extensions_config", lambda: ExtensionsConfig())
    monkeypatch.setattr(
        skills,
        "load_skills",
        lambda *args, **kwargs: load_skills_from_path(
            skills_path=skills_root,
            use_config=False,
            enabled_only=kwargs.get("enabled_only", False),
        ),
    )

    app = FastAPI()
    app.include_router(skills.router)
    return TestClient(app)


def test_skill_lifecycle_routes_round_trip_publish_management_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    resolved_paths, virtual_paths = _build_skill_archive(tmp_path)

    with _create_router_client(tmp_path, monkeypatch, resolved_paths) as client:
        evidence_response = client.post(
            "/api/skills/dry-run-evidence",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["draft"],
                "status": "passed",
                "scenario_id": "scenario-1",
                "message_ids": ["msg-1"],
                "reviewer_note": "Lifecycle round-trip evidence.",
            },
        )
        publish_response = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["archive"],
                "overwrite": False,
                "enable": True,
                "version_note": "Promote acceptance skill",
                "binding_targets": [
                    {
                        "role_id": "scientific-verification",
                        "mode": "explicit",
                        "target_skills": ["submarine-result-acceptance"],
                    },
                ],
            },
        )
        list_response = client.get("/api/skills/lifecycle")
        detail_response = client.get(
            "/api/skills/lifecycle/submarine-result-acceptance",
        )
        update_response = client.put(
            "/api/skills/lifecycle/submarine-result-acceptance",
            json={
                "enabled": False,
                "version_note": "Hold back after manual review",
                "binding_targets": [
                    {
                        "role_id": "result-reporting",
                        "mode": "explicit",
                        "target_skills": ["submarine-result-acceptance"],
                    },
                ],
            },
        )

    assert evidence_response.status_code == 200
    assert publish_response.status_code == 200

    assert list_response.status_code == 200
    lifecycle_summaries = list_response.json()["skills"]
    assert len(lifecycle_summaries) == 1
    assert lifecycle_summaries[0]["skill_name"] == "submarine-result-acceptance"
    assert lifecycle_summaries[0]["enabled"] is True
    assert lifecycle_summaries[0]["binding_targets"][0]["role_id"] == "scientific-verification"
    assert lifecycle_summaries[0]["draft_status"] == "published"
    assert lifecycle_summaries[0]["published_path"].replace("\\", "/").endswith(
        "skills/custom/submarine-result-acceptance",
    )
    assert lifecycle_summaries[0]["last_published_at"] is not None

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["version_note"] == "Promote acceptance skill"
    assert detail_payload["binding_targets"][0]["role_id"] == "scientific-verification"
    assert detail_payload["last_published_from_thread_id"] == "thread-1"

    assert update_response.status_code == 200
    updated_payload = update_response.json()
    assert updated_payload["enabled"] is False
    assert updated_payload["version_note"] == "Hold back after manual review"
    assert updated_payload["binding_targets"][0]["role_id"] == "result-reporting"


def test_skill_lifecycle_routes_support_prepublish_draft_updates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    resolved_paths, virtual_paths = _build_skill_archive(tmp_path)
    draft_path = resolved_paths[("thread-1", virtual_paths["draft"])]
    lifecycle_path = draft_path.parent / "skill-lifecycle.json"

    with _create_router_client(tmp_path, monkeypatch, resolved_paths) as client:
        update_response = client.put(
            "/api/skills/lifecycle/submarine-result-acceptance",
            json={
                "enabled": True,
                "version_note": "Draft lifecycle note before publish",
                "binding_targets": [
                    {
                        "role_id": "scientific-verification",
                        "mode": "explicit",
                        "target_skills": ["submarine-result-acceptance"],
                    },
                ],
                "thread_id": "thread-1",
                "path": virtual_paths["draft"],
            },
        )
        list_response = client.get("/api/skills/lifecycle")
        detail_response = client.get(
            "/api/skills/lifecycle/submarine-result-acceptance",
        )

    assert update_response.status_code == 200
    update_payload = update_response.json()
    assert update_payload["draft_status"] == "draft_ready"
    assert update_payload["published_path"] is None
    assert update_payload["version_note"] == "Draft lifecycle note before publish"
    assert update_payload["binding_targets"][0]["role_id"] == "scientific-verification"
    assert update_payload["binding_count"] == 1

    assert list_response.status_code == 200
    lifecycle_summaries = list_response.json()["skills"]
    assert len(lifecycle_summaries) == 1
    assert lifecycle_summaries[0]["skill_name"] == "submarine-result-acceptance"
    assert lifecycle_summaries[0]["draft_status"] == "draft_ready"
    assert lifecycle_summaries[0]["binding_count"] == 1
    assert lifecycle_summaries[0]["version_note"] == "Draft lifecycle note before publish"

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["published_path"] is None
    assert detail_payload["version_note"] == "Draft lifecycle note before publish"
    assert detail_payload["binding_targets"][0]["role_id"] == "scientific-verification"

    persisted_payload = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    assert persisted_payload["version_note"] == "Draft lifecycle note before publish"
    assert persisted_payload["bindings"][0]["role_id"] == "scientific-verification"
