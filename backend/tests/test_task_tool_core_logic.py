"""Core behavior tests for task tool orchestration."""

import importlib
from enum import Enum
from types import SimpleNamespace
from unittest.mock import MagicMock

from langgraph.types import Command

from deerflow.subagents.config import SubagentConfig

# Use module import so tests can patch the exact symbols referenced inside task_tool().
task_tool_module = importlib.import_module("deerflow.tools.builtins.task_tool")


class FakeSubagentStatus(Enum):
    # Match production enum values so branch comparisons behave identically.
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


def _make_runtime() -> SimpleNamespace:
    # Minimal ToolRuntime-like object; task_tool only reads these three attributes.
    return SimpleNamespace(
        state={
            "sandbox": {"sandbox_id": "local"},
            "thread_data": {
                "workspace_path": "/tmp/workspace",
                "uploads_path": "/tmp/uploads",
                "outputs_path": "/tmp/outputs",
            },
        },
        context={"thread_id": "thread-1"},
        config={"metadata": {"model_name": "ark-model", "trace_id": "trace-1"}},
    )


def _make_subagent_config() -> SubagentConfig:
    return SubagentConfig(
        name="general-purpose",
        description="General helper",
        system_prompt="Base system prompt",
        max_turns=50,
        timeout_seconds=10,
    )


def _make_result(
    status: FakeSubagentStatus,
    *,
    ai_messages: list[dict] | None = None,
    result: str | None = None,
    error: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        ai_messages=ai_messages or [],
        result=result,
        error=error,
    )


def test_task_tool_returns_error_for_unknown_subagent(monkeypatch):
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: None)

    result = task_tool_module.task_tool.func(
        runtime=None,
        description="执行任务",
        prompt="do work",
        subagent_type="general-purpose",
        tool_call_id="tc-1",
    )

    assert result.startswith("Error: Unknown subagent type")


def test_task_tool_accepts_submarine_subagent(monkeypatch):
    config = _make_subagent_config()
    config.name = "submarine-task-intelligence"
    events = []

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(
        task_tool_module,
        "SubagentExecutor",
        type("DummyExecutor", (), {"__init__": lambda self, **kwargs: None, "execute_async": lambda self, prompt, task_id=None: task_id}),
    )
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: "",
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_background_task_result",
        lambda _: _make_result(FakeSubagentStatus.COMPLETED, result="submarine done"),
    )
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: events.append)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda _: None)
    monkeypatch.setattr("deerflow.tools.get_available_tools", lambda **kwargs: [])

    output = task_tool_module.task_tool.func(
        runtime=_make_runtime(),
        description="案例理解",
        prompt="analyze submarine task",
        subagent_type="submarine-task-intelligence",
        tool_call_id="tc-submarine",
    )

    assert output == "Task Succeeded. Result: submarine done"
    assert events[-1]["type"] == "task_completed"


def test_task_tool_emits_running_and_completed_events(monkeypatch):
    config = _make_subagent_config()
    runtime = _make_runtime()
    events = []
    captured = {}
    get_available_tools = MagicMock(return_value=["tool-a", "tool-b"])

    class DummyExecutor:
        def __init__(self, **kwargs):
            captured["executor_kwargs"] = kwargs

        def execute_async(self, prompt, task_id=None):
            captured["prompt"] = prompt
            captured["task_id"] = task_id
            return task_id or "generated-task-id"

    # Simulate two polling rounds: first running (with one message), then completed.
    responses = iter(
        [
            _make_result(FakeSubagentStatus.RUNNING, ai_messages=[{"id": "m1", "content": "phase-1"}]),
            _make_result(
                FakeSubagentStatus.COMPLETED,
                ai_messages=[{"id": "m1", "content": "phase-1"}, {"id": "m2", "content": "phase-2"}],
                result="all done",
            ),
        ]
    )

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(task_tool_module, "SubagentExecutor", DummyExecutor)
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: f"Skills Appendix: {sorted(available_skills) if available_skills else 'all'}",
    )
    monkeypatch.setattr(task_tool_module, "get_background_task_result", lambda _: next(responses))
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: events.append)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda _: None)
    # task_tool lazily imports from deerflow.tools at call time, so patch that module-level function.
    monkeypatch.setattr("deerflow.tools.get_available_tools", get_available_tools)

    output = task_tool_module.task_tool.func(
        runtime=runtime,
        description="运行子任务",
        prompt="collect diagnostics",
        subagent_type="general-purpose",
        tool_call_id="tc-123",
        max_turns=7,
    )

    assert output == "Task Succeeded. Result: all done"
    assert captured["prompt"] == "collect diagnostics"
    assert captured["task_id"] == "tc-123"
    assert captured["executor_kwargs"]["thread_id"] == "thread-1"
    assert captured["executor_kwargs"]["parent_model"] == "ark-model"
    assert captured["executor_kwargs"]["config"].max_turns == 7
    assert "Skills Appendix: all" in captured["executor_kwargs"]["config"].system_prompt

    get_available_tools.assert_called_once_with(model_name="ark-model", subagent_enabled=False)

    event_types = [e["type"] for e in events]
    assert event_types == ["task_started", "task_running", "task_running", "task_completed"]
    assert events[-1]["result"] == "all done"


