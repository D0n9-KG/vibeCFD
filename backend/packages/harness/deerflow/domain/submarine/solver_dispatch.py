"""Submarine solver-dispatch planning and artifact generation."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path

from .artifact_store import (
    build_canonical_solver_dispatch_artifact_bundle,
    build_solver_dispatch_artifact_virtual_path,
)
from .calculation_plan import (
    calculation_plan_requires_confirmation,
    calculation_plan_requires_immediate_confirmation,
    extract_geometry_reference_inputs,
)
from .contracts import SubmarineRequestedOutput, build_supervisor_review_contract
from .experiments import (
    build_experiment_id,
    build_experiment_run_id,
    build_experiment_workflow_status,
    build_metric_snapshot,
    build_run_compare_summary,
    build_run_record,
)
from .geometry_check import inspect_geometry_file
from .library import load_case_library, rank_cases
from .models import (
    GeometryInspection,
    SubmarineCaseMatch,
    SubmarineExperimentManifest,
)
from .output_contract import build_output_delivery_plan
from .postprocess import collect_requested_postprocess_artifacts
from .solver_dispatch_case import (
    DEFAULT_DELTA_T_SECONDS,
    DEFAULT_END_TIME_SECONDS,
    DEFAULT_FLUID_DENSITY_KG_M3,
    DEFAULT_INLET_VELOCITY_MPS,
    DEFAULT_KINEMATIC_VISCOSITY_M2PS,
    DEFAULT_WRITE_INTERVAL_STEPS,
    GEOMETRY_CONVERSION_REQUIRED,
    STL_READY_EXECUTION,
    platform_fs_path,
    resolve_simulation_requirements,
    write_openfoam_case_scaffold,
    write_unix_text,
)
from .solver_dispatch_results import (
    collect_solver_results,
    looks_like_solver_failure,
    render_solver_results_markdown_enriched,
    solver_reference_values,
)
from .studies import (
    build_completed_scientific_study_results,
    build_pending_scientific_study_results,
    build_scientific_study_manifest,
    build_scientific_study_manifest_with_variant_updates,
    build_scientific_study_plan_payload,
    build_scientific_study_variant_execution,
)
from .verification import (
    build_scientific_verification_assessment,
    build_stability_evidence,
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "solver-dispatch"


def _artifact_virtual_path(run_dir_name: str, filename: str) -> str:
    return build_solver_dispatch_artifact_virtual_path(run_dir_name, filename)


def _study_slug(study_type: str) -> str:
    return study_type.replace("_", "-")


def _study_variant_virtual_path(
    run_dir_name: str,
    study_type: str,
    variant_id: str,
    filename: str,
) -> str:
    return (
        f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/studies/"
        f"{_study_slug(study_type)}/{variant_id}/{filename}"
    )


def _study_case_relative_dir(study_type: str, variant_id: str) -> str:
    return f"studies/{_study_slug(study_type)}/{variant_id}"


def _study_variant_run_record_virtual_path(
    run_dir_name: str,
    study_type: str,
    variant_id: str,
) -> str:
    return _study_variant_virtual_path(
        run_dir_name,
        study_type,
        variant_id,
        "run-record.json",
    )


def _merge_unique_paths(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for path in group:
            if path and path not in merged:
                merged.append(path)
    return merged


def _ensure_study_variant_update(
    updates: dict[str, dict[str, dict[str, object]]],
    *,
    study_type: str,
    variant_id: str,
) -> dict[str, object]:
    study_updates = updates.setdefault(study_type, {})
    return study_updates.setdefault(variant_id, {})


def _select_case(candidate_cases: list[SubmarineCaseMatch], selected_case_id: str | None) -> SubmarineCaseMatch | None:
    if selected_case_id:
        for case in candidate_cases:
            if case.case_id == selected_case_id:
                return case
    return candidate_cases[0] if candidate_cases else None


_platform_fs_path = platform_fs_path
_write_unix_text = write_unix_text
_resolve_simulation_requirements = resolve_simulation_requirements
_write_openfoam_case_scaffold = write_openfoam_case_scaffold
_collect_solver_results = collect_solver_results
_solver_reference_values = solver_reference_values
_looks_like_solver_failure = looks_like_solver_failure
_render_solver_results_markdown_enriched = render_solver_results_markdown_enriched


def _solver_results_virtual_path(run_dir_name: str, filename: str) -> str:
    return _artifact_virtual_path(run_dir_name, filename)


def _compose_summary(
    *,
    geometry: GeometryInspection,
    selected_case: SubmarineCaseMatch | None,
    dispatch_status: str,
    execute_now: bool,
) -> str:
    case_text = f"当前优先采用案例模板“{selected_case.title}”。" if selected_case else "当前未命中明确案例模板，将按通用潜艇外流场路径准备求解。"
    geometry_text = (
        "v1 直接求解输入以 clean STL 为主，当前几何已具备直接进入求解派发的条件。"
        if geometry.input_format == "stl"
        else "v1 直接求解输入严格限定为 STL；当前几何不满足 STL-only 运行时边界，应先回到 Supervisor 审核而不是继续派发求解。"
    )
    if dispatch_status == "executed":
        status_text = "已执行 sandbox 内求解派发命令。"
    elif dispatch_status == "failed":
        status_text = "已执行 sandbox 内求解派发命令，但日志显示当前求解链路仍有错误。"
    else:
        status_text = "已生成受控求解派发清单，等待进一步执行。"
    action_text = "本轮请求要求立即执行。" if execute_now else "本轮仅生成派发计划，不直接执行。"
    return (
        f"已为 `{geometry.file_name}` 生成 OpenFOAM 派发方案，几何家族识别为 `{geometry.geometry_family}`。"
        f"{geometry_text}{case_text}{status_text}{action_text}"
    )


def _render_markdown(payload: dict) -> str:
    geometry = payload["geometry"]
    selected_case = payload.get("selected_case")

    lines = [
        "# 潜艇求解派发摘要",
        "",
        "## 中文摘要",
        payload["summary_zh"],
        "",
        "## 求解派发状态",
        f"- 状态: `{payload['dispatch_status']}`",
        f"- 任务类型: `{payload['task_type']}`",
        f"- 几何文件: `{geometry['file_name']}`",
        f"- 几何家族: `{geometry['geometry_family']}`",
    ]

    if selected_case:
        lines.extend(
            [
                "",
                "## 选定案例",
                f"- `{selected_case['case_id']}` | {selected_case['title']}",
                f"- 推荐求解器: `{selected_case.get('recommended_solver') or 'OpenFOAM'}`",
                f"- 依据: {selected_case['rationale']}",
            ]
        )

    lines.extend(
        [
            "",
            "## 审核契约",
            f"- review_status: `{payload['review_status']}`",
            f"- next_recommended_stage: `{payload['next_recommended_stage']}`",
            f"- report_virtual_path: `{payload['report_virtual_path']}`",
            "",
            "## 运行产物",
            f"- 请求清单: `{payload['request_virtual_path']}`",
            f"- 摘要报告: `{payload['report_virtual_path']}`",
        ]
    )

    if payload.get("execution_log_virtual_path"):
        lines.append(f"- 执行日志: `{payload['execution_log_virtual_path']}`")

    if payload.get("solver_results_virtual_path"):
        lines.append(f"- 姹傝В缁撴灉 JSON: `{payload['solver_results_virtual_path']}`")
    if payload.get("solver_results_markdown_virtual_path"):
        lines.append(
            f"- 姹傝В缁撴灉 Markdown: `{payload['solver_results_markdown_virtual_path']}`"
        )

    if payload.get("solver_command"):
        lines.extend(
            [
                "",
                "## 命令",
                f"```bash\n{payload['solver_command']}\n```",
            ]
        )

    lines.extend(
        [
            "",
            "## 下一步建议",
            "- 由 Supervisor 审核案例、命令和运行风险。",
            "- 如果命令已执行，继续进入结果整理与报告生成。",
            "- 如果尚未执行，可在 DeerFlow runtime 内继续补全求解参数。",
            "",
        ]
    )
    return "\n".join(lines)


def _render_html(payload: dict) -> str:
    selected_case = payload.get("selected_case")
    case_html = (
        f"<p><strong>{selected_case['title']}</strong> ({selected_case['case_id']})</p><p>{selected_case['rationale']}</p>"
        if selected_case
        else "<p>当前没有命中明确案例模板，使用通用潜艇外流场派发路径。</p>"
    )
    log_html = (
        f"<p><strong>执行日志:</strong> {payload['execution_log_virtual_path']}</p>"
        if payload.get("execution_log_virtual_path")
        else ""
    )
    command_html = (
        f"<pre>{payload['solver_command']}</pre>"
        if payload.get("solver_command")
        else "<p>当前仅生成派发计划，尚未绑定具体执行命令。</p>"
    )
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>潜艇求解派发摘要</title>
    <style>
      body {{
        margin: 0;
        padding: 32px;
        font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
        background: linear-gradient(135deg, #08131f 0%, #102640 60%, #1d425e 100%);
        color: #edf4fb;
      }}
      .panel {{
        background: rgba(8, 21, 34, 0.78);
        border: 1px solid rgba(122, 173, 219, 0.2);
        border-radius: 20px;
        padding: 20px 24px;
        margin-bottom: 18px;
      }}
      pre {{
        overflow: auto;
        padding: 16px;
        border-radius: 14px;
        background: rgba(19, 44, 68, 0.92);
      }}
    </style>
  </head>
  <body>
    <section class="panel">
      <h1>潜艇求解派发摘要</h1>
      <p>{payload['summary_zh']}</p>
    </section>
    <section class="panel">
      <h2>状态</h2>
      <p><strong>派发状态:</strong> {payload['dispatch_status']}</p>
      <p><strong>任务类型:</strong> {payload['task_type']}</p>
      {log_html}
    </section>
    <section class="panel">
      <h2>案例与命令</h2>
      {case_html}
      {command_html}
    </section>
  </body>
</html>
"""


