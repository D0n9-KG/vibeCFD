"""Deterministic experiment registry helpers for submarine CFD workflows."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from .models import (
    SubmarineExperimentRunRecord,
    SubmarineRunCompareSummary,
    SubmarineRunComparison,
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9-]+", "-", value.strip().lower().replace("_", "-"))
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "experiment"


def _as_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _count_statuses(statuses: Sequence[str | None]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for status in statuses:
        if not status:
            continue
        counts[status] = counts.get(status, 0) + 1
    return counts


def _build_compare_workflow_status(
    comparisons: Sequence[SubmarineRunComparison],
) -> str:
    statuses = [comparison.compare_status for comparison in comparisons]
    if not statuses:
        return "planned"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if all(status == "planned" for status in statuses):
        return "planned"
    if all(status == "completed" for status in statuses):
        return "completed"
    return "partial"


def build_experiment_id(
    *,
    selected_case_id: str | None,
    run_dir_name: str,
    task_type: str,
) -> str:
    case_part = _slugify(selected_case_id or "submarine")
    return f"{case_part}-{_slugify(run_dir_name)}-{_slugify(task_type)}"


def build_experiment_run_id(
    *,
    study_type: str | None,
    variant_id: str | None,
) -> str:
    if not study_type or not variant_id:
        return "baseline"
    return f"{study_type}:{variant_id}"


def build_metric_snapshot(
    *,
    solver_results: Mapping[str, object] | None,
) -> dict[str, object]:
    if not isinstance(solver_results, Mapping):
        return {}

    latest_force_coefficients = solver_results.get("latest_force_coefficients")
    latest_forces = solver_results.get("latest_forces")
    mesh_summary = solver_results.get("mesh_summary")

    fx_value = None
    if isinstance(latest_forces, Mapping):
        total_force = latest_forces.get("total_force")
        if isinstance(total_force, Sequence) and total_force:
            fx_value = _as_number(total_force[0])

    mesh_cells = None
    if isinstance(mesh_summary, Mapping):
        mesh_cells = _as_number(mesh_summary.get("cells"))

    cd_value = None
    if isinstance(latest_force_coefficients, Mapping):
        cd_value = _as_number(latest_force_coefficients.get("Cd"))

    snapshot: dict[str, object] = {}
    if cd_value is not None:
        snapshot["Cd"] = cd_value
    if fx_value is not None:
        snapshot["Fx"] = fx_value

    final_time = _as_number(solver_results.get("final_time_seconds"))
    if final_time is not None:
        snapshot["final_time_seconds"] = final_time
    if mesh_cells is not None:
        snapshot["mesh_cells"] = mesh_cells

    return snapshot


def build_run_record(
    *,
    experiment_id: str,
    run_id: str,
    run_role: str,
    solver_results_virtual_path: str,
    run_record_virtual_path: str,
    execution_status: str,
    metric_snapshot: Mapping[str, object] | None = None,
    study_type: str | None = None,
    variant_id: str | None = None,
) -> SubmarineExperimentRunRecord:
    return SubmarineExperimentRunRecord(
        run_id=run_id,
        experiment_id=experiment_id,
        run_role=run_role,
        study_type=study_type,
        variant_id=variant_id,
        solver_results_virtual_path=solver_results_virtual_path,
        run_record_virtual_path=run_record_virtual_path,
        execution_status=execution_status,
        metric_snapshot=dict(metric_snapshot or {}),
    )


def build_run_comparison(
    *,
    baseline_run_id: str,
    baseline_record: Mapping[str, object],
    candidate_record: Mapping[str, object],
) -> SubmarineRunComparison:
    candidate_status = str(candidate_record.get("execution_status") or "planned")
    candidate_run_id = str(candidate_record.get("run_id") or "unknown")
    if candidate_status in {"planned", "in_progress"}:
        return SubmarineRunComparison(
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
            study_type=candidate_record.get("study_type"),
            variant_id=candidate_record.get("variant_id"),
            compare_status="planned",
            candidate_execution_status=candidate_status,
            metric_deltas={},
            notes="Candidate run is registered but scientific study execution is still pending.",
        )
    if candidate_status == "blocked":
        return SubmarineRunComparison(
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
            study_type=candidate_record.get("study_type"),
            variant_id=candidate_record.get("variant_id"),
            compare_status="blocked",
            candidate_execution_status=candidate_status,
            metric_deltas={},
            notes="Candidate run is blocked and cannot be compared against baseline.",
        )

    baseline_snapshot = baseline_record.get("metric_snapshot")
    candidate_snapshot = candidate_record.get("metric_snapshot")
    if not isinstance(baseline_snapshot, Mapping) or not isinstance(
        candidate_snapshot,
        Mapping,
    ):
        return SubmarineRunComparison(
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
            study_type=candidate_record.get("study_type"),
            variant_id=candidate_record.get("variant_id"),
            compare_status="missing_metrics",
            candidate_execution_status=candidate_status,
            metric_deltas={},
            notes="Baseline or candidate metric snapshot is missing.",
        )

    metrics = ("Cd", "Fx", "final_time_seconds", "mesh_cells")
    deltas: dict[str, object] = {}
    missing_metrics: list[str] = []
    for metric_name in metrics:
        baseline_value = _as_number(baseline_snapshot.get(metric_name))
        candidate_value = _as_number(candidate_snapshot.get(metric_name))
        if baseline_value is None or candidate_value is None:
            missing_metrics.append(metric_name)
            continue
        absolute_delta = candidate_value - baseline_value
        relative_delta = absolute_delta / max(abs(baseline_value), 1e-12)
        deltas[metric_name] = {
            "baseline_value": baseline_value,
            "candidate_value": candidate_value,
            "absolute_delta": absolute_delta,
            "relative_delta": relative_delta,
        }

    compare_status = "completed" if not missing_metrics else "missing_metrics"
    notes = None
    if missing_metrics:
        notes = "Missing compare metrics: " + ", ".join(missing_metrics)

    return SubmarineRunComparison(
        baseline_run_id=baseline_run_id,
        candidate_run_id=candidate_run_id,
        study_type=candidate_record.get("study_type"),
        variant_id=candidate_record.get("variant_id"),
        compare_status=compare_status,
        candidate_execution_status=candidate_status,
        metric_deltas=deltas,
        notes=notes,
    )


def build_run_compare_summary(
    *,
    experiment_id: str,
    baseline_run_id: str,
    baseline_record: Mapping[str, object],
    candidate_records: Sequence[Mapping[str, object]],
    artifact_virtual_paths: Sequence[str] | None = None,
) -> SubmarineRunCompareSummary:
    comparisons = [
        build_run_comparison(
            baseline_run_id=baseline_run_id,
            baseline_record=baseline_record,
            candidate_record=candidate_record,
        )
        for candidate_record in candidate_records
    ]
    return SubmarineRunCompareSummary(
        experiment_id=experiment_id,
        baseline_run_id=baseline_run_id,
        comparisons=comparisons,
        artifact_virtual_paths=list(artifact_virtual_paths or []),
        workflow_status=_build_compare_workflow_status(comparisons),
        compare_status_counts=_count_statuses(
            [comparison.compare_status for comparison in comparisons]
        ),
    )


def build_experiment_workflow_status(
    *,
    run_records: Sequence[Mapping[str, object]],
    compare_statuses: Sequence[str | None] | None = None,
) -> str:
    execution_statuses = [
        str(record.get("execution_status") or "planned")
        for record in run_records
        if isinstance(record, Mapping)
    ]
    candidate_statuses = [
        str(record.get("execution_status") or "planned")
        for record in run_records
        if isinstance(record, Mapping)
        and str(record.get("run_id") or "").strip() != "baseline"
    ]
    normalized_compare_statuses = [status for status in (compare_statuses or []) if status]

    if any(status == "blocked" for status in execution_statuses):
        return "blocked"
    if any(status == "blocked" for status in normalized_compare_statuses):
        return "blocked"
    if not candidate_statuses:
        return "completed" if "completed" in execution_statuses else "planned"
    if (
        all(status == "completed" for status in candidate_statuses)
        and normalized_compare_statuses
        and all(status == "completed" for status in normalized_compare_statuses)
    ):
        return "completed"
    if "completed" in execution_statuses or normalized_compare_statuses:
        return "partial"
    return "planned"