def test_task_tool_prefers_explicit_target_skills_over_graph_recommendations(monkeypatch):
    config = _make_subagent_config()
    captured = {}

    class DummyExecutor:
        def __init__(self, **kwargs):
            captured["executor_kwargs"] = kwargs

        def execute_async(self, prompt, task_id=None):
            return task_id or "generated-task-id"

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(task_tool_module, "SubagentExecutor", DummyExecutor)
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "_resolve_target_skills",
        lambda target_skills: set(target_skills) if target_skills else None,
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: f"Skills Appendix: {sorted(available_skills) if available_skills else 'all'}",
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_background_task_result",
        lambda *_args, **_kwargs: _make_result(FakeSubagentStatus.COMPLETED, result="done"),
    )
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: lambda *_args, **_kwargs: None)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("deerflow.tools.get_available_tools", lambda **kwargs: [])

    output = task_tool_module.task_tool.func(
        runtime=_make_runtime(),
        description="鍒嗘淳浠诲姟",
        prompt="finish report review",
        subagent_type="submarine-result-reporting",
        tool_call_id="tc-target-skills",
        target_skills=["submarine-report"],
    )

    assert isinstance(output, Command)
    assert output.update["messages"][0].content == "Task Succeeded. Result: done"
    assert captured["executor_kwargs"]["config"].system_prompt == "Base system prompt"
    assert output.update["submarine_runtime"]["activity_timeline"][-1]["skill_names"] == ["submarine-report"]


def test_task_tool_does_not_append_skill_appendix_for_specialized_submarine_subagents(
    monkeypatch,
):
    config = _make_subagent_config()
    config.name = "submarine-task-intelligence"
    config.system_prompt = "Specialized submarine prompt"
    captured = {}

    class DummyExecutor:
        def __init__(self, **kwargs):
            captured["executor_kwargs"] = kwargs

        def execute_async(self, prompt, task_id=None):
            return task_id or "generated-task-id"

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(task_tool_module, "SubagentExecutor", DummyExecutor)
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "_resolve_target_skills",
        lambda target_skills: set(target_skills) if target_skills else None,
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: "Skills Appendix: should not be injected",
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_background_task_result",
        lambda *_args, **_kwargs: _make_result(FakeSubagentStatus.COMPLETED, result="done"),
    )
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: lambda *_args, **_kwargs: None)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("deerflow.tools.get_available_tools", lambda **kwargs: [])

    output = task_tool_module.task_tool.func(
        runtime=_make_runtime(),
        description="案例理解",
        prompt="analyze baseline task",
        subagent_type="submarine-task-intelligence",
        tool_call_id="tc-subagent-skip-skill-appendix",
        target_skills=["submarine-case-search"],
    )

    assert isinstance(output, Command)
    assert output.update["messages"][0].content == "Task Succeeded. Result: done"
    assert captured["executor_kwargs"]["config"].system_prompt == "Specialized submarine prompt"


