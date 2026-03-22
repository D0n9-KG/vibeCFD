from __future__ import annotations

from typing import Protocol

from ..models import RunSummary


class ExecutionEngine(Protocol):
    engine_name: str

    def launch(self, run_id: str) -> None:
        ...

    def run_pipeline(self, run_id: str) -> RunSummary:
        ...
