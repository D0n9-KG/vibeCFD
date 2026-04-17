"""Built-in DeerFlow tool for submarine solver dispatch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from langchain.tools import InjectedToolCallId, ToolRuntime, tool
from langchain_core.messages import HumanMessage, ToolMessage
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
from deerflow.domain.submarine.geometry_check import SUPPORTED_GEOMETRY_SUFFIXES
from deerflow.domain.submarine.official_case_assembly import (
    assemble_official_case_seed,
)
from deerflow.domain.submarine.official_case_profiles import (
    get_official_case_default_simulation_requirements,
    should_pin_official_case_defaults,
)
from deerflow.domain.submarine.official_case_validation import (
    build_official_case_validation_assessment,
)
from deerflow.domain.submarine.provenance import (
    build_provenance_approval_snapshot,
    build_provenance_summary,
    build_run_provenance_manifest,
)
from deerflow.domain.submarine.runtime_plan import (
    build_runtime_status_payload,
    build_scientific_capability_updates_for_dispatch,
)
from deerflow.domain.submarine.solver_dispatch import run_solver_dispatch
from deerflow.domain.submarine.solver_dispatch_results import (
    collect_solver_results,
    looks_like_solver_failure,
    render_solver_results_markdown_enriched,
)
from deerflow.sandbox import get_sandbox_provider
from deerflow.sandbox.tools import ensure_thread_directories_exist
from deerflow.tools.builtins.submarine_runtime_context import (
    build_user_confirmation_block_message,
    detect_execution_preference_signal,
    load_existing_design_brief_payload,
    requires_user_confirmation,
    resolve_bound_geometry_virtual_path,
    resolve_confirmation_status,
    resolve_execution_preference,
    resolve_runtime_input_source,
    resolve_task_summary,
)


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
                raise ValueError(
                    "Geometry path must stay inside the current thread user-data directory",
                ) from exc
    else:
        if not uploads_dir.exists():
            raise ValueError(
                "No .stl geometry file was found in the current thread uploads directory",
            )
        candidates = sorted(
            (candidate for candidate in uploads_dir.iterdir() if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_GEOMETRY_SUFFIXES),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            raise ValueError(
                "No .stl geometry file was found in the current thread uploads directory",
            )
        resolved = candidates[0]

    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"Geometry file not found: {geometry_path or resolved}")

    if resolved.suffix.lower() not in SUPPORTED_GEOMETRY_SUFFIXES:
        raise ValueError(
            f"Only STL (.stl) geometry files are supported in v1; received {resolved.suffix}",
        )

    return resolved


def _to_virtual_thread_path(
    runtime: ToolRuntime[ContextT, ThreadState],
    actual_path: Path,
) -> str:
    uploads_dir = _get_thread_dir(runtime, "uploads_path")
    user_data_dir = uploads_dir.parent.resolve()
    relative = actual_path.resolve().relative_to(user_data_dir)
    return f"{VIRTUAL_PATH_PREFIX}/{relative.as_posix()}"


def _latest_human_message_text(runtime: ToolRuntime[ContextT, ThreadState]) -> str:
    messages = (runtime.state or {}).get("messages")
    if not isinstance(messages, list):
        return ""
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = [
                    str(item.get("text") or "")
                    for item in content
                    if isinstance(item, dict) and item.get("type") == "text"
                ]
                return "\n".join(part for part in parts if part)
            return str(content)
    return ""


def _get_execute_command(runtime: ToolRuntime[ContextT, ThreadState]):
    try:
        sandbox_state = (runtime.state or {}).get("sandbox") or {}
        sandbox_id = sandbox_state.get("sandbox_id")
        provider = get_sandbox_provider()
        sandbox = provider.get(sandbox_id) if sandbox_id else None
        if sandbox is None:
            thread_id = _get_thread_id(runtime)
            sandbox_id = provider.acquire(thread_id)
            if runtime.state is not None:
                runtime.state["sandbox"] = {"sandbox_id": sandbox_id}
            sandbox = provider.get(sandbox_id)
            if sandbox is None:
                return None
            if runtime.context is not None:
                runtime.context["sandbox_id"] = sandbox_id
        ensure_thread_directories_exist(runtime)
    except Exception:
        return None
    return sandbox.execute_command


def _official_case_run_dir_name(official_case_id: str | None) -> str:
    candidate = (official_case_id or "official-case").strip()
    return candidate or "official-case"


def _official_case_request_virtual_path(run_dir_name: str, filename: str) -> str:
    return f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/{filename}"


def _official_case_summary(
    *,
    official_case_id: str,
    dispatch_status: str,
    execute_now: bool,
) -> str:
    if dispatch_status == "executed":
        return (
            f"官方 OpenFOAM 案例 `{official_case_id}` 已完成 case 组装并执行求解，"
            "运行产物、追溯清单与 dispatch 摘要已经写回当前线程。"
        )
    if dispatch_status == "failed":
        return (
            f"官方 OpenFOAM 案例 `{official_case_id}` 已完成 case 组装，但求解执行失败。"
            "请先检查执行日志与 provenance 清单，再决定是否重试。"
        )
    if execute_now:
        return (
            f"官方 OpenFOAM 案例 `{official_case_id}` 已完成 case 组装，"
            "但当前线程没有可用执行器，暂未真正启动求解。"
        )
    return (
        f"官方 OpenFOAM 案例 `{official_case_id}` 已完成 case 组装并生成 dispatch 产物，"
        "当前仍处于待执行状态。"
    )


def _official_case_dispatch_markdown(payload: dict[str, object]) -> str:
    seed_lines = "\n".join(
        f"- `{path}`" for path in (payload.get("official_case_seed_virtual_paths") or [])
    ) or "- none"
    assembled_lines = "\n".join(
        f"- `{path}`" for path in (payload.get("assembled_case_virtual_paths") or [])
    ) or "- none"
    return "\n".join(
        [
            "# 官方 OpenFOAM 案例 Dispatch 摘要",
            "",
            payload["summary_zh"],
            "",
            f"- dispatch_status: `{payload['dispatch_status']}`",
            f"- task_type: `{payload['task_type']}`",
            f"- official_case_id: `{payload['official_case_id']}`",
            f"- execution_preference: `{payload['execution_preference']}`",
            f"- request_virtual_path: `{payload['request_virtual_path']}`",
            f"- report_virtual_path: `{payload['report_virtual_path']}`",
            f"- run_script_virtual_path: `{payload['run_script_virtual_path']}`",
            "",
            "## Imported Seeds",
            seed_lines,
            "",
            "## Assembled Case Files",
            assembled_lines,
            "",
            "## Solver Command",
            f"```bash\n{payload.get('solver_command') or 'not-bound'}\n```",
            "",
        ]
    )


def _official_case_dispatch_html(payload: dict[str, object]) -> str:
    seed_items = "".join(
        f"<li><code>{path}</code></li>"
        for path in (payload.get("official_case_seed_virtual_paths") or [])
    ) or "<li>none</li>"
    assembled_items = "".join(
        f"<li><code>{path}</code></li>"
        for path in (payload.get("assembled_case_virtual_paths") or [])
    ) or "<li>none</li>"
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>官方 OpenFOAM 案例 Dispatch 摘要</title>
  </head>
  <body>
    <h1>官方 OpenFOAM 案例 Dispatch 摘要</h1>
    <p>{payload["summary_zh"]}</p>
    <p><strong>dispatch_status:</strong> {payload["dispatch_status"]}</p>
    <p><strong>official_case_id:</strong> {payload["official_case_id"]}</p>
    <p><strong>request_virtual_path:</strong> {payload["request_virtual_path"]}</p>
    <p><strong>run_script_virtual_path:</strong> {payload["run_script_virtual_path"]}</p>
    <h2>Imported Seeds</h2>
    <ul>{seed_items}</ul>
    <h2>Assembled Case Files</h2>
    <ul>{assembled_items}</ul>
    <h2>Solver Command</h2>
    <pre>{payload.get("solver_command") or "not-bound"}</pre>
  </body>
</html>
"""


