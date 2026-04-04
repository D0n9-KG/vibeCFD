import json

from deerflow.domain.submarine.skill_lifecycle import (
    SkillLifecycleRecord,
    SkillLifecycleRegistry,
    get_skill_lifecycle_registry_path,
    load_skill_lifecycle_registry,
    save_skill_lifecycle_registry,
)


def test_skill_lifecycle_registry_path_uses_hidden_custom_registry_file(tmp_path) -> None:
    registry_path = get_skill_lifecycle_registry_path(tmp_path / "skills")

    assert registry_path.as_posix().endswith("skills/custom/.skill-studio-registry.json")


def test_skill_lifecycle_registry_round_trip_preserves_empty_bindings_and_revisions(
    tmp_path,
) -> None:
    registry_path = tmp_path / "skills" / "custom" / ".skill-studio-registry.json"
    registry = SkillLifecycleRegistry(
        records={
            "submarine-result-acceptance": SkillLifecycleRecord(
                skill_name="submarine-result-acceptance",
                skill_asset_id="submarine-result-acceptance",
                source_thread_id="thread-1",
                draft_status="draft_ready",
                draft_updated_at="2026-04-04T00:00:00Z",
                package_archive_virtual_path="/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/submarine-result-acceptance.skill",
                artifact_virtual_paths=[
                    "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/skill-draft.json",
                    "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/skill-lifecycle.json",
                ],
                active_revision_id=None,
                published_revision_id=None,
                version_note="",
                bindings=[],
                published_revisions=[],
            ),
        },
    )

    written_path = save_skill_lifecycle_registry(registry, registry_path=registry_path)
    loaded_registry = load_skill_lifecycle_registry(registry_path=written_path)
    loaded_record = loaded_registry.records["submarine-result-acceptance"]

    assert written_path == registry_path
    assert loaded_record.skill_asset_id == "submarine-result-acceptance"
    assert loaded_record.bindings == []
    assert loaded_record.published_revisions == []

    on_disk = json.loads(registry_path.read_text(encoding="utf-8"))
    stored_record = on_disk["records"]["submarine-result-acceptance"]
    assert stored_record["bindings"] == []
    assert stored_record["published_revisions"] == []


def test_load_skill_lifecycle_registry_returns_empty_registry_when_missing(tmp_path) -> None:
    registry_path = tmp_path / "skills" / "custom" / ".skill-studio-registry.json"

    loaded_registry = load_skill_lifecycle_registry(registry_path=registry_path)

    assert loaded_registry.records == {}
