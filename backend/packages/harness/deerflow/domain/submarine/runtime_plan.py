"""Helpers for surfacing scientific capabilities and runtime truth."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import ExecutionPlanStatus, SubmarineRuntimeStatus

_RUNTIME_RUNNING_STATUSES = {"in_progress", "running", "streaming"}
_RUNTIME_BLOCKED_STATUSES = {"blocked", "waiting_user"}
_RUNTIME_FAILED_STATUSES = {"failed", "error"}
_RUNTIME_COMPLETED_STATUSES = {"executed", "completed"}

_STAGE_ARTIFACT_LABELS = {
    "report_virtual_path": "阶段报告",
    "request_virtual_path": "求解请求",
    "execution_log_virtual_path": "执行日志",
    "solver_results_virtual_path": "求解结果",
}


def _as_mapping(value: object | None) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _as_int(value: object | None) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _as_str(value: object | None) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_lower(value: object | None) -> str | None:
    normalized = _as_str(value)
    return normalized.lower() if normalized else None


def _map_scientific_study_status(value: object | None) -> ExecutionPlanStatus:
    if value == "completed":
        return "completed"
    if value == "blocked":
        return "blocked"
    if value == "in_progress":
        return "in_progress"
    if value == "planned":
        return "ready"
    return "pending"


def _build_experiment_compare_status(
    *,
    experiment_status: object | None,
    compare_count: object | None,
) -> ExecutionPlanStatus:
    if experiment_status == "blocked":
        return "blocked"
    if _as_int(compare_count) and _as_int(compare_count) > 0:
        return "completed"
    if experiment_status == "completed":
        return "ready"
    return "pending"


def _build_scientific_verification_status(
    *,
    verification_status: object | None,
    dispatch_status: object | None = None,
) -> ExecutionPlanStatus:
    if verification_status == "blocked":
        return "blocked"
    if verification_status in {"passed", "needs_more_verification"}:
        return "completed"
    if dispatch_status == "executed":
        return "ready"
    return "pending"


def _build_scientific_followup_status(
    *,
    handoff_status: object | None,
    followup_entry_count: object | None,
) -> ExecutionPlanStatus:
    if _as_int(followup_entry_count) and _as_int(followup_entry_count) > 0:
        return "completed"
    if handoff_status == "not_needed":
        return "completed"
    if handoff_status in {"ready_for_auto_followup", "manual_followup_required"}:
        return "ready"
    return "pending"


def _required_runtime_artifacts(
    *,
    current_stage: object | None,
    stage_status: object | None,
) -> tuple[str, ...]:
    stage = _normalize_lower(current_stage)
    normalized_stage_status = _normalize_lower(stage_status)
    required: list[str] = ["report_virtual_path"]

    if stage == "solver-dispatch":
        required.append("request_virtual_path")
        if normalized_stage_status in _RUNTIME_COMPLETED_STATUSES | _RUNTIME_FAILED_STATUSES:
            required.append("execution_log_virtual_path")
        if normalized_stage_status in _RUNTIME_COMPLETED_STATUSES:
            required.append("solver_results_virtual_path")
    elif stage == "result-reporting":
        required.append("solver_results_virtual_path")

    return tuple(required)


def _build_missing_artifact_detail(
    *,
    current_stage: object | None,
    stage_status: object | None,
    report_virtual_path: object | None,
    request_virtual_path: object | None,
    execution_log_virtual_path: object | None,
    solver_results_virtual_path: object | None,
) -> str | None:
    stage_artifacts = {
        "report_virtual_path": _as_str(report_virtual_path),
        "request_virtual_path": _as_str(request_virtual_path),
        "execution_log_virtual_path": _as_str(execution_log_virtual_path),
        "solver_results_virtual_path": _as_str(solver_results_virtual_path),
    }
    missing_labels = [
        _STAGE_ARTIFACT_LABELS[key]
        for key in _required_runtime_artifacts(
            current_stage=current_stage,
            stage_status=stage_status,
        )
        if not stage_artifacts.get(key)
    ]
    if not missing_labels:
        return None

    stage = _normalize_lower(current_stage) or "current-stage"
    missing_text = "、".join(missing_labels)
    return f"{stage} 缺少可恢复的关键证据: {missing_text}。"


def _derive_runtime_status(
    *,
    stage_status: object | None,
    review_status: object | None,
    execution_readiness: object | None,
    missing_artifact_detail: str | None,
) -> SubmarineRuntimeStatus:
    normalized_stage_status = _normalize_lower(stage_status)
    normalized_review_status = _normalize_lower(review_status)

    if execution_readiness == "geometry_conversion_required":
        return "blocked"
    if missing_artifact_detail:
        return "blocked"
    if normalized_stage_status in _RUNTIME_FAILED_STATUSES:
        return "failed"
    if normalized_review_status == "blocked" or normalized_stage_status in _RUNTIME_BLOCKED_STATUSES:
        return "blocked"
    if normalized_stage_status in _RUNTIME_RUNNING_STATUSES:
        return "running"
    if normalized_stage_status in _RUNTIME_COMPLETED_STATUSES:
        return "completed"
    return "ready"


def _build_default_runtime_summary(
    *,
    current_stage: object | None,
    runtime_status: SubmarineRuntimeStatus,
    review_status: object | None,
    execution_readiness: object | None,
    missing_artifact_detail: str | None,
) -> str:
    stage = _normalize_lower(current_stage)
    normalized_review_status = _normalize_lower(review_status)

    if runtime_status == "blocked":
        if execution_readiness == "geometry_conversion_required":
            return "当前几何还不能直接进入 STL 求解链路，运行已暂停。"
        if missing_artifact_detail:
            return "当前线程缺少可恢复的运行证据，工作台会把它显示为阻塞而不是普通待执行。"
        if normalized_review_status == "blocked":
            return "当前运行已经被阻塞，需要先处理阻塞原因后才能继续。"
        return "当前运行已阻塞。"

    if runtime_status == "failed":
        return "当前运行已失败，请先检查日志与求解输出后再重试。"

    if runtime_status == "running":
        if stage == "solver-dispatch":
            return "OpenFOAM 求解正在运行，日志、结果与后处理证据会持续写回。"
        return "当前阶段正在执行，刷新后会继续从已持久化的运行态恢复。"

    if runtime_status == "completed":
        if stage == "solver-dispatch":
            return "求解已完成，结果证据已经落盘，可以继续进入结果整理。"
        if stage == "result-reporting":
            return "结果报告已生成，可以继续进入 Supervisor 复核。"
        return "当前阶段已完成。"

    if normalized_review_status == "needs_user_confirmation":
        return "当前方案已整理完成，但仍有待确认条件。"
    if stage == "geometry-preflight":
        return "几何预检完成，可以继续进入求解派发。"
    if stage == "solver-dispatch":
        return "求解派发方案已准备好，可以直接执行或继续补充参数。"
    return "当前研究链路已准备就绪。"


def _build_default_recovery_guidance(
    *,
    runtime_status: SubmarineRuntimeStatus,
    review_status: object | None,
    execution_readiness: object | None,
    missing_artifact_detail: str | None,
) -> str | None:
    normalized_review_status = _normalize_lower(review_status)

    if runtime_status == "blocked":
        if execution_readiness == "geometry_conversion_required":
            return "先回到几何预检阶段，完成几何清洗或格式转换后，再重新发起求解派发。"
        if missing_artifact_detail:
            return "补齐缺失 artifacts，或重新运行当前阶段，确保请求、日志与结果文件重新注册到线程。"
        if normalized_review_status == "blocked":
            return "根据阻塞说明补齐缺失边界条件、验证证据或运行产物，然后从当前线程继续恢复。"
        return "处理阻塞原因后，从当前线程继续恢复。"

    if runtime_status == "failed":
        return "优先检查 openfoam-run.log 与 solver-results.json，修正命令、网格或边界条件后再重试。"

    if normalized_review_status == "needs_user_confirmation":
        return "先确认边界条件、输出需求与 baseline 案例，再继续执行。"

    if runtime_status == "completed":
        return "可以继续进入下一阶段，或刷新页面重新检查最新证据。"

    return None


def build_runtime_status_payload(
    *,
    current_stage: object | None,
    next_recommended_stage: object | None = None,
    stage_status: object | None = None,
    review_status: object | None = None,
    execution_readiness: object | None = None,
    report_virtual_path: object | None = None,
    request_virtual_path: object | None = None,
    execution_log_virtual_path: object | None = None,
    solver_results_virtual_path: object | None = None,
    artifact_virtual_paths: object | None = None,
    runtime_status: SubmarineRuntimeStatus | None = None,
    runtime_summary: str | None = None,
    recovery_guidance: str | None = None,
    blocker_detail: str | None = None,
) -> dict[str, SubmarineRuntimeStatus | str | None]:
    del next_recommended_stage, artifact_virtual_paths

    missing_artifact_detail = _build_missing_artifact_detail(
        current_stage=current_stage,
        stage_status=stage_status,
        report_virtual_path=report_virtual_path,
        request_virtual_path=request_virtual_path,
        execution_log_virtual_path=execution_log_virtual_path,
        solver_results_virtual_path=solver_results_virtual_path,
    )
    resolved_status = runtime_status or _derive_runtime_status(
        stage_status=stage_status,
        review_status=review_status,
        execution_readiness=execution_readiness,
        missing_artifact_detail=missing_artifact_detail,
    )

    resolved_blocker_detail = blocker_detail or missing_artifact_detail
    if resolved_status == "failed" and resolved_blocker_detail is None:
        resolved_blocker_detail = "运行日志标记为失败，请检查求解命令、网格质量和边界条件。"
    if (
        resolved_status == "blocked"
        and resolved_blocker_detail is None
        and execution_readiness == "geometry_conversion_required"
    ):
        resolved_blocker_detail = "当前几何仍需要清洗或格式转换，不能直接进入 STL-only 求解链路。"

    resolved_summary = runtime_summary
    if not resolved_summary or resolved_status in {"blocked", "failed"}:
        resolved_summary = _build_default_runtime_summary(
            current_stage=current_stage,
            runtime_status=resolved_status,
            review_status=review_status,
            execution_readiness=execution_readiness,
            missing_artifact_detail=missing_artifact_detail,
        )

    resolved_guidance = recovery_guidance or _build_default_recovery_guidance(
        runtime_status=resolved_status,
        review_status=review_status,
        execution_readiness=execution_readiness,
        missing_artifact_detail=missing_artifact_detail,
    )

    return {
        "runtime_status": resolved_status,
        "runtime_summary": resolved_summary,
        "recovery_guidance": resolved_guidance,
        "blocker_detail": resolved_blocker_detail,
    }


def build_scientific_capability_updates_for_dispatch(
    payload: Mapping[str, object],
) -> dict[str, ExecutionPlanStatus]:
    study_manifest = _as_mapping(payload.get("scientific_study_manifest"))
    experiment_manifest = _as_mapping(payload.get("experiment_manifest"))
    run_compare_summary = _as_mapping(payload.get("run_compare_summary"))
    dispatch_status = payload.get("dispatch_status")

    return {
        "scientific-study": _map_scientific_study_status(
            study_manifest.get("study_execution_status")
        ),
        "experiment-compare": _build_experiment_compare_status(
            experiment_status=experiment_manifest.get("experiment_status"),
            compare_count=len(run_compare_summary.get("comparisons") or []),
        ),
        "scientific-verification": _build_scientific_verification_status(
            verification_status=None,
            dispatch_status=dispatch_status,
        ),
        "scientific-followup": "pending",
    }


def build_scientific_capability_updates_for_report(
    payload: Mapping[str, object],
) -> dict[str, ExecutionPlanStatus]:
    study_summary = _as_mapping(payload.get("scientific_study_summary"))
    experiment_summary = _as_mapping(payload.get("experiment_summary"))
    experiment_compare_summary = _as_mapping(payload.get("experiment_compare_summary"))
    scientific_verification_assessment = _as_mapping(
        payload.get("scientific_verification_assessment")
    )
    scientific_remediation_handoff = _as_mapping(
        payload.get("scientific_remediation_handoff")
    )
    scientific_followup_summary = _as_mapping(payload.get("scientific_followup_summary"))

    return {
        "scientific-study": _map_scientific_study_status(
            study_summary.get("study_execution_status")
        ),
        "experiment-compare": _build_experiment_compare_status(
            experiment_status=experiment_summary.get("experiment_status"),
            compare_count=experiment_compare_summary.get("compare_count"),
        ),
        "scientific-verification": _build_scientific_verification_status(
            verification_status=scientific_verification_assessment.get("status")
        ),
        "scientific-followup": _build_scientific_followup_status(
            handoff_status=scientific_remediation_handoff.get("handoff_status"),
            followup_entry_count=scientific_followup_summary.get("entry_count"),
        ),
    }


__all__ = [
    "build_runtime_status_payload",
    "build_scientific_capability_updates_for_dispatch",
    "build_scientific_capability_updates_for_report",
]
