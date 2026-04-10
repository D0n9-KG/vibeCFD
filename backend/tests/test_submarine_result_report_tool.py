import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from deerflow.config.paths import Paths

geometry_tool_module = importlib.import_module("deerflow.tools.builtins.submarine_geometry_check_tool")


def _make_runtime(paths: Paths, thread_id: str = "thread-1") -> SimpleNamespace:
    return SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(paths.sandbox_outputs_dir(thread_id)),
            }
        },
        context={"thread_id": thread_id},
    )


def _write_ascii_stl(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "solid demo",
                "facet normal 0 0 0",
                "  outer loop",
                "    vertex 0 0 0",
                "    vertex 4 0 0",
                "    vertex 0 1 0",
                "  endloop",
                "endfacet",
                "facet normal 0 0 0",
                "  outer loop",
                "    vertex 4 0 0",
                "    vertex 4 1 0",
                "    vertex 0 1 0",
                "  endloop",
                "endfacet",
                "endsolid demo",
            ]
        ),
        encoding="utf-8",
    )


def _execution_plan_status(runtime_state: dict, role_id: str) -> str:
    return next(
        item["status"]
        for item in runtime_state["execution_plan"]
        if item["role_id"] == role_id
    )


def test_submarine_result_report_tool_generates_final_report(tmp_path, monkeypatch):
    report_tool_module = importlib.import_module("deerflow.tools.builtins.submarine_result_report_tool")

    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "report-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(geometry_tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    geometry_result = geometry_tool_module.submarine_geometry_check_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/report-demo.stl",
        task_description="检查几何并为潜艇阻力任务生成可交付结果",
        task_type="resistance",
        geometry_family_hint="Type 209",
        tool_call_id="tc-geometry-report",
    )
    runtime.state["artifacts"] = geometry_result.update["artifacts"]
    runtime.state["submarine_runtime"] = geometry_result.update["submarine_runtime"]

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="潜艇 CFD 阶段报告",
        tool_call_id="tc-result-report",
    )

    artifacts = result.update["artifacts"]
    assert any(path.endswith("/final-report.json") for path in artifacts)
    assert any(path.endswith("/final-report.md") for path in artifacts)
    assert any(path.endswith("/final-report.html") for path in artifacts)

    json_path = outputs_dir / "submarine" / "reports" / "report-demo" / "final-report.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["report_title"] == "潜艇 CFD 阶段报告"
    assert "潜艇 CFD 阶段报告" in payload["summary_zh"]
    assert payload["source_runtime_stage"] == "geometry-preflight"
    assert payload["review_status"] == "blocked"
    assert payload["next_recommended_stage"] == "solver-dispatch"
    assert payload["scientific_supervisor_gate"]["gate_status"] == "blocked"
    assert payload["scientific_supervisor_gate"]["allowed_claim_level"] == "delivery_only"
    assert payload["decision_status"] == "blocked_by_setup"
    assert payload["delivery_decision_summary"]["decision_status"] == "blocked_by_setup"
    assert payload["delivery_decision_summary"]["recommended_option_id"] == "fix_setup"
    assert [item["option_id"] for item in payload["delivery_decision_summary"]["options"]] == [
        "fix_setup"
    ]
    assert payload["scientific_followup_summary"] is None
    assert payload["recommended_actions"]
    assert "review_report_artifacts" in payload["recommended_actions"]
    assert payload["report_virtual_path"].endswith("/final-report.md")
    assert payload["artifact_virtual_paths"]
    assert payload["report_overview"]["current_conclusion_zh"] == payload["summary_zh"]
    assert payload["report_overview"]["allowed_claim_level"] == "delivery_only"
    assert payload["delivery_highlights"]["metric_lines"]
    assert payload["conclusion_sections"]
    assert (
        payload["conclusion_sections"][0]["claim_level"]
        == payload["report_overview"]["allowed_claim_level"]
    )
    assert payload["conclusion_sections"][0]["inline_source_refs"]
    assert payload["evidence_index"]
    assert any(
        item["group_id"] == "runtime_and_lineage" for item in payload["evidence_index"]
    )
    assert result.update["submarine_runtime"]["current_stage"] == "result-reporting"
    assert result.update["submarine_runtime"]["report_virtual_path"].endswith("/final-report.md")
    assert (
        result.update["submarine_runtime"]["scientific_followup_history_virtual_path"]
        is None
    )
    assert result.update["submarine_runtime"]["scientific_gate_status"] == "blocked"
    assert result.update["submarine_runtime"]["decision_status"] == "blocked_by_setup"
    assert "review_report_artifacts" in result.update["submarine_runtime"]["recommended_actions"]
    assert (
        result.update["submarine_runtime"]["delivery_decision_summary"][
            "recommended_option_id"
        ]
        == "fix_setup"
    )
    message = result.update["messages"][0].content
    assert "研究产物" in message
    assert "DeerFlow artifacts" not in message


def test_submarine_result_report_tool_includes_solver_metrics(tmp_path):
    report_tool_module = importlib.import_module("deerflow.tools.builtins.submarine_result_report_tool")

    paths = Paths(tmp_path)
    thread_id = "thread-1"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "metrics-demo"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "workspace_postprocess_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/metrics-demo/openfoam-case/postProcessing",
                "latest_force_coefficients": {
                    "Time": 200.0,
                    "Cd": 0.12,
                    "Cl": 0.0,
                    "Cs": 0.0,
                    "CmPitch": 0.01,
                },
                "latest_forces": {
                    "Time": 200.0,
                    "pressure_force": [0.0, 0.0, 0.0],
                    "viscous_force": [8.0, 0.0, 0.0],
                    "total_force": [8.0, 0.0, 0.0],
                    "pressure_moment": [0.0, 0.0, 0.0],
                    "viscous_moment": [0.0, 0.5, 0.0],
                    "total_moment": [0.0, 0.5, 0.0],
                },
                "reference_values": {
                    "reference_length_m": 4.0,
                    "reference_area_m2": 1.0,
                    "inlet_velocity_mps": 5.0,
                    "fluid_density_kg_m3": 1000.0,
                },
                "simulation_requirements": {
                    "inlet_velocity_mps": 7.5,
                    "fluid_density_kg_m3": 998.2,
                    "kinematic_viscosity_m2ps": 8.5e-07,
                    "end_time_seconds": 600.0,
                    "delta_t_seconds": 0.5,
                    "write_interval_steps": 20,
                },
                "mesh_summary": {
                    "mesh_ok": True,
                    "points": 10234,
                    "faces": 28764,
                    "internal_faces": 27654,
                    "cells": 9342,
                },
                "residual_summary": {
                    "field_count": 3,
                    "latest_time": 200.0,
                    "max_final_residual": 0.00014,
                    "latest_by_field": {
                        "Ux": {
                            "Time": 200.0,
                            "solver": "smoothSolver",
                            "field": "Ux",
                            "initial_residual": 0.00031,
                            "final_residual": 3e-08,
                            "iterations": 2,
                        },
                        "p": {
                            "Time": 200.0,
                            "solver": "GAMG",
                            "field": "p",
                            "initial_residual": 0.012,
                            "final_residual": 0.00014,
                            "iterations": 5,
                        },
                    },
                    "history": [],
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "confirmation_status": "confirmed",
                "execution_preference": "execute_now",
                "task_summary": "真实 OpenFOAM 结果整理",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/metrics-demo.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "execution_plan": [
                    {
                        "role_id": "claude-code-supervisor",
                        "owner": "Claude Code",
                        "goal": "确认方案",
                        "status": "completed",
                    },
                    {
                        "role_id": "task-intelligence",
                        "owner": "DeerFlow task-intelligence",
                        "goal": "完成任务理解",
                        "status": "completed",
                    },
                    {
                        "role_id": "geometry-preflight",
                        "owner": "DeerFlow geometry-preflight",
                        "goal": "完成几何预检",
                        "status": "completed",
                    },
                    {
                        "role_id": "solver-dispatch",
                        "owner": "DeerFlow solver-dispatch",
                        "goal": "完成求解派发",
                        "status": "completed",
                    },
                    {
                        "role_id": "result-reporting",
                        "owner": "DeerFlow result-reporting",
                        "goal": "生成最终报告",
                        "status": "ready",
                    },
                ],
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "workspace_case_dir_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/metrics-demo/openfoam-case",
                "run_script_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/metrics-demo/openfoam-case/Allrun",
                "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/metrics-demo/supervisor-handoff.json",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/metrics-demo/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/metrics-demo/solver-results.json",
                ],
                "activity_timeline": [
                    {
                        "stage": "task-intelligence",
                        "actor": "claude-code-supervisor",
                        "title": "设计简报已确认",
                        "summary": "Claude Code 已与用户确认第一版 CFD 方案。",
                        "status": "confirmed",
                        "timestamp": "2026-03-26T10:40:00+00:00",
                    },
                    {
                        "stage": "solver-dispatch",
                        "actor": "solver-dispatch",
                        "title": "OpenFOAM 求解已执行",
                        "summary": "已完成求解并写回 solver-results 产物。",
                        "status": "executed",
                        "timestamp": "2026-03-26T10:45:00+00:00",
                    },
                ],
            },
        },
        context={"thread_id": thread_id},
    )

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="潜艇 CFD 结果指标报告",
        tool_call_id="tc-result-report-metrics",
    )

    json_path = outputs_dir / "submarine" / "reports" / "metrics-demo" / "final-report.json"
    md_path = outputs_dir / "submarine" / "reports" / "metrics-demo" / "final-report.md"
    html_path = outputs_dir / "submarine" / "reports" / "metrics-demo" / "final-report.html"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")
    html = html_path.read_text(encoding="utf-8")

    assert payload["report_title"] == "潜艇 CFD 结果指标报告"
    assert "CFD 指标" in payload["summary_zh"]
    assert payload["task_summary"] == "真实 OpenFOAM 结果整理"
    assert payload["confirmation_status"] == "confirmed"
    assert payload["execution_preference"] == "execute_now"
    assert payload["execution_readiness"] == "stl_ready"
    assert payload["solver_metrics"]["latest_force_coefficients"]["Cd"] == 0.12
    assert payload["solver_metrics"]["latest_forces"]["total_force"][0] == 8.0
    assert payload["solver_metrics"]["final_time_seconds"] == 200.0
    assert payload["solver_metrics"]["simulation_requirements"]["end_time_seconds"] == 600.0
    assert payload["solver_metrics"]["mesh_summary"]["cells"] == 9342
    assert payload["solver_metrics"]["residual_summary"]["latest_by_field"]["p"]["final_residual"] == 0.00014
    assert payload["report_overview"]["allowed_claim_level"] == "delivery_only"
    assert payload["report_overview"]["review_status"] == payload["review_status"]
    assert payload["delivery_highlights"]["metric_lines"]
    assert any("Cd" in line for line in payload["delivery_highlights"]["metric_lines"])
    assert payload["conclusion_sections"]
    assert payload["conclusion_sections"][0]["claim_level"] == "delivery_only"
    assert payload["evidence_index"]
    markdown_headings = [
        "## 结论摘要",
        "## 关键指标与代表图表",
        "## 结论与证据",
        "## 证据索引",
        "## 建议下一步",
    ]
    html_headings = [
        "<h2>结论摘要</h2>",
        "<h2>关键指标与代表图表</h2>",
        "<h2>结论与证据</h2>",
        "<h2>证据索引</h2>",
        "<h2>建议下一步</h2>",
    ]
    assert [markdown.index(item) for item in markdown_headings] == sorted(
        markdown.index(item) for item in markdown_headings
    )
    assert [html.index(item) for item in html_headings] == sorted(
        html.index(item) for item in html_headings
    )
    assert "来源：" in markdown
    assert "Claim level：" in markdown
    assert "置信度：" in markdown
    assert "证据缺口：" in markdown
    assert "<strong>来源：</strong>" in html
    assert "<strong>Claim level：</strong>" in html
    assert "<strong>置信度：</strong>" in html
    assert "<strong>证据缺口：</strong>" in html
    assert any(path.endswith("/final-report.json") for path in result.update["artifacts"])
    assert len(result.update["submarine_runtime"]["activity_timeline"]) == 3
    assert result.update["submarine_runtime"]["activity_timeline"][-1]["stage"] == "result-reporting"
    assert (
        _execution_plan_status(result.update["submarine_runtime"], "result-reporting")
        == "completed"
    )


