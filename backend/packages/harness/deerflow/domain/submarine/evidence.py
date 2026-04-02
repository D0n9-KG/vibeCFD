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


def _as_number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in deduped:
            deduped.append(normalized)
    return deduped


def _format_decimal(value: object, digits: int = 5) -> str:
    numeric = _as_number(value)
    if numeric is None:
        return "unknown"
    return f"{numeric:.{digits}f}"


def _format_percent(value: object, digits: int = 2) -> str:
    numeric = _as_number(value)
    if numeric is None:
        return "unknown"
    return f"{numeric * 100:.{digits}f}%"


def _format_benchmark_target_reference(target: Mapping[str, Any]) -> str:
    metric_id = str(target.get("metric_id") or "unknown")
    quantity = str(target.get("quantity") or "unknown")
    reference_value = _format_decimal(target.get("reference_value"))
    target_velocity = _as_number(target.get("inlet_velocity_mps"))
    source_label = str(target.get("source_label") or "").strip()

    segments = [f"Benchmark {metric_id} ({quantity}) targets reference {reference_value}"]
    if target_velocity is not None:
        segments.append(f"at {target_velocity:.2f} m/s")
    if source_label:
        segments.append(f"from {source_label}")
    return " ".join(segments) + "."


def _format_benchmark_comparison_narrative(item: Mapping[str, Any]) -> str:
    metric_id = str(item.get("metric_id") or "unknown")
    quantity = str(item.get("quantity") or "unknown")
    status = str(item.get("status") or "unknown")
    detail = str(item.get("detail") or "").strip()
    source_label = str(item.get("source_label") or "").strip()
    source_url = str(item.get("source_url") or "").strip()
    observed_value = _as_number(item.get("observed_value"))
    reference_value = _as_number(item.get("reference_value"))
    relative_error = _as_number(item.get("relative_error"))
    relative_tolerance = _as_number(item.get("relative_tolerance"))
    target_velocity = _as_number(item.get("target_inlet_velocity_mps"))
    observed_velocity = _as_number(item.get("observed_inlet_velocity_mps"))

    segments = [f"Benchmark {metric_id} ({quantity}) reported {status}."]
    if observed_value is not None or reference_value is not None:
        segments.append(
            f"Observed {_format_decimal(observed_value)} vs reference {_format_decimal(reference_value)}."
        )
    if relative_error is not None or relative_tolerance is not None:
        segments.append(
            f"Relative error {_format_percent(relative_error)} against tolerance {_format_percent(relative_tolerance)}."
        )
    if target_velocity is not None or observed_velocity is not None:
        segments.append(
            f"Velocity scope target {_format_decimal(target_velocity, 2)} m/s vs observed {_format_decimal(observed_velocity, 2)} m/s."
        )
    if source_label:
        segments.append(f"Reference source: {source_label}.")
    if source_url:
        segments.append(f"Source URL: {source_url}.")
    if detail:
        segments.append(detail)
    return " ".join(segment for segment in segments if segment)


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
    benchmark_target_items = (
        [item for item in benchmark_targets if isinstance(item, Mapping)]
        if isinstance(benchmark_targets, list)
        else []
    )
    target_count = len(benchmark_target_items)
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
        if blocking_issues:
            evidence_gaps.append(
                "Benchmark validation could not be synthesized because the acceptance assessment is already blocked."
            )
            return "blocked", blocking_issues, evidence_gaps, highlights

        evidence_gaps.extend(
            [
                f"{_format_benchmark_target_reference(target)} No matched validation comparison was produced for the current run."
                for target in benchmark_target_items
            ]
        )
        return "missing_validation_reference", blocking_issues, evidence_gaps, highlights

    has_failure = False
    has_pass = False
    has_reference_gap = False
    for item in comparison_items:
        status = str(item.get("status") or "unknown")
        detail = _format_benchmark_comparison_narrative(item)
        if status == "passed":
            has_pass = True
            highlights.append(detail)
            continue
        if status == "blocked":
            has_failure = True
        else:
            has_reference_gap = True
        evidence_gaps.append(detail)

    if has_failure:
        return "validation_failed", blocking_issues, evidence_gaps, highlights
    if has_pass:
        return "validated", blocking_issues, evidence_gaps, highlights
    if has_reference_gap:
        return "missing_validation_reference", blocking_issues, evidence_gaps, highlights
    return "blocked", blocking_issues, evidence_gaps, highlights


