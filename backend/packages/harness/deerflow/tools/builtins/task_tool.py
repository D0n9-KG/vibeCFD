"""Task tool for delegating work to subagents."""

import logging
import time
import uuid
from dataclasses import replace
from typing import Annotated, Literal

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.config import get_stream_writer
from langgraph.types import Command
from langgraph.typing import ContextT

from deerflow.agents.lead_agent.prompt import get_skills_prompt_section
from deerflow.agents.thread_state import ThreadState
from deerflow.domain.submarine.contracts import (
    SubmarineExecutionPlanItem,
    build_runtime_event,
    extend_runtime_timeline,
)
from deerflow.skills import load_skills
from deerflow.subagents import SubagentExecutor, get_subagent_config
from deerflow.subagents.executor import SubagentStatus, cleanup_background_task, get_background_task_result

logger = logging.getLogger(__name__)

_SUBMARINE_SUBAGENT_ROUTING: dict[str, dict[str, str]] = {
    "submarine-task-intelligence": {
        "stage": "task-intelligence",
        "role_id": "task-intelligence",
        "label": "task-intelligence",
    },
    "submarine-geometry-preflight": {
        "stage": "geometry-preflight",
        "role_id": "geometry-preflight",
        "label": "geometry-preflight",
    },
    "submarine-solver-dispatch": {
        "stage": "solver-dispatch",
        "role_id": "solver-dispatch",
        "label": "solver-dispatch",
    },
    "submarine-result-reporting": {
        "stage": "result-reporting",
        "role_id": "result-reporting",
        "label": "result-reporting",
    },
}


def _resolve_target_skills(target_skills: list[str] | None) -> set[str] | None:
    if target_skills is None:
        return None

    enabled_skills = {
        skill.name
        for skill in load_skills(enabled_only=True)
    }
    requested = {skill_name for skill_name in target_skills if skill_name in enabled_skills}
    return requested


def _update_execution_plan_with_target_skills(
    existing_plan: list[dict] | None,
    *,
    role_id: str,
    target_skills: list[str],
) -> list[dict]:
    normalized_plan = [
        SubmarineExecutionPlanItem.model_validate(item)
        for item in (existing_plan or [])
    ]

    for item in normalized_plan:
        if item.role_id == role_id:
            item.target_skills = list(target_skills)
            break
    else:
        normalized_plan.append(
            SubmarineExecutionPlanItem(
                role_id=role_id,
                owner=f"DeerFlow {role_id}",
                goal="Track explicitly delegated skills for the active subagent task.",
                status="ready",
                target_skills=list(target_skills),
            )
        )

    return [item.model_dump(mode="json") for item in normalized_plan]


def _build_submarine_runtime_update(
    runtime: ToolRuntime[ContextT, ThreadState] | None,
    *,
    subagent_type: str,
    description: str,
    target_skills: list[str] | None,
    terminal_status: str,
    result_summary: str,
) -> dict | None:
    if runtime is None or not target_skills:
        return None

    mapping = _SUBMARINE_SUBAGENT_ROUTING.get(subagent_type)
    if mapping is None:
        return None

    existing_runtime = dict(((runtime.state or {}).get("submarine_runtime")) or {})
    timeline = extend_runtime_timeline(
        existing_runtime,
        build_runtime_event(
            stage=mapping["stage"],
            actor="claude-code-supervisor",
            role_id=mapping["role_id"],
            title=f"Claude Code delegated {mapping['label']}",
            summary=(
                f"{description}: {result_summary}"
                if description
                else result_summary
            ),
            status=terminal_status,
            skill_names=list(target_skills),
        ),
    )

    existing_runtime["activity_timeline"] = timeline
    existing_runtime["execution_plan"] = _update_execution_plan_with_target_skills(
        existing_runtime.get("execution_plan"),
        role_id=mapping["role_id"],
        target_skills=list(target_skills),
    )
    return existing_runtime


def _build_terminal_response(
    runtime: ToolRuntime[ContextT, ThreadState] | None,
    *,
    subagent_type: str,
    description: str,
    tool_call_id: str,
    target_skills: list[str] | None,
    terminal_status: str,
    message: str,
) -> str | Command:
    runtime_update = _build_submarine_runtime_update(
        runtime,
        subagent_type=subagent_type,
        description=description,
        target_skills=target_skills,
        terminal_status=terminal_status,
        result_summary=message,
    )
    if runtime_update is None:
        return message

    return Command(
        update={
            "submarine_runtime": runtime_update,
            "messages": [ToolMessage(content=message, tool_call_id=tool_call_id)],
        }
    )


