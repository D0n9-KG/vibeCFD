"""Scientific verification contracts for research-facing submarine CFD runs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from .artifact_store import (
    load_first_json_payload_from_artifacts,
    load_json_outputs_artifact,
    load_json_payloads_from_artifacts,
)
from .models import (
    SubmarineCaseAcceptanceProfile,
    SubmarineScientificStudyManifest,
    SubmarineScientificVerificationRequirement,
)
from .studies import build_completed_scientific_study_results

_STABILITY_EVIDENCE_FILENAME = "stability-evidence.json"
_STUDY_MANIFEST_FILENAME = "study-manifest.json"
_STABILITY_REQUIREMENT_TYPES = {
    "max_final_residual",
    "force_coefficient_tail_stability",
}
_SCIENTIFIC_STUDY_TYPES = {
    "mesh_independence",
    "domain_sensitivity",
    "time_step_sensitivity",
}
_SOLVER_DISPATCH_PREFIX = "/mnt/user-data/outputs/submarine/solver-dispatch/"


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _has_artifact(artifact_virtual_paths: Iterable[str], required_artifact: str) -> bool:
    return any(path.endswith(required_artifact) for path in artifact_virtual_paths)


def _load_verification_study_payloads(
    *,
    outputs_dir: Path | None,
    artifact_virtual_paths: list[str],
    required_artifacts: list[str],
) -> list[tuple[str, dict]]:
    if outputs_dir is None:
        return []
    return load_json_payloads_from_artifacts(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=artifact_virtual_paths,
        suffixes=required_artifacts,
    )


def _study_type_for_required_artifacts(
    required_artifacts: list[str],
) -> str | None:
    for artifact_name in required_artifacts:
        if not isinstance(artifact_name, str):
            continue
        normalized_name = Path(artifact_name).name
        if not (normalized_name.startswith("verification-") and normalized_name.endswith(".json")):
            continue
        study_type = normalized_name.removeprefix("verification-").removesuffix(".json")
        study_type = study_type.replace("-", "_")
        if study_type in _SCIENTIFIC_STUDY_TYPES:
            return study_type
    return None


def _solver_dispatch_run_root(virtual_path: str) -> str | None:
    if not isinstance(virtual_path, str) or not virtual_path.startswith(_SOLVER_DISPATCH_PREFIX):
        return None
    relative_parts = [part for part in virtual_path.removeprefix(_SOLVER_DISPATCH_PREFIX).split("/") if part]
    if not relative_parts:
        return None
    return f"{_SOLVER_DISPATCH_PREFIX}{relative_parts[0]}"


def _normalize_recovered_variant_payload(
    *,
    variant_payload: dict[str, object] | None,
    run_record_payload: dict | None,
) -> dict[str, object] | None:
    candidate_status = ""
    if isinstance(run_record_payload, Mapping):
        candidate_status = str(run_record_payload.get("execution_status") or "").strip().lower()
    if not candidate_status and isinstance(variant_payload, Mapping):
        candidate_status = str(variant_payload.get("execution_status") or "").strip().lower()

    if candidate_status == "blocked":
        return {"execution_status": "blocked", **(variant_payload or {})}
    if candidate_status != "completed":
        return {"execution_status": candidate_status or "planned"} if candidate_status else None
    return {"execution_status": "completed", **(variant_payload or {})}


def _recover_requirement_row_from_study_manifest(
    *,
    outputs_dir: Path | None,
    artifact_virtual_paths: list[str],
    matched_artifacts: list[str],
    required_artifacts: list[str],
    baseline_solver_results: Mapping[str, object] | None,
    requirement: SubmarineScientificVerificationRequirement,
) -> dict | None:
    if outputs_dir is None:
        return None

    study_type = _study_type_for_required_artifacts(required_artifacts)
    if study_type is None:
        return None

    manifest_candidates = load_json_payloads_from_artifacts(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=artifact_virtual_paths,
        suffixes=[_STUDY_MANIFEST_FILENAME],
    )
    expected_run_root = next(
        (run_root for run_root in (_solver_dispatch_run_root(path) for path in [*matched_artifacts, *artifact_virtual_paths]) if run_root),
        None,
    )
    if expected_run_root is not None:
        manifest_candidates = [item for item in manifest_candidates if _solver_dispatch_run_root(item[0]) == expected_run_root]
    if not manifest_candidates:
        return None

    _, manifest_payload = manifest_candidates[0]
    try:
        study_manifest = SubmarineScientificStudyManifest.model_validate(manifest_payload)
    except Exception:
        return None

    definition = next(
        (item for item in study_manifest.study_definitions if item.study_type == study_type),
        None,
    )
    if definition is None:
        return None

    study_variant_results: dict[str, dict[str, object] | None] = {}
    for variant in definition.variants:
        variant_payload: dict[str, object] | None = None
        if variant.solver_results_virtual_path:
            variant_payload = load_json_outputs_artifact(
                outputs_dir,
                variant.solver_results_virtual_path,
            )
        if variant.run_record_virtual_path and (variant_payload is None or not str(variant_payload.get("execution_status") or "").strip() or str(variant_payload.get("execution_status") or "").strip().lower() == "planned"):
            run_record_payload = load_json_outputs_artifact(
                outputs_dir,
                variant.run_record_virtual_path,
            )
        else:
            run_record_payload = None
        variant_payload = _normalize_recovered_variant_payload(
            variant_payload=variant_payload,
            run_record_payload=run_record_payload,
        )
        if variant_payload is not None:
            study_variant_results[variant.variant_id] = variant_payload

    recovered_results = build_completed_scientific_study_results(
        manifest=study_manifest,
        baseline_solver_results=baseline_solver_results,
        variant_results={study_type: study_variant_results},
    )
    recovered_result = next(
        (item for item in recovered_results if item.study_type == study_type),
        None,
    )
    if recovered_result is None:
        return None

    return {
        "status": recovered_result.status,
        "detail": f"{requirement.label}: {recovered_result.summary_zh}",
        "relative_spread": recovered_result.relative_spread,
    }


def _load_stability_evidence_payload(
    *,
    outputs_dir: Path | None,
    artifact_virtual_paths: list[str],
) -> dict | None:
    if outputs_dir is None:
        return None

    loaded = load_first_json_payload_from_artifacts(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=artifact_virtual_paths,
        suffixes=[_STABILITY_EVIDENCE_FILENAME],
    )
    if loaded is None:
        return None
    _, payload = loaded
    return payload


def _build_residual_requirement_evidence(
    requirement: SubmarineScientificVerificationRequirement,
    residual_summary: dict,
) -> dict:
    observed = residual_summary.get("max_final_residual")
    if not _is_number(observed):
        detail = f"{requirement.label}: residual summary is unavailable for this run."
        return {
            "status": "missing_evidence",
            "detail": detail,
            "observed_value": None,
            "limit_value": requirement.max_value,
        }

    observed_value = float(observed)
    if requirement.max_value is not None and observed_value <= requirement.max_value:
        detail = f"{requirement.label}: observed {observed_value:.6f} <= {requirement.max_value:.6f}."
        status = "passed"
    else:
        detail = f"{requirement.label}: observed {observed_value:.6f} exceeds limit {requirement.max_value:.6f}."
        status = "blocked"

    return {
        "status": status,
        "detail": detail,
        "observed_value": observed_value,
        "limit_value": requirement.max_value,
    }


def _build_force_tail_requirement_evidence(
    requirement: SubmarineScientificVerificationRequirement,
    force_history: list[dict],
) -> tuple[dict, dict]:
    coefficient = requirement.force_coefficient or "Cd"
    tail_count = requirement.minimum_history_samples or 5
    tail_samples = [
        {
            "time": float(item["Time"]) if _is_number(item.get("Time")) else None,
            "value": float(item[coefficient]),
        }
        for item in force_history[-tail_count:]
        if isinstance(item, dict) and _is_number(item.get(coefficient))
    ]
    observed_sample_count = len(tail_samples)
    limit = requirement.max_tail_relative_spread or 0.02
    if observed_sample_count < tail_count:
        detail = f"{requirement.label}: need at least {tail_count} {coefficient} samples in force coefficient history."
        requirement_row = {
            "status": "missing_evidence",
            "detail": detail,
            "force_coefficient": coefficient,
            "observed_sample_count": observed_sample_count,
            "required_sample_count": tail_count,
            "relative_spread": None,
            "max_tail_relative_spread": limit,
        }
        tail_payload = {
            "coefficient": coefficient,
            "status": "missing_evidence",
            "detail": detail,
            "observed_sample_count": observed_sample_count,
            "required_sample_count": tail_count,
            "relative_spread": None,
            "max_tail_relative_spread": limit,
            "tail_samples": tail_samples,
        }
        return requirement_row, tail_payload

    tail_values = [sample["value"] for sample in tail_samples]
    baseline = max(sum(abs(value) for value in tail_values) / len(tail_values), 1e-12)
    spread = (max(tail_values) - min(tail_values)) / baseline
    if spread <= limit:
        detail = f"{requirement.label}: tail relative spread {spread:.4f} <= {limit:.4f} for {coefficient}."
        status = "passed"
    else:
        detail = f"{requirement.label}: tail relative spread {spread:.4f} exceeds {limit:.4f} for {coefficient}."
        status = "blocked"

    requirement_row = {
        "status": status,
        "detail": detail,
        "force_coefficient": coefficient,
        "observed_sample_count": observed_sample_count,
        "required_sample_count": tail_count,
        "relative_spread": spread,
        "max_tail_relative_spread": limit,
    }
    tail_payload = {
        "coefficient": coefficient,
        "status": status,
        "detail": detail,
        "observed_sample_count": observed_sample_count,
        "required_sample_count": tail_count,
        "relative_spread": spread,
        "max_tail_relative_spread": limit,
        "tail_samples": tail_samples,
    }
    return requirement_row, tail_payload


def _merge_requirement_row(
    requirement: SubmarineScientificVerificationRequirement,
    row: dict,
) -> dict:
    return {
        "requirement_id": requirement.requirement_id,
        "label": requirement.label,
        "summary_zh": requirement.summary_zh,
        "check_type": requirement.check_type,
        "status": row.get("status"),
        "detail": row.get("detail"),
        "required_artifacts": requirement.required_artifacts,
        "force_coefficient": row.get("force_coefficient", requirement.force_coefficient),
        "minimum_history_samples": requirement.minimum_history_samples,
        "max_tail_relative_spread": row.get(
            "max_tail_relative_spread",
            requirement.max_tail_relative_spread,
        ),
        "max_value": requirement.max_value,
        "observed_value": row.get("observed_value"),
        "limit_value": row.get("limit_value", requirement.max_value),
        "observed_sample_count": row.get("observed_sample_count"),
        "required_sample_count": row.get("required_sample_count"),
        "relative_spread": row.get("relative_spread"),
    }


def _collect_requirement_outcome(
    *,
    requirement_row: dict,
    blocking_issues: list[str],
    missing_evidence: list[str],
    passed_requirements: list[str],
) -> None:
    detail = str(requirement_row.get("detail") or "").strip()
    status = str(requirement_row.get("status") or "").strip()
    if not detail:
        return
    if status == "blocked":
        blocking_issues.append(detail)
    elif status == "passed":
        passed_requirements.append(detail)
    else:
        missing_evidence.append(detail)


def _compose_stability_evidence_summary(
    *,
    status: str,
    passed_count: int,
    missing_count: int,
    blocked_count: int,
) -> str:
    if status == "passed":
        return "SCI-01 基线稳定性检查已通过，残差阈值与力系数尾段稳定性证据都满足当前案例要求。"
    if status == "blocked":
        return "SCI-01 基线稳定性检查未通过，至少一项残差或力系数尾段稳定性要求触发阻塞。"
    return "SCI-01 基线稳定性证据仍不完整，当前 run 需要补齐残差摘要或力系数历史后才能完成稳定性判断。"


def build_effective_scientific_verification_requirements(
    *,
    acceptance_profile: SubmarineCaseAcceptanceProfile | None,
    task_type: str,
) -> list[SubmarineScientificVerificationRequirement]:
    if acceptance_profile is None:
        return []

    requirements: list[SubmarineScientificVerificationRequirement] = []
    if acceptance_profile.max_final_residual is not None:
        requirements.append(
            SubmarineScientificVerificationRequirement(
                requirement_id="final_residual_threshold",
                label="Final residual threshold",
                summary_zh=("要求本次基线 run 的最大最终残差不高于案例 profile 规定阈值，否则当前结果不适合作为科研对比基线。"),
                check_type="max_final_residual",
                max_value=acceptance_profile.max_final_residual,
            )
        )

    if acceptance_profile.require_force_coefficients:
        spread_limit = 0.02 if task_type == "resistance" else 0.05
        requirements.append(
            SubmarineScientificVerificationRequirement(
                requirement_id="force_coefficient_tail_stability",
                label="Force coefficient tail stability",
                summary_zh=("要求力系数历史尾段已经收敛到稳定范围，避免把尚未稳定的解直接当成科研结论。"),
                check_type="force_coefficient_tail_stability",
                force_coefficient="Cd",
                minimum_history_samples=5,
                max_tail_relative_spread=spread_limit,
            )
        )

    requirements.extend(
        [
            SubmarineScientificVerificationRequirement(
                requirement_id="mesh_independence_study",
                label="Mesh independence study",
                summary_zh="要求补齐网格无关性研究证据，确认结果不由单一网格分辨率偶然决定。",
                check_type="artifact_presence",
                required_artifacts=["verification-mesh-independence.json"],
            ),
            SubmarineScientificVerificationRequirement(
                requirement_id="domain_sensitivity_study",
                label="Domain sensitivity study",
                summary_zh="要求补齐计算域尺寸敏感性研究证据，确认外边界设置不会显著扭曲结论。",
                check_type="artifact_presence",
                required_artifacts=["verification-domain-sensitivity.json"],
            ),
            SubmarineScientificVerificationRequirement(
                requirement_id="time_step_sensitivity_study",
                label="Time-step sensitivity study",
                summary_zh="要求补齐时间步敏感性研究证据，确认时间推进设置不会主导关键结果。",
                check_type="artifact_presence",
                required_artifacts=["verification-time-step-sensitivity.json"],
            ),
        ]
    )

    custom_by_id = {item.requirement_id: item for item in acceptance_profile.scientific_verification_requirements}
    merged: list[SubmarineScientificVerificationRequirement] = []
    for item in requirements:
        merged.append(custom_by_id.pop(item.requirement_id, item))
    merged.extend(custom_by_id.values())
    return merged


def build_stability_evidence(
    *,
    acceptance_profile: SubmarineCaseAcceptanceProfile | None,
    task_type: str,
    solver_metrics: dict | None,
    solver_results_virtual_path: str | None,
    artifact_virtual_path: str | None = None,
) -> dict | None:
    requirements = [
        requirement
        for requirement in build_effective_scientific_verification_requirements(
            acceptance_profile=acceptance_profile,
            task_type=task_type,
        )
        if requirement.check_type in _STABILITY_REQUIREMENT_TYPES
    ]
    if not requirements:
        return None

    requirement_rows: list[dict] = []
    blocking_issues: list[str] = []
    missing_evidence: list[str] = []
    passed_requirements: list[str] = []
    residual_summary = (solver_metrics or {}).get("residual_summary") or {}
    force_history = (solver_metrics or {}).get("force_coefficients_history") or []
    force_coefficient_tail: dict | None = None

    for requirement in requirements:
        if requirement.check_type == "max_final_residual":
            row = _merge_requirement_row(
                requirement,
                _build_residual_requirement_evidence(requirement, residual_summary),
            )
        else:
            row, force_coefficient_tail = _build_force_tail_requirement_evidence(
                requirement,
                force_history,
            )
            row = _merge_requirement_row(requirement, row)

        requirement_rows.append(row)
        _collect_requirement_outcome(
            requirement_row=row,
            blocking_issues=blocking_issues,
            missing_evidence=missing_evidence,
            passed_requirements=passed_requirements,
        )

    status = "blocked" if blocking_issues else "missing_evidence" if missing_evidence else "passed"

    return {
        "status": status,
        "summary_zh": _compose_stability_evidence_summary(
            status=status,
            passed_count=len(passed_requirements),
            missing_count=len(missing_evidence),
            blocked_count=len(blocking_issues),
        ),
        "source_solver_results_virtual_path": solver_results_virtual_path,
        "artifact_virtual_path": artifact_virtual_path,
        "residual_summary": residual_summary or None,
        "force_coefficient_tail": force_coefficient_tail,
        "requirements": requirement_rows,
        "blocking_issues": blocking_issues,
        "missing_evidence": missing_evidence,
        "passed_requirements": passed_requirements,
    }


def build_scientific_verification_assessment(
    *,
    acceptance_profile: SubmarineCaseAcceptanceProfile | None,
    task_type: str,
    solver_metrics: dict | None,
    artifact_virtual_paths: list[str],
    outputs_dir: Path | None = None,
    stability_evidence: dict | None = None,
) -> dict | None:
    requirements = build_effective_scientific_verification_requirements(
        acceptance_profile=acceptance_profile,
        task_type=task_type,
    )
    if not requirements:
        return None

    requirement_statuses: list[dict] = []
    blocking_issues: list[str] = []
    missing_evidence: list[str] = []
    passed_requirements: list[str] = []

    resolved_stability_evidence = stability_evidence or _load_stability_evidence_payload(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=artifact_virtual_paths,
    )
    stability_by_requirement = {str(item.get("requirement_id")): item for item in (resolved_stability_evidence or {}).get("requirements") or [] if isinstance(item, dict) and item.get("requirement_id")}
    residual_summary = (solver_metrics or {}).get("residual_summary") or {}
    force_history = (solver_metrics or {}).get("force_coefficients_history") or []

    for requirement in requirements:
        stability_row = stability_by_requirement.get(requirement.requirement_id)
        if stability_row is not None:
            requirement_row = _merge_requirement_row(requirement, stability_row)
        elif requirement.check_type == "max_final_residual":
            requirement_row = _merge_requirement_row(
                requirement,
                _build_residual_requirement_evidence(requirement, residual_summary),
            )
        elif requirement.check_type == "force_coefficient_tail_stability":
            requirement_row = _merge_requirement_row(
                requirement,
                _build_force_tail_requirement_evidence(requirement, force_history)[0],
            )
        else:
            matched = [artifact_path for artifact_path in artifact_virtual_paths if any(artifact_path.endswith(required_artifact) for required_artifact in requirement.required_artifacts)]
            study_payloads = _load_verification_study_payloads(
                outputs_dir=outputs_dir,
                artifact_virtual_paths=artifact_virtual_paths,
                required_artifacts=requirement.required_artifacts,
            )
            if study_payloads:
                artifact_path, payload = study_payloads[0]
                study_status = str(payload.get("status") or "").strip().lower()
                study_summary = str(payload.get("summary_zh") or payload.get("detail") or "").strip()
                if study_status in {"passed", "research_ready"}:
                    detail = f"{requirement.label}: {study_summary or 'study evidence passed'} ({artifact_path})."
                    status = "passed"
                elif study_status in {"failed", "blocked"}:
                    detail = f"{requirement.label}: {study_summary or 'study evidence failed'} ({artifact_path})."
                    status = "blocked"
                else:
                    detail = f"{requirement.label}: evidence artifact {artifact_path} exists, but its verification status is missing or unsupported."
                    status = "missing_evidence"
            elif matched:
                detail = f"{requirement.label}: evidence artifacts exist via {', '.join(matched)}, but structured verification payloads are unreadable or missing."
                status = "missing_evidence"
            else:
                detail = f"{requirement.label}: missing evidence artifacts {', '.join(requirement.required_artifacts) or 'for this study'}."
                status = "missing_evidence"

            recovered_requirement_row = None
            if status == "missing_evidence":
                recovered_requirement_row = _recover_requirement_row_from_study_manifest(
                    outputs_dir=outputs_dir,
                    artifact_virtual_paths=artifact_virtual_paths,
                    matched_artifacts=matched,
                    required_artifacts=requirement.required_artifacts,
                    baseline_solver_results=solver_metrics,
                    requirement=requirement,
                )
                if isinstance(recovered_requirement_row, dict) and str(recovered_requirement_row.get("status") or "").strip() in {"passed", "blocked"}:
                    status = str(recovered_requirement_row["status"])
                    detail = str(recovered_requirement_row.get("detail") or detail)

            requirement_row = _merge_requirement_row(
                requirement,
                recovered_requirement_row
                if isinstance(recovered_requirement_row, dict) and str(recovered_requirement_row.get("status") or "").strip() == status
                else {
                    "status": status,
                    "detail": detail,
                },
            )

        requirement_statuses.append(requirement_row)
        _collect_requirement_outcome(
            requirement_row=requirement_row,
            blocking_issues=blocking_issues,
            missing_evidence=missing_evidence,
            passed_requirements=passed_requirements,
        )

    if blocking_issues:
        status = "blocked"
        confidence = "low"
    elif missing_evidence:
        status = "needs_more_verification"
        confidence = "medium"
    else:
        status = "research_ready"
        confidence = "high"

    return {
        "status": status,
        "confidence": confidence,
        "requirement_count": len(requirement_statuses),
        "requirements": requirement_statuses,
        "blocking_issues": blocking_issues,
        "missing_evidence": missing_evidence,
        "passed_requirements": passed_requirements,
    }
