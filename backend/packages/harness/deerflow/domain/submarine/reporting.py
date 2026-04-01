"""Submarine result reporting and final artifact generation."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .artifact_store import load_canonical_stability_evidence_payload
from .contracts import SubmarineRuntimeSnapshot, build_supervisor_review_contract
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
    build_experiment_compare_summary,
    build_experiment_summary,
    build_figure_delivery_summary,
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


_resolve_outputs_artifact = resolve_outputs_artifact
_resolve_selected_case = resolve_selected_case
_build_acceptance_assessment = build_acceptance_assessment
_build_scientific_study_summary = build_scientific_study_summary
_build_experiment_summary = build_experiment_summary
_build_experiment_compare_summary = build_experiment_compare_summary
_build_figure_delivery_summary = build_figure_delivery_summary
_render_delivery_readiness_markdown = render_delivery_readiness_markdown
_render_markdown = render_markdown
_render_html = render_html


def _compose_summary(
    snapshot: SubmarineRuntimeSnapshot,
    report_title: str,
    solver_metrics: dict | None,
) -> str:
    stage_text = {
        "geometry-preflight": "当前结果主要覆盖几何检查与案例匹配结论，尚未进入真实求解。",
        "solver-dispatch": "当前结果覆盖求解派发与执行状态，保留给 Supervisor 后续审阅与继续执行的边界。",
        "result-reporting": "当前结果已经进入报告整理阶段，可直接交由 Supervisor 做质量复核。",
    }.get(snapshot.current_stage, "当前结果已整理为可审阅交付物。")

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
        f"已生成《{report_title}》，来源阶段为 `{snapshot.current_stage}`。"
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
        artifact_virtual_paths=[scientific_remediation_handoff_json_artifact],
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

    review = build_supervisor_review_contract(
        next_recommended_stage=scientific_supervisor_gate["recommended_stage"],
        report_virtual_path=markdown_artifact,
        artifact_virtual_paths=all_artifacts,
        review_status=review_status,
        scientific_gate_status=scientific_supervisor_gate["gate_status"],
        allowed_claim_level=scientific_supervisor_gate["allowed_claim_level"],
        scientific_gate_virtual_path=scientific_gate_json_artifact,
    )
    payload = {
        "report_title": report_title,
        "summary_zh": _compose_summary(snapshot, report_title, solver_metrics),
        "source_runtime_stage": snapshot.current_stage,
        "task_summary": snapshot.task_summary,
        "confirmation_status": snapshot.confirmation_status,
        "execution_preference": snapshot.execution_preference,
        "task_type": snapshot.task_type,
        "geometry_virtual_path": snapshot.geometry_virtual_path,
        "geometry_family": snapshot.geometry_family,
        "execution_readiness": snapshot.execution_readiness,
        "selected_case_id": snapshot.selected_case_id,
        "requested_outputs": [
            item.model_dump(mode="json") for item in snapshot.requested_outputs
        ],
        "scientific_verification_requirements": scientific_verification_requirements,
        "selected_case_acceptance_profile": (
            selected_case.acceptance_profile.model_dump(mode="json")
            if selected_case and selected_case.acceptance_profile
            else None
        ),
        "workspace_case_dir_virtual_path": snapshot.workspace_case_dir_virtual_path,
        "run_script_virtual_path": snapshot.run_script_virtual_path,
        "stability_evidence_virtual_path": stability_evidence_virtual_path,
        "stability_evidence": stability_evidence,
        "supervisor_handoff_virtual_path": scientific_remediation_handoff_json_artifact,
        "source_report_virtual_path": snapshot.report_virtual_path,
        "source_artifact_virtual_paths": snapshot.artifact_virtual_paths,
        "solver_metrics": solver_metrics,
        "acceptance_assessment": acceptance_assessment,
        "experiment_summary": experiment_summary,
        "experiment_compare_summary": experiment_compare_summary,
        "research_evidence_summary": research_evidence_summary,
        "scientific_supervisor_gate": scientific_supervisor_gate,
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
