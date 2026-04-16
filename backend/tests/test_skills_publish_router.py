import asyncio
import json
import zipfile
from pathlib import Path
from types import SimpleNamespace

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
) -> tuple[dict[tuple[str, str], Path], dict[str, str]]:
    paths = Paths(tmp_path)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    payload, _ = run_skill_studio(
        outputs_dir=outputs_dir,
        skill_name="Submarine Result Acceptance",
        skill_purpose=(f"Define how Claude Code and reporting subagents should decide whether a submarine CFD run is trustworthy, needs review, or should be rerun.{skill_purpose_suffix}"),
        trigger_conditions=[
            "the user asks whether the current CFD result is trustworthy",
            "Claude Code needs a final acceptance decision before delivery",
        ],
        workflow_steps=[
            f"review mesh, residual, and force summaries from the current run{workflow_suffix}",
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
    archive_path = outputs_dir / "submarine" / "skill-studio" / skill_slug / f"{skill_slug}.skill"
    draft_virtual_path = f"/mnt/user-data/outputs/submarine/skill-studio/{skill_slug}/skill-draft.json"
    draft_path = outputs_dir / "submarine" / "skill-studio" / skill_slug / "skill-draft.json"
    return (
        {
            (thread_id, archive_virtual_path): archive_path,
            (thread_id, draft_virtual_path): draft_path,
        },
        {
            "archive": archive_virtual_path,
            "draft": draft_virtual_path,
        },
    )


def _create_client(
    tmp_path: Path,
    monkeypatch,
    resolved_paths: dict[tuple[str, str], Path],
    *,
    thread_message_ids: dict[str, list[str]] | None = None,
) -> TestClient:
    skills_root = tmp_path / "skills"
    config_path = tmp_path / "extensions_config.json"
    traceable_message_ids = thread_message_ids or {
        "thread-1": ["msg-1", "msg-2"],
        "thread-2": ["msg-2"],
    }

    def resolve_archive(thread_id: str, path: str) -> Path:
        return resolved_paths[(thread_id, path)]

    async def load_thread_state(thread_id: str) -> dict:
        return {"values": {"messages": [{"id": message_id, "type": "ai", "content": ""} for message_id in traceable_message_ids.get(thread_id, [])]}}

    monkeypatch.setattr(
        skills,
        "resolve_thread_virtual_path",
        resolve_archive,
    )
    monkeypatch.setattr(skills, "_load_thread_state", load_thread_state)
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


def test_load_thread_state_uses_configured_langgraph_url(monkeypatch) -> None:
    recorded: dict[str, str] = {}

    class RecordingThreads:
        async def get_state(self, thread_id: str) -> dict:
            recorded["thread_id"] = thread_id
            return {"values": {"messages": []}}

    def fake_get_client(*, url: str):
        recorded["url"] = url
        return SimpleNamespace(threads=RecordingThreads())

    monkeypatch.setattr(
        skills,
        "get_app_config",
        lambda: SimpleNamespace(model_extra={"channels": {"langgraph_url": "http://localhost:3024"}}),
    )
    monkeypatch.setattr("langgraph_sdk.get_client", fake_get_client)

    result = asyncio.run(skills._load_thread_state("thread-1"))

    assert recorded["url"] == "http://localhost:3024"
    assert recorded["thread_id"] == "thread-1"
    assert result == {"values": {"messages": []}}


def test_publish_skill_route_installs_and_enables_skill(tmp_path: Path, monkeypatch) -> None:
    resolved_paths, virtual_paths = _build_skill_archive(tmp_path)

    with _create_client(tmp_path, monkeypatch, resolved_paths) as client:
        evidence = client.post(
            "/api/skills/dry-run-evidence",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["draft"],
                "status": "passed",
                "scenario_id": "scenario-1",
                "message_ids": ["msg-1", "msg-2"],
                "reviewer_note": "Dry run matches the acceptance rubric.",
            },
        )
        response = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["archive"],
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

    assert evidence.status_code == 200
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["skill_name"] == "submarine-result-acceptance"
    assert data["enabled"] is True
    assert data["published_path"].replace("\\", "/").endswith(
        "skills/custom/submarine-result-acceptance",
    )
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
    resolved_paths, virtual_paths = _build_skill_archive(tmp_path)
    installed_dir = tmp_path / "skills" / "custom" / "submarine-result-acceptance"
    installed_dir.mkdir(parents=True, exist_ok=True)
    (installed_dir / "SKILL.md").write_text(
        "---\nname: submarine-result-acceptance\ndescription: old\n---\n",
        encoding="utf-8",
    )

    with _create_client(tmp_path, monkeypatch, resolved_paths) as client:
        evidence = client.post(
            "/api/skills/dry-run-evidence",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["draft"],
                "status": "passed",
                "scenario_id": "scenario-1",
                "message_ids": ["msg-1"],
                "reviewer_note": "Evidence recorded before publish.",
            },
        )
        conflict = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["archive"],
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
                "path": virtual_paths["archive"],
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

    assert evidence.status_code == 200
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
    resolved_paths_one, virtual_paths_one = _build_skill_archive(
        tmp_path,
        "thread-1",
        skill_purpose_suffix=" First release for reviewers.",
    )
    resolved_paths_two, virtual_paths_two = _build_skill_archive(
        tmp_path,
        "thread-2",
        skill_purpose_suffix=" Second release with rollback coverage.",
        workflow_suffix=" and compare against the rollback baseline",
    )

    with _create_client(
        tmp_path,
        monkeypatch,
        resolved_paths_one | resolved_paths_two,
    ) as client:
        first_evidence = client.post(
            "/api/skills/dry-run-evidence",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths_one["draft"],
                "status": "passed",
                "scenario_id": "scenario-1",
                "message_ids": ["msg-1"],
                "reviewer_note": "First revision passed dry run.",
            },
        )
        first_publish = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths_one["archive"],
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
        second_evidence = client.post(
            "/api/skills/dry-run-evidence",
            json={
                "thread_id": "thread-2",
                "path": virtual_paths_two["draft"],
                "status": "passed",
                "scenario_id": "scenario-1",
                "message_ids": ["msg-2"],
                "reviewer_note": "Second revision passed dry run.",
            },
        )
        second_publish = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-2",
                "path": virtual_paths_two["archive"],
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

    assert first_evidence.status_code == 200
    assert first_publish.status_code == 200
    assert second_evidence.status_code == 200
    assert second_publish.status_code == 200
    assert rollback.status_code == 200

    registry = load_skill_lifecycle_registry(
        registry_path=tmp_path / "skills" / "custom" / ".skill-studio-registry.json",
    )
    record = registry.records["submarine-result-acceptance"]
    revision_dir = tmp_path / "skills" / "custom" / "submarine-result-acceptance" / ".revisions"
    assert (revision_dir / "rev-001.skill").is_file() is True
    assert (revision_dir / "rev-002.skill").is_file() is True
    assert len(record.published_revisions) == 2
    assert record.active_revision_id == "rev-001"
    assert record.rollback_target_id == "rev-002"
    assert record.version_note == "First release"
    assert record.binding_targets[0].role_id == "scientific-verification"
    assert record.enabled is True

    installed_skill = (tmp_path / "skills" / "custom" / "submarine-result-acceptance" / "SKILL.md").read_text(encoding="utf-8")
    assert "review mesh, residual, and force summaries from the current run" in installed_skill
    assert "Second release with rollback coverage." not in installed_skill
    assert "compare against the rollback baseline" not in installed_skill

    rollback_data = rollback.json()
    assert rollback_data["skill_name"] == "submarine-result-acceptance"
    assert rollback_data["active_revision_id"] == "rev-001"
    assert rollback_data["rollback_target_id"] == "rev-002"
    assert rollback_data["revision_count"] == 2
    assert rollback_data["binding_count"] == 1


