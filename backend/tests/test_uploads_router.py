import asyncio
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import UploadFile

from app.gateway.routers import uploads


def test_upload_files_writes_thread_storage(tmp_path):
    thread_uploads_dir = tmp_path / "uploads"
    thread_uploads_dir.mkdir(parents=True)

    with patch.object(uploads, "get_uploads_dir", return_value=thread_uploads_dir):
        file = UploadFile(filename="notes.txt", file=BytesIO(b"hello uploads"))
        result = asyncio.run(uploads.upload_files("thread-local", files=[file]))

    assert result.success is True
    assert len(result.files) == 1
    assert result.files[0]["filename"] == "notes.txt"
    assert (thread_uploads_dir / "notes.txt").read_bytes() == b"hello uploads"


def test_upload_files_marks_markdown_file_when_conversion_succeeds(tmp_path):
    thread_uploads_dir = tmp_path / "uploads"
    thread_uploads_dir.mkdir(parents=True)

    async def fake_convert(file_path: Path) -> Path:
        md_path = file_path.with_suffix(".md")
        md_path.write_text("converted", encoding="utf-8")
        return md_path

    with (
        patch.object(uploads, "get_uploads_dir", return_value=thread_uploads_dir),
        patch.object(uploads, "convert_file_to_markdown", AsyncMock(side_effect=fake_convert)),
    ):
        file = UploadFile(filename="report.pdf", file=BytesIO(b"pdf-bytes"))
        result = asyncio.run(uploads.upload_files("thread-aio", files=[file]))

    assert result.success is True
    assert len(result.files) == 1
    file_info = result.files[0]
    assert file_info["filename"] == "report.pdf"
    assert file_info["markdown_file"] == "report.md"

    assert (thread_uploads_dir / "report.pdf").read_bytes() == b"pdf-bytes"
    assert (thread_uploads_dir / "report.md").read_text(encoding="utf-8") == "converted"


def test_upload_files_rejects_dotdot_and_dot_filenames(tmp_path):
    thread_uploads_dir = tmp_path / "uploads"
    thread_uploads_dir.mkdir(parents=True)

    with patch.object(uploads, "get_uploads_dir", return_value=thread_uploads_dir):
        for bad_name in ["..", "."]:
            file = UploadFile(filename=bad_name, file=BytesIO(b"data"))
            with pytest.raises(uploads.HTTPException) as exc_info:
                asyncio.run(uploads.upload_files("thread-local", files=[file]))

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Invalid filename"

        # Path-traversal prefixes are stripped to the basename and accepted safely
        file = UploadFile(filename="../etc/passwd", file=BytesIO(b"data"))
        result = asyncio.run(uploads.upload_files("thread-local", files=[file]))
        assert result.success is True
        assert len(result.files) == 1
        assert result.files[0]["filename"] == "passwd"

    # Only the safely normalised file should exist
    assert [f.name for f in thread_uploads_dir.iterdir()] == ["passwd"]


def test_upload_files_do_not_require_sandbox_availability(tmp_path):
    thread_uploads_dir = tmp_path / "uploads"
    thread_uploads_dir.mkdir(parents=True)

    with (
        patch.object(uploads, "get_uploads_dir", return_value=thread_uploads_dir),
        patch.object(
            uploads,
            "get_sandbox_provider",
            side_effect=AssertionError("uploads should not require sandbox startup"),
            create=True,
        ),
    ):
        file = UploadFile(filename="suboff_solid.stl", file=BytesIO(b"solid submarine"))
        result = asyncio.run(uploads.upload_files("thread-no-sandbox", files=[file]))

    assert result.success is True
    assert len(result.files) == 1
    assert result.files[0]["filename"] == "suboff_solid.stl"
    assert result.files[0]["size"] == str(len(b"solid submarine"))
    assert result.files[0]["virtual_path"] == "/mnt/user-data/uploads/suboff_solid.stl"
    assert result.files[0]["artifact_url"] == "/api/threads/thread-no-sandbox/artifacts/mnt/user-data/uploads/suboff_solid.stl"
    assert (thread_uploads_dir / "suboff_solid.stl").read_bytes() == b"solid submarine"


def test_delete_uploaded_file_removes_generated_markdown_companion(tmp_path):
    thread_uploads_dir = tmp_path / "uploads"
    thread_uploads_dir.mkdir(parents=True)
    (thread_uploads_dir / "report.pdf").write_bytes(b"pdf-bytes")
    (thread_uploads_dir / "report.md").write_text("converted", encoding="utf-8")

    with patch.object(uploads, "get_uploads_dir", return_value=thread_uploads_dir):
        result = asyncio.run(uploads.delete_uploaded_file("thread-aio", "report.pdf"))

    assert result == {"success": True, "message": "Deleted report.pdf"}
    assert not (thread_uploads_dir / "report.pdf").exists()
    assert not (thread_uploads_dir / "report.md").exists()


def test_upload_files_rejects_disallowed_extension(tmp_path):
    thread_uploads_dir = tmp_path / "uploads"
    thread_uploads_dir.mkdir(parents=True)

    with patch.object(uploads, "get_uploads_dir", return_value=thread_uploads_dir):
        file = UploadFile(filename="payload.exe", file=BytesIO(b"binary"))

        with pytest.raises(uploads.HTTPException) as exc_info:
            asyncio.run(uploads.upload_files("thread-unsafe", files=[file]))

    assert exc_info.value.status_code == 400
    assert "File type is not allowed" in str(exc_info.value.detail)


def test_upload_files_rejects_oversized_payload(tmp_path):
    thread_uploads_dir = tmp_path / "uploads"
    thread_uploads_dir.mkdir(parents=True)

    with patch.object(uploads, "get_uploads_dir", return_value=thread_uploads_dir):
        file = UploadFile(
            filename="oversized.stl",
            file=BytesIO(b"x" * (uploads.MAX_UPLOAD_BYTES + 1)),
        )

        with pytest.raises(uploads.HTTPException) as exc_info:
            asyncio.run(uploads.upload_files("thread-oversized", files=[file]))

    assert exc_info.value.status_code == 400
    assert "File too large" in str(exc_info.value.detail)


def test_enforce_upload_budget_rejects_count_and_total_quota():
    with pytest.raises(uploads.HTTPException) as count_exc:
        uploads.enforce_upload_budget(
            existing_files={"a.stl": 4, "b.stl": 4},
            incoming_files=[("c.stl", 2)],
            max_file_count=2,
            max_total_bytes=20,
        )

    assert count_exc.value.status_code == 400
    assert "Too many uploaded files" in str(count_exc.value.detail)

    with pytest.raises(uploads.HTTPException) as total_exc:
        uploads.enforce_upload_budget(
            existing_files={"a.stl": 8},
            incoming_files=[("b.stl", 5)],
            max_file_count=4,
            max_total_bytes=10,
        )

    assert total_exc.value.status_code == 400
    assert "Total upload quota exceeded" in str(total_exc.value.detail)