def build_provenance_status(
    *,
    provenance_summary: object | None,
    experiment_summary: object | None,
    scientific_study_summary: object | None,
    output_delivery_plan: list[dict[str, Any]] | None,
    artifact_virtual_paths: list[str] | None,
) -> tuple[str, list[str], list[str], list[str]]:
    provenance = _as_mapping(provenance_summary)
    experiment = _as_mapping(experiment_summary)
    studies = _as_mapping(scientific_study_summary)
    artifacts = artifact_virtual_paths or []
    delivery_items = output_delivery_plan or []

    has_provenance_manifest = bool(provenance.get("manifest_virtual_path"))
    manifest_completeness_status = str(
        provenance.get("manifest_completeness_status") or ""
    ).strip()
    has_report_artifact = any(
        path.endswith("/final-report.json") or path.endswith("/delivery-readiness.json")
        for path in artifacts
    )
    has_experiment_manifest = bool(experiment.get("manifest_virtual_path"))
    has_experiment_compare = bool(experiment.get("compare_virtual_path"))
    experiment_linkage_status = str(
        experiment.get("linkage_status") or "consistent"
    ).strip()
    experiment_workflow_status = str(
        experiment.get("workflow_status")
        or experiment.get("experiment_status")
        or "planned"
    ).strip()
    experiment_linkage_issues = _as_string_list(experiment.get("linkage_issues"))
    has_study_manifest = bool(studies.get("manifest_virtual_path"))
    study_workflow_status = str(
        studies.get("workflow_status")
        or studies.get("study_execution_status")
        or "planned"
    ).strip()
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
    reproducibility_status = str(provenance.get("parity_status") or "unknown").strip()
    reproducibility_gaps = _as_string_list(provenance.get("drift_reasons"))
    reproducibility_guidance = _as_string_list(provenance.get("recovery_guidance"))

    highlights: list[str] = []
    gaps: list[str] = []

    if has_provenance_manifest:
        highlights.append("Canonical provenance manifest is available for this run.")
    if manifest_completeness_status == "complete":
        highlights.append("Canonical provenance manifest is complete.")
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
    if experiment_workflow_status == "completed":
        highlights.append("Experiment compare workflow is complete.")
    if study_workflow_status == "completed":
        highlights.append("Scientific study workflow is complete.")
    if delivered_artifact_paths:
        highlights.append("Requested output artifacts were exported for this run.")
    if reproducibility_status == "matched":
        highlights.append(
            "Environment parity matches the declared runtime profile for reproducible reruns."
        )
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
        has_provenance_manifest
        and manifest_completeness_status == "complete"
        and has_report_artifact
        and has_experiment_manifest
        and has_experiment_compare
        and experiment_linkage_status == "consistent"
        and experiment_workflow_status == "completed"
        and has_study_manifest
        and study_workflow_status == "completed"
        and (bool(delivered_artifact_paths) or has_core_evidence_artifacts)
        and reproducibility_status == "matched"
    )
    if traceable:
        return "traceable", [], gaps, highlights

    if (
        has_provenance_manifest
        or has_report_artifact
        or has_experiment_manifest
        or has_study_manifest
        or delivered_outputs
    ):
        if not has_provenance_manifest:
            gaps.append("Canonical provenance manifest is missing from the evidence trail.")
        elif manifest_completeness_status != "complete":
            gaps.append("Canonical provenance manifest is incomplete.")
        if not has_experiment_manifest or not has_experiment_compare:
            gaps.append("Experiment registry entrypoints are incomplete.")
        if experiment_linkage_status != "consistent":
            gaps.extend(
                experiment_linkage_issues
                or ["Experiment registry coverage is incomplete for the planned studies."]
            )
        if not has_study_manifest:
            gaps.append("Scientific study manifest is missing from the evidence trail.")
        elif study_workflow_status != "completed":
            gaps.append(
                f"Scientific study workflow is still {study_workflow_status}."
            )
        if has_experiment_manifest and experiment_workflow_status != "completed":
            gaps.append(
                f"Experiment compare workflow is still {experiment_workflow_status}."
            )
        if not delivered_artifact_paths and not has_core_evidence_artifacts:
            gaps.append(
                "Requested outputs or core scientific evidence artifacts are not yet linked."
            )
        if reproducibility_status == "drifted_but_runnable":
            gaps.append(
                "Environment parity drifted from the declared runtime profile, so reruns are only partially reproducible."
            )
        elif reproducibility_status == "unknown":
            gaps.append(
                "Environment parity could not be confirmed for this run, so reproducibility remains partial."
            )
        elif reproducibility_status == "blocked":
            gaps.append(
                "Environment parity is blocked because one or more runtime prerequisites are missing."
            )
        gaps.extend(
            f"Environment parity detail: {item}" for item in reproducibility_gaps
        )
        gaps.extend(
            f"Reproducibility recovery guidance: {item}"
            for item in reproducibility_guidance
        )
        return "partial", [], gaps, highlights

    return "missing", [], ["Research provenance artifacts are missing."], highlights


def build_research_evidence_summary(
    *,
    acceptance_profile: SubmarineCaseAcceptanceProfile | Mapping[str, Any] | None,
    acceptance_assessment: object | None,
    scientific_verification_assessment: object | None,
    provenance_summary: object | None,
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
        provenance_summary=provenance_summary,
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
        blocking_issues=_dedupe_strings(blocking_issues),
        evidence_gaps=_dedupe_strings(evidence_gaps),
        passed_evidence=_dedupe_strings(passed_evidence),
        benchmark_highlights=_dedupe_strings(benchmark_highlights),
        provenance_highlights=_dedupe_strings(provenance_highlights),
        artifact_virtual_paths=_as_string_list(artifact_virtual_paths),
    )
    return summary.model_dump(mode="json")
