import json

from deerflow.domain.submarine.skill_lifecycle import (
    SkillLifecycleRevision,
    append_skill_lifecycle_revision,
    SkillLifecycleBinding,
    SkillLifecycleRecord,
    SkillLifecycleRegistry,
    get_next_skill_revision_id,
    get_skill_lifecycle_registry_path,
    get_skill_revision_archive_path,
    load_skill_lifecycle_registry,
    merge_skill_lifecycle_record,
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


def test_skill_lifecycle_registry_round_trip_preserves_runtime_revision(tmp_path) -> None:
    registry_path = tmp_path / "skills" / "custom" / ".skill-studio-registry.json"
    registry = SkillLifecycleRegistry()

    written_path = save_skill_lifecycle_registry(registry, registry_path=registry_path)
    loaded_registry = load_skill_lifecycle_registry(registry_path=written_path)

    on_disk = json.loads(written_path.read_text(encoding="utf-8"))

    assert on_disk.get("runtime_revision") == 0
    assert getattr(loaded_registry, "runtime_revision", None) == 0


def test_merge_skill_lifecycle_record_syncs_bindings_and_publish_metadata(tmp_path) -> None:
    existing_record = SkillLifecycleRecord(
        skill_name="submarine-result-acceptance",
        skill_asset_id="submarine-result-acceptance",
        source_thread_id="thread-1",
        draft_status="draft_ready",
        draft_updated_at="2026-04-04T00:00:00Z",
        package_archive_virtual_path="/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/submarine-result-acceptance.skill",
        artifact_virtual_paths=[],
        active_revision_id=None,
        published_revision_id=None,
        version_note="old note",
        bindings=[],
        published_revisions=[],
        enabled=False,
        binding_targets=[],
        published_path=str(tmp_path / "skills" / "custom" / "submarine-result-acceptance"),
        last_published_at="2026-04-04T00:00:00Z",
        last_published_from_thread_id="thread-1",
        rollback_target_id=None,
    )

    merged = merge_skill_lifecycle_record(
        skill_name="submarine-result-acceptance",
        existing_record=existing_record,
        enabled=True,
        version_note="Publish for verification stage",
        binding_targets=[
            SkillLifecycleBinding(
                role_id="scientific-verification",
                mode="explicit",
                target_skills=["submarine-result-acceptance"],
            ),
        ],
        published_path=str(tmp_path / "skills" / "custom" / "submarine-result-acceptance"),
        last_published_at="2026-04-04T01:00:00Z",
        last_published_from_thread_id="thread-2",
    )

    assert merged.enabled is True
    assert merged.version_note == "Publish for verification stage"
    assert merged.binding_targets[0].role_id == "scientific-verification"
    assert merged.binding_targets[0].target_skills == ["submarine-result-acceptance"]
    assert merged.bindings[0].role_id == "scientific-verification"
    assert merged.last_published_at == "2026-04-04T01:00:00Z"
    assert merged.last_published_from_thread_id == "thread-2"
    assert merged.published_path == str(
        tmp_path / "skills" / "custom" / "submarine-result-acceptance"
    )


def test_revision_helpers_generate_hidden_archive_paths_and_rollback_targets(
    tmp_path,
) -> None:
    record = SkillLifecycleRecord(
        skill_name="submarine-result-acceptance",
        skill_asset_id="submarine-result-acceptance",
        draft_status="published",
        artifact_virtual_paths=[],
        active_revision_id=None,
        published_revision_id=None,
        version_note="",
        bindings=[],
        published_revisions=[],
        enabled=True,
        binding_targets=[],
        rollback_target_id=None,
    )

    revision_one_path = get_skill_revision_archive_path(
        "submarine-result-acceptance",
        "rev-001",
        skills_root=tmp_path / "skills",
    )
    assert revision_one_path.as_posix().endswith(
        "skills/custom/submarine-result-acceptance/.revisions/rev-001.skill"
    )
    assert get_next_skill_revision_id(record) == "rev-001"

    record = append_skill_lifecycle_revision(
        record,
        revision=SkillLifecycleRevision(
            revision_id="rev-001",
            published_at="2026-04-04T00:00:00Z",
            archive_path=str(revision_one_path),
            published_path=str(
                tmp_path / "skills" / "custom" / "submarine-result-acceptance"
            ),
            version_note="Initial publish",
            binding_targets=[],
            enabled=True,
            source_thread_id="thread-1",
        ),
    )
    assert record.active_revision_id == "rev-001"
    assert record.rollback_target_id is None
    assert get_next_skill_revision_id(record) == "rev-002"

    record = append_skill_lifecycle_revision(
        record,
        revision=SkillLifecycleRevision(
            revision_id="rev-002",
            published_at="2026-04-04T01:00:00Z",
            archive_path=str(
                get_skill_revision_archive_path(
                    "submarine-result-acceptance",
                    "rev-002",
                    skills_root=tmp_path / "skills",
                )
            ),
            published_path=str(
                tmp_path / "skills" / "custom" / "submarine-result-acceptance"
            ),
            version_note="Second publish",
            binding_targets=[
                SkillLifecycleBinding(
                    role_id="scientific-verification",
                    mode="explicit",
                    target_skills=["submarine-result-acceptance"],
                ),
            ],
            enabled=False,
            source_thread_id="thread-2",
        ),
    )
    assert record.active_revision_id == "rev-002"
    assert record.published_revision_id == "rev-002"
    assert record.rollback_target_id == "rev-001"
    assert record.version_note == "Second publish"
    assert record.enabled is False