def test_publish_skill_route_rejects_archive_without_passing_dry_run_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    resolved_paths, virtual_paths = _build_skill_archive(tmp_path)

    with _create_client(tmp_path, monkeypatch, resolved_paths) as client:
        response = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["archive"],
                "overwrite": False,
                "enable": True,
                "version_note": "",
                "binding_targets": [],
            },
        )

    assert response.status_code == 400
    assert "dry-run evidence" in response.json()["detail"]

    registry = load_skill_lifecycle_registry(
        registry_path=tmp_path / "skills" / "custom" / ".skill-studio-registry.json",
    )
    assert registry.records == {}
    assert (tmp_path / "skills" / "custom" / "submarine-result-acceptance").exists() is False


def test_record_dry_run_evidence_rejects_passed_status_without_traceable_message_ids(
    tmp_path: Path,
    monkeypatch,
) -> None:
    resolved_paths, virtual_paths = _build_skill_archive(tmp_path)

    with _create_client(tmp_path, monkeypatch, resolved_paths) as client:
        response = client.post(
            "/api/skills/dry-run-evidence",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["draft"],
                "status": "passed",
                "scenario_id": "scenario-1",
                "message_ids": [],
                "reviewer_note": "Claimed passed without traceable evidence.",
            },
        )

    assert response.status_code == 400
    assert "message_ids" in response.json()["detail"]


