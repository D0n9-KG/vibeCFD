"""Unified research-evidence aggregation helpers for submarine CFD reporting."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from deerflow.domain.submarine.models import (
    SubmarineCaseAcceptanceProfile,
    SubmarineResearchEvidenceSummary,
)


def _as_mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return dumped
    return {}


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


def build_verification_status(
    scientific_verification_assessment: object | None,
) -> tuple[str, list[str], list[str], list[str]]:
    assessment = _as_mapping(scientific_verification_assessment)
    blocking_issues = _as_string_list(assessment.get("blocking_issues"))
    missing_evidence = _as_string_list(assessment.get("missing_evidence"))
    passed_requirements = _as_string_list(assessment.get("passed_requirements"))
    status = str(assessment.get("status") or "").strip()

    if status == "blocked":
        return "blocked", blocking_issues, missing_evidence, passed_requirements
    if status == "research_ready":
        return "passed", blocking_issues, missing_evidence, passed_requirements
    if status == "needs_more_verification":
        return (
            "needs_more_verification",
            blocking_issues,
            missing_evidence,
            passed_requirements,
        )

    return (
        "needs_more_verification",
        blocking_issues,
        missing_evidence or ["Scientific verification assessment is unavailable."],
        passed_requirements,
    )


def build_validation_status(
    *,
    acceptance_profile: SubmarineCaseAcceptanceProfile | Mapping[str, Any] | None,
    acceptance_assessment: object | None,
) -> tuple[str, list[str], list[str], list[str]]:
    profile = _as_mapping(acceptance_profile)
    assessment = _as_mapping(acceptance_assessment)
    benchmark_targets = profile.get("benchmark_targets")
    target_count = len(benchmark_targets) if isinstance(benchmark_targets, list) else 0
    comparisons = assessment.get("benchmark_comparisons")
    comparison_items = (
        [item for item in comparisons if isinstance(item, Mapping)]
        if isinstance(comparisons, list)
        else []
    )
    blocking_issues = _as_string_list(assessment.get("blocking_issues"))
    evidence_gaps: list[str] = []
    highlights: list[str] = []

    if target_count == 0:
        evidence_gaps.append("No applicable benchmark target was available for this run.")
        return "missing_validation_reference", blocking_issues, evidence_gaps, highlights

    if not comparison_items:
        evidence_gaps.append(
            "Benchmark targets exist for this case, but no validation comparisons were produced."
        )
        return "blocked", blocking_issues, evidence_gaps, highlights

    has_failure = False
    has_pass = False
    for item in comparison_items:
        metric_id = str(item.get("metric_id") or "unknown")
        status = str(item.get("status") or "unknown")
        detail = str(item.get("detail") or f"Benchmark {metric_id} reported {status}.")
        if status == "passed":
            has_pass = True
            highlights.append(detail)
            continue
        has_failure = True
        evidence_gaps.append(detail)

    if has_failure:
        return "validation_failed", blocking_issues, evidence_gaps, highlights
    if has_pass:
        return "validated", blocking_issues, evidence_gaps, highlights
    return "blocked", blocking_issues, evidence_gaps, highlights


def build_provenance_status(
    *,
    experiment_summary: object | None,
    scientific_study_summary: object | None,
    output_delivery_plan: list[dict[str, Any]] | None,
    artifact_virtual_paths: list[str] | None,
) -> tuple[str, list[str], list[str], list[str]]:
    experiment = _as_mapping(experiment_summary)
    studies = _as_mapping(scientific_study_summary)
    artifacts = artifact_virtual_paths or []
    delivery_items = output_delivery_plan or []

    has_report_artifact = any(
        path.endswith("/final-report.json") or path.endswith("/delivery-readiness.json")
        for path in artifacts
    )
    has_experiment_manifest = bool(experiment.get("manifest_virtual_path"))
    has_experiment_compare = bool(experiment.get("compare_virtual_path"))
    experiment_linkage_status = str(
        experiment.get("linkage_status") or "consistent"
    ).strip()
    experiment_linkage_issues = _as_string_list(experiment.get("linkage_issues"))
    has_study_manifest = bool(studies.get("manifest_virtual_path"))
    delivered_outputs = [
        item
        for item in delivery_items
        if isinstance(item, Mapping)
        and str(item.get("delivery_status") or "") == "delivered"
    ]
    delivered_artifact_paths = [
        path
        for item in delivered_outputs
        for path in _as_string_list(item.get("artifact_virtual_paths"))
    ]

    highlights: list[str] = []
    gaps: list[str] = []

    if has_experiment_manifest and has_experiment_compare:
        highlights.append("Experiment manifest and compare summary are available.")
    if experiment_linkage_status == "consistent" and (
        has_experiment_manifest or has_experiment_compare
    ):
        highlights.append(
            "Experiment registry coverage is consistent with the planned scientific variants."
        )
    if has_study_manifest:
        highlights.append("Scientific study manifest is available.")
    if delivered_artifact_paths:
        highlights.append("Requested output artifacts were exported for this run.")
    has_core_evidence_artifacts = any(
        path.endswith("/solver-results.json")
        or path.endswith("/verification-mesh-independence.json")
        or path.endswith("/verification-domain-sensitivity.json")
        or path.endswith("/verification-time-step-sensitivity.json")
        for path in artifacts
    )
    if has_core_evidence_artifacts:
        highlights.append("Core solver and scientific verification artifacts are available.")

    traceable = (
        has_report_artifact
        and has_experiment_manifest
        and has_experiment_compare
        and experiment_linkage_status == "consistent"
        and has_study_manifest
        and (bool(delivered_artifact_paths) or has_core_evidence_artifacts)
    )
    if traceable:
        return "traceable", [], gaps, highlights

    if has_report_artifact or has_experiment_manifest or has_study_manifest or delivered_outputs:
        if not has_experiment_manifest or not has_experiment_compare:
            gaps.append("Experiment registry entrypoints are incomplete.")
        if experiment_linkage_status != "consistent":
            gaps.extend(
                experiment_linkage_issues
                or ["Experiment registry coverage is incomplete for the planned studies."]
            )
        if not has_study_manifest:
            gaps.append("Scientific study manifest is missing from the evidence trail.")
        if not delivered_artifact_paths and not has_core_evidence_artifacts:
            gaps.append(
                "Requested outputs or core scientific evidence artifacts are not yet linked."
            )
        return "partial", [], gaps, highlights

    return "missing", [], ["Research provenance artifacts are missing."], highlights


def build_research_evidence_summary(
    *,
    acceptance_profile: SubmarineCaseAcceptanceProfile | Mapping[str, Any] | None,
    acceptance_assessment: object | None,
    scientific_verification_assessment: object | None,
    scientific_study_summary: object | None,
    experiment_summary: object | None,
    output_delivery_plan: list[dict[str, Any]] | None,
    artifact_virtual_paths: list[str] | None,
) -> dict[str, Any]:
    (
        verification_status,
        verification_blockers,
        verification_gaps,
        passed_evidence,
    ) = build_verification_status(scientific_verification_assessment)
    (
        validation_status,
        validation_blockers,
        validation_gaps,
        benchmark_highlights,
    ) = build_validation_status(
        acceptance_profile=acceptance_profile,
        acceptance_assessment=acceptance_assessment,
    )
    (
        provenance_status,
        provenance_blockers,
        provenance_gaps,
        provenance_highlights,
    ) = build_provenance_status(
        experiment_summary=experiment_summary,
        scientific_study_summary=scientific_study_summary,
        output_delivery_plan=output_delivery_plan,
        artifact_virtual_paths=artifact_virtual_paths,
    )

    blocking_issues = [
        *verification_blockers,
        *validation_blockers,
        *provenance_blockers,
    ]
    evidence_gaps = [
        *verification_gaps,
        *validation_gaps,
        *provenance_gaps,
    ]

    if verification_status == "blocked" or validation_status in {
        "blocked",
        "validation_failed",
    }:
        readiness_status = "blocked"
        confidence = "low"
    elif verification_status != "passed":
        readiness_status = "insufficient_evidence"
        confidence = "low"
    elif validation_status == "missing_validation_reference":
        readiness_status = "verified_but_not_validated"
        confidence = "medium"
    elif validation_status == "validated" and provenance_status == "traceable":
        readiness_status = "research_ready"
        confidence = "high"
    elif validation_status == "validated":
        readiness_status = "validated_with_gaps"
        confidence = "medium"
    else:
        readiness_status = "insufficient_evidence"
        confidence = "low"

    summary = SubmarineResearchEvidenceSummary(
        readiness_status=readiness_status,
        verification_status=verification_status,
        validation_status=validation_status,
        provenance_status=provenance_status,
        confidence=confidence,
        blocking_issues=blocking_issues,
        evidence_gaps=evidence_gaps,
        passed_evidence=passed_evidence,
        benchmark_highlights=benchmark_highlights,
        provenance_highlights=provenance_highlights,
        artifact_virtual_paths=_as_string_list(artifact_virtual_paths),
    )
    return summary.model_dump(mode="json")