def test_submarine_result_report_updates_scientific_capability_plan_statuses(
    tmp_path, monkeypatch
):
    contracts_module = importlib.import_module("deerflow.domain.submarine.contracts")
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-capability-report"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = contracts_module.build_runtime_snapshot(
        current_stage="solver-dispatch",
        confirmation_status="confirmed",
        execution_preference="preflight_then_execute",
        task_summary="执行并复核潜艇 CFD 研究链路",
        task_type="resistance",
        geometry_virtual_path="/mnt/user-data/uploads/capability-report.stl",
        geometry_family="DARPA SUBOFF",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        next_recommended_stage="result-reporting",
        report_virtual_path="/mnt/user-data/outputs/submarine/solver-dispatch/capability-report/dispatch-summary.md",
        artifact_virtual_paths=[
            "/mnt/user-data/outputs/submarine/solver-dispatch/capability-report/study-manifest.json"
        ],
        execution_plan=contracts_module.build_execution_plan(
            confirmation_status="confirmed"
        ),
    ).model_dump(mode="json")

    monkeypatch.setattr(
        report_tool_module,
        "run_result_report",
        lambda **_: (
            {
                "summary_zh": "已完成研究证据链报告整理。",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "supervisor-review",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/capability-report/final-report.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/reports/capability-report/final-report.json",
                    "/mnt/user-data/outputs/submarine/reports/capability-report/scientific-followup-history.json",
                ],
                "output_delivery_plan": [],
                "scientific_supervisor_gate": {
                    "gate_status": "claim_limited",
                    "allowed_claim_level": "validated_with_gaps",
                },
                "scientific_gate_virtual_path": "/mnt/user-data/outputs/submarine/reports/capability-report/supervisor-scientific-gate.json",
                "scientific_study_summary": {
                    "study_execution_status": "completed",
                    "workflow_status": "completed",
                },
                "experiment_summary": {
                    "experiment_status": "completed",
                    "workflow_status": "completed",
                    "run_count": 4,
                },
                "experiment_compare_summary": {
                    "compare_count": 3,
                    "workflow_status": "completed",
                },
                "scientific_verification_assessment": {
                    "status": "needs_more_verification",
                },
                "scientific_remediation_handoff": {
                    "handoff_status": "ready_for_auto_followup",
                },
                "scientific_followup_summary": {
                    "history_virtual_path": "/mnt/user-data/outputs/submarine/reports/capability-report/scientific-followup-history.json",
                    "entry_count": 1,
                    "latest_outcome_status": "dispatch_refreshed_report",
                },
            },
            [
                "/mnt/user-data/outputs/submarine/reports/capability-report/final-report.md",
                "/mnt/user-data/outputs/submarine/reports/capability-report/final-report.json",
            ],
        ),
    )

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        tool_call_id="tc-capability-plan-report",
    )

    runtime_state = result.update["submarine_runtime"]

    assert runtime_state["confirmation_status"] == "confirmed"
    assert runtime_state["execution_preference"] == "preflight_then_execute"
    assert _execution_plan_status(runtime_state, "scientific-study") == "completed"
    assert _execution_plan_status(runtime_state, "experiment-compare") == "completed"
    assert _execution_plan_status(runtime_state, "scientific-verification") == "completed"
    assert _execution_plan_status(runtime_state, "scientific-followup") == "completed"


def test_submarine_result_report_emits_delivery_readiness_artifacts(tmp_path):
    report_tool_module = importlib.import_module("deerflow.tools.builtins.submarine_result_report_tool")

    paths = Paths(tmp_path)
    thread_id = "thread-acceptance"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "acceptance-demo"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "workspace_postprocess_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/acceptance-demo/openfoam-case/postProcessing",
                "latest_force_coefficients": {
                    "Time": 200.0,
                    "Cd": 0.12,
                    "Cl": 0.0,
                    "Cs": 0.0,
                    "CmPitch": 0.01,
                },
                "mesh_summary": {
                    "mesh_ok": True,
                    "points": 10234,
                    "faces": 28764,
                    "internal_faces": 27654,
                    "cells": 9342,
                },
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 0.00014,
                    "latest_by_field": {
                        "Ux": {
                            "Time": 200.0,
                            "solver": "smoothSolver",
                            "field": "Ux",
                            "initial_residual": 0.00031,
                            "final_residual": 3e-08,
                            "iterations": 2,
                        },
                        "p": {
                            "Time": 200.0,
                            "solver": "GAMG",
                            "field": "p",
                            "initial_residual": 0.012,
                            "final_residual": 0.00014,
                            "iterations": 5,
                        },
                    },
                    "history": [],
                },
                "simulation_requirements": {
                    "inlet_velocity_mps": 7.5,
                    "fluid_density_kg_m3": 998.2,
                    "kinematic_viscosity_m2ps": 8.5e-07,
                    "end_time_seconds": 600.0,
                    "delta_t_seconds": 0.5,
                    "write_interval_steps": 20,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Assess delivery readiness",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/acceptance-demo.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "execution_plan": [
                    {
                        "role_id": "claude-code-supervisor",
                        "owner": "Claude Code",
                        "goal": "Confirm plan",
                        "status": "completed",
                    },
                    {
                        "role_id": "task-intelligence",
                        "owner": "DeerFlow task-intelligence",
                        "goal": "Resolve workflow",
                        "status": "completed",
                    },
                    {
                        "role_id": "geometry-preflight",
                        "owner": "DeerFlow geometry-preflight",
                        "goal": "Check geometry",
                        "status": "completed",
                    },
                    {
                        "role_id": "solver-dispatch",
                        "owner": "DeerFlow solver-dispatch",
                        "goal": "Run solver",
                        "status": "completed",
                    },
                    {
                        "role_id": "result-reporting",
                        "owner": "DeerFlow result-reporting",
                        "goal": "Summarize report",
                        "status": "ready",
                    },
                ],
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "workspace_case_dir_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/acceptance-demo/openfoam-case",
                "run_script_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/acceptance-demo/openfoam-case/Allrun",
                "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/acceptance-demo/supervisor-handoff.json",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/acceptance-demo/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/acceptance-demo/solver-results.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Acceptance report",
        tool_call_id="tc-result-report-acceptance",
    )

    readiness_path = (
        outputs_dir
        / "submarine"
        / "reports"
        / "acceptance-demo"
        / "delivery-readiness.json"
    )
    readiness_payload = json.loads(readiness_path.read_text(encoding="utf-8"))
    final_report_path = (
        outputs_dir
        / "submarine"
        / "reports"
        / "acceptance-demo"
        / "final-report.json"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))

    assert any(
        path.endswith("/delivery-readiness.json")
        for path in result.update["artifacts"]
    )
    assert any(
        path.endswith("/delivery-readiness.md")
        for path in result.update["artifacts"]
    )
    assert readiness_payload["status"] == "ready_for_review"
    assert readiness_payload["confidence"] == "medium"
    assert readiness_payload["gate_count"] >= 4
    assert any(
        gate["id"] == "planned_end_time_reached" and gate["status"] == "warning"
        for gate in readiness_payload["gates"]
    )
    assert final_payload["acceptance_assessment"]["status"] == "ready_for_review"
    assert final_payload["acceptance_assessment"]["confidence"] == "medium"
    assert any(
        "end_time_seconds" in warning
        for warning in final_payload["acceptance_assessment"]["warnings"]
    )


def test_submarine_result_report_applies_case_acceptance_profile(tmp_path):
    report_tool_module = importlib.import_module("deerflow.tools.builtins.submarine_result_report_tool")

    paths = Paths(tmp_path)
    thread_id = "thread-case-profile"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "profile-demo"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "workspace_postprocess_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/profile-demo/openfoam-case/postProcessing",
                "latest_force_coefficients": {
                    "Time": 200.0,
                    "Cd": 0.12,
                    "Cl": 0.0,
                    "Cs": 0.0,
                    "CmPitch": 0.01,
                },
                "mesh_summary": {
                    "mesh_ok": True,
                    "points": 10234,
                    "faces": 28764,
                    "internal_faces": 27654,
                    "cells": 9342,
                },
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 0.002,
                    "latest_by_field": {
                        "Ux": {
                            "Time": 200.0,
                            "solver": "smoothSolver",
                            "field": "Ux",
                            "initial_residual": 0.00031,
                            "final_residual": 4e-07,
                            "iterations": 2,
                        },
                        "p": {
                            "Time": 200.0,
                            "solver": "GAMG",
                            "field": "p",
                            "initial_residual": 0.012,
                            "final_residual": 0.002,
                            "iterations": 5,
                        },
                    },
                    "history": [],
                },
                "simulation_requirements": {
                    "inlet_velocity_mps": 5.0,
                    "fluid_density_kg_m3": 1000.0,
                    "kinematic_viscosity_m2ps": 1.0e-06,
                    "end_time_seconds": 200.0,
                    "delta_t_seconds": 1.0,
                    "write_interval_steps": 50,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Evaluate case-specific acceptance",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/profile-demo.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "execution_plan": [
                    {
                        "role_id": "claude-code-supervisor",
                        "owner": "Claude Code",
                        "goal": "Confirm plan",
                        "status": "completed",
                    },
                    {
                        "role_id": "task-intelligence",
                        "owner": "DeerFlow task-intelligence",
                        "goal": "Resolve workflow",
                        "status": "completed",
                    },
                    {
                        "role_id": "geometry-preflight",
                        "owner": "DeerFlow geometry-preflight",
                        "goal": "Check geometry",
                        "status": "completed",
                    },
                    {
                        "role_id": "solver-dispatch",
                        "owner": "DeerFlow solver-dispatch",
                        "goal": "Run solver",
                        "status": "completed",
                    },
                    {
                        "role_id": "result-reporting",
                        "owner": "DeerFlow result-reporting",
                        "goal": "Summarize report",
                        "status": "ready",
                    },
                ],
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "workspace_case_dir_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/profile-demo/openfoam-case",
                "run_script_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/profile-demo/openfoam-case/Allrun",
                "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/profile-demo/supervisor-handoff.json",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/profile-demo/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/profile-demo/solver-results.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Case profile report",
        tool_call_id="tc-result-report-profile",
    )

    final_report_path = (
        outputs_dir / "submarine" / "reports" / "profile-demo" / "final-report.json"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))

    assert (
        final_payload["selected_case_acceptance_profile"]["profile_id"]
        == "darpa-suboff-resistance-baseline"
    )
    assert final_payload["acceptance_assessment"]["status"] == "blocked"
    assert any(
        gate["id"] == "case_max_final_residual" and gate["status"] == "blocked"
        for gate in final_payload["acceptance_assessment"]["gates"]
    )
    assert any(
        "0.002" in item
        for item in final_payload["acceptance_assessment"]["blocking_issues"]
    )


def test_submarine_result_report_adds_benchmark_comparison_for_matching_case(tmp_path):
    report_tool_module = importlib.import_module("deerflow.tools.builtins.submarine_result_report_tool")

    paths = Paths(tmp_path)
    thread_id = "thread-benchmark-pass"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "benchmark-pass"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "workspace_postprocess_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/benchmark-pass/openfoam-case/postProcessing",
                "latest_force_coefficients": {
                    "Time": 200.0,
                    "Cd": 0.00310,
                    "Cl": 0.0,
                    "Cs": 0.0,
                    "CmPitch": 0.0,
                },
                "mesh_summary": {
                    "mesh_ok": True,
                    "points": 10234,
                    "faces": 28764,
                    "internal_faces": 27654,
                    "cells": 9342,
                },
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 5e-4,
                    "latest_by_field": {
                        "Ux": {
                            "Time": 200.0,
                            "solver": "smoothSolver",
                            "field": "Ux",
                            "initial_residual": 0.00031,
                            "final_residual": 4e-07,
                            "iterations": 2,
                        },
                        "p": {
                            "Time": 200.0,
                            "solver": "GAMG",
                            "field": "p",
                            "initial_residual": 0.012,
                            "final_residual": 5e-04,
                            "iterations": 5,
                        },
                    },
                    "history": [],
                },
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "fluid_density_kg_m3": 1000.0,
                    "kinematic_viscosity_m2ps": 1.0e-06,
                    "end_time_seconds": 200.0,
                    "delta_t_seconds": 1.0,
                    "write_interval_steps": 50,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Benchmark SUBOFF drag",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "execution_plan": [],
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "workspace_case_dir_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/benchmark-pass/openfoam-case",
                "run_script_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/benchmark-pass/openfoam-case/Allrun",
                "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/benchmark-pass/supervisor-handoff.json",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/benchmark-pass/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/benchmark-pass/solver-results.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Benchmark pass report",
        tool_call_id="tc-result-report-benchmark-pass",
    )

    final_report_path = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.json"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    benchmark_comparisons = final_payload["acceptance_assessment"]["benchmark_comparisons"]

    assert benchmark_comparisons
    assert benchmark_comparisons[0]["metric_id"] == "cd_at_3_05_mps"
    assert benchmark_comparisons[0]["status"] == "passed"
    assert benchmark_comparisons[0]["reference_value"] == 0.00314
    assert benchmark_comparisons[0]["observed_value"] == 0.00310
    assert benchmark_comparisons[0]["source_label"] == "Mushtaque et al. (2025) Table 6, EFD bare hull"
    assert benchmark_comparisons[0]["source_url"].startswith("https://pure.port.ac.uk/")
    assert any(
        "Mushtaque et al. (2025) Table 6, EFD bare hull" in item
        for item in final_payload["research_evidence_summary"]["benchmark_highlights"]
    )
    assert any(
        gate["id"] == "benchmark_cd_at_3_05_mps" and gate["status"] == "passed"
        for gate in final_payload["acceptance_assessment"]["gates"]
    )


def test_submarine_result_report_blocks_when_benchmark_miss_exceeds_tolerance(tmp_path):
    report_tool_module = importlib.import_module("deerflow.tools.builtins.submarine_result_report_tool")

    paths = Paths(tmp_path)
    thread_id = "thread-benchmark-blocked"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "benchmark-blocked"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "workspace_postprocess_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/benchmark-blocked/openfoam-case/postProcessing",
                "latest_force_coefficients": {
                    "Time": 200.0,
                    "Cd": 0.00360,
                    "Cl": 0.0,
                    "Cs": 0.0,
                    "CmPitch": 0.0,
                },
                "mesh_summary": {
                    "mesh_ok": True,
                    "points": 10234,
                    "faces": 28764,
                    "internal_faces": 27654,
                    "cells": 9342,
                },
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 5e-4,
                    "latest_by_field": {
                        "Ux": {
                            "Time": 200.0,
                            "solver": "smoothSolver",
                            "field": "Ux",
                            "initial_residual": 0.00031,
                            "final_residual": 4e-07,
                            "iterations": 2,
                        },
                        "p": {
                            "Time": 200.0,
                            "solver": "GAMG",
                            "field": "p",
                            "initial_residual": 0.012,
                            "final_residual": 5e-04,
                            "iterations": 5,
                        },
                    },
                    "history": [],
                },
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "fluid_density_kg_m3": 1000.0,
                    "kinematic_viscosity_m2ps": 1.0e-06,
                    "end_time_seconds": 200.0,
                    "delta_t_seconds": 1.0,
                    "write_interval_steps": 50,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Benchmark SUBOFF drag",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "execution_plan": [],
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "workspace_case_dir_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/benchmark-blocked/openfoam-case",
                "run_script_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/benchmark-blocked/openfoam-case/Allrun",
                "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/benchmark-blocked/supervisor-handoff.json",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/benchmark-blocked/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/benchmark-blocked/solver-results.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Benchmark blocked report",
        tool_call_id="tc-result-report-benchmark-blocked",
    )

    final_report_path = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.json"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    benchmark_comparisons = final_payload["acceptance_assessment"]["benchmark_comparisons"]

    assert benchmark_comparisons
    assert benchmark_comparisons[0]["metric_id"] == "cd_at_3_05_mps"
    assert benchmark_comparisons[0]["status"] == "blocked"
    assert final_payload["acceptance_assessment"]["status"] == "blocked"
    assert final_payload["research_evidence_summary"]["validation_status"] == "validation_failed"
    assert any(
        "Mushtaque et al. (2025) Table 6, EFD bare hull" in item
        for item in final_payload["research_evidence_summary"]["evidence_gaps"]
    )
    assert any(
        "Benchmark cd_at_3_05_mps" in item
        for item in final_payload["scientific_supervisor_gate"]["blocking_reasons"]
    )
    assert any(
        gate["id"] == "benchmark_cd_at_3_05_mps" and gate["status"] == "blocked"
        for gate in final_payload["acceptance_assessment"]["gates"]
    )
    assert any(
        "cd_at_3_05_mps" in item
        for item in final_payload["acceptance_assessment"]["blocking_issues"]
    )


