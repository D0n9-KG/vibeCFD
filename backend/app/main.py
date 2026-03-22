from __future__ import annotations

import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import get_settings
from .dispatcher import ExecutionDispatcher
from .execution.factory import create_execution_engine
from .models import CancelRunRequest, ConfirmRunRequest, TaskSubmission
from .orchestration.service import WorkflowOrchestrator
from .services.cases import CaseLibrary
from .services.runs import RunService
from .store import RunStore


def _stop_dispatcher(app: FastAPI) -> None:
    dispatcher = getattr(app.state, "dispatcher", None)
    if dispatcher is not None:
        dispatcher.stop()
        app.state.dispatcher = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_services(app)
    try:
        yield
    finally:
        _stop_dispatcher(app)


app = FastAPI(title="Submarine Demo Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _settings_key() -> tuple[str, str, str, float]:
    settings = get_settings()
    return (
        str(settings.root_dir),
        settings.execution_engine,
        settings.executor_base_url,
        settings.dispatch_poll_interval_seconds,
    )


def _ensure_services(app: FastAPI) -> None:
    if getattr(app.state, "settings_key", None) == _settings_key() and hasattr(app.state, "run_service"):
        dispatcher = getattr(app.state, "dispatcher", None)
        if dispatcher is not None:
            dispatcher.start()
        return

    _stop_dispatcher(app)

    settings = get_settings()
    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)

    run_store = RunStore()
    case_library = CaseLibrary()
    execution_engine = create_execution_engine(run_store)
    dispatcher = ExecutionDispatcher(
        store=run_store,
        execution_engine=execution_engine,
        poll_interval_seconds=settings.dispatch_poll_interval_seconds,
    )
    dispatcher.start()

    app.state.run_store = run_store
    app.state.run_service = RunService(store=run_store)
    app.state.case_library = case_library
    app.state.execution_engine = execution_engine
    app.state.dispatcher = dispatcher
    app.state.orchestrator = WorkflowOrchestrator(
        store=run_store,
        case_library=case_library,
        execution_engine=execution_engine,
    )
    app.state.settings_key = _settings_key()


@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    request: Request,
    task_description: str = Form(...),
    task_type: str = Form(...),
    geometry_family_hint: str | None = Form(None),
    operating_notes: str = Form(""),
    geometry_file: UploadFile | None = File(None),
):
    _ensure_services(request.app)
    settings = get_settings()
    uploaded_path: Path | None = None
    geometry_file_name: str | None = None

    if geometry_file is not None:
        geometry_file_name = geometry_file.filename
        suffix = Path(geometry_file.filename or "geometry.bin").suffix
        uploaded_path = settings.uploads_dir / f"{uuid4().hex}{suffix}"
        with uploaded_path.open("wb") as handle:
            shutil.copyfileobj(geometry_file.file, handle)

    submission = TaskSubmission(
        task_description=task_description,
        task_type=task_type,
        geometry_family_hint=geometry_family_hint,
        geometry_file_name=geometry_file_name,
        operating_notes=operating_notes,
    )

    run = request.app.state.run_service.create_run(submission, uploaded_path)
    return request.app.state.orchestrator.prepare_run(run.run_id)


@app.get("/api/runs")
def list_runs(request: Request):
    _ensure_services(request.app)
    return request.app.state.run_store.list_runs()


@app.get("/api/runs/{run_id}")
def get_run(run_id: str, request: Request):
    _ensure_services(request.app)
    try:
        return request.app.state.run_store.get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found.") from exc


@app.get("/api/runs/{run_id}/events")
def list_run_events(run_id: str, request: Request):
    _ensure_services(request.app)
    try:
        return request.app.state.run_store.list_events(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found.") from exc


@app.get("/api/runs/{run_id}/attempts")
def list_run_attempts(run_id: str, request: Request):
    _ensure_services(request.app)
    try:
        return request.app.state.run_store.list_attempts(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found.") from exc


@app.post("/api/runs/{run_id}/confirm", status_code=status.HTTP_202_ACCEPTED)
def confirm_run(run_id: str, payload: ConfirmRunRequest, request: Request):
    _ensure_services(request.app)
    if not payload.confirmed:
        raise HTTPException(status_code=400, detail="Run confirmation is required to continue.")

    try:
        run = request.app.state.orchestrator.execute_run(run_id, payload.reviewer_notes)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found.") from exc

    return run


@app.post("/api/runs/{run_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
def cancel_run(run_id: str, payload: CancelRunRequest, request: Request):
    _ensure_services(request.app)
    try:
        return request.app.state.run_store.cancel_queued_run(run_id, payload.reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/runs/{run_id}/retry", status_code=status.HTTP_201_CREATED)
def retry_run(run_id: str, request: Request):
    _ensure_services(request.app)
    try:
        retried = request.app.state.run_service.retry_run(run_id)
        return request.app.state.orchestrator.prepare_run(retried.run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/runs/{run_id}/artifacts/{artifact_path:path}")
def read_artifact(run_id: str, artifact_path: str, request: Request):
    _ensure_services(request.app)
    try:
        run = request.app.state.run_store.get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found.") from exc

    file_path = Path(run.run_directory) / artifact_path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found.")

    return FileResponse(file_path)
