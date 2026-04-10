import asyncio
import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

from deerflow.domain.submarine.skill_lifecycle import (
    SkillLifecycleBinding,
    SkillLifecycleRecord,
    SkillLifecycleRegistry,
)

prompt_module = importlib.import_module("deerflow.agents.lead_agent.prompt")


def _fake_skill(name: str, description: str):
    return SimpleNamespace(
        name=name,
        description=description,
        get_container_file_path=lambda container_base_path="/mnt/skills": f"{container_base_path}/public/{name}/SKILL.md",
    )


def test_subagent_skill_routing_prompt_section_lists_recommendations(monkeypatch):
    recommendations = {
        "submarine-task-intelligence": {"submarine-case-search"},
        "submarine-geometry-preflight": {"submarine-geometry-check"},
        "submarine-solver-dispatch": {"submarine-solver-dispatch"},
        "submarine-scientific-study": {"submarine-solver-dispatch"},
        "submarine-experiment-compare": {
            "submarine-report",
            "submarine-solver-dispatch",
        },
        "submarine-scientific-verification": {
            "submarine-report",
            "submarine-result-acceptance",
        },
        "submarine-result-reporting": {"submarine-report", "submarine-result-acceptance"},
        "submarine-scientific-followup": {
            "submarine-report",
            "submarine-solver-dispatch",
        },
    }

    monkeypatch.setattr(
        prompt_module,
        "recommend_skills_for_subagent",
        lambda subagent_name: recommendations.get(subagent_name),
    )

    section = prompt_module.get_subagent_skill_routing_prompt_section()

    assert "<subagent_skill_routing>" in section
    assert "target_skills" in section
    assert "- submarine-geometry-preflight: submarine-geometry-check" in section
    assert "- submarine-scientific-study: submarine-solver-dispatch" in section
    assert "- submarine-scientific-verification: submarine-report, submarine-result-acceptance" in section
    assert "- submarine-result-reporting: submarine-report, submarine-result-acceptance" in section


