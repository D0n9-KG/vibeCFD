import json
import logging
import os
import shutil
import socket
import stat
import tempfile
import zipfile
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.gateway.path_utils import resolve_thread_virtual_path
from deerflow.config.app_config import get_app_config
from deerflow.config.extensions_config import ExtensionsConfig, SkillStateConfig, get_extensions_config, reload_extensions_config
from deerflow.domain.submarine.skill_lifecycle import (
    SkillLifecycleBinding,
    SkillLifecycleRevision,
    SkillLifecycleRecord,
    SkillLifecycleRegistry,
    append_skill_lifecycle_revision,
    apply_skill_lifecycle_revision,
    bump_skill_runtime_revision,
    get_next_skill_revision_id,
    get_skill_lifecycle_binding_count,
    load_skill_lifecycle_record,
    load_skill_lifecycle_registry,
    get_skill_lifecycle_revision,
    get_skill_lifecycle_revision_count,
    get_skill_revision_archive_path,
    merge_skill_lifecycle_record,
    save_skill_lifecycle_registry,
    utc_timestamp,
)
from deerflow.domain.submarine.skill_studio import (
    record_skill_studio_dry_run_evidence,
)
from deerflow.skills import Skill, analyze_skill_relationships, load_skills
from deerflow.skills.loader import get_skills_root_path
from deerflow.skills.validation import _validate_skill_frontmatter

logger = logging.getLogger(__name__)
DEFAULT_LANGGRAPH_SERVER_URL = "http://localhost:2024"
LANGGRAPH_SERVER_ENV_KEYS = (
    "LANGGRAPH_PROXY_BASE_URL",
    "LANGGRAPH_SERVER_URL",
    "LANGGRAPH_BASE_URL",
    "NEXT_PUBLIC_LANGGRAPH_BASE_URL",
)
LANGGRAPH_LOCAL_FALLBACKS = (
    "http://127.0.0.1:2127",
    "http://localhost:2127",
    "http://127.0.0.1:2024",
    "http://localhost:2024",
)


def _is_unsafe_zip_member(info: zipfile.ZipInfo) -> bool:
    """Return True if the zip member path is absolute or attempts directory traversal."""
    name = info.filename
    if not name:
        return False
    path = Path(name)
    if path.is_absolute():
        return True
    if ".." in path.parts:
        return True
    return False


def _is_symlink_member(info: zipfile.ZipInfo) -> bool:
    """Detect symlinks based on the external attributes stored in the ZipInfo."""
    # Upper 16 bits of external_attr contain the Unix file mode when created on Unix.
    mode = info.external_attr >> 16
    return stat.S_ISLNK(mode)


def _safe_extract_skill_archive(
    zip_ref: zipfile.ZipFile,
    dest_path: Path,
    max_total_size: int = 512 * 1024 * 1024,
) -> None:
    """Safely extract a skill archive into dest_path with basic protections.

    Protections:
    - Reject absolute paths and directory traversal (..).
    - Skip symlink entries instead of materialising them.
    - Enforce a hard limit on total uncompressed size to mitigate zip bombs.
    """
    dest_root = Path(dest_path).resolve()
    total_size = 0

    for info in zip_ref.infolist():
        # Reject absolute paths or any path that attempts directory traversal.
        if _is_unsafe_zip_member(info):
            raise HTTPException(
                status_code=400,
                detail=f"Archive contains unsafe member path: {info.filename!r}",
            )

        # Skip any symlink entries instead of materialising them on disk.
        if _is_symlink_member(info):
            logger.warning("Skipping symlink entry in skill archive: %s", info.filename)
            continue

        # Basic unzip-bomb defence: bound the total uncompressed size we will write.
        total_size += max(info.file_size, 0)
        if total_size > max_total_size:
            raise HTTPException(
                status_code=400,
                detail="Skill archive is too large or appears highly compressed.",
            )

        member_path = dest_root / info.filename
        member_path_parent = member_path.parent
        member_path_parent.mkdir(parents=True, exist_ok=True)

        if info.is_dir():
            member_path.mkdir(parents=True, exist_ok=True)
            continue

        with zip_ref.open(info) as src, open(member_path, "wb") as dst:
            shutil.copyfileobj(src, dst)


router = APIRouter(prefix="/api", tags=["skills"])


class SkillResponse(BaseModel):
    """Response model for skill information."""

    name: str = Field(..., description="Name of the skill")
    description: str = Field(..., description="Description of what the skill does")
    license: str | None = Field(None, description="License information")
    category: str = Field(..., description="Category of the skill (public or custom)")
    enabled: bool = Field(default=True, description="Whether this skill is enabled")


class SkillsListResponse(BaseModel):
    """Response model for listing all skills."""

    skills: list[SkillResponse]


class SkillUpdateRequest(BaseModel):
    """Request model for updating a skill."""

    enabled: bool = Field(..., description="Whether to enable or disable the skill")


class SkillInstallRequest(BaseModel):
    """Request model for installing a skill from a .skill file."""

    thread_id: str = Field(..., description="The thread ID where the .skill file is located")
    path: str = Field(..., description="Virtual path to the .skill file (e.g., mnt/user-data/outputs/my-skill.skill)")


class SkillInstallResponse(BaseModel):
    """Response model for skill installation."""

    success: bool = Field(..., description="Whether the installation was successful")
    skill_name: str = Field(..., description="Name of the installed skill")
    message: str = Field(..., description="Installation result message")


