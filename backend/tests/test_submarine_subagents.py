import importlib

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


def test_submarine_workflow_prompt_section_requires_confirmed_brief_before_execution():
    section = prompt_module.get_submarine_workflow_prompt_section()

    assert "submarine_design_brief" in section
    assert "ask_clarification" in section
    assert "submarine_geometry_check" in section
    assert "submarine_solver_dispatch" in section
    assert "Do NOT answer submarine CFD requests directly" in section
    assert "wait for explicit user confirmation" in section


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
    boundaries = {
        boundary.role_id: boundary for boundary in get_subagent_role_boundaries()
    }

    geometry_preflight = boundaries["geometry-preflight"]

    assert "STL" in geometry_preflight.responsibility
    assert ".x_t" not in geometry_preflight.responsibility


def test_submarine_role_boundaries_include_scientific_capability_roles():
    boundaries = {
        boundary.role_id: boundary for boundary in get_subagent_role_boundaries()
    }

    assert {
        "scientific-study",
        "experiment-compare",
        "scientific-verification",
        "scientific-followup",
    } <= boundaries.keys()
