from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.gateway.routers import skills
from deerflow.config.extensions_config import ExtensionsConfig
from deerflow.config.paths import Paths
from deerflow.domain.submarine.skill_studio import run_skill_studio


def _build_skill_archive(tmp_path: Path, thread_id: str = "thread-1") -> tuple[Paths, str, Path]:
    paths = Paths(tmp_path)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    payload, _ = run_skill_studio(
        outputs_dir=outputs_dir,
        skill_name="Submarine Result Acceptance",
        skill_purpose=(
            "Define how Claude Code and reporting subagents should decide whether a "
            "submarine CFD run is trustworthy, needs review, or should be rerun."
        ),
        trigger_conditions=[
            "the user asks whether the current CFD result is trustworthy",
            "Claude Code needs a final acceptance decision before delivery",
        ],
        workflow_steps=[
            "review mesh, residual, and force summaries from the current run",
            "decide whether the run is deliverable, risky, or should be rerun",
            "produce a Chinese acceptance conclusion with evidence and next-step advice",
        ],
        expert_rules=[
            "flag drag values that materially diverge from the baseline case family",
        ],
        acceptance_criteria=[
            "state an explicit delivery decision",
            "cite which CFD indicators support that decision",
        ],
        test_scenarios=[
            "baseline steady-state bare-hull case with stable Cd and residual decay",
        ],
    )
    skill_slug = payload["skill_name"]
    archive_virtual_path = f"/mnt/user-data/outputs/submarine/skill-studio/{skill_slug}/{skill_slug}.skill"
    archive_path = (
        outputs_dir / "submarine" / "skill-studio" / skill_slug / f"{skill_slug}.skill"
    )
    return paths, archive_virtual_path, archive_path


def _create_client(tmp_path: Path, monkeypatch, archive_path: Path) -> TestClient:
    skills_root = tmp_path / "skills"
    config_path = tmp_path / "extensions_config.json"

    monkeypatch.setattr(
        skills,
        "resolve_thread_virtual_path",
        lambda _thread_id, _path: archive_path,
    )
    monkeypatch.setattr(skills, "get_skills_root_path", lambda: skills_root)
    monkeypatch.setattr(
        skills.ExtensionsConfig,
        "resolve_config_path",
        staticmethod(lambda: config_path),
    )
    monkeypatch.setattr(skills, "reload_extensions_config", lambda: None)
    monkeypatch.setattr(skills, "get_extensions_config", lambda: ExtensionsConfig())

    app = FastAPI()
    app.include_router(skills.router)
    return TestClient(app)


def test_publish_skill_route_installs_and_enables_skill(tmp_path: Path, monkeypatch) -> None:
    _, archive_virtual_path, archive_path = _build_skill_archive(tmp_path)

    with _create_client(tmp_path, monkeypatch, archive_path) as client:
        response = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": archive_virtual_path,
                "overwrite": False,
                "enable": True,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["skill_name"] == "submarine-result-acceptance"
    assert data["enabled"] is True
    assert data["published_path"].endswith("skills\\custom\\submarine-result-acceptance")
    installed_skill = tmp_path / "skills" / "custom" / "submarine-result-acceptance" / "SKILL.md"
    assert installed_skill.is_file() is True


def test_publish_skill_route_supports_overwrite(tmp_path: Path, monkeypatch) -> None:
    _, archive_virtual_path, archive_path = _build_skill_archive(tmp_path)
    installed_dir = tmp_path / "skills" / "custom" / "submarine-result-acceptance"
    installed_dir.mkdir(parents=True, exist_ok=True)
    (installed_dir / "SKILL.md").write_text(
        "---\nname: submarine-result-acceptance\ndescription: old\n---\n",
        encoding="utf-8",
    )

    with _create_client(tmp_path, monkeypatch, archive_path) as client:
        conflict = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": archive_virtual_path,
                "overwrite": False,
                "enable": True,
            },
        )
        overwritten = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": archive_virtual_path,
                "overwrite": True,
                "enable": True,
            },
        )

    assert conflict.status_code == 409
    assert overwritten.status_code == 200
    assert "updated successfully" in overwritten.json()["message"]
