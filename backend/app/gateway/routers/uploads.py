"""Upload router for handling file uploads."""

import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from deerflow.config.paths import VIRTUAL_PATH_PREFIX, get_paths
from deerflow.utils.file_conversion import CONVERTIBLE_EXTENSIONS, convert_file_to_markdown

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/threads/{thread_id}/uploads", tags=["uploads"])
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_THREAD_UPLOAD_BYTES = 200 * 1024 * 1024
MAX_THREAD_UPLOAD_FILES = 20
BLOCKED_EXTENSIONS = {".bat", ".cmd", ".com", ".exe", ".ps1", ".scr"}


class UploadResponse(BaseModel):
    """Response model for file upload."""

    success: bool
    files: list[dict[str, str]]
    message: str


def get_uploads_dir(thread_id: str) -> Path:
    """Get the uploads directory for a thread.

    Args:
        thread_id: The thread ID.

    Returns:
        Path to the uploads directory.
    """
    base_dir = get_paths().sandbox_uploads_dir(thread_id)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def sanitize_upload_filename(filename: str) -> str:
    safe_filename = Path(filename).name
    if not safe_filename or safe_filename in {".", ".."} or "/" in safe_filename or "\\" in safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    extension = Path(safe_filename).suffix.lower()
    if extension and extension in BLOCKED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type is not allowed: {extension}",
        )

    return safe_filename


def enforce_upload_budget(
    *,
    existing_files: dict[str, int],
    incoming_files: list[tuple[str, int]],
    max_file_count: int = MAX_THREAD_UPLOAD_FILES,
    max_total_bytes: int = MAX_THREAD_UPLOAD_BYTES,
) -> None:
    projected_files = dict(existing_files)
    for filename, size in incoming_files:
        projected_files[filename] = size

    if len(projected_files) > max_file_count:
        raise HTTPException(
            status_code=400,
            detail=f"Too many uploaded files for this thread. Max {max_file_count} files allowed.",
        )

    projected_bytes = sum(projected_files.values())
    if projected_bytes > max_total_bytes:
        raise HTTPException(
            status_code=400,
            detail=(f"Total upload quota exceeded for this thread. Max {max_total_bytes // (1024 * 1024)} MB allowed."),
        )


@router.post("", response_model=UploadResponse)
async def upload_files(
    thread_id: str,
    files: list[UploadFile] = File(...),
) -> UploadResponse:
    """Upload multiple files to a thread's uploads directory.

    For PDF, PPT, Excel, and Word files, they will be converted to markdown using markitdown.
    All files (original and converted) are saved to /mnt/user-data/uploads.

    Args:
        thread_id: The thread ID to upload files to.
        files: List of files to upload.

    Returns:
        Upload response with success status and file information.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    uploads_dir = get_uploads_dir(thread_id)
    paths = get_paths()
    uploaded_files = []
    prepared_uploads: list[tuple[str, bytes]] = []

    for file in files:
        if not file.filename:
            continue

        safe_filename = sanitize_upload_filename(file.filename)
        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=400,
                detail=(f"File too large: {safe_filename}. Max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB per file."),
            )
        prepared_uploads.append((safe_filename, content))

    existing_files = {file_path.name: file_path.stat().st_size for file_path in uploads_dir.iterdir() if file_path.is_file()}
    enforce_upload_budget(
        existing_files=existing_files,
        incoming_files=[(safe_filename, len(content)) for safe_filename, content in prepared_uploads],
    )

    for safe_filename, content in prepared_uploads:
        try:
            file_path = uploads_dir / safe_filename
            file_path.write_bytes(content)

            # Build relative path from backend root
            relative_path = str(paths.sandbox_uploads_dir(thread_id) / safe_filename)
            virtual_path = f"{VIRTUAL_PATH_PREFIX}/uploads/{safe_filename}"

            # Thread-scoped uploads on host storage are the source of truth.
            # Local DeerFlow runtimes and AIO sandbox containers already consume
            # this directory via existing filesystem/mount infrastructure, so
            # uploads must not eagerly acquire a sandbox just to mirror bytes.

            file_info = {
                "filename": safe_filename,
                "size": str(len(content)),
                "path": relative_path,  # Actual filesystem path (relative to backend/)
                "virtual_path": virtual_path,  # Path for Agent in sandbox
                "artifact_url": f"/api/threads/{thread_id}/artifacts/mnt/user-data/uploads/{safe_filename}",  # HTTP URL
            }

            logger.info(f"Saved file: {safe_filename} ({len(content)} bytes) to {relative_path}")

            # Check if file should be converted to markdown
            file_ext = file_path.suffix.lower()
            if file_ext in CONVERTIBLE_EXTENSIONS:
                md_path = await convert_file_to_markdown(file_path)
                if md_path:
                    md_relative_path = str(paths.sandbox_uploads_dir(thread_id) / md_path.name)
                    md_virtual_path = f"{VIRTUAL_PATH_PREFIX}/uploads/{md_path.name}"

                    file_info["markdown_file"] = md_path.name
                    file_info["markdown_path"] = md_relative_path
                    file_info["markdown_virtual_path"] = md_virtual_path
                    file_info["markdown_artifact_url"] = f"/api/threads/{thread_id}/artifacts/mnt/user-data/uploads/{md_path.name}"

            uploaded_files.append(file_info)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload {safe_filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload {safe_filename}: {str(e)}")

    return UploadResponse(
        success=True,
        files=uploaded_files,
        message=f"Successfully uploaded {len(uploaded_files)} file(s)",
    )


@router.get("/list", response_model=dict)
async def list_uploaded_files(thread_id: str) -> dict:
    """List all files in a thread's uploads directory.

    Args:
        thread_id: The thread ID to list files for.

    Returns:
        Dictionary containing list of files with their metadata.
    """
    uploads_dir = get_uploads_dir(thread_id)

    if not uploads_dir.exists():
        return {"files": [], "count": 0}

    files = []
    for file_path in sorted(uploads_dir.iterdir()):
        if file_path.is_file():
            stat = file_path.stat()
            relative_path = str(get_paths().sandbox_uploads_dir(thread_id) / file_path.name)
            files.append(
                {
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "path": relative_path,  # Actual filesystem path
                    "virtual_path": f"{VIRTUAL_PATH_PREFIX}/uploads/{file_path.name}",  # Path for Agent in sandbox
                    "artifact_url": f"/api/threads/{thread_id}/artifacts/mnt/user-data/uploads/{file_path.name}",  # HTTP URL
                    "extension": file_path.suffix,
                    "modified": stat.st_mtime,
                }
            )

    return {"files": files, "count": len(files)}


@router.delete("/{filename}")
async def delete_uploaded_file(thread_id: str, filename: str) -> dict:
    """Delete a file from a thread's uploads directory.

    Args:
        thread_id: The thread ID.
        filename: The filename to delete.

    Returns:
        Success message.
    """
    uploads_dir = get_uploads_dir(thread_id)
    file_path = uploads_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    # Security check: ensure the path is within the uploads directory
    try:
        file_path.resolve().relative_to(uploads_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        if file_path.suffix.lower() in CONVERTIBLE_EXTENSIONS:
            companion_markdown = file_path.with_suffix(".md")
            companion_markdown.unlink(missing_ok=True)
        file_path.unlink(missing_ok=True)
        logger.info(f"Deleted file: {filename}")
        return {"success": True, "message": f"Deleted {filename}"}
    except Exception as e:
        logger.error(f"Failed to delete {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete {filename}: {str(e)}")
