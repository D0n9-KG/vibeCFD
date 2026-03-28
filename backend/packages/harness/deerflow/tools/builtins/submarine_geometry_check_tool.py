"""Built-in DeerFlow tool for submarine geometry inspection."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.typing import ContextT

from deerflow.agents.thread_state import ThreadState
from deerflow.config.paths import VIRTUAL_PATH_PREFIX, get_paths
from deerflow.domain.submarine.contracts import (
    build_execution_plan,
    build_runtime_event,
    build_runtime_snapshot,
    extend_runtime_timeline,
)
from deerflow.domain.submarine.geometry_check import (
    SUPPORTED_GEOMETRY_SUFFIXES,
    run_geometry_check,
)
from deerflow.domain.submarine.solver_dispatch import STL_READY_EXECUTION


def _get_thread_id(runtime: ToolRuntime[ContextT, ThreadState]) -> str:
    thread_id = runtime.context.get("thread_id") if runtime.context else None
    if not thread_id:
        raise ValueError("Thread ID is not available in runtime context")
    return thread_id


def _get_thread_dir(runtime: ToolRuntime[ContextT, ThreadState], key: str) -> Path:
    thread_data = (runtime.state or {}).get("thread_data") or {}
    raw_path = thread_data.get(key)
    if not raw_path:
        raise ValueError(f"Thread data missing required path: {key}")
    return Path(raw_path).resolve()


def _resolve_geometry_path(
    runtime: ToolRuntime[ContextT, ThreadState],
    geometry_path: str | None,
) -> Path:
    thread_id = _get_thread_id(runtime)
    uploads_dir = _get_thread_dir(runtime, "uploads_path")
    user_data_dir = uploads_dir.parent

    if geometry_path:
        stripped = geometry_path.lstrip("/")
        virtual_prefix = VIRTUAL_PATH_PREFIX.lstrip("/")
        if stripped == virtual_prefix or stripped.startswith(virtual_prefix + "/"):
            resolved = get_paths().resolve_virtual_path(thread_id, geometry_path)
        else:
            resolved = Path(geometry_path).expanduser().resolve()
            try:
                resolved.relative_to(user_data_dir)
            except ValueError as exc:
                raise ValueError("Geometry path must stay inside the current thread user-data directory") from exc
    else:
        candidates = sorted(
            (
                candidate
                for candidate in uploads_dir.iterdir()
                if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_GEOMETRY_SUFFIXES
            ),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            raise ValueError("No .stl geometry file was found in the current thread uploads directory")
        resolved = candidates[0]

    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"Geometry file not found: {geometry_path or resolved}")

    if resolved.suffix.lower() not in SUPPORTED_GEOMETRY_SUFFIXES:
        raise ValueError(
            f"Only STL (.stl) geometry files are supported in v1; received {resolved.suffix}"
        )

    return resolved


def _to_virtual_thread_path(runtime: ToolRuntime[ContextT, ThreadState], actual_path: Path) -> str:
    uploads_dir = _get_thread_dir(runtime, "uploads_path")
    user_data_dir = uploads_dir.parent.resolve()
    relative = actual_path.resolve().relative_to(user_data_dir)
    return f"{VIRTUAL_PATH_PREFIX}/{relative.as_posix()}"


@tool("submarine_geometry_check", parse_docstring=True)
def submarine_geometry_check_tool(
    runtime: ToolRuntime[ContextT, ThreadState],
    geometry_path: str | None,
    task_description: str,
    task_type: str = "resistance",
    geometry_family_hint: str | None = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Inspect submarine geometry and emit DeerFlow artifacts.

    Use this tool when the user uploads a submarine geometry file and wants a
    domain-specific preflight result instead of generic file analysis.

    Args:
        geometry_path: Optional path to the geometry file. Prefer a `/mnt/user-data/uploads/...` path. When omitted, the latest uploaded `.stl` is used.
        task_description: Task goal in natural language, for example "检查这个潜艇外形是否适合阻力分析".
        task_type: CFD task type such as `resistance`, `pressure_distribution`, or `wake_field`.
        geometry_family_hint: Optional family hint such as `DARPA SUBOFF` or `Type 209`.
    """
    try:
        resolved_geometry_path = _resolve_geometry_path(runtime, geometry_path)
        outputs_dir = _get_thread_dir(runtime, "outputs_path")
        result, artifacts = run_geometry_check(
            geometry_path=resolved_geometry_path,
            outputs_dir=outputs_dir,
            task_description=task_description or "执行潜艇几何检查",
            task_type=task_type or "resistance",
            geometry_family_hint=geometry_family_hint,
        )
    except ValueError as exc:
        return Command(
            update={
                "messages": [ToolMessage(f"Error: {exc}", tool_call_id=tool_call_id)],
            }
        )

    existing_runtime = (runtime.state or {}).get("submarine_runtime")
    runtime_snapshot = build_runtime_snapshot(
        current_stage="geometry-preflight",
        task_summary=task_description,
        task_type=task_type or "resistance",
        geometry_virtual_path=_to_virtual_thread_path(runtime, resolved_geometry_path),
        geometry_family=result.geometry.geometry_family,
        execution_readiness=STL_READY_EXECUTION,
        selected_case_id=result.candidate_cases[0].case_id if result.candidate_cases else None,
        simulation_requirements=(existing_runtime or {}).get("simulation_requirements"),
        requested_outputs=(existing_runtime or {}).get("requested_outputs"),
        output_delivery_plan=(existing_runtime or {}).get("output_delivery_plan"),
        next_recommended_stage=result.next_recommended_stage,
        report_virtual_path=result.report_virtual_path,
        artifact_virtual_paths=result.artifact_virtual_paths,
        execution_plan=build_execution_plan(
            confirmation_status="confirmed",
            existing_plan=(existing_runtime or {}).get("execution_plan"),
            stage_updates={
                "claude-code-supervisor": "completed",
                "task-intelligence": "completed",
                "geometry-preflight": "completed",
                "solver-dispatch": "ready",
            },
        ),
        review_status=result.review_status,
        activity_timeline=extend_runtime_timeline(
            existing_runtime,
            build_runtime_event(
                stage="geometry-preflight",
                actor="geometry-preflight",
                title="完成潜艇几何预检",
                summary=result.summary_zh,
                status=result.review_status,
            ),
        ),
    )
    detail_lines = "\n".join(f"- {artifact}" for artifact in artifacts)
    message = (
        f"{result.summary_zh}\n"
        f"已登记 {len(artifacts)} 个 DeerFlow artifacts，可在工作区直接查看：\n{detail_lines}"
    )
    return Command(
        update={
            "artifacts": artifacts,
            "submarine_runtime": runtime_snapshot.model_dump(mode="json"),
            "messages": [ToolMessage(message, tool_call_id=tool_call_id)],
        }
    )