def test_record_dry_run_evidence_rejects_message_ids_not_present_in_thread_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    resolved_paths, virtual_paths = _build_skill_archive(tmp_path)

    with _create_client(tmp_path, monkeypatch, resolved_paths) as client:
        response = client.post(
            "/api/skills/dry-run-evidence",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["draft"],
                "status": "passed",
                "scenario_id": "scenario-1",
                "message_ids": ["fake-1"],
                "reviewer_note": "Claimed passed with fabricated evidence ids.",
            },
        )

    assert response.status_code == 400
    assert "do not belong" in response.json()["detail"]


def test_publish_skill_route_rejects_archive_without_ready_for_review_publish_status(
    tmp_path: Path,
    monkeypatch,
) -> None:
    resolved_paths, virtual_paths = _build_skill_archive(tmp_path)
    archive_path = resolved_paths[("thread-1", virtual_paths["archive"])]

    with _create_client(tmp_path, monkeypatch, resolved_paths) as client:
        evidence = client.post(
            "/api/skills/dry-run-evidence",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["draft"],
                "status": "passed",
                "scenario_id": "scenario-1",
                "message_ids": ["msg-1"],
                "reviewer_note": "Dry run passed, but readiness is intentionally corrupted.",
            },
        )

        rewritten_archive_path = archive_path.with_name("blocked-publish-readiness.skill")
        with zipfile.ZipFile(archive_path, "r") as source_archive:
            with zipfile.ZipFile(
                rewritten_archive_path,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as target_archive:
                for member in source_archive.infolist():
                    if member.is_dir():
                        continue

                    contents = source_archive.read(member)
                    if Path(member.filename).name == "publish-readiness.json":
                        payload = json.loads(contents)
                        payload["status"] = "blocked"
                        payload["blocking_count"] = max(
                            int(payload.get("blocking_count", 0)),
                            1,
                        )
                        contents = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

                    target_archive.writestr(member.filename, contents)

        archive_path.unlink()
        rewritten_archive_path.replace(archive_path)

        response = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["archive"],
                "overwrite": False,
                "enable": True,
                "version_note": "",
                "binding_targets": [],
            },
        )

    assert evidence.status_code == 200
    assert response.status_code == 400
    assert "publish readiness" in response.json()["detail"]

    registry = load_skill_lifecycle_registry(
        registry_path=tmp_path / "skills" / "custom" / ".skill-studio-registry.json",
    )
    assert registry.records == {}