def test_apply_prompt_template_includes_skill_routing_when_subagents_enabled(monkeypatch):
    monkeypatch.setattr(prompt_module, "get_skills_prompt_section", lambda available_skills=None: "<skill_system />")
    monkeypatch.setattr(prompt_module, "get_subagent_skill_routing_prompt_section", lambda: "<subagent_skill_routing />")
    monkeypatch.setattr(prompt_module, "get_project_skill_bindings_prompt_section", lambda: "<project_skill_bindings />")
    monkeypatch.setattr(prompt_module, "get_skill_studio_workflow_prompt_section", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(prompt_module, "get_deferred_tools_prompt_section", lambda: "")
    monkeypatch.setattr(prompt_module, "get_agent_soul", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(prompt_module, "_get_memory_context", lambda *_args, **_kwargs: "")

    prompt = prompt_module.apply_prompt_template(subagent_enabled=True, agent_name="tester")

    assert "<skill_system />" in prompt
    assert "<subagent_skill_routing />" in prompt
    assert "<project_skill_bindings />" in prompt


def test_skill_studio_workflow_prompt_section_is_only_included_for_skill_creators():
    section = prompt_module.get_skill_studio_workflow_prompt_section("codex-skill-creator")

    assert "<skill_studio_workflow_protocol>" in section
    assert "submarine_skill_studio" in section
    assert "skill-draft.json" in section
    assert "Do not stop at a conversational acknowledgement" in section
    assert "minimal validation or test-skill request is usually enough" in section

    assert prompt_module.get_skill_studio_workflow_prompt_section("tester") == ""


def test_apply_prompt_template_for_skill_creator_requires_structured_skill_studio_artifacts(
    monkeypatch,
):
    monkeypatch.setattr(prompt_module, "get_skills_prompt_section", lambda available_skills=None: "<skill_system />")
    monkeypatch.setattr(prompt_module, "get_subagent_skill_routing_prompt_section", lambda: "")
    monkeypatch.setattr(prompt_module, "get_project_skill_bindings_prompt_section", lambda: "")
    monkeypatch.setattr(prompt_module, "get_deferred_tools_prompt_section", lambda: "")
    monkeypatch.setattr(prompt_module, "get_agent_soul", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(prompt_module, "_get_memory_context", lambda *_args, **_kwargs: "")

    prompt = prompt_module.apply_prompt_template(
        subagent_enabled=False,
        agent_name="codex-skill-creator",
    )

    assert "<skill_studio_workflow_protocol>" in prompt
    assert "submarine_skill_studio" in prompt
    assert "validation-report" in prompt
    assert "publish-readiness" in prompt

def test_project_skill_bindings_prompt_section_lists_explicit_role_bindings(monkeypatch):
    monkeypatch.setattr(
        prompt_module,
        "load_skill_lifecycle_registry",
        lambda: SkillLifecycleRegistry(
            records={
                "submarine-result-acceptance": SkillLifecycleRecord(
                    skill_name="submarine-result-acceptance",
                    skill_asset_id="submarine-result-acceptance",
                    source_thread_id="thread-1",
                    draft_status="published",
                    draft_updated_at="2026-04-04T00:00:00Z",
                    package_archive_virtual_path="/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/submarine-result-acceptance.skill",
                    artifact_virtual_paths=[],
                    active_revision_id=None,
                    published_revision_id=None,
                    version_note="Promote acceptance skill",
                    bindings=[],
                    published_revisions=[],
                    enabled=True,
                    binding_targets=[
                        SkillLifecycleBinding(
                            role_id="scientific-verification",
                            mode="explicit",
                            target_skills=["submarine-result-acceptance"],
                        ),
                    ],
                    published_path="skills/custom/submarine-result-acceptance",
                    last_published_at="2026-04-04T01:00:00Z",
                    last_published_from_thread_id="thread-1",
                    rollback_target_id=None,
                ),
            },
        ),
    )

    section = prompt_module.get_project_skill_bindings_prompt_section()

    assert "<project_skill_bindings>" in section
    assert "- task-intelligence -> enabled skill pool" in section
    assert "- scientific-verification -> submarine-result-acceptance" in section
    assert "- result-reporting -> enabled skill pool" in section


def test_get_skills_prompt_section_uses_cached_skill_snapshot_when_available(monkeypatch):
    monkeypatch.setattr(
        prompt_module,
        "_CACHED_ENABLED_SKILLS",
        [_fake_skill("cached-skill", "Cached skill")],
        raising=False,
    )
    monkeypatch.setattr(
        prompt_module,
        "_CACHED_ENABLED_SKILLS_SOURCE_STATE",
        ("same",),
        raising=False,
    )
    monkeypatch.setattr(
        prompt_module,
        "_get_enabled_skills_snapshot_source_state",
        lambda: ("same",),
        raising=False,
    )
    monkeypatch.setattr(
        prompt_module,
        "load_skills",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("load_skills should not run when cache is warm")),
    )
    monkeypatch.setattr(
        prompt_module,
        "get_app_config",
        lambda: SimpleNamespace(skills=SimpleNamespace(container_path="/mnt/skills")),
        raising=False,
    )

    section = prompt_module.get_skills_prompt_section()

    assert "cached-skill" in section
    assert "/mnt/skills/public/cached-skill/SKILL.md" in section


def test_get_skills_prompt_section_retries_after_failed_snapshot_load(monkeypatch):
    attempts = {"count": 0}

    monkeypatch.setattr(prompt_module, "_CACHED_ENABLED_SKILLS", None, raising=False)
    monkeypatch.setattr(
        prompt_module,
        "_CACHED_ENABLED_SKILLS_SOURCE_STATE",
        None,
        raising=False,
    )
    monkeypatch.setattr(
        prompt_module,
        "_get_enabled_skills_snapshot_source_state",
        lambda: ("retry",),
        raising=False,
    )

    def _load_skills(*_args, **_kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary failure")
        return [_fake_skill("fresh-skill", "Fresh skill")]

    monkeypatch.setattr(prompt_module, "load_skills", _load_skills)
    monkeypatch.setattr(
        prompt_module,
        "get_app_config",
        lambda: SimpleNamespace(skills=SimpleNamespace(container_path="/mnt/skills")),
        raising=False,
    )

    first = prompt_module.get_skills_prompt_section()
    second = prompt_module.get_skills_prompt_section()

    assert first == ""
    assert "fresh-skill" in second
    assert attempts["count"] == 2


def test_get_skills_prompt_section_refreshes_when_source_state_changes(monkeypatch):
    current_state = {"value": ("before",)}

    monkeypatch.setattr(
        prompt_module,
        "_CACHED_ENABLED_SKILLS",
        [_fake_skill("stale-skill", "Stale skill")],
        raising=False,
    )
    monkeypatch.setattr(
        prompt_module,
        "_CACHED_ENABLED_SKILLS_SOURCE_STATE",
        ("before",),
        raising=False,
    )
    monkeypatch.setattr(
        prompt_module,
        "_get_enabled_skills_snapshot_source_state",
        lambda: current_state["value"],
        raising=False,
    )
    monkeypatch.setattr(
        prompt_module,
        "load_skills",
        lambda *args, **kwargs: [_fake_skill("fresh-skill", "Fresh skill")],
    )
    monkeypatch.setattr(
        prompt_module,
        "get_app_config",
        lambda: SimpleNamespace(skills=SimpleNamespace(container_path="/mnt/skills")),
        raising=False,
    )

    current_state["value"] = ("after",)
    section = prompt_module.get_skills_prompt_section()

    assert "fresh-skill" in section
    assert "stale-skill" not in section


def test_get_skills_prompt_section_prefers_captured_snapshot_over_live_enabled_pool(
    monkeypatch,
):
    monkeypatch.setattr(
        prompt_module,
        "_get_enabled_skills_snapshot",
        lambda: [_fake_skill("fresh-skill", "Fresh skill")],
        raising=False,
    )
    monkeypatch.setattr(
        prompt_module,
        "load_skills",
        lambda *args, **kwargs: [
            _fake_skill("cached-skill", "Cached skill"),
            _fake_skill("fresh-skill", "Fresh skill"),
        ],
    )
    monkeypatch.setattr(
        prompt_module,
        "get_app_config",
        lambda: SimpleNamespace(skills=SimpleNamespace(container_path="/mnt/skills")),
        raising=False,
    )

    section = prompt_module.get_skills_prompt_section(
        skill_snapshot={
            "runtime_revision": 1,
            "enabled_skill_names": ["cached-skill"],
            "binding_targets_applied": ["scientific-verification"],
            "source_registry_path": "skills/custom/.skill-studio-registry.json",
        }
    )

    assert "cached-skill" in section
    assert "fresh-skill" not in section


def test_get_skills_prompt_section_legacy_snapshot_does_not_rebuild_live_metadata(
    monkeypatch,
):
    monkeypatch.setattr(
        prompt_module,
        "load_skills",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("load_skills should not run for legacy pinned snapshots")
        ),
    )

    section = prompt_module.get_skills_prompt_section(
        skill_snapshot={
            "runtime_revision": 1,
            "enabled_skill_names": ["cached-skill"],
            "binding_targets_applied": ["scientific-verification"],
            "source_registry_path": "skills/custom/.skill-studio-registry.json",
        }
    )

    assert "cached-skill" in section
    assert "legacy thread snapshot" in section


def test_get_skills_prompt_section_uses_snapshot_prompt_entries_without_live_lookup(
    monkeypatch,
):
    monkeypatch.setattr(
        prompt_module,
        "load_skills",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("load_skills should not run when snapshot entries exist")
        ),
    )

    section = prompt_module.get_skills_prompt_section(
        skill_snapshot={
            "enabled_skill_names": ["cached-skill"],
            "skill_prompt_entries": [
                {
                    "name": "cached-skill",
                    "description": "Pinned cached skill",
                    "location": "/mnt/skills/custom/cached-skill/SKILL.md",
                }
            ],
        }
    )

    assert "cached-skill" in section
    assert "Pinned cached skill" in section
    assert "/mnt/skills/custom/cached-skill/SKILL.md" in section


def test_get_enabled_skills_snapshot_source_state_avoids_recursive_scan_when_cache_exists(
    tmp_path,
    monkeypatch,
):
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "public" / "demo-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("---\nname: demo-skill\n---\n", encoding="utf-8")

    monkeypatch.setattr(
        prompt_module,
        "_CACHED_ENABLED_SKILLS",
        [
            SimpleNamespace(
                name="demo-skill",
                description="Demo skill",
                skill_dir=skill_dir,
                skill_file=skill_file,
                relative_path=Path("demo-skill"),
                category="public",
            )
        ],
        raising=False,
    )
    monkeypatch.setattr(
        "deerflow.config.get_app_config",
        lambda: SimpleNamespace(
            skills=SimpleNamespace(get_skills_path=lambda: skills_root)
        ),
    )
    monkeypatch.setattr(
        Path,
        "rglob",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("rglob should not run when cached skills are present")
        ),
        raising=False,
    )

    state = prompt_module._get_enabled_skills_snapshot_source_state()

    assert state is not None
    assert state[-1] == 1


