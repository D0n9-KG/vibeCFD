"""Submarine result reporting and final artifact generation."""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

from .contracts import SubmarineRuntimeSnapshot, build_supervisor_review_contract
from .evidence import build_research_evidence_summary
from .library import load_case_library
from .models import SubmarineBenchmarkTarget, SubmarineCase
from .output_contract import build_output_delivery_plan
from .verification import (
    build_effective_scientific_verification_requirements,
    build_scientific_verification_assessment,
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "submarine-report"


def _artifact_virtual_path(run_dir_name: str, filename: str) -> str:
    return f"/mnt/user-data/outputs/submarine/reports/{run_dir_name}/{filename}"


def _resolve_outputs_artifact(outputs_dir: Path, virtual_path: str) -> Path | None:
    prefix = "/mnt/user-data/outputs/"
    if not virtual_path.startswith(prefix):
        return None
    relative_parts = [part for part in virtual_path.removeprefix(prefix).split("/") if part]
    return outputs_dir.joinpath(*relative_parts)


def _load_json_payload_from_artifacts(
    outputs_dir: Path,
    artifact_virtual_paths: list[str],
    suffix: str,
) -> tuple[str, dict] | None:
    for artifact_virtual_path in artifact_virtual_paths:
        if not artifact_virtual_path.endswith(suffix):
            continue
        local_path = _resolve_outputs_artifact(outputs_dir, artifact_virtual_path)
        if local_path is None or not local_path.exists():
            continue
        try:
            payload = json.loads(local_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            return artifact_virtual_path, payload
    return None


def _merge_artifact_paths(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for path in group:
            if path not in merged:
                merged.append(path)
    return merged


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _format_float(value: object, digits: int = 1) -> str:
    if not _is_number(value):
        return "unknown"
    return f"{float(value):.{digits}f}"


def _format_percent(value: object, digits: int = 1) -> str:
    if not _is_number(value):
        return "unknown"
    return f"{float(value) * 100:.{digits}f}%"


def _resolve_selected_case(selected_case_id: str | None) -> SubmarineCase | None:
    if not selected_case_id:
        return None
    return load_case_library().case_index.get(selected_case_id)


def _study_type_to_requirement_id(study_type: str) -> str:
    return f"{study_type}_study"


def _build_scientific_study_summary(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: list[str],
    scientific_verification_assessment: dict | None,
) -> dict | None:
    loaded = _load_json_payload_from_artifacts(
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


def _build_experiment_summary(
    *,
    outputs_dir: Path,
    artifact_virtual_paths: list[str],
) -> dict | None:
    manifest_loaded = _load_json_payload_from_artifacts(
        outputs_dir,
        artifact_virtual_paths,
        "experiment-manifest.json",
    )
    if manifest_loaded is None:
        return None

    manifest_virtual_path, manifest = manifest_loaded
    compare_loaded = _load_json_payload_from_artifacts(
        outputs_dir,
        artifact_virtual_paths,
        "run-compare-summary.json",
    )
    compare_virtual_path = compare_loaded[0] if compare_loaded is not None else None
    compare_summary = compare_loaded[1] if compare_loaded is not None else {}
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
        "manifest_virtual_path": manifest_virtual_path,
        "compare_virtual_path": compare_virtual_path,
        "artifact_virtual_paths": manifest.get("artifact_virtual_paths")
        or [manifest_virtual_path],
        "compare_count": len([item for item in comparisons if isinstance(item, dict)]),
        "compare_notes": compare_notes,
    }


def _has_required_artifact(artifact_virtual_paths: list[str], required_artifact: str) -> bool:
    return any(path.endswith(required_artifact) for path in artifact_virtual_paths)


def _resolve_benchmark_observed_value(
    benchmark_target: SubmarineBenchmarkTarget,
    solver_metrics: dict,
) -> float | None:
    quantity = benchmark_target.quantity.strip().lower()
    latest_force_coefficients = solver_metrics.get("latest_force_coefficients") or {}
    coefficient_map = {
        "cd": latest_force_coefficients.get("Cd"),
        "cl": latest_force_coefficients.get("Cl"),
        "cs": latest_force_coefficients.get("Cs"),
        "cmpitch": latest_force_coefficients.get("CmPitch"),
    }
    value = coefficient_map.get(quantity)
    if _is_number(value):
        return float(value)
    return None


def _evaluate_benchmark_target(
    benchmark_target: SubmarineBenchmarkTarget,
    solver_metrics: dict,
) -> dict | None:
    simulation_requirements = solver_metrics.get("simulation_requirements") or {}
    inlet_velocity = simulation_requirements.get("inlet_velocity_mps")
    if benchmark_target.inlet_velocity_mps is not None:
        if not _is_number(inlet_velocity):
            detail = (
                f"Benchmark {benchmark_target.metric_id} requires inlet_velocity_mps "
                f"{benchmark_target.inlet_velocity_mps:.2f}, but the solver run did not record it."
            )
            return {
                "metric_id": benchmark_target.metric_id,
                "quantity": benchmark_target.quantity,
                "status": benchmark_target.on_miss_status,
                "detail": detail,
                "reference_value": benchmark_target.reference_value,
                "observed_value": None,
                "absolute_error": None,
                "relative_error": None,
                "relative_tolerance": benchmark_target.relative_tolerance,
                "target_inlet_velocity_mps": benchmark_target.inlet_velocity_mps,
                "observed_inlet_velocity_mps": None,
                "source_label": benchmark_target.source_label,
                "source_url": benchmark_target.source_url,
            }
        if abs(float(inlet_velocity) - benchmark_target.inlet_velocity_mps) > benchmark_target.velocity_tolerance_mps:
            return None

    observed_value = _resolve_benchmark_observed_value(benchmark_target, solver_metrics)
    if observed_value is None:
        detail = (
            f"Benchmark {benchmark_target.metric_id} applies to this run, but observed "
            f"{benchmark_target.quantity} is unavailable."
        )
        return {
            "metric_id": benchmark_target.metric_id,
            "quantity": benchmark_target.quantity,
            "status": benchmark_target.on_miss_status,
            "detail": detail,
            "reference_value": benchmark_target.reference_value,
            "observed_value": None,
            "absolute_error": None,
            "relative_error": None,
            "relative_tolerance": benchmark_target.relative_tolerance,
            "target_inlet_velocity_mps": benchmark_target.inlet_velocity_mps,
            "observed_inlet_velocity_mps": float(inlet_velocity) if _is_number(inlet_velocity) else None,
            "source_label": benchmark_target.source_label,
            "source_url": benchmark_target.source_url,
        }

    reference_value = float(benchmark_target.reference_value)
    absolute_error = abs(observed_value - reference_value)
    relative_error = (
        absolute_error / abs(reference_value)
        if reference_value != 0.0
        else 0.0
    )
    passed = relative_error <= benchmark_target.relative_tolerance
    status = "passed" if passed else benchmark_target.on_miss_status
    detail = (
        f"Benchmark {benchmark_target.metric_id} observed {benchmark_target.quantity} "
        f"{observed_value:.5f} vs reference {reference_value:.5f}; relative error "
        f"{_format_percent(relative_error)} with tolerance {_format_percent(benchmark_target.relative_tolerance)}."
    )
    return {
        "metric_id": benchmark_target.metric_id,
        "quantity": benchmark_target.quantity,
        "status": status,
        "detail": detail,
        "reference_value": reference_value,
        "observed_value": observed_value,
        "absolute_error": absolute_error,
        "relative_error": relative_error,
        "relative_tolerance": benchmark_target.relative_tolerance,
        "target_inlet_velocity_mps": benchmark_target.inlet_velocity_mps,
        "observed_inlet_velocity_mps": float(inlet_velocity) if _is_number(inlet_velocity) else None,
        "source_label": benchmark_target.source_label,
        "source_url": benchmark_target.source_url,
    }


def _build_acceptance_assessment(
    snapshot: SubmarineRuntimeSnapshot,
    solver_metrics: dict | None,
    *,
    selected_case: SubmarineCase | None = None,
    artifact_virtual_paths: list[str] | None = None,
) -> dict:
    gates: list[dict[str, str]] = []
    blocking_issues: list[str] = []
    warnings: list[str] = []
    passed_checks: list[str] = []
    benchmark_comparisons: list[dict] = []
    merged_artifact_virtual_paths = artifact_virtual_paths or snapshot.artifact_virtual_paths

    def add_gate(*, gate_id: str, label: str, status: str, detail: str) -> None:
        gates.append(
            {
                "id": gate_id,
                "label": label,
                "status": status,
                "detail": detail,
            }
        )

    if not solver_metrics:
        message = "Solver metrics are unavailable for this run."
        blocking_issues.append(message)
        add_gate(
            gate_id="solver_metrics_available",
            label="Solver metrics captured",
            status="blocked",
            detail=message,
        )
        return {
            "status": "blocked",
            "confidence": "low",
            "gate_count": len(gates),
            "blocking_issues": blocking_issues,
            "warnings": warnings,
            "passed_checks": passed_checks,
            "gates": gates,
        }

    solver_completed = bool(solver_metrics.get("solver_completed"))
    if solver_completed:
        detail = "Solver completed successfully."
        passed_checks.append(detail)
        add_gate(
            gate_id="solver_completed",
            label="Solver completed",
            status="passed",
            detail=detail,
        )
    else:
        detail = "Solver did not complete successfully."
        blocking_issues.append(detail)
        add_gate(
            gate_id="solver_completed",
            label="Solver completed",
            status="blocked",
            detail=detail,
        )

    mesh_summary = solver_metrics.get("mesh_summary") or {}
    mesh_ok = mesh_summary.get("mesh_ok")
    if mesh_ok is True:
        detail = "Mesh quality checks passed."
        passed_checks.append(detail)
        add_gate(
            gate_id="mesh_quality_ok",
            label="Mesh quality",
            status="passed",
            detail=detail,
        )
    elif mesh_summary:
        detail = "Mesh quality checks did not pass."
        blocking_issues.append(detail)
        add_gate(
            gate_id="mesh_quality_ok",
            label="Mesh quality",
            status="blocked",
            detail=detail,
        )
    else:
        detail = "Mesh quality summary is missing from solver artifacts."
        warnings.append(detail)
        add_gate(
            gate_id="mesh_quality_ok",
            label="Mesh quality",
            status="warning",
            detail=detail,
        )

    residual_summary = solver_metrics.get("residual_summary") or {}
    field_count = residual_summary.get("field_count")
    max_final_residual = residual_summary.get("max_final_residual")
    if _is_number(field_count) and int(field_count) > 0 and _is_number(max_final_residual):
        if float(max_final_residual) <= 1e-3:
            detail = "Residual summary captured with acceptable final residuals."
            passed_checks.append(detail)
            add_gate(
                gate_id="residuals_available",
                label="Residual convergence",
                status="passed",
                detail=detail,
            )
        else:
            detail = (
                "Residual summary captured, but max_final_residual "
                f"{max_final_residual} needs supervisor review."
            )
            warnings.append(detail)
            add_gate(
                gate_id="residuals_available",
                label="Residual convergence",
                status="warning",
                detail=detail,
            )
    else:
        detail = "Residual summary is missing from solver artifacts."
        warnings.append(detail)
        add_gate(
            gate_id="residuals_available",
            label="Residual convergence",
            status="warning",
            detail=detail,
        )

    simulation_requirements = (
        (solver_metrics.get("simulation_requirements") or {})
        or (snapshot.simulation_requirements or {})
    )
    planned_end_time = simulation_requirements.get("end_time_seconds")
    final_time = solver_metrics.get("final_time_seconds")
    if _is_number(planned_end_time) and _is_number(final_time):
        if float(final_time) >= float(planned_end_time):
            detail = "Solver reached the planned end_time_seconds target."
            passed_checks.append(detail)
            add_gate(
                gate_id="planned_end_time_reached",
                label="Planned end time reached",
                status="passed",
                detail=detail,
            )
        else:
            detail = (
                f"Solver final time {_format_float(final_time)} is below planned "
                f"end_time_seconds {_format_float(planned_end_time)}."
            )
            warnings.append(detail)
            add_gate(
                gate_id="planned_end_time_reached",
                label="Planned end time reached",
                status="warning",
                detail=detail,
            )
    else:
        detail = "Unable to compare solver final time against planned end_time_seconds."
        warnings.append(detail)
        add_gate(
            gate_id="planned_end_time_reached",
            label="Planned end time reached",
            status="warning",
            detail=detail,
        )

    latest_force_coefficients = solver_metrics.get("latest_force_coefficients") or {}
    if _is_number(latest_force_coefficients.get("Cd")):
        detail = "Force coefficients are available for review."
        passed_checks.append(detail)
        add_gate(
            gate_id="force_coefficients_available",
            label="Force coefficients available",
            status="passed",
            detail=detail,
        )
    else:
        detail = "Force coefficients are missing from solver artifacts."
        warnings.append(detail)
        add_gate(
            gate_id="force_coefficients_available",
            label="Force coefficients available",
            status="warning",
            detail=detail,
        )

    if snapshot.execution_readiness == "stl_ready" and snapshot.selected_case_id:
        detail = "The run kept the STL-only v1 boundary and selected a case template."
        passed_checks.append(detail)
        add_gate(
            gate_id="stl_runtime_contract",
            label="STL runtime contract",
            status="passed",
            detail=detail,
        )
    else:
        detail = "Runtime readiness or selected_case_id is incomplete for supervisor review."
        warnings.append(detail)
        add_gate(
            gate_id="stl_runtime_contract",
            label="STL runtime contract",
            status="warning",
            detail=detail,
        )

    acceptance_profile = selected_case.acceptance_profile if selected_case else None
    if acceptance_profile:
        if acceptance_profile.required_artifacts:
            missing_artifacts = [
                artifact_name
                for artifact_name in acceptance_profile.required_artifacts
                if not _has_required_artifact(merged_artifact_virtual_paths, artifact_name)
            ]
            if missing_artifacts:
                detail = (
                    f"Case profile {acceptance_profile.profile_id} is missing required artifacts: "
                    + ", ".join(missing_artifacts)
                )
                blocking_issues.append(detail)
                add_gate(
                    gate_id="case_required_artifacts",
                    label="Case required artifacts",
                    status="blocked",
                    detail=detail,
                )
            else:
                detail = (
                    f"Case profile {acceptance_profile.profile_id} required artifacts are present."
                )
                passed_checks.append(detail)
                add_gate(
                    gate_id="case_required_artifacts",
                    label="Case required artifacts",
                    status="passed",
                    detail=detail,
                )

        if acceptance_profile.minimum_completed_fraction_of_planned_time is not None:
            planned_end_time = (
                (solver_metrics.get("simulation_requirements") or {}).get("end_time_seconds")
                if solver_metrics
                else None
            )
            final_time = solver_metrics.get("final_time_seconds") if solver_metrics else None
            if _is_number(planned_end_time) and float(planned_end_time) > 0 and _is_number(final_time):
                completed_fraction = float(final_time) / float(planned_end_time)
                if completed_fraction >= acceptance_profile.minimum_completed_fraction_of_planned_time:
                    detail = (
                        f"Case profile {acceptance_profile.profile_id} completed_fraction "
                        f"{completed_fraction:.3f} meets the threshold "
                        f"{acceptance_profile.minimum_completed_fraction_of_planned_time:.3f}."
                    )
                    passed_checks.append(detail)
                    add_gate(
                        gate_id="case_completed_fraction",
                        label="Case completed fraction",
                        status="passed",
                        detail=detail,
                    )
                else:
                    detail = (
                        f"Case profile {acceptance_profile.profile_id} completed_fraction "
                        f"{completed_fraction:.3f} is below the threshold "
                        f"{acceptance_profile.minimum_completed_fraction_of_planned_time:.3f}."
                    )
                    warnings.append(detail)
                    add_gate(
                        gate_id="case_completed_fraction",
                        label="Case completed fraction",
                        status="warning",
                        detail=detail,
                    )

        if acceptance_profile.max_final_residual is not None:
            residual_summary = solver_metrics.get("residual_summary") or {} if solver_metrics else {}
            max_final_residual = residual_summary.get("max_final_residual")
            if _is_number(max_final_residual):
                if float(max_final_residual) <= acceptance_profile.max_final_residual:
                    detail = (
                        f"Case profile {acceptance_profile.profile_id} max_final_residual "
                        f"{float(max_final_residual):.6f} is within the threshold "
                        f"{acceptance_profile.max_final_residual:.6f}."
                    )
                    passed_checks.append(detail)
                    add_gate(
                        gate_id="case_max_final_residual",
                        label="Case max final residual",
                        status="passed",
                        detail=detail,
                    )
                else:
                    detail = (
                        f"Case profile {acceptance_profile.profile_id} max_final_residual "
                        f"{float(max_final_residual):.6f} exceeds the threshold "
                        f"{acceptance_profile.max_final_residual:.6f}."
                    )
                    blocking_issues.append(detail)
                    add_gate(
                        gate_id="case_max_final_residual",
                        label="Case max final residual",
                        status="blocked",
                        detail=detail,
                    )

        for benchmark_target in acceptance_profile.benchmark_targets:
            comparison = _evaluate_benchmark_target(benchmark_target, solver_metrics)
            if comparison is None:
                continue
            benchmark_comparisons.append(comparison)
            detail = comparison["detail"]
            status = comparison["status"]
            if status == "passed":
                passed_checks.append(detail)
            elif status == "blocked":
                blocking_issues.append(detail)
            else:
                warnings.append(detail)
            target_velocity = benchmark_target.inlet_velocity_mps
            label_suffix = (
                f" @ {target_velocity:.2f} m/s"
                if target_velocity is not None
                else ""
            )
            add_gate(
                gate_id=f"benchmark_{benchmark_target.metric_id}",
                label=f"Benchmark {benchmark_target.quantity}{label_suffix}",
                status=status,
                detail=detail,
            )

    status = "blocked" if blocking_issues else "ready_for_review"
    if blocking_issues:
        confidence = "low"
    elif warnings:
        confidence = "medium"
    else:
        confidence = "high"

    return {
        "status": status,
        "confidence": confidence,
        "gate_count": len(gates),
        "blocking_issues": blocking_issues,
        "warnings": warnings,
        "passed_checks": passed_checks,
        "benchmark_comparisons": benchmark_comparisons,
        "gates": gates,
    }


def _render_acceptance_markdown(acceptance_assessment: dict | None) -> list[str]:
    if not acceptance_assessment:
        return []

    lines = [
        "",
        "## Delivery Readiness",
        f"- status: `{acceptance_assessment.get('status')}`",
        f"- confidence: `{acceptance_assessment.get('confidence')}`",
        f"- gate_count: `{acceptance_assessment.get('gate_count')}`",
    ]

    gates = acceptance_assessment.get("gates") or []
    if gates:
        lines.extend(["", "### Gates"])
        lines.extend(
            f"- `{gate.get('id')}` | `{gate.get('status')}` | {gate.get('detail')}"
            for gate in gates
        )

    blocking_issues = acceptance_assessment.get("blocking_issues") or []
    if blocking_issues:
        lines.extend(["", "### Blocking Issues"])
        lines.extend(f"- {item}" for item in blocking_issues)

    warnings = acceptance_assessment.get("warnings") or []
    if warnings:
        lines.extend(["", "### Warnings"])
        lines.extend(f"- {item}" for item in warnings)

    passed_checks = acceptance_assessment.get("passed_checks") or []
    if passed_checks:
        lines.extend(["", "### Passed Checks"])
        lines.extend(f"- {item}" for item in passed_checks)

    benchmark_comparisons = acceptance_assessment.get("benchmark_comparisons") or []
    if benchmark_comparisons:
        lines.extend(["", "### Benchmark Comparisons"])
        lines.extend(
            "- "
            + " | ".join(
                [
                    f"`{item.get('metric_id')}`",
                    f"`{item.get('status')}`",
                    f"observed={item.get('observed_value')}",
                    f"reference={item.get('reference_value')}",
                    f"rel_error={_format_percent(item.get('relative_error'))}",
                ]
            )
            for item in benchmark_comparisons
        )

    return lines


def _render_delivery_readiness_markdown(
    report_title: str,
    acceptance_assessment: dict,
) -> str:
    lines = [
        f"# Delivery Readiness · {report_title}",
        "",
        "This artifact summarizes whether the current submarine CFD run is ready for supervisor review.",
    ]
    lines.extend(_render_acceptance_markdown(acceptance_assessment))
    lines.append("")
    return "\n".join(lines)


def _render_output_delivery_markdown(output_delivery_plan: list[dict] | None) -> list[str]:
    if not output_delivery_plan:
        return []

    lines = ["", "## Requested Output Delivery"]
    lines.extend(
        (
            "- "
            + " | ".join(
                [
                    f"`{item.get('output_id')}`",
                    f"`{item.get('delivery_status')}`",
                    str(item.get("detail") or "No detail"),
                ]
            )
        )
        for item in output_delivery_plan
    )
    return lines


def _render_acceptance_html(acceptance_assessment: dict | None) -> str:
    if not acceptance_assessment:
        return ""

    def render_items(items: list[str]) -> str:
        if not items:
            return "<li>None</li>"
        return "".join(f"<li>{escape(item)}</li>" for item in items)

    gates = acceptance_assessment.get("gates") or []
    gate_items = "".join(
        "<li>"
        f"<strong>{escape(str(gate.get('label')))}</strong> "
        f"({escape(str(gate.get('status')))})"
        f"<p>{escape(str(gate.get('detail')))}</p>"
        "</li>"
        for gate in gates
    ) or "<li>None</li>"

    return (
        '<section class="panel">'
        "<h2>Delivery Readiness</h2>"
        f"<p><strong>status:</strong> {escape(str(acceptance_assessment.get('status')))}</p>"
        f"<p><strong>confidence:</strong> {escape(str(acceptance_assessment.get('confidence')))}</p>"
        f"<p><strong>gate_count:</strong> {escape(str(acceptance_assessment.get('gate_count')))}</p>"
        "<h3>Gates</h3>"
        f"<ul>{gate_items}</ul>"
        "<h3>Blocking Issues</h3>"
        f"<ul>{render_items(acceptance_assessment.get('blocking_issues') or [])}</ul>"
        "<h3>Warnings</h3>"
        f"<ul>{render_items(acceptance_assessment.get('warnings') or [])}</ul>"
        "<h3>Passed Checks</h3>"
        f"<ul>{render_items(acceptance_assessment.get('passed_checks') or [])}</ul>"
        "<h3>Benchmark Comparisons</h3>"
        "<ul>"
        + (
            "".join(
                "<li>"
                f"<strong>{escape(str(item.get('metric_id')))}</strong> "
                f"({escape(str(item.get('status')))})"
                f"<p>observed={escape(str(item.get('observed_value')))}, "
                f"reference={escape(str(item.get('reference_value')))}, "
                f"relative_error={escape(_format_percent(item.get('relative_error')))}</p>"
                "</li>"
                for item in (acceptance_assessment.get('benchmark_comparisons') or [])
            )
            or "<li>None</li>"
        )
        + "</ul>"
        "</section>"
    )


def _render_output_delivery_html(output_delivery_plan: list[dict] | None) -> str:
    if not output_delivery_plan:
        return ""

    items = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('label') or item.get('output_id')))}</strong> "
        f"(<code>{escape(str(item.get('delivery_status')))}</code>)"
        f"<p>{escape(str(item.get('detail') or 'No detail'))}</p>"
        "</li>"
        for item in output_delivery_plan
    ) or "<li>None</li>"
    return (
        '<section class="panel">'
        "<h2>Requested Output Delivery</h2>"
        f"<ul>{items}</ul>"
        "</section>"
    )


