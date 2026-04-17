"""Canonical provenance-manifest helpers for submarine CFD runs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .models import (
    SubmarineRunProvenanceManifest,
    SubmarineRunProvenanceManifestCompletenessStatus,
)

_REQUIRED_MANIFEST_FIELDS = (
    "manifest_version",
    "experiment_id",
    "run_id",
    "task_type",
    "geometry_virtual_path",
    "requested_output_ids",
    "simulation_requirements_snapshot",
    "approval_snapshot",
    "artifact_entrypoints",
    "environment_fingerprint",
    "environment_parity_assessment",
)


def _as_mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return dumped
    return {}


def _dedupe_requested_output_ids(requested_outputs: Sequence[Mapping[str, Any] | dict] | None) -> list[str]:
    requested_output_ids: list[str] = []
    for item in requested_outputs or []:
        output_id = str(_as_mapping(item).get("output_id") or "").strip()
        if output_id and output_id not in requested_output_ids:
            requested_output_ids.append(output_id)
    return requested_output_ids


def _normalize_file_sources(
    file_sources: object | None,
) -> dict[str, dict[str, Any]]:
    if not isinstance(file_sources, Mapping):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for relative_path, source in file_sources.items():
        if not isinstance(relative_path, str):
            continue
        dumped = _as_mapping(source)
        normalized[relative_path] = {
            "source_commit": dumped.get("source_commit"),
            "source_path": dumped.get("source_path"),
            "source_kind": dumped.get("source_kind"),
            "imported_virtual_path": dumped.get("imported_virtual_path"),
        }
    return normalized


def build_provenance_approval_snapshot(
    *,
    confirmation_status: str,
    review_status: str,
    next_recommended_stage: str,
    pending_calculation_plan: bool,
    requires_immediate_confirmation: bool,
    selected_reference_inputs: Mapping[str, Any] | None,
) -> dict[str, object]:
    snapshot: dict[str, object] = {
        "confirmation_status": confirmation_status,
        "review_status": review_status,
        "next_recommended_stage": next_recommended_stage,
        "pending_calculation_plan": pending_calculation_plan,
        "requires_immediate_confirmation": requires_immediate_confirmation,
    }
    if selected_reference_inputs:
        snapshot["selected_reference_inputs"] = dict(selected_reference_inputs)
    return snapshot


def build_run_provenance_manifest(
    *,
    experiment_id: str,
    run_id: str,
    task_type: str,
    input_source_type: str = "geometry_seed",
    geometry_virtual_path: str,
    geometry_family: str | None,
    official_case_id: str | None = None,
    official_case_seed_virtual_paths: Sequence[str] | None = None,
    assembled_case_virtual_paths: Sequence[str] | None = None,
    selected_case_id: str | None,
    file_sources: Mapping[str, Any] | None = None,
    requested_outputs: Sequence[Mapping[str, Any] | dict] | None,
    simulation_requirements: Mapping[str, Any] | None,
    approval_snapshot: Mapping[str, Any] | None,
    artifact_entrypoints: Mapping[str, str] | None,
    environment_fingerprint: Mapping[str, Any] | None,
    environment_parity_assessment: Mapping[str, Any] | None,
) -> SubmarineRunProvenanceManifest:
    return SubmarineRunProvenanceManifest(
        experiment_id=experiment_id,
        run_id=run_id,
        task_type=task_type,
        input_source_type=input_source_type,
        geometry_virtual_path=geometry_virtual_path,
        geometry_family=geometry_family,
        official_case_id=official_case_id,
        official_case_seed_virtual_paths=list(official_case_seed_virtual_paths or []),
        assembled_case_virtual_paths=list(assembled_case_virtual_paths or []),
        selected_case_id=selected_case_id,
        requested_output_ids=_dedupe_requested_output_ids(requested_outputs),
        file_sources=dict(file_sources or {}),
        simulation_requirements_snapshot=dict(simulation_requirements or {}),
        approval_snapshot=dict(approval_snapshot or {}),
        artifact_entrypoints=dict(artifact_entrypoints or {}),
        environment_fingerprint=environment_fingerprint or {},
        environment_parity_assessment=environment_parity_assessment or {},
    )


def determine_provenance_manifest_completeness(
    manifest_payload: Mapping[str, Any] | None,
) -> SubmarineRunProvenanceManifestCompletenessStatus:
    manifest = _as_mapping(manifest_payload)
    has_required_fields = all(field in manifest for field in _REQUIRED_MANIFEST_FIELDS)
    input_source_type = str(manifest.get("input_source_type") or "").strip()
    has_effective_input_source = bool(
        input_source_type
        or not manifest.get("official_case_id")
    )
    file_sources = _normalize_file_sources(manifest.get("file_sources"))
    has_official_case_requirements = True
    if input_source_type == "openfoam_case_seed":
        has_official_case_requirements = bool(
            isinstance(manifest.get("official_case_id"), str)
            and str(manifest.get("official_case_id")).strip()
            and list(manifest.get("official_case_seed_virtual_paths") or [])
            and file_sources
        )
    artifact_entrypoints = _as_mapping(manifest.get("artifact_entrypoints"))
    has_primary_entrypoints = all(isinstance(artifact_entrypoints.get(key), str) and artifact_entrypoints.get(key) for key in ("request", "dispatch_summary_markdown", "dispatch_summary_html"))
    if (
        has_required_fields
        and has_effective_input_source
        and has_official_case_requirements
        and has_primary_entrypoints
    ):
        return "complete"
    return "partial"


def build_provenance_summary(
    *,
    manifest_virtual_path: str,
    manifest_payload: Mapping[str, Any] | None,
) -> dict[str, object]:
    manifest = _as_mapping(manifest_payload)
    artifact_entrypoints = {key: str(value) for key, value in _as_mapping(manifest.get("artifact_entrypoints")).items() if isinstance(value, str) and value}
    return {
        "manifest_virtual_path": manifest_virtual_path,
        "run_id": manifest.get("run_id"),
        "experiment_id": manifest.get("experiment_id"),
        "input_source_type": manifest.get("input_source_type") or "geometry_seed",
        "geometry_virtual_path": manifest.get("geometry_virtual_path"),
        "official_case_id": manifest.get("official_case_id"),
        "official_case_seed_virtual_paths": list(manifest.get("official_case_seed_virtual_paths") or []),
        "assembled_case_virtual_paths": list(manifest.get("assembled_case_virtual_paths") or []),
        "file_sources": _normalize_file_sources(manifest.get("file_sources")),
        "selected_case_id": manifest.get("selected_case_id"),
        "requested_output_ids": list(manifest.get("requested_output_ids") or []),
        "artifact_entrypoints": artifact_entrypoints,
        "profile_id": _as_mapping(manifest.get("environment_fingerprint")).get("profile_id"),
        "parity_status": _as_mapping(manifest.get("environment_parity_assessment")).get("parity_status"),
        "drift_reasons": list(_as_mapping(manifest.get("environment_parity_assessment")).get("drift_reasons") or []),
        "recovery_guidance": list(_as_mapping(manifest.get("environment_parity_assessment")).get("recovery_guidance") or []),
        "manifest_completeness_status": determine_provenance_manifest_completeness(manifest),
    }


__all__ = [
    "build_provenance_approval_snapshot",
    "build_provenance_summary",
    "build_run_provenance_manifest",
    "determine_provenance_manifest_completeness",
]