@tool("task", parse_docstring=True)
def task_tool(
    runtime: ToolRuntime[ContextT, ThreadState],
    description: str,
    prompt: str,
    subagent_type: Literal[
        "general-purpose",
        "bash",
        "submarine-task-intelligence",
        "submarine-geometry-preflight",
        "submarine-solver-dispatch",
        "submarine-result-reporting",
    ],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_turns: int | None = None,
    target_skills: list[str] | None = None,
) -> str | Command:
    """Delegate a task to a specialized subagent that runs in its own context.

    Subagents help you:
    - Preserve context by keeping exploration and implementation separate
    - Handle complex multi-step tasks autonomously
    - Execute commands or operations in isolated contexts

    Available subagent types:
    - **general-purpose**: A capable agent for complex, multi-step tasks that require
      both exploration and action. Use when the task requires complex reasoning,
      multiple dependent steps, or would benefit from isolated context.
    - **bash**: Command execution specialist for running bash commands. Use for
      git operations, build processes, or when command output would be verbose.
    - **submarine-task-intelligence**: Specialized for submarine CFD case matching,
      task understanding, and workflow recommendation.
    - **submarine-geometry-preflight**: Specialized for uploaded submarine geometry
      inspection, preprocessing readiness, and risk discovery.
    - **submarine-solver-dispatch**: Specialized for OpenFOAM-oriented solver planning,
      dispatch preparation, and execution assumptions.
    - **submarine-result-reporting**: Specialized for Chinese result summaries, final
      reporting, and artifact-oriented synthesis.

    When to use this tool:
    - Complex tasks requiring multiple steps or tools
    - Tasks that produce verbose output
    - When you want to isolate context from the main conversation
    - Parallel research or exploration tasks

    When NOT to use this tool:
    - Simple, single-step operations (use tools directly)
    - Tasks requiring user interaction or clarification

    Args:
        description: A short (3-5 word) description of the task for logging/display. ALWAYS PROVIDE THIS PARAMETER FIRST.
        prompt: The task description for the subagent. Be specific and clear about what needs to be done. ALWAYS PROVIDE THIS PARAMETER SECOND.
        subagent_type: The type of subagent to use. ALWAYS PROVIDE THIS PARAMETER THIRD.
        max_turns: Optional maximum number of agent turns. Defaults to subagent's configured max.
        target_skills: Optional enabled skill names selected by the lead agent for this
            delegated task. When omitted, the subagent receives the normal enabled skill
            pool without additional graph-based narrowing.
    """
    # Get subagent configuration
    config = get_subagent_config(subagent_type)
    if config is None:
        return (
            f"Error: Unknown subagent type '{subagent_type}'. Available: "
            "general-purpose, bash, submarine-task-intelligence, "
            "submarine-geometry-preflight, submarine-solver-dispatch, "
            "submarine-result-reporting"
        )

    # Build config overrides
    overrides: dict = {}

    resolved_target_skills = _resolve_target_skills(target_skills)
    if target_skills is not None and not resolved_target_skills:
        return (
            "Error: None of the requested target_skills are currently enabled. "
            "Please choose enabled skills or omit target_skills to use the normal enabled skill pool."
        )

    resolved_target_skills_list = (
        sorted(resolved_target_skills)
        if resolved_target_skills is not None
        else None
    )
    available_skills = resolved_target_skills
    skills_section = get_skills_prompt_section(available_skills)
    if skills_section:
        overrides["system_prompt"] = config.system_prompt + "\n\n" + skills_section

    if max_turns is not None:
        overrides["max_turns"] = max_turns

    if overrides:
        config = replace(config, **overrides)

    # Extract parent context from runtime
    sandbox_state = None
    thread_data = None
    thread_id = None
    parent_model = None
    trace_id = None

    if runtime is not None:
        sandbox_state = runtime.state.get("sandbox")
        thread_data = runtime.state.get("thread_data")
        thread_id = runtime.context.get("thread_id") if runtime.context else None

        # Try to get parent model from configurable
        metadata = runtime.config.get("metadata", {})
        parent_model = metadata.get("model_name")

        # Get or generate trace_id for distributed tracing
        trace_id = metadata.get("trace_id") or str(uuid.uuid4())[:8]

    # Get available tools (excluding task tool to prevent nesting)
    # Lazy import to avoid circular dependency
    from deerflow.tools import get_available_tools

    # Subagents should not have subagent tools enabled (prevent recursive nesting)
    tools = get_available_tools(model_name=parent_model, subagent_enabled=False)

    # Create executor
    executor = SubagentExecutor(
        config=config,
        tools=tools,
        parent_model=parent_model,
        sandbox_state=sandbox_state,
        thread_data=thread_data,
        thread_id=thread_id,
        trace_id=trace_id,
    )

    # Start background execution (always async to prevent blocking)
    # Use tool_call_id as task_id for better traceability
    task_id = executor.execute_async(prompt, task_id=tool_call_id)

    # Poll for task completion in backend (removes need for LLM to poll)
    poll_count = 0
    last_status = None
    last_message_count = 0  # Track how many AI messages we've already sent
    # Polling timeout: execution timeout + 60s buffer, checked every 5s
    max_poll_count = (config.timeout_seconds + 60) // 5

    logger.info(f"[trace={trace_id}] Started background task {task_id} (subagent={subagent_type}, timeout={config.timeout_seconds}s, polling_limit={max_poll_count} polls)")

    writer = get_stream_writer()
    # Send Task Started message'
    writer({"type": "task_started", "task_id": task_id, "description": description})

    while True:
        result = get_background_task_result(task_id)

        if result is None:
            logger.error(f"[trace={trace_id}] Task {task_id} not found in background tasks")
            writer({"type": "task_failed", "task_id": task_id, "error": "Task disappeared from background tasks"})
            cleanup_background_task(task_id)
            return f"Error: Task {task_id} disappeared from background tasks"

        # Log status changes for debugging
        if result.status != last_status:
            logger.info(f"[trace={trace_id}] Task {task_id} status: {result.status.value}")
            last_status = result.status

        # Check for new AI messages and send task_running events
        current_message_count = len(result.ai_messages)
        if current_message_count > last_message_count:
            # Send task_running event for each new message
            for i in range(last_message_count, current_message_count):
                message = result.ai_messages[i]
                writer(
                    {
                        "type": "task_running",
                        "task_id": task_id,
                        "message": message,
                        "message_index": i + 1,  # 1-based index for display
                        "total_messages": current_message_count,
                    }
                )
                logger.info(f"[trace={trace_id}] Task {task_id} sent message #{i + 1}/{current_message_count}")
            last_message_count = current_message_count

        # Check if task completed, failed, or timed out
        if result.status == SubagentStatus.COMPLETED:
            writer({"type": "task_completed", "task_id": task_id, "result": result.result})
            logger.info(f"[trace={trace_id}] Task {task_id} completed after {poll_count} polls")
            cleanup_background_task(task_id)
            return _build_terminal_response(
                runtime,
                subagent_type=subagent_type,
                description=description,
                tool_call_id=tool_call_id,
                target_skills=resolved_target_skills_list,
                terminal_status="completed",
                message=f"Task Succeeded. Result: {result.result}",
            )
        elif result.status == SubagentStatus.FAILED:
            writer({"type": "task_failed", "task_id": task_id, "error": result.error})
            logger.error(f"[trace={trace_id}] Task {task_id} failed: {result.error}")
            cleanup_background_task(task_id)
            return _build_terminal_response(
                runtime,
                subagent_type=subagent_type,
                description=description,
                tool_call_id=tool_call_id,
                target_skills=resolved_target_skills_list,
                terminal_status="failed",
                message=f"Task failed. Error: {result.error}",
            )
        elif result.status == SubagentStatus.TIMED_OUT:
            writer({"type": "task_timed_out", "task_id": task_id, "error": result.error})
            logger.warning(f"[trace={trace_id}] Task {task_id} timed out: {result.error}")
            cleanup_background_task(task_id)
            return _build_terminal_response(
                runtime,
                subagent_type=subagent_type,
                description=description,
                tool_call_id=tool_call_id,
                target_skills=resolved_target_skills_list,
                terminal_status="timed_out",
                message=f"Task timed out. Error: {result.error}",
            )

        # Still running, wait before next poll
        time.sleep(5)  # Poll every 5 seconds
        poll_count += 1

        # Polling timeout as a safety net (in case thread pool timeout doesn't work)
        # Set to execution timeout + 60s buffer, in 5s poll intervals
        # This catches edge cases where the background task gets stuck
        # Note: We don't call cleanup_background_task here because the task may
        # still be running in the background. The cleanup will happen when the
        # executor completes and sets a terminal status.
        if poll_count > max_poll_count:
            timeout_minutes = config.timeout_seconds // 60
            logger.error(f"[trace={trace_id}] Task {task_id} polling timed out after {poll_count} polls (should have been caught by thread pool timeout)")
            writer({"type": "task_timed_out", "task_id": task_id})
            return f"Task polling timed out after {timeout_minutes} minutes. This may indicate the background task is stuck. Status: {result.status.value}"
