"""Lifecycle registry helpers for Skill Studio draft and publish state."""

from __future__ import annotations

import json
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
