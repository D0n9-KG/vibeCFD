import importlib

from deerflow.domain.submarine.skill_lifecycle import (
    SkillLifecycleBinding,
    SkillLifecycleRecord,
    SkillLifecycleRegistry,
)

prompt_module = importlib.import_module("deerflow.agents.lead_agent.prompt")


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
    monkeypatch.setattr(prompt_module, "get_deferred_tools_prompt_section", lambda: "")
    monkeypatch.setattr(prompt_module, "get_agent_soul", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(prompt_module, "_get_memory_context", lambda *_args, **_kwargs: "")

    prompt = prompt_module.apply_prompt_template(subagent_enabled=True, agent_name="tester")

    assert "<skill_system />" in prompt
    assert "<subagent_skill_routing />" in prompt
    assert "<project_skill_bindings />" in prompt


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
