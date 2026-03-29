"""Acceptance and benchmark assessment helpers for submarine result reporting."""

from __future__ import annotations

from .contracts import SubmarineRuntimeSnapshot
from .models import SubmarineBenchmarkTarget, SubmarineCase


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


def build_acceptance_assessment(
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

__all__ = ["build_acceptance_assessment"]
