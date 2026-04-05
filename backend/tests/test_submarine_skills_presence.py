from deerflow.skills import load_skills


def test_submarine_skills_are_discoverable():
    skills = load_skills(enabled_only=False)
    names = {skill.name for skill in skills}

    assert {
        "submarine-case-search",
        "submarine-geometry-check",
        "submarine-solver-dispatch",
        "submarine-report",
    } <= names


def test_submarine_v1_skills_reinforce_stl_only_runtime_boundary():
    skills = {skill.name: skill for skill in load_skills(enabled_only=False)}

    geometry_skill = skills["submarine-geometry-check"].skill_file.read_text(
        encoding="utf-8"
    )
    orchestrator_skill = skills["submarine-orchestrator"].skill_file.read_text(
        encoding="utf-8"
    )

    assert "STL-only" in geometry_skill
    assert "STL-only" in orchestrator_skill


def test_submarine_case_search_skill_does_not_point_subagents_to_raw_repo_paths():
    skills = {skill.name: skill for skill in load_skills(enabled_only=False)}

    case_search_skill = skills["submarine-case-search"].skill_file.read_text(
        encoding="utf-8"
    )

    assert "domain/submarine/cases/index.json" not in case_search_skill