def test_get_enabled_skills_snapshot_returns_stale_cache_inside_running_loop(monkeypatch):
    cached_skill = _fake_skill("cached-skill", "Cached skill")

    monkeypatch.setattr(
        prompt_module,
        "_CACHED_ENABLED_SKILLS",
        [cached_skill],
        raising=False,
    )
    monkeypatch.setattr(
        prompt_module,
        "_CACHED_ENABLED_SKILLS_SOURCE_STATE",
        ("before",),
        raising=False,
    )
    monkeypatch.setattr(
        prompt_module,
        "_get_enabled_skills_snapshot_source_state",
        lambda: ("after",),
        raising=False,
    )
    monkeypatch.setattr(
        prompt_module,
        "load_skills",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("load_skills should not run synchronously in an active event loop")
        ),
    )
    monkeypatch.setattr(
        prompt_module,
        "_refresh_enabled_skills_snapshot_in_background",
        lambda: None,
        raising=False,
    )

    result = asyncio.run(_call_snapshot(prompt_module))

    assert result[0].name == "cached-skill"


async def _call_snapshot(module):
    return module._get_enabled_skills_snapshot()


def test_enabled_skills_snapshot_source_state_changes_when_skill_file_changes(
    tmp_path,
    monkeypatch,
):
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "public" / "demo-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("---\nname: demo-skill\n---\n", encoding="utf-8")

    monkeypatch.setattr(
        "deerflow.config.get_app_config",
        lambda: SimpleNamespace(
            skills=SimpleNamespace(get_skills_path=lambda: skills_root)
        ),
    )

    first = prompt_module._get_enabled_skills_snapshot_source_state()
    next_mtime = skill_file.stat().st_mtime + 5
    os.utime(skill_file, (next_mtime, next_mtime))
    second = prompt_module._get_enabled_skills_snapshot_source_state()

    assert second != first


