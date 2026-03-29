"""Built-in DeerFlow tool for executing scientific remediation follow-up handoffs."""

from __future__ import annotations

from typing import Annotated

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.typing import ContextT

from deerflow.agents.thread_state import ThreadState
from deerflow.domain.submarine.handoff import load_scientific_remediation_handoff
from deerflow.tools.builtins.submarine_result_report_tool import (
    _get_runtime_snapshot,
    _get_thread_dir,
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

    return Command(
        update={
            "messages": [
                ToolMessage(
                    (
                        "Scientific follow-up found an executable handoff, "
                        f"but supported delegation is not implemented yet. "
                        f"tool_name={tool_name}; "
                        f"recommended_action_id={recommended_action_id}; "
                        f"reason={reason}"
                    ),
                    tool_call_id=tool_call_id,
                )
            ]
        }
    )
