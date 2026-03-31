"""Helpers for recovering submarine design-brief context across tool boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from deerflow.domain.submarine.artifact_store import (
    load_first_json_payload_from_artifacts,
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
    "actual openfoam",
    "real openfoam",
)
_PREFLIGHT_THEN_EXECUTE_KEYWORDS = (
    "先做预检",
    "先预检再执行",
    "若通过再继续",
    "预检后再执行",
    "preflight then execute",
)
_PLAN_ONLY_KEYWORDS = (
    "仅做几何预检",
    "仅做预检",
    "只做预检",
    "不实际计算",
    "不执行计算",
    "plan only",
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


def _contains_any(description: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in description for keyword in keywords)


def _looks_like_confirm_then_execute(description: str) -> bool:
    return _contains_any(description, _CONFIRMATION_KEYWORDS) and _contains_any(
        description, _CONTINUE_EXECUTION_KEYWORDS
    )


def infer_execution_preference(
    task_description: str | None,
) -> SubmarineExecutionPreference:
    description = (task_description or "").strip().lower()
    if _contains_any(description, _PLAN_ONLY_KEYWORDS):
        return "plan_only"
    if _contains_any(description, _PREFLIGHT_THEN_EXECUTE_KEYWORDS) or (
        _looks_like_confirm_then_execute(description)
    ):
        return "preflight_then_execute"
    if _contains_any(description, _DIRECT_EXECUTION_KEYWORDS):
        return "execute_now"
    return "plan_only"


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