def test_enabled_skills_snapshot_source_state_changes_when_runtime_revision_changes(
    tmp_path,
    monkeypatch,
):
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "public" / "demo-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("---\nname: demo-skill\n---\n", encoding="utf-8")

    registry_path = skills_root / "custom" / ".skill-studio-registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps({"version": "1.0", "records": {}}, indent=2),
        encoding="utf-8",
    )

    runtime_revision = {"value": 1}

    monkeypatch.setattr(
        "deerflow.config.get_app_config",
        lambda: SimpleNamespace(
            skills=SimpleNamespace(get_skills_path=lambda: skills_root)
        ),
    )
    monkeypatch.setattr(prompt_module, "_CACHED_ENABLED_SKILLS", None, raising=False)
    monkeypatch.setattr(
        prompt_module,
        "load_skill_lifecycle_registry",
        lambda *args, **kwargs: SimpleNamespace(
            runtime_revision=runtime_revision["value"]
        ),
    )
    monkeypatch.setattr(
        prompt_module,
        "get_skill_lifecycle_registry_path",
        lambda *args, **kwargs: registry_path,
        raising=False,
    )

    first = prompt_module._get_enabled_skills_snapshot_source_state()
    runtime_revision["value"] = 2
    second = prompt_module._get_enabled_skills_snapshot_source_state()

    assert second != first