class SkillGraphNodeResponse(BaseModel):
    name: str
    description: str
    category: str
    enabled: bool
    related_count: int
    stage: str | None = None
    revision_count: int = 0
    active_revision_id: str | None = None
    rollback_target_id: str | None = None
    binding_count: int = 0
    last_published_at: str | None = None


class SkillGraphRelationshipResponse(BaseModel):
    source: str
    target: str
    relationship_type: str
    score: float
    reason: str


class SkillGraphSummaryResponse(BaseModel):
    skill_count: int
    enabled_skill_count: int
    public_skill_count: int
    custom_skill_count: int
    edge_count: int
    relationship_counts: dict[str, int]


class SkillGraphFocusItemResponse(BaseModel):
    skill_name: str
    category: str
    enabled: bool
    description: str
    relationship_types: list[str]
    strongest_score: float
    reasons: list[str]
    revision_count: int = 0
    active_revision_id: str | None = None
    rollback_target_id: str | None = None
    binding_count: int = 0
    last_published_at: str | None = None


class SkillGraphFocusResponse(BaseModel):
    skill_name: str
    related_skill_count: int
    related_skills: list[SkillGraphFocusItemResponse]


class SkillGraphResponse(BaseModel):
    summary: SkillGraphSummaryResponse
    skills: list[SkillGraphNodeResponse]
    relationships: list[SkillGraphRelationshipResponse]
    focus: SkillGraphFocusResponse | None = None


class SkillPublishRequest(BaseModel):
    """Request model for publishing a drafted skill package into the project."""

    thread_id: str = Field(..., description="Thread ID where the generated .skill archive lives")
    path: str = Field(..., description="Virtual path to the generated .skill archive")
    overwrite: bool = Field(default=False, description="Whether to replace an existing custom skill with the same name")
    enable: bool = Field(default=True, description="Whether to enable the published skill in extensions_config.json")
    version_note: str = Field(default="", description="Optional lifecycle note recorded for the published revision")
    binding_targets: list[SkillLifecycleBinding] = Field(
        default_factory=list,
        description="Explicit role bindings to persist for this project-local skill",
    )


class SkillPublishResponse(BaseModel):
    """Response model for publishing a generated skill package."""

    success: bool = Field(..., description="Whether publishing succeeded")
    skill_name: str = Field(..., description="Name of the published skill")
    message: str = Field(..., description="Publish result message")
    published_path: str = Field(..., description="Filesystem path of the published skill directory")
    enabled: bool = Field(..., description="Whether the skill is enabled after publishing")


class SkillDryRunEvidenceRequest(BaseModel):
    thread_id: str = Field(
        ...,
        description="Thread ID where the Skill Studio draft artifacts live",
    )
    path: str = Field(
        ...,
        description="Virtual path to the Skill Studio skill-draft.json artifact",
    )
    status: Literal["passed", "failed"] = Field(
        ...,
        description="Reviewed dry-run result for the current draft",
    )
    scenario_id: str | None = Field(
        default=None,
        description="Optional scenario identifier used for the reviewed dry run",
    )
    message_ids: list[str] = Field(
        default_factory=list,
        description="Conversation message IDs that provide traceable dry-run evidence",
    )
    reviewer_note: str = Field(
        default="",
        description="Optional reviewer note recorded beside the dry-run evidence",
    )


class SkillDryRunEvidenceResponse(BaseModel):
    success: bool = True
    skill_name: str
    dry_run_evidence_status: str
    dry_run_evidence_virtual_path: str
    publish_status: str
    package_archive_virtual_path: str
    artifact_virtual_paths: list[str] = Field(default_factory=list)


def _has_traceable_message_ids(message_ids: object) -> bool:
    return bool(_normalize_message_ids(message_ids))


def _normalize_message_ids(message_ids: object) -> list[str]:
    if not isinstance(message_ids, list):
        return []

    normalized: list[str] = []
    for value in message_ids:
        if not isinstance(value, str):
            continue
        candidate = value.strip()
        if candidate:
            normalized.append(candidate)
    return normalized


async def _load_thread_state(thread_id: str) -> dict:
    from langgraph_sdk import get_client

    client = get_client(url=_get_langgraph_server_url())
    try:
        return await client.threads.get_state(thread_id)
    except Exception as exc:  # pragma: no cover - defensive integration boundary
        logger.error(
            "Failed to load LangGraph thread state for %s: %s",
            thread_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to verify dry-run evidence against the LangGraph thread "
                "state right now."
            ),
        ) from exc


def _get_langgraph_server_url() -> str:
    for env_key in LANGGRAPH_SERVER_ENV_KEYS:
        configured_value = os.getenv(env_key, "").strip()
        if configured_value:
            return configured_value

    try:
        app_config = get_app_config()
    except Exception:
        return _get_reachable_langgraph_fallback()

    extra = getattr(app_config, "model_extra", None)
    if not isinstance(extra, dict):
        return _get_reachable_langgraph_fallback()

    channels_config = extra.get("channels")
    if not isinstance(channels_config, dict):
        return _get_reachable_langgraph_fallback()

    configured_url = channels_config.get("langgraph_url")
    if isinstance(configured_url, str) and configured_url.strip():
        return configured_url.strip()

    return _get_reachable_langgraph_fallback()


