from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.gateway.routers import skills
from deerflow.domain.submarine.skill_lifecycle import (
    SkillLifecycleBinding,
    SkillLifecycleRecord,
    SkillLifecycleRegistry,
    SkillLifecycleRevision,
    save_skill_lifecycle_registry,
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


def _client_for_skills(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.setattr(skills, "get_skills_root_path", lambda: tmp_path)
    app = FastAPI()
    app.include_router(skills.router)
    return TestClient(app)


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
                            archive_path=str(root / "custom" / "submarine-result-acceptance" / ".revisions" / "rev-001.skill"),
                            published_path=str(root / "custom" / "submarine-result-acceptance"),
                            version_note="Initial publish",
                            binding_targets=[],
                            enabled=True,
                            source_thread_id="thread-1",
                        ),
                        SkillLifecycleRevision(
                            revision_id="rev-002",
                            published_at="2026-04-04T01:00:00Z",
                            archive_path=str(root / "custom" / "submarine-result-acceptance" / ".revisions" / "rev-002.skill"),
                            published_path=str(root / "custom" / "submarine-result-acceptance"),
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


def test_skill_graph_route_returns_summary_and_edges(tmp_path: Path, monkeypatch) -> None:
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

    with _client_for_skills(tmp_path, monkeypatch) as client:
        response = client.get("/api/skills/graph")

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["skill_count"] == 2
    assert data["summary"]["relationship_counts"]["depend_on"] >= 1
    assert any(edge["relationship_type"] == "depend_on" and edge["source"] == "submarine-result-acceptance" and edge["target"] == "submarine-report" for edge in data["relationships"])
    acceptance_node = next(node for node in data["skills"] if node["name"] == "submarine-result-acceptance")
    assert acceptance_node["revision_count"] == 2
    assert acceptance_node["active_revision_id"] == "rev-002"
    assert acceptance_node["rollback_target_id"] == "rev-001"
    assert acceptance_node["binding_count"] == 1
    assert acceptance_node["last_published_at"] == "2026-04-04T01:00:00Z"


def test_skill_graph_route_supports_focus_skill(tmp_path: Path, monkeypatch) -> None:
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

    with _client_for_skills(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/skills/graph",
            params={"skill_name": "submarine-report"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["focus"]["skill_name"] == "submarine-report"
    assert data["focus"]["related_skill_count"] >= 1
    related_item = next(related for related in data["focus"]["related_skills"] if related["skill_name"] == "submarine-result-acceptance")
    assert related_item["revision_count"] == 2
    assert related_item["binding_count"] == 1
    assert related_item["rollback_target_id"] == "rev-001"
