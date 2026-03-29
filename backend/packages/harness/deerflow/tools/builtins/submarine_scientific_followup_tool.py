"""Built-in DeerFlow tool for executing scientific remediation follow-up handoffs."""

from __future__ import annotations

from collections.abc import Mapping
from types import SimpleNamespace
from typing import Annotated

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.typing import ContextT

from deerflow.agents.thread_state import ThreadState
from deerflow.domain.submarine.handoff import load_scientific_remediation_handoff
from deerflow.tools.builtins.submarine_result_report_tool import (
    submarine_result_report_tool,
)
from deerflow.tools.builtins.submarine_result_report_tool import (
    _get_runtime_snapshot,
    _get_thread_dir,
)
from deerflow.tools.builtins.submarine_solver_dispatch_tool import (
    submarine_solver_dispatch_tool,
)


def _build_chained_runtime(
    runtime: ToolRuntime[ContextT, ThreadState],
    *,
    submarine_runtime: Mapping[str, object],
) -> SimpleNamespace:
    chained_state = dict(runtime.state or {})
    chained_state["submarine_runtime"] = dict(submarine_runtime)
    return SimpleNamespace(
        state=chained_state,
        context=runtime.context,
    )


@tool("submarine_scientific_followup", parse_docstring=True)
def submarine_scientific_followup_tool(
    runtime: ToolRuntime[ContextT, ThreadState],
    handoff_virtual_path: str | None = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Continue a submarine CFD run from the latest scientific remediation handoff.

    Args:
        handoff_virtual_path: Optional handoff artifact path. Defaults to the current runtime `supervisor_handoff_virtual_path`.
    """
    try:
        snapshot = _get_runtime_snapshot(runtime)
        outputs_dir = _get_thread_dir(runtime, "outputs_path")
        resolved_handoff_virtual_path = (
            handoff_virtual_path or snapshot.supervisor_handoff_virtual_path
        )
        if not resolved_handoff_virtual_path:
            raise ValueError(
                "Submarine runtime is missing supervisor_handoff_virtual_path for scientific follow-up"
            )
        handoff = load_scientific_remediation_handoff(
            outputs_dir=outputs_dir,
            artifact_virtual_path=resolved_handoff_virtual_path,
        )
    except ValueError as exc:
        return Command(
            update={"messages": [ToolMessage(f"Error: {exc}", tool_call_id=tool_call_id)]}
        )

    handoff_status = str(handoff.get("handoff_status") or "unknown")
    recommended_action_id = str(handoff.get("recommended_action_id") or "none")
    reason = str(handoff.get("reason") or "No detail")
    tool_name = handoff.get("tool_name")

    if handoff_status != "ready_for_auto_followup":
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        (
                            "Scientific follow-up did not execute. "
                            f"handoff_status={handoff_status}; "
                            f"recommended_action_id={recommended_action_id}; "
                            f"reason={reason}"
                        ),
                        tool_call_id=tool_call_id,
                    )
                ]
            }
        )

    tool_args = handoff.get("tool_args") or {}
    if not isinstance(tool_args, Mapping):
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        (
                            "Scientific follow-up could not execute because the handoff "
                            f"tool_args payload is invalid. tool_name={tool_name}; "
                            f"recommended_action_id={recommended_action_id}"
                        ),
                        tool_call_id=tool_call_id,
                    )
                ]
            }
        )

    if tool_name == "submarine_solver_dispatch":
        dispatch_args = dict(tool_args)
        dispatch_args["execute_now"] = True
        dispatch_result = submarine_solver_dispatch_tool.func(
            runtime=runtime,
            tool_call_id=tool_call_id,
            **dispatch_args,
        )
        dispatch_update = (
            dispatch_result.update
            if isinstance(dispatch_result.update, Mapping)
            else {}
        )
        dispatch_runtime = dispatch_update.get("submarine_runtime")
        if not isinstance(dispatch_runtime, Mapping):
            return dispatch_result
        if str(dispatch_runtime.get("stage_status") or "") != "executed":
            return dispatch_result
        chained_runtime = _build_chained_runtime(
            runtime,
            submarine_runtime=dispatch_runtime,
        )
        return submarine_result_report_tool.func(
            runtime=chained_runtime,
            tool_call_id=tool_call_id,
        )

    if tool_name == "submarine_result_report":
        return submarine_result_report_tool.func(
            runtime=runtime,
            tool_call_id=tool_call_id,
            **dict(tool_args),
        )

    return Command(
        update={
            "messages": [
                ToolMessage(
                    (
                        "Scientific follow-up found an executable handoff, "
                        f"but the tool target is not supported yet. "
                        f"tool_name={tool_name}; "
                        f"recommended_action_id={recommended_action_id}; "
                        f"reason={reason}"
                    ),
                    tool_call_id=tool_call_id,
                )
            ]
        }
    )
