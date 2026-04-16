import importlib

tool_module = importlib.import_module("deerflow.tools.builtins.submarine_skill_studio_tool")


def test_submarine_skill_studio_tool_description_targets_generic_skill_studio_requests():
    description = tool_module.submarine_skill_studio_tool.description

    assert "Skill Studio" in description
    assert "publish-ready" in description
    assert "submarine-domain skill" not in description
