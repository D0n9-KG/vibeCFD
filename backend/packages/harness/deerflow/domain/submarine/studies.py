"""Deterministic scientific-study planning for submarine CFD workflows."""

from __future__ import annotations

from collections.abc import Mapping

from .models import (
    SubmarineCase,
    SubmarineScientificStudyDefinition,
    SubmarineScientificStudyManifest,
    SubmarineScientificStudyResult,
    SubmarineScientificStudyType,
    SubmarineScientificStudyVariant,
)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _study_tolerance_for_task(task_type: str) -> float:
    return 0.02 if task_type == "resistance" else 0.05


def _monitored_quantity_for_task(task_type: str) -> str:
    return "Cd" if task_type == "resistance" else "Cl"


def _variant(
    *,
    study_type: SubmarineScientificStudyType,
    variant_id: str,
    variant_label: str,
    rationale: str,
    parameter_overrides: dict[str, float | int | str],
) -> SubmarineScientificStudyVariant:
    return SubmarineScientificStudyVariant(
        study_type=study_type,
        variant_id=variant_id,
        variant_label=variant_label,
        rationale=rationale,
        parameter_overrides=parameter_overrides,
    )


def _mesh_variants() -> list[SubmarineScientificStudyVariant]:
    study_type: SubmarineScientificStudyType = "mesh_independence"
    return [
        _variant(
            study_type=study_type,
            variant_id="coarse",
            variant_label="Coarse",
            rationale="Reduce mesh density to test sensitivity to a less refined baseline.",
            parameter_overrides={"mesh_scale_factor": 0.75},
        ),
        _variant(
            study_type=study_type,
            variant_id="baseline",
            variant_label="Baseline",
            rationale="Keep the baseline mesh configuration as the comparison anchor.",
            parameter_overrides={"mesh_scale_factor": 1.0},
        ),
        _variant(
            study_type=study_type,
            variant_id="fine",
            variant_label="Fine",
            rationale="Increase mesh density to test convergence of the monitored quantity.",
            parameter_overrides={"mesh_scale_factor": 1.25},
        ),
    ]


def _domain_variants() -> list[SubmarineScientificStudyVariant]:
    study_type: SubmarineScientificStudyType = "domain_sensitivity"
    return [
        _variant(
            study_type=study_type,
            variant_id="compact",
            variant_label="Compact",
            rationale="Tighten the far-field domain to test boundary-condition sensitivity.",
            parameter_overrides={"domain_extent_multiplier": 0.85},
        ),
        _variant(
            study_type=study_type,
            variant_id="baseline",
            variant_label="Baseline",
            rationale="Keep the baseline domain extent as the comparison anchor.",
            parameter_overrides={"domain_extent_multiplier": 1.0},
        ),
        _variant(
            study_type=study_type,
            variant_id="expanded",
            variant_label="Expanded",
            rationale="Expand the far-field domain to verify that external boundaries do not drive the result.",
            parameter_overrides={"domain_extent_multiplier": 1.2},
        ),
    ]


def _time_step_variants(
    simulation_requirements: Mapping[str, float | int] | None,
) -> list[SubmarineScientificStudyVariant]:
    study_type: SubmarineScientificStudyType = "time_step_sensitivity"
    baseline_delta_t = None
    if simulation_requirements is not None:
        delta_t_value = simulation_requirements.get("delta_t_seconds")
        if isinstance(delta_t_value, (int, float)) and not isinstance(delta_t_value, bool):
            baseline_delta_t = float(delta_t_value)

    variants: list[tuple[str, str, str, float]] = [
        ("coarse", "Coarse", "Use a larger step to test time-advance sensitivity.", 2.0),
        ("baseline", "Baseline", "Keep the baseline time step as the comparison anchor.", 1.0),
        ("fine", "Fine", "Use a smaller step to test convergence of the monitored quantity.", 0.5),
    ]

    planned: list[SubmarineScientificStudyVariant] = []
    for variant_id, variant_label, rationale, multiplier in variants:
        overrides: dict[str, float | int | str] = {"delta_t_multiplier": multiplier}
        if baseline_delta_t is not None:
            overrides["delta_t_seconds"] = baseline_delta_t * multiplier
        planned.append(
            _variant(
                study_type=study_type,
                variant_id=variant_id,
                variant_label=variant_label,
                rationale=rationale,
                parameter_overrides=overrides,
            )
        )
    return planned


