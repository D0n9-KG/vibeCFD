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
    build_runtime_status_payload,
    build_scientific_capability_updates_for_dispatch,
)
from deerflow.domain.submarine.solver_dispatch import run_solver_dispatch
from deerflow.sandbox import get_sandbox_provider
from deerflow.tools.builtins.submarine_runtime_context import (
    build_user_confirmation_block_message,
    load_existing_design_brief_payload,
    requires_user_confirmation,
    resolve_bound_geometry_virtual_path,
    resolve_confirmation_status,
    resolve_execution_preference,
    resolve_task_summary,
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
        if not uploads_dir.exists():
            raise ValueError(
                "No .stl geometry file was found in the current thread uploads directory",
            )
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
    execute_now: bool | None = None,
    execute_scientific_studies: bool = False,
    custom_variants: list[dict] | None = None,
    solver_command: str | None = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Prepare or execute a controlled OpenFOAM-style solver dispatch for a submarine task.

    Args:
        geometry_path: Optional geometry file path. Prefer `/mnt/user-data/uploads/...`. When omitted, use the runtime-bound path or latest uploaded `.stl`.
        task_description: Task goal in natural language.
        task_type: CFD task type such as `resistance`, `pressure_distribution`, or `wake_field`.
        geometry_family_hint: Optional family hint such as `DARPA SUBOFF` or `Type 209`.
        selected_case_id: Optional case ID to force the selected template.
        inlet_velocity_mps: Optional inlet velocity for the CFD case.
        fluid_density_kg_m3: Optional fluid density for the CFD case.
        kinematic_viscosity_m2ps: Optional kinematic viscosity for the CFD case.
        end_time_seconds: Optional solver end time.
        delta_t_seconds: Optional solver deltaT.
        write_interval_steps: Optional write interval in time steps.
        execute_now: Whether to execute the dispatch command immediately inside the current DeerFlow sandbox. When omitted, recover the latest confirmed execution intent from the design brief.
        execute_scientific_studies: Whether to execute the planned scientific study variants in addition to the baseline run.
        custom_variants: Optional custom experiment variants to register in the experiment manifest alongside the baseline and scientific-study variants.
        solver_command: Optional command to run when `execute_now=true`, for example `simpleFoam -case /mnt/user-data/workspace/case`.
    """
    try:
        existing_runtime = (runtime.state or {}).get("submarine_runtime") or {}
        outputs_dir = _get_thread_dir(runtime, "outputs_path")
        uploads_dir = _get_thread_dir(runtime, "uploads_path")
        existing_brief = load_existing_design_brief_payload(
            outputs_dir=outputs_dir,
            state=runtime.state,
        )
        if requires_user_confirmation(
            existing_runtime=existing_runtime,
            existing_brief=existing_brief,
            target_stage="solver-dispatch",
        ):
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            build_user_confirmation_block_message(
                                existing_runtime=existing_runtime,
                                existing_brief=existing_brief,
                                blocked_stage_label="Solver dispatch",
                                retry_tool_name="submarine_solver_dispatch",
                            ),
                            tool_call_id=tool_call_id,
                        )
                    ]
                }
            )

        existing_requirements = (
            existing_runtime.get("simulation_requirements")
            or existing_brief.get("simulation_requirements")
            or {}
        )
        resolved_task_description = resolve_task_summary(
            explicit_task_description=task_description,
            existing_runtime=existing_runtime,
            existing_brief=existing_brief,
            fallback_task_description="Prepare a submarine solver dispatch plan",
        )
        resolved_task_type = (
            task_type
            or existing_runtime.get("task_type")
            or existing_brief.get("task_type")
            or "resistance"
        )
        resolved_geometry_family_hint = (
            geometry_family_hint
            if geometry_family_hint is not None
            else existing_runtime.get("geometry_family")
            or existing_brief.get("geometry_family_hint")
        )
        resolved_selected_case_id = (
            selected_case_id
            if selected_case_id is not None
            else existing_runtime.get("selected_case_id")
            or existing_brief.get("selected_case_id")
        )
        resolved_geometry_input = resolve_bound_geometry_virtual_path(
            thread_id=_get_thread_id(runtime),
            uploads_dir=uploads_dir,
            explicit_geometry_path=geometry_path,
            existing_runtime=existing_runtime,
            existing_brief=existing_brief,
            uploaded_files=(runtime.state or {}).get("uploaded_files"),
        )
        resolved_geometry_path = _resolve_geometry_path(runtime, resolved_geometry_input)
        workspace_dir = _get_thread_dir(runtime, "workspace_path")
        geometry_virtual_path = _to_virtual_thread_path(runtime, resolved_geometry_path)
        resolved_confirmation_status = resolve_confirmation_status(
            existing_runtime=existing_runtime,
            existing_brief=existing_brief,
        )
        resolved_execution_preference = resolve_execution_preference(
            explicit_preference=None,
            existing_runtime=existing_runtime,
            existing_brief=existing_brief,
            task_description=resolved_task_description,
        )
        resolved_execute_now = execute_now
        if resolved_execute_now is None:
            resolved_execute_now = (
                execute_scientific_studies
                or (
                    resolved_confirmation_status == "confirmed"
                    and resolved_execution_preference == "execute_now"
                )
            )
        execute_command = _get_execute_command(runtime) if resolved_execute_now else None
        payload, artifacts = run_solver_dispatch(
            geometry_path=resolved_geometry_path,
            outputs_dir=outputs_dir,
            workspace_dir=workspace_dir,
            task_description=resolved_task_description,
            task_type=resolved_task_type,
            confirmation_status=resolved_confirmation_status,
            execution_preference=resolved_execution_preference,
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
            requested_outputs=(
                existing_runtime.get("requested_outputs")
                or existing_brief.get("requested_outputs")
            ),
            custom_variants=(
                custom_variants
                if custom_variants is not None
                else existing_runtime.get("custom_variants")
                or existing_brief.get("custom_variants")
            ),
            geometry_findings=(
                existing_runtime.get("geometry_findings")
                or existing_brief.get("geometry_findings")
            ),
            scale_assessment=(
                existing_runtime.get("scale_assessment")
                or existing_brief.get("scale_assessment")
            ),
            reference_value_suggestions=(
                existing_runtime.get("reference_value_suggestions")
                or existing_brief.get("reference_value_suggestions")
            ),
            clarification_required=bool(
                existing_runtime.get("clarification_required")
                or existing_brief.get("clarification_required")
            ),
            calculation_plan=(
                existing_runtime.get("calculation_plan")
                or existing_brief.get("calculation_plan")
            ),
            requires_immediate_confirmation=bool(
                existing_runtime.get("requires_immediate_confirmation")
                or existing_brief.get("requires_immediate_confirmation")
            ),
            solver_command=solver_command,
            execute_now=resolved_execute_now,
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
    elif payload.get("review_status") == "needs_user_confirmation":
        execution_updates["solver-dispatch"] = "pending"
        execution_updates["result-reporting"] = "pending"
    else:
        execution_updates["solver-dispatch"] = "in_progress"
        execution_updates["result-reporting"] = "pending"
    execution_updates.update(build_scientific_capability_updates_for_dispatch(payload))
    runtime_truth = build_runtime_status_payload(
        current_stage="solver-dispatch",
        next_recommended_stage=payload["next_recommended_stage"],
        stage_status=dispatch_status,
        review_status=payload["review_status"],
        execution_readiness=payload.get("execution_readiness"),
        report_virtual_path=payload["report_virtual_path"],
        request_virtual_path=payload.get("request_virtual_path"),
        execution_log_virtual_path=payload.get("execution_log_virtual_path"),
        solver_results_virtual_path=payload.get("solver_results_virtual_path"),
        artifact_virtual_paths=payload.get("artifact_virtual_paths"),
        runtime_summary=payload["summary_zh"],
    )

    runtime_snapshot = build_runtime_snapshot(
        current_stage="solver-dispatch",
        task_summary=resolved_task_description,
        confirmation_status=resolved_confirmation_status,
        execution_preference=resolved_execution_preference,
        task_type=resolved_task_type,
        geometry_virtual_path=geometry_virtual_path,
        geometry_family=(payload.get("geometry") or {}).get("geometry_family"),
        execution_readiness=payload.get("execution_readiness"),
        geometry_findings=payload.get("geometry_findings"),
        scale_assessment=payload.get("scale_assessment"),
        reference_value_suggestions=payload.get("reference_value_suggestions"),
        clarification_required=bool(payload.get("clarification_required")),
        calculation_plan=payload.get("calculation_plan"),
        requires_immediate_confirmation=bool(
            payload.get("requires_immediate_confirmation")
        ),
        selected_case_id=selected_case.get("case_id"),
        simulation_requirements=payload.get("simulation_requirements"),
        requested_outputs=payload.get("requested_outputs"),
        recommended_actions=payload.get("recommended_actions"),
        custom_variants=payload.get("custom_variants"),
        output_delivery_plan=payload.get("output_delivery_plan"),
        stage_status=dispatch_status,
        runtime_status=runtime_truth["runtime_status"],
        runtime_summary=runtime_truth["runtime_summary"],
        recovery_guidance=runtime_truth["recovery_guidance"],
        blocker_detail=runtime_truth["blocker_detail"],
        workspace_case_dir_virtual_path=payload.get("workspace_case_dir_virtual_path"),
        run_script_virtual_path=payload.get("run_script_virtual_path"),
        request_virtual_path=payload.get("request_virtual_path"),
        provenance_manifest_virtual_path=payload.get("provenance_manifest_virtual_path"),
        execution_log_virtual_path=payload.get("execution_log_virtual_path"),
        solver_results_virtual_path=payload.get("solver_results_virtual_path"),
        stability_evidence_virtual_path=payload.get("stability_evidence_virtual_path"),
        stability_evidence=payload.get("stability_evidence"),
        provenance_summary=payload.get("provenance_summary"),
        environment_fingerprint=payload.get("environment_fingerprint"),
        environment_parity_assessment=payload.get("environment_parity_assessment"),
        supervisor_handoff_virtual_path=payload.get("supervisor_handoff_virtual_path"),
        next_recommended_stage=payload["next_recommended_stage"],
        report_virtual_path=payload["report_virtual_path"],
        artifact_virtual_paths=payload["artifact_virtual_paths"],
        execution_plan=build_execution_plan(
            confirmation_status=resolved_confirmation_status,
            existing_plan=existing_runtime.get("execution_plan"),
            stage_updates=execution_updates,
        ),
        review_status=payload["review_status"],
        scientific_verification_assessment=payload.get(
            "scientific_verification_assessment"
        ),
        activity_timeline=extend_runtime_timeline(
            existing_runtime,
            build_runtime_event(
                stage="solver-dispatch",
                actor="solver-dispatch",
                title="Updated OpenFOAM solver dispatch",
                summary=payload["summary_zh"],
                status=dispatch_status,
            ),
        ),
    )
    detail_lines = "\n".join(f"- {artifact}" for artifact in artifacts)
    message = (
        f"{payload['summary_zh']}\n"
        f"已登记 {len(artifacts)} 项研究产物，可在工作区直接查看：\n{detail_lines}"
    )
    return Command(
        update={
            "artifacts": artifacts,
            "submarine_runtime": runtime_snapshot.model_dump(mode="json"),
            "messages": [ToolMessage(message, tool_call_id=tool_call_id)],
        },
    )
