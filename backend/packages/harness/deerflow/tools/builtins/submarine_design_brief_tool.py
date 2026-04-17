"""Built-in DeerFlow tool for submarine CFD design brief drafting."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command
from langgraph.typing import ContextT

from deerflow.agents.thread_state import ThreadState
from deerflow.config.paths import VIRTUAL_PATH_PREFIX, get_paths
from deerflow.domain.submarine.calculation_plan import (
    calculation_plan_requires_confirmation,
    calculation_plan_requires_immediate_confirmation,
)
from deerflow.domain.submarine.contracts import (
    build_execution_plan,
    build_runtime_event,
    build_runtime_snapshot,
    extend_runtime_timeline,
)
from deerflow.domain.submarine.design_brief import run_design_brief
from deerflow.domain.submarine.geometry_check import SUPPORTED_GEOMETRY_SUFFIXES
from deerflow.domain.submarine.official_case_profiles import (
    get_official_case_default_simulation_requirements,
    get_official_case_profile,
    should_pin_official_case_defaults,
)
from deerflow.domain.submarine.output_contract import (
    resolve_effective_expected_outputs,
)
from deerflow.tools.builtins.submarine_runtime_context import (
    detect_execution_preference_signal,
    load_existing_design_brief_payload,
    resolve_bound_geometry_virtual_path,
    resolve_execution_preference,
    resolve_runtime_input_source,
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
        if not uploads_dir.exists():
            return None
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


def _build_official_case_profile_payload(
    *,
    official_case_id: str,
    seed_virtual_paths: list[str],
) -> dict[str, object]:
    profile = get_official_case_profile(official_case_id)
    return {
        "case_id": profile.case_id,
        "source_commit": profile.source_commit,
        "source_kind": "pinned_official_source",
        "source_paths": [profile.tutorial_root, *seed_virtual_paths],
        "command_chain": profile.command_chain,
    }


def _latest_human_message_text(runtime: ToolRuntime[ContextT, ThreadState]) -> str:
    messages = (runtime.state or {}).get("messages")
    if not isinstance(messages, list):
        return ""
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = [
                    str(item.get("text") or "")
                    for item in content
                    if isinstance(item, dict) and item.get("type") == "text"
                ]
                return "\n".join(part for part in parts if part)
            return str(content)
    return ""


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
        confirmation_status: Whether the current brief is still a draft or already
            confirmed with the user. When omitted, reuse the last saved value.
            If the latest user turn confirms the proposed CFD setup or resolves
            the pending open questions, pass `confirmed` here and send only the
            remaining unresolved `open_questions` (use an empty list when
            everything needed for execution is now confirmed).
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
        existing_runtime = (runtime.state or {}).get("submarine_runtime") or {}
        outputs_dir = _get_thread_dir(runtime, "outputs_path")
        uploads_dir = _get_thread_dir(runtime, "uploads_path")
        thread_id = _get_thread_id(runtime)
        existing_payload = load_existing_design_brief_payload(
            outputs_dir=outputs_dir,
            state=runtime.state,
        )
        existing_requirements = existing_payload.get("simulation_requirements") or {}

        resolved_task_description = task_description or existing_payload.get("task_description")
        if not resolved_task_description:
            raise ValueError("task_description is required for the first design brief revision")
        latest_user_message_text = _latest_human_message_text(runtime)
        intent_description = "\n".join(
            part
            for part in (latest_user_message_text, resolved_task_description)
            if part
        )

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
        resolved_input_source = resolve_runtime_input_source(
            thread_id=thread_id,
            uploads_dir=uploads_dir,
            explicit_geometry_path=geometry_path,
            existing_runtime=existing_runtime,
            existing_brief=existing_payload,
            uploaded_files=(runtime.state or {}).get("uploaded_files"),
            task_description=resolved_task_description,
            task_type=resolved_task_type,
        )
        if resolved_input_source.get("kind") in {"partial_case_seed", "ambiguous"}:
            raise ValueError(str(resolved_input_source.get("user_message") or "Unsupported runtime input state"))

        input_source_type = (
            existing_runtime.get("input_source_type")
            or existing_payload.get("input_source_type")
            or "geometry_seed"
        )
        official_case_id = (
            existing_runtime.get("official_case_id")
            or existing_payload.get("official_case_id")
        )
        official_case_seed_virtual_paths = list(
            existing_runtime.get("official_case_seed_virtual_paths")
            or existing_payload.get("official_case_seed_virtual_paths")
            or []
        )
        official_case_profile = (
            existing_runtime.get("official_case_profile")
            or existing_payload.get("official_case_profile")
        )
        geometry_virtual_path = existing_runtime.get("geometry_virtual_path") or existing_payload.get(
            "geometry_virtual_path"
        )
        if resolved_input_source.get("kind") == "openfoam_case_seed":
            input_source_type = "openfoam_case_seed"
            official_case_id = str(resolved_input_source.get("official_case_id") or "")
            official_case_seed_virtual_paths = list(
                resolved_input_source.get("seed_virtual_paths") or []
            )
            official_case_profile = _build_official_case_profile_payload(
                official_case_id=official_case_id,
                seed_virtual_paths=official_case_seed_virtual_paths,
            )
            geometry_virtual_path = None
        else:
            resolved_geometry_input = resolve_bound_geometry_virtual_path(
                thread_id=thread_id,
                uploads_dir=uploads_dir,
                explicit_geometry_path=geometry_path,
                existing_runtime=existing_runtime,
                existing_brief=existing_payload,
                uploaded_files=(runtime.state or {}).get("uploaded_files"),
            )
            resolved_geometry_path = _resolve_geometry_path(runtime, resolved_geometry_input)
            geometry_virtual_path = (
                _to_virtual_thread_path(runtime, resolved_geometry_path)
                if resolved_geometry_path is not None
                else None
            )
        requirement_defaults = dict(existing_requirements)
        allow_explicit_requirement_overrides = True
        if input_source_type == "openfoam_case_seed" and official_case_id:
            resolved_task_type = "official_openfoam_case"
            resolved_selected_case_id = official_case_id
            official_case_requirement_defaults = (
                get_official_case_default_simulation_requirements(official_case_id)
            )
            if should_pin_official_case_defaults(intent_description):
                requirement_defaults = official_case_requirement_defaults
                allow_explicit_requirement_overrides = False
            else:
                requirement_defaults = {
                    **official_case_requirement_defaults,
                    **existing_requirements,
                }

        resolved_execution_preference = resolve_execution_preference(
            explicit_preference=(
                execution_preference
                or detect_execution_preference_signal(latest_user_message_text)
            ),
            existing_runtime=(runtime.state or {}).get("submarine_runtime"),
            existing_brief=existing_payload,
            task_description=intent_description,
        )
        resolved_expected_outputs = resolve_effective_expected_outputs(
            existing_outputs=existing_payload.get("expected_outputs"),
            explicit_outputs=expected_outputs,
            task_description=resolved_task_description,
        )
        payload, artifacts = run_design_brief(
            outputs_dir=outputs_dir,
            task_description=resolved_task_description,
            task_type=resolved_task_type,
            confirmation_status=resolved_confirmation_status,
            execution_preference=resolved_execution_preference,
            input_source_type=input_source_type,
            geometry_virtual_path=geometry_virtual_path,
            official_case_id=official_case_id,
            official_case_seed_virtual_paths=official_case_seed_virtual_paths,
            official_case_profile=official_case_profile,
            geometry_family_hint=resolved_geometry_family_hint,
            selected_case_id=resolved_selected_case_id,
            inlet_velocity_mps=(
                inlet_velocity_mps
                if allow_explicit_requirement_overrides and inlet_velocity_mps is not None
                else requirement_defaults.get("inlet_velocity_mps")
            ),
            fluid_density_kg_m3=(
                fluid_density_kg_m3
                if allow_explicit_requirement_overrides and fluid_density_kg_m3 is not None
                else requirement_defaults.get("fluid_density_kg_m3")
            ),
            kinematic_viscosity_m2ps=(
                kinematic_viscosity_m2ps
                if allow_explicit_requirement_overrides
                and kinematic_viscosity_m2ps is not None
                else requirement_defaults.get("kinematic_viscosity_m2ps")
            ),
            end_time_seconds=(
                end_time_seconds
                if allow_explicit_requirement_overrides and end_time_seconds is not None
                else requirement_defaults.get("end_time_seconds")
            ),
            delta_t_seconds=(
                delta_t_seconds
                if allow_explicit_requirement_overrides and delta_t_seconds is not None
                else requirement_defaults.get("delta_t_seconds")
            ),
            write_interval_steps=(
                write_interval_steps
                if allow_explicit_requirement_overrides and write_interval_steps is not None
                else requirement_defaults.get("write_interval_steps")
            ),
            expected_outputs=resolved_expected_outputs,
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
            existing_calculation_plan=(
                existing_runtime.get("calculation_plan")
                or existing_payload.get("calculation_plan")
            ),
            previous_contract_revision=(
                existing_runtime.get("contract_revision")
                or existing_payload.get("contract_revision")
            ),
            existing_custom_variants=(
                existing_runtime.get("custom_variants")
                or existing_payload.get("custom_variants")
            ),
            ready_stage_when_confirmed=(
                "solver-dispatch"
                if input_source_type == "openfoam_case_seed"
                else (
                    "solver-dispatch"
                    if (existing_runtime or {}).get("current_stage")
                    in {"geometry-preflight", "solver-dispatch", "result-reporting"}
                    else None
                )
            ),
        )
    except ValueError as exc:
        return Command(update={"messages": [ToolMessage(f"Error: {exc}", tool_call_id=tool_call_id)]})

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
    clarified_calculation_plan = payload.get("calculation_plan")
    clarification_required = calculation_plan_requires_confirmation(
        clarified_calculation_plan
    ) or bool(payload.get("open_questions"))
    requires_immediate_confirmation = calculation_plan_requires_immediate_confirmation(
        clarified_calculation_plan
    )
    runtime_snapshot = build_runtime_snapshot(
        current_stage="task-intelligence",
        task_summary=payload["task_description"],
        confirmation_status=payload["confirmation_status"],
        approval_state=payload.get("approval_state", "needs_confirmation"),
        goal_status=payload.get("goal_status", "planning"),
        execution_preference=payload["execution_preference"],
        task_type=payload["task_type"],
        input_source_type=payload.get("input_source_type", "geometry_seed"),
        geometry_virtual_path=payload.get("geometry_virtual_path") or "",
        geometry_family=payload.get("geometry_family_hint"),
        official_case_id=payload.get("official_case_id"),
        official_case_seed_virtual_paths=payload.get("official_case_seed_virtual_paths"),
        official_case_profile=payload.get("official_case_profile"),
        geometry_findings=(existing_runtime or {}).get("geometry_findings"),
        scale_assessment=(existing_runtime or {}).get("scale_assessment"),
        reference_value_suggestions=(
            (existing_runtime or {}).get("reference_value_suggestions")
        ),
        execution_readiness=(existing_runtime or {}).get("execution_readiness"),
        clarification_required=clarification_required,
        calculation_plan=clarified_calculation_plan,
        requires_immediate_confirmation=requires_immediate_confirmation,
        contract_revision=payload.get("contract_revision", 1),
        iteration_mode=payload.get("iteration_mode", "baseline"),
        revision_summary=payload.get("revision_summary"),
        capability_gaps=payload.get("capability_gaps"),
        unresolved_decisions=payload.get("unresolved_decisions"),
        evidence_expectations=payload.get("evidence_expectations"),
        variant_policy=payload.get("variant_policy"),
        selected_case_id=payload.get("selected_case_id"),
        simulation_requirements=payload.get("simulation_requirements"),
        requested_outputs=payload.get("requested_outputs"),
        recommended_actions=(existing_runtime or {}).get("recommended_actions"),
        custom_variants=(existing_runtime or {}).get("custom_variants"),
        output_delivery_plan=payload.get("output_delivery_plan"),
        stage_status=payload.get("confirmation_status"),
        runtime_summary=payload["summary_zh"],
        workspace_case_dir_virtual_path=(existing_runtime or {}).get(
            "workspace_case_dir_virtual_path"
        ),
        run_script_virtual_path=(existing_runtime or {}).get(
            "run_script_virtual_path"
        ),
        provenance_manifest_virtual_path=(existing_runtime or {}).get(
            "provenance_manifest_virtual_path"
        ),
        next_recommended_stage=payload["next_recommended_stage"],
        report_virtual_path=payload["report_virtual_path"],
        artifact_virtual_paths=payload["artifact_virtual_paths"],
        request_virtual_path=(existing_runtime or {}).get("request_virtual_path"),
        execution_log_virtual_path=(existing_runtime or {}).get(
            "execution_log_virtual_path"
        ),
        solver_results_virtual_path=(existing_runtime or {}).get(
            "solver_results_virtual_path"
        ),
        stability_evidence_virtual_path=(existing_runtime or {}).get(
            "stability_evidence_virtual_path"
        ),
        stability_evidence=(existing_runtime or {}).get("stability_evidence"),
        provenance_summary=(existing_runtime or {}).get("provenance_summary"),
        environment_fingerprint=(existing_runtime or {}).get("environment_fingerprint"),
        environment_parity_assessment=(existing_runtime or {}).get(
            "environment_parity_assessment"
        ),
        supervisor_handoff_virtual_path=(existing_runtime or {}).get(
            "supervisor_handoff_virtual_path"
        ),
        scientific_followup_history_virtual_path=(existing_runtime or {}).get(
            "scientific_followup_history_virtual_path"
        ),
        execution_plan=build_execution_plan(
            confirmation_status=payload["confirmation_status"],
            existing_plan=payload["execution_outline"],
        ),
        review_status=payload["review_status"],
        scientific_verification_assessment=(existing_runtime or {}).get(
            "scientific_verification_assessment"
        ),
        scientific_gate_status=(existing_runtime or {}).get("scientific_gate_status"),
        allowed_claim_level=(existing_runtime or {}).get("allowed_claim_level"),
        scientific_gate_virtual_path=(existing_runtime or {}).get(
            "scientific_gate_virtual_path"
        ),
        decision_status=(existing_runtime or {}).get("decision_status"),
        delivery_decision_summary=(existing_runtime or {}).get(
            "delivery_decision_summary"
        ),
        stage_hints=payload.get("stage_hints"),
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
