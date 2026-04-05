from __future__ import annotations

from ..execution.base import ExecutionEngine
from ..models import RunSummary
from ..services.cases import CaseLibrary
from ..services.workflow import WorkflowService
from ..store import RunStore
from .graph import build_orchestration_graph


class WorkflowOrchestrator:
    def __init__(
        self,
        *,
        store: RunStore,
        case_library: CaseLibrary,
        execution_engine: ExecutionEngine,
    ) -> None:
        self.store = store
        self.execution_engine = execution_engine
        self.workflow_service = WorkflowService(case_library=case_library, store=store)
        self.graph = build_orchestration_graph(
            store=store,
            workflow_service=self.workflow_service,
            execution_engine=execution_engine,
        )

    def prepare_run(self, run_id: str) -> RunSummary:
        state = self.graph.invoke({"mode": "prepare", "run_id": run_id})
        return state["run"]

    def execute_run(self, run_id: str, reviewer_notes: str = "") -> RunSummary:
        state = self.graph.invoke(
            {
                "mode": "execute",
                "run_id": run_id,
                "reviewer_notes": reviewer_notes,
            }
        )
        return state["run"]
