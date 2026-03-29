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
        for record in _as_dict_list(experiment_manifest_mapping.get("run_records"))
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
    ]

    return {
        "linkage_status": "incomplete" if linkage_issues else "consistent",
        "linkage_issue_count": len(linkage_issues),
        "linkage_issues": linkage_issues,
        "expected_variant_run_ids": expected_variant_run_ids,
        "recorded_variant_run_ids": recorded_variant_run_ids,
        "compared_variant_run_ids": compared_variant_run_ids,
        "additional_variant_run_ids": additional_variant_run_ids,
    }


__all__ = ["build_experiment_linkage_assessment"]
