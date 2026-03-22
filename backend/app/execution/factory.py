from __future__ import annotations

from ..config import get_settings
from ..store import RunStore
from .base import ExecutionEngine
from .claude_executor_engine import ClaudeExecutorEngine
from .mock_engine import MockExecutionEngine
from .openfoam_engine import OpenFoamExecutionEngine


def create_execution_engine(store: RunStore) -> ExecutionEngine:
    settings = get_settings()

    if settings.execution_engine == "mock":
        return MockExecutionEngine(store)
    if settings.execution_engine == "openfoam":
        return OpenFoamExecutionEngine(store)
    if settings.execution_engine == "claude_executor":
        return ClaudeExecutorEngine(store=store)

    raise ValueError(f"Unsupported execution engine: {settings.execution_engine}")