def _get_reachable_langgraph_fallback() -> str:
    for candidate in LANGGRAPH_LOCAL_FALLBACKS:
        if _is_langgraph_url_reachable(candidate):
            return candidate
    return DEFAULT_LANGGRAPH_SERVER_URL


def _is_langgraph_url_reachable(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return False

    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80

    try:
        with socket.create_connection((hostname, port), timeout=0.2):
            return True
    except OSError:
        return False


def _extract_thread_message_ids(thread_state: object) -> set[str]:
    if not isinstance(thread_state, dict):
        return set()

    values = thread_state.get("values")
    if not isinstance(values, dict):
        return set()

    messages = values.get("messages")
    if not isinstance(messages, list):
        return set()

    traceable_ids: set[str] = set()
    for message in messages:
        if not isinstance(message, dict):
            continue
        message_id = message.get("id")
        if isinstance(message_id, str) and message_id.strip():
            traceable_ids.add(message_id.strip())
    return traceable_ids


async def _require_thread_message_ids(
    *,
    thread_id: str,
    message_ids: object,
    required_detail: str,
    mismatch_detail: str,
) -> list[str]:
    normalized_message_ids = _normalize_message_ids(message_ids)
    if not normalized_message_ids:
        raise HTTPException(status_code=400, detail=required_detail)

    thread_state = await _load_thread_state(thread_id)
    thread_message_ids = _extract_thread_message_ids(thread_state)
    missing_ids = [
        message_id
        for message_id in normalized_message_ids
        if message_id not in thread_message_ids
    ]
    if missing_ids:
        joined_ids = ", ".join(missing_ids[:3])
        suffix = "..." if len(missing_ids) > 3 else ""
        raise HTTPException(
            status_code=400,
            detail=f"{mismatch_detail}: {joined_ids}{suffix}",
        )

    return normalized_message_ids


class SkillLifecycleSummaryResponse(BaseModel):
    skill_name: str
    enabled: bool
    binding_targets: list[SkillLifecycleBinding] = Field(default_factory=list)
    revision_count: int = 0
    binding_count: int = 0
    active_revision_id: str | None = None
    published_revision_id: str | None = None
    rollback_target_id: str | None = None
    draft_status: str
    published_path: str | None = None
    last_published_at: str | None = None
    version_note: str = ""


class SkillLifecycleListResponse(BaseModel):
    skills: list[SkillLifecycleSummaryResponse]


class SkillLifecycleDetailResponse(SkillLifecycleRecord):
    revision_count: int = 0
    binding_count: int = 0


class SkillLifecycleUpdateRequest(BaseModel):
    enabled: bool = Field(..., description="Whether the custom skill should stay enabled for later threads")
    version_note: str = Field(default="", description="Project-level note attached to the current published state")
    binding_targets: list[SkillLifecycleBinding] = Field(
        default_factory=list,
        description="Explicit role bindings keyed by role_id, mode, and target_skills",
    )
    thread_id: str | None = Field(
        default=None,
        description=(
            "Optional thread ID for an unpublished Skill Studio draft whose "
            "lifecycle state should be updated."
        ),
    )
    path: str | None = Field(
        default=None,
        description=(
            "Optional virtual path to the Skill Studio draft or lifecycle "
            "artifact used to persist a pre-publish lifecycle update."
        ),
    )


class SkillRollbackRequest(BaseModel):
    revision_id: str = Field(..., description="Published revision ID to restore")


def _should_ignore_archive_entry(path: Path) -> bool:
    return path.name.startswith(".") or path.name == "__MACOSX"


def _resolve_skill_dir_from_archive_root(temp_path: Path) -> Path:
    extracted_items = [item for item in temp_path.iterdir() if not _should_ignore_archive_entry(item)]
    if len(extracted_items) == 0:
        raise HTTPException(status_code=400, detail="Skill archive is empty")
    if len(extracted_items) == 1 and extracted_items[0].is_dir():
        return extracted_items[0]
    return temp_path


def _skill_to_response(skill: Skill) -> SkillResponse:
    """Convert a Skill object to a SkillResponse."""
    return SkillResponse(
        name=skill.name,
        description=skill.description,
        license=skill.license,
        category=skill.category,
        enabled=skill.enabled,
    )


def _find_custom_skill(skill_name: str) -> Skill | None:
    skills = load_skills(
        skills_path=get_skills_root_path(),
        use_config=False,
        enabled_only=False,
    )
    return next(
        (
            skill
            for skill in skills
            if skill.name == skill_name and skill.category == "custom"
        ),
        None,
    )


def _get_skill_lifecycle_payload_path(skill: Skill) -> Path:
    return skill.skill_dir / "skill-lifecycle.json"


def _resolve_skill_lifecycle_record(
    skill: Skill,
    registry: SkillLifecycleRegistry,
) -> SkillLifecycleRecord:
    lifecycle_payload = load_skill_lifecycle_record(
        _get_skill_lifecycle_payload_path(skill),
    )
    return merge_skill_lifecycle_record(
        skill_name=skill.name,
        lifecycle_payload=lifecycle_payload,
        existing_record=registry.records.get(skill.name),
        enabled=skill.enabled,
        published_path=str(skill.skill_dir),
    )


def _save_skill_lifecycle_record(
    record: SkillLifecycleRecord,
    *,
    skills_root: Path | None = None,
    bump_runtime_revision: bool = False,
) -> None:
    registry = load_skill_lifecycle_registry(skills_root=skills_root)
    registry.records[record.skill_name] = record
    if bump_runtime_revision:
        bump_skill_runtime_revision(registry)
    save_skill_lifecycle_registry(registry, skills_root=skills_root)


def _resolve_draft_skill_lifecycle_path(
    *,
    thread_id: str,
    path: str,
) -> Path:
    resolved_path = resolve_thread_virtual_path(thread_id, path)
    if resolved_path.name == "skill-draft.json":
        resolved_path = resolved_path.with_name("skill-lifecycle.json")

    if resolved_path.name != "skill-lifecycle.json":
        raise HTTPException(
            status_code=400,
            detail=(
                "Draft lifecycle updates require a Skill Studio "
                "'skill-lifecycle.json' or 'skill-draft.json' path."
            ),
        )
    if not resolved_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Skill lifecycle draft not found: {resolved_path}",
        )
    return resolved_path


