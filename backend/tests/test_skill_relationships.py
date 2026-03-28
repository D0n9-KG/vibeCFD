from pathlib import Path

from deerflow.skills.relationships import (
    analyze_skill_relationships,
    recommend_skills_for_subagent,
)


def _write_skill(
    root: Path,
    category: str,
    name: str,
    description: str,
    body: str,
) -> None:
    skill_dir = root / category / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                f"description: {description}",
                "---",
                "",
                f"# {name}",
                "",
                body,
                "",
            ],
        ),
        encoding="utf-8",
    )


def test_analyze_skill_relationships_builds_local_skill_graph(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        "public",
        "submarine-report",
        "Use when synthesizing submarine CFD results into reviewable final reports.",
        "Focus on Chinese summaries and final report packaging.",
    )
    _write_skill(
        tmp_path,
        "public",
        "submarine-geometry-check",
        "Use when checking submarine STL geometry before solver dispatch.",
        "Focus on geometry readiness, scale checks, and preprocessing risks.",
    )
    _write_skill(
        tmp_path,
        "custom",
        "submarine-result-acceptance",
        "Use when reviewing submarine CFD result acceptance and final report trustworthiness.",
        (
            "Compose with submarine-report when the user needs a final delivery decision.\n"
            "Review mesh, residual, and force summaries before deciding whether the run is trustworthy."
        ),
    )
    _write_skill(
        tmp_path,
        "public",
        "skill-creator",
        "Use when creating new skills from expert rules and reusable workflows.",
        "Generate SKILL.md files and related package structure.",
    )

    graph = analyze_skill_relationships(skills_path=tmp_path)

    assert graph.summary.skill_count == 4
    assert graph.summary.enabled_skill_count == 4
    assert graph.summary.custom_skill_count == 1
    assert graph.summary.public_skill_count == 3
    assert graph.summary.edge_count >= 3
    assert graph.summary.relationship_counts["similar_to"] >= 1
    assert graph.summary.relationship_counts["compose_with"] >= 1
    assert graph.summary.relationship_counts["depend_on"] >= 1

    related_names = {node.name for node in graph.skills}
    assert related_names == {
        "submarine-report",
        "submarine-geometry-check",
        "submarine-result-acceptance",
        "skill-creator",
    }

    assert any(
        edge.source == "submarine-result-acceptance"
        and edge.target == "submarine-report"
        and edge.relationship_type == "depend_on"
        for edge in graph.relationships
    )
    assert any(
        {
            edge.source,
            edge.target,
        }
        == {"submarine-result-acceptance", "submarine-report"}
        and edge.relationship_type == "similar_to"
        for edge in graph.relationships
    )
    assert any(
        {
            edge.source,
            edge.target,
        }
        == {"submarine-geometry-check", "submarine-report"}
        and edge.relationship_type == "compose_with"
        for edge in graph.relationships
    )


def test_analyze_skill_relationships_can_focus_on_one_skill(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        "public",
        "submarine-report",
        "Use when synthesizing submarine CFD results into reviewable final reports.",
        "Focus on Chinese summaries and final report packaging.",
    )
    _write_skill(
        tmp_path,
        "custom",
        "submarine-result-acceptance",
        "Use when reviewing submarine CFD result acceptance and final report trustworthiness.",
        "Compose with submarine-report when the user needs a final delivery decision.",
    )

    graph = analyze_skill_relationships(
        skills_path=tmp_path,
        focus_skill_name="submarine-result-acceptance",
    )

    assert graph.focus is not None
    assert graph.focus.skill_name == "submarine-result-acceptance"
    assert graph.focus.related_skill_count >= 1
    assert any(
        item.skill_name == "submarine-report"
        for item in graph.focus.related_skills
    )


def test_recommend_skills_for_subagent_uses_stage_and_graph_context(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        "public",
        "submarine-geometry-check",
        "Use when checking submarine STL geometry before solver dispatch.",
        "Focus on geometry readiness, scale checks, and preprocessing risks.",
    )
    _write_skill(
        tmp_path,
        "public",
        "submarine-solver-dispatch",
        "Use when preparing OpenFOAM solver dispatch after geometry validation.",
        "Compose with submarine-geometry-check for CFD execution readiness.",
    )
    _write_skill(
        tmp_path,
        "public",
        "submarine-report",
        "Use when synthesizing submarine CFD results into reviewable final reports.",
        "Focus on Chinese summaries and final report packaging.",
    )
    _write_skill(
        tmp_path,
        "custom",
        "submarine-result-acceptance",
        "Use when reviewing submarine CFD result acceptance and final report trustworthiness.",
        "Compose with submarine-report when the user needs a final delivery decision.",
    )

    dispatch_skills = recommend_skills_for_subagent(
        "submarine-solver-dispatch",
        skills_path=tmp_path,
    )
    reporting_skills = recommend_skills_for_subagent(
        "submarine-result-reporting",
        skills_path=tmp_path,
    )

    assert "submarine-solver-dispatch" in dispatch_skills
    assert "submarine-geometry-check" in dispatch_skills
    assert "submarine-result-acceptance" not in dispatch_skills

    assert "submarine-report" in reporting_skills
    assert "submarine-result-acceptance" in reporting_skills
    assert "submarine-geometry-check" not in reporting_skills
