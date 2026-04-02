"""Structured summary builders for submarine result reporting."""

from __future__ import annotations

from pathlib import Path

from .artifact_store import (
    load_canonical_provenance_manifest_payload,
    load_first_json_payload_from_artifacts,
    resolve_outputs_artifact,
)
from .experiment_linkage import build_experiment_linkage_assessment
from .figure_delivery import build_figure_delivery_summary as _build_figure_delivery_from_manifest
from .library import load_case_library
from .models import SubmarineCase
from .provenance import build_provenance_summary as _build_provenance_summary_from_manifest


def load_json_payload_from_artifacts(
    outputs_dir: Path,
    artifact_virtual_paths: list[str],
    suffix: str,
) -> tuple[str, dict] | None:
    return load_first_json_payload_from_artifacts(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=artifact_virtual_paths,
        suffixes=[suffix],
    )


def resolve_selected_case(selected_case_id: str | None) -> SubmarineCase | None:
    if not selected_case_id:
        return None
    return load_case_library().case_index.get(selected_case_id)


def _pick_primary_reference(selected_case: SubmarineCase):
    if not selected_case.reference_sources:
        return None
    for source in selected_case.reference_sources:
        if not source.is_placeholder:
            return source
    return selected_case.reference_sources[0]


def _collect_case_applicability_conditions(selected_case: SubmarineCase) -> list[str]:
    primary_source = _pick_primary_reference(selected_case)
    values = [
        *selected_case.condition_tags,
        *(primary_source.applicability_conditions if primary_source else []),
    ]
    deduped: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in deduped:
            deduped.append(normalized)
    return deduped


def build_selected_case_provenance_summary(
    selected_case: SubmarineCase | None,
) -> dict | None:
    if selected_case is None:
        return None

    primary_source = _pick_primary_reference(selected_case)
    return {
        "case_id": selected_case.case_id,
        "title": selected_case.title,
        "source_label": (
            primary_source.source_label or primary_source.title
            if primary_source is not None
            else None
        ),
        "source_url": primary_source.url if primary_source is not None else None,
        "source_type": primary_source.source_type if primary_source is not None else None,
        "applicability_conditions": _collect_case_applicability_conditions(selected_case),
        "confidence_note": (
            primary_source.confidence_note if primary_source is not None else None
        ),
        "is_placeholder": (
            primary_source.is_placeholder if primary_source is not None else False
        ),
        "evidence_gap_note": (
            primary_source.evidence_gap_note if primary_source is not None else None
        ),
        "acceptance_profile_summary_zh": (
            selected_case.acceptance_profile.summary_zh
            if selected_case.acceptance_profile is not None
            else None
        ),
        "benchmark_metric_ids": (
            [
                target.metric_id
                for target in selected_case.acceptance_profile.benchmark_targets
            ]
            if selected_case.acceptance_profile is not None
            else []
        ),
        "reference_sources": [
            source.model_dump(mode="json") for source in selected_case.reference_sources
        ],
    }


def _study_type_to_requirement_id(study_type: str) -> str:
    return f"{study_type}_study"


