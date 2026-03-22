from __future__ import annotations

from fastapi import FastAPI

from .executor_protocol import ExecutorTaskRequest, ExecutorTaskResult
from .executor_stub import run_stub_executor


app = FastAPI(title="Submarine Claude Executor")


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/execute")
def execute_task(payload: ExecutorTaskRequest) -> ExecutorTaskResult:
    return run_stub_executor(payload)
