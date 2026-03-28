import importlib

prompt_module = importlib.import_module("deerflow.agents.lead_agent.prompt")


def test_subagent_skill_routing_prompt_section_lists_recommendations(monkeypatch):
    recommendations = {
        "submarine-task-intelligence": {"submarine-case-search"},
        "submarine-geometry-preflight": {"submarine-geometry-check"},
        "submarine-solver-dispatch": {"submarine-solver-dispatch"},
        "submarine-result-reporting": {"submarine-report", "submarine-result-acceptance"},
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
    assert "- submarine-result-reporting: submarine-report, submarine-result-acceptance" in section


def test_apply_prompt_template_includes_skill_routing_when_subagents_enabled(monkeypatch):
    monkeypatch.setattr(prompt_module, "get_skills_prompt_section", lambda available_skills=None: "<skill_system />")
    monkeypatch.setattr(prompt_module, "get_subagent_skill_routing_prompt_section", lambda: "<subagent_skill_routing />")
    monkeypatch.setattr(prompt_module, "get_deferred_tools_prompt_section", lambda: "")
    monkeypatch.setattr(prompt_module, "get_agent_soul", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(prompt_module, "_get_memory_context", lambda *_args, **_kwargs: "")

    prompt = prompt_module.apply_prompt_template(subagent_enabled=True, agent_name="tester")

    assert "<skill_system />" in prompt
    assert "<subagent_skill_routing />" in prompt
