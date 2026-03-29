"""Helpers for surfacing scientific capabilities in the shared runtime plan."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import ExecutionPlanStatus


def _as_mapping(value: object | None) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _as_int(value: object | None) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _map_scientific_study_status(value: object | None) -> ExecutionPlanStatus:
    if value == "completed":
        return "completed"
    if value == "blocked":
        return "blocked"
    if value == "in_progress":
        return "in_progress"
    if value == "planned":
        return "ready"
    return "pending"


def _build_experiment_compare_status(
    *,
    experiment_status: object | None,
    compare_count: object | None,
) -> ExecutionPlanStatus:
    if experiment_status == "blocked":
        return "blocked"
    if _as_int(compare_count) and _as_int(compare_count) > 0:
        return "completed"
    if experiment_status == "completed":
        return "ready"
    return "pending"


def _build_scientific_verification_status(
    *,
    verification_status: object | None,
    dispatch_status: object | None = None,
) -> ExecutionPlanStatus:
    if verification_status == "blocked":
        return "blocked"
    if verification_status in {"passed", "needs_more_verification"}:
        return "completed"
    if dispatch_status == "executed":
        return "ready"
    return "pending"


def _build_scientific_followup_status(
    *,
    handoff_status: object | None,
    followup_entry_count: object | None,
) -> ExecutionPlanStatus:
    if _as_int(followup_entry_count) and _as_int(followup_entry_count) > 0:
        return "completed"
    if handoff_status == "not_needed":
        return "completed"
    if handoff_status in {"ready_for_auto_followup", "manual_followup_required"}:
        return "ready"
    return "pending"


def build_scientific_capability_updates_for_dispatch(
    payload: Mapping[str, object],
) -> dict[str, ExecutionPlanStatus]:
    study_manifest = _as_mapping(payload.get("scientific_study_manifest"))
    experiment_manifest = _as_mapping(payload.get("experiment_manifest"))
    run_compare_summary = _as_mapping(payload.get("run_compare_summary"))
    dispatch_status = payload.get("dispatch_status")

    return {
        "scientific-study": _map_scientific_study_status(
            study_manifest.get("study_execution_status")
        ),
        "experiment-compare": _build_experiment_compare_status(
            experiment_status=experiment_manifest.get("experiment_status"),
            compare_count=len(run_compare_summary.get("comparisons") or []),
        ),
        "scientific-verification": _build_scientific_verification_status(
            verification_status=None,
            dispatch_status=dispatch_status,
        ),
        "scientific-followup": "pending",
    }


def build_scientific_capability_updates_for_report(
    payload: Mapping[str, object],
) -> dict[str, ExecutionPlanStatus]:
    study_summary = _as_mapping(payload.get("scientific_study_summary"))
    experiment_summary = _as_mapping(payload.get("experiment_summary"))
    experiment_compare_summary = _as_mapping(payload.get("experiment_compare_summary"))
    scientific_verification_assessment = _as_mapping(
        payload.get("scientific_verification_assessment")
    )
    scientific_remediation_handoff = _as_mapping(
        payload.get("scientific_remediation_handoff")
    )
    scientific_followup_summary = _as_mapping(payload.get("scientific_followup_summary"))

    return {
        "scientific-study": _map_scientific_study_status(
            study_summary.get("study_execution_status")
        ),
        "experiment-compare": _build_experiment_compare_status(
            experiment_status=experiment_summary.get("experiment_status"),
            compare_count=experiment_compare_summary.get("compare_count"),
        ),
        "scientific-verification": _build_scientific_verification_status(
            verification_status=scientific_verification_assessment.get("status")
        ),
        "scientific-followup": _build_scientific_followup_status(
            handoff_status=scientific_remediation_handoff.get("handoff_status"),
            followup_entry_count=scientific_followup_summary.get("entry_count"),
        ),
    }


__all__ = [
    "build_scientific_capability_updates_for_dispatch",
    "build_scientific_capability_updates_for_report",
]
