"""Structured summary builders for submarine result reporting."""

from __future__ import annotations

from collections.abc import Mapping
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


def _as_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return dumped
    return {}


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
        "source_label": (primary_source.source_label or primary_source.title if primary_source is not None else None),
        "source_url": primary_source.url if primary_source is not None else None,
        "source_type": primary_source.source_type if primary_source is not None else None,
        "applicability_conditions": _collect_case_applicability_conditions(selected_case),
        "confidence_note": (primary_source.confidence_note if primary_source is not None else None),
        "is_placeholder": (primary_source.is_placeholder if primary_source is not None else False),
        "evidence_gap_note": (primary_source.evidence_gap_note if primary_source is not None else None),
        "acceptance_profile_summary_zh": (selected_case.acceptance_profile.summary_zh if selected_case.acceptance_profile is not None else None),
        "benchmark_metric_ids": ([target.metric_id for target in selected_case.acceptance_profile.benchmark_targets] if selected_case.acceptance_profile is not None else []),
        "reference_sources": [source.model_dump(mode="json") for source in selected_case.reference_sources],
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
    return [item for item in (definition.get("variants") or []) if isinstance(item, dict) and str(item.get("variant_id") or "").strip() != "baseline"]


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
        details.append("Running variants: " + ", ".join(in_progress_variant_run_ids))
    if planned_variant_run_ids:
        details.append("Pending variants: " + ", ".join(planned_variant_run_ids))
    if planned_compare_variant_run_ids:
        details.append("Pending compare coverage: " + ", ".join(planned_compare_variant_run_ids))
    if missing_metrics_variant_run_ids:
        details.append("Incomplete compare metrics: " + ", ".join(missing_metrics_variant_run_ids))
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
    planned_custom_variant_run_ids = summary.get("planned_custom_variant_run_ids") or []
    completed_custom_variant_run_ids = summary.get("completed_custom_variant_run_ids") or []
    missing_custom_compare_entry_ids = summary.get("missing_custom_compare_entry_ids") or []
    registered_custom_variant_run_ids = summary.get("registered_custom_variant_run_ids") or []

    if blocked_variant_run_ids:
        details.append("Blocked variants: " + ", ".join(map(str, blocked_variant_run_ids)))
    if missing_run_records:
        details.append("Missing run records: " + ", ".join(map(str, missing_run_records)))
    if missing_compare_entries:
        details.append("Missing compare entries: " + ", ".join(map(str, missing_compare_entries)))
    if planned_variant_run_ids:
        details.append("Pending variant execution: " + ", ".join(map(str, planned_variant_run_ids)))
    if missing_metrics_variant_run_ids:
        details.append("Compare metrics not ready: " + ", ".join(map(str, missing_metrics_variant_run_ids)))
    if planned_custom_variant_run_ids:
        details.append("Pending custom variants: " + ", ".join(map(str, planned_custom_variant_run_ids)))
    if missing_custom_compare_entry_ids:
        details.append("Custom variants missing compare entries: " + ", ".join(map(str, missing_custom_compare_entry_ids)))
    if completed_custom_variant_run_ids and not details:
        details.append("Completed custom variants: " + ", ".join(map(str, completed_custom_variant_run_ids)))
    if details:
        return " ".join(details)
    workflow_status = str(summary.get("workflow_status") or "").strip()
    if workflow_status == "completed":
        if registered_custom_variant_run_ids:
            return "Experiment linkage, run records, and compare coverage are complete across scientific and custom variants."
        return "Experiment linkage, run records, and compare coverage are complete."
    if workflow_status == "planned":
        return "Experiment registry is prepared but variant execution has not started."
    return "Experiment workflow status is available."


def _is_custom_variant_entry(item: dict) -> bool:
    run_role = str(item.get("run_role") or item.get("variant_origin") or "").strip()
    candidate_run_id = str(item.get("candidate_run_id") or "").strip()
    return run_role == "custom_variant" or candidate_run_id.startswith("custom:")