def _run_official_case_dispatch(
    *,
    runtime: ToolRuntime[ContextT, ThreadState],
    existing_runtime: dict,
    outputs_dir: Path,
    uploads_dir: Path,
    workspace_dir: Path,
    task_description: str,
    task_type: str,
    confirmation_status: str,
    execution_preference: str,
    official_case_id: str,
    official_case_seed_virtual_paths: list[str],
    official_case_profile: dict[str, object] | None,
    simulation_requirements: dict[str, float | int],
    execute_now: bool,
    execute_command,
    tool_call_id: str,
) -> Command:
    run_dir_name = _official_case_run_dir_name(official_case_id)
    artifact_dir = outputs_dir / "submarine" / "solver-dispatch" / run_dir_name
    artifact_dir.mkdir(parents=True, exist_ok=True)

    request_path = artifact_dir / "openfoam-request.json"
    markdown_path = artifact_dir / "dispatch-summary.md"
    html_path = artifact_dir / "dispatch-summary.html"
    handoff_path = artifact_dir / "supervisor-handoff.json"
    provenance_manifest_path = artifact_dir / "provenance-manifest.json"
    official_case_validation_path = artifact_dir / "official-case-parity.json"
    log_path = artifact_dir / "openfoam-run.log"
    solver_results_json_path = artifact_dir / "solver-results.json"
    solver_results_md_path = artifact_dir / "solver-results.md"

    request_virtual_path = _official_case_request_virtual_path(
        run_dir_name, "openfoam-request.json"
    )
    report_virtual_path = _official_case_request_virtual_path(
        run_dir_name, "dispatch-summary.md"
    )
    run_result = assemble_official_case_seed(
        case_id=official_case_id,
        seed_virtual_paths=official_case_seed_virtual_paths,
        uploads_dir=uploads_dir,
        workspace_dir=workspace_dir,
        outputs_dir=outputs_dir,
        run_dir_name=run_dir_name,
        source_commit=str((official_case_profile or {}).get("source_commit") or ""),
        simulation_requirements=simulation_requirements,
    )

    solver_command = f"bash {run_result.run_script_virtual_path}"
    dispatch_status = "planned"
    execution_log_virtual_path = None
    solver_results_virtual_path = None
    solver_results_markdown_virtual_path = None
    solver_results = None
    official_case_validation_virtual_path = _official_case_request_virtual_path(
        run_dir_name, "official-case-parity.json"
    )
    if execute_now and execute_command is not None:
        command_output = execute_command(solver_command)
        log_path.write_text(command_output, encoding="utf-8")
        execution_log_virtual_path = _official_case_request_virtual_path(
            run_dir_name, "openfoam-run.log"
        )
        solver_results = collect_solver_results(
            case_dir=run_result.assembled_case_dir,
            run_dir_name=run_dir_name,
            command_output=command_output,
            reference_values={
                "reference_length_m": 1.0,
                "reference_area_m2": 1.0,
                "inlet_velocity_mps": float(
                    simulation_requirements.get("inlet_velocity_mps") or 1.0
                ),
                "fluid_density_kg_m3": float(
                    simulation_requirements.get("fluid_density_kg_m3") or 1.0
                ),
            },
            simulation_requirements=simulation_requirements,
        )
        solver_results_json_path.write_text(
            json.dumps(solver_results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        solver_results_md_path.write_text(
            render_solver_results_markdown_enriched(solver_results),
            encoding="utf-8",
        )
        solver_results_virtual_path = _official_case_request_virtual_path(
            run_dir_name, "solver-results.json"
        )
        solver_results_markdown_virtual_path = _official_case_request_virtual_path(
            run_dir_name, "solver-results.md"
        )
        dispatch_status = (
            "failed"
            if looks_like_solver_failure(command_output)
            or not bool(solver_results.get("solver_completed"))
            else "executed"
        )

    official_case_validation_assessment = build_official_case_validation_assessment(
        case_id=official_case_id,
        solver_results=solver_results,
        assembled_case_dir=run_result.assembled_case_dir,
    )
    official_case_validation_path.write_text(
        json.dumps(
            official_case_validation_assessment, ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )

    artifact_virtual_paths = [
        request_virtual_path,
        report_virtual_path,
        _official_case_request_virtual_path(run_dir_name, "dispatch-summary.html"),
        _official_case_request_virtual_path(run_dir_name, "supervisor-handoff.json"),
        _official_case_request_virtual_path(run_dir_name, "provenance-manifest.json"),
        official_case_validation_virtual_path,
    ]
    if execution_log_virtual_path:
        artifact_virtual_paths.append(execution_log_virtual_path)
    if solver_results_virtual_path:
        artifact_virtual_paths.append(solver_results_virtual_path)
    if solver_results_markdown_virtual_path:
        artifact_virtual_paths.append(solver_results_markdown_virtual_path)

    next_recommended_stage = (
        "result-reporting" if dispatch_status == "executed" else "solver-dispatch"
    )
    review_status = "blocked" if dispatch_status == "failed" else "ready_for_supervisor"
    approval_snapshot = build_provenance_approval_snapshot(
        confirmation_status=confirmation_status,
        review_status=review_status,
        next_recommended_stage=next_recommended_stage,
        pending_calculation_plan=False,
        requires_immediate_confirmation=False,
        selected_reference_inputs=None,
    )
    provenance_manifest = build_run_provenance_manifest(
        experiment_id=f"official-{run_dir_name}",
        run_id="baseline",
        task_type=task_type,
        input_source_type="openfoam_case_seed",
        geometry_virtual_path="",
        geometry_family=None,
        official_case_id=official_case_id,
        official_case_seed_virtual_paths=official_case_seed_virtual_paths,
        assembled_case_virtual_paths=run_result.assembled_case_virtual_paths,
        selected_case_id=official_case_id,
        file_sources=run_result.file_sources,
        requested_outputs=[],
        simulation_requirements=simulation_requirements,
        approval_snapshot=approval_snapshot,
        artifact_entrypoints={
            "request": request_virtual_path,
            "dispatch_summary_markdown": report_virtual_path,
            "dispatch_summary_html": _official_case_request_virtual_path(
                run_dir_name, "dispatch-summary.html"
            ),
            **(
                {"solver_results": solver_results_virtual_path}
                if solver_results_virtual_path
                else {}
            ),
        },
        environment_fingerprint={},
        environment_parity_assessment={},
    ).model_dump(mode="json")
    provenance_manifest_path.write_text(
        json.dumps(provenance_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    provenance_summary = build_provenance_summary(
        manifest_virtual_path=_official_case_request_virtual_path(
            run_dir_name, "provenance-manifest.json"
        ),
        manifest_payload=provenance_manifest,
    )

    payload = {
        "task_description": task_description,
        "task_type": task_type,
        "confirmation_status": confirmation_status,
        "execution_preference": execution_preference,
        "dispatch_status": dispatch_status,
        "input_source_type": "openfoam_case_seed",
        "official_case_id": official_case_id,
        "official_case_seed_virtual_paths": official_case_seed_virtual_paths,
        "assembled_case_virtual_paths": run_result.assembled_case_virtual_paths,
        "official_case_profile": official_case_profile
        or {
            "case_id": official_case_id,
            "source_commit": run_result.execution_profile.source_commit,
            "source_kind": "pinned_official_source",
            "source_paths": [run_result.execution_profile.tutorial_root],
            "command_chain": run_result.execution_profile.command_chain,
        },
        "geometry_virtual_path": "",
        "geometry_family": None,
        "report_virtual_path": report_virtual_path,
        "request_virtual_path": request_virtual_path,
        "workspace_case_dir_virtual_path": (
            f"/mnt/user-data/workspace/official-openfoam/{run_dir_name}/openfoam-case"
        ),
        "run_script_virtual_path": run_result.run_script_virtual_path,
        "provenance_manifest_virtual_path": _official_case_request_virtual_path(
            run_dir_name, "provenance-manifest.json"
        ),
        "provenance_summary": provenance_summary,
        "official_case_validation_virtual_path": official_case_validation_virtual_path,
        "official_case_validation_assessment": official_case_validation_assessment,
        "execution_log_virtual_path": execution_log_virtual_path,
        "solver_results_virtual_path": solver_results_virtual_path,
        "solver_results_markdown_virtual_path": solver_results_markdown_virtual_path,
        "artifact_virtual_paths": artifact_virtual_paths,
        "solver_command": solver_command,
        "simulation_requirements": simulation_requirements,
    }
    payload["summary_zh"] = _official_case_summary(
        official_case_id=official_case_id,
        dispatch_status=dispatch_status,
        execute_now=execute_now,
    )

    request_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(
        _official_case_dispatch_markdown(payload),
        encoding="utf-8",
    )
    html_path.write_text(
        _official_case_dispatch_html(payload),
        encoding="utf-8",
    )
    supervisor_handoff = {
        "task_summary": task_description,
        "confirmation_status": confirmation_status,
        "execution_preference": execution_preference,
        "task_type": task_type,
        "input_source_type": "openfoam_case_seed",
        "official_case_id": official_case_id,
        "official_case_seed_virtual_paths": official_case_seed_virtual_paths,
        "assembled_case_virtual_paths": run_result.assembled_case_virtual_paths,
        "report_virtual_path": report_virtual_path,
        "artifact_virtual_paths": artifact_virtual_paths,
        "request_virtual_path": request_virtual_path,
        "provenance_manifest_virtual_path": payload["provenance_manifest_virtual_path"],
        "provenance_summary": provenance_summary,
        "official_case_validation_virtual_path": official_case_validation_virtual_path,
        "official_case_validation_assessment": official_case_validation_assessment,
        "workspace_case_dir_virtual_path": payload["workspace_case_dir_virtual_path"],
        "run_script_virtual_path": run_result.run_script_virtual_path,
        "review_status": review_status,
        "next_recommended_stage": next_recommended_stage,
    }
    handoff_path.write_text(
        json.dumps(supervisor_handoff, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    execution_updates = {
        "claude-code-supervisor": "completed",
        "task-intelligence": "completed",
        "geometry-preflight": "completed",
        "solver-dispatch": (
            "completed"
            if dispatch_status == "executed"
            else ("blocked" if dispatch_status == "failed" else "in_progress")
        ),
        "result-reporting": ("ready" if dispatch_status == "executed" else "pending"),
    }
    runtime_truth = build_runtime_status_payload(
        current_stage="solver-dispatch",
        next_recommended_stage=next_recommended_stage,
        stage_status=dispatch_status,
        review_status=review_status,
        execution_readiness=None,
        report_virtual_path=report_virtual_path,
        request_virtual_path=request_virtual_path,
        execution_log_virtual_path=execution_log_virtual_path,
        solver_results_virtual_path=solver_results_virtual_path,
        artifact_virtual_paths=artifact_virtual_paths,
        runtime_summary=payload["summary_zh"],
    )
    runtime_snapshot = build_runtime_snapshot(
        current_stage="solver-dispatch",
        task_summary=task_description,
        confirmation_status=confirmation_status,
        execution_preference=execution_preference,
        task_type=task_type,
        input_source_type="openfoam_case_seed",
        geometry_virtual_path="",
        geometry_family=None,
        official_case_id=official_case_id,
        official_case_seed_virtual_paths=official_case_seed_virtual_paths,
        assembled_case_virtual_paths=run_result.assembled_case_virtual_paths,
        official_case_profile=payload["official_case_profile"],
        official_case_validation_virtual_path=official_case_validation_virtual_path,
        official_case_validation_assessment=official_case_validation_assessment,
        selected_case_id=official_case_id,
        simulation_requirements=simulation_requirements,
        stage_status=dispatch_status,
        runtime_status=runtime_truth["runtime_status"],
        runtime_summary=runtime_truth["runtime_summary"],
        recovery_guidance=runtime_truth["recovery_guidance"],
        blocker_detail=runtime_truth["blocker_detail"],
        workspace_case_dir_virtual_path=payload["workspace_case_dir_virtual_path"],
        run_script_virtual_path=run_result.run_script_virtual_path,
        request_virtual_path=request_virtual_path,
        provenance_manifest_virtual_path=payload["provenance_manifest_virtual_path"],
        execution_log_virtual_path=execution_log_virtual_path,
        solver_results_virtual_path=solver_results_virtual_path,
        provenance_summary=provenance_summary,
        next_recommended_stage=next_recommended_stage,
        report_virtual_path=report_virtual_path,
        artifact_virtual_paths=artifact_virtual_paths,
        execution_plan=build_execution_plan(
            confirmation_status=confirmation_status,
            existing_plan=existing_runtime.get("execution_plan"),
            stage_updates=execution_updates,
        ),
        review_status=review_status,
        activity_timeline=extend_runtime_timeline(
            existing_runtime,
            build_runtime_event(
                stage="solver-dispatch",
                actor="solver-dispatch",
                title="Updated official OpenFOAM case dispatch",
                summary=payload["summary_zh"],
                status=dispatch_status,
            ),
        ),
    )
    detail_lines = "\n".join(f"- {artifact}" for artifact in artifact_virtual_paths)
    message = (
        f"{payload['summary_zh']}\n"
        f"已登记 {len(artifact_virtual_paths)} 项研究产物，可在工作区直接查看：\n{detail_lines}"
    )
    return Command(
        update={
            "artifacts": artifact_virtual_paths,
            "submarine_runtime": runtime_snapshot.model_dump(mode="json"),
            "messages": [ToolMessage(message, tool_call_id=tool_call_id)],
        }
    )


@tool("submarine_solver_dispatch", parse_docstring=True)
def submarine_solver_dispatch_tool(
    runtime: ToolRuntime[ContextT, ThreadState],
    task_description: str,
    geometry_path: str | None = None,
    task_type: str = "resistance",
    geometry_family_hint: str | None = None,
    selected_case_id: str | None = None,
    inlet_velocity_mps: float | None = None,
    fluid_density_kg_m3: float | None = None,
    kinematic_viscosity_m2ps: float | None = None,
    end_time_seconds: float | None = None,
    delta_t_seconds: float | None = None,
    write_interval_steps: int | None = None,
    contract_revision: int | None = None,
    iteration_mode: str | None = None,
    revision_summary: str | None = None,
    execute_now: bool | None = None,
    execute_scientific_studies: bool = False,
    custom_variants: list[dict] | None = None,
    solver_command: str | None = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Prepare or execute a controlled OpenFOAM-style solver dispatch for a submarine task.

    Args:
        geometry_path: Optional geometry file path. Prefer `/mnt/user-data/uploads/...`. When omitted, use the runtime-bound path or latest uploaded `.stl`.
        task_description: Task goal in natural language.
        task_type: CFD task type such as `resistance`, `pressure_distribution`, or `wake_field`.
        geometry_family_hint: Optional family hint such as `DARPA SUBOFF` or `Type 209`.
        selected_case_id: Optional case ID to force the selected template.
        inlet_velocity_mps: Optional inlet velocity for the CFD case.
        fluid_density_kg_m3: Optional fluid density for the CFD case.
        kinematic_viscosity_m2ps: Optional kinematic viscosity for the CFD case.
        end_time_seconds: Optional solver end time.
        delta_t_seconds: Optional solver deltaT.
        write_interval_steps: Optional write interval in time steps.
        execute_now: Whether to execute the dispatch command immediately inside the current DeerFlow sandbox. When omitted, recover the latest confirmed execution intent from the design brief.
        execute_scientific_studies: Whether to execute the planned scientific study variants in addition to the baseline run.
        custom_variants: Optional custom experiment variants to register in the experiment manifest alongside the baseline and scientific-study variants.
        solver_command: Optional command to run when `execute_now=true`, for example `simpleFoam -case /mnt/user-data/workspace/case`.
    """
    try:
        existing_runtime = (runtime.state or {}).get("submarine_runtime") or {}
        outputs_dir = _get_thread_dir(runtime, "outputs_path")
        uploads_dir = _get_thread_dir(runtime, "uploads_path")
        existing_brief = load_existing_design_brief_payload(
            outputs_dir=outputs_dir,
            state=runtime.state,
        )
        if requires_user_confirmation(
            existing_runtime=existing_runtime,
            existing_brief=existing_brief,
            target_stage="solver-dispatch",
        ):
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            build_user_confirmation_block_message(
                                existing_runtime=existing_runtime,
                                existing_brief=existing_brief,
                                blocked_stage_label="Solver dispatch",
                                retry_tool_name="submarine_solver_dispatch",
                            ),
                            tool_call_id=tool_call_id,
                        )
                    ]
                }
            )

        existing_requirements = existing_runtime.get("simulation_requirements") or existing_brief.get("simulation_requirements") or {}
        resolved_task_description = resolve_task_summary(
            explicit_task_description=task_description,
            existing_runtime=existing_runtime,
            existing_brief=existing_brief,
            fallback_task_description="Prepare a submarine solver dispatch plan",
        )
        latest_user_message_text = _latest_human_message_text(runtime)
        intent_description = "\n".join(
            part
            for part in (latest_user_message_text, resolved_task_description)
            if part
        )
        resolved_task_type = task_type or existing_runtime.get("task_type") or existing_brief.get("task_type") or "resistance"
        resolved_geometry_family_hint = geometry_family_hint if geometry_family_hint is not None else existing_runtime.get("geometry_family") or existing_brief.get("geometry_family_hint")
        resolved_selected_case_id = selected_case_id if selected_case_id is not None else existing_runtime.get("selected_case_id") or existing_brief.get("selected_case_id")
        thread_id = _get_thread_id(runtime)
        resolved_input_source = resolve_runtime_input_source(
            thread_id=thread_id,
            uploads_dir=uploads_dir,
            explicit_geometry_path=geometry_path,
            existing_runtime=existing_runtime,
            existing_brief=existing_brief,
            uploaded_files=(runtime.state or {}).get("uploaded_files"),
            task_description=resolved_task_description,
            task_type=resolved_task_type,
        )
        if resolved_input_source.get("kind") in {"partial_case_seed", "ambiguous"}:
            raise ValueError(
                str(
                    resolved_input_source.get("user_message")
                    or "Unsupported runtime input state"
                )
            )
        workspace_dir = _get_thread_dir(runtime, "workspace_path")
        resolved_confirmation_status = resolve_confirmation_status(
            existing_runtime=existing_runtime,
            existing_brief=existing_brief,
        )
        explicit_execution_preference = "execute_now" if execute_now is True else "plan_only" if execute_now is False else None
        resolved_execution_preference = resolve_execution_preference(
            explicit_preference=(
                explicit_execution_preference
                or detect_execution_preference_signal(latest_user_message_text)
            ),
            existing_runtime=existing_runtime,
            existing_brief=existing_brief,
            task_description=intent_description,
        )
        requirement_defaults = dict(existing_requirements)
        allow_explicit_requirement_overrides = True
        if resolved_input_source.get("kind") == "openfoam_case_seed":
            official_case_id = str(resolved_input_source.get("official_case_id") or "")
            resolved_task_type = "official_openfoam_case"
            resolved_selected_case_id = official_case_id
            official_case_requirement_defaults = (
                get_official_case_default_simulation_requirements(official_case_id)
            )
            if should_pin_official_case_defaults(intent_description):
                requirement_defaults = official_case_requirement_defaults
                allow_explicit_requirement_overrides = False
            else:
                requirement_defaults = {
                    **official_case_requirement_defaults,
                    **existing_requirements,
                }

        resolved_execute_now = execute_now
        if resolved_execute_now is None:
            resolved_execute_now = execute_scientific_studies or (resolved_confirmation_status == "confirmed" and resolved_execution_preference == "execute_now")
        execute_command = _get_execute_command(runtime) if resolved_execute_now else None
        resolved_simulation_requirements = {
            key: value
            for key, value in {
                "inlet_velocity_mps": (
                    inlet_velocity_mps
                    if allow_explicit_requirement_overrides
                    and inlet_velocity_mps is not None
                    else requirement_defaults.get("inlet_velocity_mps")
                ),
                "fluid_density_kg_m3": (
                    fluid_density_kg_m3
                    if allow_explicit_requirement_overrides
                    and fluid_density_kg_m3 is not None
                    else requirement_defaults.get("fluid_density_kg_m3")
                ),
                "kinematic_viscosity_m2ps": (
                    kinematic_viscosity_m2ps
                    if allow_explicit_requirement_overrides
                    and kinematic_viscosity_m2ps is not None
                    else requirement_defaults.get("kinematic_viscosity_m2ps")
                ),
                "end_time_seconds": (
                    end_time_seconds
                    if allow_explicit_requirement_overrides
                    and end_time_seconds is not None
                    else requirement_defaults.get("end_time_seconds")
                ),
                "delta_t_seconds": (
                    delta_t_seconds
                    if allow_explicit_requirement_overrides
                    and delta_t_seconds is not None
                    else requirement_defaults.get("delta_t_seconds")
                ),
                "write_interval_steps": (
                    write_interval_steps
                    if allow_explicit_requirement_overrides
                    and write_interval_steps is not None
                    else requirement_defaults.get("write_interval_steps")
                ),
            }.items()
            if value is not None
        }

        if resolved_input_source.get("kind") == "openfoam_case_seed":
            official_case_id = str(resolved_input_source.get("official_case_id") or "")
            official_case_seed_virtual_paths = list(
                resolved_input_source.get("seed_virtual_paths") or []
            )
            official_case_profile = (
                existing_runtime.get("official_case_profile")
                or existing_brief.get("official_case_profile")
            )
            return _run_official_case_dispatch(
                runtime=runtime,
                existing_runtime=existing_runtime,
                outputs_dir=outputs_dir,
                uploads_dir=uploads_dir,
                workspace_dir=workspace_dir,
                task_description=resolved_task_description,
                task_type=resolved_task_type,
                confirmation_status=resolved_confirmation_status,
                execution_preference=resolved_execution_preference,
                official_case_id=official_case_id,
                official_case_seed_virtual_paths=official_case_seed_virtual_paths,
                official_case_profile=official_case_profile,
                simulation_requirements=resolved_simulation_requirements,
                execute_now=bool(resolved_execute_now),
                execute_command=execute_command,
                tool_call_id=tool_call_id,
            )

        resolved_geometry_input = resolve_bound_geometry_virtual_path(
            thread_id=thread_id,
            uploads_dir=uploads_dir,
            explicit_geometry_path=geometry_path,
            existing_runtime=existing_runtime,
            existing_brief=existing_brief,
            uploaded_files=(runtime.state or {}).get("uploaded_files"),
        )
        resolved_geometry_path = _resolve_geometry_path(runtime, resolved_geometry_input)
        geometry_virtual_path = _to_virtual_thread_path(runtime, resolved_geometry_path)
        payload, artifacts = run_solver_dispatch(
            geometry_path=resolved_geometry_path,
            outputs_dir=outputs_dir,
            workspace_dir=workspace_dir,
            task_description=resolved_task_description,
            task_type=resolved_task_type,
            confirmation_status=resolved_confirmation_status,
            execution_preference=resolved_execution_preference,
            geometry_family_hint=resolved_geometry_family_hint,
            selected_case_id=resolved_selected_case_id,
            geometry_virtual_path=geometry_virtual_path,
            inlet_velocity_mps=resolved_simulation_requirements.get("inlet_velocity_mps"),
            fluid_density_kg_m3=resolved_simulation_requirements.get("fluid_density_kg_m3"),
            kinematic_viscosity_m2ps=resolved_simulation_requirements.get("kinematic_viscosity_m2ps"),
            end_time_seconds=resolved_simulation_requirements.get("end_time_seconds"),
            delta_t_seconds=resolved_simulation_requirements.get("delta_t_seconds"),
            write_interval_steps=resolved_simulation_requirements.get("write_interval_steps"),
            requested_outputs=(existing_runtime.get("requested_outputs") or existing_brief.get("requested_outputs")),
            custom_variants=(custom_variants if custom_variants is not None else existing_runtime.get("custom_variants") or existing_brief.get("custom_variants")),
            geometry_findings=(existing_runtime.get("geometry_findings") or existing_brief.get("geometry_findings")),
            scale_assessment=(existing_runtime.get("scale_assessment") or existing_brief.get("scale_assessment")),
            reference_value_suggestions=(existing_runtime.get("reference_value_suggestions") or existing_brief.get("reference_value_suggestions")),
            clarification_required=bool(existing_runtime.get("clarification_required") or existing_brief.get("clarification_required")),
            calculation_plan=(existing_runtime.get("calculation_plan") or existing_brief.get("calculation_plan")),
            requires_immediate_confirmation=bool(existing_runtime.get("requires_immediate_confirmation") or existing_brief.get("requires_immediate_confirmation")),
            contract_revision=int(contract_revision if contract_revision is not None else existing_runtime.get("contract_revision") or existing_brief.get("contract_revision") or 1),
            revision_summary=(revision_summary if revision_summary is not None else existing_runtime.get("revision_summary") or existing_brief.get("revision_summary")),
            iteration_mode=(iteration_mode if iteration_mode is not None else existing_runtime.get("iteration_mode") or existing_brief.get("iteration_mode") or "baseline"),
            capability_gaps=(existing_runtime.get("capability_gaps") or existing_brief.get("capability_gaps")),
            unresolved_decisions=(existing_runtime.get("unresolved_decisions") or existing_brief.get("unresolved_decisions")),
            evidence_expectations=(existing_runtime.get("evidence_expectations") or existing_brief.get("evidence_expectations")),
            variant_policy=(existing_runtime.get("variant_policy") or existing_brief.get("variant_policy")),
            solver_command=solver_command,
            execute_now=resolved_execute_now,
            execute_scientific_studies=execute_scientific_studies,
            execute_command=execute_command,
        )
    except ValueError as exc:
        return Command(
            update={"messages": [ToolMessage(f"Error: {exc}", tool_call_id=tool_call_id)]},
        )

    selected_case = payload.get("selected_case") or {}
    dispatch_status = payload.get("dispatch_status")
    execution_updates: dict[str, str] = {
        "claude-code-supervisor": "completed",
        "task-intelligence": "completed",
        "geometry-preflight": "completed",
    }
    if dispatch_status == "executed":
        execution_updates["solver-dispatch"] = "completed"
        execution_updates["result-reporting"] = "ready"
    elif dispatch_status == "failed":
        execution_updates["solver-dispatch"] = "blocked"
        execution_updates["result-reporting"] = "pending"
    elif payload.get("review_status") == "needs_user_confirmation":
        execution_updates["solver-dispatch"] = "pending"
        execution_updates["result-reporting"] = "pending"
    else:
        execution_updates["solver-dispatch"] = "in_progress"
        execution_updates["result-reporting"] = "pending"
    execution_updates.update(build_scientific_capability_updates_for_dispatch(payload))
    runtime_truth = build_runtime_status_payload(
        current_stage="solver-dispatch",
        next_recommended_stage=payload["next_recommended_stage"],
        stage_status=dispatch_status,
        review_status=payload["review_status"],
        execution_readiness=payload.get("execution_readiness"),
        report_virtual_path=payload["report_virtual_path"],
        request_virtual_path=payload.get("request_virtual_path"),
        execution_log_virtual_path=payload.get("execution_log_virtual_path"),
        solver_results_virtual_path=payload.get("solver_results_virtual_path"),
        artifact_virtual_paths=payload.get("artifact_virtual_paths"),
        runtime_summary=payload["summary_zh"],
    )

    runtime_snapshot = build_runtime_snapshot(
        current_stage="solver-dispatch",
        task_summary=resolved_task_description,
        confirmation_status=resolved_confirmation_status,
        execution_preference=resolved_execution_preference,
        task_type=resolved_task_type,
        geometry_virtual_path=geometry_virtual_path,
        geometry_family=(payload.get("geometry") or {}).get("geometry_family"),
        execution_readiness=payload.get("execution_readiness"),
        geometry_findings=payload.get("geometry_findings"),
        scale_assessment=payload.get("scale_assessment"),
        reference_value_suggestions=payload.get("reference_value_suggestions"),
        clarification_required=bool(payload.get("clarification_required")),
        calculation_plan=payload.get("calculation_plan"),
        requires_immediate_confirmation=bool(payload.get("requires_immediate_confirmation")),
        contract_revision=int(payload.get("contract_revision") or 1),
        iteration_mode=str(payload.get("iteration_mode") or "baseline"),
        revision_summary=payload.get("revision_summary"),
        capability_gaps=payload.get("capability_gaps"),
        unresolved_decisions=payload.get("unresolved_decisions"),
        evidence_expectations=payload.get("evidence_expectations"),
        variant_policy=payload.get("variant_policy"),
        selected_case_id=selected_case.get("case_id"),
        simulation_requirements=payload.get("simulation_requirements"),
        requested_outputs=payload.get("requested_outputs"),
        recommended_actions=payload.get("recommended_actions"),
        custom_variants=payload.get("custom_variants"),
        output_delivery_plan=payload.get("output_delivery_plan"),
        stage_status=dispatch_status,
        runtime_status=runtime_truth["runtime_status"],
        runtime_summary=runtime_truth["runtime_summary"],
        recovery_guidance=runtime_truth["recovery_guidance"],
        blocker_detail=runtime_truth["blocker_detail"],
        workspace_case_dir_virtual_path=payload.get("workspace_case_dir_virtual_path"),
        run_script_virtual_path=payload.get("run_script_virtual_path"),
        request_virtual_path=payload.get("request_virtual_path"),
        provenance_manifest_virtual_path=payload.get("provenance_manifest_virtual_path"),
        execution_log_virtual_path=payload.get("execution_log_virtual_path"),
        solver_results_virtual_path=payload.get("solver_results_virtual_path"),
        stability_evidence_virtual_path=payload.get("stability_evidence_virtual_path"),
        stability_evidence=payload.get("stability_evidence"),
        provenance_summary=payload.get("provenance_summary"),
        environment_fingerprint=payload.get("environment_fingerprint"),
        environment_parity_assessment=payload.get("environment_parity_assessment"),
        supervisor_handoff_virtual_path=payload.get("supervisor_handoff_virtual_path"),
        next_recommended_stage=payload["next_recommended_stage"],
        report_virtual_path=payload["report_virtual_path"],
        artifact_virtual_paths=payload["artifact_virtual_paths"],
        execution_plan=build_execution_plan(
            confirmation_status=resolved_confirmation_status,
            existing_plan=existing_runtime.get("execution_plan"),
            stage_updates=execution_updates,
        ),
        review_status=payload["review_status"],
        scientific_verification_assessment=payload.get("scientific_verification_assessment"),
        activity_timeline=extend_runtime_timeline(
            existing_runtime,
            build_runtime_event(
                stage="solver-dispatch",
                actor="solver-dispatch",
                title="Updated OpenFOAM solver dispatch",
                summary=payload["summary_zh"],
                status=dispatch_status,
            ),
        ),
    )
    detail_lines = "\n".join(f"- {artifact}" for artifact in artifacts)
    message = f"{payload['summary_zh']}\n已登记 {len(artifacts)} 项研究产物，可在工作区直接查看：\n{detail_lines}"
    return Command(
        update={
            "artifacts": artifacts,
            "submarine_runtime": runtime_snapshot.model_dump(mode="json"),
            "messages": [ToolMessage(message, tool_call_id=tool_call_id)],
        },
    )