def test_publish_skill_route_rejects_archive_with_untraceable_root_dry_run_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    resolved_paths, virtual_paths = _build_skill_archive(tmp_path)
    archive_path = resolved_paths[("thread-1", virtual_paths["archive"])]

    with _create_client(tmp_path, monkeypatch, resolved_paths) as client:
        evidence = client.post(
            "/api/skills/dry-run-evidence",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["draft"],
                "status": "passed",
                "scenario_id": "scenario-1",
                "message_ids": ["msg-1"],
                "reviewer_note": "Dry run passed before archive tampering.",
            },
        )

        rewritten_archive_path = archive_path.with_name("blocked-untraceable-evidence.skill")
        with zipfile.ZipFile(archive_path, "r") as source_archive:
            with zipfile.ZipFile(
                rewritten_archive_path,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as target_archive:
                for member in source_archive.infolist():
                    if member.is_dir():
                        continue

                    contents = source_archive.read(member)
                    if Path(member.filename).name == "dry-run-evidence.json":
                        payload = json.loads(contents)
                        payload["message_ids"] = []
                        contents = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

                    target_archive.writestr(member.filename, contents)

        archive_path.unlink()
        rewritten_archive_path.replace(archive_path)

        response = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["archive"],
                "overwrite": False,
                "enable": True,
                "version_note": "",
                "binding_targets": [],
            },
        )

    assert evidence.status_code == 200
    assert response.status_code == 400
    assert "traceable" in response.json()["detail"]


def test_publish_skill_route_rejects_archive_with_fabricated_traceable_message_ids(
    tmp_path: Path,
    monkeypatch,
) -> None:
    resolved_paths, virtual_paths = _build_skill_archive(tmp_path)
    archive_path = resolved_paths[("thread-1", virtual_paths["archive"])]

    with _create_client(tmp_path, monkeypatch, resolved_paths) as client:
        evidence = client.post(
            "/api/skills/dry-run-evidence",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["draft"],
                "status": "passed",
                "scenario_id": "scenario-1",
                "message_ids": ["msg-1"],
                "reviewer_note": "Dry run passed before archive tampering.",
            },
        )

        rewritten_archive_path = archive_path.with_name("blocked-fabricated-evidence.skill")
        with zipfile.ZipFile(archive_path, "r") as source_archive:
            with zipfile.ZipFile(
                rewritten_archive_path,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as target_archive:
                for member in source_archive.infolist():
                    if member.is_dir():
                        continue

                    contents = source_archive.read(member)
                    if Path(member.filename).name == "dry-run-evidence.json":
                        payload = json.loads(contents)
                        payload["message_ids"] = ["fake-1"]
                        contents = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

                    target_archive.writestr(member.filename, contents)

        archive_path.unlink()
        rewritten_archive_path.replace(archive_path)

        response = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["archive"],
                "overwrite": False,
                "enable": True,
                "version_note": "",
                "binding_targets": [],
            },
        )

    assert evidence.status_code == 200
    assert response.status_code == 400
    assert "do not belong" in response.json()["detail"]


def test_publish_skill_route_rejects_nested_dry_run_evidence_outside_archive_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    resolved_paths, virtual_paths = _build_skill_archive(tmp_path)
    archive_path = resolved_paths[("thread-1", virtual_paths["archive"])]
    rewritten_archive_path = archive_path.with_name("nested-evidence.skill")

    with zipfile.ZipFile(archive_path, "r") as source_archive:
        with zipfile.ZipFile(
            rewritten_archive_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as target_archive:
            for member in source_archive.infolist():
                if member.is_dir():
                    continue
                if Path(member.filename).name == "dry-run-evidence.json":
                    continue
                target_archive.writestr(member.filename, source_archive.read(member))

            target_archive.writestr(
                "submarine-result-acceptance/assets/dry-run-evidence.json",
                json.dumps(
                    {
                        "skill_name": "submarine-result-acceptance",
                        "status": "passed",
                    }
                ),
            )

    archive_path.unlink()
    rewritten_archive_path.replace(archive_path)

    with _create_client(tmp_path, monkeypatch, resolved_paths) as client:
        response = client.post(
            "/api/skills/publish",
            json={
                "thread_id": "thread-1",
                "path": virtual_paths["archive"],
                "overwrite": False,
                "enable": True,
                "version_note": "",
                "binding_targets": [],
            },
        )

    assert response.status_code == 400
    assert "dry-run evidence" in response.json()["detail"]