def _render_scientific_study_markdown(scientific_study_summary: dict | None) -> list[str]:
    if not scientific_study_summary:
        return []

    lines = [
        "",
        "## Scientific Studies",
        f"- execution_status: `{scientific_study_summary.get('study_execution_status')}`",
        f"- manifest: `{scientific_study_summary.get('manifest_virtual_path')}`",
    ]
    studies = scientific_study_summary.get("studies") or []
    if studies:
        lines.extend(["", "### Study Summary"])
        lines.extend(
            (
                "- "
                + " | ".join(
                    [
                        f"`{item.get('study_type')}`",
                        f"verification=`{item.get('verification_status')}`",
                        f"variants={item.get('variant_count')}",
                        str(item.get("verification_detail") or "No detail"),
                    ]
                )
            )
            for item in studies
        )

    return lines


def _render_experiment_markdown(experiment_summary: dict | None) -> list[str]:
    if not experiment_summary:
        return []

    lines = [
        "",
        "## Experiment Registry",
        f"- experiment_id: `{experiment_summary.get('experiment_id')}`",
        f"- experiment_status: `{experiment_summary.get('experiment_status')}`",
        f"- baseline_run_id: `{experiment_summary.get('baseline_run_id')}`",
        f"- run_count: `{experiment_summary.get('run_count')}`",
        f"- manifest: `{experiment_summary.get('manifest_virtual_path')}`",
    ]
    if experiment_summary.get("compare_virtual_path"):
        lines.append(
            f"- compare: `{experiment_summary.get('compare_virtual_path')}`"
        )
    compare_notes = experiment_summary.get("compare_notes") or []
    if compare_notes:
        lines.extend(["", "### Compare Summary"])
        lines.extend(f"- {item}" for item in compare_notes)
    return lines


