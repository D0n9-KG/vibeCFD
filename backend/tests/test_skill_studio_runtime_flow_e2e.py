from types import SimpleNamespace
import importlib

from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain.agents.middleware.types import ModelRequest
from langchain_core.messages import SystemMessage
from langgraph.runtime import Runtime

from app.gateway.routers import skills
from deerflow.agents.middlewares.skill_runtime_snapshot_middleware import (
    SkillRuntimeSnapshotMiddleware,
    capture_skill_runtime_snapshot,
)
from deerflow.config.extensions_config import ExtensionsConfig
from deerflow.config.paths import Paths
from deerflow.domain.submarine.skill_lifecycle import load_skill_lifecycle_registry
from deerflow.domain.submarine.skill_studio import run_skill_studio
from deerflow.skills.loader import load_skills as load_skills_from_path

prompt_module = importlib.import_module("deerflow.agents.lead_agent.prompt")


def _build_skill_archive(
    tmp_path,
    thread_id: str,
    *,
    skill_name: str,
    skill_purpose: str,
) -> tuple[dict[tuple[str, str], object], dict[str, str]]:
    paths = Paths(tmp_path)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    payload, _ = run_skill_studio(
        outputs_dir=outputs_dir,
        skill_name=skill_name,
        skill_purpose=skill_purpose,
        trigger_conditions=[
            "the user asks for a submarine CFD result decision",
        ],
        workflow_steps=[
            "review the current submarine CFD evidence package",
            "state a decision with the right delivery guardrails",
        ],
        expert_rules=[
            "flag inconsistent CFD evidence before delivery",
        ],
        acceptance_criteria=[
            "state an explicit delivery decision",
        ],
        test_scenarios=[
            "baseline steady-state bare-hull case with stable Cd and residual decay",
        ],
    )
    skill_slug = payload["skill_name"]
    archive_virtual_path = (
        f"/mnt/user-data/outputs/submarine/skill-studio/{skill_slug}/{skill_slug}.skill"
    )
    draft_virtual_path = (
        f"/mnt/user-data/outputs/submarine/skill-studio/{skill_slug}/skill-draft.json"
    )
    draft_dir = outputs_dir / "submarine" / "skill-studio" / skill_slug
    return (
        {
            (thread_id, archive_virtual_path): draft_dir / f"{skill_slug}.skill",
            (thread_id, draft_virtual_path): draft_dir / "skill-draft.json",
        },
        {
            "archive": archive_virtual_path,
            "draft": draft_virtual_path,
            "skill_name": skill_slug,
        },
    )


