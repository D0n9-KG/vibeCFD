import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.gateway.routers.skills import _get_langgraph_server_url
from deerflow.config.paths import Paths, get_paths

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/threads", tags=["threads"])


class ThreadDeleteResponse(BaseModel):
    """Response model for thread cleanup."""

    success: bool
    message: str


class ThreadStorageSliceResponse(BaseModel):
    exists: bool
    file_count: int
    total_bytes: int


class ThreadLocalStorageResponse(BaseModel):
    thread_dir: str
    exists: bool
    workspace: ThreadStorageSliceResponse
    uploads: ThreadStorageSliceResponse
    outputs: ThreadStorageSliceResponse
    total_files: int
    total_bytes: int


class ThreadImpactSummaryResponse(BaseModel):
    total_files: int
    total_bytes: int


class ThreadLangGraphStateResponse(BaseModel):
    status: str
    can_delete: bool


class ThreadDeletePreviewResponse(BaseModel):
    thread_id: str
    impact_summary: ThreadImpactSummaryResponse
    local_storage: ThreadLocalStorageResponse
    langgraph_state: ThreadLangGraphStateResponse


class ThreadDeleteStepResponse(BaseModel):
    key: str
    status: str
    detail: str


class ThreadCascadeDeleteResponse(BaseModel):
    success: bool
    message: str
    thread_id: str
    partial_success: bool
    steps: list[ThreadDeleteStepResponse] = Field(default_factory=list)


class ThreadOrphanResponse(BaseModel):
    thread_id: str
    thread_dir: str
    total_files: int
    total_bytes: int
    langgraph_state: ThreadLangGraphStateResponse


class ThreadOrphanAuditResponse(BaseModel):
    orphans: list[ThreadOrphanResponse] = Field(default_factory=list)


def _summarize_directory(path: Path) -> ThreadStorageSliceResponse:
    if not path.exists():
        return ThreadStorageSliceResponse(exists=False, file_count=0, total_bytes=0)

    total_bytes = 0
    file_count = 0
    for file_path in path.rglob("*"):
        if not file_path.is_file():
            continue
        file_count += 1
        try:
            total_bytes += file_path.stat().st_size
        except OSError:
            logger.warning("Could not stat thread file %s", file_path)
    return ThreadStorageSliceResponse(
        exists=True,
        file_count=file_count,
        total_bytes=total_bytes,
    )


def _summarize_local_thread_storage(
    thread_id: str,
    paths: Paths | None = None,
) -> ThreadLocalStorageResponse:
    path_manager = paths or get_paths()
    thread_dir = path_manager.thread_dir(thread_id)
    workspace = _summarize_directory(path_manager.sandbox_work_dir(thread_id))
    uploads = _summarize_directory(path_manager.sandbox_uploads_dir(thread_id))
    outputs = _summarize_directory(path_manager.sandbox_outputs_dir(thread_id))
    total_files = workspace.file_count + uploads.file_count + outputs.file_count
    total_bytes = workspace.total_bytes + uploads.total_bytes + outputs.total_bytes
    return ThreadLocalStorageResponse(
        thread_dir=str(thread_dir),
        exists=thread_dir.exists(),
        workspace=workspace,
        uploads=uploads,
        outputs=outputs,
        total_files=total_files,
        total_bytes=total_bytes,
    )


def _is_missing_langgraph_thread_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code == 404:
        return True

    message = str(exc).lower()
    return "404" in message or "not found" in message


async def _probe_langgraph_thread_state(thread_id: str) -> dict[str, object]:
    try:
        from langgraph_sdk import get_client

        client = get_client(url=_get_langgraph_server_url())
        await client.threads.get_state(thread_id)
        return {"status": "present", "can_delete": True}
    except Exception as exc:  # pragma: no cover - integration boundary
        if _is_missing_langgraph_thread_error(exc):
            return {"status": "missing", "can_delete": False}
        logger.warning("Unable to probe LangGraph thread state for %s: %s", thread_id, exc)
        return {"status": "unknown", "can_delete": False}


async def _delete_langgraph_thread_state(thread_id: str) -> dict[str, str]:
    try:
        from langgraph_sdk import get_client

        client = get_client(url=_get_langgraph_server_url())
        await client.threads.delete(thread_id)
        return {"status": "deleted", "detail": "Deleted LangGraph thread state."}
    except Exception as exc:  # pragma: no cover - integration boundary
        if _is_missing_langgraph_thread_error(exc):
            return {
                "status": "already_missing",
                "detail": "LangGraph thread state was already missing.",
            }
        logger.warning("Unable to delete LangGraph thread state for %s: %s", thread_id, exc)
        return {
            "status": "unavailable",
            "detail": "LangGraph thread state could not be deleted right now.",
        }


