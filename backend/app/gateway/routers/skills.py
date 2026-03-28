import json
import logging
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.gateway.path_utils import resolve_thread_virtual_path
from deerflow.config.extensions_config import ExtensionsConfig, SkillStateConfig, get_extensions_config, reload_extensions_config
from deerflow.skills import Skill, analyze_skill_relationships, load_skills
from deerflow.skills.loader import get_skills_root_path
from deerflow.skills.validation import _validate_skill_frontmatter

logger = logging.getLogger(__name__)


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


class SkillPublishResponse(BaseModel):
    """Response model for publishing a generated skill package."""

    success: bool = Field(..., description="Whether publishing succeeded")
    skill_name: str = Field(..., description="Name of the published skill")
    message: str = Field(..., description="Publish result message")
    published_path: str = Field(..., description="Filesystem path of the published skill directory")
    enabled: bool = Field(..., description="Whether the skill is enabled after publishing")


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
        if target_dir.exists():
            if not overwrite:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Skill '{skill_name}' already exists. "
                        "Use overwrite=true to replace it."
                    ),
                )
            shutil.rmtree(target_dir)

        shutil.copytree(skill_dir, target_dir)

    return skill_name, target_dir


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
        skill_name, target_dir = _install_skill_archive(
            skill_file_path,
            overwrite=request.overwrite,
        )
        _set_skill_enabled(skill_name, request.enable)

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