def _count_statuses(statuses: list[str | None]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for status in statuses:
        if not status:
            continue
        counts[status] = counts.get(status, 0) + 1
    return counts


def _expected_variant_run_ids(
    variants: list[SubmarineScientificStudyVariant],
) -> list[str]:
    return [
        variant.expected_run_id
        for variant in variants
        if variant.variant_id != "baseline" and variant.expected_run_id
    ]


def _study_execution_status(
    variants: list[SubmarineScientificStudyVariant],
) -> str:
    candidate_statuses = [
        variant.execution_status
        for variant in variants
        if variant.variant_id != "baseline"
    ]
    if any(status == "blocked" for status in candidate_statuses):
        return "blocked"
    if any(status == "in_progress" for status in candidate_statuses):
        return "in_progress"
    if candidate_statuses and all(status == "completed" for status in candidate_statuses):
        return "completed"
    return "planned"


def _study_workflow_status(
    variants: list[SubmarineScientificStudyVariant],
) -> str:
    candidate_variants = [
        variant for variant in variants if variant.variant_id != "baseline"
    ]
    baseline_completed = any(
        variant.variant_id == "baseline" and variant.execution_status == "completed"
        for variant in variants
    )
    execution_statuses = [variant.execution_status for variant in candidate_variants]
    compare_statuses = [
        variant.compare_status
        for variant in candidate_variants
        if variant.compare_status is not None
    ]
    if any(status == "blocked" for status in execution_statuses):
        return "blocked"
    if any(status == "blocked" for status in compare_statuses):
        return "blocked"
    if any(status == "in_progress" for status in execution_statuses):
        return "in_progress"
    if (
        candidate_variants
        and all(status == "planned" for status in execution_statuses)
        and (not compare_statuses or all(status == "planned" for status in compare_statuses))
    ):
        return "partial" if baseline_completed else "planned"
    if (
        candidate_variants
        and all(status == "completed" for status in execution_statuses)
        and len(compare_statuses) == len(candidate_variants)
        and all(status == "completed" for status in compare_statuses)
    ):
        return "completed"
    if baseline_completed or any(
        status == "completed" for status in execution_statuses
    ) or compare_statuses:
        return "partial"
    return "planned"


def _manifest_execution_status(
    definitions: list[SubmarineScientificStudyDefinition],
) -> str:
    statuses = [definition.study_execution_status for definition in definitions]
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "in_progress" for status in statuses):
        return "in_progress"
    if statuses and all(status == "completed" for status in statuses):
        return "completed"
    return "planned"


def _manifest_workflow_status(
    definitions: list[SubmarineScientificStudyDefinition],
) -> str:
    statuses = [definition.workflow_status for definition in definitions]
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if statuses and all(status == "completed" for status in statuses):
        return "completed"
    if any(status == "in_progress" for status in statuses):
        return "in_progress"
    if any(status in {"partial", "completed"} for status in statuses):
        return "partial"
    return "planned"


def build_scientific_study_manifest_with_variant_updates(
    *,
    manifest: SubmarineScientificStudyManifest,
    variant_updates: Mapping[str, Mapping[str, Mapping[str, object]]] | None = None,
    artifact_virtual_paths: list[str] | None = None,
) -> SubmarineScientificStudyManifest:
    updates = variant_updates or {}
    updated_definitions: list[SubmarineScientificStudyDefinition] = []

    for definition in manifest.study_definitions:
        study_updates = updates.get(definition.study_type) or {}
        updated_variants = [
            variant.model_copy(update=dict(study_updates.get(variant.variant_id) or {}))
            for variant in definition.variants
        ]
        updated_definitions.append(
            definition.model_copy(
                update={
                    "variants": updated_variants,
                    "study_execution_status": _study_execution_status(updated_variants),
                    "workflow_status": _study_workflow_status(updated_variants),
                    "variant_status_counts": _count_statuses(
                        [variant.execution_status for variant in updated_variants]
                    ),
                    "compare_status_counts": _count_statuses(
                        [variant.compare_status for variant in updated_variants]
                    ),
                    "expected_variant_run_ids": _expected_variant_run_ids(
                        updated_variants
                    ),
                }
            )
        )

    merged_artifact_paths = list(
        dict.fromkeys(artifact_virtual_paths or manifest.artifact_virtual_paths)
    )
    return manifest.model_copy(
        update={
            "study_definitions": updated_definitions,
            "artifact_virtual_paths": merged_artifact_paths,
            "study_execution_status": _manifest_execution_status(updated_definitions),
            "workflow_status": _manifest_workflow_status(updated_definitions),
            "study_status_counts": _count_statuses(
                [definition.workflow_status for definition in updated_definitions]
            ),
        }
    )


