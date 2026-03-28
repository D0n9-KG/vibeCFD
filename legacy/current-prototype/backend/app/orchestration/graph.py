from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from ..models import RunSummary
from ..store import RunStore
from ..execution.base import ExecutionEngine
from ..services.workflow import WorkflowService


class OrchestratorState(TypedDict):
    mode: Literal["prepare", "execute"]
    run_id: str
    reviewer_notes: NotRequired[str]
    run: NotRequired[RunSummary]


def build_orchestration_graph(
    *,
    store: RunStore,
    workflow_service: WorkflowService,
    execution_engine: ExecutionEngine,
):
    graph = StateGraph(OrchestratorState)

    def route_mode(state: OrchestratorState) -> str:
        return state["mode"]

    def prepare_run(state: OrchestratorState) -> OrchestratorState:
        run = workflow_service.prepare_run(state["run_id"])
        return {"run": run}

    def confirm_run(state: OrchestratorState) -> OrchestratorState:
        run = store.confirm_run(state["run_id"], state.get("reviewer_notes", ""))
        return {"run": run}

    graph.add_node("prepare_run", prepare_run)
    graph.add_node("confirm_run", confirm_run)

    graph.add_conditional_edges(
        START,
        route_mode,
        {
            "prepare": "prepare_run",
            "execute": "confirm_run",
        },
    )
    graph.add_edge("prepare_run", END)
    graph.add_edge("confirm_run", END)

    return graph.compile()