def _count_statuses(statuses: list[str | None]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for status in statuses:
        if not status:
            continue
        counts[status] = counts.get(status, 0) + 1
    return counts


def _candidate_variant_dicts(definition: dict) -> list[dict]:
    return [
        item
        for item in (definition.get("variants") or [])
        if isinstance(item, dict) and str(item.get("variant_id") or "").strip() != "baseline"
    ]


def _variant_run_ids_by_status(
    variants: list[dict],
    *,
    field: str,
    statuses: set[str],
) -> list[str]:
    run_ids: list[str] = []
    for variant in variants:
        if str(variant.get(field) or "").strip() not in statuses:
            continue
        run_id = str(variant.get("expected_run_id") or "").strip()
        if run_id:
            run_ids.append(run_id)
    return run_ids


def _build_study_workflow_detail(
    *,
    workflow_status: str,
    planned_variant_run_ids: list[str],
    in_progress_variant_run_ids: list[str],
    blocked_variant_run_ids: list[str],
    planned_compare_variant_run_ids: list[str],
    missing_metrics_variant_run_ids: list[str],
) -> str:
    details: list[str] = []
    if blocked_variant_run_ids:
        details.append("Blocked variants: " + ", ".join(blocked_variant_run_ids))
    if in_progress_variant_run_ids:
        details.append(
            "Running variants: " + ", ".join(in_progress_variant_run_ids)
        )
    if planned_variant_run_ids:
        details.append("Pending variants: " + ", ".join(planned_variant_run_ids))
    if planned_compare_variant_run_ids:
        details.append(
            "Pending compare coverage: " + ", ".join(planned_compare_variant_run_ids)
        )
    if missing_metrics_variant_run_ids:
        details.append(
            "Incomplete compare metrics: "
            + ", ".join(missing_metrics_variant_run_ids)
        )
    if details:
        return " ".join(details)
    if workflow_status == "completed":
        return "All planned study variants completed with compare coverage."
    if workflow_status == "planned":
        return "Study variants are defined but baseline-linked verification runs have not started."
    return "Scientific study workflow status is available."


def _build_experiment_workflow_detail(summary: dict) -> str:
    details: list[str] = []
    missing_run_records = summary.get("missing_variant_run_record_ids") or []
    missing_compare_entries = summary.get("missing_compare_entry_ids") or []
    blocked_variant_run_ids = summary.get("blocked_variant_run_ids") or []
    planned_variant_run_ids = summary.get("planned_variant_run_ids") or []
    missing_metrics_variant_run_ids = summary.get("missing_metrics_variant_run_ids") or []

    if blocked_variant_run_ids:
        details.append("Blocked variants: " + ", ".join(map(str, blocked_variant_run_ids)))
    if missing_run_records:
        details.append(
            "Missing run records: " + ", ".join(map(str, missing_run_records))
        )
    if missing_compare_entries:
        details.append(
            "Missing compare entries: "
            + ", ".join(map(str, missing_compare_entries))
        )
    if planned_variant_run_ids:
        details.append(
            "Pending variant execution: "
            + ", ".join(map(str, planned_variant_run_ids))
        )
    if missing_metrics_variant_run_ids:
        details.append(
            "Compare metrics not ready: "
            + ", ".join(map(str, missing_metrics_variant_run_ids))
        )
    if details:
        return " ".join(details)
    workflow_status = str(summary.get("workflow_status") or "").strip()
    if workflow_status == "completed":
        return "Experiment linkage, run records, and compare coverage are complete."
    if workflow_status == "planned":
        return "Experiment registry is prepared but variant execution has not started."
    return "Experiment workflow status is available."


def build_scientific_study_summary(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: list[str],
    scientific_verification_assessment: dict | None,
) -> dict | None:
    loaded = load_json_payload_from_artifacts(
        outputs_dir,
        artifact_virtual_paths,
        "study-manifest.json",
    )
    if loaded is None:
        return None

    manifest_virtual_path, manifest = loaded
    study_definitions = manifest.get("study_definitions") or []
    requirement_index = {
        str(item.get("requirement_id")): item
        for item in (scientific_verification_assessment or {}).get("requirements") or []
        if isinstance(item, dict)
    }

    studies: list[dict[str, object]] = []
    for definition in study_definitions:
        if not isinstance(definition, dict):
            continue
        study_type = str(definition.get("study_type") or "").strip()
        requirement = requirement_index.get(_study_type_to_requirement_id(study_type), {})
        variants = definition.get("variants") or []
        candidate_variants = _candidate_variant_dicts(definition)
        variant_status_counts = definition.get("variant_status_counts") or _count_statuses(
            [
                str(item.get("execution_status") or "").strip()
                for item in variants
                if isinstance(item, dict)
            ]
        )
        compare_status_counts = definition.get("compare_status_counts") or _count_statuses(
            [
                str(item.get("compare_status") or "").strip()
                for item in candidate_variants
            ]
        )
        planned_variant_run_ids = _variant_run_ids_by_status(
            candidate_variants,
            field="execution_status",
            statuses={"planned"},
        )
        in_progress_variant_run_ids = _variant_run_ids_by_status(
            candidate_variants,
            field="execution_status",
            statuses={"in_progress"},
        )
        completed_variant_run_ids = _variant_run_ids_by_status(
            candidate_variants,
            field="execution_status",
            statuses={"completed"},
        )
        blocked_variant_run_ids = _variant_run_ids_by_status(
            candidate_variants,
            field="execution_status",
            statuses={"blocked"},
        )
        planned_compare_variant_run_ids = _variant_run_ids_by_status(
            candidate_variants,
            field="compare_status",
            statuses={"planned"},
        )
        completed_compare_variant_run_ids = _variant_run_ids_by_status(
            candidate_variants,
            field="compare_status",
            statuses={"completed"},
        )
        blocked_compare_variant_run_ids = _variant_run_ids_by_status(
            candidate_variants,
            field="compare_status",
            statuses={"blocked"},
        )
        missing_metrics_variant_run_ids = _variant_run_ids_by_status(
            candidate_variants,
            field="compare_status",
            statuses={"missing_metrics"},
        )
        workflow_status = str(
            definition.get("workflow_status")
            or definition.get("study_execution_status")
            or manifest.get("workflow_status")
            or manifest.get("study_execution_status")
            or "planned"
        ).strip()
        studies.append(
            {
                "study_type": study_type,
                "summary_label": definition.get("summary_label"),
                "monitored_quantity": definition.get("monitored_quantity"),
                "variant_count": len([item for item in variants if isinstance(item, dict)]),
                "study_execution_status": definition.get("study_execution_status"),
                "workflow_status": workflow_status,
                "variant_status_counts": variant_status_counts,
                "compare_status_counts": compare_status_counts,
                "expected_variant_run_ids": definition.get("expected_variant_run_ids") or [],
                "planned_variant_run_ids": planned_variant_run_ids,
                "in_progress_variant_run_ids": in_progress_variant_run_ids,
                "completed_variant_run_ids": completed_variant_run_ids,
                "blocked_variant_run_ids": blocked_variant_run_ids,
                "planned_compare_variant_run_ids": planned_compare_variant_run_ids,
                "completed_compare_variant_run_ids": completed_compare_variant_run_ids,
                "blocked_compare_variant_run_ids": blocked_compare_variant_run_ids,
                "missing_metrics_variant_run_ids": missing_metrics_variant_run_ids,
                "workflow_detail": _build_study_workflow_detail(
                    workflow_status=workflow_status,
                    planned_variant_run_ids=planned_variant_run_ids,
                    in_progress_variant_run_ids=in_progress_variant_run_ids,
                    blocked_variant_run_ids=blocked_variant_run_ids,
                    planned_compare_variant_run_ids=planned_compare_variant_run_ids,
                    missing_metrics_variant_run_ids=missing_metrics_variant_run_ids,
                ),
                "verification_status": requirement.get("status"),
                "verification_detail": requirement.get("detail"),
            }
        )

    return {
        "selected_case_id": manifest.get("selected_case_id"),
        "study_execution_status": manifest.get("study_execution_status"),
        "workflow_status": manifest.get("workflow_status")
        or manifest.get("study_execution_status"),
        "study_status_counts": manifest.get("study_status_counts") or _count_statuses(
            [
                str(item.get("workflow_status") or "").strip()
                for item in studies
                if isinstance(item, dict)
            ]
        ),
        "manifest_virtual_path": manifest_virtual_path,
        "artifact_virtual_paths": manifest.get("artifact_virtual_paths") or [manifest_virtual_path],
        "studies": studies,
    }


def build_experiment_summary(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: list[str],
) -> dict | None:
    study_loaded = load_json_payload_from_artifacts(
        outputs_dir,
        artifact_virtual_paths,
        "study-manifest.json",
    )
    manifest_loaded = load_json_payload_from_artifacts(
        outputs_dir,
        artifact_virtual_paths,
        "experiment-manifest.json",
    )
    if manifest_loaded is None:
        return None

    manifest_virtual_path, manifest = manifest_loaded
    study_manifest_virtual_path = study_loaded[0] if study_loaded is not None else None
    study_manifest = study_loaded[1] if study_loaded is not None else {}
    compare_loaded = load_json_payload_from_artifacts(
        outputs_dir,
        artifact_virtual_paths,
        "run-compare-summary.json",
    )
    compare_virtual_path = compare_loaded[0] if compare_loaded is not None else None
    compare_summary = compare_loaded[1] if compare_loaded is not None else {}
    linkage_assessment = build_experiment_linkage_assessment(
        study_manifest=study_manifest,
        experiment_manifest=manifest,
        compare_summary=compare_summary,
    )
    comparisons = compare_summary.get("comparisons") or []
    compare_notes: list[str] = []
    for item in comparisons:
        if not isinstance(item, dict):
            continue
        candidate_run_id = str(item.get("candidate_run_id") or "unknown")
        compare_status = str(item.get("compare_status") or "unknown")
        compare_notes.append(f"{candidate_run_id} | {compare_status}")

    run_records = manifest.get("run_records") or []
    return {
        "experiment_id": manifest.get("experiment_id"),
        "experiment_status": manifest.get("experiment_status"),
        "workflow_status": linkage_assessment.get("workflow_status")
        or manifest.get("workflow_status")
        or manifest.get("experiment_status"),
        "baseline_run_id": manifest.get("baseline_run_id"),
        "run_count": len([item for item in run_records if isinstance(item, dict)]),
        "study_manifest_virtual_path": study_manifest_virtual_path,
        "manifest_virtual_path": manifest_virtual_path,
        "compare_virtual_path": compare_virtual_path,
        "artifact_virtual_paths": list(
            dict.fromkeys(
                [
                    *(
                        manifest.get("artifact_virtual_paths")
                        or [manifest_virtual_path]
                    ),
                    *( [study_manifest_virtual_path] if study_manifest_virtual_path else [] ),
                    *( [compare_virtual_path] if compare_virtual_path else [] ),
                ]
            )
        ),
        "compare_count": len([item for item in comparisons if isinstance(item, dict)]),
        "compare_notes": compare_notes,
        "workflow_detail": _build_experiment_workflow_detail(linkage_assessment),
        **linkage_assessment,
    }


def build_provenance_summary(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: list[str],
    provenance_manifest_virtual_path: str | None = None,
) -> dict | None:
    loaded = load_canonical_provenance_manifest_payload(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=artifact_virtual_paths,
        provenance_manifest_virtual_path=provenance_manifest_virtual_path,
    )
    if loaded is None:
        return None

    manifest_virtual_path, manifest = loaded
    return _build_provenance_summary_from_manifest(
        manifest_virtual_path=manifest_virtual_path,
        manifest_payload=manifest,
    )


def build_experiment_compare_summary(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: list[str],
) -> dict | None:
    manifest_loaded = load_json_payload_from_artifacts(
        outputs_dir,
        artifact_virtual_paths,
        "experiment-manifest.json",
    )
    compare_loaded = load_json_payload_from_artifacts(
        outputs_dir,
        artifact_virtual_paths,
        "run-compare-summary.json",
    )
    if manifest_loaded is None or compare_loaded is None:
        return None

    _, manifest = manifest_loaded
    compare_virtual_path, compare_summary = compare_loaded
    run_record_index = {
        str(item.get("run_id") or "unknown"): item
        for item in (manifest.get("run_records") or [])
        if isinstance(item, dict)
    }
    baseline_run_id = str(compare_summary.get("baseline_run_id") or "baseline")
    baseline_record = run_record_index.get(baseline_run_id, {})

    comparisons: list[dict[str, object]] = []
    for item in compare_summary.get("comparisons") or []:
        if not isinstance(item, dict):
            continue
        candidate_run_id = str(item.get("candidate_run_id") or "unknown")
        candidate_record = run_record_index.get(candidate_run_id, {})
        comparisons.append(
            {
                "candidate_run_id": candidate_run_id,
                "study_type": item.get("study_type"),
                "variant_id": item.get("variant_id"),
                "compare_status": item.get("compare_status"),
                "candidate_execution_status": item.get("candidate_execution_status")
                or candidate_record.get("execution_status"),
                "notes": item.get("notes"),
                "metric_deltas": item.get("metric_deltas") or {},
                "baseline_solver_results_virtual_path": baseline_record.get(
                    "solver_results_virtual_path"
                ),
                "candidate_solver_results_virtual_path": candidate_record.get(
                    "solver_results_virtual_path"
                ),
                "baseline_run_record_virtual_path": baseline_record.get(
                    "run_record_virtual_path"
                ),
                "candidate_run_record_virtual_path": candidate_record.get(
                    "run_record_virtual_path"
                ),
            }
        )

    return {
        "experiment_id": compare_summary.get("experiment_id") or manifest.get("experiment_id"),
        "baseline_run_id": baseline_run_id,
        "compare_count": len(comparisons),
        "compare_virtual_path": compare_virtual_path,
        "workflow_status": compare_summary.get("workflow_status")
        or (
            "blocked"
            if any(item.get("compare_status") == "blocked" for item in comparisons)
            else "completed"
            if comparisons
            and all(item.get("compare_status") == "completed" for item in comparisons)
            else "planned"
            if comparisons
            and all(item.get("compare_status") == "planned" for item in comparisons)
            else "partial"
            if comparisons
            else "planned"
        ),
        "compare_status_counts": compare_summary.get("compare_status_counts")
        or _count_statuses(
            [
                str(item.get("compare_status") or "").strip()
                for item in comparisons
                if isinstance(item, dict)
            ]
        ),
        "planned_candidate_run_ids": [
            item.get("candidate_run_id")
            for item in comparisons
            if item.get("compare_status") == "planned"
        ],
        "completed_candidate_run_ids": [
            item.get("candidate_run_id")
            for item in comparisons
            if item.get("compare_status") == "completed"
        ],
        "blocked_candidate_run_ids": [
            item.get("candidate_run_id")
            for item in comparisons
            if item.get("compare_status") == "blocked"
        ],
        "missing_metrics_candidate_run_ids": [
            item.get("candidate_run_id")
            for item in comparisons
            if item.get("compare_status") == "missing_metrics"
        ],
        "artifact_virtual_paths": compare_summary.get("artifact_virtual_paths")
        or [compare_virtual_path],
        "comparisons": comparisons,
    }


def build_figure_delivery_summary(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: list[str],
) -> dict | None:
    loaded = load_json_payload_from_artifacts(
        outputs_dir,
        artifact_virtual_paths,
        "figure-manifest.json",
    )
    if loaded is None:
        return None

    manifest_virtual_path, manifest = loaded
    return _build_figure_delivery_from_manifest(
        manifest=manifest,
        manifest_virtual_path=manifest_virtual_path,
    )

__all__ = [
    "build_experiment_compare_summary",
    "build_experiment_summary",
    "build_figure_delivery_summary",
    "build_provenance_summary",
    "build_selected_case_provenance_summary",
    "build_scientific_study_summary",
    "resolve_outputs_artifact",
    "resolve_selected_case",
]
