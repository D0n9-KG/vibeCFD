from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.gateway.routers import skills


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

    with _client_for_skills(tmp_path, monkeypatch) as client:
        response = client.get("/api/skills/graph")

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["skill_count"] == 2
    assert data["summary"]["relationship_counts"]["depend_on"] >= 1
    assert any(
        edge["relationship_type"] == "depend_on"
        and edge["source"] == "submarine-result-acceptance"
        and edge["target"] == "submarine-report"
        for edge in data["relationships"]
    )


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

    with _client_for_skills(tmp_path, monkeypatch) as client:
        response = client.get(
            "/api/skills/graph",
            params={"skill_name": "submarine-result-acceptance"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["focus"]["skill_name"] == "submarine-result-acceptance"
    assert data["focus"]["related_skill_count"] >= 1
    assert any(
        related["skill_name"] == "submarine-report"
        for related in data["focus"]["related_skills"]
    )
