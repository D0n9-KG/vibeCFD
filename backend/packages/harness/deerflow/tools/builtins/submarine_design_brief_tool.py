"""Built-in DeerFlow tool for submarine CFD design brief drafting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.typing import ContextT

from deerflow.agents.thread_state import ThreadState
from deerflow.config.paths import VIRTUAL_PATH_PREFIX, get_paths
from deerflow.domain.submarine.contracts import (
    build_execution_plan,
    build_runtime_event,
    build_runtime_snapshot,
    extend_runtime_timeline,
)
from deerflow.domain.submarine.design_brief import run_design_brief
from deerflow.domain.submarine.geometry_check import SUPPORTED_GEOMETRY_SUFFIXES
from deerflow.tools.builtins.submarine_runtime_context import (
    load_existing_design_brief_payload,
    resolve_execution_preference,
)


def _get_thread_id(runtime: ToolRuntime[ContextT, ThreadState]) -> str:
    thread_id = runtime.context.get("thread_id") if runtime.context else None
    if not thread_id:
        raise ValueError("Thread ID is not available in runtime context")
    return thread_id


def _get_thread_dir(runtime: ToolRuntime[ContextT, ThreadState], key: str) -> Path:
    thread_data = (runtime.state or {}).get("thread_data") or {}
    raw_path = thread_data.get(key)
    if not raw_path:
        raise ValueError(f"Thread data missing required path: {key}")
    return Path(raw_path).resolve()


def _resolve_geometry_path(runtime: ToolRuntime[ContextT, ThreadState], geometry_path: str | None) -> Path | None:
    thread_id = _get_thread_id(runtime)
    uploads_dir = _get_thread_dir(runtime, "uploads_path")
    user_data_dir = uploads_dir.parent

    if geometry_path:
        stripped = geometry_path.lstrip("/")
        virtual_prefix = VIRTUAL_PATH_PREFIX.lstrip("/")
        if stripped == virtual_prefix or stripped.startswith(virtual_prefix + "/"):
            resolved = get_paths().resolve_virtual_path(thread_id, geometry_path)
        else:
            resolved = Path(geometry_path).expanduser().resolve()
            try:
                resolved.relative_to(user_data_dir)
            except ValueError as exc:
                raise ValueError("Geometry path must stay inside the current thread user-data directory") from exc
    else:
        candidates = sorted(
            (
                candidate
                for candidate in uploads_dir.iterdir()
                if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_GEOMETRY_SUFFIXES
            ),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            return None
        resolved = candidates[0]

    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"Geometry file not found: {geometry_path or resolved}")
    if resolved.suffix.lower() not in SUPPORTED_GEOMETRY_SUFFIXES:
        raise ValueError(f"Unsupported geometry format: {resolved.suffix}")
    return resolved


def _to_virtual_thread_path(runtime: ToolRuntime[ContextT, ThreadState], actual_path: Path) -> str:
    uploads_dir = _get_thread_dir(runtime, "uploads_path")
    user_data_dir = uploads_dir.parent.resolve()
    relative = actual_path.resolve().relative_to(user_data_dir)
    return f"{VIRTUAL_PATH_PREFIX}/{relative.as_posix()}"


@tool("submarine_design_brief", parse_docstring=True)
def submarine_design_brief_tool(
    runtime: ToolRuntime[ContextT, ThreadState],
    task_description: str | None = None,
    geometry_path: str | None = None,
    task_type: str | None = "resistance",
    confirmation_status: Literal["draft", "confirmed"] | None = "draft",
    execution_preference: Literal[
        "plan_only",
        "execute_now",
        "preflight_then_execute",
    ]
    | None = None,
    geometry_family_hint: str | None = None,
    selected_case_id: str | None = None,
    inlet_velocity_mps: float | None = None,
    fluid_density_kg_m3: float | None = None,
    kinematic_viscosity_m2ps: float | None = None,
    end_time_seconds: float | None = None,
    delta_t_seconds: float | None = None,
    write_interval_steps: int | None = None,
    expected_outputs: list[str] | None = None,
    user_constraints: list[str] | None = None,
    open_questions: list[str] | None = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Capture the evolving submarine CFD design brief as DeerFlow artifacts.

    Use this tool when Claude Code has discussed the task with the user and
    needs to turn the current understanding into a structured CFD design brief
    that DeerFlow subagents can follow and continue updating.

    Args:
        task_description: Natural-language task goal agreed with the user. When omitted, reuse the last saved design brief description.
        geometry_path: Optional geometry path. Prefer `/mnt/user-data/uploads/...`. When omitted, the latest uploaded geometry is used if present.
        task_type: CFD task type such as `resistance`, `pressure_distribution`, or `wake_field`. When omitted, reuse the last saved value.
        confirmation_status: Whether the current brief is still a draft or already confirmed with the user. When omitted, reuse the last saved value.
        geometry_family_hint: Optional family hint such as `DARPA SUBOFF` or `Type 209`.
        selected_case_id: Optional recommended baseline case ID.
        inlet_velocity_mps: Optional inlet velocity captured from the conversation.
        fluid_density_kg_m3: Optional fluid density captured from the conversation.
        kinematic_viscosity_m2ps: Optional kinematic viscosity captured from the conversation.
        end_time_seconds: Optional planned end time for the first CFD run.
        delta_t_seconds: Optional planned time-step size.
        write_interval_steps: Optional planned write interval.
        expected_outputs: Optional list of requested deliverables.
        user_constraints: Optional list of constraints or preferences explicitly provided by the user.
        open_questions: Optional list of unresolved questions Claude Code still needs to confirm.
    """
    try:
        outputs_dir = _get_thread_dir(runtime, "outputs_path")
        existing_payload = load_existing_design_brief_payload(
            outputs_dir=outputs_dir,
            state=runtime.state,
        )
        existing_requirements = existing_payload.get("simulation_requirements") or {}

        resolved_task_description = task_description or existing_payload.get("task_description")
        if not resolved_task_description:
            raise ValueError("task_description is required for the first design brief revision")

        resolved_task_type = task_type or existing_payload.get("task_type") or "resistance"
        resolved_confirmation_status = (
            confirmation_status
            or existing_payload.get("confirmation_status")
            or "draft"
        )
        resolved_geometry_family_hint = (
            geometry_family_hint
            if geometry_family_hint is not None
            else existing_payload.get("geometry_family_hint")
        )
        resolved_selected_case_id = (
            selected_case_id
            if selected_case_id is not None
            else existing_payload.get("selected_case_id")
        )
        resolved_geometry_input = geometry_path or existing_payload.get("geometry_virtual_path")
        resolved_geometry_path = _resolve_geometry_path(runtime, resolved_geometry_input)
        geometry_virtual_path = (
            _to_virtual_thread_path(runtime, resolved_geometry_path) if resolved_geometry_path is not None else None
        )
        resolved_execution_preference = resolve_execution_preference(
            explicit_preference=execution_preference,
            existing_runtime=(runtime.state or {}).get("submarine_runtime"),
            existing_brief=existing_payload,
            task_description=resolved_task_description,
        )
        payload, artifacts = run_design_brief(
            outputs_dir=outputs_dir,
            task_description=resolved_task_description,
            task_type=resolved_task_type,
            confirmation_status=resolved_confirmation_status,
            execution_preference=resolved_execution_preference,
            geometry_virtual_path=geometry_virtual_path,
            geometry_family_hint=resolved_geometry_family_hint,
            selected_case_id=resolved_selected_case_id,
            inlet_velocity_mps=(
                inlet_velocity_mps
                if inlet_velocity_mps is not None
                else existing_requirements.get("inlet_velocity_mps")
            ),
            fluid_density_kg_m3=(
                fluid_density_kg_m3
                if fluid_density_kg_m3 is not None
                else existing_requirements.get("fluid_density_kg_m3")
            ),
            kinematic_viscosity_m2ps=(
                kinematic_viscosity_m2ps
                if kinematic_viscosity_m2ps is not None
                else existing_requirements.get("kinematic_viscosity_m2ps")
            ),
            end_time_seconds=(
                end_time_seconds
                if end_time_seconds is not None
                else existing_requirements.get("end_time_seconds")
            ),
            delta_t_seconds=(
                delta_t_seconds
                if delta_t_seconds is not None
                else existing_requirements.get("delta_t_seconds")
            ),
            write_interval_steps=(
                write_interval_steps
                if write_interval_steps is not None
                else existing_requirements.get("write_interval_steps")
            ),
            expected_outputs=(
                expected_outputs
                if expected_outputs is not None
                else existing_payload.get("expected_outputs")
            ),
            user_constraints=(
                user_constraints
                if user_constraints is not None
                else existing_payload.get("user_constraints")
            ),
            open_questions=(
                open_questions
                if open_questions is not None
                else existing_payload.get("open_questions")
            ),
        )
    except ValueError as exc:
        return Command(update={"messages": [ToolMessage(f"Error: {exc}", tool_call_id=tool_call_id)]})

    existing_runtime = (runtime.state or {}).get("submarine_runtime")
    timeline = extend_runtime_timeline(
        existing_runtime,
        build_runtime_event(
            stage="task-intelligence",
            actor="claude-code-supervisor",
            title="更新 CFD 设计简报",
            summary=payload["summary_zh"],
            status=payload["confirmation_status"],
        ),
    )
    runtime_snapshot = build_runtime_snapshot(
        current_stage="task-intelligence",
        task_summary=payload["task_description"],
        confirmation_status=payload["confirmation_status"],
        execution_preference=payload["execution_preference"],
        task_type=payload["task_type"],
        geometry_virtual_path=payload.get("geometry_virtual_path") or "",
        geometry_family=payload.get("geometry_family_hint"),
        selected_case_id=payload.get("selected_case_id"),
        simulation_requirements=payload.get("simulation_requirements"),
        requested_outputs=payload.get("requested_outputs"),
        stage_status=payload.get("confirmation_status"),
        next_recommended_stage=payload["next_recommended_stage"],
        report_virtual_path=payload["report_virtual_path"],
        artifact_virtual_paths=payload["artifact_virtual_paths"],
        execution_plan=build_execution_plan(
            confirmation_status=payload["confirmation_status"],
            existing_plan=payload["execution_outline"],
        ),
        review_status=payload["review_status"],
        activity_timeline=timeline,
    )
    detail_lines = "\n".join(f"- {artifact}" for artifact in artifacts)
    message = (
        f"{payload['summary_zh']}\n"
        f"已更新 {len(artifacts)} 个设计简报 artifacts，可在工作区中持续审阅和迭代：\n{detail_lines}"
    )
    return Command(
        update={
            "artifacts": artifacts,
            "submarine_runtime": runtime_snapshot.model_dump(mode='json'),
            "messages": [ToolMessage(message, tool_call_id=tool_call_id)],
        }
    )