def test_task_tool_keeps_specialized_subagent_turn_budget_above_builtin_floor(monkeypatch):
    config = _make_subagent_config()
    config.name = "submarine-task-intelligence"
    config.max_turns = 30
    captured = {}

    class DummyExecutor:
        def __init__(self, **kwargs):
            captured["executor_kwargs"] = kwargs

        def execute_async(self, prompt, task_id=None):
            return task_id or "generated-task-id"

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(task_tool_module, "SubagentExecutor", DummyExecutor)
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: "",
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_background_task_result",
        lambda *_args, **_kwargs: _make_result(FakeSubagentStatus.COMPLETED, result="done"),
    )
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: lambda *_args, **_kwargs: None)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("deerflow.tools.get_available_tools", lambda **kwargs: [])

    output = task_tool_module.task_tool.func(
        runtime=_make_runtime(),
        description="案例理解",
        prompt="analyze baseline task",
        subagent_type="submarine-task-intelligence",
        tool_call_id="tc-subagent-floor",
        max_turns=8,
    )

    assert output == "Task Succeeded. Result: done"
    assert captured["executor_kwargs"]["config"].max_turns == 30


def test_task_tool_persists_target_skills_into_execution_plan(monkeypatch):
    config = _make_subagent_config()
    config.name = "submarine-result-reporting"
    runtime = _make_runtime()
    runtime.state["submarine_runtime"] = {
        "current_stage": "solver-dispatch",
        "task_summary": "review the run",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/demo.stl",
        "review_status": "ready_for_supervisor",
        "next_recommended_stage": "result-reporting",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
        "execution_plan": [
            {
                "role_id": "result-reporting",
                "owner": "DeerFlow result-reporting",
                "goal": "Organize metrics into the final report.",
                "status": "ready",
            }
        ],
        "activity_timeline": [],
    }

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(
        task_tool_module,
        "SubagentExecutor",
        type("DummyExecutor", (), {"__init__": lambda self, **kwargs: None, "execute_async": lambda self, prompt, task_id=None: task_id}),
    )
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "_resolve_target_skills",
        lambda target_skills: set(target_skills) if target_skills else None,
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: "",
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_background_task_result",
        lambda *_args, **_kwargs: _make_result(FakeSubagentStatus.COMPLETED, result="done"),
    )
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: lambda *_args, **_kwargs: None)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("deerflow.tools.get_available_tools", lambda **kwargs: [])

    output = task_tool_module.task_tool.func(
        runtime=runtime,
        description="鍒嗘淳缁撴灉鏁寸悊",
        prompt="finish result reporting",
        subagent_type="submarine-result-reporting",
        tool_call_id="tc-plan-target-skills",
        target_skills=["submarine-report", "submarine-result-acceptance"],
    )

    assert isinstance(output, Command)
    updated_runtime = output.update["submarine_runtime"]
    assert updated_runtime["execution_plan"][0]["target_skills"] == [
        "submarine-report",
        "submarine-result-acceptance",
    ]
    assert updated_runtime["activity_timeline"][-1]["role_id"] == "result-reporting"


def test_task_tool_returns_error_when_explicit_target_skills_are_not_enabled(monkeypatch):
    config = _make_subagent_config()

    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "_resolve_target_skills",
        lambda *_args, **_kwargs: set(),
    )

    output = task_tool_module.task_tool.func(
        runtime=_make_runtime(),
        description="鍒嗘淳浠诲姟",
        prompt="finish report review",
        subagent_type="submarine-result-reporting",
        tool_call_id="tc-invalid-target-skills",
        target_skills=["missing-skill"],
    )

    assert output.startswith("Error: None of the requested target_skills are currently enabled")


