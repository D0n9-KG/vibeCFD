from unittest.mock import patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.gateway.routers import threads
from deerflow.config.paths import Paths


def test_delete_thread_data_removes_thread_directory(tmp_path):
    paths = Paths(tmp_path)
    thread_dir = paths.thread_dir("thread-cleanup")
    workspace = paths.sandbox_work_dir("thread-cleanup")
    uploads = paths.sandbox_uploads_dir("thread-cleanup")
    outputs = paths.sandbox_outputs_dir("thread-cleanup")

    for directory in [workspace, uploads, outputs]:
        directory.mkdir(parents=True, exist_ok=True)
    (workspace / "notes.txt").write_text("hello", encoding="utf-8")
    (uploads / "report.pdf").write_bytes(b"pdf")
    (outputs / "result.json").write_text("{}", encoding="utf-8")

    assert thread_dir.exists()

    response = threads._delete_thread_data("thread-cleanup", paths=paths)

    assert response.success is True
    assert not thread_dir.exists()


def test_delete_thread_data_is_idempotent_for_missing_directory(tmp_path):
    paths = Paths(tmp_path)

    response = threads._delete_thread_data("missing-thread", paths=paths)

    assert response.success is True
    assert not paths.thread_dir("missing-thread").exists()


def test_delete_thread_data_rejects_invalid_thread_id(tmp_path):
    paths = Paths(tmp_path)

    with pytest.raises(HTTPException) as exc_info:
        threads._delete_thread_data("../escape", paths=paths)

    assert exc_info.value.status_code == 422
    assert "Invalid thread_id" in exc_info.value.detail


def test_delete_thread_route_cleans_thread_directory(tmp_path):
    paths = Paths(tmp_path)
    thread_dir = paths.thread_dir("thread-route")
    paths.sandbox_work_dir("thread-route").mkdir(parents=True, exist_ok=True)
    (paths.sandbox_work_dir("thread-route") / "notes.txt").write_text("hello", encoding="utf-8")

    app = FastAPI()
    app.include_router(threads.router)

    with (
        patch("app.gateway.routers.threads.get_paths", return_value=paths),
        patch.object(
            threads,
            "_delete_langgraph_thread_state",
            return_value={"status": "deleted", "detail": "Deleted LangGraph thread state."},
            create=True,
        ),
    ):
        with TestClient(app) as client:
            response = client.delete("/api/threads/thread-route")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["thread_id"] == "thread-route"
    assert payload["partial_success"] is False
    assert payload["steps"][0]["key"] == "langgraph_state"
    assert payload["steps"][0]["status"] == "deleted"
    assert payload["steps"][1]["key"] == "local_storage"
    assert payload["steps"][1]["status"] == "deleted"
    assert not thread_dir.exists()


def test_delete_thread_route_rejects_invalid_thread_id(tmp_path):
    paths = Paths(tmp_path)

    app = FastAPI()
    app.include_router(threads.router)

    with patch("app.gateway.routers.threads.get_paths", return_value=paths):
        with TestClient(app) as client:
            response = client.delete("/api/threads/../escape")

    assert response.status_code == 404


def test_delete_thread_route_returns_422_for_route_safe_invalid_id(tmp_path):
    paths = Paths(tmp_path)

    app = FastAPI()
    app.include_router(threads.router)

    with patch("app.gateway.routers.threads.get_paths", return_value=paths):
        with TestClient(app) as client:
            response = client.delete("/api/threads/thread.with.dot")

    assert response.status_code == 422
    assert "Invalid thread_id" in response.json()["detail"]


def test_delete_thread_data_returns_generic_500_error(tmp_path):
    paths = Paths(tmp_path)

    with (
        patch.object(paths, "delete_thread_dir", side_effect=OSError("/secret/path")),
        patch.object(threads.logger, "exception") as log_exception,
    ):
        with pytest.raises(HTTPException) as exc_info:
            threads._delete_thread_data("thread-cleanup", paths=paths)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to delete local thread data."
    assert "/secret/path" not in exc_info.value.detail
    log_exception.assert_called_once_with("Failed to delete thread data for %s", "thread-cleanup")