def _render_research_evidence_markdown(research_evidence_summary: dict | None) -> list[str]:
    if not research_evidence_summary:
        return []

    lines = [
        "",
        "## Research Evidence",
        f"- readiness_status: `{research_evidence_summary.get('readiness_status')}`",
        f"- verification_status: `{research_evidence_summary.get('verification_status')}`",
        f"- validation_status: `{research_evidence_summary.get('validation_status')}`",
        f"- provenance_status: `{research_evidence_summary.get('provenance_status')}`",
        f"- confidence: `{research_evidence_summary.get('confidence')}`",
    ]
    passed_evidence = research_evidence_summary.get("passed_evidence") or []
    evidence_gaps = research_evidence_summary.get("evidence_gaps") or []
    if passed_evidence:
        lines.extend(["", "### Passed Evidence"])
        lines.extend(f"- {item}" for item in passed_evidence)
    if evidence_gaps:
        lines.extend(["", "### Evidence Gaps"])
        lines.extend(f"- {item}" for item in evidence_gaps)
    return lines


def _render_scientific_verification_markdown(
    scientific_verification_assessment: dict | None,
) -> list[str]:
    if not scientific_verification_assessment:
        return []

    lines = [
        "",
        "## Scientific Verification",
        f"- status: `{scientific_verification_assessment.get('status')}`",
        f"- confidence: `{scientific_verification_assessment.get('confidence')}`",
        f"- requirement_count: `{scientific_verification_assessment.get('requirement_count')}`",
    ]
    requirements = scientific_verification_assessment.get("requirements") or []
    if requirements:
        lines.extend(["", "### Verification Requirements"])
        lines.extend(
            (
                "- "
                + " | ".join(
                    [
                        f"`{item.get('requirement_id')}`",
                        f"`{item.get('status')}`",
                        str(item.get("detail") or "No detail"),
                    ]
                )
            )
            for item in requirements
        )

    missing_evidence = scientific_verification_assessment.get("missing_evidence") or []
    if missing_evidence:
        lines.extend(["", "### Missing Evidence"])
        lines.extend(f"- {item}" for item in missing_evidence)

    blocking_issues = scientific_verification_assessment.get("blocking_issues") or []
    if blocking_issues:
        lines.extend(["", "### Blocking Issues"])
        lines.extend(f"- {item}" for item in blocking_issues)

    passed_requirements = (
        scientific_verification_assessment.get("passed_requirements") or []
    )
    if passed_requirements:
        lines.extend(["", "### Passed Requirements"])
        lines.extend(f"- {item}" for item in passed_requirements)

    return lines