def _persist_draft_skill_lifecycle_record(
    lifecycle_path: Path,
    record: SkillLifecycleRecord,
) -> None:
    lifecycle_path.write_text(
        json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _to_skill_lifecycle_summary(
    record: SkillLifecycleRecord,
) -> SkillLifecycleSummaryResponse:
    return SkillLifecycleSummaryResponse(
        skill_name=record.skill_name,
        enabled=record.enabled,
        binding_targets=[
            binding.model_copy(deep=True)
            for binding in record.binding_targets
        ],
        revision_count=get_skill_lifecycle_revision_count(record),
        binding_count=get_skill_lifecycle_binding_count(record),
        active_revision_id=record.active_revision_id,
        published_revision_id=record.published_revision_id,
        rollback_target_id=record.rollback_target_id,
        draft_status=record.draft_status,
        published_path=record.published_path,
        last_published_at=record.last_published_at,
        version_note=record.version_note,
    )


def _to_skill_lifecycle_detail(
    record: SkillLifecycleRecord,
) -> SkillLifecycleDetailResponse:
    return SkillLifecycleDetailResponse(
        **record.model_dump(mode="python"),
        revision_count=get_skill_lifecycle_revision_count(record),
        binding_count=get_skill_lifecycle_binding_count(record),
    )


def _build_published_skill_revision(
    *,
    record: SkillLifecycleRecord,
    revision_id: str,
    revision_archive_path: Path,
    published_path: Path,
    published_at: str,
    source_thread_id: str,
) -> SkillLifecycleRevision:
    return SkillLifecycleRevision(
        revision_id=revision_id,
        published_at=published_at,
        archive_path=str(revision_archive_path),
        published_path=str(published_path),
        version_note=record.version_note,
        binding_targets=[
            binding.model_copy(deep=True)
            for binding in record.binding_targets
        ],
        enabled=record.enabled,
        source_thread_id=source_thread_id,
    )


def _get_extensions_config_path() -> Path:
    config_path = ExtensionsConfig.resolve_config_path()
    if config_path is None:
        config_path = Path.cwd().parent / "extensions_config.json"
        logger.info(
            "No existing extensions config found. Creating new config at: %s",
            config_path,
        )
    return config_path


def _write_extensions_config(config_path: Path, extensions_config: ExtensionsConfig) -> None:
    config_data = {
        "mcpServers": {
            name: server.model_dump()
            for name, server in extensions_config.mcp_servers.items()
        },
        "skills": {
            name: {"enabled": skill_config.enabled}
            for name, skill_config in extensions_config.skills.items()
        },
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)


def _set_skill_enabled(skill_name: str, enabled: bool) -> None:
    config_path = _get_extensions_config_path()
    extensions_config = get_extensions_config()
    extensions_config.skills[skill_name] = SkillStateConfig(enabled=enabled)
    _write_extensions_config(config_path, extensions_config)
    reload_extensions_config()


def _install_skill_archive(skill_file_path: Path, *, overwrite: bool = False) -> tuple[str, Path]:
    if not skill_file_path.exists():
        raise HTTPException(status_code=404, detail=f"Skill file not found: {skill_file_path}")

    if not skill_file_path.is_file():
        raise HTTPException(status_code=400, detail=f"Path is not a file: {skill_file_path}")

    if skill_file_path.suffix != ".skill":
        raise HTTPException(status_code=400, detail="File must have .skill extension")

    if not zipfile.is_zipfile(skill_file_path):
        raise HTTPException(status_code=400, detail="File is not a valid ZIP archive")

    skills_root = get_skills_root_path()
    custom_skills_dir = skills_root / "custom"
    custom_skills_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with zipfile.ZipFile(skill_file_path, "r") as zip_ref:
            _safe_extract_skill_archive(zip_ref, temp_path)

        skill_dir = _resolve_skill_dir_from_archive_root(temp_path)
        is_valid, message, skill_name = _validate_skill_frontmatter(skill_dir)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid skill: {message}")
        if not skill_name:
            raise HTTPException(status_code=400, detail="Could not determine skill name")

        target_dir = custom_skills_dir / skill_name
        preserved_revisions_dir = temp_path / "__preserved_revisions__"
        if target_dir.exists():
            if not overwrite:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Skill '{skill_name}' already exists. "
                        "Use overwrite=true to replace it."
                    ),
                )
            revision_dir = target_dir / ".revisions"
            if revision_dir.exists():
                shutil.copytree(revision_dir, preserved_revisions_dir)
            shutil.rmtree(target_dir)

        shutil.copytree(skill_dir, target_dir)
        if preserved_revisions_dir.exists():
            restored_revision_dir = target_dir / ".revisions"
            if restored_revision_dir.exists():
                shutil.rmtree(restored_revision_dir)
            shutil.copytree(preserved_revisions_dir, restored_revision_dir)

    return skill_name, target_dir


