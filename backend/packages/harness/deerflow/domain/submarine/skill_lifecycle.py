"""Lifecycle registry helpers for Skill Studio draft and publish state."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from deerflow.skills.loader import get_skills_root_path


class SkillLifecycleBinding(BaseModel):
    role_id: str
    mode: str
    target_skills: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class SkillLifecycleRevision(BaseModel):
    revision_id: str
    published_at: str
    archive_path: str
    published_path: str
    version_note: str = ""
    binding_targets: list[SkillLifecycleBinding] = Field(default_factory=list)
    enabled: bool = True
    source_thread_id: str | None = None

    model_config = ConfigDict(extra="forbid")


class SkillLifecycleDraftState(BaseModel):
    skill_name: str
    skill_asset_id: str
    source_thread_id: str | None = None
    draft_status: str
    draft_updated_at: str | None = None
    package_archive_virtual_path: str | None = None
    artifact_virtual_paths: list[str] = Field(default_factory=list)
    active_revision_id: str | None = None
    published_revision_id: str | None = None
    version_note: str = ""
    bindings: list[SkillLifecycleBinding] = Field(default_factory=list)
    published_revisions: list[SkillLifecycleRevision] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class SkillLifecycleRecord(SkillLifecycleDraftState):
    enabled: bool = False
    binding_targets: list[SkillLifecycleBinding] = Field(default_factory=list)
    published_path: str | None = None
    last_published_at: str | None = None
    last_published_from_thread_id: str | None = None
    rollback_target_id: str | None = None

    model_config = ConfigDict(extra="forbid")


class SkillLifecycleRegistry(BaseModel):
    version: str = "1.0"
    records: dict[str, SkillLifecycleRecord] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


def utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def build_default_skill_lifecycle_record(
    skill_name: str,
    *,
    enabled: bool = False,
    published_path: str | None = None,
) -> SkillLifecycleRecord:
    return SkillLifecycleRecord(
        skill_name=skill_name,
        skill_asset_id=skill_name,
        draft_status="published" if published_path else "draft_ready",
        enabled=enabled,
        published_path=published_path,
    )


def load_skill_lifecycle_record(
    lifecycle_path: Path | None,
) -> SkillLifecycleRecord | None:
    if lifecycle_path is None:
        return None

    resolved_path = Path(lifecycle_path)
    if not resolved_path.exists():
        return None

    with resolved_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return SkillLifecycleRecord.model_validate(payload)


def merge_skill_lifecycle_record(
    *,
    skill_name: str,
    lifecycle_payload: SkillLifecycleRecord | None = None,
    existing_record: SkillLifecycleRecord | None = None,
    enabled: bool | None = None,
    version_note: str | None = None,
    binding_targets: list[SkillLifecycleBinding] | None = None,
    published_path: str | None = None,
    last_published_at: str | None = None,
    last_published_from_thread_id: str | None = None,
) -> SkillLifecycleRecord:
    merged = (
        existing_record.model_copy(deep=True)
        if existing_record is not None
        else build_default_skill_lifecycle_record(
            skill_name,
            published_path=published_path,
            enabled=enabled or False,
        )
    )

    if lifecycle_payload is not None:
        merged.skill_asset_id = lifecycle_payload.skill_asset_id
        merged.source_thread_id = lifecycle_payload.source_thread_id
        merged.draft_status = lifecycle_payload.draft_status
        merged.draft_updated_at = lifecycle_payload.draft_updated_at
        merged.package_archive_virtual_path = lifecycle_payload.package_archive_virtual_path
        merged.artifact_virtual_paths = list(lifecycle_payload.artifact_virtual_paths)
        merged.version_note = lifecycle_payload.version_note
        merged.bindings = [
            binding.model_copy(deep=True)
            for binding in lifecycle_payload.bindings
        ]
        if lifecycle_payload.active_revision_id is not None:
            merged.active_revision_id = lifecycle_payload.active_revision_id
        if lifecycle_payload.published_revision_id is not None:
            merged.published_revision_id = lifecycle_payload.published_revision_id
        if lifecycle_payload.published_revisions:
            merged.published_revisions = [
                revision.model_copy(deep=True)
                for revision in lifecycle_payload.published_revisions
            ]
        if not merged.binding_targets and merged.bindings:
            merged.binding_targets = [
                binding.model_copy(deep=True)
                for binding in merged.bindings
            ]

    if binding_targets is not None:
        merged.binding_targets = [
            SkillLifecycleBinding.model_validate(binding).model_copy(deep=True)
            for binding in binding_targets
        ]
        merged.bindings = [
            binding.model_copy(deep=True)
            for binding in merged.binding_targets
        ]
    elif not merged.binding_targets and merged.bindings:
        merged.binding_targets = [
            binding.model_copy(deep=True)
            for binding in merged.bindings
        ]
    elif not merged.bindings and merged.binding_targets:
        merged.bindings = [
            binding.model_copy(deep=True)
            for binding in merged.binding_targets
        ]

    if enabled is not None:
        merged.enabled = enabled
    if version_note is not None:
        merged.version_note = version_note
    if published_path is not None:
        merged.published_path = published_path
        if merged.draft_status == "draft_ready":
            merged.draft_status = "published"
    if last_published_at is not None:
        merged.last_published_at = last_published_at
    if last_published_from_thread_id is not None:
        merged.last_published_from_thread_id = last_published_from_thread_id

    return merged


def get_skill_lifecycle_registry_path(skills_root: Path | None = None) -> Path:
    root = Path(skills_root) if skills_root is not None else get_skills_root_path()
    return root / "custom" / ".skill-studio-registry.json"


def load_skill_lifecycle_registry(
    *,
    registry_path: Path | None = None,
    skills_root: Path | None = None,
) -> SkillLifecycleRegistry:
    resolved_path = (
        Path(registry_path)
        if registry_path is not None
        else get_skill_lifecycle_registry_path(skills_root)
    )
    if not resolved_path.exists():
        return SkillLifecycleRegistry()

    with resolved_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return SkillLifecycleRegistry.model_validate(payload)


def save_skill_lifecycle_registry(
    registry: SkillLifecycleRegistry,
    *,
    registry_path: Path | None = None,
    skills_root: Path | None = None,
) -> Path:
    resolved_path = (
        Path(registry_path)
        if registry_path is not None
        else get_skill_lifecycle_registry_path(skills_root)
    )
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    with resolved_path.open("w", encoding="utf-8") as handle:
        json.dump(registry.model_dump(mode="json"), handle, indent=2, ensure_ascii=False)
    return resolved_path