def test_submarine_result_report_marks_benchmark_reference_not_applicable_on_velocity_mismatch(
    tmp_path,
):
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-benchmark-not-applicable"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = (
        outputs_dir / "submarine" / "solver-dispatch" / "benchmark-not-applicable"
    )
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "latest_force_coefficients": {
                    "Time": 200.0,
                    "Cd": 0.00310,
                    "Cl": 0.0,
                    "Cs": 0.0,
                    "CmPitch": 0.0,
                },
                "mesh_summary": {"mesh_ok": True, "cells": 9342},
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 5e-4,
                },
                "simulation_requirements": {
                    "inlet_velocity_mps": 5.00,
                    "fluid_density_kg_m3": 1000.0,
                    "kinematic_viscosity_m2ps": 1.0e-06,
                    "end_time_seconds": 200.0,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Benchmark SUBOFF drag at unmatched inlet velocity",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "execution_plan": [],
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/benchmark-not-applicable/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/benchmark-not-applicable/solver-results.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Benchmark not applicable report",
        tool_call_id="tc-result-report-benchmark-not-applicable",
    )

    final_report_path = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.json"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    comparison = final_payload["acceptance_assessment"]["benchmark_comparisons"][0]
    research = final_payload["research_evidence_summary"]

    assert comparison["status"] == "not_applicable"
    assert "not applicable" in comparison["detail"]
    assert research["validation_status"] == "missing_validation_reference"
    assert any(
        "not applicable to the current run condition" in item
        for item in research["evidence_gaps"]
    )


def test_submarine_result_report_tracks_requested_output_delivery(tmp_path):
    report_tool_module = importlib.import_module("deerflow.tools.builtins.submarine_result_report_tool")

    paths = Paths(tmp_path)
    thread_id = "thread-requested-report"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "requested-report"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "workspace_postprocess_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/requested-report/openfoam-case/postProcessing",
                "latest_force_coefficients": {
                    "Time": 200.0,
                    "Cd": 0.00310,
                    "Cl": 0.0,
                    "Cs": 0.0,
                    "CmPitch": 0.0,
                },
                "latest_forces": {
                    "Time": 200.0,
                    "pressure_force": [0.0, 0.0, 0.0],
                    "viscous_force": [8.0, 0.0, 0.0],
                    "total_force": [8.0, 0.0, 0.0],
                    "pressure_moment": [0.0, 0.0, 0.0],
                    "viscous_moment": [0.0, 0.5, 0.0],
                    "total_moment": [0.0, 0.5, 0.0],
                },
                "mesh_summary": {
                    "mesh_ok": True,
                    "points": 10234,
                    "faces": 28764,
                    "internal_faces": 27654,
                    "cells": 9342,
                },
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 5e-4,
                    "latest_by_field": {
                        "Ux": {
                            "Time": 200.0,
                            "solver": "smoothSolver",
                            "field": "Ux",
                            "initial_residual": 0.00031,
                            "final_residual": 4e-07,
                            "iterations": 2,
                        },
                        "p": {
                            "Time": 200.0,
                            "solver": "GAMG",
                            "field": "p",
                            "initial_residual": 0.012,
                            "final_residual": 5e-04,
                            "iterations": 5,
                        },
                    },
                    "history": [],
                },
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "fluid_density_kg_m3": 1000.0,
                    "kinematic_viscosity_m2ps": 1.0e-06,
                    "end_time_seconds": 200.0,
                    "delta_t_seconds": 1.0,
                    "write_interval_steps": 50,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "根据用户要求交付结果",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/requested-report.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "requested_outputs": [
                    {
                        "output_id": "drag_coefficient",
                        "label": "阻力系数 Cd",
                        "requested_label": "阻力系数 Cd",
                        "status": "requested",
                        "support_level": "supported",
                        "notes": "当前运行时可交付该结构化结果。",
                    },
                    {
                        "output_id": "benchmark_comparison",
                        "label": "Benchmark 对比",
                        "requested_label": "Benchmark 对比",
                        "status": "requested",
                        "support_level": "supported",
                        "notes": "当前运行时可交付该结构化结果。",
                    },
                    {
                        "output_id": "surface_pressure_contour",
                        "label": "表面压力云图",
                        "requested_label": "表面压力云图",
                        "status": "requested",
                        "support_level": "supported",
                        "notes": "当前运行时可在存在后处理文件时导出压力结果 artifact。",
                    },
                    {
                        "output_id": "chinese_report",
                        "label": "中文结果报告",
                        "requested_label": "中文结果报告",
                        "status": "requested",
                        "support_level": "supported",
                        "notes": "当前运行时可交付该结构化结果。",
                    },
                ],
                "execution_plan": [],
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "workspace_case_dir_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/requested-report/openfoam-case",
                "run_script_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/requested-report/openfoam-case/Allrun",
                "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/requested-report/supervisor-handoff.json",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/requested-report/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/requested-report/solver-results.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Requested outputs report",
        tool_call_id="tc-result-report-requested-outputs",
    )

    final_report_path = (
        outputs_dir / "submarine" / "reports" / "requested-report" / "final-report.json"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))

    assert [item["output_id"] for item in final_payload["requested_outputs"]] == [
        "drag_coefficient",
        "benchmark_comparison",
        "surface_pressure_contour",
        "chinese_report",
    ]
    assert final_payload["output_delivery_plan"][0]["delivery_status"] == "delivered"
    assert final_payload["output_delivery_plan"][1]["delivery_status"] == "delivered"
    assert final_payload["output_delivery_plan"][2]["delivery_status"] == "not_available_for_this_run"
    assert final_payload["output_delivery_plan"][3]["delivery_status"] == "delivered"


