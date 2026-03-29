from deerflow.agents.lead_agent.prompt import apply_prompt_template
from deerflow.domain.submarine.roles import get_subagent_role_boundaries
from deerflow.subagents.registry import get_subagent_names


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