def test_task_tool_returns_failed_message(monkeypatch):
    config = _make_subagent_config()
    events = []

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(
        task_tool_module,
        "SubagentExecutor",
        type("DummyExecutor", (), {"__init__": lambda self, **kwargs: None, "execute_async": lambda self, prompt, task_id=None: task_id}),
    )
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: "",
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_background_task_result",
        lambda _: _make_result(FakeSubagentStatus.FAILED, error="subagent crashed"),
    )
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: events.append)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda _: None)
    monkeypatch.setattr("deerflow.tools.get_available_tools", lambda **kwargs: [])

    output = task_tool_module.task_tool.func(
        runtime=_make_runtime(),
        description="执行任务",
        prompt="do fail",
        subagent_type="general-purpose",
        tool_call_id="tc-fail",
    )

    assert output == "Task failed. Error: subagent crashed"
    assert events[-1]["type"] == "task_failed"
    assert events[-1]["error"] == "subagent crashed"


def test_task_tool_returns_timed_out_message(monkeypatch):
    config = _make_subagent_config()
    events = []

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(
        task_tool_module,
        "SubagentExecutor",
        type("DummyExecutor", (), {"__init__": lambda self, **kwargs: None, "execute_async": lambda self, prompt, task_id=None: task_id}),
    )
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: "",
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_background_task_result",
        lambda _: _make_result(FakeSubagentStatus.TIMED_OUT, error="timeout"),
    )
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: events.append)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda _: None)
    monkeypatch.setattr("deerflow.tools.get_available_tools", lambda **kwargs: [])

    output = task_tool_module.task_tool.func(
        runtime=_make_runtime(),
        description="执行任务",
        prompt="do timeout",
        subagent_type="general-purpose",
        tool_call_id="tc-timeout",
    )

    assert output == "Task timed out. Error: timeout"
    assert events[-1]["type"] == "task_timed_out"
    assert events[-1]["error"] == "timeout"


def test_task_tool_polling_safety_timeout(monkeypatch):
    config = _make_subagent_config()
    # Keep max_poll_count small for test speed: (1 + 60) // 5 = 12
    config.timeout_seconds = 1
    events = []

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(
        task_tool_module,
        "SubagentExecutor",
        type("DummyExecutor", (), {"__init__": lambda self, **kwargs: None, "execute_async": lambda self, prompt, task_id=None: task_id}),
    )
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: "",
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_background_task_result",
        lambda _: _make_result(FakeSubagentStatus.RUNNING, ai_messages=[]),
    )
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: events.append)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda _: None)
    monkeypatch.setattr("deerflow.tools.get_available_tools", lambda **kwargs: [])

    output = task_tool_module.task_tool.func(
        runtime=_make_runtime(),
        description="执行任务",
        prompt="never finish",
        subagent_type="general-purpose",
        tool_call_id="tc-safety-timeout",
    )

    assert output.startswith("Task polling timed out after 0 minutes")
    assert events[0]["type"] == "task_started"
    assert events[-1]["type"] == "task_timed_out"


def test_cleanup_called_on_completed(monkeypatch):
    """Verify cleanup_background_task is called when task completes."""
    config = _make_subagent_config()
    events = []
    cleanup_calls = []

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(
        task_tool_module,
        "SubagentExecutor",
        type("DummyExecutor", (), {"__init__": lambda self, **kwargs: None, "execute_async": lambda self, prompt, task_id=None: task_id}),
    )
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: "",
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_background_task_result",
        lambda _: _make_result(FakeSubagentStatus.COMPLETED, result="done"),
    )
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: events.append)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda _: None)
    monkeypatch.setattr("deerflow.tools.get_available_tools", lambda **kwargs: [])
    monkeypatch.setattr(
        task_tool_module,
        "cleanup_background_task",
        lambda task_id: cleanup_calls.append(task_id),
    )

    output = task_tool_module.task_tool.func(
        runtime=_make_runtime(),
        description="执行任务",
        prompt="complete task",
        subagent_type="general-purpose",
        tool_call_id="tc-cleanup-completed",
    )

    assert output == "Task Succeeded. Result: done"
    assert cleanup_calls == ["tc-cleanup-completed"]