def _load_archive_root_json_payload(
    skill_file_path: Path,
    *,
    member_name: str,
    missing_detail: str,
    invalid_detail_prefix: str,
) -> dict:
    if not skill_file_path.exists():
        raise HTTPException(status_code=404, detail=f"Skill file not found: {skill_file_path}")

    if not skill_file_path.is_file():
        raise HTTPException(status_code=400, detail=f"Path is not a file: {skill_file_path}")

    if skill_file_path.suffix != ".skill":
        raise HTTPException(status_code=400, detail="File must have .skill extension")

    if not zipfile.is_zipfile(skill_file_path):
        raise HTTPException(status_code=400, detail="File is not a valid ZIP archive")

    with zipfile.ZipFile(skill_file_path, "r") as archive:
        archive_members = [
            Path(info.filename)
            for info in archive.infolist()
            if not info.is_dir() and not _should_ignore_archive_entry(Path(info.filename))
        ]
        if len(archive_members) == 0:
            raise HTTPException(status_code=400, detail="Skill archive is empty")

        top_level_entries = {
            member.parts[0]
            for member in archive_members
            if len(member.parts) > 0
        }
        root_prefix = (
            Path(next(iter(top_level_entries)))
            if len(top_level_entries) == 1
            else Path()
        )
        expected_member_name = (
            (root_prefix / member_name).as_posix()
            if root_prefix != Path()
            else member_name
        )
        archive_member = next(
            (
                info
                for info in archive.infolist()
                if not info.is_dir() and info.filename == expected_member_name
            ),
            None,
        )
        if archive_member is None:
            raise HTTPException(
                status_code=400,
                detail=missing_detail,
            )

        try:
            with archive.open(archive_member, "r") as file_obj:
                return json.load(file_obj)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"{invalid_detail_prefix}: {exc}",
            ) from exc


def _load_archive_dry_run_evidence(skill_file_path: Path) -> dict:
    return _load_archive_root_json_payload(
        skill_file_path,
        member_name="dry-run-evidence.json",
        missing_detail="Publish blocked: dry-run evidence is missing or has not passed.",
        invalid_detail_prefix="Invalid dry-run evidence payload in archive",
    )


def _load_archive_publish_readiness(skill_file_path: Path) -> dict:
    return _load_archive_root_json_payload(
        skill_file_path,
        member_name="publish-readiness.json",
        missing_detail="Publish blocked: publish readiness is missing or not ready for review.",
        invalid_detail_prefix="Invalid publish-readiness payload in archive",
    )


@router.get(
    "/skills",
    response_model=SkillsListResponse,
    summary="List All Skills",
    description="Retrieve a list of all available skills from both public and custom directories.",
)
async def list_skills() -> SkillsListResponse:
    """List all available skills.

    Returns all skills regardless of their enabled status.

    Returns:
        A list of all skills with their metadata.

    Example Response:
        ```json
        {
            "skills": [
                {
                    "name": "PDF Processing",
                    "description": "Extract and analyze PDF content",
                    "license": "MIT",
                    "category": "public",
                    "enabled": true
                },
                {
                    "name": "Frontend Design",
                    "description": "Generate frontend designs and components",
                    "license": null,
                    "category": "custom",
                    "enabled": false
                }
            ]
        }
        ```
    """
    try:
        # Load all skills (including disabled ones)
        skills = load_skills(enabled_only=False)
        return SkillsListResponse(skills=[_skill_to_response(skill) for skill in skills])
    except Exception as e:
        logger.error(f"Failed to load skills: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load skills: {str(e)}")


@router.get(
    "/skills/graph",
    response_model=SkillGraphResponse,
    summary="Get Skill Relationship Graph",
    description=(
        "Analyze the local DeerFlow skill library and return a lightweight "
        "SkillNet-style relationship graph for governance and routing."
    ),
)
async def get_skill_graph(skill_name: str | None = None) -> SkillGraphResponse:
    try:
        graph = analyze_skill_relationships(
            skills_path=get_skills_root_path(),
            focus_skill_name=skill_name,
        )
        return SkillGraphResponse.model_validate(graph.to_dict())
    except Exception as e:
        logger.error("Failed to build skill graph: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build skill graph: {str(e)}",
        )


@router.get(
    "/skills/lifecycle",
    response_model=SkillLifecycleListResponse,
    summary="List Skill Lifecycle State",
    description="Return lifecycle summaries for every custom project-local skill.",
)
async def list_skill_lifecycle() -> SkillLifecycleListResponse:
    try:
        skills_root = get_skills_root_path()
        registry = load_skill_lifecycle_registry(skills_root=skills_root)
        custom_skills = [
            skill
            for skill in load_skills(enabled_only=False)
            if skill.category == "custom"
        ]
        custom_skills_by_name = {
            skill.name: skill
            for skill in custom_skills
        }
        lifecycle_names = sorted(
            set(custom_skills_by_name) | set(registry.records),
        )
        summaries = []
        for skill_name in lifecycle_names:
            skill = custom_skills_by_name.get(skill_name)
            record = (
                _resolve_skill_lifecycle_record(skill, registry)
                if skill is not None
                else registry.records[skill_name].model_copy(deep=True)
            )
            summaries.append(_to_skill_lifecycle_summary(record))
        summaries.sort(key=lambda item: item.skill_name)
        return SkillLifecycleListResponse(skills=summaries)
    except Exception as e:
        logger.error("Failed to list skill lifecycle summaries: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list skill lifecycle summaries: {str(e)}",
        )


