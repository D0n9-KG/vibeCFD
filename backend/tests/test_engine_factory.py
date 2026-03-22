from pathlib import Path

import pytest

from app.execution.claude_executor_engine import ClaudeExecutorEngine
from app.execution.factory import create_execution_engine
from app.execution.mock_engine import MockExecutionEngine
from app.execution.openfoam_engine import OpenFoamExecutionEngine
from app.store import RunStore


def test_factory_returns_mock_engine(monkeypatch: pytest.MonkeyPatch, temp_workspace: Path) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "mock")

    engine = create_execution_engine(RunStore())

    assert isinstance(engine, MockExecutionEngine)


def test_factory_returns_openfoam_engine(
    monkeypatch: pytest.MonkeyPatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "openfoam")

    engine = create_execution_engine(RunStore())

    assert isinstance(engine, OpenFoamExecutionEngine)


def test_factory_returns_claude_executor_engine(
    monkeypatch: pytest.MonkeyPatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "claude_executor")

    engine = create_execution_engine(RunStore())

    assert isinstance(engine, ClaudeExecutorEngine)


def test_factory_rejects_unknown_engine(
    monkeypatch: pytest.MonkeyPatch, temp_workspace: Path
) -> None:
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "mystery")

    with pytest.raises(ValueError, match="Unsupported execution engine"):
        create_execution_engine(RunStore())