def _format_compare_entry_label(item: dict) -> str:
    variant_id = str(item.get("variant_id") or "unknown").strip() or "unknown"
    if _is_custom_variant_entry(item):
        return f"custom / {variant_id}"
    study_type = str(item.get("study_type") or "unknown").strip() or "unknown"
    return f"{study_type} / {variant_id}"


def _format_compare_note(item: dict) -> str:
    candidate_run_id = str(item.get("candidate_run_id") or "unknown").strip() or "unknown"
    compare_status = str(item.get("compare_status") or "unknown").strip() or "unknown"
    compare_target_run_id = str(item.get("compare_target_run_id") or item.get("baseline_run_id") or "baseline").strip() or "baseline"
    if _is_custom_variant_entry(item):
        variant_label = str(item.get("variant_label") or item.get("variant_id") or candidate_run_id)
        return f"Custom Variant | {variant_label} | {candidate_run_id} | {compare_status} | compare target {compare_target_run_id}"
    return f"{_format_compare_entry_label(item)} | {candidate_run_id} | {compare_status}"


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
    requirement_index = {str(item.get("requirement_id")): item for item in (scientific_verification_assessment or {}).get("requirements") or [] if isinstance(item, dict)}

    studies: list[dict[str, object]] = []
    for definition in study_definitions:
        if not isinstance(definition, dict):
            continue
        study_type = str(definition.get("study_type") or "").strip()
        requirement = requirement_index.get(_study_type_to_requirement_id(study_type), {})
        variants = definition.get("variants") or []
        candidate_variants = _candidate_variant_dicts(definition)
        variant_status_counts = definition.get("variant_status_counts") or _count_statuses([str(item.get("execution_status") or "").strip() for item in variants if isinstance(item, dict)])
        compare_status_counts = definition.get("compare_status_counts") or _count_statuses([str(item.get("compare_status") or "").strip() for item in candidate_variants])
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
        workflow_status = str(definition.get("workflow_status") or definition.get("study_execution_status") or manifest.get("workflow_status") or manifest.get("study_execution_status") or "planned").strip()
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
        "workflow_status": manifest.get("workflow_status") or manifest.get("study_execution_status"),
        "study_status_counts": manifest.get("study_status_counts") or _count_statuses([str(item.get("workflow_status") or "").strip() for item in studies if isinstance(item, dict)]),
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
        compare_notes.append(_format_compare_note(item))

    run_records = manifest.get("run_records") or []
    return {
        "experiment_id": manifest.get("experiment_id"),
        "experiment_status": manifest.get("experiment_status"),
        "workflow_status": linkage_assessment.get("workflow_status") or manifest.get("workflow_status") or manifest.get("experiment_status"),
        "baseline_run_id": manifest.get("baseline_run_id"),
        "run_count": len([item for item in run_records if isinstance(item, dict)]),
        "study_manifest_virtual_path": study_manifest_virtual_path,
        "manifest_virtual_path": manifest_virtual_path,
        "compare_virtual_path": compare_virtual_path,
        "artifact_virtual_paths": list(
            dict.fromkeys(
                [
                    *(manifest.get("artifact_virtual_paths") or [manifest_virtual_path]),
                    *([study_manifest_virtual_path] if study_manifest_virtual_path else []),
                    *([compare_virtual_path] if compare_virtual_path else []),
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


def build_reproducibility_summary(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: list[str],
    provenance_manifest_virtual_path: str | None = None,
    environment_parity_assessment: Mapping[str, object] | None = None,
) -> dict | None:
    loaded = load_canonical_provenance_manifest_payload(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=artifact_virtual_paths,
        provenance_manifest_virtual_path=provenance_manifest_virtual_path,
    )
    manifest_virtual_path = loaded[0] if loaded is not None else provenance_manifest_virtual_path
    manifest = loaded[1] if loaded is not None else {}
    if manifest_virtual_path is None and not environment_parity_assessment:
        return None

    parity_mapping = _as_mapping(environment_parity_assessment) or _as_mapping(_as_mapping(manifest).get("environment_parity_assessment"))
    fingerprint_mapping = _as_mapping(_as_mapping(manifest).get("environment_fingerprint"))
    parity_status = str(parity_mapping.get("parity_status") or fingerprint_mapping.get("parity_status") or "unknown")
    profile_id = str(parity_mapping.get("profile_id") or fingerprint_mapping.get("profile_id") or "unknown")

    return {
        "manifest_virtual_path": manifest_virtual_path,
        "profile_id": profile_id,
        "parity_status": parity_status,
        "reproducibility_status": parity_status,
        "drift_reasons": list(parity_mapping.get("drift_reasons") or []),
        "recovery_guidance": list(parity_mapping.get("recovery_guidance") or []),
    }


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
    run_record_index = {str(item.get("run_id") or "unknown"): item for item in (manifest.get("run_records") or []) if isinstance(item, dict)}
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
                "run_role": item.get("run_role") or candidate_record.get("run_role"),
                "variant_origin": item.get("variant_origin") or candidate_record.get("variant_origin") or candidate_record.get("run_role"),
                "study_type": item.get("study_type"),
                "variant_id": item.get("variant_id"),
                "variant_label": item.get("variant_label") or candidate_record.get("variant_label"),
                "baseline_reference_run_id": item.get("baseline_reference_run_id") or candidate_record.get("baseline_reference_run_id") or baseline_run_id,
                "compare_target_run_id": item.get("compare_target_run_id") or candidate_record.get("compare_target_run_id") or baseline_run_id,
                "compare_status": item.get("compare_status"),
                "candidate_execution_status": item.get("candidate_execution_status") or candidate_record.get("execution_status"),
                "notes": item.get("notes"),
                "metric_deltas": item.get("metric_deltas") or {},
                "baseline_solver_results_virtual_path": baseline_record.get("solver_results_virtual_path"),
                "candidate_solver_results_virtual_path": candidate_record.get("solver_results_virtual_path"),
                "baseline_run_record_virtual_path": baseline_record.get("run_record_virtual_path"),
                "candidate_run_record_virtual_path": candidate_record.get("run_record_virtual_path"),
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
            if comparisons and all(item.get("compare_status") == "completed" for item in comparisons)
            else "planned"
            if comparisons and all(item.get("compare_status") == "planned" for item in comparisons)
            else "partial"
            if comparisons
            else "planned"
        ),
        "compare_status_counts": compare_summary.get("compare_status_counts") or _count_statuses([str(item.get("compare_status") or "").strip() for item in comparisons if isinstance(item, dict)]),
        "planned_candidate_run_ids": [item.get("candidate_run_id") for item in comparisons if item.get("compare_status") == "planned"],
        "completed_candidate_run_ids": [item.get("candidate_run_id") for item in comparisons if item.get("compare_status") == "completed"],
        "blocked_candidate_run_ids": [item.get("candidate_run_id") for item in comparisons if item.get("compare_status") == "blocked"],
        "missing_metrics_candidate_run_ids": [item.get("candidate_run_id") for item in comparisons if item.get("compare_status") == "missing_metrics"],
        "artifact_virtual_paths": compare_summary.get("artifact_virtual_paths") or [compare_virtual_path],
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


def _dedupe_strings(values: list[object] | None) -> list[str]:
    deduped: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if text and text not in deduped:
            deduped.append(text)
    return deduped


def _claim_level_label_zh(value: object) -> str:
    return {
        "delivery_only": "仅限交付说明",
        "verified_but_not_validated": "已验证但未完成外部验证",
        "validated_with_gaps": "已验证但仍有证据缺口",
        "research_ready": "研究结论可交付",
    }.get(str(value or "").strip(), str(value or "").strip() or "待判定")


def _review_status_label_zh(value: object) -> str:
    return {
        "ready_for_supervisor": "待复核",
        "needs_user_confirmation": "待研究者确认",
        "blocked": "已阻塞",
    }.get(str(value or "").strip(), str(value or "").strip() or "待判定")


def _reproducibility_status_label_zh(value: object) -> str:
    return {
        "matched": "环境一致，可复现",
        "drifted_but_runnable": "环境漂移但仍可运行",
        "unknown": "环境画像未知",
        "blocked": "环境不满足复现要求",
    }.get(str(value or "").strip(), str(value or "").strip() or "待判定")


def _confidence_label_zh(value: object) -> str:
    return {
        "low": "低",
        "medium": "中",
        "high": "高",
    }.get(str(value or "").strip(), str(value or "").strip() or "待判定")


def _recommended_next_step_zh(
    *,
    scientific_supervisor_gate: dict | None,
    research_evidence_summary: dict | None,
    reproducibility_summary: dict | None,
    scientific_followup_summary: dict | None,
) -> str:
    blocking_reasons = _dedupe_strings((scientific_supervisor_gate or {}).get("blocking_reasons"))
    evidence_gaps = _dedupe_strings((research_evidence_summary or {}).get("evidence_gaps"))
    drift_reasons = _dedupe_strings((reproducibility_summary or {}).get("drift_reasons"))
    followup_history_path = str((scientific_followup_summary or {}).get("history_virtual_path") or "").strip()

    if blocking_reasons:
        return "先处理当前阻塞项并修正设置或证据链，再决定是否继续求解。"
    if evidence_gaps:
        return "优先补齐缺失证据或外部对照，再决定是否提升当前结论等级。"
    if drift_reasons:
        return "先校准运行环境与 provenance，再将本次结果视为可复现实验结论。"
    if followup_history_path:
        return "回到聊天确认当前任务是否结束，或基于既有 follow-up 记录继续扩展研究。"
    return "回到聊天确认当前任务是否结束，或根据证据索引继续扩展研究。"


def build_report_overview(
    *,
    summary_zh: str,
    scientific_supervisor_gate: dict | None,
    reproducibility_summary: dict | None,
    review_status: str | None,
    scientific_followup_summary: dict | None,
    research_evidence_summary: dict | None,
) -> dict:
    allowed_claim_level = str((scientific_supervisor_gate or {}).get("allowed_claim_level") or "delivery_only")
    reproducibility_status = str((reproducibility_summary or {}).get("reproducibility_status") or (reproducibility_summary or {}).get("parity_status") or "unknown")
    return {
        "current_conclusion_zh": summary_zh.strip() or "当前暂无可交付结论摘要。",
        "allowed_claim_level": allowed_claim_level,
        "review_status": review_status or "ready_for_supervisor",
        "reproducibility_status": reproducibility_status,
        "recommended_next_step_zh": _recommended_next_step_zh(
            scientific_supervisor_gate=scientific_supervisor_gate,
            research_evidence_summary=research_evidence_summary,
            reproducibility_summary=reproducibility_summary,
            scientific_followup_summary=scientific_followup_summary,
        ),
    }


def build_delivery_highlights(
    *,
    solver_metrics: dict | None,
    scientific_supervisor_gate: dict | None,
    reproducibility_summary: dict | None,
    review_status: str | None,
    figure_delivery_summary: dict | None,
    final_artifact_virtual_paths: list[str],
    source_report_virtual_path: str | None,
    provenance_manifest_virtual_path: str | None,
    scientific_gate_virtual_path: str | None,
) -> dict:
    metric_lines: list[str] = []
    latest_force_coefficients = (solver_metrics or {}).get("latest_force_coefficients") or {}
    latest_forces = (solver_metrics or {}).get("latest_forces") or {}
    total_force = latest_forces.get("total_force") or []

    cd = latest_force_coefficients.get("Cd")
    if isinstance(cd, (int, float)):
        metric_lines.append(f"阻力系数 Cd：{cd:.6f}")
    final_time = (solver_metrics or {}).get("final_time_seconds")
    if isinstance(final_time, (int, float)):
        metric_lines.append(f"最终时间步：{final_time:g} s")
    if total_force and isinstance(total_force[0], (int, float)):
        metric_lines.append(f"总阻力 Fx：{total_force[0]:.4f} N")

    metric_lines.append("允许结论等级：" + _claim_level_label_zh((scientific_supervisor_gate or {}).get("allowed_claim_level")))
    metric_lines.append("复核状态：" + _review_status_label_zh(review_status))
    metric_lines.append("复现状态：" + _reproducibility_status_label_zh((reproducibility_summary or {}).get("reproducibility_status") or (reproducibility_summary or {}).get("parity_status")))

    figure_titles = _dedupe_strings([item.get("title") or item.get("output_id") for item in (figure_delivery_summary or {}).get("figures") or [] if isinstance(item, dict)])
    highlight_artifact_virtual_paths = _dedupe_strings(
        [
            source_report_virtual_path,
            provenance_manifest_virtual_path,
            scientific_gate_virtual_path,
            *(final_artifact_virtual_paths or []),
            *((figure_delivery_summary or {}).get("artifact_virtual_paths") or []),
            *(path for item in (figure_delivery_summary or {}).get("figures") or [] if isinstance(item, dict) for path in (item.get("artifact_virtual_paths") or [])),
        ]
    )
    return {
        "metric_lines": metric_lines,
        "figure_titles": figure_titles,
        "highlight_artifact_virtual_paths": highlight_artifact_virtual_paths[:8],
    }


def build_conclusion_sections(
    *,
    summary_zh: str,
    scientific_supervisor_gate: dict | None,
    research_evidence_summary: dict | None,
    reproducibility_summary: dict | None,
    provenance_manifest_virtual_path: str | None,
    scientific_gate_virtual_path: str | None,
    stability_evidence_virtual_path: str | None,
    source_report_virtual_path: str | None,
    source_artifact_virtual_paths: list[str],
    final_artifact_virtual_paths: list[str],
    figure_delivery_summary: dict | None,
    scientific_followup_summary: dict | None,
) -> list[dict]:
    gate = scientific_supervisor_gate or {}
    research = research_evidence_summary or {}
    reproducibility = reproducibility_summary or {}
    followup = scientific_followup_summary or {}

    allowed_claim_level = str(gate.get("allowed_claim_level") or "delivery_only")
    confidence_label = _confidence_label_zh(research.get("confidence"))
    blocking_reasons = _dedupe_strings(gate.get("blocking_reasons"))
    advisory_notes = _dedupe_strings(gate.get("advisory_notes"))
    evidence_gaps = _dedupe_strings(research.get("evidence_gaps"))
    drift_reasons = _dedupe_strings(reproducibility.get("drift_reasons"))
    provenance_highlights = _dedupe_strings(research.get("provenance_highlights"))

    figure_titles = _dedupe_strings([item.get("title") or item.get("output_id") for item in (figure_delivery_summary or {}).get("figures") or [] if isinstance(item, dict)])

    sections = [
        {
            "conclusion_id": "current_conclusion",
            "title_zh": "当前研究结论",
            "summary_zh": summary_zh.strip() or "当前暂无可交付结论摘要。",
            "claim_level": allowed_claim_level,
            "confidence_label": confidence_label,
            "inline_source_refs": _dedupe_strings(
                [
                    source_report_virtual_path,
                    scientific_gate_virtual_path,
                    provenance_manifest_virtual_path,
                ]
            ),
            "evidence_gap_notes": evidence_gaps[:3] or blocking_reasons[:3],
            "artifact_virtual_paths": _dedupe_strings(
                [
                    source_report_virtual_path,
                    provenance_manifest_virtual_path,
                    *final_artifact_virtual_paths,
                ]
            )[:8],
        },
        {
            "conclusion_id": "evidence_boundary",
            "title_zh": "证据与结论边界",
            "summary_zh": "；".join(
                [
                    f"当前允许的 claim level 为“{_claim_level_label_zh(allowed_claim_level)}”",
                    *(blocking_reasons[:1] or advisory_notes[:1] or ["当前未记录额外阻塞说明"]),
                ]
            ),
            "claim_level": allowed_claim_level,
            "confidence_label": confidence_label,
            "inline_source_refs": _dedupe_strings(
                [
                    scientific_gate_virtual_path,
                    *(research.get("artifact_virtual_paths") or []),
                    stability_evidence_virtual_path,
                ]
            ),
            "evidence_gap_notes": evidence_gaps[:4] or blocking_reasons[:4] or advisory_notes[:4],
            "artifact_virtual_paths": _dedupe_strings(
                [
                    scientific_gate_virtual_path,
                    *(research.get("artifact_virtual_paths") or []),
                    stability_evidence_virtual_path,
                ]
            )[:8],
        },
        {
            "conclusion_id": "reproducibility_traceability",
            "title_zh": "复现与追溯锚点",
            "summary_zh": "；".join(
                [
                    f"复现状态为“{_reproducibility_status_label_zh(reproducibility.get('reproducibility_status') or reproducibility.get('parity_status'))}”",
                    *(provenance_highlights[:1] or (["已记录 provenance manifest。"] if provenance_manifest_virtual_path else [])),
                    *(figure_titles[:1] and [f"代表图表可从“{figure_titles[0]}”开始追溯。"] or []),
                ]
            ),
            "claim_level": allowed_claim_level,
            "confidence_label": confidence_label,
            "inline_source_refs": _dedupe_strings(
                [
                    provenance_manifest_virtual_path,
                    source_report_virtual_path,
                    followup.get("history_virtual_path"),
                ]
            ),
            "evidence_gap_notes": drift_reasons[:4] or _dedupe_strings(followup.get("latest_notes"))[:4],
            "artifact_virtual_paths": _dedupe_strings(
                [
                    provenance_manifest_virtual_path,
                    source_report_virtual_path,
                    *source_artifact_virtual_paths,
                    *((figure_delivery_summary or {}).get("artifact_virtual_paths") or []),
                ]
            )[:8],
        },
    ]
    return sections


def build_evidence_index(
    *,
    research_evidence_summary: dict | None,
    figure_delivery_summary: dict | None,
    scientific_followup_summary: dict | None,
    source_artifact_virtual_paths: list[str],
    final_artifact_virtual_paths: list[str],
    provenance_manifest_virtual_path: str | None,
    source_report_virtual_path: str | None,
    scientific_gate_virtual_path: str | None,
    stability_evidence_virtual_path: str | None,
    supervisor_handoff_virtual_path: str | None,
) -> list[dict]:
    index: list[dict] = []

    def add_group(group_id: str, group_title_zh: str, paths: list[object] | None) -> None:
        artifact_virtual_paths = _dedupe_strings(paths)
        if not artifact_virtual_paths:
            return
        index.append(
            {
                "group_id": group_id,
                "group_title_zh": group_title_zh,
                "artifact_virtual_paths": artifact_virtual_paths,
                "provenance_manifest_virtual_path": provenance_manifest_virtual_path,
            }
        )

    add_group(
        "research_evidence",
        "研究证据与科学判断",
        [
            *((research_evidence_summary or {}).get("artifact_virtual_paths") or []),
            scientific_gate_virtual_path,
            stability_evidence_virtual_path,
        ],
    )
    add_group(
        "figures_and_delivery",
        "代表图表与交付产物",
        [
            *final_artifact_virtual_paths,
            *((figure_delivery_summary or {}).get("artifact_virtual_paths") or []),
            *(path for item in (figure_delivery_summary or {}).get("figures") or [] if isinstance(item, dict) for path in (item.get("artifact_virtual_paths") or [])),
        ],
    )
    add_group(
        "runtime_and_lineage",
        "运行产物与追溯锚点",
        [
            source_report_virtual_path,
            provenance_manifest_virtual_path,
            supervisor_handoff_virtual_path,
            *source_artifact_virtual_paths,
        ],
    )
    add_group(
        "followup_and_refresh",
        "后续动作与刷新链路",
        [
            *((scientific_followup_summary or {}).get("artifact_virtual_paths") or []),
            (scientific_followup_summary or {}).get("latest_result_report_virtual_path"),
            (scientific_followup_summary or {}).get("latest_result_supervisor_handoff_virtual_path"),
        ],
    )
    return index


__all__ = [
    "build_conclusion_sections",
    "build_delivery_highlights",
    "build_evidence_index",
    "build_experiment_compare_summary",
    "build_experiment_summary",
    "build_figure_delivery_summary",
    "build_provenance_summary",
    "build_report_overview",
    "build_reproducibility_summary",
    "build_selected_case_provenance_summary",
    "build_scientific_study_summary",
    "resolve_outputs_artifact",
    "resolve_selected_case",
]
