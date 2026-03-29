"""Structured summary builders for submarine result reporting."""

from __future__ import annotations

from pathlib import Path

from .artifact_store import (
    load_first_json_payload_from_artifacts,
    resolve_outputs_artifact,
)
from .experiment_linkage import build_experiment_linkage_assessment
from .figure_delivery import build_figure_delivery_summary as _build_figure_delivery_from_manifest
from .library import load_case_library
from .models import SubmarineCase

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


def _study_type_to_requirement_id(study_type: str) -> str:
    return f"{study_type}_study"


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
        studies.append(
            {
                "study_type": study_type,
                "summary_label": definition.get("summary_label"),
                "monitored_quantity": definition.get("monitored_quantity"),
                "variant_count": len([item for item in variants if isinstance(item, dict)]),
                "verification_status": requirement.get("status"),
                "verification_detail": requirement.get("detail"),
            }
        )

    return {
        "selected_case_id": manifest.get("selected_case_id"),
        "study_execution_status": manifest.get("study_execution_status"),
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
        **linkage_assessment,
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
    "build_scientific_study_summary",
    "resolve_outputs_artifact",
    "resolve_selected_case",
]
