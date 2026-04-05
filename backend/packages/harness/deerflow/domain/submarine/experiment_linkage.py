"""Experiment/study linkage assessment for submarine research evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .experiments import build_experiment_run_id


def _as_mapping(value: object | None) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return dumped
    return {}


def _as_dict_list(value: object | None) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _as_string(value: object | None) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _unique_strings(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _count_statuses(statuses: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for status in statuses:
        if not status:
            continue
        counts[status] = counts.get(status, 0) + 1
    return counts


def _planned_variant_run_ids(study_manifest: Mapping[str, Any]) -> list[str]:
    expected: list[str] = []
    for definition in _as_dict_list(study_manifest.get("study_definitions")):
        study_type = _as_string(definition.get("study_type"))
        if not study_type:
            continue
        for variant in _as_dict_list(definition.get("variants")):
            variant_id = _as_string(variant.get("variant_id"))
            if not variant_id or variant_id == "baseline":
                continue
            expected.append(
                build_experiment_run_id(
                    study_type=study_type,
                    variant_id=variant_id,
                )
            )
    return _unique_strings(expected)


def _recorded_variant_run_ids(experiment_manifest: Mapping[str, Any]) -> list[str]:
    recorded: list[str] = []
    for record in _as_dict_list(experiment_manifest.get("run_records")):
        run_id = _as_string(record.get("run_id"))
        if not run_id or run_id == "baseline":
            continue
        recorded.append(run_id)
    return _unique_strings(recorded)


def _compared_variant_run_ids(compare_summary: Mapping[str, Any]) -> list[str]:
    compared: list[str] = []
    for comparison in _as_dict_list(compare_summary.get("comparisons")):
        candidate_run_id = _as_string(comparison.get("candidate_run_id"))
        if not candidate_run_id or candidate_run_id == "baseline":
            continue
        compared.append(candidate_run_id)
    return _unique_strings(compared)


def _is_custom_variant_record(record: Mapping[str, Any]) -> bool:
    run_id = _as_string(record.get("run_id"))
    run_role = _as_string(record.get("run_role"))
    variant_origin = _as_string(record.get("variant_origin"))
    return (
        run_role == "custom_variant"
        or variant_origin == "custom_variant"
        or run_id.startswith("custom:")
    )


def _registered_custom_variant_run_ids(
    experiment_manifest: Mapping[str, Any],
) -> list[str]:
    registered: list[str] = []
    for record in _as_dict_list(experiment_manifest.get("run_records")):
        run_id = _as_string(record.get("run_id"))
        if not run_id or run_id == "baseline" or not _is_custom_variant_record(record):
            continue
        registered.append(run_id)
    return _unique_strings(registered)


def build_experiment_linkage_assessment(
    *,
    study_manifest: object | None,
    experiment_manifest: object | None,
    compare_summary: object | None,
) -> dict[str, Any]:
    study_manifest_mapping = _as_mapping(study_manifest)
    experiment_manifest_mapping = _as_mapping(experiment_manifest)
    compare_summary_mapping = _as_mapping(compare_summary)

    expected_variant_run_ids = _planned_variant_run_ids(study_manifest_mapping)
    recorded_variant_run_ids = _recorded_variant_run_ids(experiment_manifest_mapping)
    compared_variant_run_ids = _compared_variant_run_ids(compare_summary_mapping)
    registered_custom_variant_run_ids = _registered_custom_variant_run_ids(
        experiment_manifest_mapping
    )
    run_records = _as_dict_list(experiment_manifest_mapping.get("run_records"))
    comparisons = _as_dict_list(compare_summary_mapping.get("comparisons"))

    linkage_issues: list[str] = []

    manifest_baseline_run_id = _as_string(experiment_manifest_mapping.get("baseline_run_id"))
    compare_baseline_run_id = _as_string(compare_summary_mapping.get("baseline_run_id"))
    if (
        manifest_baseline_run_id
        and compare_baseline_run_id
        and manifest_baseline_run_id != compare_baseline_run_id
    ):
        linkage_issues.append(
            "Experiment registry baseline run id does not match compare summary baseline run id."
        )

    manifest_experiment_id = _as_string(experiment_manifest_mapping.get("experiment_id"))
    compare_experiment_id = _as_string(compare_summary_mapping.get("experiment_id"))
    if (
        manifest_experiment_id
        and compare_experiment_id
        and manifest_experiment_id != compare_experiment_id
    ):
        linkage_issues.append(
            "Experiment registry experiment_id does not match compare summary experiment_id."
        )

    run_record_ids = {
        _as_string(record.get("run_id"))
        for record in run_records
        if _as_string(record.get("run_id"))
    }
    if manifest_baseline_run_id and manifest_baseline_run_id not in run_record_ids:
        linkage_issues.append(
            "Experiment registry is missing the declared baseline run record."
        )

    missing_variant_run_records = [
        run_id
        for run_id in expected_variant_run_ids
        if run_id not in recorded_variant_run_ids
    ]
    linkage_issues.extend(
        f"Planned scientific variant is missing from experiment run records: {run_id}."
        for run_id in missing_variant_run_records
    )

    missing_compare_entries = [
        run_id
        for run_id in expected_variant_run_ids
        if run_id not in compared_variant_run_ids
    ]
    linkage_issues.extend(
        f"Planned scientific variant is missing from experiment compare entry coverage: {run_id}."
        for run_id in missing_compare_entries
    )

    orphan_compare_entries = [
        run_id
        for run_id in compared_variant_run_ids
        if run_id not in recorded_variant_run_ids
    ]
    linkage_issues.extend(
        f"Experiment compare entry has no matching run record: {run_id}."
        for run_id in orphan_compare_entries
    )

    additional_variant_run_ids = [
        run_id
        for run_id in recorded_variant_run_ids
        if run_id not in expected_variant_run_ids
        and run_id not in registered_custom_variant_run_ids
    ]
    linkage_issues.extend(
        f"Experiment registry contains an unrecognized variant run record: {run_id}."
        for run_id in additional_variant_run_ids
    )
    variant_run_status_by_id = {
        _as_string(record.get("run_id")): _as_string(record.get("execution_status"))
        for record in run_records
        if _as_string(record.get("run_id")) and _as_string(record.get("run_id")) != "baseline"
    }
    compare_status_by_id = {
        _as_string(comparison.get("candidate_run_id")): _as_string(
            comparison.get("compare_status")
        )
        for comparison in comparisons
        if _as_string(comparison.get("candidate_run_id"))
        and _as_string(comparison.get("candidate_run_id")) != "baseline"
    }
    baseline_status = next(
        (
            _as_string(record.get("execution_status"))
            for record in run_records
            if _as_string(record.get("run_id")) == manifest_baseline_run_id
        ),
        "",
    )
    run_status_counts = _count_statuses(list(variant_run_status_by_id.values()))
    compare_status_counts = _count_statuses(list(compare_status_by_id.values()))
    planned_variant_run_ids = [
        run_id
        for run_id in expected_variant_run_ids
        if variant_run_status_by_id.get(run_id) == "planned"
    ]
    in_progress_variant_run_ids = [
        run_id
        for run_id in expected_variant_run_ids
        if variant_run_status_by_id.get(run_id) == "in_progress"
    ]
    completed_variant_run_ids = [
        run_id
        for run_id in expected_variant_run_ids
        if variant_run_status_by_id.get(run_id) == "completed"
    ]
    blocked_variant_run_ids = [
        run_id
        for run_id in expected_variant_run_ids
        if variant_run_status_by_id.get(run_id) == "blocked"
    ]
    planned_compare_variant_run_ids = [
        run_id
        for run_id in expected_variant_run_ids
        if compare_status_by_id.get(run_id) == "planned"
    ]
    completed_compare_variant_run_ids = [
        run_id
        for run_id in expected_variant_run_ids
        if compare_status_by_id.get(run_id) == "completed"
    ]
    blocked_compare_variant_run_ids = [
        run_id
        for run_id in expected_variant_run_ids
        if compare_status_by_id.get(run_id) == "blocked"
    ]
    missing_metrics_variant_run_ids = [
        run_id
        for run_id in expected_variant_run_ids
        if compare_status_by_id.get(run_id) == "missing_metrics"
    ]
    planned_custom_variant_run_ids = [
        run_id
        for run_id in registered_custom_variant_run_ids
        if variant_run_status_by_id.get(run_id) in {"planned", "in_progress"}
    ]
    completed_custom_variant_run_ids = [
        run_id
        for run_id in registered_custom_variant_run_ids
        if variant_run_status_by_id.get(run_id) == "completed"
    ]
    missing_custom_compare_entry_ids = [
        run_id
        for run_id in registered_custom_variant_run_ids
        if run_id not in compared_variant_run_ids
    ]

    workflow_status = "planned"
    expected_run_statuses = [
        variant_run_status_by_id.get(run_id) for run_id in expected_variant_run_ids
    ]
    expected_compare_statuses = [
        compare_status_by_id.get(run_id) for run_id in expected_variant_run_ids
    ]
    registered_custom_run_statuses = [
        variant_run_status_by_id.get(run_id)
        for run_id in registered_custom_variant_run_ids
    ]
    registered_custom_compare_statuses = [
        compare_status_by_id.get(run_id)
        for run_id in registered_custom_variant_run_ids
    ]
    if blocked_variant_run_ids or blocked_compare_variant_run_ids or any(
        status == "blocked"
        for status in [*registered_custom_run_statuses, *registered_custom_compare_statuses]
    ):
        workflow_status = "blocked"
    elif (
        (expected_variant_run_ids or registered_custom_variant_run_ids)
        and not linkage_issues
        and all(status == "completed" for status in expected_run_statuses)
        and all(status == "completed" for status in expected_compare_statuses)
        and all(status == "completed" for status in registered_custom_run_statuses)
        and all(status == "completed" for status in registered_custom_compare_statuses)
    ):
        workflow_status = "completed"
    elif not expected_variant_run_ids and not registered_custom_variant_run_ids:
        workflow_status = "completed" if baseline_status == "completed" else "planned"
    elif baseline_status == "completed" or recorded_variant_run_ids or compared_variant_run_ids:
        workflow_status = "partial"

    return {
        "linkage_status": "incomplete" if linkage_issues else "consistent",
        "linkage_issue_count": len(linkage_issues),
        "linkage_issues": linkage_issues,
        "expected_variant_run_ids": expected_variant_run_ids,
        "recorded_variant_run_ids": recorded_variant_run_ids,
        "compared_variant_run_ids": compared_variant_run_ids,
        "registered_custom_variant_run_ids": registered_custom_variant_run_ids,
        "additional_variant_run_ids": additional_variant_run_ids,
        "missing_variant_run_record_ids": missing_variant_run_records,
        "missing_compare_entry_ids": missing_compare_entries,
        "planned_custom_variant_run_ids": planned_custom_variant_run_ids,
        "completed_custom_variant_run_ids": completed_custom_variant_run_ids,
        "missing_custom_compare_entry_ids": missing_custom_compare_entry_ids,
        "orphan_compare_entry_ids": orphan_compare_entries,
        "run_status_counts": run_status_counts,
        "compare_status_counts": compare_status_counts,
        "workflow_status": workflow_status,
        "planned_variant_run_ids": planned_variant_run_ids,
        "in_progress_variant_run_ids": in_progress_variant_run_ids,
        "completed_variant_run_ids": completed_variant_run_ids,
        "blocked_variant_run_ids": blocked_variant_run_ids,
        "planned_compare_variant_run_ids": planned_compare_variant_run_ids,
        "completed_compare_variant_run_ids": completed_compare_variant_run_ids,
        "blocked_compare_variant_run_ids": blocked_compare_variant_run_ids,
        "missing_metrics_variant_run_ids": missing_metrics_variant_run_ids,
    }


__all__ = ["build_experiment_linkage_assessment"]
