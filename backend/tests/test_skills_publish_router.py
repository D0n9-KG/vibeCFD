from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.gateway.routers import skills
from deerflow.config.extensions_config import ExtensionsConfig
from deerflow.config.paths import Paths
from deerflow.domain.submarine.skill_lifecycle import load_skill_lifecycle_registry
from deerflow.domain.submarine.skill_studio import run_skill_studio


def _build_skill_archive(
    tmp_path: Path,
    thread_id: str = "thread-1",
    *,
    skill_purpose_suffix: str = "",
    workflow_suffix: str = "",
) -> tuple[Paths, str, Path]:
    paths = Paths(tmp_path)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    payload, _ = run_skill_studio(
        outputs_dir=outputs_dir,
        skill_name="Submarine Result Acceptance",
        skill_purpose=(
            "Define how Claude Code and reporting subagents should decide whether a "
            "submarine CFD run is trustworthy, needs review, or should be rerun."
            f"{skill_purpose_suffix}"
        ),
        trigger_conditions=[
            "the user asks whether the current CFD result is trustworthy",
            "Claude Code needs a final acceptance decision before delivery",
        ],
        workflow_steps=[
            "review mesh, residual, and force summaries from the current run"
            f"{workflow_suffix}",
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


def _create_client(tmp_path: Path, monkeypatch, archive_paths) -> TestClient:
    skills_root = tmp_path / "skills"
    config_path = tmp_path / "extensions_config.json"

    def resolve_archive(thread_id: str, _path: str) -> Path:
        if isinstance(archive_paths, dict):
            return archive_paths[thread_id]
        return archive_paths

    monkeypatch.setattr(
        skills,
        "resolve_thread_virtual_path",
        resolve_archive,
    )
    monkeypatch.setattr(skills, "get_skills_root_path", lambda: skills_root)
    monkeypatch.setattr(
        skills.ExtensionsConfig,
        "resolve_config_path",
        staticmethod(lambda *_args, **_kwargs: config_path),
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
                "version_note": "Promote acceptance skill",
                "binding_targets": [
                    {
                        "role_id": "scientific-verification",
                        "mode": "explicit",
                        "target_skills": ["submarine-result-acceptance"],
                    },
                ],
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

    registry = load_skill_lifecycle_registry(
        registry_path=tmp_path / "skills" / "custom" / ".skill-studio-registry.json",
    )
    record = registry.records["submarine-result-acceptance"]
    assert record.enabled is True
    assert record.version_note == "Promote acceptance skill"
    assert record.binding_targets[0].role_id == "scientific-verification"
    assert record.binding_targets[0].target_skills == ["submarine-result-acceptance"]
    assert record.last_published_at is not None
    assert record.last_published_from_thread_id == "thread-1"


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
                "version_note": "",
                "binding_targets": [],
            },
        )
        overwritten = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": archive_virtual_path,
                "overwrite": True,
                "enable": True,
                "version_note": "Overwrite publish",
                "binding_targets": [
                    {
                        "role_id": "result-reporting",
                        "mode": "explicit",
                        "target_skills": ["submarine-result-acceptance"],
                    },
                ],
            },
        )

    assert conflict.status_code == 409
    assert overwritten.status_code == 200
    assert "updated successfully" in overwritten.json()["message"]

    registry = load_skill_lifecycle_registry(
        registry_path=tmp_path / "skills" / "custom" / ".skill-studio-registry.json",
    )
    record = registry.records["submarine-result-acceptance"]
    assert record.version_note == "Overwrite publish"
    assert record.binding_targets[0].role_id == "result-reporting"


def test_publish_skill_route_tracks_revisions_and_supports_rollback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _, archive_virtual_path_one, archive_path_one = _build_skill_archive(
        tmp_path,
        "thread-1",
        skill_purpose_suffix=" First release for reviewers.",
    )
    _, archive_virtual_path_two, archive_path_two = _build_skill_archive(
        tmp_path,
        "thread-2",
        skill_purpose_suffix=" Second release with rollback coverage.",
        workflow_suffix=" and compare against the rollback baseline",
    )

    with _create_client(
        tmp_path,
        monkeypatch,
        {
            "thread-1": archive_path_one,
            "thread-2": archive_path_two,
        },
    ) as client:
        first_publish = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": archive_virtual_path_one,
                "overwrite": False,
                "enable": True,
                "version_note": "First release",
                "binding_targets": [
                    {
                        "role_id": "scientific-verification",
                        "mode": "explicit",
                        "target_skills": ["submarine-result-acceptance"],
                    },
                ],
            },
        )
        second_publish = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-2",
                "path": archive_virtual_path_two,
                "overwrite": True,
                "enable": False,
                "version_note": "Second release",
                "binding_targets": [
                    {
                        "role_id": "result-reporting",
                        "mode": "explicit",
                        "target_skills": ["submarine-result-acceptance"],
                    },
                ],
            },
        )

        rollback = client.post(
            "/api/skills/submarine-result-acceptance/rollback",
            json={"revision_id": "rev-001"},
        )

    assert first_publish.status_code == 200
    assert second_publish.status_code == 200
    assert rollback.status_code == 200

    registry = load_skill_lifecycle_registry(
        registry_path=tmp_path / "skills" / "custom" / ".skill-studio-registry.json",
    )
    record = registry.records["submarine-result-acceptance"]
    revision_dir = (
        tmp_path
        / "skills"
        / "custom"
        / "submarine-result-acceptance"
        / ".revisions"
    )
    assert (revision_dir / "rev-001.skill").is_file() is True
    assert (revision_dir / "rev-002.skill").is_file() is True
    assert len(record.published_revisions) == 2
    assert record.active_revision_id == "rev-001"
    assert record.rollback_target_id == "rev-002"
    assert record.version_note == "First release"
    assert record.binding_targets[0].role_id == "scientific-verification"
    assert record.enabled is True

    installed_skill = (
        tmp_path / "skills" / "custom" / "submarine-result-acceptance" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "First release for reviewers." in installed_skill
    assert "Second release with rollback coverage." not in installed_skill

    rollback_data = rollback.json()
    assert rollback_data["skill_name"] == "submarine-result-acceptance"
    assert rollback_data["active_revision_id"] == "rev-001"
    assert rollback_data["rollback_target_id"] == "rev-002"
    assert rollback_data["revision_count"] == 2
    assert rollback_data["binding_count"] == 1