def test_submarine_result_report_marks_postprocess_exports_delivered(tmp_path):
    report_tool_module = importlib.import_module("deerflow.tools.builtins.submarine_result_report_tool")

    paths = Paths(tmp_path)
    thread_id = "thread-postprocess-report"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "postprocess-report"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "workspace_postprocess_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/postprocess-report/openfoam-case/postProcessing",
                "latest_force_coefficients": {
                    "Time": 200.0,
                    "Cd": 0.00310,
                    "Cl": 0.0,
                    "Cs": 0.0,
                    "CmPitch": 0.0,
                },
                "mesh_summary": {
                    "mesh_ok": True,
                    "points": 10234,
                    "faces": 28764,
                    "internal_faces": 27654,
                    "cells": 9342,
                },
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 5e-4,
                    "latest_by_field": {
                        "Ux": {
                            "Time": 200.0,
                            "solver": "smoothSolver",
                            "field": "Ux",
                            "initial_residual": 0.00031,
                            "final_residual": 4e-07,
                            "iterations": 2,
                        },
                        "p": {
                            "Time": 200.0,
                            "solver": "GAMG",
                            "field": "p",
                            "initial_residual": 0.012,
                            "final_residual": 5e-04,
                            "iterations": 5,
                        },
                    },
                    "history": [],
                },
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "fluid_density_kg_m3": 1000.0,
                    "kinematic_viscosity_m2ps": 1.0e-06,
                    "end_time_seconds": 200.0,
                    "delta_t_seconds": 1.0,
                    "write_interval_steps": 50,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "surface-pressure.csv").write_text(
        "x,y,z,p\n0,0,0,12.0\n",
        encoding="utf-8",
    )
    (solver_results_dir / "surface-pressure.md").write_text(
        "# Surface Pressure\n",
        encoding="utf-8",
    )
    (solver_results_dir / "wake-velocity-slice.csv").write_text(
        "x,y,z,Ux,Uy,Uz\n5,0,0,4.8,0,0\n",
        encoding="utf-8",
    )
    (solver_results_dir / "wake-velocity-slice.md").write_text(
        "# Wake Velocity Slice\n",
        encoding="utf-8",
    )
    (solver_results_dir / "figure-manifest.json").write_text(
        json.dumps(
            {
                "run_dir_name": "postprocess-report",
                "figure_count": 2,
                "figures": [
                    {
                        "figure_id": "postprocess-report:surface_pressure_contour",
                        "output_id": "surface_pressure_contour",
                        "title": "Surface Pressure Result",
                        "caption": (
                            "Surface pressure contour over the selected hull patches, "
                            "colored by p. Patch selection: hull. Samples: 1."
                        ),
                        "render_status": "rendered",
                        "field": "p",
                        "selector_summary": "Patch selection: hull",
                        "axes": ["x", "y"],
                        "color_metric": "p",
                        "sample_count": 1,
                        "value_range": {"min": 12.0, "max": 12.0},
                        "source_csv_virtual_path": (
                            "/mnt/user-data/outputs/submarine/solver-dispatch/"
                            "postprocess-report/surface-pressure.csv"
                        ),
                        "artifact_virtual_paths": [
                            "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/surface-pressure.csv",
                            "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/surface-pressure.md",
                        ],
                    },
                    {
                        "figure_id": "postprocess-report:wake_velocity_slice",
                        "output_id": "wake_velocity_slice",
                        "title": "Wake Velocity Slice",
                        "caption": (
                            "Wake velocity slice extracted from the requested cutting plane, "
                            "colored by |U|. Plane slice at x/Lref=1.25 with normal "
                            "(1.0, 0.0, 0.0). Samples: 1."
                        ),
                        "render_status": "rendered",
                        "field": "U",
                        "selector_summary": (
                            "Plane slice at x/Lref=1.25 with normal (1.0, 0.0, 0.0)"
                        ),
                        "axes": ["y", "z"],
                        "color_metric": "|U|",
                        "sample_count": 1,
                        "value_range": {"min": 4.8, "max": 4.8},
                        "source_csv_virtual_path": (
                            "/mnt/user-data/outputs/submarine/solver-dispatch/"
                            "postprocess-report/wake-velocity-slice.csv"
                        ),
                        "artifact_virtual_paths": [
                            "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/wake-velocity-slice.csv",
                            "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/wake-velocity-slice.md",
                        ],
                    },
                ],
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/surface-pressure.csv",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/surface-pressure.md",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/wake-velocity-slice.csv",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/wake-velocity-slice.md",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "交付压力和尾流结果",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/postprocess-report.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "requested_outputs": [
                    {
                        "output_id": "surface_pressure_contour",
                        "label": "表面压力云图",
                        "requested_label": "表面压力云图",
                        "status": "requested",
                        "support_level": "supported",
                        "postprocess_spec": {
                            "field": "p",
                            "time_mode": "latest",
                            "selector": {
                                "type": "patch",
                                "patches": ["hull"],
                            },
                            "formats": ["csv", "png", "report"],
                        },
                        "notes": "当前运行时可在存在后处理文件时导出压力结果 artifact。",
                    },
                    {
                        "output_id": "wake_velocity_slice",
                        "label": "尾流速度切片",
                        "requested_label": "尾流速度切片",
                        "status": "requested",
                        "support_level": "supported",
                        "postprocess_spec": {
                            "field": "U",
                            "time_mode": "latest",
                            "selector": {
                                "type": "plane",
                                "origin_mode": "x_by_lref",
                                "origin_value": 1.25,
                                "normal": [1.0, 0.0, 0.0],
                            },
                            "formats": ["csv", "png", "report"],
                        },
                        "notes": "当前运行时可在存在后处理文件时导出尾流结果 artifact。",
                    },
                ],
                "execution_plan": [],
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "workspace_case_dir_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/postprocess-report/openfoam-case",
                "run_script_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/postprocess-report/openfoam-case/Allrun",
                "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/supervisor-handoff.json",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/solver-results.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/surface-pressure.csv",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/surface-pressure.md",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/wake-velocity-slice.csv",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/wake-velocity-slice.md",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/postprocess-report/figure-manifest.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Postprocess export report",
        tool_call_id="tc-result-report-postprocess",
    )

    final_report_path = (
        outputs_dir / "submarine" / "reports" / "postprocess-report" / "final-report.json"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    final_markdown = (
        outputs_dir / "submarine" / "reports" / "postprocess-report" / "final-report.md"
    ).read_text(encoding="utf-8")
    final_html = (
        outputs_dir / "submarine" / "reports" / "postprocess-report" / "final-report.html"
    ).read_text(encoding="utf-8")

    assert final_payload["output_delivery_plan"][0]["delivery_status"] == "delivered"
    assert final_payload["output_delivery_plan"][1]["delivery_status"] == "delivered"
    assert final_payload["requested_outputs"][0]["postprocess_spec"]["formats"] == [
        "csv",
        "png",
        "report",
    ]
    assert final_payload["figure_delivery_summary"]["figure_count"] == 2
    assert final_payload["figure_delivery_summary"]["manifest_virtual_path"].endswith(
        "/figure-manifest.json"
    )
    assert final_payload["figure_delivery_summary"]["figures"][0]["caption"].startswith(
        "Surface pressure contour"
    )
    assert any(
        path.endswith("/surface-pressure.csv")
        for path in final_payload["figure_delivery_summary"]["figures"][0][
            "artifact_virtual_paths"
        ]
    )
    assert final_payload["figure_delivery_summary"]["figures"][1]["selector_summary"] == (
        "Plane slice at x/Lref=1.25 with normal (1.0, 0.0, 0.0)"
    )
    assert any(
        path.endswith("/figure-manifest.json")
        for path in final_payload["artifact_virtual_paths"]
    )
    assert "## 关键指标与代表图表" in final_markdown
    assert "Surface Pressure Result" in final_markdown
    assert "Wake Velocity Slice" in final_markdown
    assert "<h2>关键指标与代表图表</h2>" in final_html
    assert "Surface Pressure Result" in final_html
    assert "Wake Velocity Slice" in final_html


def test_submarine_result_report_adds_scientific_verification_assessment(tmp_path):
    report_tool_module = importlib.import_module("deerflow.tools.builtins.submarine_result_report_tool")

    paths = Paths(tmp_path)
    thread_id = "thread-scientific-verification"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = (
        outputs_dir / "submarine" / "solver-dispatch" / "scientific-verification"
    )
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "workspace_postprocess_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/scientific-verification/openfoam-case/postProcessing",
                "latest_force_coefficients": {
                    "Time": 200.0,
                    "Cd": 0.00312,
                    "Cl": 0.0,
                    "Cs": 0.0,
                    "CmPitch": 0.0,
                },
                "force_coefficients_history": [
                    {"Time": 160.0, "Cd": 0.00313},
                    {"Time": 170.0, "Cd": 0.00312},
                    {"Time": 180.0, "Cd": 0.00311},
                    {"Time": 190.0, "Cd": 0.00312},
                    {"Time": 200.0, "Cd": 0.00312},
                ],
                "mesh_summary": {
                    "mesh_ok": True,
                    "points": 10234,
                    "faces": 28764,
                    "internal_faces": 27654,
                    "cells": 9342,
                },
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 5e-4,
                    "latest_by_field": {
                        "Ux": {
                            "Time": 200.0,
                            "solver": "smoothSolver",
                            "field": "Ux",
                            "initial_residual": 0.00031,
                            "final_residual": 4e-07,
                            "iterations": 2,
                        },
                        "p": {
                            "Time": 200.0,
                            "solver": "GAMG",
                            "field": "p",
                            "initial_residual": 0.012,
                            "final_residual": 5e-04,
                            "iterations": 5,
                        },
                    },
                    "history": [],
                },
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "fluid_density_kg_m3": 1000.0,
                    "kinematic_viscosity_m2ps": 1.0e-06,
                    "end_time_seconds": 200.0,
                    "delta_t_seconds": 1.0,
                    "write_interval_steps": 50,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "stability-evidence.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "summary_zh": "SCI-01 基线稳定性检查已通过。",
                "source_solver_results_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/scientific-verification/solver-results.json",
                "artifact_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/scientific-verification/stability-evidence.json",
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 5e-4,
                },
                "force_coefficient_tail": {
                    "coefficient": "Cd",
                    "status": "passed",
                    "detail": "Force coefficient tail stability: tail relative spread 0.0064 <= 0.0200 for Cd.",
                    "observed_sample_count": 5,
                    "required_sample_count": 5,
                    "relative_spread": 0.0064,
                    "max_tail_relative_spread": 0.02,
                    "tail_samples": [
                        {"time": 160.0, "value": 0.00313},
                        {"time": 170.0, "value": 0.00312},
                        {"time": 180.0, "value": 0.00311},
                        {"time": 190.0, "value": 0.00312},
                        {"time": 200.0, "value": 0.00312},
                    ],
                },
                "requirements": [
                    {
                        "requirement_id": "final_residual_threshold",
                        "label": "Final residual threshold",
                        "check_type": "max_final_residual",
                        "status": "passed",
                        "detail": "Final residual threshold: observed 0.000500 <= 0.001000.",
                        "observed_value": 0.0005,
                        "limit_value": 0.001,
                    },
                    {
                        "requirement_id": "force_coefficient_tail_stability",
                        "label": "Force coefficient tail stability",
                        "check_type": "force_coefficient_tail_stability",
                        "status": "passed",
                        "detail": "Force coefficient tail stability: tail relative spread 0.0064 <= 0.0200 for Cd.",
                        "force_coefficient": "Cd",
                        "observed_sample_count": 5,
                        "required_sample_count": 5,
                        "relative_spread": 0.0064,
                        "max_tail_relative_spread": 0.02,
                    },
                ],
                "blocking_issues": [],
                "missing_evidence": [],
                "passed_requirements": [
                    "Final residual threshold: observed 0.000500 <= 0.001000.",
                    "Force coefficient tail stability: tail relative spread 0.0064 <= 0.0200 for Cd.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Evaluate research-facing scientific verification readiness",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "workspace_case_dir_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/scientific-verification/openfoam-case",
                "run_script_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/scientific-verification/openfoam-case/Allrun",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/scientific-verification/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/scientific-verification/solver-results.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/scientific-verification/stability-evidence.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Scientific verification report",
        tool_call_id="tc-result-report-scientific-verification",
    )

    final_report_path = (
        outputs_dir
        / "submarine"
        / "reports"
        / "suboff_solid"
        / "final-report.json"
    )
    md_path = (
        outputs_dir
        / "submarine"
        / "reports"
        / "suboff_solid"
        / "final-report.md"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")
    assessment = final_payload["scientific_verification_assessment"]
    stability_evidence = final_payload["stability_evidence"]

    assert assessment["status"] == "needs_more_verification"
    assert assessment["confidence"] == "medium"
    assert [item["requirement_id"] for item in assessment["requirements"]] == [
        "final_residual_threshold",
        "force_coefficient_tail_stability",
        "mesh_independence_study",
        "domain_sensitivity_study",
        "time_step_sensitivity_study",
    ]
    assert assessment["requirements"][0]["status"] == "passed"
    assert assessment["requirements"][1]["status"] == "passed"
    assert assessment["requirements"][2]["status"] == "missing_evidence"
    assert stability_evidence["status"] == "passed"
    assert stability_evidence["artifact_virtual_path"].endswith("/stability-evidence.json")
    assert stability_evidence["requirements"][0]["status"] == "passed"
    assert stability_evidence["requirements"][1]["status"] == "passed"
    assert any(
        "mesh independence" in item.lower()
        for item in assessment["missing_evidence"]
    )
    assert "## 结论与证据" in markdown


def test_scientific_verification_marks_study_artifact_as_passed(tmp_path):
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-scientific-verification-pass-artifact"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "verification-pass"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "latest_force_coefficients": {"Time": 200.0, "Cd": 0.00312},
                "force_coefficients_history": [
                    {"Time": 160.0, "Cd": 0.00313},
                    {"Time": 170.0, "Cd": 0.00312},
                    {"Time": 180.0, "Cd": 0.00311},
                    {"Time": 190.0, "Cd": 0.00312},
                    {"Time": 200.0, "Cd": 0.00312},
                ],
                "mesh_summary": {"mesh_ok": True},
                "residual_summary": {"max_final_residual": 5e-4},
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "end_time_seconds": 200.0,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "verification-mesh-independence.json").write_text(
        json.dumps(
            {
                "study_type": "mesh_independence",
                "status": "passed",
                "summary_zh": "Three-grid study shows Cd variation below tolerance.",
                "monitored_quantity": "Cd",
                "variant_count": 3,
                "relative_spread": 0.008,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "study-manifest.json").write_text(
        json.dumps(
            {
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "study_execution_status": "planned",
                "study_definitions": [
                    {
                        "study_type": "mesh_independence",
                        "summary_label": "Mesh Independence",
                        "monitored_quantity": "Cd",
                        "pass_fail_tolerance": 0.02,
                        "variants": [
                            {"variant_id": "coarse", "variant_label": "Coarse"},
                            {"variant_id": "baseline", "variant_label": "Baseline"},
                            {"variant_id": "fine", "variant_label": "Fine"},
                        ],
                    }
                ],
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verification-pass/study-manifest.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verification-pass/verification-mesh-independence.json",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Evaluate scientific verification evidence artifacts",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/verification-pass/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verification-pass/solver-results.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verification-pass/study-manifest.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verification-pass/verification-mesh-independence.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Scientific verification pass artifact report",
        tool_call_id="tc-result-report-scientific-pass-artifact",
    )

    final_report_virtual_path = next(
        path for path in result.update["artifacts"] if path.endswith("/final-report.json")
    )
    final_report_path = outputs_dir.joinpath(
        *[
            part
            for part in final_report_virtual_path.removeprefix("/mnt/user-data/outputs/").split("/")
            if part
        ]
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    requirements = final_payload["scientific_verification_assessment"]["requirements"]
    mesh_requirement = next(
        item for item in requirements if item["requirement_id"] == "mesh_independence_study"
    )
    scientific_study_summary = final_payload["scientific_study_summary"]
    mesh_study = next(
        item
        for item in scientific_study_summary["studies"]
        if item["study_type"] == "mesh_independence"
    )

    assert mesh_requirement["status"] == "passed"
    assert "below tolerance" in mesh_requirement["detail"]
    assert scientific_study_summary["study_execution_status"] == "planned"
    assert any(
        path.endswith("/study-manifest.json")
        for path in scientific_study_summary["artifact_virtual_paths"]
    )
    assert mesh_study["verification_status"] == "passed"


def test_scientific_verification_prefers_blocked_structured_stability_evidence(tmp_path):
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-stability-evidence-blocked"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "stability-blocked"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "latest_force_coefficients": {"Time": 200.0, "Cd": 0.00312},
                "force_coefficients_history": [
                    {"Time": 160.0, "Cd": 0.00312},
                    {"Time": 170.0, "Cd": 0.00312},
                    {"Time": 180.0, "Cd": 0.00312},
                    {"Time": 190.0, "Cd": 0.00312},
                    {"Time": 200.0, "Cd": 0.00312},
                ],
                "mesh_summary": {"mesh_ok": True},
                "residual_summary": {"max_final_residual": 5e-4},
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "end_time_seconds": 200.0,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "stability-evidence.json").write_text(
        json.dumps(
            {
                "status": "blocked",
                "summary_zh": "SCI-01 基线稳定性检查未通过。",
                "source_solver_results_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/stability-blocked/solver-results.json",
                "artifact_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/stability-blocked/stability-evidence.json",
                "requirements": [
                    {
                        "requirement_id": "final_residual_threshold",
                        "label": "Final residual threshold",
                        "check_type": "max_final_residual",
                        "status": "blocked",
                        "detail": "Final residual threshold: observed 0.004000 exceeds limit 0.001000.",
                        "observed_value": 0.004,
                        "limit_value": 0.001,
                    },
                    {
                        "requirement_id": "force_coefficient_tail_stability",
                        "label": "Force coefficient tail stability",
                        "check_type": "force_coefficient_tail_stability",
                        "status": "passed",
                        "detail": "Force coefficient tail stability: tail relative spread 0.0000 <= 0.0200 for Cd.",
                        "force_coefficient": "Cd",
                        "observed_sample_count": 5,
                        "required_sample_count": 5,
                        "relative_spread": 0.0,
                        "max_tail_relative_spread": 0.02,
                    },
                ],
                "blocking_issues": [
                    "Final residual threshold: observed 0.004000 exceeds limit 0.001000.",
                ],
                "missing_evidence": [],
                "passed_requirements": [
                    "Force coefficient tail stability: tail relative spread 0.0000 <= 0.0200 for Cd.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Prefer structured stability evidence",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/stability-blocked/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/stability-blocked/solver-results.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/stability-blocked/stability-evidence.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Structured stability evidence blocked report",
        tool_call_id="tc-result-report-stability-blocked",
    )

    final_report_path = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.json"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    assessment = final_payload["scientific_verification_assessment"]
    residual_requirement = next(
        item
        for item in assessment["requirements"]
        if item["requirement_id"] == "final_residual_threshold"
    )

    assert assessment["status"] == "blocked"
    assert residual_requirement["status"] == "blocked"
    assert "0.004000 exceeds limit 0.001000" in residual_requirement["detail"]
    assert final_payload["stability_evidence"]["status"] == "blocked"
    assert result.update["submarine_runtime"]["scientific_verification_assessment"]["status"] == "blocked"


def test_scientific_verification_surfaces_missing_structured_stability_evidence(tmp_path):
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-stability-evidence-missing"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "stability-missing"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "latest_force_coefficients": {"Time": 200.0, "Cd": 0.00312},
                "force_coefficients_history": [
                    {"Time": 160.0, "Cd": 0.00312},
                    {"Time": 170.0, "Cd": 0.00312},
                    {"Time": 180.0, "Cd": 0.00312},
                    {"Time": 190.0, "Cd": 0.00312},
                    {"Time": 200.0, "Cd": 0.00312},
                ],
                "mesh_summary": {"mesh_ok": True},
                "residual_summary": {"max_final_residual": 5e-4},
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "end_time_seconds": 200.0,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "stability-evidence.json").write_text(
        json.dumps(
            {
                "status": "missing_evidence",
                "summary_zh": "SCI-01 基线稳定性证据仍不完整。",
                "source_solver_results_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/stability-missing/solver-results.json",
                "artifact_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/stability-missing/stability-evidence.json",
                "requirements": [
                    {
                        "requirement_id": "final_residual_threshold",
                        "label": "Final residual threshold",
                        "check_type": "max_final_residual",
                        "status": "passed",
                        "detail": "Final residual threshold: observed 0.000500 <= 0.001000.",
                        "observed_value": 0.0005,
                        "limit_value": 0.001,
                    },
                    {
                        "requirement_id": "force_coefficient_tail_stability",
                        "label": "Force coefficient tail stability",
                        "check_type": "force_coefficient_tail_stability",
                        "status": "missing_evidence",
                        "detail": "Force coefficient tail stability: need at least 5 Cd samples in force coefficient history.",
                        "force_coefficient": "Cd",
                        "observed_sample_count": 2,
                        "required_sample_count": 5,
                        "relative_spread": None,
                        "max_tail_relative_spread": 0.02,
                    },
                ],
                "blocking_issues": [],
                "missing_evidence": [
                    "Force coefficient tail stability: need at least 5 Cd samples in force coefficient history.",
                ],
                "passed_requirements": [
                    "Final residual threshold: observed 0.000500 <= 0.001000.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    for suffix, study_type in [
        ("verification-mesh-independence.json", "mesh_independence"),
        ("verification-domain-sensitivity.json", "domain_sensitivity"),
        ("verification-time-step-sensitivity.json", "time_step_sensitivity"),
    ]:
        (solver_results_dir / suffix).write_text(
            json.dumps(
                {
                    "study_type": study_type,
                    "status": "passed",
                    "summary_zh": f"{study_type} evidence passed.",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Surface missing SCI-01 evidence from structured artifact",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/stability-missing/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/stability-missing/solver-results.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/stability-missing/stability-evidence.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/stability-missing/verification-mesh-independence.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/stability-missing/verification-domain-sensitivity.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/stability-missing/verification-time-step-sensitivity.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Structured stability evidence missing report",
        tool_call_id="tc-result-report-stability-missing",
    )

    final_report_path = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.json"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    assessment = final_payload["scientific_verification_assessment"]
    force_requirement = next(
        item
        for item in assessment["requirements"]
        if item["requirement_id"] == "force_coefficient_tail_stability"
    )

    assert assessment["status"] == "needs_more_verification"
    assert force_requirement["status"] == "missing_evidence"
    assert "need at least 5 Cd samples" in force_requirement["detail"]
    assert any(
        "need at least 5 Cd samples" in item for item in assessment["missing_evidence"]
    )
    assert final_payload["research_evidence_summary"]["verification_status"] == "needs_more_verification"


def test_scientific_verification_keeps_unreadable_study_artifact_as_missing_evidence(tmp_path):
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-scientific-verification-bad-artifact"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "verification-bad"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "latest_force_coefficients": {"Time": 200.0, "Cd": 0.00312},
                "force_coefficients_history": [
                    {"Time": 160.0, "Cd": 0.00313},
                    {"Time": 170.0, "Cd": 0.00312},
                    {"Time": 180.0, "Cd": 0.00311},
                    {"Time": 190.0, "Cd": 0.00312},
                    {"Time": 200.0, "Cd": 0.00312},
                ],
                "mesh_summary": {"mesh_ok": True},
                "residual_summary": {"max_final_residual": 5e-4},
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "end_time_seconds": 200.0,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "verification-mesh-independence.json").write_text(
        "{not valid json",
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Evaluate unreadable scientific verification evidence artifact",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/verification-bad/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verification-bad/solver-results.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verification-bad/verification-mesh-independence.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Scientific verification unreadable artifact report",
        tool_call_id="tc-result-report-scientific-bad-artifact",
    )

    final_report_virtual_path = next(
        path for path in result.update["artifacts"] if path.endswith("/final-report.json")
    )
    final_report_path = outputs_dir.joinpath(
        *[
            part
            for part in final_report_virtual_path.removeprefix("/mnt/user-data/outputs/").split("/")
            if part
        ]
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    requirements = final_payload["scientific_verification_assessment"]["requirements"]
    mesh_requirement = next(
        item for item in requirements if item["requirement_id"] == "mesh_independence_study"
    )

    assert mesh_requirement["status"] == "missing_evidence"
    assert "missing" in mesh_requirement["detail"].lower() or "unsupported" in mesh_requirement["detail"].lower()


def test_submarine_result_report_adds_experiment_summary(tmp_path):
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-experiment-summary"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = (
        outputs_dir / "submarine" / "solver-dispatch" / "experiment-summary"
    )
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "mesh_summary": {"mesh_ok": True, "cells": 9342},
                "latest_force_coefficients": {"Cd": 0.12},
                "latest_forces": {"total_force": [8.0, 0.0, 0.0]},
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 0.00014,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "run-record.json").write_text(
        json.dumps(
            {
                "run_id": "baseline",
                "experiment_id": "darpa-suboff-bare-hull-resistance-experiment-summary-resistance",
                "run_role": "baseline",
                "solver_results_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/solver-results.json",
                "run_record_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/run-record.json",
                "execution_status": "completed",
                "metric_snapshot": {
                    "Cd": 0.12,
                    "Fx": 8.0,
                    "final_time_seconds": 200.0,
                    "mesh_cells": 9342,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    variant_dir = (
        solver_results_dir
        / "studies"
        / "mesh-independence"
        / "coarse"
    )
    variant_dir.mkdir(parents=True, exist_ok=True)
    (variant_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "mesh_summary": {"mesh_ok": True, "cells": 8120},
                "latest_force_coefficients": {"Cd": 0.1212},
                "latest_forces": {"total_force": [8.2, 0.0, 0.0]},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (variant_dir / "run-record.json").write_text(
        json.dumps(
            {
                "run_id": "mesh_independence:coarse",
                "experiment_id": "darpa-suboff-bare-hull-resistance-experiment-summary-resistance",
                "run_role": "scientific_study_variant",
                "study_type": "mesh_independence",
                "variant_id": "coarse",
                "solver_results_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/studies/mesh-independence/coarse/solver-results.json",
                "run_record_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/studies/mesh-independence/coarse/run-record.json",
                "execution_status": "completed",
                "metric_snapshot": {
                    "Cd": 0.1212,
                    "Fx": 8.2,
                    "final_time_seconds": 200.0,
                    "mesh_cells": 8120,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "experiment-manifest.json").write_text(
        json.dumps(
            {
                "experiment_id": "darpa-suboff-bare-hull-resistance-experiment-summary-resistance",
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "task_type": "resistance",
                "baseline_run_id": "baseline",
                "run_records": [
                    {
                        "run_id": "baseline",
                        "run_role": "baseline",
                        "solver_results_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/solver-results.json",
                        "run_record_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/run-record.json",
                        "execution_status": "completed",
                    },
                    {
                        "run_id": "mesh_independence:coarse",
                        "run_role": "scientific_study_variant",
                        "study_type": "mesh_independence",
                        "variant_id": "coarse",
                        "solver_results_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/studies/mesh-independence/coarse/solver-results.json",
                        "run_record_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/studies/mesh-independence/coarse/run-record.json",
                        "execution_status": "completed",
                    },
                ],
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/experiment-manifest.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/run-compare-summary.json",
                ],
                "experiment_status": "completed",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "run-compare-summary.json").write_text(
        json.dumps(
            {
                "experiment_id": "darpa-suboff-bare-hull-resistance-experiment-summary-resistance",
                "baseline_run_id": "baseline",
                "comparisons": [
                    {
                        "baseline_run_id": "baseline",
                        "candidate_run_id": "mesh_independence:coarse",
                        "study_type": "mesh_independence",
                        "variant_id": "coarse",
                        "compare_status": "completed",
                        "metric_deltas": {
                            "Cd": {
                                "baseline_value": 0.12,
                                "candidate_value": 0.1212,
                                "absolute_delta": 0.0012,
                                "relative_delta": 0.01,
                            }
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Summarize experiment registry artifacts",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/solver-results.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/experiment-manifest.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/experiment-summary/run-compare-summary.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Experiment summary report",
        tool_call_id="tc-result-report-experiment-summary",
    )

    final_report_virtual_path = next(
        path for path in result.update["artifacts"] if path.endswith("/final-report.json")
    )
    final_report_path = outputs_dir.joinpath(
        *[
            part
            for part in final_report_virtual_path.removeprefix("/mnt/user-data/outputs/").split("/")
            if part
        ]
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    final_markdown = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.md"
    ).read_text(encoding="utf-8")
    final_html = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.html"
    ).read_text(encoding="utf-8")
    experiment_summary = final_payload["experiment_summary"]
    experiment_compare = final_payload["experiment_compare_summary"]

    assert experiment_summary["experiment_id"] == (
        "darpa-suboff-bare-hull-resistance-experiment-summary-resistance"
    )
    assert experiment_summary["baseline_run_id"] == "baseline"
    assert experiment_summary["run_count"] == 2
    assert experiment_summary["compare_virtual_path"].endswith("/run-compare-summary.json")
    assert experiment_compare["compare_count"] == 1
    assert experiment_compare["baseline_run_id"] == "baseline"
    assert experiment_compare["compare_virtual_path"].endswith("/run-compare-summary.json")
    comparison = experiment_compare["comparisons"][0]
    assert comparison["candidate_run_id"] == "mesh_independence:coarse"
    assert comparison["study_type"] == "mesh_independence"
    assert comparison["variant_id"] == "coarse"
    assert comparison["compare_status"] == "completed"
    assert comparison["baseline_solver_results_virtual_path"].endswith("/solver-results.json")
    assert comparison["candidate_solver_results_virtual_path"].endswith(
        "/studies/mesh-independence/coarse/solver-results.json"
    )
    assert comparison["baseline_run_record_virtual_path"].endswith("/run-record.json")
    assert comparison["candidate_run_record_virtual_path"].endswith(
        "/studies/mesh-independence/coarse/run-record.json"
    )
    assert comparison["metric_deltas"]["Cd"]["relative_delta"] == 0.01
    assert "## 证据索引" in final_markdown
    assert "<h2>证据索引</h2>" in final_html


def test_submarine_result_report_marks_verified_but_not_validated_without_benchmark_reference(
    tmp_path, monkeypatch
):
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )
    reporting_module = importlib.import_module("deerflow.domain.submarine.reporting")
    models_module = importlib.import_module("deerflow.domain.submarine.models")

    fake_case = models_module.SubmarineCase(
        case_id="research_evidence_custom_case",
        title="Research evidence custom case",
        geometry_family="DARPA SUBOFF",
        geometry_description="Custom benchmark-free verification case",
        task_type="resistance",
        acceptance_profile=models_module.SubmarineCaseAcceptanceProfile(
            profile_id="research-evidence-no-benchmark",
            summary_zh="Verification-focused case without external benchmark targets",
            max_final_residual=0.001,
            require_force_coefficients=True,
            benchmark_targets=[],
        ),
    )
    monkeypatch.setattr(reporting_module, "_resolve_selected_case", lambda _: fake_case)

    paths = Paths(tmp_path)
    thread_id = "thread-verified-not-validated"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = (
        outputs_dir / "submarine" / "solver-dispatch" / "verified-not-validated"
    )
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "mesh_summary": {"mesh_ok": True, "cells": 9342},
                "latest_force_coefficients": {"Time": 200.0, "Cd": 0.00312},
                "force_coefficients_history": [
                    {"Time": 160.0, "Cd": 0.00313},
                    {"Time": 170.0, "Cd": 0.00312},
                    {"Time": 180.0, "Cd": 0.00311},
                    {"Time": 190.0, "Cd": 0.00312},
                    {"Time": 200.0, "Cd": 0.00312},
                ],
                "latest_forces": {"total_force": [8.0, 0.0, 0.0]},
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 5e-4,
                },
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "fluid_density_kg_m3": 1000.0,
                    "kinematic_viscosity_m2ps": 1.0e-06,
                    "end_time_seconds": 200.0,
                    "delta_t_seconds": 1.0,
                    "write_interval_steps": 50,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    for artifact_name, study_type in [
        ("verification-mesh-independence.json", "mesh_independence"),
        ("verification-domain-sensitivity.json", "domain_sensitivity"),
        ("verification-time-step-sensitivity.json", "time_step_sensitivity"),
    ]:
        (solver_results_dir / artifact_name).write_text(
            json.dumps(
                {
                    "study_type": study_type,
                    "status": "passed",
                    "summary_zh": f"{study_type} evidence passed.",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    (solver_results_dir / "study-manifest.json").write_text(
        json.dumps(
            {
                "selected_case_id": "research_evidence_custom_case",
                "baseline_configuration_snapshot": {"task_type": "resistance"},
                "study_definitions": [],
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verified-not-validated/study-manifest.json"
                ],
                "study_execution_status": "completed",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "experiment-manifest.json").write_text(
        json.dumps(
            {
                "experiment_id": "research-evidence-custom-case-verified-not-validated-resistance",
                "selected_case_id": "research_evidence_custom_case",
                "task_type": "resistance",
                "baseline_run_id": "baseline",
                "run_records": [
                    {
                        "run_id": "baseline",
                        "run_role": "baseline",
                        "execution_status": "completed",
                    }
                ],
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verified-not-validated/experiment-manifest.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verified-not-validated/run-compare-summary.json",
                ],
                "experiment_status": "completed",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "run-compare-summary.json").write_text(
        json.dumps(
            {
                "experiment_id": "research-evidence-custom-case-verified-not-validated-resistance",
                "baseline_run_id": "baseline",
                "comparisons": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Assess research evidence without external validation target",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "selected_case_id": "research_evidence_custom_case",
                "stage_status": "executed",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/verified-not-validated/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verified-not-validated/solver-results.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verified-not-validated/study-manifest.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verified-not-validated/experiment-manifest.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verified-not-validated/run-compare-summary.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verified-not-validated/verification-mesh-independence.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verified-not-validated/verification-domain-sensitivity.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verified-not-validated/verification-time-step-sensitivity.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Verified but not validated report",
        tool_call_id="tc-result-report-verified-not-validated",
    )

    final_report_path = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.json"
    )
    final_markdown = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.md"
    ).read_text(encoding="utf-8")
    final_html = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.html"
    ).read_text(encoding="utf-8")
    handoff_path = (
        outputs_dir
        / "submarine"
        / "reports"
        / "suboff_solid"
        / "scientific-remediation-handoff.json"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    research = final_payload["research_evidence_summary"]
    gate = final_payload["scientific_supervisor_gate"]
    remediation = final_payload["scientific_remediation_summary"]
    handoff = final_payload["scientific_remediation_handoff"]

    assert research["verification_status"] == "passed"
    assert research["validation_status"] == "missing_validation_reference"
    assert research["readiness_status"] == "verified_but_not_validated"
    assert gate["gate_status"] == "claim_limited"
    assert gate["allowed_claim_level"] == "verified_but_not_validated"
    assert gate["recommended_stage"] == "supervisor-review"
    assert gate["remediation_stage"] == "solver-dispatch"
    assert final_payload["decision_status"] == "needs_more_evidence"
    assert (
        final_payload["delivery_decision_summary"]["decision_status"]
        == "needs_more_evidence"
    )
    assert (
        final_payload["delivery_decision_summary"]["recommended_option_id"]
        == "add_evidence"
    )
    assert [item["option_id"] for item in final_payload["delivery_decision_summary"]["options"]] == [
        "add_evidence",
        "finish_task",
        "extend_study",
    ]
    assert remediation["plan_status"] == "recommended"
    assert remediation["current_claim_level"] == "verified_but_not_validated"
    assert remediation["target_claim_level"] == "research_ready"
    assert remediation["recommended_stage"] == "supervisor-review"
    assert remediation["artifact_virtual_paths"][0].endswith(
        "/scientific-remediation-plan.json"
    )
    assert remediation["actions"][0]["action_id"] == "attach-validation-reference"
    assert remediation["actions"][0]["owner_stage"] == "supervisor-review"
    assert remediation["actions"][0]["execution_mode"] == "manual_required"
    assert handoff["handoff_status"] == "manual_followup_required"
    assert handoff["tool_name"] is None
    assert handoff["artifact_virtual_paths"][0].endswith(
        "/scientific-remediation-handoff.json"
    )
    assert handoff["manual_actions"][0]["action_id"] == "attach-validation-reference"
    assert final_payload["review_status"] == "ready_for_supervisor"
    assert final_payload["next_recommended_stage"] == "supervisor-review"
    assert final_payload["supervisor_handoff_virtual_path"].endswith(
        "/scientific-remediation-handoff.json"
    )
    assert handoff_path.exists()
    handoff_payload = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert handoff_payload["handoff_status"] == "manual_followup_required"
    assert "## 建议下一步" in final_markdown
    assert final_payload["report_overview"]["recommended_next_step_zh"] in final_markdown
    assert "<h2>建议下一步</h2>" in final_html
    assert final_payload["report_overview"]["recommended_next_step_zh"] in final_html
    assert result.update["submarine_runtime"]["supervisor_handoff_virtual_path"].endswith(
        "/scientific-remediation-handoff.json"
    )
    assert result.update["submarine_runtime"]["decision_status"] == "needs_more_evidence"


def test_submarine_result_report_marks_research_ready_with_validation_and_traceable_evidence(
    tmp_path, monkeypatch
):
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )
    reporting_module = importlib.import_module("deerflow.domain.submarine.reporting")
    models_module = importlib.import_module("deerflow.domain.submarine.models")

    fake_case = models_module.SubmarineCase(
        case_id="research_evidence_validated_case",
        title="Research evidence validated case",
        geometry_family="DARPA SUBOFF",
        geometry_description="Validation-backed research case",
        task_type="resistance",
        acceptance_profile=models_module.SubmarineCaseAcceptanceProfile(
            profile_id="research-evidence-validated",
            summary_zh="Validation-backed case",
            max_final_residual=0.001,
            require_force_coefficients=True,
            benchmark_targets=[
                models_module.SubmarineBenchmarkTarget(
                    metric_id="cd_at_3_05_mps",
                    quantity="Cd",
                    summary_zh="Compare Cd against reference",
                    reference_value=0.00314,
                    relative_tolerance=0.02,
                    inlet_velocity_mps=3.05,
                )
            ],
        ),
    )
    monkeypatch.setattr(reporting_module, "_resolve_selected_case", lambda _: fake_case)

    paths = Paths(tmp_path)
    thread_id = "thread-research-ready"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "research-ready"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "mesh_summary": {"mesh_ok": True, "cells": 9342},
                "latest_force_coefficients": {"Time": 200.0, "Cd": 0.00312},
                "force_coefficients_history": [
                    {"Time": 160.0, "Cd": 0.00313},
                    {"Time": 170.0, "Cd": 0.00312},
                    {"Time": 180.0, "Cd": 0.00311},
                    {"Time": 190.0, "Cd": 0.00312},
                    {"Time": 200.0, "Cd": 0.00312},
                ],
                "latest_forces": {"total_force": [8.0, 0.0, 0.0]},
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 5e-4,
                },
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "fluid_density_kg_m3": 1000.0,
                    "kinematic_viscosity_m2ps": 1.0e-06,
                    "end_time_seconds": 200.0,
                    "delta_t_seconds": 1.0,
                    "write_interval_steps": 50,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    for artifact_name, study_type in [
        ("verification-mesh-independence.json", "mesh_independence"),
        ("verification-domain-sensitivity.json", "domain_sensitivity"),
        ("verification-time-step-sensitivity.json", "time_step_sensitivity"),
    ]:
        (solver_results_dir / artifact_name).write_text(
            json.dumps(
                {
                    "study_type": study_type,
                    "status": "passed",
                    "summary_zh": f"{study_type} evidence passed.",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    (solver_results_dir / "study-manifest.json").write_text(
        json.dumps(
            {
                "selected_case_id": "research_evidence_validated_case",
                "baseline_configuration_snapshot": {"task_type": "resistance"},
                "study_definitions": [
                    {
                        "study_type": "mesh_independence",
                        "summary_label": "Mesh Independence",
                        "monitored_quantity": "Cd",
                        "pass_fail_tolerance": 0.02,
                        "variants": [
                            {
                                "study_type": "mesh_independence",
                                "variant_id": "coarse",
                                "variant_label": "Coarse",
                                "rationale": "Coarse mesh validation run.",
                            }
                        ],
                    }
                ],
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/study-manifest.json"
                ],
                "study_execution_status": "completed",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "experiment-manifest.json").write_text(
        json.dumps(
            {
                "experiment_id": "research-evidence-validated-case-research-ready-resistance",
                "selected_case_id": "research_evidence_validated_case",
                "task_type": "resistance",
                "baseline_run_id": "baseline",
                "run_records": [
                    {
                        "run_id": "baseline",
                        "run_role": "baseline",
                        "execution_status": "completed",
                    },
                    {
                        "run_id": "mesh_independence:coarse",
                        "run_role": "scientific_study_variant",
                        "study_type": "mesh_independence",
                        "variant_id": "coarse",
                        "execution_status": "completed",
                    },
                ],
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/experiment-manifest.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/run-compare-summary.json",
                ],
                "experiment_status": "completed",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "run-compare-summary.json").write_text(
        json.dumps(
            {
                "experiment_id": "research-evidence-validated-case-research-ready-resistance",
                "baseline_run_id": "baseline",
                "comparisons": [
                    {
                        "baseline_run_id": "baseline",
                        "candidate_run_id": "mesh_independence:coarse",
                        "study_type": "mesh_independence",
                        "variant_id": "coarse",
                        "compare_status": "completed",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    provenance_manifest_virtual_path = (
        "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/provenance-manifest.json"
    )
    (solver_results_dir / "provenance-manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": "v1",
                "experiment_id": "research-evidence-validated-case-research-ready-resistance",
                "run_id": "baseline",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "selected_case_id": "research_evidence_validated_case",
                "requested_output_ids": ["drag_coefficient"],
                "simulation_requirements_snapshot": {
                    "inlet_velocity_mps": 3.05,
                    "fluid_density_kg_m3": 1000.0,
                    "kinematic_viscosity_m2ps": 1.0e-06,
                    "end_time_seconds": 200.0,
                    "delta_t_seconds": 1.0,
                    "write_interval_steps": 50,
                },
                "approval_snapshot": {
                    "confirmation_status": "confirmed",
                    "review_status": "ready_for_supervisor",
                    "next_recommended_stage": "result-reporting",
                },
                "artifact_entrypoints": {
                    "request": "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/openfoam-request.json",
                    "solver_results": "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/solver-results.json",
                    "study_manifest": "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/study-manifest.json",
                    "experiment_manifest": "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/experiment-manifest.json",
                    "run_record": "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/experiment-manifest.json",
                    "run_compare_summary": "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/run-compare-summary.json",
                    "dispatch_summary_markdown": "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/dispatch-summary.md",
                    "dispatch_summary_html": "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/dispatch-summary.html",
                },
                "environment_fingerprint": {
                    "profile_id": "research-ready-profile",
                    "runtime_origin": "unit-test",
                },
                "environment_parity_assessment": {
                    "profile_id": "research-ready-profile",
                    "profile_label": "Research Ready Profile",
                    "parity_status": "matched",
                    "drift_reasons": [],
                    "recovery_guidance": [],
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Assess research readiness with validation and provenance",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "selected_case_id": "research_evidence_validated_case",
                "stage_status": "executed",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/dispatch-summary.md",
                "provenance_manifest_virtual_path": provenance_manifest_virtual_path,
                "environment_fingerprint": {
                    "profile_id": "research-ready-profile",
                    "runtime_origin": "unit-test",
                },
                "environment_parity_assessment": {
                    "profile_id": "research-ready-profile",
                    "profile_label": "Research Ready Profile",
                    "parity_status": "matched",
                    "drift_reasons": [],
                    "recovery_guidance": [],
                },
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/solver-results.json",
                    provenance_manifest_virtual_path,
                    "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/study-manifest.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/experiment-manifest.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/run-compare-summary.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/verification-mesh-independence.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/verification-domain-sensitivity.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/research-ready/verification-time-step-sensitivity.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Research ready report",
        tool_call_id="tc-result-report-research-ready",
    )

    final_report_path = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.json"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    research = final_payload["research_evidence_summary"]
    gate = final_payload["scientific_supervisor_gate"]

    assert research["validation_status"] == "validated"
    assert research["provenance_status"] == "traceable"
    assert research["readiness_status"] == "research_ready"
    assert final_payload["reproducibility_summary"]["parity_status"] == "matched"
    assert final_payload["reproducibility_summary"]["reproducibility_status"] == (
        "matched"
    )
    assert final_payload["provenance_summary"]["manifest_virtual_path"] == (
        provenance_manifest_virtual_path
    )
    assert (
        final_payload["provenance_summary"]["manifest_completeness_status"] == "complete"
    )
    assert gate["gate_status"] == "ready_for_claim"
    assert gate["allowed_claim_level"] == "research_ready"
    assert gate["recommended_stage"] == "supervisor-review"
    assert gate["remediation_stage"] is None
    assert final_payload["decision_status"] == "ready_for_user_decision"
    assert (
        final_payload["delivery_decision_summary"]["recommended_option_id"]
        == "finish_task"
    )
    assert [item["option_id"] for item in final_payload["delivery_decision_summary"]["options"]] == [
        "finish_task",
        "extend_study",
    ]
    assert final_payload["review_status"] == "ready_for_supervisor"
    assert final_payload["next_recommended_stage"] == "supervisor-review"
    assert final_payload["scientific_gate_virtual_path"].endswith(
        "/supervisor-scientific-gate.json"
    )
    assert any(
        path.endswith("/research-evidence-summary.json")
        for path in final_payload["artifact_virtual_paths"]
    )
    assert any(
        path.endswith("/supervisor-scientific-gate.json")
        for path in final_payload["artifact_virtual_paths"]
    )
    assert result.update["submarine_runtime"]["decision_status"] == "ready_for_user_decision"
    assert (
        result.update["submarine_runtime"]["provenance_manifest_virtual_path"]
        == provenance_manifest_virtual_path
    )
    assert (
        result.update["submarine_runtime"]["provenance_summary"]["manifest_virtual_path"]
        == provenance_manifest_virtual_path
    )
    assert result.update["submarine_runtime"]["scientific_gate_status"] == "ready_for_claim"
    assert result.update["submarine_runtime"]["execution_plan"][-1]["status"] == "ready"


def test_research_evidence_summary_downgrades_when_provenance_manifest_is_missing():
    evidence_module = importlib.import_module("deerflow.domain.submarine.evidence")
    models_module = importlib.import_module("deerflow.domain.submarine.models")

    summary = evidence_module.build_research_evidence_summary(
        acceptance_profile=models_module.SubmarineCaseAcceptanceProfile(
            profile_id="research-evidence-partial",
            summary_zh="Provenance manifest missing",
            benchmark_targets=[
                models_module.SubmarineBenchmarkTarget(
                    metric_id="cd_at_3_05_mps",
                    quantity="Cd",
                    summary_zh="Compare Cd against reference",
                    reference_value=0.00314,
                    relative_tolerance=0.02,
                    inlet_velocity_mps=3.05,
                )
            ],
        ),
        acceptance_assessment={
            "benchmark_comparisons": [
                {
                    "metric_id": "cd_at_3_05_mps",
                    "quantity": "Cd",
                    "status": "passed",
                    "observed_value": 0.00312,
                    "reference_value": 0.00314,
                    "relative_error": 0.0064,
                    "relative_tolerance": 0.02,
                    "target_inlet_velocity_mps": 3.05,
                    "observed_inlet_velocity_mps": 3.05,
                }
            ]
        },
        scientific_verification_assessment={
            "status": "research_ready",
            "passed_requirements": ["mesh_independence_study"],
        },
        provenance_summary=None,
        scientific_study_summary={
            "manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
            "workflow_status": "completed",
            "study_execution_status": "completed",
        },
        experiment_summary={
            "manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
            "compare_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
            "linkage_status": "consistent",
            "workflow_status": "completed",
        },
        output_delivery_plan=[
            {
                "delivery_status": "delivered",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json"
                ],
            }
        ],
        artifact_virtual_paths=[
            "/mnt/user-data/outputs/submarine/reports/demo/final-report.json",
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
        ],
    )

    assert summary["validation_status"] == "validated"
    assert summary["provenance_status"] == "partial"
    assert summary["readiness_status"] == "validated_with_gaps"
    assert any(
        "Canonical provenance manifest is missing" in item
        for item in summary["evidence_gaps"]
    )


def test_research_evidence_summary_downgrades_when_environment_parity_drifts():
    evidence_module = importlib.import_module("deerflow.domain.submarine.evidence")
    models_module = importlib.import_module("deerflow.domain.submarine.models")

    summary = evidence_module.build_research_evidence_summary(
        acceptance_profile=models_module.SubmarineCaseAcceptanceProfile(
            profile_id="research-evidence-parity-drift",
            summary_zh="Parity drifted after a scientifically valid run",
            benchmark_targets=[
                models_module.SubmarineBenchmarkTarget(
                    metric_id="cd_at_3_05_mps",
                    quantity="Cd",
                    summary_zh="Compare Cd against reference",
                    reference_value=0.00314,
                    relative_tolerance=0.02,
                    inlet_velocity_mps=3.05,
                )
            ],
        ),
        acceptance_assessment={
            "benchmark_comparisons": [
                {
                    "metric_id": "cd_at_3_05_mps",
                    "quantity": "Cd",
                    "status": "passed",
                    "observed_value": 0.00312,
                    "reference_value": 0.00314,
                    "relative_error": 0.0064,
                    "relative_tolerance": 0.02,
                    "target_inlet_velocity_mps": 3.05,
                    "observed_inlet_velocity_mps": 3.05,
                }
            ]
        },
        scientific_verification_assessment={
            "status": "research_ready",
            "passed_requirements": ["mesh_independence_study"],
        },
        provenance_summary={
            "manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest.json",
            "manifest_completeness_status": "complete",
            "parity_status": "drifted_but_runnable",
            "drift_reasons": [
                "Host mount strategy `workspace_path` does not match `docker_compose_dev` expectations."
            ],
            "recovery_guidance": [
                "Align DEER_FLOW_RUNTIME_PROFILE with the actual runtime path before treating the run as reproducible."
            ],
        },
        scientific_study_summary={
            "manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
            "workflow_status": "completed",
            "study_execution_status": "completed",
        },
        experiment_summary={
            "manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
            "compare_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
            "linkage_status": "consistent",
            "workflow_status": "completed",
        },
        output_delivery_plan=[
            {
                "delivery_status": "delivered",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json"
                ],
            }
        ],
        artifact_virtual_paths=[
            "/mnt/user-data/outputs/submarine/reports/demo/final-report.json",
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
        ],
    )

    assert summary["verification_status"] == "passed"
    assert summary["validation_status"] == "validated"
    assert summary["provenance_status"] == "partial"
    assert summary["readiness_status"] == "validated_with_gaps"
    assert any(
        "Environment parity drifted" in item for item in summary["evidence_gaps"]
    )
    assert any(
        "Host mount strategy" in item for item in summary["evidence_gaps"]
    )


def test_submarine_result_report_marks_validation_failed_in_research_evidence_summary(
    tmp_path, monkeypatch
):
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )
    reporting_module = importlib.import_module("deerflow.domain.submarine.reporting")
    models_module = importlib.import_module("deerflow.domain.submarine.models")

    fake_case = models_module.SubmarineCase(
        case_id="research_evidence_failed_case",
        title="Research evidence failed case",
        geometry_family="DARPA SUBOFF",
        geometry_description="Validation failure case",
        task_type="resistance",
        acceptance_profile=models_module.SubmarineCaseAcceptanceProfile(
            profile_id="research-evidence-failed",
            summary_zh="Validation-failed case",
            max_final_residual=0.001,
            require_force_coefficients=True,
            benchmark_targets=[
                models_module.SubmarineBenchmarkTarget(
                    metric_id="cd_at_3_05_mps",
                    quantity="Cd",
                    summary_zh="Compare Cd against reference",
                    reference_value=0.00314,
                    relative_tolerance=0.02,
                    inlet_velocity_mps=3.05,
                )
            ],
        ),
    )
    monkeypatch.setattr(reporting_module, "_resolve_selected_case", lambda _: fake_case)

    paths = Paths(tmp_path)
    thread_id = "thread-validation-failed"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = (
        outputs_dir / "submarine" / "solver-dispatch" / "validation-failed"
    )
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "mesh_summary": {"mesh_ok": True, "cells": 9342},
                "latest_force_coefficients": {"Time": 200.0, "Cd": 0.00360},
                "force_coefficients_history": [
                    {"Time": 160.0, "Cd": 0.00358},
                    {"Time": 170.0, "Cd": 0.00360},
                    {"Time": 180.0, "Cd": 0.00359},
                    {"Time": 190.0, "Cd": 0.00360},
                    {"Time": 200.0, "Cd": 0.00360},
                ],
                "residual_summary": {
                    "field_count": 2,
                    "latest_time": 200.0,
                    "max_final_residual": 5e-4,
                },
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "fluid_density_kg_m3": 1000.0,
                    "kinematic_viscosity_m2ps": 1.0e-06,
                    "end_time_seconds": 200.0,
                    "delta_t_seconds": 1.0,
                    "write_interval_steps": 50,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    for artifact_name, study_type in [
        ("verification-mesh-independence.json", "mesh_independence"),
        ("verification-domain-sensitivity.json", "domain_sensitivity"),
        ("verification-time-step-sensitivity.json", "time_step_sensitivity"),
    ]:
        (solver_results_dir / artifact_name).write_text(
            json.dumps(
                {
                    "study_type": study_type,
                    "status": "passed",
                    "summary_zh": f"{study_type} evidence passed.",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Assess failed research validation",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "selected_case_id": "research_evidence_failed_case",
                "stage_status": "executed",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/validation-failed/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/validation-failed/solver-results.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/validation-failed/verification-mesh-independence.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/validation-failed/verification-domain-sensitivity.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/validation-failed/verification-time-step-sensitivity.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Validation failed report",
        tool_call_id="tc-result-report-validation-failed",
    )

    final_report_path = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.json"
    )
    markdown_report_path = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.md"
    )
    html_report_path = (
        outputs_dir / "submarine" / "reports" / "suboff_solid" / "final-report.html"
    )
    evidence_path = (
        outputs_dir
        / "submarine"
        / "reports"
        / "suboff_solid"
        / "research-evidence-summary.json"
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    markdown = markdown_report_path.read_text(encoding="utf-8")
    html = html_report_path.read_text(encoding="utf-8")
    research = final_payload["research_evidence_summary"]
    gate = final_payload["scientific_supervisor_gate"]

    assert research["validation_status"] == "validation_failed"
    assert research["readiness_status"] == "blocked"
    assert evidence_path.exists()
    assert gate["gate_status"] == "blocked"
    assert gate["allowed_claim_level"] == "delivery_only"
    assert gate["recommended_stage"] == "solver-dispatch"
    assert final_payload["review_status"] == "blocked"
    assert final_payload["next_recommended_stage"] == "solver-dispatch"
    assert final_payload["scientific_gate_virtual_path"].endswith(
        "/supervisor-scientific-gate.json"
    )
    assert "回到 `solver-dispatch` 补齐验证或整改项后，再刷新最终报告。" in markdown
    assert final_payload["report_overview"]["recommended_next_step_zh"] in html
    assert result.update["submarine_runtime"]["review_status"] == "blocked"
    assert result.update["submarine_runtime"]["scientific_gate_status"] == "blocked"
    assert result.update["submarine_runtime"]["execution_plan"][-1]["status"] == "blocked"


def test_submarine_result_report_surfaces_scientific_followup_summary(
    tmp_path, monkeypatch
):
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-followup-report-summary"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "followup-summary.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(geometry_tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    geometry_result = geometry_tool_module.submarine_geometry_check_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/followup-summary.stl",
        task_description="Generate a report with followup history context",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        tool_call_id="tc-geometry-followup-summary",
    )
    history_virtual_path = (
        "/mnt/user-data/outputs/submarine/reports/followup-summary/"
        "scientific-followup-history.json"
    )
    history_path = (
        outputs_dir
        / "submarine"
        / "reports"
        / "followup-summary"
        / "scientific-followup-history.json"
    )
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(
        json.dumps(
            {
                "history_version": "v1",
                "entry_count": 2,
                "latest_entry_id": "scientific-followup-0002",
                "artifact_virtual_paths": [history_virtual_path],
                "entries": [
                    {
                        "entry_id": "scientific-followup-0001",
                        "sequence_index": 1,
                        "source_handoff_virtual_path": "/mnt/user-data/outputs/submarine/reports/followup-summary/scientific-remediation-handoff.json",
                        "source_report_virtual_path": "/mnt/user-data/outputs/submarine/reports/followup-summary/final-report.md",
                        "handoff_status": "ready_for_auto_followup",
                        "recommended_action_id": "execute-scientific-studies",
                        "tool_name": "submarine_solver_dispatch",
                        "followup_kind": "parameter_correction",
                        "decision_summary_zh": "先修正设置，再决定是否重新运行。",
                        "source_conclusion_ids": ["current_conclusion"],
                        "source_evidence_gap_ids": ["invalid_setup"],
                        "outcome_status": "dispatch_failed",
                        "dispatch_stage_status": "failed",
                        "report_refreshed": False,
                        "result_report_virtual_path": None,
                        "result_provenance_manifest_virtual_path": None,
                        "result_supervisor_handoff_virtual_path": None,
                        "task_completion_status": "continued",
                        "artifact_virtual_paths": [history_virtual_path],
                        "notes": ["The solver dispatch failed in the previous attempt."],
                    },
                    {
                        "entry_id": "scientific-followup-0002",
                        "sequence_index": 2,
                        "source_handoff_virtual_path": "/mnt/user-data/outputs/submarine/reports/followup-summary/scientific-remediation-handoff.json",
                        "source_report_virtual_path": "/mnt/user-data/outputs/submarine/reports/followup-summary/final-report.md",
                        "handoff_status": "ready_for_auto_followup",
                        "recommended_action_id": "execute-scientific-studies",
                        "tool_name": "submarine_solver_dispatch",
                        "followup_kind": "evidence_supplement",
                        "decision_summary_zh": "补齐外部验证证据后刷新报告。",
                        "source_conclusion_ids": ["current_conclusion"],
                        "source_evidence_gap_ids": ["missing_validation_reference"],
                        "outcome_status": "dispatch_refreshed_report",
                        "dispatch_stage_status": "executed",
                        "report_refreshed": True,
                        "result_report_virtual_path": "/mnt/user-data/outputs/submarine/reports/followup-summary/final-report.md",
                        "result_provenance_manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/followup-summary/provenance-manifest.json",
                        "result_supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/reports/followup-summary/scientific-remediation-handoff.json",
                        "task_completion_status": "continued",
                        "artifact_virtual_paths": [
                            history_virtual_path,
                            "/mnt/user-data/outputs/submarine/reports/followup-summary/final-report.md",
                            "/mnt/user-data/outputs/submarine/solver-dispatch/followup-summary/provenance-manifest.json",
                        ],
                        "notes": [
                            "The scientific rerun completed and the report was refreshed."
                        ],
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime.state["artifacts"] = geometry_result.update["artifacts"]
    runtime.state["submarine_runtime"] = geometry_result.update["submarine_runtime"]
    runtime.state["submarine_runtime"]["scientific_followup_history_virtual_path"] = (
        history_virtual_path
    )
    runtime.state["submarine_runtime"]["artifact_virtual_paths"] = [
        *runtime.state["submarine_runtime"]["artifact_virtual_paths"],
        history_virtual_path,
    ]

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Followup history report",
        tool_call_id="tc-result-report-followup-summary",
    )

    final_report_path = (
        outputs_dir / "submarine" / "reports" / "followup-summary" / "final-report.json"
    )
    final_markdown = (
        outputs_dir / "submarine" / "reports" / "followup-summary" / "final-report.md"
    ).read_text(encoding="utf-8")
    final_html = (
        outputs_dir / "submarine" / "reports" / "followup-summary" / "final-report.html"
    ).read_text(encoding="utf-8")
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    followup_summary = final_payload["scientific_followup_summary"]

    assert followup_summary["entry_count"] == 2
    assert followup_summary["latest_outcome_status"] == "dispatch_refreshed_report"
    assert followup_summary["latest_tool_name"] == "submarine_solver_dispatch"
    assert followup_summary["latest_recommended_action_id"] == "execute-scientific-studies"
    assert followup_summary["latest_followup_kind"] == "evidence_supplement"
    assert followup_summary["latest_decision_summary_zh"] == "补齐外部验证证据后刷新报告。"
    assert followup_summary["latest_source_conclusion_ids"] == ["current_conclusion"]
    assert followup_summary["latest_source_evidence_gap_ids"] == [
        "missing_validation_reference"
    ]
    assert followup_summary["report_refreshed"] is True
    assert followup_summary["history_virtual_path"] == history_virtual_path
    assert (
        followup_summary["latest_result_provenance_manifest_virtual_path"]
        == "/mnt/user-data/outputs/submarine/solver-dispatch/followup-summary/provenance-manifest.json"
    )
    assert (
        result.update["submarine_runtime"]["scientific_followup_history_virtual_path"]
        == history_virtual_path
    )
    assert any(
        item["group_id"] == "followup_and_refresh"
        for item in final_payload["evidence_index"]
    )
    assert "## 建议下一步" in final_markdown
    assert history_virtual_path in final_markdown
    assert "<h2>建议下一步</h2>" in final_html
    assert history_virtual_path in final_html


def test_scientific_verification_blocks_when_study_artifact_reports_failure(tmp_path):
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-scientific-verification-failed-artifact"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / "verification-fail"
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    (solver_results_dir / "solver-results.json").write_text(
        json.dumps(
            {
                "solver_completed": True,
                "final_time_seconds": 200.0,
                "latest_force_coefficients": {"Time": 200.0, "Cd": 0.00312},
                "force_coefficients_history": [
                    {"Time": 160.0, "Cd": 0.00313},
                    {"Time": 170.0, "Cd": 0.00312},
                    {"Time": 180.0, "Cd": 0.00311},
                    {"Time": 190.0, "Cd": 0.00312},
                    {"Time": 200.0, "Cd": 0.00312},
                ],
                "mesh_summary": {"mesh_ok": True},
                "residual_summary": {"max_final_residual": 5e-4},
                "simulation_requirements": {
                    "inlet_velocity_mps": 3.05,
                    "end_time_seconds": 200.0,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (solver_results_dir / "verification-domain-sensitivity.json").write_text(
        json.dumps(
            {
                "study_type": "domain_sensitivity",
                "status": "failed",
                "summary_zh": "Outer-domain sweep shows Cd drift above accepted tolerance.",
                "monitored_quantity": "Cd",
                "variant_count": 3,
                "relative_spread": 0.061,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Evaluate failed scientific verification evidence artifact",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "selected_case_id": "darpa_suboff_bare_hull_resistance",
                "stage_status": "executed",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/verification-fail/dispatch-summary.md",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verification-fail/solver-results.json",
                    "/mnt/user-data/outputs/submarine/solver-dispatch/verification-fail/verification-domain-sensitivity.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    result = report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Scientific verification failed artifact report",
        tool_call_id="tc-result-report-scientific-failed-artifact",
    )

    final_report_virtual_path = next(
        path for path in result.update["artifacts"] if path.endswith("/final-report.json")
    )
    final_report_path = outputs_dir.joinpath(
        *[
            part
            for part in final_report_virtual_path.removeprefix("/mnt/user-data/outputs/").split("/")
            if part
        ]
    )
    final_payload = json.loads(final_report_path.read_text(encoding="utf-8"))
    assessment = final_payload["scientific_verification_assessment"]
    domain_requirement = next(
        item
        for item in assessment["requirements"]
        if item["requirement_id"] == "domain_sensitivity_study"
    )

    assert assessment["status"] == "blocked"
    assert domain_requirement["status"] == "blocked"
    assert "above accepted tolerance" in domain_requirement["detail"]


def test_reporting_decomposition_module_acceptance_keeps_benchmark_semantics():
    acceptance_module = importlib.import_module(
        "deerflow.domain.submarine.reporting_acceptance"
    )
    contracts_module = importlib.import_module("deerflow.domain.submarine.contracts")
    library_module = importlib.import_module("deerflow.domain.submarine.library")

    snapshot = contracts_module.SubmarineRuntimeSnapshot.model_validate(
        {
            "current_stage": "solver-dispatch",
            "task_summary": "Benchmark SUBOFF drag",
            "task_type": "resistance",
            "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
            "geometry_family": "DARPA SUBOFF",
            "execution_readiness": "stl_ready",
            "selected_case_id": "darpa_suboff_bare_hull_resistance",
            "stage_status": "executed",
            "review_status": "ready_for_supervisor",
            "next_recommended_stage": "result-reporting",
            "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/benchmark-blocked/dispatch-summary.md",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/solver-dispatch/benchmark-blocked/solver-results.json",
            ],
        }
    )
    selected_case = library_module.load_case_library().case_index[
        "darpa_suboff_bare_hull_resistance"
    ]
    acceptance = acceptance_module.build_acceptance_assessment(
        snapshot=snapshot,
        solver_metrics={
            "solver_completed": True,
            "final_time_seconds": 200.0,
            "latest_force_coefficients": {
                "Cd": 0.00420,
                "Cl": 0.0,
                "Cs": 0.0,
                "CmPitch": 0.0,
            },
            "mesh_summary": {"mesh_ok": True},
            "residual_summary": {
                "field_count": 2,
                "latest_time": 200.0,
                "max_final_residual": 1.4e-4,
            },
            "simulation_requirements": {
                "inlet_velocity_mps": 3.05,
                "end_time_seconds": 200.0,
            },
        },
        selected_case=selected_case,
        artifact_virtual_paths=snapshot.artifact_virtual_paths,
    )

    assert acceptance["status"] == "blocked"
    assert acceptance["benchmark_comparisons"]
    assert acceptance["benchmark_comparisons"][0]["metric_id"] == "cd_at_3_05_mps"
    assert acceptance["benchmark_comparisons"][0]["status"] == "blocked"
    assert any(
        gate["id"] == "benchmark_cd_at_3_05_mps" and gate["status"] == "blocked"
        for gate in acceptance["gates"]
    )


def test_reporting_decomposition_module_summaries_build_experiment_compare_summary(
    tmp_path,
):
    summaries_module = importlib.import_module(
        "deerflow.domain.submarine.reporting_summaries"
    )

    outputs_dir = tmp_path / "outputs"
    run_dir = outputs_dir / "submarine" / "solver-dispatch" / "compare-demo"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "experiment-manifest.json").write_text(
        json.dumps(
            {
                "experiment_id": "suboff-compare-demo",
                "baseline_run_id": "baseline",
                "run_records": [
                    {
                        "run_id": "baseline",
                        "solver_results_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/compare-demo/solver-results.json",
                        "run_record_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/compare-demo/run-record.json",
                    },
                    {
                        "run_id": "mesh_independence:coarse",
                        "solver_results_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/compare-demo/studies/mesh-independence/coarse/solver-results.json",
                        "run_record_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/compare-demo/studies/mesh-independence/coarse/run-record.json",
                    },
                ],
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/compare-demo/experiment-manifest.json",
                ],
                "experiment_status": "completed",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "run-compare-summary.json").write_text(
        json.dumps(
            {
                "experiment_id": "suboff-compare-demo",
                "baseline_run_id": "baseline",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/compare-demo/run-compare-summary.json",
                ],
                "comparisons": [
                    {
                        "candidate_run_id": "mesh_independence:coarse",
                        "study_type": "mesh_independence",
                        "variant_id": "coarse",
                        "compare_status": "completed",
                        "notes": "Relative Cd shift stayed within tolerance.",
                        "metric_deltas": {
                            "Cd": {
                                "baseline_value": 0.12,
                                "candidate_value": 0.1212,
                                "absolute_delta": 0.0012,
                                "relative_delta": 0.01,
                            }
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    experiment_summary = summaries_module.build_experiment_summary(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=[
            "/mnt/user-data/outputs/submarine/solver-dispatch/compare-demo/experiment-manifest.json",
            "/mnt/user-data/outputs/submarine/solver-dispatch/compare-demo/run-compare-summary.json",
        ],
    )
    experiment_compare_summary = summaries_module.build_experiment_compare_summary(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=[
            "/mnt/user-data/outputs/submarine/solver-dispatch/compare-demo/experiment-manifest.json",
            "/mnt/user-data/outputs/submarine/solver-dispatch/compare-demo/run-compare-summary.json",
        ],
    )

    assert experiment_summary["experiment_id"] == "suboff-compare-demo"
    assert experiment_summary["compare_count"] == 1
    assert experiment_compare_summary["baseline_run_id"] == "baseline"
    assert experiment_compare_summary["compare_count"] == 1
    assert (
        experiment_compare_summary["comparisons"][0]["candidate_run_id"]
        == "mesh_independence:coarse"
    )


def test_reporting_decomposition_module_render_uses_conclusion_first_sections():
    render_module = importlib.import_module("deerflow.domain.submarine.reporting_render")

    payload = {
        "report_title": "Decomposition Render Report",
        "summary_zh": "Report render regression fixture.",
        "report_overview": {
            "current_conclusion_zh": "当前结论支持交付说明，但还不能提升到研究级结论。",
            "allowed_claim_level": "validated_with_gaps",
            "review_status": "ready_for_supervisor",
            "reproducibility_status": "drifted_but_runnable",
            "recommended_next_step_zh": "优先补齐 benchmark 交叉验证，再决定是否提升 claim level。",
        },
        "delivery_highlights": {
            "metric_lines": [
                "阻力系数 Cd：0.120000",
                "最终时间步：200 s",
                "复核状态：ready_for_supervisor",
            ],
            "figure_titles": [
                "表面压力云图",
                "尾流速度切片",
            ],
            "highlight_artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/suboff/final-report.md",
                "/mnt/user-data/outputs/submarine/reports/suboff/final-report.html",
            ],
        },
        "conclusion_sections": [
            {
                "conclusion_id": "current_conclusion",
                "title_zh": "当前研究结论",
                "summary_zh": "当前结果已经形成可交付的阻力结论，但外部验证仍有缺口。",
                "claim_level": "validated_with_gaps",
                "confidence_label": "中",
                "inline_source_refs": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/suboff/dispatch-summary.md",
                    "/mnt/user-data/outputs/submarine/reports/suboff/supervisor-scientific-gate.json",
                ],
                "evidence_gap_notes": [
                    "缺少面向当前速度工况的 benchmark 交叉验证。",
                ],
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/reports/suboff/final-report.json",
                    "/mnt/user-data/outputs/submarine/reports/suboff/final-report.md",
                ],
            },
            {
                "conclusion_id": "reproducibility_traceability",
                "title_zh": "复现与追溯锚点",
                "summary_zh": "当前结果已绑定 provenance manifest，可追溯到求解与复核产物。",
                "claim_level": "validated_with_gaps",
                "confidence_label": "中",
                "inline_source_refs": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/suboff/provenance-manifest.json",
                ],
                "evidence_gap_notes": [
                    "运行环境仍存在 drifted_but_runnable 偏差。",
                ],
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/reports/suboff/scientific-remediation-handoff.json",
                ],
            },
        ],
        "evidence_index": [
            {
                "group_id": "research_evidence",
                "group_title_zh": "研究证据与科学判断",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/reports/suboff/research-evidence-summary.json",
                    "/mnt/user-data/outputs/submarine/reports/suboff/supervisor-scientific-gate.json",
                ],
                "provenance_manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/suboff/provenance-manifest.json",
            },
            {
                "group_id": "runtime_and_lineage",
                "group_title_zh": "运行产物与追溯锚点",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/suboff/dispatch-summary.md",
                    "/mnt/user-data/outputs/submarine/reports/suboff/scientific-remediation-handoff.json",
                ],
                "provenance_manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/suboff/provenance-manifest.json",
            },
        ],
        "scientific_followup_summary": {
            "history_virtual_path": "/mnt/user-data/outputs/submarine/reports/suboff/scientific-followup-history.json",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/reports/suboff/scientific-followup-history.json",
            ],
        },
        "next_recommended_stage": "supervisor-review",
        "source_report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/suboff/dispatch-summary.md",
        "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/reports/suboff/scientific-remediation-handoff.json",
    }

    markdown = render_module.render_markdown(payload)
    html = render_module.render_html(payload)

    markdown_headings = [
        "## 结论摘要",
        "## 关键指标与代表图表",
        "## 结论与证据",
        "## 证据索引",
        "## 建议下一步",
    ]
    html_headings = [
        "<h2>结论摘要</h2>",
        "<h2>关键指标与代表图表</h2>",
        "<h2>结论与证据</h2>",
        "<h2>证据索引</h2>",
        "<h2>建议下一步</h2>",
    ]

    assert [markdown.index(item) for item in markdown_headings] == sorted(
        markdown.index(item) for item in markdown_headings
    )
    assert [html.index(item) for item in html_headings] == sorted(
        html.index(item) for item in html_headings
    )
    assert "来源：" in markdown
    assert "Claim level：" in markdown
    assert "置信度：" in markdown
    assert "证据缺口：" in markdown
    assert "研究证据与科学判断" in markdown
    assert "provenance_manifest_virtual_path" in markdown
    assert "<strong>来源：</strong>" in html
    assert "<strong>Claim level：</strong>" in html
    assert "<strong>置信度：</strong>" in html
    assert "<strong>证据缺口：</strong>" in html
    assert "<strong>provenance_manifest_virtual_path：</strong>" in html


def test_result_reporting_includes_selected_case_provenance_summary(tmp_path):
    contracts_module = importlib.import_module("deerflow.domain.submarine.contracts")
    reporting_module = importlib.import_module("deerflow.domain.submarine.reporting")

    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    snapshot = contracts_module.SubmarineRuntimeSnapshot.model_validate(
        {
            "current_stage": "geometry-preflight",
            "task_summary": "Review the engineering Type 209 drag workflow assumptions.",
            "confirmation_status": "confirmed",
            "execution_preference": "preflight_then_execute",
            "task_type": "resistance",
            "geometry_virtual_path": "/mnt/user-data/uploads/type209-provenance.stl",
            "geometry_family": "Type 209",
            "selected_case_id": "type209_engineering_drag",
            "review_status": "needs_user_confirmation",
            "next_recommended_stage": "user-confirmation",
            "report_virtual_path": "/mnt/user-data/outputs/submarine/geometry-check/type209-provenance/geometry-check.md",
            "artifact_virtual_paths": [],
        }
    )

    payload, _ = reporting_module.run_result_report(
        snapshot=snapshot,
        outputs_dir=outputs_dir,
        report_title="Type 209 provenance report",
    )

    html_path = (
        outputs_dir / "submarine" / "reports" / "type209-provenance" / "final-report.html"
    )
    html = html_path.read_text(encoding="utf-8")
    provenance = payload["selected_case_provenance_summary"]

    assert provenance["case_id"] == "type209_engineering_drag"
    assert provenance["source_label"] == "Type 209 engineering placeholder"
    assert provenance["source_type"] == "placeholder_reference"
    assert provenance["is_placeholder"] is True
    assert provenance["applicability_conditions"]
    assert "engineering review" in provenance["evidence_gap_note"]
    assert "<h2>建议下一步</h2>" in html
    assert payload["report_overview"]["recommended_next_step_zh"] in html