def run_solver_dispatch(
    *,
    geometry_path: Path,
    outputs_dir: Path,
    workspace_dir: Path | None,
    task_description: str,
    task_type: str,
    confirmation_status: str = "draft",
    execution_preference: str = "plan_only",
    geometry_family_hint: str | None = None,
    selected_case_id: str | None = None,
    geometry_virtual_path: str | None = None,
    inlet_velocity_mps: float | None = None,
    fluid_density_kg_m3: float | None = None,
    kinematic_viscosity_m2ps: float | None = None,
    end_time_seconds: float | None = None,
    delta_t_seconds: float | None = None,
    write_interval_steps: int | None = None,
    requested_outputs: list[dict] | None = None,
    geometry_findings: list[dict] | None = None,
    scale_assessment: dict | None = None,
    reference_value_suggestions: list[dict] | None = None,
    clarification_required: bool = False,
    calculation_plan: list[dict] | None = None,
    requires_immediate_confirmation: bool = False,
    solver_command: str | None = None,
    execute_now: bool = False,
    execute_scientific_studies: bool = False,
    execute_command: Callable[[str], str] | None = None,
) -> tuple[dict, list[str]]:
    geometry = inspect_geometry_file(geometry_path, geometry_family_hint)
    candidate_cases = rank_cases(
        task_description=task_description,
        task_type=task_type,
        geometry_family_hint=geometry.geometry_family,
        geometry_file_name=geometry.file_name,
    )
    selected_case = _select_case(candidate_cases, selected_case_id)
    normalized_requested_outputs = [
        SubmarineRequestedOutput.model_validate(item).model_dump(mode="json")
        for item in (requested_outputs or [])
    ]
    simulation_requirements = _resolve_simulation_requirements(
        inlet_velocity_mps=inlet_velocity_mps,
        fluid_density_kg_m3=fluid_density_kg_m3,
        kinematic_viscosity_m2ps=kinematic_viscosity_m2ps,
        end_time_seconds=end_time_seconds,
        delta_t_seconds=delta_t_seconds,
        write_interval_steps=write_interval_steps,
    )
    selected_reference_inputs = extract_geometry_reference_inputs(calculation_plan)
    if (
        selected_reference_inputs is None
        and reference_value_suggestions
    ):
        low_risk_values = {
            item.get("quantity"): item.get("value")
            for item in reference_value_suggestions
            if item.get("is_low_risk") and not item.get("requires_confirmation")
        }
        if low_risk_values:
            selected_reference_inputs = {
                key: value
                for key, value in low_risk_values.items()
                if value is not None
            }
            if selected_reference_inputs:
                selected_reference_inputs["approval_state"] = "pending_researcher_confirmation"
                selected_reference_inputs["justification"] = (
                    "Derived from low-risk geometry reference suggestions."
                )
    pending_calculation_plan = calculation_plan_requires_confirmation(calculation_plan)
    requires_immediate_confirmation = (
        requires_immediate_confirmation
        or calculation_plan_requires_immediate_confirmation(calculation_plan)
    )

    run_dir_name = _slugify(geometry_path.stem)
    artifact_dir = outputs_dir / "submarine" / "solver-dispatch" / run_dir_name
    artifact_dir.mkdir(parents=True, exist_ok=True)

    request_path = artifact_dir / "openfoam-request.json"
    markdown_path = artifact_dir / "dispatch-summary.md"
    html_path = artifact_dir / "dispatch-summary.html"
    study_plan_path = artifact_dir / "study-plan.json"
    study_manifest_path = artifact_dir / "study-manifest.json"
    log_path = artifact_dir / "openfoam-run.log"
    handoff_path = artifact_dir / "supervisor-handoff.json"
    solver_results_json_path = artifact_dir / "solver-results.json"
    solver_results_md_path = artifact_dir / "solver-results.md"
    stability_evidence_json_path = artifact_dir / "stability-evidence.json"
    experiment_manifest_path = artifact_dir / "experiment-manifest.json"
    baseline_run_record_path = artifact_dir / "run-record.json"
    run_compare_summary_path = artifact_dir / "run-compare-summary.json"
    request_virtual_path = _artifact_virtual_path(run_dir_name, "openfoam-request.json")
    report_virtual_path = _artifact_virtual_path(run_dir_name, "dispatch-summary.md")
    supervisor_handoff_virtual_path = _artifact_virtual_path(
        run_dir_name,
        "supervisor-handoff.json",
    )

    selected_case_definition = None
    if selected_case is not None:
        selected_case_definition = load_case_library().case_index.get(selected_case.case_id)
    experiment_id = build_experiment_id(
        selected_case_id=selected_case.case_id if selected_case else None,
        run_dir_name=run_dir_name,
        task_type=task_type,
    )

    scientific_study_manifest_model = None
    scientific_study_plan: dict | None = None
    scientific_study_manifest: dict | None = None
    experiment_manifest: dict | None = None
    run_compare_summary: dict | None = None
    baseline_run_record_model = None
    candidate_run_record_models: list = []
    study_variant_updates: dict[str, dict[str, dict[str, object]]] = {}
    study_verification_artifact_paths: list[str] = []
    baseline_run_record_virtual_path = _artifact_virtual_path(
        run_dir_name,
        "run-record.json",
    )
    run_compare_summary_virtual_path = _artifact_virtual_path(
        run_dir_name,
        "run-compare-summary.json",
    )
    experiment_manifest_virtual_path = _artifact_virtual_path(
        run_dir_name,
        "experiment-manifest.json",
    )
    planned_study_artifact_paths: list[str] = []
    if selected_case_definition is not None:
        scientific_study_manifest_model = build_scientific_study_manifest(
            selected_case=selected_case_definition,
            simulation_requirements=simulation_requirements,
            baseline_configuration_snapshot={
                "task_type": task_type,
                "geometry_family": geometry.geometry_family,
                "recommended_solver": selected_case_definition.recommended_solver,
            },
        )
        planned_study_artifact_paths.extend(
            [
                path
                for definition in scientific_study_manifest_model.study_definitions
                for variant in definition.variants
                for path in (
                    _study_variant_virtual_path(
                        run_dir_name,
                        definition.study_type,
                        variant.variant_id,
                        "solver-results.json",
                    ),
                    *(
                        [
                            _study_variant_run_record_virtual_path(
                                run_dir_name,
                                definition.study_type,
                                variant.variant_id,
                            )
                        ]
                        if variant.variant_id != "baseline"
                        else []
                    ),
                )
            ]
        )
        for definition in scientific_study_manifest_model.study_definitions:
            for variant in definition.variants:
                expected_run_id = build_experiment_run_id(
                    study_type=definition.study_type,
                    variant_id=variant.variant_id,
                )
                variant_update = _ensure_study_variant_update(
                    study_variant_updates,
                    study_type=definition.study_type,
                    variant_id=variant.variant_id,
                )
                variant_update.update(
                    {
                        "expected_run_id": expected_run_id,
                        "solver_results_virtual_path": _study_variant_virtual_path(
                            run_dir_name,
                            definition.study_type,
                            variant.variant_id,
                            "solver-results.json",
                        ),
                        "baseline_solver_results_virtual_path": _solver_results_virtual_path(
                            run_dir_name,
                            "solver-results.json",
                        ),
                        "execution_status": "planned",
                        "compare_status": (
                            None if variant.variant_id == "baseline" else "planned"
                        ),
                    }
                )
                if variant.variant_id != "baseline":
                    variant_update["run_record_virtual_path"] = (
                        _study_variant_run_record_virtual_path(
                            run_dir_name,
                            definition.study_type,
                            variant.variant_id,
                        )
                    )
        scientific_study_manifest_model = build_scientific_study_manifest_with_variant_updates(
            manifest=scientific_study_manifest_model,
            variant_updates=study_variant_updates,
            artifact_virtual_paths=planned_study_artifact_paths,
        )
        scientific_study_plan = build_scientific_study_plan_payload(
            scientific_study_manifest_model
        )
        scientific_study_manifest = scientific_study_manifest_model.model_dump(mode="json")

    case_scaffold: dict[str, object] = {}
    if workspace_dir is not None:
        case_scaffold = _write_openfoam_case_scaffold(
            workspace_dir=workspace_dir,
            run_dir_name=run_dir_name,
            geometry_path=geometry_path,
            geometry=geometry,
            selected_case=selected_case,
            simulation_requirements=simulation_requirements,
            requested_outputs=normalized_requested_outputs,
            reference_inputs=selected_reference_inputs,
        )

    effective_solver_command = solver_command or (
        f"bash {case_scaffold['run_script_virtual_path']}" if case_scaffold.get("run_script_virtual_path") else None
    )

    dispatch_status = "planned"
    execution_log_virtual_path: str | None = None
    solver_results_virtual_path: str | None = None
    solver_results_markdown_virtual_path: str | None = None
    stability_evidence_virtual_path: str | None = None
    solver_results: dict | None = None
    stability_evidence: dict | None = None
    scientific_verification_assessment: dict | None = None
    requested_postprocess_artifacts: list[str] = []
    scientific_study_artifacts: list[str] = []
    scientific_variant_results: dict[str, dict[str, dict[str, object] | None]] = {}
    experiment_artifacts: list[str] = []
    if (
        execute_now
        and not pending_calculation_plan
        and effective_solver_command
        and execute_command is not None
    ):
        command_output = execute_command(effective_solver_command)
        log_path.write_text(command_output, encoding="utf-8")
        dispatch_status = "failed" if _looks_like_solver_failure(command_output) else "executed"
        execution_log_virtual_path = _artifact_virtual_path(run_dir_name, "openfoam-run.log")
        if workspace_dir is not None:
            case_dir = workspace_dir / "submarine" / "solver-dispatch" / run_dir_name / "openfoam-case"
            solver_results = _collect_solver_results(
                case_dir=case_dir,
                run_dir_name=run_dir_name,
                command_output=command_output,
                reference_values=_solver_reference_values(case_scaffold),
                simulation_requirements=simulation_requirements,
            )
            solver_results_json_path.write_text(
                json.dumps(solver_results, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            solver_results_md_path.write_text(
                _render_solver_results_markdown_enriched(solver_results),
                encoding="utf-8",
            )
            solver_results_virtual_path = _solver_results_virtual_path(
                run_dir_name,
                "solver-results.json",
            )
            solver_results_markdown_virtual_path = _solver_results_virtual_path(
                run_dir_name,
                "solver-results.md",
            )
            stability_evidence_virtual_path = _solver_results_virtual_path(
                run_dir_name,
                "stability-evidence.json",
            )
            stability_evidence = build_stability_evidence(
                acceptance_profile=(
                    selected_case_definition.acceptance_profile
                    if selected_case_definition is not None
                    else None
                ),
                task_type=task_type,
                solver_metrics=solver_results,
                solver_results_virtual_path=solver_results_virtual_path,
                artifact_virtual_path=stability_evidence_virtual_path,
            )
            if stability_evidence is not None:
                stability_evidence_json_path.write_text(
                    json.dumps(stability_evidence, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            requested_postprocess_artifacts = collect_requested_postprocess_artifacts(
                case_dir=case_dir,
                artifact_dir=artifact_dir,
                run_dir_name=run_dir_name,
                requested_outputs=normalized_requested_outputs,
                artifact_virtual_path_builder=_artifact_virtual_path,
                write_text=_write_unix_text,
            )
            baseline_run_record_model = build_run_record(
                experiment_id=experiment_id,
                run_id=build_experiment_run_id(
                    study_type=None,
                    variant_id=None,
                ),
                run_role="baseline",
                solver_results_virtual_path=_solver_results_virtual_path(
                    run_dir_name,
                    "solver-results.json",
                ),
                run_record_virtual_path=baseline_run_record_virtual_path,
                execution_status=(
                    "completed" if solver_results.get("solver_completed") else "blocked"
                ),
                metric_snapshot=build_metric_snapshot(solver_results=solver_results),
            )
            baseline_run_record_path.write_text(
                json.dumps(
                    baseline_run_record_model.model_dump(mode="json"),
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            run_compare_summary_model = build_run_compare_summary(
                experiment_id=experiment_id,
                baseline_run_id=baseline_run_record_model.run_id,
                baseline_record=baseline_run_record_model.model_dump(mode="json"),
                candidate_records=[],
                artifact_virtual_paths=[
                    baseline_run_record_virtual_path,
                    run_compare_summary_virtual_path,
                ],
            )
            run_compare_summary_path.write_text(
                json.dumps(
                    run_compare_summary_model.model_dump(mode="json"),
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            experiment_manifest_model = SubmarineExperimentManifest(
                experiment_id=experiment_id,
                selected_case_id=selected_case.case_id if selected_case else None,
                task_type=task_type,
                baseline_run_id=baseline_run_record_model.run_id,
                run_records=[baseline_run_record_model],
                artifact_virtual_paths=[
                    baseline_run_record_virtual_path,
                    run_compare_summary_virtual_path,
                    experiment_manifest_virtual_path,
                ],
                experiment_status=(
                    "completed"
                    if baseline_run_record_model.execution_status == "completed"
                    else "blocked"
                ),
            )
            experiment_manifest_path.write_text(
                json.dumps(
                    experiment_manifest_model.model_dump(mode="json"),
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            experiment_manifest = experiment_manifest_model.model_dump(mode="json")
            run_compare_summary = run_compare_summary_model.model_dump(mode="json")
            experiment_artifacts.extend(
                [
                    baseline_run_record_virtual_path,
                    run_compare_summary_virtual_path,
                    experiment_manifest_virtual_path,
                ]
            )

    if scientific_study_manifest_model is not None:
        study_results = []
        if solver_results is not None:
            if execute_scientific_studies and execute_command is not None and workspace_dir is not None:
                for definition in scientific_study_manifest_model.study_definitions:
                    study_variant_results = scientific_variant_results.setdefault(
                        definition.study_type,
                        {},
                    )
                    for variant in definition.variants:
                        variant_output_path = _platform_fs_path(
                            artifact_dir
                            / "studies"
                            / _study_slug(definition.study_type)
                            / variant.variant_id
                            / "solver-results.json"
                        )
                        variant_run_record_path = _platform_fs_path(
                            artifact_dir
                            / "studies"
                            / _study_slug(definition.study_type)
                            / variant.variant_id
                            / "run-record.json"
                        )
                        variant_output_path.parent.mkdir(parents=True, exist_ok=True)
                        variant_virtual_path = _study_variant_virtual_path(
                            run_dir_name,
                            definition.study_type,
                            variant.variant_id,
                            "solver-results.json",
                        )
                        variant_run_record_virtual_path = (
                            _study_variant_run_record_virtual_path(
                                run_dir_name,
                                definition.study_type,
                                variant.variant_id,
                            )
                        )
                        variant_update = _ensure_study_variant_update(
                            study_variant_updates,
                            study_type=definition.study_type,
                            variant_id=variant.variant_id,
                        )
                        variant_update.update(
                            {
                                "solver_results_virtual_path": variant_virtual_path,
                                "baseline_solver_results_virtual_path": _solver_results_virtual_path(
                                    run_dir_name,
                                    "solver-results.json",
                                ),
                            }
                        )

                        if variant.variant_id == "baseline":
                            baseline_variant_payload = {
                                **solver_results,
                                "study_type": definition.study_type,
                                "variant_id": variant.variant_id,
                                "variant_label": variant.variant_label,
                                "execution_status": "completed",
                                "parameter_overrides": variant.parameter_overrides,
                                "baseline_solver_results_virtual_path": _solver_results_virtual_path(
                                    run_dir_name,
                                    "solver-results.json",
                                ),
                            }
                            study_variant_results[variant.variant_id] = baseline_variant_payload
                            variant_output_path.write_text(
                                json.dumps(
                                    baseline_variant_payload,
                                    ensure_ascii=False,
                                    indent=2,
                                ),
                                encoding="utf-8",
                            )
                            scientific_study_artifacts.append(variant_virtual_path)
                            variant_update.update(
                                {
                                    "execution_status": "completed",
                                    "compare_status": None,
                                }
                            )
                            continue

                        case_relative_dir = _study_case_relative_dir(
                            definition.study_type,
                            variant.variant_id,
                        )
                        variant_execution = build_scientific_study_variant_execution(
                            variant=variant,
                            simulation_requirements=simulation_requirements,
                        )
                        variant_scaffold = _write_openfoam_case_scaffold(
                            workspace_dir=workspace_dir,
                            run_dir_name=run_dir_name,
                            geometry_path=geometry_path,
                            geometry=geometry,
                            selected_case=selected_case,
                            simulation_requirements=variant_execution["simulation_requirements"],
                            case_relative_dir=case_relative_dir,
                            mesh_scale_factor=float(variant_execution["mesh_scale_factor"]),
                            domain_extent_multiplier=float(
                                variant_execution["domain_extent_multiplier"]
                            ),
                        )
                        variant_command = (
                            f"bash {variant_scaffold['run_script_virtual_path']}"
                            if variant_scaffold.get("run_script_virtual_path")
                            else None
                        )
                        variant_command_output = (
                            execute_command(variant_command) if variant_command else ""
                        )
                        variant_failed = (
                            not variant_command
                            or _looks_like_solver_failure(variant_command_output)
                            or bool(variant_scaffold.get("requires_geometry_conversion"))
                        )
                        variant_case_dir = (
                            workspace_dir
                            / "submarine"
                            / "solver-dispatch"
                            / run_dir_name
                            / Path(case_relative_dir)
                            / "openfoam-case"
                        )
                        variant_solver_results: dict[str, object] | None = None
                        if not variant_failed:
                            variant_solver_results = _collect_solver_results(
                                case_dir=variant_case_dir,
                                run_dir_name=run_dir_name,
                                case_relative_dir=case_relative_dir,
                                command_output=variant_command_output,
                                reference_values=_solver_reference_values(
                                    variant_scaffold
                                ),
                                simulation_requirements=variant_execution[
                                    "simulation_requirements"
                                ],
                            )
                            if not variant_solver_results.get("solver_completed"):
                                variant_failed = True

                        variant_payload: dict[str, object] = {
                            "study_type": definition.study_type,
                            "variant_id": variant.variant_id,
                            "variant_label": variant.variant_label,
                            "parameter_overrides": variant.parameter_overrides,
                            "solver_command": variant_command,
                            "workspace_case_dir_virtual_path": variant_scaffold.get(
                                "workspace_case_dir_virtual_path"
                            ),
                            "run_script_virtual_path": variant_scaffold.get(
                                "run_script_virtual_path"
                            ),
                            "baseline_solver_results_virtual_path": _solver_results_virtual_path(
                                run_dir_name,
                                "solver-results.json",
                            ),
                        }
                        if variant_solver_results is not None:
                            variant_payload.update(variant_solver_results)
                        if variant_failed:
                            variant_payload["execution_status"] = "blocked"
                        else:
                            variant_payload["execution_status"] = "completed"
                        study_variant_results[variant.variant_id] = variant_payload

                        variant_output_path.write_text(
                            json.dumps(variant_payload, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                        variant_run_record_model = build_run_record(
                            experiment_id=experiment_id,
                            run_id=build_experiment_run_id(
                                study_type=definition.study_type,
                                variant_id=variant.variant_id,
                            ),
                            run_role="scientific_study_variant",
                            study_type=definition.study_type,
                            variant_id=variant.variant_id,
                            solver_results_virtual_path=variant_virtual_path,
                            run_record_virtual_path=variant_run_record_virtual_path,
                            execution_status=str(variant_payload["execution_status"]),
                            metric_snapshot=build_metric_snapshot(
                                solver_results=variant_solver_results
                            ),
                        )
                        variant_run_record_path.write_text(
                            json.dumps(
                                variant_run_record_model.model_dump(mode="json"),
                                ensure_ascii=False,
                                indent=2,
                            ),
                            encoding="utf-8",
                        )
                        candidate_run_record_models.append(variant_run_record_model)
                        scientific_study_artifacts.append(variant_virtual_path)
                        experiment_artifacts.append(variant_run_record_virtual_path)
                        variant_update.update(
                            {
                                "run_record_virtual_path": variant_run_record_virtual_path,
                                "execution_status": str(variant_payload["execution_status"]),
                                "compare_status": "planned",
                            }
                        )

                study_results = build_completed_scientific_study_results(
                    manifest=scientific_study_manifest_model,
                    baseline_solver_results=solver_results,
                    variant_results=scientific_variant_results,
                )
            else:
                study_results = build_pending_scientific_study_results(
                    manifest=scientific_study_manifest_model,
                    baseline_solver_results=solver_results,
                )
                for definition in scientific_study_manifest_model.study_definitions:
                    study_variant_results = scientific_variant_results.setdefault(
                        definition.study_type,
                        {},
                    )
                    for variant in definition.variants:
                        variant_output_path = _platform_fs_path(
                            artifact_dir
                            / "studies"
                            / _study_slug(definition.study_type)
                            / variant.variant_id
                            / "solver-results.json"
                        )
                        variant_output_path.parent.mkdir(parents=True, exist_ok=True)
                        variant_virtual_path = _study_variant_virtual_path(
                            run_dir_name,
                            definition.study_type,
                            variant.variant_id,
                            "solver-results.json",
                        )
                        variant_run_record_virtual_path = (
                            _study_variant_run_record_virtual_path(
                                run_dir_name,
                                definition.study_type,
                                variant.variant_id,
                            )
                        )
                        variant_update = _ensure_study_variant_update(
                            study_variant_updates,
                            study_type=definition.study_type,
                            variant_id=variant.variant_id,
                        )
                        variant_update.update(
                            {
                                "solver_results_virtual_path": variant_virtual_path,
                                "baseline_solver_results_virtual_path": _solver_results_virtual_path(
                                    run_dir_name,
                                    "solver-results.json",
                                ),
                            }
                        )

                        if variant.variant_id == "baseline":
                            baseline_variant_payload = {
                                **solver_results,
                                "study_type": definition.study_type,
                                "variant_id": variant.variant_id,
                                "variant_label": variant.variant_label,
                                "execution_status": "completed",
                                "parameter_overrides": variant.parameter_overrides,
                                "baseline_solver_results_virtual_path": _solver_results_virtual_path(
                                    run_dir_name,
                                    "solver-results.json",
                                ),
                            }
                            study_variant_results[variant.variant_id] = baseline_variant_payload
                            variant_output_path.write_text(
                                json.dumps(
                                    baseline_variant_payload,
                                    ensure_ascii=False,
                                    indent=2,
                                ),
                                encoding="utf-8",
                            )
                            scientific_study_artifacts.append(variant_virtual_path)
                            variant_update.update(
                                {
                                    "execution_status": "completed",
                                    "compare_status": None,
                                }
                            )
                            continue

                        planned_variant_payload = {
                            "study_type": definition.study_type,
                            "variant_id": variant.variant_id,
                            "variant_label": variant.variant_label,
                            "execution_status": "planned",
                            "parameter_overrides": variant.parameter_overrides,
                            "expected_run_id": build_experiment_run_id(
                                study_type=definition.study_type,
                                variant_id=variant.variant_id,
                            ),
                            "run_record_virtual_path": variant_run_record_virtual_path,
                            "baseline_solver_results_virtual_path": _solver_results_virtual_path(
                                run_dir_name,
                                "solver-results.json",
                            ),
                        }
                        variant_output_path.write_text(
                            json.dumps(
                                planned_variant_payload,
                                ensure_ascii=False,
                                indent=2,
                            ),
                            encoding="utf-8",
                        )
                        planned_run_record_model = build_run_record(
                            experiment_id=experiment_id,
                            run_id=build_experiment_run_id(
                                study_type=definition.study_type,
                                variant_id=variant.variant_id,
                            ),
                            run_role="scientific_study_variant",
                            study_type=definition.study_type,
                            variant_id=variant.variant_id,
                            solver_results_virtual_path=variant_virtual_path,
                            run_record_virtual_path=variant_run_record_virtual_path,
                            execution_status="planned",
                            metric_snapshot={},
                        )
                        variant_run_record_path = _platform_fs_path(
                            artifact_dir
                            / "studies"
                            / _study_slug(definition.study_type)
                            / variant.variant_id
                            / "run-record.json"
                        )
                        variant_run_record_path.write_text(
                            json.dumps(
                                planned_run_record_model.model_dump(mode="json"),
                                ensure_ascii=False,
                                indent=2,
                            ),
                            encoding="utf-8",
                        )
                        candidate_run_record_models.append(planned_run_record_model)
                        scientific_study_artifacts.append(variant_virtual_path)
                        experiment_artifacts.append(variant_run_record_virtual_path)
                        variant_update.update(
                            {
                                "run_record_virtual_path": variant_run_record_virtual_path,
                                "execution_status": "planned",
                                "compare_status": "planned",
                            }
                        )

            for result in study_results:
                filename = f"verification-{_study_slug(result.study_type)}.json"
                verification_path = artifact_dir / filename
                verification_virtual_path = _artifact_virtual_path(run_dir_name, filename)
                verification_path.write_text(
                    json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                study_verification_artifact_paths.append(verification_virtual_path)
                scientific_study_artifacts.append(verification_virtual_path)

    if baseline_run_record_model is not None:
        all_run_records = [
            baseline_run_record_model,
            *candidate_run_record_models,
        ]
        all_run_record_payloads = [
            item.model_dump(mode="json") for item in all_run_records
        ]
        run_compare_summary_model = build_run_compare_summary(
            experiment_id=experiment_id,
            baseline_run_id=baseline_run_record_model.run_id,
            baseline_record=baseline_run_record_model.model_dump(mode="json"),
            candidate_records=[
                item.model_dump(mode="json") for item in candidate_run_record_models
            ],
            artifact_virtual_paths=[
                baseline_run_record_virtual_path,
                run_compare_summary_virtual_path,
                *[
                    item.run_record_virtual_path
                    for item in candidate_run_record_models
                ],
            ],
        )
        run_compare_summary_path.write_text(
            json.dumps(
                run_compare_summary_model.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        experiment_manifest_model = SubmarineExperimentManifest(
            experiment_id=experiment_id,
            selected_case_id=selected_case.case_id if selected_case else None,
            task_type=task_type,
            baseline_run_id=baseline_run_record_model.run_id,
            run_records=all_run_records,
            artifact_virtual_paths=[
                baseline_run_record_virtual_path,
                run_compare_summary_virtual_path,
                experiment_manifest_virtual_path,
                *[
                    item.run_record_virtual_path
                    for item in candidate_run_record_models
                ],
            ],
            experiment_status=build_experiment_workflow_status(
                run_records=all_run_record_payloads,
                compare_statuses=[
                    comparison.compare_status
                    for comparison in run_compare_summary_model.comparisons
                ],
            ),
            workflow_status=build_experiment_workflow_status(
                run_records=all_run_record_payloads,
                compare_statuses=[
                    comparison.compare_status
                    for comparison in run_compare_summary_model.comparisons
                ],
            ),
            run_status_counts={
                status: len(
                    [
                        item
                        for item in candidate_run_record_models
                        if item.execution_status == status
                    ]
                )
                for status in {
                    item.execution_status for item in candidate_run_record_models
                }
            },
            compare_status_counts=run_compare_summary_model.compare_status_counts,
        )
        experiment_manifest_path.write_text(
            json.dumps(
                experiment_manifest_model.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        experiment_manifest = experiment_manifest_model.model_dump(mode="json")
        run_compare_summary = run_compare_summary_model.model_dump(mode="json")
        experiment_artifacts = _merge_unique_paths(
            experiment_artifacts,
            [
                baseline_run_record_virtual_path,
                run_compare_summary_virtual_path,
                experiment_manifest_virtual_path,
            ],
        )

        if scientific_study_manifest_model is not None:
            compare_status_by_run_id = {
                comparison.candidate_run_id: comparison.compare_status
                for comparison in run_compare_summary_model.comparisons
            }
            for definition in scientific_study_manifest_model.study_definitions:
                for variant in definition.variants:
                    if variant.variant_id == "baseline":
                        continue
                    expected_run_id = build_experiment_run_id(
                        study_type=definition.study_type,
                        variant_id=variant.variant_id,
                    )
                    variant_update = _ensure_study_variant_update(
                        study_variant_updates,
                        study_type=definition.study_type,
                        variant_id=variant.variant_id,
                    )
                    variant_update["compare_status"] = compare_status_by_run_id.get(
                        expected_run_id,
                        variant_update.get("compare_status") or "planned",
                    )

    if scientific_study_manifest_model is not None:
        scientific_study_manifest_model = build_scientific_study_manifest_with_variant_updates(
            manifest=scientific_study_manifest_model,
            variant_updates=study_variant_updates,
            artifact_virtual_paths=_merge_unique_paths(
                planned_study_artifact_paths,
                study_verification_artifact_paths,
            ),
        )
        scientific_study_manifest = scientific_study_manifest_model.model_dump(mode="json")
        scientific_study_plan = build_scientific_study_plan_payload(
            scientific_study_manifest_model
        )

    artifacts = build_canonical_solver_dispatch_artifact_bundle(
        run_dir_name=run_dir_name,
        include_scientific_study_plan=scientific_study_manifest is not None,
        execution_log_virtual_path=execution_log_virtual_path,
        solver_results_virtual_path=solver_results_virtual_path,
        solver_results_markdown_virtual_path=solver_results_markdown_virtual_path,
        stability_evidence_virtual_path=stability_evidence_virtual_path,
        requested_postprocess_artifacts=requested_postprocess_artifacts,
        scientific_study_artifacts=scientific_study_artifacts,
        experiment_artifacts=experiment_artifacts,
    )
    scientific_verification_assessment = build_scientific_verification_assessment(
        acceptance_profile=(
            selected_case_definition.acceptance_profile
            if selected_case_definition is not None
            else None
        ),
        task_type=task_type,
        solver_metrics=solver_results,
        artifact_virtual_paths=artifacts,
        outputs_dir=outputs_dir,
        stability_evidence=stability_evidence,
    )

    review_status = "ready_for_supervisor"
    next_stage = "result-reporting" if dispatch_status == "executed" else "solver-dispatch"
    if pending_calculation_plan:
        review_status = "needs_user_confirmation"
        next_stage = "user-confirmation"
    elif case_scaffold.get("requires_geometry_conversion"):
        review_status = "needs_user_confirmation"
        next_stage = "geometry-preflight"
    elif dispatch_status == "failed":
        review_status = "blocked"
        next_stage = "solver-dispatch"

    review = build_supervisor_review_contract(
        next_recommended_stage=next_stage,
        report_virtual_path=report_virtual_path,
        artifact_virtual_paths=artifacts,
        review_status=review_status,
    )
    output_delivery_plan = build_output_delivery_plan(
        normalized_requested_outputs,
        stage="solver-dispatch",
        solver_metrics=solver_results,
        artifact_virtual_paths=artifacts,
    )

    payload = {
        "task_description": task_description,
        "task_type": task_type,
        "confirmation_status": confirmation_status,
        "execution_preference": execution_preference,
        "geometry": geometry.model_dump(mode="json"),
        "candidate_cases": [case.model_dump(mode="json") for case in candidate_cases],
        "selected_case": selected_case.model_dump(mode="json") if selected_case else None,
        "dispatch_status": dispatch_status,
        "solver_command": effective_solver_command,
        "request_virtual_path": request_virtual_path,
        "report_virtual_path": review.report_virtual_path,
        "execution_log_virtual_path": execution_log_virtual_path,
        "solver_results_virtual_path": solver_results_virtual_path,
        "solver_results_markdown_virtual_path": solver_results_markdown_virtual_path,
        "stability_evidence_virtual_path": stability_evidence_virtual_path,
        "stability_evidence": stability_evidence,
        "solver_results": solver_results,
        "scientific_verification_assessment": scientific_verification_assessment,
        "simulation_requirements": simulation_requirements,
        "requested_outputs": normalized_requested_outputs,
        "geometry_findings": geometry_findings or [],
        "scale_assessment": scale_assessment,
        "reference_value_suggestions": reference_value_suggestions or [],
        "clarification_required": clarification_required,
        "calculation_plan": calculation_plan or [],
        "requires_immediate_confirmation": requires_immediate_confirmation,
        "selected_reference_inputs": selected_reference_inputs,
        "output_delivery_plan": output_delivery_plan,
        "scientific_study_plan": scientific_study_plan,
        "scientific_study_manifest": scientific_study_manifest,
        "experiment_manifest": experiment_manifest,
        "run_compare_summary": run_compare_summary,
        "review_status": review.review_status,
        "next_recommended_stage": review.next_recommended_stage,
        "artifact_virtual_paths": review.artifact_virtual_paths,
        "workspace_case_dir_virtual_path": case_scaffold.get("workspace_case_dir_virtual_path"),
        "run_script_virtual_path": case_scaffold.get("run_script_virtual_path"),
        "solver_application": case_scaffold.get("solver_application"),
        "requires_geometry_conversion": case_scaffold.get("requires_geometry_conversion", False),
        "execution_readiness": case_scaffold.get("execution_readiness", STL_READY_EXECUTION),
        "supervisor_handoff_virtual_path": supervisor_handoff_virtual_path,
        "summary_zh": _compose_summary(
            geometry=geometry,
            selected_case=selected_case,
            dispatch_status=dispatch_status,
            execute_now=execute_now,
        ),
    }

    supervisor_handoff = {
        "task_summary": task_description,
        "confirmation_status": confirmation_status,
        "execution_preference": execution_preference,
        "uploaded_geometry_path": geometry_virtual_path or geometry.file_name,
        "task_type": task_type,
        "geometry_family_hint": geometry.geometry_family,
        "selected_case_id": selected_case.case_id if selected_case else None,
        "requested_outputs": normalized_requested_outputs,
        "calculation_plan": calculation_plan or [],
        "requires_immediate_confirmation": requires_immediate_confirmation,
        "selected_reference_inputs": selected_reference_inputs,
        "output_delivery_plan": output_delivery_plan,
        "review_status": payload["review_status"],
        "next_recommended_stage": payload["next_recommended_stage"],
        "report_virtual_path": payload["report_virtual_path"],
        "artifact_virtual_paths": payload["artifact_virtual_paths"],
        "request_virtual_path": request_virtual_path,
        "execution_log_virtual_path": execution_log_virtual_path,
        "solver_results_virtual_path": solver_results_virtual_path,
        "stability_evidence_virtual_path": stability_evidence_virtual_path,
        "scientific_verification_assessment": scientific_verification_assessment,
        "workspace_case_dir_virtual_path": payload["workspace_case_dir_virtual_path"],
        "run_script_virtual_path": payload["run_script_virtual_path"],
        "solver_application": payload["solver_application"],
        "requires_geometry_conversion": payload["requires_geometry_conversion"],
        "execution_readiness": payload["execution_readiness"],
        "simulation_requirements": simulation_requirements,
    }

    request_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
    html_path.write_text(_render_html(payload), encoding="utf-8")
    handoff_path.write_text(json.dumps(supervisor_handoff, ensure_ascii=False, indent=2), encoding="utf-8")
    if scientific_study_plan is not None:
        study_plan_path.write_text(
            json.dumps(scientific_study_plan, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if scientific_study_manifest is not None:
        study_manifest_path.write_text(
            json.dumps(scientific_study_manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return payload, artifacts