def test_cleanup_called_on_failed(monkeypatch):
    """Verify cleanup_background_task is called when task fails."""
    config = _make_subagent_config()
    events = []
    cleanup_calls = []

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(
        task_tool_module,
        "SubagentExecutor",
        type("DummyExecutor", (), {"__init__": lambda self, **kwargs: None, "execute_async": lambda self, prompt, task_id=None: task_id}),
    )
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: "",
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_background_task_result",
        lambda _: _make_result(FakeSubagentStatus.FAILED, error="error"),
    )
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: events.append)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda _: None)
    monkeypatch.setattr("deerflow.tools.get_available_tools", lambda **kwargs: [])
    monkeypatch.setattr(
        task_tool_module,
        "cleanup_background_task",
        lambda task_id: cleanup_calls.append(task_id),
    )

    output = task_tool_module.task_tool.func(
        runtime=_make_runtime(),
        description="执行任务",
        prompt="fail task",
        subagent_type="general-purpose",
        tool_call_id="tc-cleanup-failed",
    )

    assert output == "Task failed. Error: error"
    assert cleanup_calls == ["tc-cleanup-failed"]


def test_cleanup_called_on_timed_out(monkeypatch):
    """Verify cleanup_background_task is called when task times out."""
    config = _make_subagent_config()
    events = []
    cleanup_calls = []

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(
        task_tool_module,
        "SubagentExecutor",
        type("DummyExecutor", (), {"__init__": lambda self, **kwargs: None, "execute_async": lambda self, prompt, task_id=None: task_id}),
    )
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: "",
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_background_task_result",
        lambda _: _make_result(FakeSubagentStatus.TIMED_OUT, error="timeout"),
    )
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: events.append)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda _: None)
    monkeypatch.setattr("deerflow.tools.get_available_tools", lambda **kwargs: [])
    monkeypatch.setattr(
        task_tool_module,
        "cleanup_background_task",
        lambda task_id: cleanup_calls.append(task_id),
    )

    output = task_tool_module.task_tool.func(
        runtime=_make_runtime(),
        description="执行任务",
        prompt="timeout task",
        subagent_type="general-purpose",
        tool_call_id="tc-cleanup-timedout",
    )

    assert output == "Task timed out. Error: timeout"
    assert cleanup_calls == ["tc-cleanup-timedout"]


def test_cleanup_not_called_on_polling_safety_timeout(monkeypatch):
    """Verify cleanup_background_task is NOT called on polling safety timeout.

    This prevents race conditions where the background task is still running
    but the polling loop gives up. The cleanup should happen later when the
    executor completes and sets a terminal status.
    """
    config = _make_subagent_config()
    # Keep max_poll_count small for test speed: (1 + 60) // 5 = 12
    config.timeout_seconds = 1
    events = []
    cleanup_calls = []

    monkeypatch.setattr(task_tool_module, "SubagentStatus", FakeSubagentStatus)
    monkeypatch.setattr(
        task_tool_module,
        "SubagentExecutor",
        type("DummyExecutor", (), {"__init__": lambda self, **kwargs: None, "execute_async": lambda self, prompt, task_id=None: task_id}),
    )
    monkeypatch.setattr(task_tool_module, "get_subagent_config", lambda _: config)
    monkeypatch.setattr(
        task_tool_module,
        "get_skills_prompt_section",
        lambda available_skills=None: "",
    )
    monkeypatch.setattr(
        task_tool_module,
        "get_background_task_result",
        lambda _: _make_result(FakeSubagentStatus.RUNNING, ai_messages=[]),
    )
    monkeypatch.setattr(task_tool_module, "get_stream_writer", lambda: events.append)
    monkeypatch.setattr(task_tool_module.time, "sleep", lambda _: None)
    monkeypatch.setattr("deerflow.tools.get_available_tools", lambda **kwargs: [])
    monkeypatch.setattr(
        task_tool_module,
        "cleanup_background_task",
        lambda task_id: cleanup_calls.append(task_id),
    )

    output = task_tool_module.task_tool.func(
        runtime=_make_runtime(),
        description="执行任务",
        prompt="never finish",
        subagent_type="general-purpose",
        tool_call_id="tc-no-cleanup-safety-timeout",
    )

    assert output.startswith("Task polling timed out after 0 minutes")
    # cleanup should NOT be called because the task is still RUNNING
    assert cleanup_calls == []
