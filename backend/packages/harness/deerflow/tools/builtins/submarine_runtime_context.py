"""Helpers for recovering submarine design-brief context across tool boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from deerflow.config.paths import VIRTUAL_PATH_PREFIX, get_paths
from deerflow.domain.submarine.artifact_store import (
    load_first_json_payload_from_artifacts,
)
from deerflow.domain.submarine.calculation_plan import (
    calculation_plan_requires_confirmation,
    calculation_plan_requires_immediate_confirmation,
)
from deerflow.domain.submarine.geometry_check import SUPPORTED_GEOMETRY_SUFFIXES
from deerflow.domain.submarine.official_case_seed_resolver import (
    resolve_official_case_seed,
)

SubmarineExecutionPreference = Literal[
    "plan_only",
    "execute_now",
    "preflight_then_execute",
]

_DIRECT_EXECUTION_KEYWORDS = (
    "直接执行",
    "直接发起",
    "直接开始",
    "立即执行",
    "立即计算",
    "真实求解",
    "执行案例",
    "运行案例",
    "组装并执行",
    "actual openfoam",
    "real openfoam",
    "execute_now",
    "execution_preference=execute_now",
)
_PREFLIGHT_THEN_EXECUTE_KEYWORDS = (
    "先做预检",
    "先预检再执行",
    "若通过再继续",
    "预检后再执行",
    "preflight then execute",
    "preflight_then_execute",
    "execution_preference=preflight_then_execute",
)
_PLAN_ONLY_KEYWORDS = (
    "仅做几何预检",
    "仅做预检",
    "只做预检",
    "不实际计算",
    "不执行计算",
    "不要启动求解",
    "不启动求解",
    "先不要启动求解",
    "不要启动计算",
    "不启动计算",
    "先不要启动计算",
    "\u5148\u4e0d\u8981\u5b9e\u9645\u6267\u884c",
    "\u7b49\u6211\u786e\u8ba4\u540e\u518d\u6267\u884c",
    "\u7b49\u6211\u786e\u8ba4\u540e\u518d\u8fd0\u884c",
    "\u7b49\u6211\u786e\u8ba4\u540e\u518d\u6c42\u89e3",
    "do not run the solver until i explicitly confirm",
    "do not run the solver until i confirm",
    "wait for my confirmation before execution",
    "hold solver execution",
    "plan only",
    "plan_only",
    "execution_preference=plan_only",
)
_CONFIRMATION_KEYWORDS = (
    "确认方案",
    "确认当前方案",
    "确认后",
    "按当前方案",
    "沿当前方案",
    "confirm the plan",
    "confirm current brief",
)
_CONTINUE_EXECUTION_KEYWORDS = (
    "开始执行",
    "继续执行",
    "开始计算",
    "继续计算",
    "开始算",
    "继续算",
    "start execution",
    "continue execution",
    "proceed with execution",
)

_OFFICIAL_CASE_INTENT_KEYWORDS = (
    "不要走 stl",
    "不走 stl",
    "not stl",
    "do not use stl",
    "official case reconstruction",
    "official openfoam",
    "official cavity",
    "official pitzdaily",
    "按官方 openfoam",
    "按官方案例",
    "官方 openfoam",
    "官方 cavity",
    "官方 pitzdaily",
)


def _contains_any(description: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in description for keyword in keywords)


def _looks_like_confirm_then_execute(description: str) -> bool:
    return _contains_any(description, _CONFIRMATION_KEYWORDS) and _contains_any(
        description, _CONTINUE_EXECUTION_KEYWORDS
    )


def detect_execution_preference_signal(
    task_description: str | None,
) -> SubmarineExecutionPreference | None:
    description = (task_description or "").strip().lower()
    if not description:
        return None
    if _contains_any(description, _PLAN_ONLY_KEYWORDS):
        return "plan_only"
    if _contains_any(description, _PREFLIGHT_THEN_EXECUTE_KEYWORDS) or (
        _looks_like_confirm_then_execute(description)
    ):
        return "preflight_then_execute"
    if _contains_any(description, _DIRECT_EXECUTION_KEYWORDS):
        return "execute_now"
    return None


def detect_official_case_seed_intent(task_description: str | None) -> bool:
    description = (task_description or "").strip().lower()
    if not description:
        return False
    return _contains_any(description, _OFFICIAL_CASE_INTENT_KEYWORDS)


def has_structured_official_case_intent(task_type: str | None) -> bool:
    return str(task_type or "").strip().lower() == "official_openfoam_case"


def infer_execution_preference(
    task_description: str | None,
) -> SubmarineExecutionPreference:
    return detect_execution_preference_signal(task_description) or "plan_only"


def resolve_execution_preference(
    *,
    explicit_preference: str | None,
    existing_runtime: Mapping[str, Any] | None,
    existing_brief: Mapping[str, Any] | None,
    task_description: str | None,
) -> SubmarineExecutionPreference:
    runtime_preference = (
        str((existing_runtime or {}).get("execution_preference") or "").strip()
    )
    brief_preference = (
        str((existing_brief or {}).get("execution_preference") or "").strip()
    )
    if explicit_preference:
        return explicit_preference  # type: ignore[return-value]
    if runtime_preference:
        return runtime_preference  # type: ignore[return-value]
    if brief_preference:
        return brief_preference  # type: ignore[return-value]
    return infer_execution_preference(task_description)


def resolve_task_summary(
    *,
    explicit_task_description: str | None,
    existing_runtime: Mapping[str, Any] | None,
    existing_brief: Mapping[str, Any] | None,
    fallback_task_description: str,
) -> str:
    brief_task_description = (
        str((existing_brief or {}).get("task_description") or "").strip()
    )
    runtime_task_summary = (
        str((existing_runtime or {}).get("task_summary") or "").strip()
    )
    explicit_task_summary = str(explicit_task_description or "").strip()
    fallback_summary = str(fallback_task_description or "").strip()
    return (
        brief_task_description
        or explicit_task_summary
        or runtime_task_summary
        or fallback_summary
    )


def resolve_confirmation_status(
    *,
    existing_runtime: Mapping[str, Any] | None,
    existing_brief: Mapping[str, Any] | None,
) -> Literal["draft", "confirmed"]:
    raw_status = (
        str((existing_brief or {}).get("confirmation_status") or "").strip()
        or str((existing_runtime or {}).get("confirmation_status") or "").strip()
        or "draft"
    )
    return "confirmed" if raw_status == "confirmed" else "draft"


def requires_user_confirmation(
    *,
    existing_runtime: Mapping[str, Any] | None,
    existing_brief: Mapping[str, Any] | None,
    target_stage: Literal["geometry-preflight", "solver-dispatch"] = "solver-dispatch",
    task_description: str | None = None,
) -> bool:
    calculation_plan = (
        (existing_runtime or {}).get("calculation_plan")
        or (existing_brief or {}).get("calculation_plan")
    )
    runtime_preference = str((existing_runtime or {}).get("execution_preference") or "").strip()
    brief_preference = str((existing_brief or {}).get("execution_preference") or "").strip()
    explicit_signal = detect_execution_preference_signal(task_description)
    execution_preference = (
        runtime_preference
        or brief_preference
        or explicit_signal
    )

    if (
        target_stage == "geometry-preflight"
        and execution_preference == "plan_only"
        and not calculation_plan_requires_immediate_confirmation(calculation_plan)
    ):
        return False

    if calculation_plan_requires_confirmation(calculation_plan):
        return True

    approval_state = (
        str((existing_brief or {}).get("approval_state") or "").strip()
        or str((existing_runtime or {}).get("approval_state") or "").strip()
    )
    if approval_state == "approved":
        return False

    if (
        resolve_confirmation_status(
            existing_runtime=existing_runtime,
            existing_brief=existing_brief,
        )
        == "confirmed"
    ):
        return False

    review_status = (
        (existing_brief or {}).get("review_status")
        or (existing_runtime or {}).get("review_status")
    )
    next_stage = (
        (existing_brief or {}).get("next_recommended_stage")
        or (existing_runtime or {}).get("next_recommended_stage")
    )
    return (
        review_status == "needs_user_confirmation"
        or next_stage == "user-confirmation"
    )


def _localize_blocked_stage_label(blocked_stage_label: str) -> str:
    mapping = {
        "Geometry preflight": "几何预检",
        "Solver dispatch": "求解准备",
    }
    return mapping.get(blocked_stage_label, blocked_stage_label)


def _localize_retry_action(
    *, retry_tool_name: str, blocked_stage_label: str
) -> str:
    mapping = {
        "submarine_geometry_check": "继续几何预检",
        "submarine_solver_dispatch": "继续求解准备",
    }
    return mapping.get(
        retry_tool_name,
        f"继续{_localize_blocked_stage_label(blocked_stage_label)}",
    )


def build_user_confirmation_block_message(
    *,
    existing_runtime: Mapping[str, Any] | None,
    existing_brief: Mapping[str, Any] | None,
    blocked_stage_label: str,
    retry_tool_name: str,
) -> str:
    stage_label = _localize_blocked_stage_label(blocked_stage_label)
    retry_action = _localize_retry_action(
        retry_tool_name=retry_tool_name,
        blocked_stage_label=blocked_stage_label,
    )
    task_summary = (
        (existing_brief or {}).get("task_description")
        or (existing_runtime or {}).get("task_summary")
        or "当前潜艇 CFD 研究任务"
    )
    calculation_plan = (
        (existing_runtime or {}).get("calculation_plan")
        or (existing_brief or {}).get("calculation_plan")
    )
    if calculation_plan_requires_confirmation(calculation_plan):
        if calculation_plan_requires_immediate_confirmation(calculation_plan):
            return (
                f"{stage_label}需要先完成研究者确认。"
                f"当前计算方案里还有需要立即确认的条目，请先在协商区补充或修订相关假设，"
                f"更新设计简报后，再{retry_action}。"
            )
        return (
            f"{stage_label}需要先完成研究者确认。"
            f"请先在协商区确认 {task_summary} 对应的几何、工况与计算方案，"
            f"更新设计简报后，再{retry_action}。"
        )
    return (
        f"{stage_label}需要先完成研究者确认。"
        f"请先在协商区确认 {task_summary} 涉及的工况与约束，"
        f"更新设计简报后，再{retry_action}。"
    )


def _normalize_geometry_candidate(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if Path(candidate).suffix.lower() not in SUPPORTED_GEOMETRY_SUFFIXES:
        return None
    return candidate


def _resolve_geometry_candidate_path(
    *,
    candidate: str,
    thread_id: str,
    uploads_dir: Path,
) -> Path | None:
    stripped = candidate.lstrip("/")
    virtual_prefix = VIRTUAL_PATH_PREFIX.lstrip("/")
    user_data_dir = uploads_dir.parent.resolve()

    if stripped == virtual_prefix or stripped.startswith(virtual_prefix + "/"):
        try:
            resolved = get_paths().resolve_virtual_path(thread_id, candidate)
        except ValueError:
            return None
    else:
        resolved = Path(candidate).expanduser().resolve()
        try:
            resolved.relative_to(user_data_dir)
        except ValueError:
            return None

    if not resolved.exists() or not resolved.is_file():
        return None
    if resolved.suffix.lower() not in SUPPORTED_GEOMETRY_SUFFIXES:
        return None
    return resolved


def _to_virtual_thread_path(uploads_dir: Path, actual_path: Path) -> str:
    user_data_dir = uploads_dir.parent.resolve()
    relative = actual_path.resolve().relative_to(user_data_dir)
    return f"{VIRTUAL_PATH_PREFIX}/{relative.as_posix()}"


def _is_supported_geometry_virtual_path(candidate: object) -> bool:
    if not isinstance(candidate, str):
        return False
    return Path(candidate).suffix.lower() in SUPPORTED_GEOMETRY_SUFFIXES


def resolve_bound_geometry_virtual_path(
    *,
    thread_id: str,
    uploads_dir: Path,
    explicit_geometry_path: str | None,
    existing_runtime: Mapping[str, Any] | None,
    existing_brief: Mapping[str, Any] | None,
    uploaded_files: list[dict] | None,
) -> str | None:
    """Return the best recoverable thread-bound geometry virtual path.

    Precedence:
    1. explicit geometry path when it resolves to a valid STL inside thread user-data
    2. `submarine_runtime.geometry_virtual_path`
    3. design-brief `geometry_virtual_path`
    4. `uploaded_files[*].path`
    5. latest STL under the thread uploads directory
    """

    explicit_candidate = (
        explicit_geometry_path.strip()
        if isinstance(explicit_geometry_path, str)
        else None
    )
    if explicit_candidate:
        resolved_explicit = _resolve_geometry_candidate_path(
            candidate=explicit_candidate,
            thread_id=thread_id,
            uploads_dir=uploads_dir,
        )
        if resolved_explicit is not None:
            return _to_virtual_thread_path(uploads_dir, resolved_explicit)
        explicit_suffix = Path(explicit_candidate).suffix.lower()
        if explicit_suffix and explicit_suffix not in SUPPORTED_GEOMETRY_SUFFIXES:
            return explicit_candidate

    candidate_values: list[str] = []
    for value in (
        (existing_runtime or {}).get("geometry_virtual_path"),
        (existing_brief or {}).get("geometry_virtual_path"),
    ):
        normalized = _normalize_geometry_candidate(value)
        if normalized and normalized not in candidate_values:
            candidate_values.append(normalized)

    for uploaded in uploaded_files or []:
        if not isinstance(uploaded, Mapping):
            continue
        normalized = _normalize_geometry_candidate(uploaded.get("path"))
        if normalized and normalized not in candidate_values:
            candidate_values.append(normalized)

    for candidate in candidate_values:
        resolved = _resolve_geometry_candidate_path(
            candidate=candidate,
            thread_id=thread_id,
            uploads_dir=uploads_dir,
        )
        if resolved is not None:
            return _to_virtual_thread_path(uploads_dir, resolved)

    if not uploads_dir.exists():
        return None

    candidates = sorted(
        (
            candidate
            for candidate in uploads_dir.iterdir()
            if candidate.is_file()
            and candidate.suffix.lower() in SUPPORTED_GEOMETRY_SUFFIXES
        ),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None
    return _to_virtual_thread_path(uploads_dir, candidates[0])


def resolve_runtime_input_source(
    *,
    thread_id: str,
    uploads_dir: Path,
    explicit_geometry_path: str | None,
    existing_runtime: Mapping[str, Any] | None,
    existing_brief: Mapping[str, Any] | None,
    uploaded_files: list[dict] | None,
    task_description: str | None,
    task_type: str | None = None,
) -> dict[str, Any]:
    official_case_seed = resolve_official_case_seed(uploads_dir=uploads_dir)
    geometry_virtual_path = resolve_bound_geometry_virtual_path(
        thread_id=thread_id,
        uploads_dir=uploads_dir,
        explicit_geometry_path=explicit_geometry_path,
        existing_runtime=existing_runtime,
        existing_brief=existing_brief,
        uploaded_files=uploaded_files,
    )
    explicit_official_case_intent = detect_official_case_seed_intent(
        task_description
    ) or has_structured_official_case_intent(task_type)
    has_supported_geometry_candidate = _is_supported_geometry_virtual_path(
        geometry_virtual_path
    )

    if official_case_seed and official_case_seed.status == "partial":
        return {
            "kind": "partial_case_seed",
            "official_case_id": official_case_seed.case_id,
            "seed_virtual_paths": official_case_seed.seed_virtual_paths,
            "user_message": official_case_seed.user_message,
        }

    if official_case_seed and has_supported_geometry_candidate:
        if explicit_official_case_intent:
            return {
                "kind": "openfoam_case_seed",
                "official_case_id": official_case_seed.case_id,
                "seed_virtual_paths": official_case_seed.seed_virtual_paths,
            }
        return {
            "kind": "ambiguous",
            "user_message": (
                "Both a valid STL input and an official OpenFOAM case seed were found. "
                "Please confirm whether this thread should use the official OpenFOAM case reconstruction path "
                "or the STL-based submarine workflow."
            ),
        }

    if official_case_seed:
        return {
            "kind": "openfoam_case_seed",
            "official_case_id": official_case_seed.case_id,
            "seed_virtual_paths": official_case_seed.seed_virtual_paths,
        }

    if geometry_virtual_path:
        return {
            "kind": "geometry_seed",
            "geometry_virtual_path": geometry_virtual_path,
        }

    return {
        "kind": "missing",
        "user_message": "No valid STL geometry or supported official OpenFOAM case seed was found in the current thread uploads.",
    }


def load_existing_design_brief_payload(
    *,
    outputs_dir: Path,
    state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(state, Mapping):
        return {}

    runtime_state = state.get("submarine_runtime")
    if not isinstance(runtime_state, Mapping):
        runtime_state = {}

    artifact_candidates: list[str] = []
    report_virtual_path = runtime_state.get("report_virtual_path")
    if (
        isinstance(report_virtual_path, str)
        and report_virtual_path.endswith("/cfd-design-brief.md")
    ):
        artifact_candidates.append(report_virtual_path[:-3] + "json")

    for source in (
        runtime_state.get("artifact_virtual_paths"),
        state.get("artifacts"),
    ):
        if not isinstance(source, list):
            continue
        for path in source:
            if (
                isinstance(path, str)
                and path.endswith("/cfd-design-brief.json")
                and path not in artifact_candidates
            ):
                artifact_candidates.append(path)

    loaded = load_first_json_payload_from_artifacts(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=artifact_candidates,
        suffixes=("/cfd-design-brief.json",),
    )
    if loaded is None:
        return {}

    _, payload = loaded
    return payload
