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

    geometry_skill = skills["submarine-geometry-check"].skill_file.read_text(encoding="utf-8")
    orchestrator_skill = skills["submarine-orchestrator"].skill_file.read_text(encoding="utf-8")

    assert "STL-only" in geometry_skill
    assert "STL-only" in orchestrator_skill


def test_submarine_case_search_skill_does_not_point_subagents_to_raw_repo_paths():
    skills = {skill.name: skill for skill in load_skills(enabled_only=False)}

    case_search_skill = skills["submarine-case-search"].skill_file.read_text(encoding="utf-8")

    assert "domain/submarine/cases/index.json" not in case_search_skill


def test_iterative_core_skills_speak_contract_delivery_and_lineage_language():
    skills = {skill.name: skill for skill in load_skills(enabled_only=False)}

    orchestrator_skill = skills["submarine-orchestrator"].skill_file.read_text(encoding="utf-8")
    report_skill = skills["submarine-report"].skill_file.read_text(encoding="utf-8")
    dispatch_skill = skills["submarine-solver-dispatch"].skill_file.read_text(encoding="utf-8")

    assert "contract_revision" in orchestrator_skill
    assert "output_delivery_plan" in orchestrator_skill
    assert "baseline_reference_run_id" in orchestrator_skill
    assert "compare_target_run_id" in orchestrator_skill

    assert "output_delivery_plan" in report_skill
    assert "support_level" in report_skill
    assert "requested_outputs" in report_skill

    assert "contract_revision" in dispatch_skill
    assert "requested_output_ids" in dispatch_skill
    assert "lineage" in dispatch_skill.lower()
