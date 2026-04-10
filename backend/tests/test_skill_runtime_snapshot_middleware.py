from types import SimpleNamespace

from langchain.agents.middleware.types import ModelRequest
from langchain_core.messages import SystemMessage
from langgraph.runtime import Runtime

from deerflow.agents.middlewares.skill_runtime_snapshot_middleware import (
    SkillRuntimeSnapshotMiddleware,
    capture_skill_runtime_snapshot,
)


def _build_request(system_prompt: str = "live prompt fresh-skill") -> ModelRequest:
    return ModelRequest(
        model=SimpleNamespace(),
        messages=[],
        system_message=SystemMessage(content=system_prompt),
        tools=[],
        state={"messages": []},
        runtime=Runtime(context={}),
    )


def _fake_skill(name: str, description: str):
    return SimpleNamespace(
        name=name,
        description=description,
        get_container_file_path=lambda container_base_path="/mnt/skills": (
            f"{container_base_path}/custom/{name}/SKILL.md"
        ),
    )


def test_before_model_captures_skill_runtime_snapshot(monkeypatch):
    middleware = SkillRuntimeSnapshotMiddleware()
    snapshot = {
        "runtime_revision": 4,
        "captured_at": "2026-04-10T08:00:00Z",
        "enabled_skill_names": ["submarine-result-acceptance"],
        "binding_targets_applied": ["scientific-verification"],
        "source_registry_path": "skills/custom/.skill-studio-registry.json",
    }

    monkeypatch.setattr(
        "deerflow.agents.middlewares.skill_runtime_snapshot_middleware.capture_skill_runtime_snapshot",
        lambda: snapshot,
    )

    result = middleware.before_model(
        state={"messages": []},
        runtime=Runtime(context={}),
    )

    assert result == {"skill_runtime_snapshot": snapshot}


def test_before_model_backfills_legacy_snapshot_prompt_entries(monkeypatch):
    middleware = SkillRuntimeSnapshotMiddleware()
    monkeypatch.setattr(
        "deerflow.agents.middlewares.skill_runtime_snapshot_middleware._resolve_skills_root",
        lambda: "skills-root",
    )
    monkeypatch.setattr(
        "deerflow.agents.middlewares.skill_runtime_snapshot_middleware.load_skills_from_path",
        lambda *args, **kwargs: [_fake_skill("cached-skill", "Pinned cached skill")],
    )

    result = middleware.before_model(
        state={
            "messages": [],
            "skill_runtime_snapshot": {
                "runtime_revision": 1,
                "captured_at": "2026-04-10T08:00:00Z",
                "enabled_skill_names": ["cached-skill"],
                "binding_targets_applied": ["scientific-verification"],
                "source_registry_path": "skills/custom/.skill-studio-registry.json",
            },
        },
        runtime=Runtime(context={}),
    )

    assert result is not None
    assert result["skill_runtime_snapshot"]["skill_prompt_entries"][0]["name"] == (
        "cached-skill"
    )


def test_capture_skill_runtime_snapshot_uses_fresh_live_enabled_skills(monkeypatch):
    monkeypatch.setattr(
        "deerflow.agents.middlewares.skill_runtime_snapshot_middleware._resolve_skills_root",
        lambda: "skills-root",
    )
    monkeypatch.setattr(
        "deerflow.agents.middlewares.skill_runtime_snapshot_middleware.load_skill_lifecycle_registry",
        lambda *args, **kwargs: SimpleNamespace(runtime_revision=5, records={}),
    )
    monkeypatch.setattr(
        "deerflow.agents.lead_agent.prompt._get_enabled_skills_snapshot",
        lambda: [_fake_skill("stale-skill", "Stale skill")],
    )
    monkeypatch.setattr(
        "deerflow.agents.middlewares.skill_runtime_snapshot_middleware.load_skills_from_path",
        lambda *args, **kwargs: [_fake_skill("fresh-skill", "Fresh skill")],
        raising=False,
    )

    snapshot = capture_skill_runtime_snapshot()

    assert snapshot["enabled_skill_names"] == ["fresh-skill"]


def test_override_skill_snapshot_rewrites_system_prompt(monkeypatch):
    middleware = SkillRuntimeSnapshotMiddleware()
    monkeypatch.setattr(
        "deerflow.agents.middlewares.skill_runtime_snapshot_middleware.apply_prompt_template",
        lambda **kwargs: (
            "skills="
            + ",".join(sorted(kwargs.get("available_skills") or []))
            + ";bindings="
            + ",".join(kwargs.get("skill_snapshot", {}).get("binding_targets_applied", []))
        ),
    )

    request = _build_request()
    overridden = middleware._override_skill_snapshot(
        request,
        {
            "runtime_revision": 3,
            "enabled_skill_names": ["cached-skill"],
            "binding_targets_applied": ["result-reporting"],
            "captured_at": "2026-04-10T08:00:00Z",
            "source_registry_path": "skills/custom/.skill-studio-registry.json",
        },
    )

    assert "cached-skill" in overridden.system_prompt
    assert "fresh-skill" not in overridden.system_prompt
    assert "result-reporting" in overridden.system_prompt