def _render_scientific_study_html(scientific_study_summary: dict | None) -> str:
    if not scientific_study_summary:
        return ""

    study_items = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('summary_label') or item.get('study_type')))}</strong> "
        f"(<code>{escape(str(item.get('verification_status')))}</code>)"
        f"<p>{escape(str(item.get('verification_detail') or 'No detail'))}</p>"
        "</li>"
        for item in (scientific_study_summary.get("studies") or [])
    ) or "<li>None</li>"

    return (
        '<section class="panel">'
        "<h2>Scientific Studies</h2>"
        f"<p><strong>execution_status:</strong> {escape(str(scientific_study_summary.get('study_execution_status')))}</p>"
        f"<p><strong>manifest:</strong> {escape(str(scientific_study_summary.get('manifest_virtual_path')))}</p>"
        "<h3>Study Summary</h3>"
        f"<ul>{study_items}</ul>"
        "</section>"
    )


def _render_experiment_html(experiment_summary: dict | None) -> str:
    if not experiment_summary:
        return ""

    compare_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (experiment_summary.get("compare_notes") or [])
    ) or "<li>None</li>"
    compare_html = (
        f"<p><strong>compare:</strong> {escape(str(experiment_summary.get('compare_virtual_path')))}</p>"
        if experiment_summary.get("compare_virtual_path")
        else ""
    )
    return (
        '<section class="panel">'
        "<h2>Experiment Registry</h2>"
        f"<p><strong>experiment_id:</strong> {escape(str(experiment_summary.get('experiment_id')))}</p>"
        f"<p><strong>experiment_status:</strong> {escape(str(experiment_summary.get('experiment_status')))}</p>"
        f"<p><strong>baseline_run_id:</strong> {escape(str(experiment_summary.get('baseline_run_id')))}</p>"
        f"<p><strong>run_count:</strong> {escape(str(experiment_summary.get('run_count')))}</p>"
        f"<p><strong>manifest:</strong> {escape(str(experiment_summary.get('manifest_virtual_path')))}</p>"
        f"{compare_html}"
        "<h3>Compare Summary</h3>"
        f"<ul>{compare_items}</ul>"
        "</section>"
    )


def _render_research_evidence_html(research_evidence_summary: dict | None) -> str:
    if not research_evidence_summary:
        return ""

    passed_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (research_evidence_summary.get("passed_evidence") or [])
    ) or "<li>None</li>"
    gap_items = "".join(
        f"<li>{escape(str(item))}</li>"
        for item in (research_evidence_summary.get("evidence_gaps") or [])
    ) or "<li>None</li>"
    return (
        '<section class="panel">'
        "<h2>Research Evidence</h2>"
        f"<p><strong>readiness_status:</strong> {escape(str(research_evidence_summary.get('readiness_status')))}</p>"
        f"<p><strong>verification_status:</strong> {escape(str(research_evidence_summary.get('verification_status')))}</p>"
        f"<p><strong>validation_status:</strong> {escape(str(research_evidence_summary.get('validation_status')))}</p>"
        f"<p><strong>provenance_status:</strong> {escape(str(research_evidence_summary.get('provenance_status')))}</p>"
        f"<p><strong>confidence:</strong> {escape(str(research_evidence_summary.get('confidence')))}</p>"
        "<h3>Passed Evidence</h3>"
        f"<ul>{passed_items}</ul>"
        "<h3>Evidence Gaps</h3>"
        f"<ul>{gap_items}</ul>"
        "</section>"
    )


