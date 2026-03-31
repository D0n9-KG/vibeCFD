"""Built-in DeerFlow tool for submarine solver dispatch."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

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
from deerflow.domain.submarine.geometry_check import SUPPORTED_GEOMETRY_SUFFIXES
from deerflow.domain.submarine.runtime_plan import (
    build_scientific_capability_updates_for_dispatch,
)
from deerflow.domain.submarine.solver_dispatch import run_solver_dispatch
from deerflow.sandbox import get_sandbox_provider


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


def _resolve_geometry_path(
    runtime: ToolRuntime[ContextT, ThreadState],
    geometry_path: str | None,
) -> Path:
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
                raise ValueError(
                    "Geometry path must stay inside the current thread user-data directory",
                ) from exc
    else:
        candidates = sorted(
            (
                candidate
                for candidate in uploads_dir.iterdir()
                if candidate.is_file()
                and candidate.suffix.lower() in SUPPORTED_GEOMETRY_SUFFIXES
            ),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            raise ValueError(
                "No .stl geometry file was found in the current thread uploads directory",
            )
        resolved = candidates[0]

    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"Geometry file not found: {geometry_path or resolved}")

    if resolved.suffix.lower() not in SUPPORTED_GEOMETRY_SUFFIXES:
        raise ValueError(
            f"Only STL (.stl) geometry files are supported in v1; received {resolved.suffix}",
        )

    return resolved


def _to_virtual_thread_path(
    runtime: ToolRuntime[ContextT, ThreadState],
    actual_path: Path,
) -> str:
    uploads_dir = _get_thread_dir(runtime, "uploads_path")
    user_data_dir = uploads_dir.parent.resolve()
    relative = actual_path.resolve().relative_to(user_data_dir)
    return f"{VIRTUAL_PATH_PREFIX}/{relative.as_posix()}"


def _get_execute_command(runtime: ToolRuntime[ContextT, ThreadState]):
    sandbox_state = (runtime.state or {}).get("sandbox") or {}
    sandbox_id = sandbox_state.get("sandbox_id")
    if not sandbox_id:
        return None

    sandbox = get_sandbox_provider().get(sandbox_id)
    if sandbox is None:
        return None
    return sandbox.execute_command


def _requires_user_confirmation(existing_runtime: dict) -> bool:
    return (
        existing_runtime.get("review_status") == "needs_user_confirmation"
        or existing_runtime.get("next_recommended_stage") == "user-confirmation"
    )


def _build_user_confirmation_block_message(existing_runtime: dict) -> str:
    task_summary = existing_runtime.get("task_summary") or "the current submarine CFD brief"
    return (
        "Solver dispatch is blocked until user confirmation is complete for the current design brief. "
        f"Please resolve the missing operating-condition questions for {task_summary} in chat, "
        "update the design brief, and then retry submarine_solver_dispatch."
    )


@tool("submarine_solver_dispatch", parse_docstring=True)
def submarine_solver_dispatch_tool(
    runtime: ToolRuntime[ContextT, ThreadState],
    geometry_path: str | None,
    task_description: str,
    task_type: str = "resistance",
    geometry_family_hint: str | None = None,
    selected_case_id: str | None = None,
    inlet_velocity_mps: float | None = None,
    fluid_density_kg_m3: float | None = None,
    kinematic_viscosity_m2ps: float | None = None,
    end_time_seconds: float | None = None,
    delta_t_seconds: float | None = None,
    write_interval_steps: int | None = None,
    execute_now: bool = False,
    execute_scientific_studies: bool = False,
    solver_command: str | None = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Prepare or execute a controlled OpenFOAM-style solver dispatch for a submarine task.

    Args:
        geometry_path: Optional geometry file path. Prefer `/mnt/user-data/uploads/...`. When omitted, use the runtime-bound path or latest uploaded `.stl`.
        task_description: Task goal in natural language, for example `为这个潜艇几何准备 OpenFOAM 阻力分析`.
        task_type: CFD task type such as `resistance`, `pressure_distribution`, or `wake_field`.
        geometry_family_hint: Optional family hint such as `DARPA SUBOFF` or `Type 209`.
        selected_case_id: Optional case ID to force the selected template.
        inlet_velocity_mps: Optional inlet velocity for the CFD case.
        fluid_density_kg_m3: Optional fluid density for the CFD case.
        kinematic_viscosity_m2ps: Optional kinematic viscosity for the CFD case.
        end_time_seconds: Optional solver end time.
        delta_t_seconds: Optional solver deltaT.
        write_interval_steps: Optional write interval in time steps.
        execute_now: Whether to execute the dispatch command immediately inside the current DeerFlow sandbox.
        execute_scientific_studies: Whether to execute the planned scientific study variants in addition to the baseline run.
        solver_command: Optional command to run when `execute_now=true`, for example `simpleFoam -case /mnt/user-data/workspace/case`.
    """
    try:
        existing_runtime = (runtime.state or {}).get("submarine_runtime") or {}
        if _requires_user_confirmation(existing_runtime):
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            _build_user_confirmation_block_message(existing_runtime),
                            tool_call_id=tool_call_id,
                        )
                    ]
                }
            )
        existing_requirements = existing_runtime.get("simulation_requirements") or {}
        resolved_task_description = (
            task_description
            or existing_runtime.get("task_summary")
            or "生成潜艇求解派发方案"
        )
        resolved_task_type = task_type or existing_runtime.get("task_type") or "resistance"
        resolved_geometry_family_hint = (
            geometry_family_hint
            if geometry_family_hint is not None
            else existing_runtime.get("geometry_family")
        )
        resolved_selected_case_id = (
            selected_case_id
            if selected_case_id is not None
            else existing_runtime.get("selected_case_id")
        )
        resolved_geometry_input = (
            geometry_path or existing_runtime.get("geometry_virtual_path")
        )
        resolved_geometry_path = _resolve_geometry_path(runtime, resolved_geometry_input)
        outputs_dir = _get_thread_dir(runtime, "outputs_path")
        workspace_dir = _get_thread_dir(runtime, "workspace_path")
        geometry_virtual_path = _to_virtual_thread_path(runtime, resolved_geometry_path)
        execute_command = _get_execute_command(runtime) if execute_now else None
        payload, artifacts = run_solver_dispatch(
            geometry_path=resolved_geometry_path,
            outputs_dir=outputs_dir,
            workspace_dir=workspace_dir,
            task_description=resolved_task_description,
            task_type=resolved_task_type,
            geometry_family_hint=resolved_geometry_family_hint,
            selected_case_id=resolved_selected_case_id,
            geometry_virtual_path=geometry_virtual_path,
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
            requested_outputs=existing_runtime.get("requested_outputs"),
            solver_command=solver_command,
            execute_now=execute_now,
            execute_scientific_studies=execute_scientific_studies,
            execute_command=execute_command,
        )
    except ValueError as exc:
        return Command(
            update={"messages": [ToolMessage(f"Error: {exc}", tool_call_id=tool_call_id)]},
        )

    selected_case = payload.get("selected_case") or {}
    dispatch_status = payload.get("dispatch_status")
    execution_updates: dict[str, str] = {
        "claude-code-supervisor": "completed",
        "task-intelligence": "completed",
        "geometry-preflight": "completed",
    }
    if dispatch_status == "executed":
        execution_updates["solver-dispatch"] = "completed"
        execution_updates["result-reporting"] = "ready"
    elif dispatch_status == "failed":
        execution_updates["solver-dispatch"] = "blocked"
        execution_updates["result-reporting"] = "pending"
    else:
        execution_updates["solver-dispatch"] = "in_progress"
        execution_updates["result-reporting"] = "pending"
    execution_updates.update(
        build_scientific_capability_updates_for_dispatch(payload)
    )

    runtime_snapshot = build_runtime_snapshot(
        current_stage="solver-dispatch",
        task_summary=resolved_task_description,
        task_type=resolved_task_type,
        geometry_virtual_path=geometry_virtual_path,
        geometry_family=(payload.get("geometry") or {}).get("geometry_family"),
        execution_readiness=payload.get("execution_readiness"),
        selected_case_id=selected_case.get("case_id"),
        simulation_requirements=payload.get("simulation_requirements"),
        requested_outputs=payload.get("requested_outputs"),
        output_delivery_plan=payload.get("output_delivery_plan"),
        stage_status=dispatch_status,
        workspace_case_dir_virtual_path=payload.get("workspace_case_dir_virtual_path"),
        run_script_virtual_path=payload.get("run_script_virtual_path"),
        supervisor_handoff_virtual_path=payload.get("supervisor_handoff_virtual_path"),
        next_recommended_stage=payload["next_recommended_stage"],
        report_virtual_path=payload["report_virtual_path"],
        artifact_virtual_paths=payload["artifact_virtual_paths"],
        execution_plan=build_execution_plan(
            confirmation_status="confirmed",
            existing_plan=existing_runtime.get("execution_plan"),
            stage_updates=execution_updates,
        ),
        review_status=payload["review_status"],
        activity_timeline=extend_runtime_timeline(
            existing_runtime,
            build_runtime_event(
                stage="solver-dispatch",
                actor="solver-dispatch",
                title="更新 OpenFOAM 求解派发",
                summary=payload["summary_zh"],
                status=dispatch_status,
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
        },
    )
