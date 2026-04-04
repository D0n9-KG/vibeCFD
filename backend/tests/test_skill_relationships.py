from pathlib import Path

from deerflow.domain.submarine.skill_lifecycle import (
    SkillLifecycleBinding,
    SkillLifecycleRecord,
    SkillLifecycleRegistry,
    SkillLifecycleRevision,
    save_skill_lifecycle_registry,
)
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


def _write_registry(root: Path) -> None:
    save_skill_lifecycle_registry(
        SkillLifecycleRegistry(
            records={
                "submarine-result-acceptance": SkillLifecycleRecord(
                    skill_name="submarine-result-acceptance",
                    skill_asset_id="submarine-result-acceptance",
                    draft_status="rollback_available",
                    artifact_virtual_paths=[],
                    active_revision_id="rev-002",
                    published_revision_id="rev-002",
                    version_note="Promote acceptance skill",
                    bindings=[],
                    published_revisions=[
                        SkillLifecycleRevision(
                            revision_id="rev-001",
                            published_at="2026-04-04T00:00:00Z",
                            archive_path=str(
                                root
                                / "custom"
                                / "submarine-result-acceptance"
                                / ".revisions"
                                / "rev-001.skill"
                            ),
                            published_path=str(
                                root / "custom" / "submarine-result-acceptance"
                            ),
                            version_note="Initial publish",
                            binding_targets=[],
                            enabled=True,
                            source_thread_id="thread-1",
                        ),
                        SkillLifecycleRevision(
                            revision_id="rev-002",
                            published_at="2026-04-04T01:00:00Z",
                            archive_path=str(
                                root
                                / "custom"
                                / "submarine-result-acceptance"
                                / ".revisions"
                                / "rev-002.skill"
                            ),
                            published_path=str(
                                root / "custom" / "submarine-result-acceptance"
                            ),
                            version_note="Promote acceptance skill",
                            binding_targets=[
                                SkillLifecycleBinding(
                                    role_id="scientific-verification",
                                    mode="explicit",
                                    target_skills=["submarine-result-acceptance"],
                                ),
                            ],
                            enabled=True,
                            source_thread_id="thread-2",
                        ),
                    ],
                    enabled=True,
                    binding_targets=[
                        SkillLifecycleBinding(
                            role_id="scientific-verification",
                            mode="explicit",
                            target_skills=["submarine-result-acceptance"],
                        ),
                    ],
                    published_path=str(root / "custom" / "submarine-result-acceptance"),
                    last_published_at="2026-04-04T01:00:00Z",
                    last_published_from_thread_id="thread-2",
                    rollback_target_id="rev-001",
                ),
            },
        ),
        skills_root=root,
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
    _write_registry(tmp_path)

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
    acceptance_node = next(
        node for node in graph.skills if node.name == "submarine-result-acceptance"
    )
    assert acceptance_node.revision_count == 2
    assert acceptance_node.binding_count == 1
    assert acceptance_node.rollback_target_id == "rev-001"
    assert acceptance_node.last_published_at == "2026-04-04T01:00:00Z"


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
    _write_registry(tmp_path)

    graph = analyze_skill_relationships(
        skills_path=tmp_path,
        focus_skill_name="submarine-report",
    )

    assert graph.focus is not None
    assert graph.focus.skill_name == "submarine-report"
    assert graph.focus.related_skill_count >= 1
    focused_item = next(
        item
        for item in graph.focus.related_skills
        if item.skill_name == "submarine-result-acceptance"
    )
    assert focused_item.revision_count == 2
    assert focused_item.binding_count == 1
    assert focused_item.active_revision_id == "rev-002"


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