def _render_scientific_verification_html(
    scientific_verification_assessment: dict | None,
) -> str:
    if not scientific_verification_assessment:
        return ""

    def render_items(items: list[str]) -> str:
        if not items:
            return "<li>None</li>"
        return "".join(f"<li>{escape(item)}</li>" for item in items)

    requirement_items = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('label') or item.get('requirement_id')))}</strong> "
        f"(<code>{escape(str(item.get('status')))}</code>)"
        f"<p>{escape(str(item.get('detail') or 'No detail'))}</p>"
        "</li>"
        for item in (scientific_verification_assessment.get("requirements") or [])
    ) or "<li>None</li>"

    return (
        '<section class="panel">'
        "<h2>Scientific Verification</h2>"
        f"<p><strong>status:</strong> {escape(str(scientific_verification_assessment.get('status')))}</p>"
        f"<p><strong>confidence:</strong> {escape(str(scientific_verification_assessment.get('confidence')))}</p>"
        f"<p><strong>requirement_count:</strong> {escape(str(scientific_verification_assessment.get('requirement_count')))}</p>"
        "<h3>Verification Requirements</h3>"
        f"<ul>{requirement_items}</ul>"
        "<h3>Missing Evidence</h3>"
        f"<ul>{render_items(scientific_verification_assessment.get('missing_evidence') or [])}</ul>"
        "<h3>Blocking Issues</h3>"
        f"<ul>{render_items(scientific_verification_assessment.get('blocking_issues') or [])}</ul>"
        "<h3>Passed Requirements</h3>"
        f"<ul>{render_items(scientific_verification_assessment.get('passed_requirements') or [])}</ul>"
        "</section>"
    )


def _compose_summary(
    snapshot: SubmarineRuntimeSnapshot,
    report_title: str,
    solver_metrics: dict | None,
) -> str:
    stage_text = {
        "geometry-preflight": "当前结果主要覆盖几何检查与案例匹配结论，尚未进入真实求解。",
        "solver-dispatch": "当前结果覆盖求解派发与执行状态，保留给 Supervisor 后续审阅与继续执行的边界。",
        "result-reporting": "当前结果已经进入报告整理阶段，可直接交由 Supervisor 做质量复核。",
    }.get(snapshot.current_stage, "当前结果已整理为可审阅交付物。")

    case_text = (
        f"选定案例 `{snapshot.selected_case_id}`。"
        if snapshot.selected_case_id
        else "当前尚未固定单一案例模板。"
    )
    family_text = (
        f"几何家族识别为 `{snapshot.geometry_family}`。"
        if snapshot.geometry_family
        else "几何家族仍待进一步确认。"
    )
    metrics_text = ""
    if solver_metrics and solver_metrics.get("latest_force_coefficients"):
        cd = solver_metrics["latest_force_coefficients"].get("Cd")
        final_time = solver_metrics.get("final_time_seconds")
        metrics_text = f" 已提取 CFD 指标，最终时间步 `{final_time}`，Cd `{cd}`。"

    return (
        f"已生成《{report_title}》，来源阶段为 `{snapshot.current_stage}`。"
        f"{family_text}{case_text}{stage_text}{metrics_text}"
    )