def _delete_thread_data(thread_id: str, paths: Paths | None = None) -> ThreadDeleteResponse:
    """Delete local persisted filesystem data for a thread."""
    path_manager = paths or get_paths()
    try:
        path_manager.delete_thread_dir(thread_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to delete thread data for %s", thread_id)
        raise HTTPException(status_code=500, detail="Failed to delete local thread data.") from exc

    logger.info("Deleted local thread data for %s", thread_id)
    return ThreadDeleteResponse(success=True, message=f"Deleted local thread data for {thread_id}")


def _iter_local_thread_ids(paths: Paths | None = None) -> list[str]:
    path_manager = paths or get_paths()
    threads_dir = path_manager.base_dir / "threads"
    if not threads_dir.exists():
        return []

    thread_ids: list[str] = []
    for entry in sorted(threads_dir.iterdir(), key=lambda item: item.name):
        if not entry.is_dir():
            continue
        try:
            path_manager.thread_dir(entry.name)
        except ValueError:
            logger.warning("Skipping invalid local thread directory %s", entry)
            continue
        thread_ids.append(entry.name)
    return thread_ids


@router.get("/orphans", response_model=ThreadOrphanAuditResponse)
async def list_orphan_thread_dirs() -> ThreadOrphanAuditResponse:
    """List local thread directories whose LangGraph state is already gone."""
    path_manager = get_paths()
    orphans: list[ThreadOrphanResponse] = []

    for thread_id in _iter_local_thread_ids(path_manager):
        langgraph_state = ThreadLangGraphStateResponse.model_validate(
            await _probe_langgraph_thread_state(thread_id),
        )
        if langgraph_state.status != "missing":
            continue

        storage = _summarize_local_thread_storage(thread_id, path_manager)
        orphans.append(
            ThreadOrphanResponse(
                thread_id=thread_id,
                thread_dir=storage.thread_dir,
                total_files=storage.total_files,
                total_bytes=storage.total_bytes,
                langgraph_state=langgraph_state,
            )
        )

    return ThreadOrphanAuditResponse(orphans=orphans)


@router.get("/{thread_id}/delete-preview", response_model=ThreadDeletePreviewResponse)
async def get_thread_delete_preview(thread_id: str) -> ThreadDeletePreviewResponse:
    """Preview local + LangGraph cleanup impact for a thread."""
    try:
        storage = _summarize_local_thread_storage(thread_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    langgraph_state = ThreadLangGraphStateResponse.model_validate(
        await _probe_langgraph_thread_state(thread_id),
    )
    return ThreadDeletePreviewResponse(
        thread_id=thread_id,
        impact_summary=ThreadImpactSummaryResponse(
            total_files=storage.total_files,
            total_bytes=storage.total_bytes,
        ),
        local_storage=storage,
        langgraph_state=langgraph_state,
    )


@router.delete("/{thread_id}", response_model=ThreadCascadeDeleteResponse)
async def delete_thread_data(thread_id: str) -> ThreadCascadeDeleteResponse:
    """Delete LangGraph thread state and DeerFlow local persisted data."""
    preview = await get_thread_delete_preview(thread_id)

    langgraph_step = ThreadDeleteStepResponse(
        key="langgraph_state",
        **(await _delete_langgraph_thread_state(thread_id)),
    )

    try:
        local_status = "deleted" if preview.local_storage.exists else "already_missing"
        local_detail = (
            "Deleted local thread data."
            if local_status == "deleted"
            else "Local thread data was already missing."
        )
        _delete_thread_data(thread_id)
        local_step = ThreadDeleteStepResponse(
            key="local_storage",
            status=local_status,
            detail=local_detail,
        )
    except HTTPException as exc:
        local_step = ThreadDeleteStepResponse(
            key="local_storage",
            status="failed",
            detail=str(exc.detail),
        )

    steps = [langgraph_step, local_step]
    partial_success = any(step.status not in {"deleted", "already_missing"} for step in steps)
    return ThreadCascadeDeleteResponse(
        success=not partial_success,
        message=(
            f"Deleted thread data for {thread_id}"
            if not partial_success
            else f"Deleted thread data for {thread_id} with remaining cleanup steps."
        ),
        thread_id=thread_id,
        partial_success=partial_success,
        steps=steps,
    )
