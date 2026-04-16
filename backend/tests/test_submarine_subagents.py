import importlib
from pathlib import Path

from deerflow.agents.lead_agent.prompt import apply_prompt_template
from deerflow.domain.submarine.roles import get_subagent_role_boundaries
from deerflow.subagents.registry import get_subagent_names

prompt_module = importlib.import_module("deerflow.agents.lead_agent.prompt")


def test_submarine_subagents_are_registered():
    names = set(get_subagent_names())

    assert {
        "submarine-task-intelligence",
        "submarine-geometry-preflight",
        "submarine-solver-dispatch",
        "submarine-scientific-study",
        "submarine-experiment-compare",
        "submarine-scientific-verification",
        "submarine-result-reporting",
        "submarine-scientific-followup",
    } <= names


def test_subagent_prompt_mentions_submarine_roles():
    prompt = apply_prompt_template(subagent_enabled=True)

    assert "submarine-task-intelligence" in prompt
    assert "submarine-geometry-preflight" in prompt
    assert "submarine-solver-dispatch" in prompt
    assert "submarine-scientific-study" in prompt
    assert "submarine-experiment-compare" in prompt
    assert "submarine-scientific-verification" in prompt
    assert "submarine-result-reporting" in prompt
    assert "submarine-scientific-followup" in prompt


def test_submarine_workflow_prompt_section_requires_approval_for_solver_execution_but_allows_safe_preflight():
    section = prompt_module.get_submarine_workflow_prompt_section()

    assert "submarine_design_brief" in section
    assert "ask_clarification" in section
    assert "submarine_geometry_check" in section
    assert "submarine_solver_dispatch" in section
    assert "Do NOT answer submarine CFD requests directly" in section
    assert "approved execution" in section
    assert "high-risk execution" in section
    assert "geometry-only" in section
    assert "solver dispatch still waits for explicit user confirmation" in section


def test_submarine_workflow_prompt_section_is_guidance_first_not_stage_mandatory():
    section = prompt_module.get_submarine_workflow_prompt_section()

    assert "primary agent" in section.lower()
    assert "recommended" in section.lower()
    assert "follow this protocol strictly" not in section.lower()
    assert "always capture or refresh the structured plan" not in section.lower()


def test_submarine_workflow_prompt_section_refreshes_design_brief_on_material_contract_changes():
    section = prompt_module.get_submarine_workflow_prompt_section()

    assert "contract revision" in section.lower()
    assert "changes outputs" in section.lower()
    assert "variant strategy" in section.lower()
    assert "update `submarine_design_brief` first" in section.lower()


def test_submarine_workflow_prompt_section_requires_confirmed_brief_before_solver_dispatch():
    section = prompt_module.get_submarine_workflow_prompt_section()

    assert 'confirmation_status="confirmed"' in section
    assert "rerun `submarine_design_brief`" in section.lower()
    assert "before calling `submarine_solver_dispatch`" in section.lower()
    assert 'approval_state="approved"' in section


def test_submarine_workflow_prompt_section_forbids_todo_only_replies_when_bound_stl_and_concrete_request_exist():
    section = prompt_module.get_submarine_workflow_prompt_section()

    assert "write_todos" in section
    assert "same turn" in section.lower()
    assert "bound STL" in section
    assert "generic acknowledgement" in section.lower()
    assert "submarine_geometry_check" in section


def test_submarine_workflow_prompt_section_keeps_draft_when_confirmation_is_partial():
    section = prompt_module.get_submarine_workflow_prompt_section()

    assert 'confirmation_status="draft"' in section
    assert "still-unresolved items" in section
    assert "stop before solver dispatch" in section.lower()


def test_apply_prompt_template_includes_submarine_workflow_protocol(monkeypatch):
    monkeypatch.setattr(
        prompt_module,
        "get_submarine_workflow_prompt_section",
        lambda: "<submarine_workflow_protocol />",
    )
    monkeypatch.setattr(prompt_module, "get_skills_prompt_section", lambda available_skills=None: "")
    monkeypatch.setattr(prompt_module, "get_subagent_skill_routing_prompt_section", lambda: "")
    monkeypatch.setattr(prompt_module, "get_deferred_tools_prompt_section", lambda: "")
    monkeypatch.setattr(prompt_module, "get_agent_soul", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(prompt_module, "_get_memory_context", lambda *_args, **_kwargs: "")

    prompt = prompt_module.apply_prompt_template(subagent_enabled=True)

    assert "<submarine_workflow_protocol />" in prompt


def test_submarine_role_boundaries_keep_stl_only_v1_language():
    boundaries = {boundary.role_id: boundary for boundary in get_subagent_role_boundaries()}

    geometry_preflight = boundaries["geometry-preflight"]

    assert "STL" in geometry_preflight.responsibility
    assert ".x_t" not in geometry_preflight.responsibility


def test_submarine_role_boundaries_include_scientific_capability_roles():
    boundaries = {boundary.role_id: boundary for boundary in get_subagent_role_boundaries()}

    assert {
        "scientific-study",
        "experiment-compare",
        "scientific-verification",
        "scientific-followup",
    } <= boundaries.keys()


def test_submarine_orchestrator_skill_guides_judgment_without_fixed_tool_order():
    skill_path = Path(__file__).resolve().parents[2] / "skills" / "public" / "submarine-orchestrator" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")

    assert "when the primary agent should" in content.lower()
    assert "use the built-in tools in this order" not in content.lower()
    assert "required orchestration path" not in content.lower()


def test_submarine_orchestrator_skill_mentions_confirmation_refresh_before_execution():
    skill_path = Path(__file__).resolve().parents[2] / "skills" / "public" / "submarine-orchestrator" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")

    assert 'confirmation_status="confirmed"' in content
    assert "submarine_design_brief" in content
    assert "before `submarine_solver_dispatch`" in content
