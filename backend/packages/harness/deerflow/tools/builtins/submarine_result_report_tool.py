"""Built-in DeerFlow tool for submarine result reporting."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.typing import ContextT

from deerflow.agents.thread_state import ThreadState
from deerflow.domain.submarine.contracts import (
    SubmarineRuntimeSnapshot,
    build_execution_plan,
    build_runtime_event,
    build_runtime_snapshot,
    extend_runtime_timeline,
)
from deerflow.domain.submarine.reporting import run_result_report
from deerflow.domain.submarine.runtime_plan import (
    build_scientific_capability_updates_for_report,
)


def _get_thread_dir(runtime: ToolRuntime[ContextT, ThreadState], key: str) -> Path:
    thread_data = (runtime.state or {}).get("thread_data") or {}
    raw_path = thread_data.get(key)
    if not raw_path:
        raise ValueError(f"Thread data missing required path: {key}")
    return Path(raw_path).resolve()


def _get_runtime_snapshot(runtime: ToolRuntime[ContextT, ThreadState]) -> SubmarineRuntimeSnapshot:
    submarine_runtime = (runtime.state or {}).get("submarine_runtime")
    if not submarine_runtime:
        raise ValueError("Submarine runtime state is not available in the current thread")
    return SubmarineRuntimeSnapshot.model_validate(submarine_runtime)


@tool("submarine_result_report", parse_docstring=True)
def submarine_result_report_tool(
    runtime: ToolRuntime[ContextT, ThreadState],
    report_title: str | None = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Generate a traceable Chinese submarine run report from thread runtime state.

    Args:
        report_title: Optional report title. Defaults to `潜艇 CFD 阶段报告`.
    """
    try:
        snapshot = _get_runtime_snapshot(runtime)
        outputs_dir = _get_thread_dir(runtime, "outputs_path")
        payload, artifacts = run_result_report(
            snapshot=snapshot,
            outputs_dir=outputs_dir,
            report_title=report_title,
        )
    except ValueError as exc:
        return Command(update={"messages": [ToolMessage(f"Error: {exc}", tool_call_id=tool_call_id)]})

    scientific_followup_summary = payload.get("scientific_followup_summary") or {}
    scientific_gate = payload.get("scientific_supervisor_gate") or {}
    runtime_blocker_detail = None
    blocking_reasons = scientific_gate.get("blocking_reasons") or []
    if isinstance(blocking_reasons, list):
        normalized_reasons = [
            reason.strip()
            for reason in blocking_reasons
            if isinstance(reason, str) and reason.strip()
        ]
        if normalized_reasons:
            runtime_blocker_detail = "；".join(normalized_reasons)
    execution_updates = {
        "claude-code-supervisor": "completed",
        "task-intelligence": "completed",
        "geometry-preflight": "completed",
        "solver-dispatch": "completed",
        "result-reporting": "completed",
        "supervisor-review": (
            "blocked" if payload["review_status"] == "blocked" else "ready"
        ),
    }
    execution_updates.update(
        build_scientific_capability_updates_for_report(payload)
    )
    runtime_snapshot = build_runtime_snapshot(
        current_stage="result-reporting",
        task_summary=snapshot.task_summary,
        confirmation_status=snapshot.confirmation_status,
        execution_preference=snapshot.execution_preference,
        task_type=snapshot.task_type,
        geometry_virtual_path=snapshot.geometry_virtual_path,
        geometry_family=snapshot.geometry_family,
        execution_readiness=snapshot.execution_readiness,
        selected_case_id=snapshot.selected_case_id,
        simulation_requirements=snapshot.simulation_requirements,
        requested_outputs=payload.get("requested_outputs", snapshot.requested_outputs),
        output_delivery_plan=payload.get("output_delivery_plan"),
        stage_status=snapshot.stage_status,
        runtime_summary=payload["summary_zh"],
        blocker_detail=runtime_blocker_detail,
        workspace_case_dir_virtual_path=snapshot.workspace_case_dir_virtual_path,
        run_script_virtual_path=snapshot.run_script_virtual_path,
        request_virtual_path=snapshot.request_virtual_path,
        provenance_manifest_virtual_path=payload.get("provenance_manifest_virtual_path")
        or snapshot.provenance_manifest_virtual_path,
        execution_log_virtual_path=snapshot.execution_log_virtual_path,
        solver_results_virtual_path=snapshot.solver_results_virtual_path,
        stability_evidence_virtual_path=payload.get("stability_evidence_virtual_path"),
        stability_evidence=payload.get("stability_evidence"),
        provenance_summary=payload.get("provenance_summary"),
        environment_fingerprint=payload.get("environment_fingerprint")
        or snapshot.environment_fingerprint,
        supervisor_handoff_virtual_path=payload.get("supervisor_handoff_virtual_path"),
        scientific_followup_history_virtual_path=(
            scientific_followup_summary.get("history_virtual_path")
            or snapshot.scientific_followup_history_virtual_path
        ),
        next_recommended_stage=payload["next_recommended_stage"],
        report_virtual_path=payload["report_virtual_path"],
        artifact_virtual_paths=payload["artifact_virtual_paths"],
        execution_plan=build_execution_plan(
            confirmation_status=snapshot.confirmation_status,
            existing_plan=snapshot.execution_plan,
            stage_updates=execution_updates,
        ),
        review_status=payload["review_status"],
        scientific_verification_assessment=payload.get(
            "scientific_verification_assessment"
        ),
        scientific_gate_status=scientific_gate.get(
            "gate_status"
        ),
        allowed_claim_level=scientific_gate.get(
            "allowed_claim_level"
        ),
        scientific_gate_virtual_path=payload.get("scientific_gate_virtual_path"),
        activity_timeline=extend_runtime_timeline(
            snapshot,
            build_runtime_event(
                stage="result-reporting",
                actor="result-reporting",
                title="生成中文结果报告",
                summary=payload["summary_zh"],
                status=payload["review_status"],
            ),
        ),
    )
    detail_lines = "\n".join(f"- {artifact}" for artifact in artifacts)
    message = (
        f"{payload['summary_zh']}\n"
        f"已登记 {len(artifacts)} 个 DeerFlow artifacts，可在工作区直接查看：\n{detail_lines}"
    )
    return Command(
        update={
            "artifacts": artifacts,
            "submarine_runtime": runtime_snapshot.model_dump(mode="json"),
            "messages": [ToolMessage(message, tool_call_id=tool_call_id)],
        }
    )