def build_effective_scientific_study_definitions(
    *,
    selected_case: SubmarineCase,
    simulation_requirements: Mapping[str, float | int] | None,
) -> list[SubmarineScientificStudyDefinition]:
    acceptance_profile = selected_case.acceptance_profile
    if acceptance_profile is None or not acceptance_profile.require_force_coefficients:
        return []

    monitored_quantity = _monitored_quantity_for_task(selected_case.task_type)
    tolerance = _study_tolerance_for_task(selected_case.task_type)

    return [
        SubmarineScientificStudyDefinition(
            study_type="mesh_independence",
            summary_label="Mesh Independence",
            monitored_quantity=monitored_quantity,
            pass_fail_tolerance=tolerance,
            variants=_mesh_variants(),
        ),
        SubmarineScientificStudyDefinition(
            study_type="domain_sensitivity",
            summary_label="Domain Sensitivity",
            monitored_quantity=monitored_quantity,
            pass_fail_tolerance=tolerance,
            variants=_domain_variants(),
        ),
        SubmarineScientificStudyDefinition(
            study_type="time_step_sensitivity",
            summary_label="Time-step Sensitivity",
            monitored_quantity=monitored_quantity,
            pass_fail_tolerance=tolerance,
            variants=_time_step_variants(simulation_requirements),
        ),
    ]


def build_scientific_study_manifest(
    *,
    selected_case: SubmarineCase,
    simulation_requirements: Mapping[str, float | int] | None,
    baseline_configuration_snapshot: Mapping[str, object] | None = None,
) -> SubmarineScientificStudyManifest:
    snapshot = dict(baseline_configuration_snapshot or {})
    if simulation_requirements is not None:
        snapshot.setdefault("simulation_requirements", dict(simulation_requirements))

    manifest = SubmarineScientificStudyManifest(
        selected_case_id=selected_case.case_id,
        baseline_configuration_snapshot=snapshot,
        study_definitions=build_effective_scientific_study_definitions(
            selected_case=selected_case,
            simulation_requirements=simulation_requirements,
        ),
        artifact_virtual_paths=[],
        study_execution_status="planned",
    )
    return build_scientific_study_manifest_with_variant_updates(manifest=manifest)


def build_scientific_study_plan_payload(
    manifest: SubmarineScientificStudyManifest,
) -> dict[str, object]:
    studies: list[dict[str, object]] = []
    for definition in manifest.study_definitions:
        studies.append(
            {
                "study_type": definition.study_type,
                "summary_label": definition.summary_label,
                "monitored_quantity": definition.monitored_quantity,
                "pass_fail_tolerance": definition.pass_fail_tolerance,
                "variant_ids": [variant.variant_id for variant in definition.variants],
                "study_execution_status": definition.study_execution_status,
                "workflow_status": definition.workflow_status,
                "variant_status_counts": definition.variant_status_counts,
                "compare_status_counts": definition.compare_status_counts,
                "expected_variant_run_ids": definition.expected_variant_run_ids,
            }
        )
    return {
        "selected_case_id": manifest.selected_case_id,
        "study_count": len(manifest.study_definitions),
        "study_execution_status": manifest.study_execution_status,
        "workflow_status": manifest.workflow_status,
        "study_status_counts": manifest.study_status_counts,
        "studies": studies,
    }


def build_pending_scientific_study_results(
    *,
    manifest: SubmarineScientificStudyManifest,
    baseline_solver_results: Mapping[str, object] | None,
) -> list[SubmarineScientificStudyResult]:
    latest_force_coefficients = {}
    if isinstance(baseline_solver_results, Mapping):
        force_coefficients = baseline_solver_results.get("latest_force_coefficients")
        if isinstance(force_coefficients, Mapping):
            latest_force_coefficients = force_coefficients

    results: list[SubmarineScientificStudyResult] = []
    for definition in manifest.study_definitions:
        baseline_value = latest_force_coefficients.get(definition.monitored_quantity)
        if isinstance(baseline_value, bool) or not isinstance(baseline_value, (int, float)):
            baseline_value = None

        results.append(
            SubmarineScientificStudyResult(
                study_type=definition.study_type,
                monitored_quantity=definition.monitored_quantity,
                baseline_value=float(baseline_value) if baseline_value is not None else None,
                compared_values=[],
                relative_spread=None,
                status="missing_evidence",
                summary_zh=(
                    "已生成研究变体清单，但当前仅完成 baseline run，尚未补齐该研究所需的"
                    "变体求解结果。"
                ),
            )
        )
    return results


