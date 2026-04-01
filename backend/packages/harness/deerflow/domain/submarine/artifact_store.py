"""Shared outputs-artifact resolution and canonical submarine artifact helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path


_OUTPUTS_PREFIX = "/mnt/user-data/outputs/"
_SOLVER_DISPATCH_PREFIX = "/mnt/user-data/outputs/submarine/solver-dispatch/"
_REQUEST_FILENAME = "openfoam-request.json"
_DISPATCH_SUMMARY_MARKDOWN_FILENAME = "dispatch-summary.md"
_DISPATCH_SUMMARY_HTML_FILENAME = "dispatch-summary.html"
_SUPERVISOR_HANDOFF_FILENAME = "supervisor-handoff.json"
_EXECUTION_LOG_FILENAME = "openfoam-run.log"
_SOLVER_RESULTS_JSON_FILENAME = "solver-results.json"
_SOLVER_RESULTS_MARKDOWN_FILENAME = "solver-results.md"
_STABILITY_EVIDENCE_FILENAME = "stability-evidence.json"
_STUDY_PLAN_FILENAME = "study-plan.json"
_STUDY_MANIFEST_FILENAME = "study-manifest.json"


def resolve_outputs_artifact(outputs_dir: Path, virtual_path: str) -> Path | None:
    if not virtual_path.startswith(_OUTPUTS_PREFIX):
        return None
    relative_parts = [
        part for part in virtual_path.removeprefix(_OUTPUTS_PREFIX).split("/") if part
    ]
    return outputs_dir.joinpath(*relative_parts)


def read_json_mapping(path: Path) -> dict | None:
    if not path.exists() or path.suffix.lower() != ".json":
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    return dict(payload)


def load_json_outputs_artifact(outputs_dir: Path, virtual_path: str) -> dict | None:
    local_path = resolve_outputs_artifact(outputs_dir, virtual_path)
    if local_path is None:
        return None
    return read_json_mapping(local_path)


def load_json_payloads_from_artifacts(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: Sequence[str],
    suffixes: Sequence[str],
) -> list[tuple[str, dict]]:
    payloads: list[tuple[str, dict]] = []
    for artifact_virtual_path in artifact_virtual_paths:
        if not any(artifact_virtual_path.endswith(suffix) for suffix in suffixes):
            continue
        payload = load_json_outputs_artifact(outputs_dir, artifact_virtual_path)
        if payload is not None:
            payloads.append((artifact_virtual_path, payload))
    return payloads


def load_first_json_payload_from_artifacts(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: Sequence[str],
    suffixes: Sequence[str],
) -> tuple[str, dict] | None:
    payloads = load_json_payloads_from_artifacts(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=artifact_virtual_paths,
        suffixes=suffixes,
    )
    return payloads[0] if payloads else None


def dedupe_virtual_paths(paths: Sequence[str]) -> list[str]:
    merged: list[str] = []
    for path in paths:
        if isinstance(path, str) and path and path not in merged:
            merged.append(path)
    return merged


def build_solver_dispatch_artifact_virtual_path(run_dir_name: str, filename: str) -> str:
    return f"{_SOLVER_DISPATCH_PREFIX}{run_dir_name}/{filename}"


def build_canonical_solver_dispatch_artifact_bundle(
    *,
    run_dir_name: str,
    include_scientific_study_plan: bool = False,
    execution_log_virtual_path: str | None = None,
    solver_results_virtual_path: str | None = None,
    solver_results_markdown_virtual_path: str | None = None,
    stability_evidence_virtual_path: str | None = None,
    requested_postprocess_artifacts: Sequence[str] | None = None,
    scientific_study_artifacts: Sequence[str] | None = None,
    experiment_artifacts: Sequence[str] | None = None,
) -> list[str]:
    bundle: list[str] = [
        build_solver_dispatch_artifact_virtual_path(
            run_dir_name,
            _DISPATCH_SUMMARY_MARKDOWN_FILENAME,
        ),
        build_solver_dispatch_artifact_virtual_path(
            run_dir_name,
            _DISPATCH_SUMMARY_HTML_FILENAME,
        ),
        build_solver_dispatch_artifact_virtual_path(run_dir_name, _REQUEST_FILENAME),
        build_solver_dispatch_artifact_virtual_path(
            run_dir_name,
            _SUPERVISOR_HANDOFF_FILENAME,
        ),
    ]
    if include_scientific_study_plan:
        bundle.extend(
            [
                build_solver_dispatch_artifact_virtual_path(
                    run_dir_name,
                    _STUDY_PLAN_FILENAME,
                ),
                build_solver_dispatch_artifact_virtual_path(
                    run_dir_name,
                    _STUDY_MANIFEST_FILENAME,
                ),
            ]
        )
    if execution_log_virtual_path:
        bundle.append(execution_log_virtual_path)
    if solver_results_virtual_path:
        bundle.append(solver_results_virtual_path)
    if solver_results_markdown_virtual_path:
        bundle.append(solver_results_markdown_virtual_path)
    if stability_evidence_virtual_path:
        bundle.append(stability_evidence_virtual_path)
    bundle.extend(requested_postprocess_artifacts or [])
    bundle.extend(scientific_study_artifacts or [])
    bundle.extend(experiment_artifacts or [])
    return dedupe_virtual_paths(bundle)


def resolve_canonical_solver_dispatch_artifact(
    *,
    artifact_virtual_paths: Sequence[str],
    explicit_virtual_path: str | None = None,
    filename: str,
) -> str | None:
    if explicit_virtual_path:
        return explicit_virtual_path

    suffix = f"/{filename}"
    for path in artifact_virtual_paths:
        if isinstance(path, str) and path.endswith(suffix):
            return path
    return None


def load_canonical_solver_dispatch_request_payload(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: Sequence[str],
    request_virtual_path: str | None = None,
) -> tuple[str, dict] | None:
    resolved_virtual_path = resolve_canonical_solver_dispatch_artifact(
        artifact_virtual_paths=artifact_virtual_paths,
        explicit_virtual_path=request_virtual_path,
        filename=_REQUEST_FILENAME,
    )
    if resolved_virtual_path is None:
        return None

    payload = load_json_outputs_artifact(outputs_dir, resolved_virtual_path)
    if payload is None:
        return None
    return resolved_virtual_path, payload


def load_canonical_solver_results_payload(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: Sequence[str],
    solver_results_virtual_path: str | None = None,
) -> tuple[str, dict] | None:
    resolved_virtual_path = resolve_canonical_solver_dispatch_artifact(
        artifact_virtual_paths=artifact_virtual_paths,
        explicit_virtual_path=solver_results_virtual_path,
        filename=_SOLVER_RESULTS_JSON_FILENAME,
    )
    if resolved_virtual_path is None:
        return None

    payload = load_json_outputs_artifact(outputs_dir, resolved_virtual_path)
    if payload is None:
        return None
    return resolved_virtual_path, payload


def load_canonical_stability_evidence_payload(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: Sequence[str],
    stability_evidence_virtual_path: str | None = None,
) -> tuple[str, dict] | None:
    resolved_virtual_path = resolve_canonical_solver_dispatch_artifact(
        artifact_virtual_paths=artifact_virtual_paths,
        explicit_virtual_path=stability_evidence_virtual_path,
        filename=_STABILITY_EVIDENCE_FILENAME,
    )
    if resolved_virtual_path is None:
        return None

    payload = load_json_outputs_artifact(outputs_dir, resolved_virtual_path)
    if payload is None:
        return None
    return resolved_virtual_path, payload


__all__ = [
    "build_canonical_solver_dispatch_artifact_bundle",
    "build_solver_dispatch_artifact_virtual_path",
    "dedupe_virtual_paths",
    "load_canonical_solver_dispatch_request_payload",
    "load_canonical_solver_results_payload",
    "load_canonical_stability_evidence_payload",
    "load_first_json_payload_from_artifacts",
    "load_json_outputs_artifact",
    "load_json_payloads_from_artifacts",
    "read_json_mapping",
    "resolve_canonical_solver_dispatch_artifact",
    "resolve_outputs_artifact",
]