@router.get(
    "/skills/lifecycle/{skill_name}",
    response_model=SkillLifecycleDetailResponse,
    summary="Get Skill Lifecycle Details",
    description="Return the full lifecycle record for a custom project-local skill.",
)
async def get_skill_lifecycle(skill_name: str) -> SkillLifecycleDetailResponse:
    try:
        registry = load_skill_lifecycle_registry(skills_root=get_skills_root_path())
        skill = _find_custom_skill(skill_name)
        if skill is not None:
            return _to_skill_lifecycle_detail(
                _resolve_skill_lifecycle_record(skill, registry),
            )

        draft_record = registry.records.get(skill_name)
        if draft_record is None:
            raise HTTPException(
                status_code=404,
                detail=f"Custom skill '{skill_name}' not found",
            )
        return _to_skill_lifecycle_detail(draft_record.model_copy(deep=True))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get skill lifecycle for %s: %s",
            skill_name,
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get skill lifecycle: {str(e)}",
        )


@router.put(
    "/skills/lifecycle/{skill_name}",
    response_model=SkillLifecycleDetailResponse,
    summary="Update Skill Lifecycle Management State",
    description="Update enablement, version note, and explicit binding targets without re-publishing the skill.",
)
async def update_skill_lifecycle(
    skill_name: str,
    request: SkillLifecycleUpdateRequest,
) -> SkillLifecycleDetailResponse:
    try:
        skills_root = get_skills_root_path()
        registry = load_skill_lifecycle_registry(skills_root=skills_root)
        lifecycle_path: Path | None = None
        lifecycle_payload: SkillLifecycleRecord | None = None
        published_path: str | None = None
        skill = _find_custom_skill(skill_name)

        if skill is not None:
            _set_skill_enabled(skill_name, request.enabled)
            updated_skill = _find_custom_skill(skill_name)
            if updated_skill is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to reload custom skill '{skill_name}' after lifecycle update",
                )
            lifecycle_payload = load_skill_lifecycle_record(
                _get_skill_lifecycle_payload_path(updated_skill),
            )
            published_path = str(updated_skill.skill_dir)
        else:
            if request.thread_id and request.path:
                lifecycle_path = _resolve_draft_skill_lifecycle_path(
                    thread_id=request.thread_id,
                    path=request.path,
                )
                lifecycle_payload = load_skill_lifecycle_record(lifecycle_path)
                if lifecycle_payload is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Skill lifecycle draft not found: {lifecycle_path}",
                    )
                if lifecycle_payload.skill_name != skill_name:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Skill lifecycle draft does not match the "
                            f"requested skill '{skill_name}'."
                        ),
                    )
            elif registry.records.get(skill_name) is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Custom skill '{skill_name}' not found",
                )

        record = merge_skill_lifecycle_record(
            skill_name=skill_name,
            lifecycle_payload=lifecycle_payload,
            existing_record=registry.records.get(skill_name),
            enabled=request.enabled,
            version_note=request.version_note,
            binding_targets=request.binding_targets,
            published_path=published_path,
        )
        if lifecycle_path is not None:
            record.draft_updated_at = utc_timestamp()
            _persist_draft_skill_lifecycle_record(lifecycle_path, record)
        registry.records[skill_name] = record
        bump_skill_runtime_revision(registry)
        save_skill_lifecycle_registry(registry, skills_root=skills_root)
        return _to_skill_lifecycle_detail(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update skill lifecycle for %s: %s",
            skill_name,
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update skill lifecycle: {str(e)}",
        )


@router.post(
    "/skills/{skill_name}/rollback",
    response_model=SkillLifecycleSummaryResponse,
    summary="Rollback Published Skill Revision",
    description="Restore a previously published skill snapshot into the project-local custom skills directory.",
)
async def rollback_skill_revision(
    skill_name: str,
    request: SkillRollbackRequest,
) -> SkillLifecycleSummaryResponse:
    try:
        skill = _find_custom_skill(skill_name)
        if skill is None:
            raise HTTPException(
                status_code=404,
                detail=f"Custom skill '{skill_name}' not found",
            )

        skills_root = get_skills_root_path()
        registry = load_skill_lifecycle_registry(skills_root=skills_root)
        record = _resolve_skill_lifecycle_record(skill, registry)
        revision = get_skill_lifecycle_revision(record, request.revision_id)
        if revision is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Published revision '{request.revision_id}' not found for "
                    f"skill '{skill_name}'"
                ),
            )

        revision_archive_path = Path(revision.archive_path)
        if not revision_archive_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Revision archive not found: {revision_archive_path}",
            )

        restored_skill_name, target_dir = _install_skill_archive(
            revision_archive_path,
            overwrite=True,
        )
        if restored_skill_name != skill_name:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Revision '{request.revision_id}' does not match "
                    f"skill '{skill_name}'"
                ),
            )

        _set_skill_enabled(skill_name, revision.enabled)
        updated_skill = _find_custom_skill(skill_name)
        if updated_skill is None:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reload custom skill '{skill_name}' after rollback",
            )

        restored_record = merge_skill_lifecycle_record(
            skill_name=skill_name,
            lifecycle_payload=load_skill_lifecycle_record(
                _get_skill_lifecycle_payload_path(updated_skill),
            ),
            existing_record=record,
            sync_active_revision=False,
            enabled=revision.enabled,
            published_path=str(target_dir),
        )
        restored_record = apply_skill_lifecycle_revision(
            restored_record,
            revision=revision,
        )
        registry.records[skill_name] = restored_record
        bump_skill_runtime_revision(registry)
        save_skill_lifecycle_registry(registry, skills_root=skills_root)
        return _to_skill_lifecycle_summary(restored_record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to roll back skill %s to revision %s: %s",
            skill_name,
            request.revision_id,
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rollback skill revision: {str(e)}",
        )


