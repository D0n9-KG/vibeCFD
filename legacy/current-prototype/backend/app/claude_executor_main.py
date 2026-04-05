from __future__ import annotations

from fastapi import FastAPI, Request

from .agent_runtime.service import AgentExecutionService
from .executor_protocol import ExecutorTaskRequest, ExecutorTaskResult


app = FastAPI(title="Submarine Agent Executor")


def _get_execution_service(app: FastAPI) -> AgentExecutionService:
    service = getattr(app.state, "execution_service", None)
    if service is None:
        service = AgentExecutionService()
        app.state.execution_service = service
    return service


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/execute")
def execute_task(payload: ExecutorTaskRequest, request: Request) -> ExecutorTaskResult:
    return _get_execution_service(request.app).execute(payload)
