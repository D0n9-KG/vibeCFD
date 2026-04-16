"""Submarine result reporting and final artifact generation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .artifact_store import (
    load_canonical_stability_evidence_payload,
    resolve_user_data_artifact,
    resolve_workspace_artifact,
)
from .contracts import (
    SubmarineDeliveryDecisionOption,
    SubmarineDeliveryDecisionSummary,
    SubmarineRuntimeSnapshot,
    build_supervisor_review_contract,
)
from .evidence import build_research_evidence_summary
from .followup import build_scientific_followup_summary, load_scientific_followup_history
from .handoff import build_scientific_remediation_handoff
from .output_contract import build_output_delivery_plan
from .remediation import build_scientific_remediation_summary
from .reporting_acceptance import build_acceptance_assessment
from .reporting_render import (
    render_delivery_readiness_markdown,
    render_html,
    render_markdown,
)
from .reporting_summaries import (
    build_conclusion_sections,
    build_delivery_highlights,
    build_evidence_index,
    build_experiment_compare_summary,
    build_experiment_summary,
    build_figure_delivery_summary,
    build_provenance_summary,
    build_report_overview,
    build_reproducibility_summary,
    build_selected_case_provenance_summary,
    build_scientific_study_summary,
    resolve_outputs_artifact,
    resolve_selected_case,
)
from .supervision import build_scientific_supervisor_gate
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


def _merge_artifact_paths(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for path in group:
            if path not in merged:
                merged.append(path)
    return merged


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _string_list(value: object | None) -> list[str]:
    if not isinstance(value, list):
        return []
    deduped: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        normalized = item.strip()
        if normalized and normalized not in deduped:
            deduped.append(normalized)
    return deduped


def _first_remediation_gap(scientific_remediation_summary: dict[str, Any]) -> str | None:
    actions = scientific_remediation_summary.get("actions")
    if not isinstance(actions, list):
        return None
    for action in actions:
        if not isinstance(action, dict):
            continue
        evidence_gap = action.get("evidence_gap")
        if isinstance(evidence_gap, str) and evidence_gap.strip():
            return evidence_gap.strip()
    return None


def _build_delivery_decision_summary(
    *,
    scientific_supervisor_gate: dict[str, Any],
    research_evidence_summary: dict[str, Any],
    scientific_remediation_summary: dict[str, Any],
    scientific_remediation_handoff: dict[str, Any],
) -> dict[str, Any]:
    gate_status = str(scientific_supervisor_gate.get("gate_status") or "blocked")
    evidence_gaps = _string_list(research_evidence_summary.get("evidence_gaps"))
    blocking_reasons = _string_list(scientific_supervisor_gate.get("blocking_reasons"))
    advisory_notes = _string_list(scientific_supervisor_gate.get("advisory_notes"))
    remediation_gap = _first_remediation_gap(scientific_remediation_summary)
    decision_artifacts = _merge_artifact_paths(
        _string_list(scientific_supervisor_gate.get("artifact_virtual_paths")),
        _string_list(scientific_remediation_summary.get("artifact_virtual_paths")),
        _string_list(scientific_remediation_handoff.get("artifact_virtual_paths")),
    )

    if gate_status == "blocked":
        decision_status = "blocked_by_setup"
        recommended_option_id = "fix_setup"
        if not blocking_reasons and remediation_gap:
            blocking_reasons = [remediation_gap]
        if not blocking_reasons and evidence_gaps:
            blocking_reasons = evidence_gaps
        if not advisory_notes:
            advisory_notes = [
                "当前结果仍需修正设置或补齐关键证据，暂不建议直接结束任务。",
            ]
        option_ids = ["fix_setup"]
        question = "当前结果仍有阻塞项。请在聊天中确认下一步。"
    elif gate_status == "claim_limited":
        decision_status = "needs_more_evidence"
        recommended_option_id = "add_evidence"
        if not blocking_reasons:
            blocking_reasons = evidence_gaps[:]
        option_ids = ["add_evidence", "finish_task", "extend_study"]
        question = "当前结论可以交付，但仍有证据缺口。请在聊天中确认下一步。"
    else:
        decision_status = "ready_for_user_decision"
        recommended_option_id = "finish_task"
        if not advisory_notes:
            advisory_notes = [
                "当前结论已经满足当前交付要求，如需扩大研究范围，可继续安排下一轮研究。",
            ]
        option_ids = ["finish_task", "extend_study"]
        question = "当前结论已经可用于任务交付。请在聊天中确认下一步。"

    primary_reason = blocking_reasons[0] if blocking_reasons else None
    options_by_id = {
        "finish_task": SubmarineDeliveryDecisionOption(
            option_id="finish_task",
            label_zh="完成任务",
            summary_zh="接受当前结论作为本次任务终点，并在聊天中确认收口。",
            followup_kind="task_complete",
            requires_additional_execution=False,
        ),
        "add_evidence": SubmarineDeliveryDecisionOption(
            option_id="add_evidence",
            label_zh="补充证据",
            summary_zh=(
                f"优先补齐缺失证据：{primary_reason}"
                if primary_reason
                else "补齐缺失的验证证据、基准对照或证据链后，再决定是否提升 claim level。"
            ),
            followup_kind="evidence_supplement",
            requires_additional_execution=True,
        ),
        "fix_setup": SubmarineDeliveryDecisionOption(
            option_id="fix_setup",
            label_zh="修正设置",
            summary_zh=(
                f"先修正当前阻塞项：{primary_reason}"
                if primary_reason
                else "先修正当前设置、输入或关键产物，再重新执行并刷新报告。"
            ),
            followup_kind="parameter_correction",
            requires_additional_execution=True,
        ),
        "extend_study": SubmarineDeliveryDecisionOption(
            option_id="extend_study",
            label_zh="扩展研究",
            summary_zh="在当前有效结果基础上扩展更多工况、参数或敏感性研究。",
            followup_kind="study_extension",
            requires_additional_execution=True,
        ),
    }
    options = [options_by_id[option_id] for option_id in option_ids]

    summary = SubmarineDeliveryDecisionSummary(
        decision_status=decision_status,
        decision_question_zh=question,
        recommended_option_id=recommended_option_id,
        options=options,
        blocking_reason_lines=blocking_reasons,
        advisory_note_lines=advisory_notes,
        artifact_virtual_paths=decision_artifacts,
    )
    return summary.model_dump(mode="json")


def _recommended_actions(*, review_status: str, decision_status: str | None) -> list[str]:
    actions = ["review_report_artifacts"]
    if review_status == "blocked":
        actions.append("fix_setup_and_retry")
    elif decision_status == "needs_more_evidence":
        actions.append("collect_more_evidence")
    else:
        actions.append("confirm_delivery_or_followup")
    return actions


_resolve_outputs_artifact = resolve_outputs_artifact
_resolve_selected_case = resolve_selected_case
_build_acceptance_assessment = build_acceptance_assessment
_build_scientific_study_summary = build_scientific_study_summary
_build_experiment_summary = build_experiment_summary
_build_experiment_compare_summary = build_experiment_compare_summary
_build_figure_delivery_summary = build_figure_delivery_summary
_build_report_overview = build_report_overview
_build_delivery_highlights = build_delivery_highlights
_build_conclusion_sections = build_conclusion_sections
_build_evidence_index = build_evidence_index
_build_provenance_summary = build_provenance_summary
_build_reproducibility_summary = build_reproducibility_summary
_build_selected_case_provenance_summary = build_selected_case_provenance_summary
_render_delivery_readiness_markdown = render_delivery_readiness_markdown
_render_markdown = render_markdown
_render_html = render_html


def _compose_summary(
    snapshot: SubmarineRuntimeSnapshot,
    report_title: str,
    solver_metrics: dict | None,
    *,
    source_runtime_stage: str,
) -> str:
    stage_text = {
        "geometry-preflight": "当前结果主要覆盖几何检查与案例匹配结论，尚未进入真实求解。",
        "solver-dispatch": "当前结果覆盖求解派发与执行状态，保留给 Supervisor 后续审阅与继续执行的边界。",
        "result-reporting": "当前结果已经进入报告整理阶段，可直接交由 Supervisor 做质量复核。",
    }.get(source_runtime_stage, "当前结果已整理为可审阅交付物。")

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
        f"已生成《{report_title}》，来源阶段为 `{source_runtime_stage}`。"
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


def _load_stability_evidence(outputs_dir: Path, artifact_virtual_paths: list[str]) -> tuple[str, dict] | None:
    return load_canonical_stability_evidence_payload(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=artifact_virtual_paths,
    )


def _load_previous_report_payload(
    outputs_dir: Path,
    *,
    artifact_virtual_paths: list[str],
    report_virtual_path: str | None,
) -> dict[str, Any] | None:
    candidate_paths: list[str] = []

    if isinstance(report_virtual_path, str) and report_virtual_path.endswith("/final-report.md"):
        candidate_paths.append(report_virtual_path[:-3] + ".json")

    candidate_paths.extend(
        path
        for path in artifact_virtual_paths
        if isinstance(path, str) and path.endswith("/final-report.json")
    )

    seen_paths: set[str] = set()
    for virtual_path in candidate_paths:
        if not virtual_path or virtual_path in seen_paths:
            continue
        seen_paths.add(virtual_path)
        local_path = _resolve_outputs_artifact(outputs_dir, virtual_path)
        if local_path is None or not local_path.exists():
            continue
        try:
            payload = json.loads(local_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload

    return None


def _workspace_run_root_virtual_path(workspace_case_dir_virtual_path: str | None) -> str | None:
    if not isinstance(workspace_case_dir_virtual_path, str):
        return None
    normalized = workspace_case_dir_virtual_path.strip().rstrip("/")
    suffix = "/openfoam-case"
    if normalized.endswith(suffix):
        return normalized[: -len(suffix)] or None
    return None


def _workspace_run_virtual_paths(
    outputs_dir: Path,
    workspace_case_dir_virtual_path: str | None,
) -> list[str]:
    run_root_virtual_path = _workspace_run_root_virtual_path(workspace_case_dir_virtual_path)
    workspace_case_dir = (
        resolve_workspace_artifact(outputs_dir, workspace_case_dir_virtual_path)
        if workspace_case_dir_virtual_path
        else None
    )
    if (
        run_root_virtual_path is None
        or workspace_case_dir is None
        or not workspace_case_dir.exists()
    ):
        return []

    run_root_dir = workspace_case_dir.parent
    candidates: list[Path] = [run_root_dir]
    candidates.extend(sorted(run_root_dir.rglob("*")))

    virtual_paths: list[str] = []
    for candidate in candidates:
        relative_path = candidate.relative_to(run_root_dir)
        if relative_path.parts:
            virtual_path = (
                run_root_virtual_path
                + "/"
                + "/".join(relative_path.parts)
            )
        else:
            virtual_path = run_root_virtual_path
        if virtual_path not in virtual_paths:
            virtual_paths.append(virtual_path)
    return virtual_paths


def _artifact_stage(virtual_path: str) -> str:
    if "/reports/" in virtual_path:
        return "result-reporting"
    if "/geometry-check/" in virtual_path:
        return "geometry-preflight"
    if "/studies/" in virtual_path:
        return "scientific-study"
    if "/solver-dispatch/" in virtual_path:
        return "solver-dispatch"
    return "result-reporting"


def _artifact_location_kind(
    virtual_path: str,
    *,
    workspace_case_dir_virtual_path: str | None,
    workspace_postprocess_virtual_path: str | None,
) -> str:
    if "/mnt/user-data/outputs/submarine/reports/" in virtual_path:
        return "report_output"
    if virtual_path.startswith("/mnt/user-data/outputs/"):
        return "solver_output"
    if workspace_case_dir_virtual_path and virtual_path == workspace_case_dir_virtual_path:
        return "workspace_case"
    if workspace_postprocess_virtual_path and (
        virtual_path == workspace_postprocess_virtual_path
        or virtual_path.startswith(workspace_postprocess_virtual_path.rstrip("/") + "/")
    ):
        return "workspace_postprocess"
    if "/studies/" in virtual_path:
        return "study_workspace_case"
    return "workspace_case_file"


def _artifact_file_type(local_path: Path | None, virtual_path: str) -> str:
    if local_path and local_path.exists() and local_path.is_dir():
        return "directory"
    suffix = Path(virtual_path).suffix.lstrip(".")
    return suffix or "file"


def _artifact_filename(local_path: Path | None, virtual_path: str) -> str:
    if local_path:
        return local_path.name
    return Path(virtual_path.rstrip("/")).name


def _artifact_label_and_description(
    *,
    filename: str,
    file_type: str,
    location_kind: str,
    virtual_path: str,
) -> tuple[str, str]:
    named_artifacts: dict[str, tuple[str, str]] = {
        "final-report.json": (
            "最终报告 JSON",
            "最终结构化 CFD 报告，供程序消费和后续追溯使用。",
        ),
        "final-report.md": (
            "最终报告 Markdown",
            "最终 CFD 技术报告的 Markdown 版本，适合人工阅读和归档。",
        ),
        "final-report.html": (
            "最终报告 HTML",
            "最终 CFD 技术报告的 HTML 版本，适合浏览器查看和交付。",
        ),
        "delivery-readiness.json": (
            "交付就绪性 JSON",
            "交付门禁判定的结构化摘要。",
        ),
        "delivery-readiness.md": (
            "交付就绪性 Markdown",
            "交付门禁判定的文字版摘要。",
        ),
        "research-evidence-summary.json": (
            "研究证据摘要 JSON",
            "汇总验证、追溯与交付证据链的结构化摘要。",
        ),
        "supervisor-scientific-gate.json": (
            "科学门禁 JSON",
            "主管智能体用于判定 claim level 与后续阶段的门禁结果。",
        ),
        "scientific-remediation-plan.json": (
            "科学整改计划 JSON",
            "针对证据缺口给出的整改建议与补救动作。",
        ),
        "scientific-remediation-handoff.json": (
            "科学整改交接 JSON",
            "用于后续自动或人工跟进的整改交接说明。",
        ),
        "dispatch-summary.md": (
            "派发摘要 Markdown",
            "求解派发阶段的概览摘要。",
        ),
        "dispatch-summary.html": (
            "派发摘要 HTML",
            "求解派发阶段的 HTML 摘要。",
        ),
        "openfoam-request.json": (
            "OpenFOAM 请求 JSON",
            "记录求解参数、路径与运行请求的派发输入。",
        ),
        "solver-results.json": (
            "求解结果 JSON",
            "OpenFOAM 求解后的主要数值结果与关键指标。",
        ),
        "solver-results.md": (
            "求解结果 Markdown",
            "OpenFOAM 求解结果的文字版摘要。",
        ),
        "stability-evidence.json": (
            "稳定性证据 JSON",
            "残差与力系数稳定性等基础验证证据。",
        ),
        "study-plan.json": (
            "研究计划 JSON",
            "科学研究扩展的试验计划。",
        ),
        "study-manifest.json": (
            "研究清单 JSON",
            "研究分支、变体与执行状态汇总。",
        ),
        "provenance-manifest.json": (
            "追溯清单 JSON",
            "记录输入、求解、后处理与报告之间的追溯关系。",
        ),
        "Allrun": (
            "OpenFOAM 运行脚本",
            "用于执行当前工作空间 case 的主脚本。",
        ),
        "controlDict": (
            "OpenFOAM controlDict",
            "定义求解控制、写出频率和时间推进策略。",
        ),
        "fvSchemes": (
            "OpenFOAM fvSchemes",
            "定义离散格式与数值格式。",
        ),
        "fvSolution": (
            "OpenFOAM fvSolution",
            "定义线性求解器和收敛参数。",
        ),
    }
    if filename in named_artifacts:
        return named_artifacts[filename]
    if location_kind == "workspace_case":
        return (
            "OpenFOAM 主 case 目录",
            "当前基线 OpenFOAM case 的工作目录，包含 system、constant、0 和后处理子目录。",
        )
    if location_kind == "study_workspace_case":
        return (
            "研究分支 workspace 项",
            "研究变体对应的 OpenFOAM 工作空间目录或文件。",
        )
    if location_kind == "workspace_postprocess":
        return (
            "OpenFOAM 后处理项",
            "OpenFOAM 后处理目录或其中的导出结果。",
        )
    if location_kind == "workspace_case_file":
        return (
            f"Workspace {file_type}",
            "OpenFOAM 工作空间中的中间文件或配置文件。",
        )
    if location_kind == "report_output":
        return (
            f"报告产物 {filename}",
            "最终报告阶段生成的交付或门禁产物。",
        )
    if location_kind == "solver_output":
        return (
            f"求解产物 {filename}",
            "求解阶段或后处理阶段生成的输出文件。",
        )
    return (
        filename,
        f"记录于 {virtual_path} 的 {file_type} 产物。",
    )


def _manifest_entry(
    *,
    outputs_dir: Path,
    virtual_path: str,
    workspace_case_dir_virtual_path: str | None,
    workspace_postprocess_virtual_path: str | None,
    final_artifact_virtual_paths: list[str],
) -> dict[str, Any]:
    local_path = resolve_user_data_artifact(outputs_dir, virtual_path)
    filename = _artifact_filename(local_path, virtual_path)
    file_type = _artifact_file_type(local_path, virtual_path)
    location_kind = _artifact_location_kind(
        virtual_path,
        workspace_case_dir_virtual_path=workspace_case_dir_virtual_path,
        workspace_postprocess_virtual_path=workspace_postprocess_virtual_path,
    )
    label, description = _artifact_label_and_description(
        filename=filename,
        file_type=file_type,
        location_kind=location_kind,
        virtual_path=virtual_path,
    )
    absolute_path = (
        str(local_path.resolve(strict=False))
        if local_path is not None
        else ""
    )
    return {
        "label": label,
        "description": description,
        "filename": filename,
        "file_type": file_type,
        "location_kind": location_kind,
        "stage": _artifact_stage(virtual_path),
        "virtual_path": virtual_path,
        "absolute_path": absolute_path,
        "is_final_deliverable": location_kind in {"report_output", "solver_output"},
    }


def _build_report_artifact_manifest(
    *,
    outputs_dir: Path,
    source_artifact_virtual_paths: list[str],
    final_artifact_virtual_paths: list[str],
    workspace_case_dir_virtual_path: str | None,
    run_script_virtual_path: str | None,
    workspace_postprocess_virtual_path: str | None,
) -> list[dict[str, Any]]:
    key_filenames = {
        "dispatch-summary.md",
        "dispatch-summary.html",
        "openfoam-request.json",
        "supervisor-handoff.json",
        "solver-results.json",
        "solver-results.md",
        "stability-evidence.json",
        "study-plan.json",
        "study-manifest.json",
        "provenance-manifest.json",
        "run-record.json",
        "run-compare-summary.json",
        "experiment-manifest.json",
        "figure-manifest.json",
        "scientific-followup-history.json",
    }
    deliverable_suffixes = {
        ".csv",
        ".png",
        ".jpg",
        ".jpeg",
        ".svg",
        ".pdf",
    }

    def is_key_artifact(virtual_path: str) -> bool:
        if virtual_path in final_artifact_virtual_paths:
            return True
        if "/studies/" in virtual_path:
            return False
        filename = Path(virtual_path.rstrip("/")).name
        if filename in key_filenames or filename.startswith("verification-"):
            return True
        return Path(filename).suffix.lower() in deliverable_suffixes

    candidate_paths = _merge_artifact_paths(
        final_artifact_virtual_paths,
        [
            path
            for path in source_artifact_virtual_paths
            if isinstance(path, str) and path.strip() and is_key_artifact(path)
        ],
    )
    manifest = [
        _manifest_entry(
            outputs_dir=outputs_dir,
            virtual_path=virtual_path,
            workspace_case_dir_virtual_path=workspace_case_dir_virtual_path,
            workspace_postprocess_virtual_path=workspace_postprocess_virtual_path,
            final_artifact_virtual_paths=final_artifact_virtual_paths,
        )
        for virtual_path in candidate_paths
        if isinstance(virtual_path, str) and virtual_path.strip()
    ]
    manifest.sort(
        key=lambda item: (
            item["stage"],
            item["location_kind"],
            item["virtual_path"],
        )
    )
    return manifest


def _build_workspace_storage_summary(
    *,
    outputs_dir: Path,
    workspace_case_dir_virtual_path: str | None,
    run_script_virtual_path: str | None,
    workspace_postprocess_virtual_path: str | None,
) -> dict[str, Any]:
    workspace_case_dir = (
        resolve_workspace_artifact(outputs_dir, workspace_case_dir_virtual_path)
        if workspace_case_dir_virtual_path
        else None
    )
    workspace_run_root_virtual_path = _workspace_run_root_virtual_path(
        workspace_case_dir_virtual_path
    )
    workspace_run_root_dir = workspace_case_dir.parent if workspace_case_dir else None
    run_script_path = (
        resolve_workspace_artifact(outputs_dir, run_script_virtual_path)
        if run_script_virtual_path
        else None
    )
    workspace_postprocess_path = (
        resolve_workspace_artifact(outputs_dir, workspace_postprocess_virtual_path)
        if workspace_postprocess_virtual_path
        else None
    )
    study_workspace_root_virtual_path = (
        f"{workspace_run_root_virtual_path}/studies"
        if workspace_run_root_virtual_path
        else ""
    )
    study_workspace_root_dir = (
        workspace_run_root_dir / "studies"
        if workspace_run_root_dir is not None
        else None
    )
    directory_notes = []
    if workspace_case_dir_virtual_path:
        directory_notes.append(
            "主 OpenFOAM case 的 system、constant 以及各时间步中间文件位于主 case 目录下。"
        )
    if workspace_postprocess_virtual_path:
        directory_notes.append("后处理结果位于 postProcessing 目录下。")
    if study_workspace_root_dir is not None and study_workspace_root_dir.exists():
        directory_notes.append("参数、网格或时间步敏感性研究变体位于 studies 目录下。")

    return {
        "workspace_run_root_virtual_path": workspace_run_root_virtual_path or "",
        "workspace_run_root_absolute_path": (
            str(workspace_run_root_dir.resolve(strict=False))
            if workspace_run_root_dir is not None
            else ""
        ),
        "workspace_case_dir_virtual_path": workspace_case_dir_virtual_path or "",
        "workspace_case_dir_absolute_path": (
            str(workspace_case_dir.resolve(strict=False))
            if workspace_case_dir is not None
            else ""
        ),
        "run_script_virtual_path": run_script_virtual_path or "",
        "run_script_absolute_path": (
            str(run_script_path.resolve(strict=False))
            if run_script_path is not None
            else ""
        ),
        "workspace_postprocess_virtual_path": workspace_postprocess_virtual_path or "",
        "workspace_postprocess_absolute_path": (
            str(workspace_postprocess_path.resolve(strict=False))
            if workspace_postprocess_path is not None
            else ""
        ),
        "study_workspace_root_virtual_path": (
            study_workspace_root_virtual_path
            if study_workspace_root_dir is not None and study_workspace_root_dir.exists()
            else ""
        ),
        "study_workspace_root_absolute_path": (
            str(study_workspace_root_dir.resolve(strict=False))
            if study_workspace_root_dir is not None and study_workspace_root_dir.exists()
            else ""
        ),
        "directory_notes": directory_notes,
    }


def _workspace_group_item(
    *,
    filename: str,
    label: str,
    description: str,
    virtual_path: str,
    absolute_path: str,
) -> dict[str, Any]:
    return {
        "label": label,
        "description": description,
        "filename": filename,
        "file_type": (
            Path(filename).suffix.lstrip(".") if Path(filename).suffix else "directory"
        ),
        "location_kind": "workspace_intermediate",
        "stage": "solver-dispatch",
        "virtual_path": virtual_path,
        "absolute_path": absolute_path,
        "is_final_deliverable": False,
    }


def _group_text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _group_string_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    normalized: list[str] = []
    for value in values:
        text = _group_text(value)
        if text:
            normalized.append(text)
    return normalized


def _build_artifact_group_summary(
    *,
    artifact_manifest: list[dict[str, Any]],
    workspace_storage_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    report_items = [
        dict(item)
        for item in artifact_manifest
        if item.get("location_kind") == "report_output"
    ]
    solver_items = [
        dict(item)
        for item in artifact_manifest
        if item.get("location_kind") == "solver_output"
    ]
    workspace_items = [
        dict(item)
        for item in artifact_manifest
        if item.get("location_kind") not in {"report_output", "solver_output"}
    ]

    for filename, label, description, virtual_key, absolute_key in [
        (
            "workspace-run-root",
            "主工作目录",
            "该轮求解在工作区中的根目录，包含主 case、studies 以及辅助脚本。",
            "workspace_run_root_virtual_path",
            "workspace_run_root_absolute_path",
        ),
        (
            "openfoam-case",
            "主 OpenFOAM case",
            "主基线 case 目录，包含 system、constant、0 以及时间步中间文件。",
            "workspace_case_dir_virtual_path",
            "workspace_case_dir_absolute_path",
        ),
        (
            "Allrun",
            "执行脚本",
            "调用 blockMesh、surfaceFeatures、snappyHexMesh 与 simpleFoam 的入口脚本。",
            "run_script_virtual_path",
            "run_script_absolute_path",
        ),
        (
            "postProcessing",
            "后处理目录",
            "forceCoeffs、forces 以及其他后处理结果所在目录。",
            "workspace_postprocess_virtual_path",
            "workspace_postprocess_absolute_path",
        ),
        (
            "studies",
            "研究变体目录",
            "网格、域范围和时间步等敏感性研究的工作目录。",
            "study_workspace_root_virtual_path",
            "study_workspace_root_absolute_path",
        ),
    ]:
        virtual_path = _group_text(workspace_storage_summary.get(virtual_key))
        absolute_path = _group_text(workspace_storage_summary.get(absolute_key))
        if not virtual_path and not absolute_path:
            continue
        workspace_items.append(
            _workspace_group_item(
                filename=filename,
                label=label,
                description=description,
                virtual_path=virtual_path,
                absolute_path=absolute_path,
            )
        )

    deduped_workspace_items: list[dict[str, Any]] = []
    seen_paths: set[tuple[str, str]] = set()
    for item in workspace_items:
        key = (
            _group_text(item.get("virtual_path")),
            _group_text(item.get("absolute_path")),
        )
        if key in seen_paths:
            continue
        seen_paths.add(key)
        deduped_workspace_items.append(item)

    return [
        {
            "group_id": "report_outputs",
            "title_zh": "报告交付文件",
            "summary_zh": "最终报告、交付门禁与研究结论说明相关文件。",
            "items": report_items,
            "notes": [],
        },
        {
            "group_id": "solver_outputs",
            "title_zh": "求解与验证输出",
            "summary_zh": "OpenFOAM 主求解结果、稳定性证据与验证摘要。",
            "items": solver_items,
            "notes": [],
        },
        {
            "group_id": "workspace_intermediate",
            "title_zh": "工作区与中间文件",
            "summary_zh": "用于复算与追溯的工作目录、中间文件位置及后处理目录。",
            "items": deduped_workspace_items,
            "notes": _group_string_list(workspace_storage_summary.get("directory_notes")),
        },
    ]


def _resolve_source_runtime_stage(
    snapshot: SubmarineRuntimeSnapshot,
    *,
    outputs_dir: Path,
) -> str:
    if snapshot.current_stage != "task-intelligence":
        return snapshot.current_stage

    previous_payload = _load_previous_report_payload(
        outputs_dir,
        artifact_virtual_paths=snapshot.artifact_virtual_paths,
        report_virtual_path=snapshot.report_virtual_path,
    )
    previous_stage = (
        previous_payload.get("source_runtime_stage")
        if isinstance(previous_payload, dict)
        else None
    )
    if isinstance(previous_stage, str) and previous_stage.strip():
        normalized_previous_stage = previous_stage.strip()
        if normalized_previous_stage != "task-intelligence":
            return normalized_previous_stage

    if previous_payload is not None:
        return "result-reporting"

    if any(
        isinstance(path, str) and path.endswith("/solver-results.json")
        for path in snapshot.artifact_virtual_paths
    ):
        return "solver-dispatch"

    return snapshot.current_stage


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
    scientific_gate_json_artifact = _artifact_virtual_path(
        run_dir_name, "supervisor-scientific-gate.json"
    )
    scientific_remediation_json_artifact = _artifact_virtual_path(
        run_dir_name, "scientific-remediation-plan.json"
    )
    scientific_remediation_handoff_json_artifact = _artifact_virtual_path(
        run_dir_name, "scientific-remediation-handoff.json"
    )
    json_artifact = _artifact_virtual_path(run_dir_name, "final-report.json")
    markdown_artifact = _artifact_virtual_path(run_dir_name, "final-report.md")
    html_artifact = _artifact_virtual_path(run_dir_name, "final-report.html")
    new_artifacts = [
        delivery_markdown_artifact,
        delivery_json_artifact,
        research_evidence_json_artifact,
        scientific_gate_json_artifact,
        scientific_remediation_json_artifact,
        scientific_remediation_handoff_json_artifact,
        markdown_artifact,
        html_artifact,
        json_artifact,
    ]
    all_artifacts = _merge_artifact_paths(snapshot.artifact_virtual_paths, new_artifacts)
    solver_metrics = _load_solver_metrics(outputs_dir, snapshot.artifact_virtual_paths)
    loaded_stability_evidence = _load_stability_evidence(
        outputs_dir,
        snapshot.artifact_virtual_paths,
    )
    stability_evidence_virtual_path = loaded_stability_evidence[0] if loaded_stability_evidence else None
    stability_evidence = loaded_stability_evidence[1] if loaded_stability_evidence else None
    selected_case = _resolve_selected_case(snapshot.selected_case_id)
    selected_case_provenance_summary = _build_selected_case_provenance_summary(
        selected_case
    )
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
        stability_evidence=stability_evidence,
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
    experiment_compare_summary = _build_experiment_compare_summary(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=all_artifacts,
    )
    figure_delivery_summary = _build_figure_delivery_summary(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=all_artifacts,
    )
    provenance_summary = _build_provenance_summary(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=all_artifacts,
        provenance_manifest_virtual_path=snapshot.provenance_manifest_virtual_path,
    )
    provenance_manifest_virtual_path = (
        provenance_summary.get("manifest_virtual_path")
        if isinstance(provenance_summary, dict)
        else snapshot.provenance_manifest_virtual_path
    )
    reproducibility_summary = _build_reproducibility_summary(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=all_artifacts,
        provenance_manifest_virtual_path=provenance_manifest_virtual_path,
        environment_parity_assessment=snapshot.environment_parity_assessment,
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
        provenance_summary=provenance_summary,
        scientific_study_summary=scientific_study_summary,
        experiment_summary=experiment_summary,
        output_delivery_plan=output_delivery_plan,
        artifact_virtual_paths=all_artifacts,
    )
    scientific_supervisor_gate = build_scientific_supervisor_gate(
        research_evidence_summary=research_evidence_summary,
        artifact_virtual_paths=[scientific_gate_json_artifact],
    )
    scientific_remediation_summary = build_scientific_remediation_summary(
        scientific_supervisor_gate=scientific_supervisor_gate,
        research_evidence_summary=research_evidence_summary,
        scientific_verification_assessment=scientific_verification_assessment,
        scientific_study_summary=scientific_study_summary,
        artifact_virtual_paths=[scientific_remediation_json_artifact],
    )
    scientific_remediation_handoff = build_scientific_remediation_handoff(
        snapshot=snapshot,
        scientific_remediation_summary=scientific_remediation_summary,
        experiment_summary=experiment_summary,
        experiment_compare_summary=experiment_compare_summary,
        artifact_virtual_paths=[scientific_remediation_handoff_json_artifact],
    )
    delivery_decision_summary = _build_delivery_decision_summary(
        scientific_supervisor_gate=scientific_supervisor_gate,
        research_evidence_summary=research_evidence_summary,
        scientific_remediation_summary=scientific_remediation_summary,
        scientific_remediation_handoff=scientific_remediation_handoff,
    )
    scientific_followup_summary = None
    if snapshot.scientific_followup_history_virtual_path:
        followup_history_path = _resolve_outputs_artifact(
            outputs_dir,
            snapshot.scientific_followup_history_virtual_path,
        )
        if followup_history_path and followup_history_path.exists():
            try:
                followup_history = load_scientific_followup_history(
                    artifact_path=followup_history_path,
                    artifact_virtual_path=snapshot.scientific_followup_history_virtual_path,
                )
            except ValueError:
                followup_history = None
            if followup_history:
                scientific_followup_summary = build_scientific_followup_summary(
                    history=followup_history,
                    history_virtual_path=snapshot.scientific_followup_history_virtual_path,
                )
    review_status = (
        "blocked"
        if scientific_supervisor_gate["gate_status"] == "blocked"
        else "ready_for_supervisor"
    )
    source_runtime_stage = _resolve_source_runtime_stage(
        snapshot,
        outputs_dir=outputs_dir,
    )

    review = build_supervisor_review_contract(
        next_recommended_stage=scientific_supervisor_gate["recommended_stage"],
        report_virtual_path=markdown_artifact,
        artifact_virtual_paths=all_artifacts,
        review_status=review_status,
        scientific_gate_status=scientific_supervisor_gate["gate_status"],
        allowed_claim_level=scientific_supervisor_gate["allowed_claim_level"],
        scientific_gate_virtual_path=scientific_gate_json_artifact,
        decision_status=delivery_decision_summary["decision_status"],
        delivery_decision_summary=delivery_decision_summary,
    )
    report_overview = _build_report_overview(
        summary_zh=_compose_summary(
            snapshot,
            report_title,
            solver_metrics,
            source_runtime_stage=source_runtime_stage,
        ),
        scientific_supervisor_gate=scientific_supervisor_gate,
        reproducibility_summary=reproducibility_summary,
        review_status=review.review_status,
        scientific_followup_summary=scientific_followup_summary,
        research_evidence_summary=research_evidence_summary,
    )
    delivery_highlights = _build_delivery_highlights(
        solver_metrics=solver_metrics,
        scientific_supervisor_gate=scientific_supervisor_gate,
        reproducibility_summary=reproducibility_summary,
        review_status=review.review_status,
        figure_delivery_summary=figure_delivery_summary,
        final_artifact_virtual_paths=new_artifacts,
        source_report_virtual_path=snapshot.report_virtual_path,
        provenance_manifest_virtual_path=provenance_manifest_virtual_path,
        scientific_gate_virtual_path=scientific_gate_json_artifact,
    )
    conclusion_sections = _build_conclusion_sections(
        summary_zh=report_overview["current_conclusion_zh"],
        scientific_supervisor_gate=scientific_supervisor_gate,
        research_evidence_summary=research_evidence_summary,
        reproducibility_summary=reproducibility_summary,
        provenance_manifest_virtual_path=provenance_manifest_virtual_path,
        scientific_gate_virtual_path=scientific_gate_json_artifact,
        stability_evidence_virtual_path=stability_evidence_virtual_path,
        source_report_virtual_path=snapshot.report_virtual_path,
        source_artifact_virtual_paths=snapshot.artifact_virtual_paths,
        final_artifact_virtual_paths=new_artifacts,
        figure_delivery_summary=figure_delivery_summary,
        scientific_followup_summary=scientific_followup_summary,
    )
    evidence_index = _build_evidence_index(
        research_evidence_summary=research_evidence_summary,
        figure_delivery_summary=figure_delivery_summary,
        scientific_followup_summary=scientific_followup_summary,
        source_artifact_virtual_paths=snapshot.artifact_virtual_paths,
        final_artifact_virtual_paths=new_artifacts,
        provenance_manifest_virtual_path=provenance_manifest_virtual_path,
        source_report_virtual_path=snapshot.report_virtual_path,
        scientific_gate_virtual_path=scientific_gate_json_artifact,
        stability_evidence_virtual_path=stability_evidence_virtual_path,
        supervisor_handoff_virtual_path=scientific_remediation_handoff_json_artifact,
    )
    workspace_postprocess_virtual_path = None
    if isinstance(solver_metrics, dict):
        raw_workspace_postprocess_virtual_path = solver_metrics.get(
            "workspace_postprocess_virtual_path"
        )
        if isinstance(raw_workspace_postprocess_virtual_path, str):
            workspace_postprocess_virtual_path = raw_workspace_postprocess_virtual_path
    artifact_manifest = _build_report_artifact_manifest(
        outputs_dir=outputs_dir,
        source_artifact_virtual_paths=snapshot.artifact_virtual_paths,
        final_artifact_virtual_paths=new_artifacts,
        workspace_case_dir_virtual_path=snapshot.workspace_case_dir_virtual_path,
        run_script_virtual_path=snapshot.run_script_virtual_path,
        workspace_postprocess_virtual_path=workspace_postprocess_virtual_path,
    )
    workspace_storage_summary = _build_workspace_storage_summary(
        outputs_dir=outputs_dir,
        workspace_case_dir_virtual_path=snapshot.workspace_case_dir_virtual_path,
        run_script_virtual_path=snapshot.run_script_virtual_path,
        workspace_postprocess_virtual_path=workspace_postprocess_virtual_path,
    )
    artifact_group_summary = _build_artifact_group_summary(
        artifact_manifest=artifact_manifest,
        workspace_storage_summary=workspace_storage_summary,
    )
    payload = {
        "report_title": report_title,
        "summary_zh": report_overview["current_conclusion_zh"],
        "source_runtime_stage": source_runtime_stage,
        "task_summary": snapshot.task_summary,
        "confirmation_status": snapshot.confirmation_status,
        "contract_revision": snapshot.contract_revision,
        "iteration_mode": snapshot.iteration_mode,
        "revision_summary": snapshot.revision_summary,
        "execution_preference": snapshot.execution_preference,
        "task_type": snapshot.task_type,
        "geometry_virtual_path": snapshot.geometry_virtual_path,
        "geometry_family": snapshot.geometry_family,
        "execution_readiness": snapshot.execution_readiness,
        "selected_case_id": snapshot.selected_case_id,
        "simulation_requirements": snapshot.simulation_requirements,
        "capability_gaps": snapshot.capability_gaps,
        "unresolved_decisions": snapshot.unresolved_decisions,
        "evidence_expectations": snapshot.evidence_expectations,
        "variant_policy": snapshot.variant_policy,
        "requested_outputs": [
            item.model_dump(mode="json") for item in snapshot.requested_outputs
        ],
        "scientific_verification_requirements": scientific_verification_requirements,
        "selected_case_acceptance_profile": (
            selected_case.acceptance_profile.model_dump(mode="json")
            if selected_case and selected_case.acceptance_profile
            else None
        ),
        "selected_case_provenance_summary": selected_case_provenance_summary,
        "workspace_case_dir_virtual_path": snapshot.workspace_case_dir_virtual_path,
        "run_script_virtual_path": snapshot.run_script_virtual_path,
        "provenance_manifest_virtual_path": provenance_manifest_virtual_path,
        "provenance_summary": provenance_summary,
        "environment_fingerprint": snapshot.environment_fingerprint,
        "environment_parity_assessment": snapshot.environment_parity_assessment,
        "reproducibility_summary": reproducibility_summary,
        "report_overview": report_overview,
        "delivery_highlights": delivery_highlights,
        "conclusion_sections": conclusion_sections,
        "evidence_index": evidence_index,
        "stability_evidence_virtual_path": stability_evidence_virtual_path,
        "stability_evidence": stability_evidence,
        "supervisor_handoff_virtual_path": scientific_remediation_handoff_json_artifact,
        "source_report_virtual_path": snapshot.report_virtual_path,
        "source_artifact_virtual_paths": snapshot.artifact_virtual_paths,
        "solver_metrics": solver_metrics,
        "workspace_postprocess_virtual_path": workspace_postprocess_virtual_path,
        "acceptance_assessment": acceptance_assessment,
        "experiment_summary": experiment_summary,
        "experiment_compare_summary": experiment_compare_summary,
        "research_evidence_summary": research_evidence_summary,
        "scientific_supervisor_gate": scientific_supervisor_gate,
        "scientific_gate_status": scientific_supervisor_gate["gate_status"],
        "allowed_claim_level": scientific_supervisor_gate["allowed_claim_level"],
        "decision_status": review.decision_status,
        "delivery_decision_summary": (
            review.delivery_decision_summary.model_dump(mode="json")
            if review.delivery_decision_summary
            else None
        ),
        "recommended_actions": _recommended_actions(
            review_status=review.review_status,
            decision_status=review.decision_status,
        ),
        "scientific_remediation_summary": scientific_remediation_summary,
        "scientific_remediation_handoff": scientific_remediation_handoff,
        "scientific_followup_summary": scientific_followup_summary,
        "scientific_study_summary": scientific_study_summary,
        "figure_delivery_summary": figure_delivery_summary,
        "scientific_verification_assessment": scientific_verification_assessment,
        "output_delivery_plan": output_delivery_plan,
        "stage_status": snapshot.stage_status,
        "review_status": review.review_status,
        "next_recommended_stage": review.next_recommended_stage,
        "report_virtual_path": review.report_virtual_path,
        "scientific_gate_virtual_path": review.scientific_gate_virtual_path,
        "final_artifact_virtual_paths": new_artifacts,
        "artifact_virtual_paths": review.artifact_virtual_paths,
        "artifact_manifest": artifact_manifest,
        "artifact_group_summary": artifact_group_summary,
        "workspace_storage_summary": workspace_storage_summary,
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
    (artifact_dir / "supervisor-scientific-gate.json").write_text(
        json.dumps(scientific_supervisor_gate, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (artifact_dir / "scientific-remediation-plan.json").write_text(
        json.dumps(scientific_remediation_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (artifact_dir / "scientific-remediation-handoff.json").write_text(
        json.dumps(scientific_remediation_handoff, ensure_ascii=False, indent=2),
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