@router.get(
    "/skills/{skill_name}",
    response_model=SkillResponse,
    summary="Get Skill Details",
    description="Retrieve detailed information about a specific skill by its name.",
)
async def get_skill(skill_name: str) -> SkillResponse:
    """Get a specific skill by name.

    Args:
        skill_name: The name of the skill to retrieve.

    Returns:
        Skill information if found.

    Raises:
        HTTPException: 404 if skill not found.

    Example Response:
        ```json
        {
            "name": "PDF Processing",
            "description": "Extract and analyze PDF content",
            "license": "MIT",
            "category": "public",
            "enabled": true
        }
        ```
    """
    try:
        skills = load_skills(enabled_only=False)
        skill = next((s for s in skills if s.name == skill_name), None)

        if skill is None:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

        return _skill_to_response(skill)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get skill {skill_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get skill: {str(e)}")


@router.put(
    "/skills/{skill_name}",
    response_model=SkillResponse,
    summary="Update Skill",
    description="Update a skill's enabled status by modifying the extensions_config.json file.",
)
async def update_skill(skill_name: str, request: SkillUpdateRequest) -> SkillResponse:
    """Update a skill's enabled status.

    This will modify the extensions_config.json file to update the enabled state.
    The SKILL.md file itself is not modified.

    Args:
        skill_name: The name of the skill to update.
        request: The update request containing the new enabled status.

    Returns:
        The updated skill information.

    Raises:
        HTTPException: 404 if skill not found, 500 if update fails.

    Example Request:
        ```json
        {
            "enabled": false
        }
        ```

    Example Response:
        ```json
        {
            "name": "PDF Processing",
            "description": "Extract and analyze PDF content",
            "license": "MIT",
            "category": "public",
            "enabled": false
        }
        ```
    """
    try:
        # Find the skill to verify it exists
        skills = load_skills(enabled_only=False)
        skill = next((s for s in skills if s.name == skill_name), None)

        if skill is None:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

        _set_skill_enabled(skill_name, request.enabled)
        logger.info("Skill '%s' enabled status updated to %s", skill_name, request.enabled)

        if skill.category == "custom":
            record = merge_skill_lifecycle_record(
                skill_name=skill.name,
                lifecycle_payload=load_skill_lifecycle_record(
                    _get_skill_lifecycle_payload_path(skill),
                ),
                existing_record=load_skill_lifecycle_registry(
                    skills_root=get_skills_root_path(),
                ).records.get(skill.name),
                enabled=request.enabled,
                published_path=str(skill.skill_dir),
            )
            _save_skill_lifecycle_record(
                record,
                skills_root=get_skills_root_path(),
                bump_runtime_revision=True,
            )

        # Reload the skills to get the updated status (for API response)
        skills = load_skills(enabled_only=False)
        updated_skill = next((s for s in skills if s.name == skill_name), None)

        if updated_skill is None:
            raise HTTPException(status_code=500, detail=f"Failed to reload skill '{skill_name}' after update")
        return _skill_to_response(updated_skill)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update skill {skill_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update skill: {str(e)}")


@router.post(
    "/skills/install",
    response_model=SkillInstallResponse,
    summary="Install Skill",
    description="Install a skill from a .skill file (ZIP archive) located in the thread's user-data directory.",
)
async def install_skill(request: SkillInstallRequest) -> SkillInstallResponse:
    """Install a skill from a .skill file.

    The .skill file is a ZIP archive containing a skill directory with SKILL.md
    and optional resources (scripts, references, assets).

    Args:
        request: The install request containing thread_id and virtual path to .skill file.

    Returns:
        Installation result with skill name and status message.

    Raises:
        HTTPException:
            - 400 if path is invalid or file is not a valid .skill file
            - 403 if access denied (path traversal detected)
            - 404 if file not found
            - 409 if skill already exists
            - 500 if installation fails

    Example Request:
        ```json
        {
            "thread_id": "abc123-def456",
            "path": "/mnt/user-data/outputs/my-skill.skill"
        }
        ```

    Example Response:
        ```json
        {
            "success": true,
            "skill_name": "my-skill",
            "message": "Skill 'my-skill' installed successfully"
        }
        ```
    """
    try:
        skill_file_path = resolve_thread_virtual_path(request.thread_id, request.path)
        skill_name, target_dir = _install_skill_archive(skill_file_path, overwrite=False)
        logger.info(f"Skill '{skill_name}' installed successfully to {target_dir}")
        return SkillInstallResponse(success=True, skill_name=skill_name, message=f"Skill '{skill_name}' installed successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to install skill: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to install skill: {str(e)}")


@router.post(
    "/skills/dry-run-evidence",
    response_model=SkillDryRunEvidenceResponse,
    summary="Record Skill Studio Dry-Run Evidence",
    description=(
        "Persist the reviewed dry-run result for a Skill Studio draft, refresh "
        "publish-readiness artifacts, and rebuild the packaged .skill archive."
    ),
)
async def record_skill_dry_run_evidence(
    request: SkillDryRunEvidenceRequest,
) -> SkillDryRunEvidenceResponse:
    try:
        draft_path = resolve_thread_virtual_path(request.thread_id, request.path)
        validated_message_ids = request.message_ids
        if request.status == "passed" or _has_traceable_message_ids(request.message_ids):
            validated_message_ids = await _require_thread_message_ids(
                thread_id=request.thread_id,
                message_ids=request.message_ids,
                required_detail="Passed dry-run evidence requires non-empty traceable message_ids.",
                mismatch_detail=(
                    "Passed dry-run evidence message_ids do not belong to the "
                    "requested thread"
                ),
            )
        result = record_skill_studio_dry_run_evidence(
            draft_path=draft_path,
            thread_id=request.thread_id,
            status=request.status,
            scenario_id=request.scenario_id,
            message_ids=validated_message_ids,
            reviewer_note=request.reviewer_note,
        )
        return SkillDryRunEvidenceResponse(success=True, **result)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to record dry-run evidence for %s: %s",
            request.path,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record dry-run evidence: {str(exc)}",
        ) from exc


@router.post(
    "/skills/publish",
    response_model=SkillPublishResponse,
    summary="Publish Skill Draft",
    description=(
        "Publish a generated Skill Studio .skill archive into the project's "
        "custom skills directory and optionally enable it immediately."
    ),
)
async def publish_skill(request: SkillPublishRequest) -> SkillPublishResponse:
    """Publish a generated skill package from Skill Studio into the repo."""
    try:
        skill_file_path = resolve_thread_virtual_path(request.thread_id, request.path)
        dry_run_evidence = _load_archive_dry_run_evidence(skill_file_path)
        if dry_run_evidence.get("status") != "passed":
            raise HTTPException(
                status_code=400,
                detail="Publish blocked: dry-run evidence is missing or has not passed.",
            )
        if not _has_traceable_message_ids(dry_run_evidence.get("message_ids")):
            raise HTTPException(
                status_code=400,
                detail="Publish blocked: dry-run evidence is missing traceable message_ids.",
            )
        if str(dry_run_evidence.get("thread_id") or "").strip() != request.thread_id:
            raise HTTPException(
                status_code=400,
                detail="Publish blocked: dry-run evidence thread_id does not match the requested thread.",
            )
        dry_run_evidence["message_ids"] = await _require_thread_message_ids(
            thread_id=request.thread_id,
            message_ids=dry_run_evidence.get("message_ids"),
            required_detail="Publish blocked: dry-run evidence is missing traceable message_ids.",
            mismatch_detail=(
                "Publish blocked: dry-run evidence message_ids do not belong to "
                "the requested thread"
            ),
        )
        publish_readiness = _load_archive_publish_readiness(skill_file_path)
        if publish_readiness.get("status") != "ready_for_review":
            raise HTTPException(
                status_code=400,
                detail="Publish blocked: publish readiness is missing or not ready for review.",
            )
        skill_name, target_dir = _install_skill_archive(
            skill_file_path,
            overwrite=request.overwrite,
        )
        _set_skill_enabled(skill_name, request.enable)

        skills_root = get_skills_root_path()
        registry = load_skill_lifecycle_registry(skills_root=skills_root)
        published_at = utc_timestamp()
        record = merge_skill_lifecycle_record(
            skill_name=skill_name,
            lifecycle_payload=load_skill_lifecycle_record(
                target_dir / "skill-lifecycle.json",
            ),
            existing_record=registry.records.get(skill_name),
            sync_active_revision=False,
            enabled=request.enable,
            version_note=request.version_note,
            binding_targets=request.binding_targets,
            published_path=str(target_dir),
            last_published_at=published_at,
            last_published_from_thread_id=request.thread_id,
        )
        revision_id = get_next_skill_revision_id(record)
        revision_archive_path = get_skill_revision_archive_path(
            skill_name,
            revision_id,
            skills_root=skills_root,
        )
        revision_archive_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_file_path, revision_archive_path)
        record = append_skill_lifecycle_revision(
            record,
            revision=_build_published_skill_revision(
                record=record,
                revision_id=revision_id,
                revision_archive_path=revision_archive_path,
                published_path=target_dir,
                published_at=published_at,
                source_thread_id=request.thread_id,
            ),
        )
        registry.records[skill_name] = record
        bump_skill_runtime_revision(registry)
        save_skill_lifecycle_registry(registry, skills_root=skills_root)

        action = "updated" if request.overwrite else "installed"
        message = f"Skill '{skill_name}' {action} successfully"
        logger.info("%s at %s", message, target_dir)
        return SkillPublishResponse(
            success=True,
            skill_name=skill_name,
            message=message,
            published_path=str(target_dir),
            enabled=request.enable,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to publish skill: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to publish skill: {str(e)}")
