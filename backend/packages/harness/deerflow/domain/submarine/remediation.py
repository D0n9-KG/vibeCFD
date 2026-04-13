"""Scientific remediation-plan helpers for submarine CFD reporting."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _as_mapping(value: object | None) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return dumped
    return {}


def _as_string_list(value: object | None) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


def _merge_artifact_paths(*groups: object) -> list[str]:
    merged: list[str] = []
    for group in groups:
        if isinstance(group, str):
            candidates = [group]
        elif isinstance(group, list):
            candidates = [item for item in group if isinstance(item, str) and item]
        else:
            candidates = []
        for item in candidates:
            if item not in merged:
                merged.append(item)
    return merged


def _collect_actionable_study_types(
    scientific_study_summary: Mapping[str, Any],
) -> list[str]:
    study_types: list[str] = []
    for item in scientific_study_summary.get("studies") or []:
        if not isinstance(item, Mapping):
            continue
        verification_status = str(item.get("verification_status") or "")
        if verification_status not in {"missing_evidence", "blocked"}:
            continue
        actionable = False
        for field_name in (
            "planned_variant_run_ids",
            "in_progress_variant_run_ids",
            "blocked_variant_run_ids",
            "planned_compare_variant_run_ids",
            "missing_metrics_variant_run_ids",
        ):
            value = item.get(field_name)
            if isinstance(value, list) and any(
                isinstance(entry, str) and entry for entry in value
            ):
                actionable = True
                break
        if not actionable and verification_status != "missing_evidence":
            continue
        study_type = str(item.get("study_type") or "scientific_study")
        if study_type not in study_types:
            study_types.append(study_type)
    return study_types


def _build_action(
    *,
    action_id: str,
    title: str,
    summary: str,
    owner_stage: str,
    priority: str,
    execution_mode: str,
    evidence_gap: str,
    required_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "title": title,
        "summary": summary,
        "owner_stage": owner_stage,
        "priority": priority,
        "execution_mode": execution_mode,
        "status": "pending",
        "evidence_gap": evidence_gap,
        "required_artifacts": required_artifacts or [],
    }


def build_scientific_remediation_summary(
    *,
    scientific_supervisor_gate: object | None,
    research_evidence_summary: object | None,
    scientific_verification_assessment: object | None = None,
    scientific_study_summary: object | None = None,
    artifact_virtual_paths: list[str] | None = None,
) -> dict[str, Any]:
    gate = _as_mapping(scientific_supervisor_gate)
    research = _as_mapping(research_evidence_summary)
    verification = _as_mapping(scientific_verification_assessment)
    study_summary = _as_mapping(scientific_study_summary)

    current_claim_level = str(gate.get("allowed_claim_level") or "delivery_only")
    current_readiness = str(
        research.get("readiness_status")
        or gate.get("source_readiness_status")
        or "insufficient_evidence"
    )
    validation_status = str(research.get("validation_status") or "").strip()
    provenance_status = str(research.get("provenance_status") or "").strip()
    recommended_stage = str(gate.get("recommended_stage") or "supervisor-review")
    evidence_gaps = _as_string_list(research.get("evidence_gaps"))
    missing_evidence = _as_string_list(verification.get("missing_evidence"))
    actionable_study_types = _collect_actionable_study_types(study_summary)
    plan_artifacts = _as_string_list(artifact_virtual_paths)
    gate_artifacts = _as_string_list(gate.get("artifact_virtual_paths"))

    actions: list[dict[str, Any]] = []

    if current_readiness == "research_ready" and current_claim_level == "research_ready":
        return {
            "plan_status": "not_needed",
            "current_claim_level": "research_ready",
            "target_claim_level": "research_ready",
            "recommended_stage": str(gate.get("recommended_stage") or "supervisor-review"),
            "artifact_virtual_paths": plan_artifacts,
            "actions": [],
        }

    if missing_evidence or actionable_study_types:
        study_manifest_path = study_summary.get("manifest_virtual_path")
        study_label = (
            ", ".join(actionable_study_types)
            if actionable_study_types
            else "scientific verification studies"
        )
        evidence_gap = missing_evidence[0] if missing_evidence else None
        if evidence_gap is None:
            for item in study_summary.get("studies") or []:
                if not isinstance(item, Mapping):
                    continue
                study_type = str(item.get("study_type") or "")
                if study_type not in actionable_study_types:
                    continue
                detail = item.get("verification_detail")
                if isinstance(detail, str) and detail:
                    evidence_gap = detail
                    break
        if evidence_gap is None:
            evidence_gap = f"Scientific study evidence is incomplete for {study_label}."
        actions.append(
            _build_action(
                action_id="execute-scientific-studies",
                title="Execute scientific verification studies",
                summary=(
                    "Run the planned scientific study variants and regenerate the missing verification artifacts "
                    f"for {study_label}."
                ),
                owner_stage="solver-dispatch",
                priority="high",
                execution_mode="auto_executable",
                evidence_gap=evidence_gap,
                required_artifacts=_merge_artifact_paths(
                    study_manifest_path,
                    study_summary.get("artifact_virtual_paths"),
                ),
            )
        )

    if validation_status == "missing_validation_reference":
        actions.append(
            _build_action(
                action_id="attach-validation-reference",
                title="Attach validation reference",
                summary=(
                    "Provide or configure a benchmark target for the selected case so the current run can move "
                    "from numerical verification to external validation."
                ),
                owner_stage="supervisor-review",
                priority="high",
                execution_mode="manual_required",
                evidence_gap=(
                    evidence_gaps[0]
                    if evidence_gaps
                    else "No applicable benchmark target was available for this run."
                ),
                required_artifacts=gate_artifacts,
            )
        )

    if (
        str(gate.get("remediation_stage") or "") == "result-reporting"
        or (
            provenance_status in {"partial", "missing"}
            and validation_status == "validated"
        )
    ) and current_readiness != "research_ready":
        actions.append(
            _build_action(
                action_id="regenerate-research-report-linkage",
                title="Regenerate research evidence packaging",
                summary=(
                    "Rebuild result-reporting artifacts so research evidence, compare outputs, and figure delivery "
                    "artifacts are linked consistently."
                ),
                owner_stage="result-reporting",
                priority="medium",
                execution_mode="auto_executable",
                evidence_gap=(
                    evidence_gaps[0]
                    if evidence_gaps
                    else "Reporting and provenance linkage still limit the claim level."
                ),
                required_artifacts=gate_artifacts,
            )
        )

    if actions:
        recommended_stage = str(actions[0].get("owner_stage") or recommended_stage)

    return {
        "plan_status": "recommended" if actions else "blocked",
        "current_claim_level": current_claim_level,
        "target_claim_level": "research_ready",
        "recommended_stage": recommended_stage,
        "artifact_virtual_paths": plan_artifacts,
        "actions": actions,
    }
