"""Built-in DeerFlow tool for executing scientific remediation follow-up handoffs."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.typing import ContextT

from deerflow.agents.thread_state import ThreadState
from deerflow.agents.thread_state import merge_artifacts
from deerflow.domain.submarine.followup import (
    append_scientific_followup_history,
    resolve_scientific_followup_history_virtual_path,
)
from deerflow.domain.submarine.handoff import load_scientific_remediation_handoff
from deerflow.sandbox.tools import replace_virtual_path
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


def _with_unique_paths(*path_groups: object) -> list[str]:
    seen: set[str] = set()
    combined: list[str] = []
    for group in path_groups:
        if isinstance(group, str):
            items = [group]
        elif isinstance(group, list):
            items = [item for item in group if isinstance(item, str)]
        else:
            items = []
        for item in items:
            if not item or item in seen:
                continue
            seen.add(item)
            combined.append(item)
    return combined


def _augment_runtime_update(
    runtime_update: Mapping[str, object] | None,
    *,
    snapshot,
    history_virtual_path: str,
) -> dict[str, object]:
    if isinstance(runtime_update, Mapping):
        updated_runtime = dict(runtime_update)
    else:
        updated_runtime = snapshot.model_dump(mode="json")

    artifact_virtual_paths = merge_artifacts(
        updated_runtime.get("artifact_virtual_paths")
        if isinstance(updated_runtime.get("artifact_virtual_paths"), list)
        else [],
        [history_virtual_path],
    )
    updated_runtime["artifact_virtual_paths"] = artifact_virtual_paths
    updated_runtime["scientific_followup_history_virtual_path"] = history_virtual_path
    return updated_runtime


def _augment_command_update(
    command: Command,
    *,
    snapshot,
    history_virtual_path: str,
) -> dict[str, object]:
    update = command.update if isinstance(command.update, Mapping) else {}
    augmented_update = dict(update)
    augmented_update["submarine_runtime"] = _augment_runtime_update(
        update.get("submarine_runtime")
        if isinstance(update.get("submarine_runtime"), Mapping)
        else None,
        snapshot=snapshot,
        history_virtual_path=history_virtual_path,
    )
    augmented_update["artifacts"] = merge_artifacts(
        update.get("artifacts")
        if isinstance(update.get("artifacts"), list)
        else [],
        [history_virtual_path],
    )
    return augmented_update


def _resolve_history_artifact_path(runtime, history_virtual_path: str) -> Path:
    thread_data = (runtime.state or {}).get("thread_data")
    actual_path = replace_virtual_path(history_virtual_path, thread_data)
    return Path(actual_path).resolve()


def _record_followup_history(
    *,
    runtime,
    snapshot,
    source_handoff_virtual_path: str | None,
    handoff_status: str,
    recommended_action_id: str | None,
    tool_name: str | None,
    outcome_status: str,
    dispatch_stage_status: str | None = None,
    report_refreshed: bool = False,
    result_report_virtual_path: str | None = None,
    result_supervisor_handoff_virtual_path: str | None = None,
    artifact_virtual_paths: list[str] | None = None,
    notes: list[str] | None = None,
) -> str | None:
    history_virtual_path = resolve_scientific_followup_history_virtual_path(
        snapshot.scientific_followup_history_virtual_path,
        source_handoff_virtual_path,
        snapshot.report_virtual_path,
        result_report_virtual_path,
        result_supervisor_handoff_virtual_path,
    )
    if not history_virtual_path:
        return None

    append_scientific_followup_history(
        artifact_path=_resolve_history_artifact_path(runtime, history_virtual_path),
        artifact_virtual_path=history_virtual_path,
        entry={
            "source_handoff_virtual_path": source_handoff_virtual_path,
            "source_report_virtual_path": snapshot.report_virtual_path,
            "handoff_status": handoff_status,
            "recommended_action_id": recommended_action_id,
            "tool_name": tool_name,
            "outcome_status": outcome_status,
            "dispatch_stage_status": dispatch_stage_status,
            "report_refreshed": report_refreshed,
            "result_report_virtual_path": result_report_virtual_path,
            "result_supervisor_handoff_virtual_path": result_supervisor_handoff_virtual_path,
            "artifact_virtual_paths": _with_unique_paths(
                source_handoff_virtual_path,
                result_report_virtual_path,
                result_supervisor_handoff_virtual_path,
                artifact_virtual_paths or [],
            ),
            "notes": notes or [],
        },
    )
    return history_virtual_path


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
    snapshot = None
    outputs_dir = None
    resolved_handoff_virtual_path = handoff_virtual_path
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
        error_command = Command(
            update={"messages": [ToolMessage(f"Error: {exc}", tool_call_id=tool_call_id)]}
        )
        if snapshot is None or outputs_dir is None:
            return error_command
        history_virtual_path = _record_followup_history(
            runtime=runtime,
            snapshot=snapshot,
            source_handoff_virtual_path=resolved_handoff_virtual_path,
            handoff_status="error",
            recommended_action_id=None,
            tool_name=None,
            outcome_status="error",
            notes=[str(exc)],
        )
        if not history_virtual_path:
            return error_command
        return Command(
            update=_augment_command_update(
                error_command,
                snapshot=snapshot,
                history_virtual_path=history_virtual_path,
            )
        )

    handoff_status = str(handoff.get("handoff_status") or "unknown")
    recommended_action_id = str(handoff.get("recommended_action_id") or "none")
    reason = str(handoff.get("reason") or "No detail")
    tool_name = handoff.get("tool_name")

    if handoff_status != "ready_for_auto_followup":
        non_executing_command = Command(
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
        history_virtual_path = _record_followup_history(
            runtime=runtime,
            snapshot=snapshot,
            source_handoff_virtual_path=resolved_handoff_virtual_path,
            handoff_status=handoff_status,
            recommended_action_id=recommended_action_id,
            tool_name=tool_name if isinstance(tool_name, str) else None,
            outcome_status=handoff_status,
            artifact_virtual_paths=handoff.get("artifact_virtual_paths")
            if isinstance(handoff.get("artifact_virtual_paths"), list)
            else None,
            notes=[reason],
        )
        if not history_virtual_path:
            return non_executing_command
        return Command(
            update=_augment_command_update(
                non_executing_command,
                snapshot=snapshot,
                history_virtual_path=history_virtual_path,
            )
        )

    tool_args = handoff.get("tool_args") or {}
    if not isinstance(tool_args, Mapping):
        invalid_args_command = Command(
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
        history_virtual_path = _record_followup_history(
            runtime=runtime,
            snapshot=snapshot,
            source_handoff_virtual_path=resolved_handoff_virtual_path,
            handoff_status=handoff_status,
            recommended_action_id=recommended_action_id,
            tool_name=tool_name if isinstance(tool_name, str) else None,
            outcome_status="invalid_tool_args",
            notes=[reason],
        )
        if not history_virtual_path:
            return invalid_args_command
        return Command(
            update=_augment_command_update(
                invalid_args_command,
                snapshot=snapshot,
                history_virtual_path=history_virtual_path,
            )
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
        dispatch_stage_status = str(dispatch_runtime.get("stage_status") or "unknown")
        if dispatch_stage_status != "executed":
            history_virtual_path = _record_followup_history(
                runtime=runtime,
                snapshot=snapshot,
                source_handoff_virtual_path=resolved_handoff_virtual_path,
                handoff_status=handoff_status,
                recommended_action_id=recommended_action_id,
                tool_name=tool_name,
                outcome_status=f"dispatch_{dispatch_stage_status}",
                dispatch_stage_status=dispatch_stage_status,
                report_refreshed=False,
                result_report_virtual_path=(
                    str(dispatch_runtime.get("report_virtual_path"))
                    if dispatch_runtime.get("report_virtual_path")
                    else None
                ),
                result_supervisor_handoff_virtual_path=(
                    str(dispatch_runtime.get("supervisor_handoff_virtual_path"))
                    if dispatch_runtime.get("supervisor_handoff_virtual_path")
                    else None
                ),
                artifact_virtual_paths=(
                    dispatch_update.get("artifacts")
                    if isinstance(dispatch_update.get("artifacts"), list)
                    else None
                ),
                notes=[reason],
            )
            if not history_virtual_path:
                return dispatch_result
            return Command(
                update=_augment_command_update(
                    dispatch_result,
                    snapshot=snapshot,
                    history_virtual_path=history_virtual_path,
                )
            )
        chained_runtime = _build_chained_runtime(
            runtime,
            submarine_runtime=dispatch_runtime,
        )
        report_result = submarine_result_report_tool.func(
            runtime=chained_runtime,
            tool_call_id=tool_call_id,
        )
        report_update = report_result.update if isinstance(report_result.update, Mapping) else {}
        report_runtime = (
            report_update.get("submarine_runtime")
            if isinstance(report_update.get("submarine_runtime"), Mapping)
            else None
        )
        history_virtual_path = _record_followup_history(
            runtime=runtime,
            snapshot=snapshot,
            source_handoff_virtual_path=resolved_handoff_virtual_path,
            handoff_status=handoff_status,
            recommended_action_id=recommended_action_id,
            tool_name=tool_name,
            outcome_status="dispatch_refreshed_report",
            dispatch_stage_status=dispatch_stage_status,
            report_refreshed=True,
            result_report_virtual_path=(
                str(report_runtime.get("report_virtual_path"))
                if report_runtime and report_runtime.get("report_virtual_path")
                else None
            ),
            result_supervisor_handoff_virtual_path=(
                str(report_runtime.get("supervisor_handoff_virtual_path"))
                if report_runtime
                and report_runtime.get("supervisor_handoff_virtual_path")
                else None
            ),
            artifact_virtual_paths=_with_unique_paths(
                dispatch_update.get("artifacts")
                if isinstance(dispatch_update.get("artifacts"), list)
                else [],
                report_update.get("artifacts")
                if isinstance(report_update.get("artifacts"), list)
                else [],
            ),
            notes=[reason],
        )
        if not history_virtual_path:
            return report_result
        return Command(
            update=_augment_command_update(
                report_result,
                snapshot=snapshot,
                history_virtual_path=history_virtual_path,
            )
        )

    if tool_name == "submarine_result_report":
        report_result = submarine_result_report_tool.func(
            runtime=runtime,
            tool_call_id=tool_call_id,
            **dict(tool_args),
        )
        report_update = report_result.update if isinstance(report_result.update, Mapping) else {}
        report_runtime = (
            report_update.get("submarine_runtime")
            if isinstance(report_update.get("submarine_runtime"), Mapping)
            else None
        )
        history_virtual_path = _record_followup_history(
            runtime=runtime,
            snapshot=snapshot,
            source_handoff_virtual_path=resolved_handoff_virtual_path,
            handoff_status=handoff_status,
            recommended_action_id=recommended_action_id,
            tool_name=tool_name,
            outcome_status="result_report_refreshed",
            report_refreshed=True,
            result_report_virtual_path=(
                str(report_runtime.get("report_virtual_path"))
                if report_runtime and report_runtime.get("report_virtual_path")
                else None
            ),
            result_supervisor_handoff_virtual_path=(
                str(report_runtime.get("supervisor_handoff_virtual_path"))
                if report_runtime
                and report_runtime.get("supervisor_handoff_virtual_path")
                else None
            ),
            artifact_virtual_paths=(
                report_update.get("artifacts")
                if isinstance(report_update.get("artifacts"), list)
                else None
            ),
            notes=[reason],
        )
        if not history_virtual_path:
            return report_result
        return Command(
            update=_augment_command_update(
                report_result,
                snapshot=snapshot,
                history_virtual_path=history_virtual_path,
            )
        )

    unsupported_command = Command(
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
    history_virtual_path = _record_followup_history(
        runtime=runtime,
        snapshot=snapshot,
        source_handoff_virtual_path=resolved_handoff_virtual_path,
        handoff_status=handoff_status,
        recommended_action_id=recommended_action_id,
        tool_name=tool_name if isinstance(tool_name, str) else None,
        outcome_status="unsupported_target",
        artifact_virtual_paths=handoff.get("artifact_virtual_paths")
        if isinstance(handoff.get("artifact_virtual_paths"), list)
        else None,
        notes=[reason],
    )
    if not history_virtual_path:
        return unsupported_command
    return Command(
        update=_augment_command_update(
            unsupported_command,
            snapshot=snapshot,
            history_virtual_path=history_virtual_path,
        )
    )