def build_scientific_study_variant_execution(
    *,
    variant: SubmarineScientificStudyVariant,
    simulation_requirements: Mapping[str, float | int],
) -> dict[str, object]:
    resolved_requirements = dict(simulation_requirements)
    delta_t_override = variant.parameter_overrides.get("delta_t_seconds")
    if _is_number(delta_t_override):
        resolved_requirements["delta_t_seconds"] = float(delta_t_override)

    mesh_scale_factor = variant.parameter_overrides.get("mesh_scale_factor", 1.0)
    domain_extent_multiplier = variant.parameter_overrides.get(
        "domain_extent_multiplier",
        1.0,
    )

    return {
        "simulation_requirements": resolved_requirements,
        "mesh_scale_factor": float(mesh_scale_factor)
        if _is_number(mesh_scale_factor)
        else 1.0,
        "domain_extent_multiplier": float(domain_extent_multiplier)
        if _is_number(domain_extent_multiplier)
        else 1.0,
    }


def _resolve_monitored_value(
    solver_results: Mapping[str, object] | None,
    monitored_quantity: str,
) -> float | None:
    if not isinstance(solver_results, Mapping):
        return None
    coefficients = solver_results.get("latest_force_coefficients")
    if not isinstance(coefficients, Mapping):
        return None
    value = coefficients.get(monitored_quantity)
    if not _is_number(value):
        return None
    return float(value)


def build_completed_scientific_study_results(
    *,
    manifest: SubmarineScientificStudyManifest,
    baseline_solver_results: Mapping[str, object] | None,
    variant_results: Mapping[str, Mapping[str, Mapping[str, object] | None]],
) -> list[SubmarineScientificStudyResult]:
    results: list[SubmarineScientificStudyResult] = []

    for definition in manifest.study_definitions:
        study_results = variant_results.get(definition.study_type) or {}
        baseline_result = study_results.get("baseline") or baseline_solver_results
        baseline_value = _resolve_monitored_value(
            baseline_result,
            definition.monitored_quantity,
        )
        if baseline_value is None:
            results.append(
                SubmarineScientificStudyResult(
                    study_type=definition.study_type,
                    monitored_quantity=definition.monitored_quantity,
                    baseline_value=None,
                    compared_values=[],
                    relative_spread=None,
                    status="missing_evidence",
                    summary_zh="Baseline study result is missing the monitored quantity required for comparison.",
                )
            )
            continue

        compared_values: list[dict[str, object]] = []
        monitored_values = [baseline_value]
        blocked_variants: list[str] = []
        missing_variants: list[str] = []
        for variant in definition.variants:
            if variant.variant_id == "baseline":
                continue
            solver_result = study_results.get(variant.variant_id)
            if isinstance(solver_result, Mapping) and (
                solver_result.get("execution_status") == "blocked"
            ):
                blocked_variants.append(variant.variant_id)
                continue
            monitored_value = _resolve_monitored_value(
                solver_result,
                definition.monitored_quantity,
            )
            if monitored_value is None:
                missing_variants.append(variant.variant_id)
                continue
            monitored_values.append(monitored_value)
            compared_values.append(
                {
                    "variant_id": variant.variant_id,
                    "variant_label": variant.variant_label,
                    "observed_value": monitored_value,
                    "relative_delta": abs(monitored_value - baseline_value)
                    / max(abs(baseline_value), 1e-12),
                    }
                )

        if blocked_variants:
            results.append(
                SubmarineScientificStudyResult(
                    study_type=definition.study_type,
                    monitored_quantity=definition.monitored_quantity,
                    baseline_value=baseline_value,
                    compared_values=compared_values,
                    relative_spread=None,
                    status="blocked",
                    summary_zh=(
                        "Scientific-study variant execution is blocked for: "
                        + ", ".join(blocked_variants)
                        + "."
                    ),
                )
            )
            continue

        if missing_variants:
            results.append(
                SubmarineScientificStudyResult(
                    study_type=definition.study_type,
                    monitored_quantity=definition.monitored_quantity,
                    baseline_value=baseline_value,
                    compared_values=compared_values,
                    relative_spread=None,
                    status="missing_evidence",
                    summary_zh=(
                        "Some scientific-study variants are missing solver results: "
                        + ", ".join(missing_variants)
                        + "."
                    ),
                )
            )
            continue

        relative_spread = (max(monitored_values) - min(monitored_values)) / max(
            abs(baseline_value),
            1e-12,
        )
        status = "passed" if relative_spread <= definition.pass_fail_tolerance else "blocked"
        summary = (
            f"{definition.summary_label} keeps {definition.monitored_quantity} spread "
            f"within tolerance {definition.pass_fail_tolerance:.4f}."
            if status == "passed"
            else f"{definition.summary_label} shows {definition.monitored_quantity} spread "
            f"above tolerance {definition.pass_fail_tolerance:.4f}."
        )
        results.append(
            SubmarineScientificStudyResult(
                study_type=definition.study_type,
                monitored_quantity=definition.monitored_quantity,
                baseline_value=baseline_value,
                compared_values=compared_values,
                relative_spread=relative_spread,
                status=status,
                summary_zh=summary,
            )
        )

    return results