def _load_solver_metrics(outputs_dir: Path, artifact_virtual_paths: list[str]) -> dict | None:
    preferred_paths = [
        virtual_path for virtual_path in artifact_virtual_paths if virtual_path.endswith("/solver-results.json")
    ]
    fallback_paths = [
        virtual_path for virtual_path in artifact_virtual_paths if virtual_path.endswith("/openfoam-request.json")
    ]

    for virtual_path in [*preferred_paths, *fallback_paths]:
        local_path = _resolve_outputs_artifact(outputs_dir, virtual_path)
        if local_path is None or not local_path.exists():
            continue
        try:
            payload = json.loads(local_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if virtual_path.endswith("/solver-results.json"):
            return payload
        solver_results = payload.get("solver_results")
        if solver_results:
            return solver_results
    return None


def _render_solver_metrics_markdown(solver_metrics: dict | None) -> list[str]:
    if not solver_metrics:
        return []

    coefficient_metrics = solver_metrics.get("latest_force_coefficients") or {}
    force_metrics = solver_metrics.get("latest_forces") or {}
    reference_values = solver_metrics.get("reference_values") or {}
    lines = [
        "",
        "## CFD 结果指标",
        f"- 求解完成: `{solver_metrics.get('solver_completed')}`",
        f"- 最终时间步: `{solver_metrics.get('final_time_seconds')}`",
        f"- 后处理目录: `{solver_metrics.get('workspace_postprocess_virtual_path')}`",
    ]
    if coefficient_metrics:
        lines.extend(
            [
                f"- Cd: `{coefficient_metrics.get('Cd')}`",
                f"- Cl: `{coefficient_metrics.get('Cl')}`",
                f"- Cs: `{coefficient_metrics.get('Cs')}`",
                f"- CmPitch: `{coefficient_metrics.get('CmPitch')}`",
            ]
        )
    if force_metrics:
        lines.extend(
            [
                f"- 总阻力向量 (N): `{force_metrics.get('total_force')}`",
                f"- 总力矩向量 (N·m): `{force_metrics.get('total_moment')}`",
            ]
        )
    if reference_values:
        lines.extend(
            [
                "",
                "## 参考量",
                f"- 参考长度: `{reference_values.get('reference_length_m')}` m",
                f"- 参考面积: `{reference_values.get('reference_area_m2')}` m^2",
                f"- 来流速度: `{reference_values.get('inlet_velocity_mps')}` m/s",
                f"- 流体密度: `{reference_values.get('fluid_density_kg_m3')}` kg/m^3",
            ]
        )
    return lines


def _render_solver_metrics_markdown_enriched(solver_metrics: dict | None) -> list[str]:
    if not solver_metrics:
        return []

    coefficient_metrics = solver_metrics.get("latest_force_coefficients") or {}
    force_metrics = solver_metrics.get("latest_forces") or {}
    reference_values = solver_metrics.get("reference_values") or {}
    simulation_requirements = solver_metrics.get("simulation_requirements") or {}
    mesh_summary = solver_metrics.get("mesh_summary") or {}
    residual_summary = solver_metrics.get("residual_summary") or {}

    lines = [
        "",
        "## CFD 结果指标",
        f"- 求解完成: `{solver_metrics.get('solver_completed')}`",
        f"- 最终时间步: `{solver_metrics.get('final_time_seconds')}`",
        f"- 后处理目录: `{solver_metrics.get('workspace_postprocess_virtual_path')}`",
    ]
    if coefficient_metrics:
        lines.extend(
            [
                f"- Cd: `{coefficient_metrics.get('Cd')}`",
                f"- Cl: `{coefficient_metrics.get('Cl')}`",
                f"- Cs: `{coefficient_metrics.get('Cs')}`",
                f"- CmPitch: `{coefficient_metrics.get('CmPitch')}`",
            ]
        )
    if force_metrics:
        lines.extend(
            [
                f"- 总阻力向量(N): `{force_metrics.get('total_force')}`",
                f"- 总力矩向量(N·m): `{force_metrics.get('total_moment')}`",
            ]
        )
    if reference_values:
        lines.extend(
            [
                "",
                "## 参考量",
                f"- 参考长度: `{reference_values.get('reference_length_m')}` m",
                f"- 参考面积: `{reference_values.get('reference_area_m2')}` m^2",
                f"- 来流速度: `{reference_values.get('inlet_velocity_mps')}` m/s",
                f"- 流体密度: `{reference_values.get('fluid_density_kg_m3')}` kg/m^3",
            ]
        )
    if simulation_requirements:
        lines.extend(
            [
                "",
                "## 计算要求",
                f"- inlet_velocity_mps: `{simulation_requirements.get('inlet_velocity_mps')}`",
                f"- fluid_density_kg_m3: `{simulation_requirements.get('fluid_density_kg_m3')}`",
                f"- kinematic_viscosity_m2ps: `{simulation_requirements.get('kinematic_viscosity_m2ps')}`",
                f"- end_time_seconds: `{simulation_requirements.get('end_time_seconds')}`",
                f"- delta_t_seconds: `{simulation_requirements.get('delta_t_seconds')}`",
                f"- write_interval_steps: `{simulation_requirements.get('write_interval_steps')}`",
            ]
        )
    if mesh_summary:
        lines.extend(
            [
                "",
                "## 网格质量摘要",
                f"- Mesh OK: `{mesh_summary.get('mesh_ok')}`",
                f"- cells: `{mesh_summary.get('cells')}`",
                f"- faces: `{mesh_summary.get('faces')}`",
                f"- internal faces: `{mesh_summary.get('internal_faces')}`",
                f"- points: `{mesh_summary.get('points')}`",
            ]
        )
    if residual_summary:
        lines.extend(
            [
                "",
                "## 残差收敛摘要",
                f"- 字段数: `{residual_summary.get('field_count')}`",
                f"- 最新时间: `{residual_summary.get('latest_time')}`",
                f"- 最大最终残差: `{residual_summary.get('max_final_residual')}`",
            ]
        )
        latest_by_field = residual_summary.get("latest_by_field") or {}
        for field_name, entry in latest_by_field.items():
            lines.append(
                f"- {field_name}: initial `{entry.get('initial_residual')}`, "
                f"final `{entry.get('final_residual')}`, iterations `{entry.get('iterations')}`"
            )
    return lines


def _format_spec_number(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "--"
    if float(value).is_integer():
        return str(int(value))
    return f"{float(value):.4f}".rstrip("0").rstrip(".")


def _summarize_postprocess_spec(spec: object) -> str | None:
    if not isinstance(spec, dict):
        return None

    parts: list[str] = []
    field = spec.get("field")
    if isinstance(field, str) and field:
        parts.append(f"field={field}")

    selector = spec.get("selector")
    if isinstance(selector, dict):
        selector_type = selector.get("type")
        if selector_type == "patch":
            patches = selector.get("patches")
            patch_names = [
                str(item)
                for item in patches
                if isinstance(item, str) and item
            ] if isinstance(patches, list) else []
            parts.append(
                f"selector=patch[{','.join(patch_names)}]"
                if patch_names
                else "selector=patch"
            )
        elif selector_type == "plane":
            origin_mode = selector.get("origin_mode")
            origin_value = selector.get("origin_value")
            if origin_mode == "x_by_lref" and isinstance(origin_value, (int, float)):
                origin_summary = f"x/Lref={_format_spec_number(origin_value)}"
            elif origin_mode == "x_absolute_m" and isinstance(origin_value, (int, float)):
                origin_summary = f"x={_format_spec_number(origin_value)}m"
            elif isinstance(origin_value, (int, float)):
                origin_summary = f"origin={_format_spec_number(origin_value)}"
            else:
                origin_summary = "origin=--"

            normal = selector.get("normal")
            normal_summary = ""
            if (
                isinstance(normal, list)
                and len(normal) == 3
                and all(isinstance(item, (int, float)) for item in normal)
            ):
                normal_summary = "; normal=(" + ", ".join(
                    _format_spec_number(item) for item in normal
                ) + ")"
            parts.append(f"selector=plane[{origin_summary}{normal_summary}]")

    time_mode = spec.get("time_mode")
    if isinstance(time_mode, str) and time_mode:
        parts.append(f"time={time_mode}")

    formats = spec.get("formats")
    if isinstance(formats, list):
        format_names = [str(item) for item in formats if isinstance(item, str) and item]
        if format_names:
            parts.append(f"formats={','.join(format_names)}")

    return "; ".join(parts) if parts else None


def _render_markdown(payload: dict) -> str:
    source_artifacts = "\n".join(f"- `{path}`" for path in payload["source_artifact_virtual_paths"]) or "- 暂无"
    final_artifacts = "\n".join(f"- `{path}`" for path in payload["final_artifact_virtual_paths"])
    requested_outputs = "\n".join(
        (
            f"- `{item['output_id']}` | {item['label']} | "
            f"requested=`{item['requested_label']}` | support=`{item['support_level']}`"
            + (
                f" | spec=`{_summarize_postprocess_spec(item.get('postprocess_spec'))}`"
                if _summarize_postprocess_spec(item.get("postprocess_spec"))
                else ""
            )
        )
        for item in payload.get("requested_outputs") or []
    ) or "- 暂无"
    lines = [
        f"# {payload['report_title']}",
        "",
        "## 中文摘要",
        payload["summary_zh"],
        "",
        "## 运行上下文",
        f"- 来源阶段: `{payload['source_runtime_stage']}`",
        f"- 任务类型: `{payload['task_type']}`",
        f"- 几何文件: `{payload['geometry_virtual_path']}`",
        f"- 几何家族: `{payload.get('geometry_family') or '待确认'}`",
        f"- 执行就绪状态: `{payload.get('execution_readiness') or '待判定'}`",
        f"- 选定案例: `{payload.get('selected_case_id') or '未固定'}`",
        f"- Workspace case: `{payload.get('workspace_case_dir_virtual_path') or '当前阶段无'}`",
        f"- Run script: `{payload.get('run_script_virtual_path') or '当前阶段无'}`",
        "",
        "## 当前阶段判断",
        f"- review_status: `{payload['review_status']}`",
        f"- next_recommended_stage: `{payload['next_recommended_stage']}`",
        f"- source_report_virtual_path: `{payload['source_report_virtual_path']}`",
        (
            f"- supervisor_handoff_virtual_path: "
            f"`{payload.get('supervisor_handoff_virtual_path') or '当前阶段无'}`"
        ),
        "",
        "## 来源证据",
        source_artifacts,
    ]
    lines.extend(
        [
            "",
            "## Requested Outputs",
            requested_outputs,
        ]
    )
    lines.extend(_render_solver_metrics_markdown_enriched(payload.get("solver_metrics")))
    lines.extend(_render_acceptance_markdown(payload.get("acceptance_assessment")))
    lines.extend(_render_experiment_markdown(payload.get("experiment_summary")))
    lines.extend(_render_research_evidence_markdown(payload.get("research_evidence_summary")))
    lines.extend(_render_scientific_study_markdown(payload.get("scientific_study_summary")))
    lines.extend(
        _render_scientific_verification_markdown(
            payload.get("scientific_verification_assessment")
        )
    )
    lines.extend(_render_output_delivery_markdown(payload.get("output_delivery_plan")))
    lines.extend(
        [
            "",
            "## 本阶段产物",
            final_artifacts,
            "",
            "## 建议",
            "- 由 Claude Code Supervisor 审阅当前阶段结论，再决定是否进入下一次 DeerFlow run。",
            "- 若当前仅完成几何预检，请在继续前补全工况、案例和求解参数确认。",
            "- 若当前已完成求解派发或执行，请继续补齐结果整理与后处理展示。",
            "",
        ]
    )
    return "\n".join(lines)


def _render_solver_metrics_html(solver_metrics: dict | None) -> str:
    if not solver_metrics:
        return ""

    coefficient_metrics = solver_metrics.get("latest_force_coefficients") or {}
    force_metrics = solver_metrics.get("latest_forces") or {}
    reference_values = solver_metrics.get("reference_values") or {}
    metric_lines = [
        f"<p><strong>求解完成:</strong> {escape(str(solver_metrics.get('solver_completed')))}</p>",
        f"<p><strong>最终时间步:</strong> {escape(str(solver_metrics.get('final_time_seconds')))}</p>",
        (
            "<p><strong>后处理目录:</strong> "
            f"{escape(str(solver_metrics.get('workspace_postprocess_virtual_path')))}</p>"
        ),
    ]
    if coefficient_metrics:
        metric_lines.extend(
            [
                f"<p><strong>Cd:</strong> {escape(str(coefficient_metrics.get('Cd')))}</p>",
                f"<p><strong>Cl:</strong> {escape(str(coefficient_metrics.get('Cl')))}</p>",
                f"<p><strong>Cs:</strong> {escape(str(coefficient_metrics.get('Cs')))}</p>",
                f"<p><strong>CmPitch:</strong> {escape(str(coefficient_metrics.get('CmPitch')))}</p>",
            ]
        )
    if force_metrics:
        metric_lines.extend(
            [
                f"<p><strong>总阻力向量 (N):</strong> {escape(str(force_metrics.get('total_force')))}</p>",
                f"<p><strong>总力矩向量 (N·m):</strong> {escape(str(force_metrics.get('total_moment')))}</p>",
            ]
        )
    if reference_values:
        metric_lines.extend(
            [
                f"<p><strong>参考长度:</strong> {escape(str(reference_values.get('reference_length_m')))} m</p>",
                f"<p><strong>参考面积:</strong> {escape(str(reference_values.get('reference_area_m2')))} m^2</p>",
                f"<p><strong>来流速度:</strong> {escape(str(reference_values.get('inlet_velocity_mps')))} m/s</p>",
                f"<p><strong>流体密度:</strong> {escape(str(reference_values.get('fluid_density_kg_m3')))} kg/m^3</p>",
            ]
        )

    return "<section class=\"panel\"><h2>CFD 结果指标</h2>" + "".join(metric_lines) + "</section>"


def _render_solver_metrics_html_enriched(solver_metrics: dict | None) -> str:
    if not solver_metrics:
        return ""

    coefficient_metrics = solver_metrics.get("latest_force_coefficients") or {}
    force_metrics = solver_metrics.get("latest_forces") or {}
    reference_values = solver_metrics.get("reference_values") or {}
    simulation_requirements = solver_metrics.get("simulation_requirements") or {}
    mesh_summary = solver_metrics.get("mesh_summary") or {}
    residual_summary = solver_metrics.get("residual_summary") or {}
    metric_lines = [
        f"<p><strong>求解完成:</strong> {escape(str(solver_metrics.get('solver_completed')))}</p>",
        f"<p><strong>最终时间步:</strong> {escape(str(solver_metrics.get('final_time_seconds')))}</p>",
        (
            "<p><strong>后处理目录:</strong> "
            f"{escape(str(solver_metrics.get('workspace_postprocess_virtual_path')))}</p>"
        ),
    ]
    if coefficient_metrics:
        metric_lines.extend(
            [
                f"<p><strong>Cd:</strong> {escape(str(coefficient_metrics.get('Cd')))}</p>",
                f"<p><strong>Cl:</strong> {escape(str(coefficient_metrics.get('Cl')))}</p>",
                f"<p><strong>Cs:</strong> {escape(str(coefficient_metrics.get('Cs')))}</p>",
                f"<p><strong>CmPitch:</strong> {escape(str(coefficient_metrics.get('CmPitch')))}</p>",
            ]
        )
    if force_metrics:
        metric_lines.extend(
            [
                f"<p><strong>总阻力向量(N):</strong> {escape(str(force_metrics.get('total_force')))}</p>",
                f"<p><strong>总力矩向量(N·m):</strong> {escape(str(force_metrics.get('total_moment')))}</p>",
            ]
        )
    if reference_values:
        metric_lines.extend(
            [
                f"<p><strong>参考长度:</strong> {escape(str(reference_values.get('reference_length_m')))} m</p>",
                f"<p><strong>参考面积:</strong> {escape(str(reference_values.get('reference_area_m2')))} m^2</p>",
                f"<p><strong>来流速度:</strong> {escape(str(reference_values.get('inlet_velocity_mps')))} m/s</p>",
                f"<p><strong>流体密度:</strong> {escape(str(reference_values.get('fluid_density_kg_m3')))} kg/m^3</p>",
            ]
        )
    if simulation_requirements:
        metric_lines.extend(
            [
                "<h3>计算要求</h3>",
                f"<p><strong>inlet_velocity_mps:</strong> {escape(str(simulation_requirements.get('inlet_velocity_mps')))}</p>",
                f"<p><strong>fluid_density_kg_m3:</strong> {escape(str(simulation_requirements.get('fluid_density_kg_m3')))}</p>",
                f"<p><strong>kinematic_viscosity_m2ps:</strong> {escape(str(simulation_requirements.get('kinematic_viscosity_m2ps')))}</p>",
                f"<p><strong>end_time_seconds:</strong> {escape(str(simulation_requirements.get('end_time_seconds')))}</p>",
                f"<p><strong>delta_t_seconds:</strong> {escape(str(simulation_requirements.get('delta_t_seconds')))}</p>",
                f"<p><strong>write_interval_steps:</strong> {escape(str(simulation_requirements.get('write_interval_steps')))}</p>",
            ]
        )
    if mesh_summary:
        metric_lines.extend(
            [
                "<h3>网格质量摘要</h3>",
                f"<p><strong>Mesh OK:</strong> {escape(str(mesh_summary.get('mesh_ok')))}</p>",
                f"<p><strong>cells:</strong> {escape(str(mesh_summary.get('cells')))}</p>",
                f"<p><strong>faces:</strong> {escape(str(mesh_summary.get('faces')))}</p>",
                f"<p><strong>internal faces:</strong> {escape(str(mesh_summary.get('internal_faces')))}</p>",
                f"<p><strong>points:</strong> {escape(str(mesh_summary.get('points')))}</p>",
            ]
        )
    if residual_summary:
        metric_lines.extend(
            [
                "<h3>残差收敛摘要</h3>",
                f"<p><strong>字段数:</strong> {escape(str(residual_summary.get('field_count')))}</p>",
                f"<p><strong>最新时间:</strong> {escape(str(residual_summary.get('latest_time')))}</p>",
                f"<p><strong>最大最终残差:</strong> {escape(str(residual_summary.get('max_final_residual')))}</p>",
            ]
        )
        latest_by_field = residual_summary.get("latest_by_field") or {}
        for field_name, entry in latest_by_field.items():
            metric_lines.append(
                "<p>"
                f"<strong>{escape(str(field_name))}:</strong> "
                f"initial {escape(str(entry.get('initial_residual')))}, "
                f"final {escape(str(entry.get('final_residual')))}, "
                f"iterations {escape(str(entry.get('iterations')))}"
                "</p>"
            )

    return "<section class=\"panel\"><h2>CFD 结果指标</h2>" + "".join(metric_lines) + "</section>"


def _render_html(payload: dict) -> str:
    source_items = "".join(f"<li>{escape(path)}</li>" for path in payload["source_artifact_virtual_paths"]) or "<li>暂无</li>"
    final_items = "".join(f"<li>{escape(path)}</li>" for path in payload["final_artifact_virtual_paths"])
    metrics_section = _render_solver_metrics_html_enriched(payload.get("solver_metrics"))
    acceptance_section = _render_acceptance_html(payload.get("acceptance_assessment"))
    experiment_section = _render_experiment_html(payload.get("experiment_summary"))
    research_evidence_section = _render_research_evidence_html(
        payload.get("research_evidence_summary")
    )
    scientific_study_section = _render_scientific_study_html(
        payload.get("scientific_study_summary")
    )
    scientific_verification_section = _render_scientific_verification_html(
        payload.get("scientific_verification_assessment")
    )
    requested_outputs_section = (
        '<section class="panel"><h2>Requested Outputs</h2><ul>'
        + (
            "".join(
                "<li>"
                f"<strong>{escape(str(item.get('label')))}</strong> "
                f"(<code>{escape(str(item.get('output_id')))}</code>)"
                f"<p>requested={escape(str(item.get('requested_label')))}, "
                f"support={escape(str(item.get('support_level')))}"
                + (
                    f", spec={escape(summary)}"
                    if (summary := _summarize_postprocess_spec(item.get("postprocess_spec")))
                    else ""
                )
                + "</p>"
                "</li>"
                for item in (payload.get("requested_outputs") or [])
            )
            or "<li>暂无</li>"
        )
        + "</ul></section>"
    )
    output_delivery_section = _render_output_delivery_html(payload.get("output_delivery_plan"))
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>{escape(payload['report_title'])}</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
        background: #f7f8fa;
        color: #111827;
      }}
      .panel {{
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
      }}
      h1, h2 {{ margin: 0 0 12px; }}
      p {{ line-height: 1.7; }}
      ul {{ margin: 0; padding-left: 20px; }}
      li {{ margin-bottom: 8px; }}
      strong {{ color: #0f172a; }}
    </style>
  </head>
  <body>
    <section class="panel">
      <h1>{escape(payload['report_title'])}</h1>
      <p>{escape(payload['summary_zh'])}</p>
    </section>
    <section class="panel">
      <h2>运行上下文</h2>
      <p><strong>来源阶段:</strong> {escape(str(payload['source_runtime_stage']))}</p>
      <p><strong>任务类型:</strong> {escape(str(payload['task_type']))}</p>
      <p><strong>几何文件:</strong> {escape(str(payload['geometry_virtual_path']))}</p>
      <p><strong>几何家族:</strong> {escape(str(payload.get('geometry_family') or '待确认'))}</p>
      <p><strong>Workspace case:</strong> {escape(str(payload.get('workspace_case_dir_virtual_path') or '当前阶段无'))}</p>
      <p><strong>Run script:</strong> {escape(str(payload.get('run_script_virtual_path') or '当前阶段无'))}</p>
    </section>
    <section class="panel">
      <h2>来源证据</h2>
      <ul>{source_items}</ul>
    </section>
    {requested_outputs_section}
      {metrics_section}
      {acceptance_section}
      {experiment_section}
      {research_evidence_section}
      {scientific_study_section}
      {scientific_verification_section}
    {output_delivery_section}
    <section class="panel">
      <h2>本阶段产物</h2>
      <ul>{final_items}</ul>
    </section>
  </body>
</html>
"""


def run_result_report(
    *,
    snapshot: SubmarineRuntimeSnapshot,
    outputs_dir: Path,
    report_title: str | None = None,
) -> tuple[dict, list[str]]:
    geometry_name = Path(snapshot.geometry_virtual_path).stem or "submarine-run"
    run_dir_name = _slugify(geometry_name)
    artifact_dir = outputs_dir / "submarine" / "reports" / run_dir_name
    artifact_dir.mkdir(parents=True, exist_ok=True)

    report_title = report_title or "潜艇 CFD 阶段报告"
    delivery_markdown_artifact = _artifact_virtual_path(run_dir_name, "delivery-readiness.md")
    delivery_json_artifact = _artifact_virtual_path(run_dir_name, "delivery-readiness.json")
    research_evidence_json_artifact = _artifact_virtual_path(
        run_dir_name, "research-evidence-summary.json"
    )
    json_artifact = _artifact_virtual_path(run_dir_name, "final-report.json")
    markdown_artifact = _artifact_virtual_path(run_dir_name, "final-report.md")
    html_artifact = _artifact_virtual_path(run_dir_name, "final-report.html")
    new_artifacts = [
        delivery_markdown_artifact,
        delivery_json_artifact,
        research_evidence_json_artifact,
        markdown_artifact,
        html_artifact,
        json_artifact,
    ]
    all_artifacts = _merge_artifact_paths(snapshot.artifact_virtual_paths, new_artifacts)
    solver_metrics = _load_solver_metrics(outputs_dir, snapshot.artifact_virtual_paths)
    selected_case = _resolve_selected_case(snapshot.selected_case_id)
    scientific_verification_requirements = [
        item.model_dump(mode="json")
        for item in build_effective_scientific_verification_requirements(
            acceptance_profile=selected_case.acceptance_profile if selected_case else None,
            task_type=snapshot.task_type,
        )
    ]
    acceptance_assessment = _build_acceptance_assessment(
        snapshot,
        solver_metrics,
        selected_case=selected_case,
        artifact_virtual_paths=all_artifacts,
    )
    scientific_verification_assessment = build_scientific_verification_assessment(
        acceptance_profile=selected_case.acceptance_profile if selected_case else None,
        task_type=snapshot.task_type,
        solver_metrics=solver_metrics,
        artifact_virtual_paths=all_artifacts,
        outputs_dir=outputs_dir,
    )
    scientific_study_summary = _build_scientific_study_summary(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=all_artifacts,
        scientific_verification_assessment=scientific_verification_assessment,
    )
    experiment_summary = _build_experiment_summary(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=all_artifacts,
    )
    output_delivery_plan = build_output_delivery_plan(
        snapshot.requested_outputs,
        stage="result-reporting",
        solver_metrics=solver_metrics,
        artifact_virtual_paths=all_artifacts,
        acceptance_assessment=acceptance_assessment,
    )
    research_evidence_summary = build_research_evidence_summary(
        acceptance_profile=selected_case.acceptance_profile if selected_case else None,
        acceptance_assessment=acceptance_assessment,
        scientific_verification_assessment=scientific_verification_assessment,
        scientific_study_summary=scientific_study_summary,
        experiment_summary=experiment_summary,
        output_delivery_plan=output_delivery_plan,
        artifact_virtual_paths=all_artifacts,
    )

    review = build_supervisor_review_contract(
        next_recommended_stage="supervisor-review",
        report_virtual_path=markdown_artifact,
        artifact_virtual_paths=all_artifacts,
    )
    payload = {
        "report_title": report_title,
        "summary_zh": _compose_summary(snapshot, report_title, solver_metrics),
        "source_runtime_stage": snapshot.current_stage,
        "task_summary": snapshot.task_summary,
        "task_type": snapshot.task_type,
        "geometry_virtual_path": snapshot.geometry_virtual_path,
        "geometry_family": snapshot.geometry_family,
        "execution_readiness": snapshot.execution_readiness,
        "selected_case_id": snapshot.selected_case_id,
        "requested_outputs": [
            item.model_dump(mode="json") for item in snapshot.requested_outputs
        ],
        "scientific_verification_requirements": scientific_verification_requirements,
        "selected_case_acceptance_profile": (
            selected_case.acceptance_profile.model_dump(mode="json")
            if selected_case and selected_case.acceptance_profile
            else None
        ),
        "workspace_case_dir_virtual_path": snapshot.workspace_case_dir_virtual_path,
        "run_script_virtual_path": snapshot.run_script_virtual_path,
        "supervisor_handoff_virtual_path": snapshot.supervisor_handoff_virtual_path,
        "source_report_virtual_path": snapshot.report_virtual_path,
        "source_artifact_virtual_paths": snapshot.artifact_virtual_paths,
        "solver_metrics": solver_metrics,
        "acceptance_assessment": acceptance_assessment,
        "experiment_summary": experiment_summary,
        "research_evidence_summary": research_evidence_summary,
        "scientific_study_summary": scientific_study_summary,
        "scientific_verification_assessment": scientific_verification_assessment,
        "output_delivery_plan": output_delivery_plan,
        "stage_status": snapshot.stage_status,
        "review_status": review.review_status,
        "next_recommended_stage": review.next_recommended_stage,
        "report_virtual_path": review.report_virtual_path,
        "final_artifact_virtual_paths": new_artifacts,
        "artifact_virtual_paths": review.artifact_virtual_paths,
    }

    (artifact_dir / "delivery-readiness.json").write_text(
        json.dumps(acceptance_assessment, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (artifact_dir / "delivery-readiness.md").write_text(
        _render_delivery_readiness_markdown(report_title, acceptance_assessment),
        encoding="utf-8",
    )
    (artifact_dir / "research-evidence-summary.json").write_text(
        json.dumps(research_evidence_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (artifact_dir / "final-report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (artifact_dir / "final-report.md").write_text(
        _render_markdown(payload),
        encoding="utf-8",
    )
    (artifact_dir / "final-report.html").write_text(
        _render_html(payload),
        encoding="utf-8",
    )

    return payload, new_artifacts
