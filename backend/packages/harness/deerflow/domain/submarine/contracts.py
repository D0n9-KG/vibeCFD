"""Supervisor-facing contracts for the submarine DeerFlow runtime."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .models import (
    CalculationPlanItem,
    GeometryFinding,
    GeometryReferenceValueSuggestion,
    GeometryScaleAssessment,
    SubmarineCustomExperimentVariant,
)


class SubmarineRuntimeRequest(BaseModel):
    """Structured request passed from the Supervisor into the DeerFlow runtime."""

    task_summary: str
    confirmation_status: Literal["draft", "confirmed"] = "draft"
    execution_preference: Literal[
        "plan_only",
        "execute_now",
        "preflight_then_execute",
    ] = "plan_only"
    uploaded_geometry_path: str
    task_type: str = "resistance"
    geometry_family_hint: str | None = None
    selected_case_id: str | None = None
    simulation_requirements: dict[str, float | int] | None = None
    requested_outputs: list[dict] = Field(default_factory=list)
    supervisor_notes: list[str] = Field(default_factory=list)
    calculation_plan: list[CalculationPlanItem] = Field(default_factory=list)
    custom_variants: list[SubmarineCustomExperimentVariant] = Field(default_factory=list)


class SupervisorReviewContract(BaseModel):
    """Structured review metadata emitted by DeerFlow runtime stages."""

    review_status: Literal["ready_for_supervisor", "needs_user_confirmation", "blocked"] = "ready_for_supervisor"
    next_recommended_stage: str
    report_virtual_path: str
    artifact_virtual_paths: list[str] = Field(default_factory=list)
    scientific_gate_status: Literal["ready_for_claim", "claim_limited", "blocked"] | None = None
    allowed_claim_level: Literal[
        "delivery_only",
        "verified_but_not_validated",
        "validated_with_gaps",
        "research_ready",
    ] | None = None
    scientific_gate_virtual_path: str | None = None


class SubmarineRuntimeEvent(BaseModel):
    """Structured timeline item persisted in thread runtime state."""

    stage: str
    actor: str
    role_id: str | None = None
    title: str
    summary: str
    status: str | None = None
    skill_names: list[str] = Field(default_factory=list)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
    )


ExecutionPlanStatus = Literal[
    "pending",
    "ready",
    "in_progress",
    "completed",
    "blocked",
]
SubmarineRuntimeStatus = Literal[
    "ready",
    "running",
    "blocked",
    "failed",
    "completed",
]


class SubmarineExecutionPlanItem(BaseModel):
    """Structured execution-plan item visible to the supervisor and user workbench."""

    role_id: str
    owner: str
    goal: str
    status: ExecutionPlanStatus
    target_skills: list[str] = Field(default_factory=list)


class SubmarineRequestedOutput(BaseModel):
    output_id: str
    label: str
    requested_label: str
    status: Literal["requested"] = "requested"
    support_level: Literal["supported", "not_yet_supported", "needs_clarification"] = "supported"
    postprocess_spec: dict[str, Any] | None = None
    notes: str | None = None


class SubmarineOutputDeliveryItem(BaseModel):
    output_id: str
    label: str
    delivery_status: Literal[
        "planned",
        "pending",
        "delivered",
        "not_yet_supported",
        "not_available_for_this_run",
    ]
    detail: str
    artifact_virtual_paths: list[str] = Field(default_factory=list)


SubmarineScientificGateStatus = Literal["ready_for_claim", "claim_limited", "blocked"]
SubmarineScientificClaimLevel = Literal[
    "delivery_only",
    "verified_but_not_validated",
    "validated_with_gaps",
    "research_ready",
]


class SubmarineScientificSupervisorGate(BaseModel):
    gate_status: SubmarineScientificGateStatus
    allowed_claim_level: SubmarineScientificClaimLevel
    source_readiness_status: str
    recommended_stage: str
    remediation_stage: str | None = None
    blocking_reasons: list[str] = Field(default_factory=list)
    advisory_notes: list[str] = Field(default_factory=list)
    artifact_virtual_paths: list[str] = Field(default_factory=list)


_EXECUTION_PLAN_TEMPLATE: tuple[tuple[str, str, str], ...] = (
    (
        "claude-code-supervisor",
        "Claude Code",
        "Clarify the CFD objective, constraints, deliverables, and keep the active plan aligned with the user.",
    ),
    (
        "task-intelligence",
        "DeerFlow task-intelligence",
        "Match candidate cases, understand the task, and select the most relevant submarine CFD workflow template.",
    ),
    (
        "geometry-preflight",
        "DeerFlow geometry-preflight",
        "Inspect the uploaded STL geometry, detect scale or format risks, and record a traceable preflight decision.",
    ),
    (
        "solver-dispatch",
        "DeerFlow solver-dispatch",
        "Map the confirmed setup into an OpenFOAM case, run controlled execution, and capture CFD outputs.",
    ),
    (
        "scientific-study",
        "DeerFlow scientific-study",
        "Plan and track deterministic scientific-study variants so baseline evidence can expand into research-grade sensitivity checks.",
    ),
    (
        "experiment-compare",
        "DeerFlow experiment-compare",
        "Compare baseline and study-variant runs through structured experiment manifests and run-delta summaries.",
    ),
    (
        "scientific-verification",
        "DeerFlow scientific-verification",
        "Evaluate study evidence, verification requirements, and scientific readiness before stronger claims are made.",
    ),
    (
        "result-reporting",
        "DeerFlow result-reporting",
        "Organize metrics, logs, and reports into reviewable artifacts for supervisor sign-off and user delivery.",
    ),
    (
        "scientific-followup",
        "DeerFlow scientific-followup",
        "Execute or track remediation follow-ups after scientific review so the next iteration stays traceable.",
    ),
    (
        "supervisor-review",
        "Claude Code Supervisor",
        "Review the scientific evidence gate, confirm the allowed claim level, and decide whether follow-up remediation is needed.",
    ),
)


def build_execution_plan(
    *,
    confirmation_status: Literal["draft", "confirmed"] = "draft",
    existing_plan: list[SubmarineExecutionPlanItem | dict] | None = None,
    stage_updates: dict[str, ExecutionPlanStatus] | None = None,
) -> list[dict]:
    """Normalize the shared submarine execution plan and advance selected stages."""

    existing_by_role: dict[str, SubmarineExecutionPlanItem] = {}
    for item in existing_plan or []:
        normalized = SubmarineExecutionPlanItem.model_validate(item)
        existing_by_role[normalized.role_id] = normalized

    if confirmation_status == "confirmed":
        default_statuses: dict[str, ExecutionPlanStatus] = {
            "claude-code-supervisor": "completed",
            "task-intelligence": "ready",
            "geometry-preflight": "ready",
            "solver-dispatch": "pending",
            "scientific-study": "pending",
            "experiment-compare": "pending",
            "scientific-verification": "pending",
            "result-reporting": "pending",
            "scientific-followup": "pending",
            "supervisor-review": "pending",
        }
    else:
        default_statuses = {
            "claude-code-supervisor": "in_progress",
            "task-intelligence": "pending",
            "geometry-preflight": "pending",
            "solver-dispatch": "pending",
            "scientific-study": "pending",
            "experiment-compare": "pending",
            "scientific-verification": "pending",
            "result-reporting": "pending",
            "scientific-followup": "pending",
            "supervisor-review": "pending",
        }

    plan_updates = stage_updates or {}
    plan: list[dict] = []
    for role_id, owner, goal in _EXECUTION_PLAN_TEMPLATE:
        existing_item = existing_by_role.get(role_id)
        item = SubmarineExecutionPlanItem(
            role_id=role_id,
            owner=existing_item.owner if existing_item else owner,
            goal=existing_item.goal if existing_item else goal,
            status=existing_item.status if existing_item else default_statuses[role_id],
            target_skills=existing_item.target_skills if existing_item else [],
        )
        if role_id in plan_updates:
            item.status = plan_updates[role_id]
        plan.append(item.model_dump(mode="json"))

    return plan


class SubmarineRuntimeSnapshot(BaseModel):
    """Latest structured submarine runtime stage persisted in DeerFlow thread state."""

    current_stage: Literal[
        "task-intelligence",
        "geometry-preflight",
        "solver-dispatch",
        "result-reporting",
    ]
    task_summary: str
    confirmation_status: Literal["draft", "confirmed"] = "draft"
    execution_preference: Literal[
        "plan_only",
        "execute_now",
        "preflight_then_execute",
    ] = "plan_only"
    task_type: str
    geometry_virtual_path: str
    geometry_family: str | None = None
    execution_readiness: Literal["stl_ready", "geometry_conversion_required"] | None = None
    geometry_findings: list[GeometryFinding] = Field(default_factory=list)
    scale_assessment: GeometryScaleAssessment | None = None
    reference_value_suggestions: list[GeometryReferenceValueSuggestion] = Field(
        default_factory=list
    )
    clarification_required: bool = False
    calculation_plan: list[CalculationPlanItem] = Field(default_factory=list)
    requires_immediate_confirmation: bool = False
    selected_case_id: str | None = None
    simulation_requirements: dict[str, float | int] | None = None
    requested_outputs: list[SubmarineRequestedOutput] = Field(default_factory=list)
    custom_variants: list[SubmarineCustomExperimentVariant] = Field(default_factory=list)
    output_delivery_plan: list[SubmarineOutputDeliveryItem] = Field(default_factory=list)
    stage_status: str | None = None
    runtime_status: SubmarineRuntimeStatus = "ready"
    runtime_summary: str | None = None
    recovery_guidance: str | None = None
    blocker_detail: str | None = None
    workspace_case_dir_virtual_path: str | None = None
    run_script_virtual_path: str | None = None
    request_virtual_path: str | None = None
    provenance_manifest_virtual_path: str | None = None
    execution_log_virtual_path: str | None = None
    solver_results_virtual_path: str | None = None
    stability_evidence_virtual_path: str | None = None
    stability_evidence: dict[str, Any] | None = None
    provenance_summary: dict[str, Any] | None = None
    environment_fingerprint: dict[str, Any] | None = None
    supervisor_handoff_virtual_path: str | None = None
    scientific_followup_history_virtual_path: str | None = None
    review_status: Literal["ready_for_supervisor", "needs_user_confirmation", "blocked"] = "ready_for_supervisor"
    scientific_verification_assessment: dict[str, Any] | None = None
    scientific_gate_status: SubmarineScientificGateStatus | None = None
    allowed_claim_level: SubmarineScientificClaimLevel | None = None
    scientific_gate_virtual_path: str | None = None
    next_recommended_stage: str
    report_virtual_path: str
    artifact_virtual_paths: list[str] = Field(default_factory=list)
    execution_plan: list[SubmarineExecutionPlanItem] = Field(default_factory=list)
    activity_timeline: list[SubmarineRuntimeEvent] = Field(default_factory=list)


def build_supervisor_review_contract(
    *,
    next_recommended_stage: str,
    report_virtual_path: str,
    artifact_virtual_paths: list[str] | None = None,
    review_status: Literal["ready_for_supervisor", "needs_user_confirmation", "blocked"] = "ready_for_supervisor",
    scientific_gate_status: SubmarineScientificGateStatus | None = None,
    allowed_claim_level: SubmarineScientificClaimLevel | None = None,
    scientific_gate_virtual_path: str | None = None,
) -> SupervisorReviewContract:
    return SupervisorReviewContract(
        review_status=review_status,
        next_recommended_stage=next_recommended_stage,
        report_virtual_path=report_virtual_path,
        artifact_virtual_paths=artifact_virtual_paths or [],
        scientific_gate_status=scientific_gate_status,
        allowed_claim_level=allowed_claim_level,
        scientific_gate_virtual_path=scientific_gate_virtual_path,
    )


def build_runtime_snapshot(
    *,
    current_stage: Literal[
        "task-intelligence",
        "geometry-preflight",
        "solver-dispatch",
        "result-reporting",
    ],
    task_summary: str,
    confirmation_status: Literal["draft", "confirmed"] = "draft",
    execution_preference: Literal[
        "plan_only",
        "execute_now",
        "preflight_then_execute",
    ] = "plan_only",
    task_type: str,
    geometry_virtual_path: str,
    geometry_family: str | None,
    execution_readiness: Literal["stl_ready", "geometry_conversion_required"] | None = None,
    geometry_findings: list[GeometryFinding | dict] | None = None,
    scale_assessment: GeometryScaleAssessment | dict | None = None,
    reference_value_suggestions: list[GeometryReferenceValueSuggestion | dict] | None = None,
    clarification_required: bool = False,
    calculation_plan: list[CalculationPlanItem | dict] | None = None,
    requires_immediate_confirmation: bool = False,
    next_recommended_stage: str,
    report_virtual_path: str,
    artifact_virtual_paths: list[str] | None = None,
    execution_plan: list[SubmarineExecutionPlanItem | dict] | None = None,
    selected_case_id: str | None = None,
    simulation_requirements: dict[str, float | int] | None = None,
    requested_outputs: list[SubmarineRequestedOutput | dict] | None = None,
    custom_variants: list[SubmarineCustomExperimentVariant | dict] | None = None,
    output_delivery_plan: list[SubmarineOutputDeliveryItem | dict] | None = None,
    stage_status: str | None = None,
    runtime_status: SubmarineRuntimeStatus | None = None,
    runtime_summary: str | None = None,
    recovery_guidance: str | None = None,
    blocker_detail: str | None = None,
    workspace_case_dir_virtual_path: str | None = None,
    run_script_virtual_path: str | None = None,
    request_virtual_path: str | None = None,
    provenance_manifest_virtual_path: str | None = None,
    execution_log_virtual_path: str | None = None,
    solver_results_virtual_path: str | None = None,
    stability_evidence_virtual_path: str | None = None,
    stability_evidence: dict[str, Any] | None = None,
    provenance_summary: dict[str, Any] | None = None,
    environment_fingerprint: dict[str, Any] | None = None,
    supervisor_handoff_virtual_path: str | None = None,
    scientific_followup_history_virtual_path: str | None = None,
    review_status: Literal["ready_for_supervisor", "needs_user_confirmation", "blocked"] = "ready_for_supervisor",
    scientific_verification_assessment: dict[str, Any] | None = None,
    scientific_gate_status: SubmarineScientificGateStatus | None = None,
    allowed_claim_level: SubmarineScientificClaimLevel | None = None,
    scientific_gate_virtual_path: str | None = None,
    activity_timeline: list[SubmarineRuntimeEvent | dict] | None = None,
) -> SubmarineRuntimeSnapshot:
    from .runtime_plan import build_runtime_status_payload

    runtime_truth = build_runtime_status_payload(
        current_stage=current_stage,
        next_recommended_stage=next_recommended_stage,
        stage_status=stage_status,
        review_status=review_status,
        execution_readiness=execution_readiness,
        report_virtual_path=report_virtual_path,
        request_virtual_path=request_virtual_path,
        execution_log_virtual_path=execution_log_virtual_path,
        solver_results_virtual_path=solver_results_virtual_path,
        artifact_virtual_paths=artifact_virtual_paths,
        runtime_status=runtime_status,
        runtime_summary=runtime_summary,
        recovery_guidance=recovery_guidance,
        blocker_detail=blocker_detail,
    )

    return SubmarineRuntimeSnapshot(
        current_stage=current_stage,
        task_summary=task_summary,
        confirmation_status=confirmation_status,
        execution_preference=execution_preference,
        task_type=task_type,
        geometry_virtual_path=geometry_virtual_path,
        geometry_family=geometry_family,
        execution_readiness=execution_readiness,
        geometry_findings=geometry_findings or [],
        scale_assessment=scale_assessment,
        reference_value_suggestions=reference_value_suggestions or [],
        clarification_required=clarification_required,
        calculation_plan=calculation_plan or [],
        requires_immediate_confirmation=requires_immediate_confirmation,
        selected_case_id=selected_case_id,
        simulation_requirements=simulation_requirements,
        requested_outputs=requested_outputs or [],
        custom_variants=custom_variants or [],
        output_delivery_plan=output_delivery_plan or [],
        stage_status=stage_status,
        runtime_status=runtime_truth["runtime_status"],
        runtime_summary=runtime_truth["runtime_summary"],
        recovery_guidance=runtime_truth["recovery_guidance"],
        blocker_detail=runtime_truth["blocker_detail"],
        workspace_case_dir_virtual_path=workspace_case_dir_virtual_path,
        run_script_virtual_path=run_script_virtual_path,
        request_virtual_path=request_virtual_path,
        provenance_manifest_virtual_path=provenance_manifest_virtual_path,
        execution_log_virtual_path=execution_log_virtual_path,
        solver_results_virtual_path=solver_results_virtual_path,
        stability_evidence_virtual_path=stability_evidence_virtual_path,
        stability_evidence=stability_evidence,
        provenance_summary=provenance_summary,
        environment_fingerprint=environment_fingerprint,
        supervisor_handoff_virtual_path=supervisor_handoff_virtual_path,
        scientific_followup_history_virtual_path=scientific_followup_history_virtual_path,
        review_status=review_status,
        scientific_verification_assessment=scientific_verification_assessment,
        scientific_gate_status=scientific_gate_status,
        allowed_claim_level=allowed_claim_level,
        scientific_gate_virtual_path=scientific_gate_virtual_path,
        next_recommended_stage=next_recommended_stage,
        report_virtual_path=report_virtual_path,
        artifact_virtual_paths=artifact_virtual_paths or [],
        execution_plan=execution_plan or [],
        activity_timeline=activity_timeline or [],
    )


def build_runtime_event(
    *,
    stage: str,
    actor: str,
    role_id: str | None = None,
    title: str,
    summary: str,
    status: str | None = None,
    skill_names: list[str] | None = None,
) -> SubmarineRuntimeEvent:
    return SubmarineRuntimeEvent(
        stage=stage,
        actor=actor,
        role_id=role_id,
        title=title,
        summary=summary,
        status=status,
        skill_names=skill_names or [],
    )


def extend_runtime_timeline(
    existing_snapshot: SubmarineRuntimeSnapshot | dict | None,
    event: SubmarineRuntimeEvent,
) -> list[dict]:
    raw_existing = []
    if existing_snapshot:
        if isinstance(existing_snapshot, SubmarineRuntimeSnapshot):
            raw_existing = existing_snapshot.activity_timeline
        else:
            raw_existing = existing_snapshot.get("activity_timeline") or []

    timeline = [
        SubmarineRuntimeEvent.model_validate(item).model_dump(mode="json")
        for item in raw_existing
    ]
    timeline.append(event.model_dump(mode="json"))
    return timeline