def test_delete_preview_route_summarizes_local_storage_and_langgraph_state(tmp_path):
    paths = Paths(tmp_path)
    workspace = paths.sandbox_work_dir("thread-preview")
    uploads = paths.sandbox_uploads_dir("thread-preview")
    outputs = paths.sandbox_outputs_dir("thread-preview")
    workspace.mkdir(parents=True, exist_ok=True)
    uploads.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    (workspace / "notes.txt").write_text("hello", encoding="utf-8")
    (uploads / "report.pdf").write_bytes(b"pdf")
    (outputs / "result.json").write_text("{}", encoding="utf-8")

    app = FastAPI()
    app.include_router(threads.router)

    with (
        patch("app.gateway.routers.threads.get_paths", return_value=paths),
        patch.object(
            threads,
            "_probe_langgraph_thread_state",
            return_value={"status": "present", "can_delete": True},
            create=True,
        ),
    ):
        with TestClient(app) as client:
            response = client.get("/api/threads/thread-preview/delete-preview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["thread_id"] == "thread-preview"
    assert payload["impact_summary"] == {"total_files": 3, "total_bytes": 10}
    assert payload["local_storage"]["workspace"]["file_count"] == 1
    assert payload["local_storage"]["uploads"]["file_count"] == 1
    assert payload["local_storage"]["outputs"]["file_count"] == 1
    assert payload["local_storage"]["total_files"] == 3
    assert payload["local_storage"]["total_bytes"] == 10
    assert payload["langgraph_state"] == {"status": "present", "can_delete": True}


def test_orphan_audit_route_reports_only_missing_langgraph_threads(tmp_path):
    paths = Paths(tmp_path)
    live_workspace = paths.sandbox_work_dir("live-thread")
    orphan_workspace = paths.sandbox_work_dir("orphan-thread")
    live_workspace.mkdir(parents=True, exist_ok=True)
    orphan_workspace.mkdir(parents=True, exist_ok=True)
    (live_workspace / "keep.txt").write_text("keep", encoding="utf-8")
    (orphan_workspace / "stale.txt").write_text("stale", encoding="utf-8")

    def probe(thread_id: str):
        if thread_id == "live-thread":
            return {"status": "present", "can_delete": True}
        return {"status": "missing", "can_delete": False}

    app = FastAPI()
    app.include_router(threads.router)

    with (
        patch("app.gateway.routers.threads.get_paths", return_value=paths),
        patch.object(
            threads,
            "_probe_langgraph_thread_state",
            side_effect=probe,
            create=True,
        ),
    ):
        with TestClient(app) as client:
            response = client.get("/api/threads/orphans")

    assert response.status_code == 200
    payload = response.json()
    assert payload["orphans"] == [
        {
            "thread_id": "orphan-thread",
            "thread_dir": str(paths.thread_dir("orphan-thread")),
            "total_files": 1,
            "total_bytes": 5,
            "langgraph_state": {"status": "missing", "can_delete": False},
        }
    ]


def test_delete_thread_route_reports_partial_success_when_local_cleanup_fails(tmp_path):
    paths = Paths(tmp_path)
    paths.sandbox_work_dir("thread-partial").mkdir(parents=True, exist_ok=True)
    (paths.sandbox_work_dir("thread-partial") / "notes.txt").write_text("hello", encoding="utf-8")

    app = FastAPI()
    app.include_router(threads.router)

    with (
        patch("app.gateway.routers.threads.get_paths", return_value=paths),
        patch.object(
            threads,
            "_delete_langgraph_thread_state",
            return_value={"status": "deleted", "detail": "Deleted LangGraph thread state."},
            create=True,
        ),
        patch.object(paths, "delete_thread_dir", side_effect=OSError("boom")),
    ):
        with TestClient(app) as client:
            response = client.delete("/api/threads/thread-partial")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["partial_success"] is True
    assert payload["steps"][0]["status"] == "deleted"
    assert payload["steps"][1]["key"] == "local_storage"
    assert payload["steps"][1]["status"] == "failed"