def _create_client(tmp_path, monkeypatch, resolved_paths) -> TestClient:
    skills_root = tmp_path / "skills"
    config_path = tmp_path / "extensions_config.json"
    thread_message_ids = {
        "thread-old": ["msg-1"],
        "thread-new": ["msg-2"],
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

    app_config = SimpleNamespace(
        skills=SimpleNamespace(
            get_skills_path=lambda: skills_root,
            container_path="/mnt/skills",
        ),
        tool_search=SimpleNamespace(enabled=False),
    )
    monkeypatch.setattr("deerflow.config.get_app_config", lambda: app_config)
    monkeypatch.setattr(
        prompt_module,
        "load_skills",
        lambda *args, **kwargs: load_skills_from_path(
            skills_path=skills_root,
            use_config=False,
            enabled_only=kwargs.get("enabled_only", True),
        ),
    )
    monkeypatch.setattr(prompt_module, "_CACHED_ENABLED_SKILLS", None, raising=False)
    monkeypatch.setattr(
        prompt_module,
        "_CACHED_ENABLED_SKILLS_SOURCE_STATE",
        None,
        raising=False,
    )

    app = FastAPI()
    app.include_router(skills.router)
    return TestClient(app)


def _build_request() -> ModelRequest:
    return ModelRequest(
        model=SimpleNamespace(),
        messages=[],
        system_message=SystemMessage(content="live system prompt"),
        tools=[],
        state={"messages": []},
        runtime=Runtime(context={}),
    )


def test_skill_studio_runtime_flow_end_to_end(tmp_path, monkeypatch) -> None:
    first_paths, first_virtual_paths = _build_skill_archive(
        tmp_path,
        "thread-old",
        skill_name="Submarine Result Acceptance",
        skill_purpose="Decide whether the current submarine CFD run is trustworthy.",
    )
    second_paths, second_virtual_paths = _build_skill_archive(
        tmp_path,
        "thread-new",
        skill_name="Submarine Reporting Guard",
        skill_purpose="Decide whether a submarine CFD report is safe to deliver.",
    )
    middleware = SkillRuntimeSnapshotMiddleware()

    with _create_client(
        tmp_path,
        monkeypatch,
        first_paths | second_paths,
    ) as client:
        blocked = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-old",
                "path": first_virtual_paths["archive"],
                "overwrite": False,
                "enable": True,
                "version_note": "",
                "binding_targets": [],
            },
        )

        recorded_first = client.post(
            "/api/skills/dry-run-evidence",
            json={
                "thread_id": "thread-old",
                "path": first_virtual_paths["draft"],
                "status": "passed",
                "scenario_id": "scenario-1",
                "message_ids": ["msg-1"],
                "reviewer_note": "First snapshot candidate passed dry run.",
            },
        )
        published_first = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-old",
                "path": first_virtual_paths["archive"],
                "overwrite": False,
                "enable": True,
                "version_note": "First publish",
                "binding_targets": [
                    {
                        "role_id": "scientific-verification",
                        "mode": "explicit",
                        "target_skills": [first_virtual_paths["skill_name"]],
                    },
                ],
            },
        )

        old_snapshot = capture_skill_runtime_snapshot()

        recorded_second = client.post(
            "/api/skills/dry-run-evidence",
            json={
                "thread_id": "thread-new",
                "path": second_virtual_paths["draft"],
                "status": "passed",
                "scenario_id": "scenario-2",
                "message_ids": ["msg-2"],
                "reviewer_note": "Second snapshot candidate passed dry run.",
            },
        )
        published_second = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-new",
                "path": second_virtual_paths["archive"],
                "overwrite": False,
                "enable": True,
                "version_note": "Second publish",
                "binding_targets": [
                    {
                        "role_id": "result-reporting",
                        "mode": "explicit",
                        "target_skills": [second_virtual_paths["skill_name"]],
                    },
                ],
            },
        )

        new_snapshot = capture_skill_runtime_snapshot()

    assert blocked.status_code == 400
    assert "dry-run evidence" in blocked.json()["detail"]
    assert recorded_first.status_code == 200
    assert published_first.status_code == 200
    assert recorded_second.status_code == 200
    assert published_second.status_code == 200

    registry = load_skill_lifecycle_registry(
        registry_path=tmp_path / "skills" / "custom" / ".skill-studio-registry.json",
    )
    assert registry.runtime_revision == 2

    assert old_snapshot["runtime_revision"] == 1
    assert old_snapshot["enabled_skill_names"] == [
        first_virtual_paths["skill_name"]
    ]
    assert old_snapshot["binding_targets_applied"] == ["scientific-verification"]

    assert new_snapshot["runtime_revision"] == 2
    assert sorted(new_snapshot["enabled_skill_names"]) == sorted(
        [
            first_virtual_paths["skill_name"],
            second_virtual_paths["skill_name"],
        ]
    )
    assert new_snapshot["binding_targets_applied"] == [
        "result-reporting",
        "scientific-verification",
    ]

    old_request = middleware._override_skill_snapshot(_build_request(), old_snapshot)
    new_request = middleware._override_skill_snapshot(_build_request(), new_snapshot)

    assert first_virtual_paths["skill_name"] in old_request.system_prompt
    assert second_virtual_paths["skill_name"] not in old_request.system_prompt
    assert second_virtual_paths["skill_name"] in new_request.system_prompt
