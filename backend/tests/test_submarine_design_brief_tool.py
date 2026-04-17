import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from langchain_core.messages import HumanMessage

from deerflow.config.paths import Paths

tool_module = importlib.import_module("deerflow.tools.builtins.submarine_design_brief_tool")
design_brief_module = importlib.import_module("deerflow.domain.submarine.design_brief")


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


def test_submarine_design_brief_tool_generates_deerflow_artifacts(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "brief-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_design_brief_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/brief-demo.stl",
        task_description="目标是完成潜艇裸艇阻力基线计算，并拿到可审阅的结果报告",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="draft",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        inlet_velocity_mps=7.5,
        fluid_density_kg_m3=998.2,
        kinematic_viscosity_m2ps=8.5e-07,
        end_time_seconds=600.0,
        delta_t_seconds=0.5,
        write_interval_steps=20,
        expected_outputs=["阻力系数 Cd", "阻力分解", "中文结果报告"],
        user_constraints=["先做单工况稳健基线，不做参数扫描"],
        open_questions=["是否需要额外对比 5 m/s 工况"],
        tool_call_id="tc-design-brief-1",
    )

    artifacts = result.update["artifacts"]
    assert any(path.endswith("/cfd-design-brief.json") for path in artifacts)
    assert any(path.endswith("/cfd-design-brief.md") for path in artifacts)
    assert any(path.endswith("/cfd-design-brief.html") for path in artifacts)

    json_path = outputs_dir / "submarine" / "design-brief" / "brief-demo" / "cfd-design-brief.json"
    md_path = outputs_dir / "submarine" / "design-brief" / "brief-demo" / "cfd-design-brief.md"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert payload["confirmation_status"] == "draft"
    assert payload["geometry_virtual_path"] == "/mnt/user-data/uploads/brief-demo.stl"
    assert payload["selected_case_id"] == "darpa_suboff_bare_hull_resistance"
    assert payload["simulation_requirements"]["end_time_seconds"] == 600.0
    assert payload["expected_outputs"] == ["阻力系数 Cd", "阻力分解", "中文结果报告"]
    assert payload["user_constraints"] == ["先做单工况稳健基线，不做参数扫描"]
    assert payload["open_questions"] == ["是否需要额外对比 5 m/s 工况"]
    assert payload["approval_state"] == "needs_confirmation"
    assert payload["goal_status"] == "planning"
    assert payload["stage_hints"]["current"] == "task-intelligence"
    assert payload["stage_hints"]["suggested_next"] == "user-confirmation"
    assert payload["execution_outline"][0]["role_id"] == "claude-code-supervisor"
    assert payload["execution_outline"][1]["role_id"] == "task-intelligence"
    assert payload["execution_outline"][0]["status"] == "in_progress"
    assert payload["execution_outline"][1]["status"] == "pending"
    assert payload["execution_outline"][2]["status"] == "pending"
    assert "计算要求" in markdown
    assert "待确认项" in markdown
    assert "执行分工" in markdown

    runtime_state = result.update["submarine_runtime"]
    assert runtime_state["current_stage"] == "task-intelligence"
    assert runtime_state["approval_state"] == "needs_confirmation"
    assert runtime_state["goal_status"] == "planning"
    assert runtime_state["stage_hints"]["suggested_next"] == "user-confirmation"
    assert runtime_state["report_virtual_path"].endswith("/cfd-design-brief.md")
    assert runtime_state["simulation_requirements"]["delta_t_seconds"] == 0.5
    assert runtime_state["execution_plan"][0]["status"] == "in_progress"
    assert runtime_state["execution_plan"][2]["status"] == "pending"
    assert runtime_state["review_status"] == "needs_user_confirmation"
    assert runtime_state["next_recommended_stage"] == "user-confirmation"
    assert len(runtime_state["activity_timeline"]) == 1
    assert runtime_state["activity_timeline"][0]["stage"] == "task-intelligence"
    assert runtime_state["activity_timeline"][0]["actor"] == "claude-code-supervisor"


def test_submarine_design_brief_tool_merges_existing_brief_context(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "merge-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    initial = tool_module.submarine_design_brief_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/merge-demo.stl",
        task_description="先完成基线阻力工况的方案讨论和设计简报",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="draft",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        inlet_velocity_mps=5.0,
        fluid_density_kg_m3=1000.0,
        expected_outputs=["阻力系数 Cd", "中文结果报告"],
        user_constraints=["先做单工况基线"],
        open_questions=["是否追加 7 m/s 对比工况"],
        tool_call_id="tc-design-brief-initial",
    )
    runtime.state["submarine_runtime"] = initial.update["submarine_runtime"]
    runtime.state["artifacts"] = initial.update["artifacts"]

    updated = tool_module.submarine_design_brief_tool.func(
        runtime=runtime,
        geometry_path=None,
        task_description=None,
        task_type=None,
        geometry_family_hint=None,
        confirmation_status="confirmed",
        selected_case_id=None,
        inlet_velocity_mps=None,
        fluid_density_kg_m3=None,
        expected_outputs=["阻力系数 Cd", "中文结果报告", "网格质量摘要"],
        user_constraints=None,
        open_questions=[],
        tool_call_id="tc-design-brief-update",
    )

    json_path = outputs_dir / "submarine" / "design-brief" / "merge-demo" / "cfd-design-brief.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = updated.update["submarine_runtime"]

    assert payload["task_description"] == "先完成基线阻力工况的方案讨论和设计简报"
    assert payload["task_type"] == "resistance"
    assert payload["geometry_virtual_path"] == "/mnt/user-data/uploads/merge-demo.stl"
    assert payload["geometry_family_hint"] == "DARPA SUBOFF"
    assert payload["selected_case_id"] == "darpa_suboff_bare_hull_resistance"
    assert payload["simulation_requirements"]["inlet_velocity_mps"] == 5.0
    assert payload["simulation_requirements"]["fluid_density_kg_m3"] == 1000.0
    assert payload["user_constraints"] == ["先做单工况基线"]
    assert payload["confirmation_status"] == "confirmed"
    assert payload["approval_state"] == "approved"
    assert payload["goal_status"] == "ready_for_execution"
    assert payload["stage_hints"]["current"] == "task-intelligence"
    assert payload["stage_hints"]["suggested_next"] == "geometry-preflight"
    assert payload["open_questions"] == []
    assert payload["expected_outputs"] == ["阻力系数 Cd", "中文结果报告", "网格质量摘要"]
    assert runtime_state["review_status"] == "ready_for_supervisor"
    assert runtime_state["approval_state"] == "approved"
    assert runtime_state["goal_status"] == "ready_for_execution"
    assert runtime_state["clarification_required"] is False
    assert runtime_state["requires_immediate_confirmation"] is False
    assert runtime_state["stage_hints"]["suggested_next"] == "geometry-preflight"
    assert runtime_state["next_recommended_stage"] == "geometry-preflight"
    assert len(runtime_state["activity_timeline"]) == 2
    assert runtime_state["activity_timeline"][-1]["status"] == "confirmed"
    assert payload["execution_outline"][0]["status"] == "completed"
    assert payload["execution_outline"][1]["status"] == "ready"
    assert payload["execution_outline"][2]["status"] == "ready"
    assert runtime_state["execution_plan"][0]["status"] == "completed"
    assert runtime_state["execution_plan"][1]["status"] == "ready"


def test_submarine_design_brief_preserves_existing_followup_handoff_state(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-preserve-followup"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "preserve-followup.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = {
        "current_stage": "result-reporting",
        "task_summary": "Continue the scientific CFD remediation flow",
        "confirmation_status": "confirmed",
        "approval_state": "approved",
        "goal_status": "ready_for_execution",
        "execution_preference": "execute_now",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/preserve-followup.stl",
        "geometry_family": "DARPA SUBOFF",
        "execution_readiness": "stl_ready",
        "selected_case_id": "darpa_suboff_bare_hull_resistance",
        "simulation_requirements": {
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
        },
        "stage_status": "blocked",
        "next_recommended_stage": "result-reporting",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/reports/preserve-followup/final-report.md",
        "artifact_virtual_paths": ["/mnt/user-data/outputs/submarine/reports/preserve-followup/final-report.json"],
        "provenance_manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/preserve-followup/provenance-manifest.json",
        "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/reports/preserve-followup/scientific-remediation-handoff.json",
        "scientific_gate_virtual_path": "/mnt/user-data/outputs/submarine/reports/preserve-followup/supervisor-scientific-gate.json",
        "review_status": "blocked",
        "execution_plan": [],
        "activity_timeline": [],
    }

    result = tool_module.submarine_design_brief_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/preserve-followup.stl",
        task_description=("请继续建议的修正流程：基于当前科学审查给出的 remediation handoff，复用现有几何、案例和已确认设置，立即重跑当前求解并补齐缺失的 solver metrics，然后刷新结果报告。整个过程请保持在当前线程中可追踪。"),
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="confirmed",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        tool_call_id="tc-design-brief-preserve-followup",
    )

    runtime_state = result.update["submarine_runtime"]

    assert runtime_state["current_stage"] == "task-intelligence"
    assert runtime_state["supervisor_handoff_virtual_path"] == "/mnt/user-data/outputs/submarine/reports/preserve-followup/scientific-remediation-handoff.json"
    assert runtime_state["scientific_gate_virtual_path"] == "/mnt/user-data/outputs/submarine/reports/preserve-followup/supervisor-scientific-gate.json"
    assert runtime_state["provenance_manifest_virtual_path"] == "/mnt/user-data/outputs/submarine/solver-dispatch/preserve-followup/provenance-manifest.json"


def test_submarine_design_brief_normalizes_requested_outputs(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-requested-outputs"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "requested-outputs.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_design_brief_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/requested-outputs.stl",
        task_description="希望按用户要求输出阻力系数、表面压力云图、流线图和中文报告",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="draft",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        expected_outputs=["阻力系数 Cd", "表面压力云图", "流线图", "中文结果报告"],
        tool_call_id="tc-design-brief-requested-outputs",
    )

    json_path = outputs_dir / "submarine" / "design-brief" / "requested-outputs" / "cfd-design-brief.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    requested_outputs = payload["requested_outputs"]
    runtime_state = result.update["submarine_runtime"]

    assert [item["output_id"] for item in requested_outputs] == [
        "drag_coefficient",
        "surface_pressure_contour",
        "streamlines",
        "chinese_report",
    ]
    assert requested_outputs[0]["support_level"] == "supported"
    assert requested_outputs[1]["support_level"] == "supported"
    assert requested_outputs[2]["support_level"] == "not_yet_supported"
    assert requested_outputs[3]["support_level"] == "supported"
    assert runtime_state["requested_outputs"] == requested_outputs


def test_submarine_design_brief_clears_geometry_preflight_confirmation_flags(
    tmp_path,
    monkeypatch,
):
    paths = Paths(tmp_path)
    thread_id = "thread-confirmed-preflight"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "confirmed-preflight.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = {
        "current_stage": "geometry-preflight",
        "approval_state": "needs_confirmation",
        "confirmation_status": "draft",
        "goal_status": "planning",
        "execution_preference": "plan_only",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/confirmed-preflight.stl",
        "geometry_family": "DARPA SUBOFF bare hull",
        "clarification_required": True,
        "requires_immediate_confirmation": True,
        "review_status": "needs_user_confirmation",
        "next_recommended_stage": "user-confirmation",
        "calculation_plan": [
            {
                "item_id": "geometry.reference_length_m",
                "category": "geometry",
                "label": "参考长度",
                "proposed_value": 4.356,
                "proposed_range": None,
                "unit": "m",
                "source_label": "geometry-preflight",
                "source_url": None,
                "confidence": "low",
                "applicability_conditions": [],
                "evidence_gap_note": "建议参考长度已生成，但当前尺度解释仍需研究者确认。",
                "origin": "ai_suggestion",
                "approval_state": "pending_researcher_confirmation",
                "requires_immediate_confirmation": True,
                "researcher_note": None,
            },
            {
                "item_id": "geometry.reference_area_m2",
                "category": "geometry",
                "label": "参考面积",
                "proposed_value": 0.370988,
                "proposed_range": None,
                "unit": "m^2",
                "source_label": "geometry-preflight",
                "source_url": None,
                "confidence": "low",
                "applicability_conditions": [],
                "evidence_gap_note": "建议参考面积已生成，但当前几何尺度仍需确认。",
                "origin": "ai_suggestion",
                "approval_state": "pending_researcher_confirmation",
                "requires_immediate_confirmation": True,
                "researcher_note": None,
            },
        ],
    }

    result = tool_module.submarine_design_brief_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/confirmed-preflight.stl",
        task_description="我确认参考长度取 4.356 m，参考面积取 0.370988 m^2。",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="confirmed",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        inlet_velocity_mps=5.0,
        tool_call_id="tc-design-brief-confirmed-preflight",
    )

    runtime_state = result.update["submarine_runtime"]

    assert runtime_state["approval_state"] == "approved"
    assert runtime_state["goal_status"] == "ready_for_execution"
    assert runtime_state["clarification_required"] is False
    assert runtime_state["requires_immediate_confirmation"] is False
    assert runtime_state["review_status"] == "ready_for_supervisor"
    assert runtime_state["next_recommended_stage"] != "user-confirmation"
    assert all(item["approval_state"] == "researcher_confirmed" for item in runtime_state["calculation_plan"])


def test_submarine_design_brief_assigns_default_postprocess_specs(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-postprocess-spec"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "postprocess-spec.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_design_brief_tool.func(
        runtime=_make_runtime(paths, thread_id),
        task_description="根据用户结果需求生成带后处理 spec 的设计简报",
        geometry_path="/mnt/user-data/uploads/postprocess-spec.stl",
        task_type="resistance",
        confirmation_status="draft",
        geometry_family_hint="DARPA SUBOFF",
        expected_outputs=["表面压力云图", "尾流速度切片"],
        tool_call_id="tc-brief-postprocess-spec",
    )

    json_path = outputs_dir / "submarine" / "design-brief" / "postprocess-spec" / "cfd-design-brief.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    requested_outputs = payload["requested_outputs"]
    runtime_state = result.update["submarine_runtime"]

    assert requested_outputs[0]["postprocess_spec"]["field"] == "p"
    assert requested_outputs[0]["postprocess_spec"]["selector"]["type"] == "patch"
    assert requested_outputs[0]["postprocess_spec"]["selector"]["patches"] == ["hull"]
    assert requested_outputs[1]["postprocess_spec"]["field"] == "U"
    assert requested_outputs[1]["postprocess_spec"]["selector"]["origin_mode"] == "x_by_lref"
    assert requested_outputs[1]["postprocess_spec"]["selector"]["origin_value"] == 1.25
    assert requested_outputs[1]["postprocess_spec"]["selector"]["normal"] == [1.0, 0.0, 0.0]
    assert runtime_state["requested_outputs"] == requested_outputs


def test_submarine_design_brief_recovers_geometry_from_uploaded_files_state(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-uploaded-files-brief"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "uploaded-files-brief.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["uploaded_files"] = [
        {
            "filename": "uploaded-files-brief.stl",
            "path": "/mnt/user-data/uploads/uploaded-files-brief.stl",
        }
    ]

    result = tool_module.submarine_design_brief_tool.func(
        runtime=runtime,
        geometry_path=None,
        task_description="请根据当前线程里已上传的 STL 生成第一版阻力 CFD brief。",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="draft",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        tool_call_id="tc-design-brief-uploaded-files",
    )

    json_path = outputs_dir / "submarine" / "design-brief" / "uploaded-files-brief" / "cfd-design-brief.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]

    assert payload["geometry_virtual_path"] == "/mnt/user-data/uploads/uploaded-files-brief.stl"
    assert runtime_state["geometry_virtual_path"] == "/mnt/user-data/uploads/uploaded-files-brief.stl"


def test_submarine_design_brief_includes_scientific_verification_requirements(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-verification-brief"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "verification-brief.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    tool_module.submarine_design_brief_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/verification-brief.stl",
        task_description="希望把这次 SUBOFF 计算组织成科研可复核的阻力基线 run。",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="confirmed",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        expected_outputs=["阻力系数 Cd", "表面压力云图", "中文结果报告"],
        tool_call_id="tc-design-brief-verification",
    )

    json_path = outputs_dir / "submarine" / "design-brief" / "verification-brief" / "cfd-design-brief.json"
    md_path = outputs_dir / "submarine" / "design-brief" / "verification-brief" / "cfd-design-brief.md"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert [item["requirement_id"] for item in payload["scientific_verification_requirements"]] == [
        "final_residual_threshold",
        "force_coefficient_tail_stability",
        "mesh_independence_study",
        "domain_sensitivity_study",
        "time_step_sensitivity_study",
    ]
    assert payload["scientific_verification_requirements"][1]["force_coefficient"] == "Cd"
    assert "科研验证要求" in markdown
    assert "mesh_independence_study" in markdown


def test_submarine_design_brief_captures_direct_execution_preference(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-execution-preference"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "execution-preference.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_design_brief_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/execution-preference.stl",
        task_description="直接发起 5 m/s 基线 CFD 计算，并尽力得到 Cd 与阻力结果。",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="confirmed",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        inlet_velocity_mps=5.0,
        fluid_density_kg_m3=1025.0,
        kinematic_viscosity_m2ps=1.05e-06,
        expected_outputs=["闃诲姏绯绘暟 Cd", "涓枃缁撴灉鎶ュ憡"],
        open_questions=[],
        tool_call_id="tc-design-brief-execution-preference",
    )

    json_path = outputs_dir / "submarine" / "design-brief" / "execution-preference" / "cfd-design-brief.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]

    assert payload["execution_preference"] == "execute_now"
    assert runtime_state["execution_preference"] == "execute_now"


def test_submarine_design_brief_caps_fallback_run_dir_name_on_long_task_description(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-long-run-basis"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    long_task_description = ("DARPA SUBOFF 5 mps CFD scientific verification submarine result acceptance visible preflight then execute ") * 3

    result = tool_module.submarine_design_brief_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path=None,
        task_description=long_task_description.strip(),
        task_type="resistance",
        confirmation_status="confirmed",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        tool_call_id="tc-design-brief-long-run-basis",
    )

    json_artifact = next(path for path in result.update["artifacts"] if path.endswith("/cfd-design-brief.json"))
    run_dir_name = json_artifact.split("/")[-2]
    json_path = outputs_dir / "submarine" / "design-brief" / run_dir_name / "cfd-design-brief.json"

    assert json_path.exists()
    assert len(run_dir_name) <= 80
    assert len(str(json_path)) < 240


def test_submarine_design_brief_run_dir_budget_respects_near_limit_output_root():
    outputs_dir = Path("C:/near-limit-root") / ("solver-segment-" * 4) / ("artifact-segment-" * 4)
    run_basis = ("DARPA SUBOFF 5 mps CFD scientific verification submarine result acceptance visible preflight then execute ") * 4

    run_dir_name = design_brief_module._build_run_dir_name(
        outputs_dir=outputs_dir,
        run_basis=run_basis,
    )
    artifact_path = outputs_dir / "submarine" / "design-brief" / run_dir_name / "cfd-design-brief.json"

    assert len(run_dir_name) <= design_brief_module._resolve_run_dir_name_budget(outputs_dir)
    assert len(run_dir_name.rsplit("-", 1)[-1]) == design_brief_module._RUN_DIR_HASH_CHARS
    assert len(str(artifact_path)) <= design_brief_module._MAX_ARTIFACT_PATH_CHARS


def test_submarine_design_brief_builds_initial_output_delivery_plan(
    tmp_path,
    monkeypatch,
):
    paths = Paths(tmp_path)
    thread_id = "thread-initial-output-delivery"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "initial-output-delivery.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_design_brief_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/initial-output-delivery.stl",
        task_description="先确认 baseline 阻力计算，并把尾流速度切片和流线图交付边界写清楚。",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="draft",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        expected_outputs=["阻力系数 Cd", "尾流速度切片", "流线图"],
        tool_call_id="tc-design-brief-initial-output-delivery",
    )

    json_path = outputs_dir / "submarine" / "design-brief" / "initial-output-delivery" / "cfd-design-brief.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]
    delivery_by_id = {item["output_id"]: item for item in payload["output_delivery_plan"]}

    assert delivery_by_id["drag_coefficient"]["delivery_status"] == "planned"
    assert delivery_by_id["wake_velocity_slice"]["delivery_status"] == "planned"
    assert delivery_by_id["streamlines"]["delivery_status"] == "not_yet_supported"
    assert runtime_state["output_delivery_plan"] == payload["output_delivery_plan"]


def test_submarine_design_brief_merges_inferred_added_outputs_when_tool_args_omit_expected_outputs(
    tmp_path,
    monkeypatch,
):
    paths = Paths(tmp_path)
    thread_id = "thread-infer-added-outputs"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "infer-added-outputs.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    initial = tool_module.submarine_design_brief_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/infer-added-outputs.stl",
        task_description="先确认当前基线阻力计算，并交付阻力系数 Cd 与中文结果报告。",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="confirmed",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        expected_outputs=["阻力系数 Cd", "中文结果报告"],
        open_questions=[],
        tool_call_id="tc-design-brief-infer-added-initial",
    )
    runtime.state["submarine_runtime"] = initial.update["submarine_runtime"]
    runtime.state["artifacts"] = initial.update["artifacts"]

    updated = tool_module.submarine_design_brief_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/infer-added-outputs.stl",
        task_description=("在当前已确认基线的基础上，追加两个交付输出：尾流速度切片和流线图。请更新当前设计简报与交付计划，并明确支持边界。"),
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="confirmed",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        tool_call_id="tc-design-brief-infer-added-update",
    )

    json_path = outputs_dir / "submarine" / "design-brief" / "infer-added-outputs" / "cfd-design-brief.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = updated.update["submarine_runtime"]
    requested_outputs = payload["requested_outputs"]
    delivery_by_id = {item["output_id"]: item for item in payload["output_delivery_plan"]}

    assert payload["expected_outputs"] == [
        "阻力系数 Cd",
        "中文结果报告",
        "尾流速度切片",
        "流线图",
    ]
    assert [item["output_id"] for item in requested_outputs] == [
        "drag_coefficient",
        "chinese_report",
        "wake_velocity_slice",
        "streamlines",
    ]
    assert delivery_by_id["wake_velocity_slice"]["delivery_status"] == "planned"
    assert delivery_by_id["streamlines"]["delivery_status"] == "not_yet_supported"
    assert runtime_state["requested_outputs"] == requested_outputs
    assert runtime_state["output_delivery_plan"] == payload["output_delivery_plan"]


def test_submarine_design_brief_detects_official_case_seed_without_geometry(
    tmp_path,
    monkeypatch,
):
    paths = Paths(tmp_path)
    thread_id = "thread-official-case-brief"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    seed_path = uploads_dir / "cavity" / "system" / "blockMeshDict"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text("FoamFile{}", encoding="utf-8")

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_design_brief_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path=None,
        task_description="Use the official OpenFOAM cavity defaults and prepare the run brief.",
        task_type="official_openfoam_case",
        confirmation_status="confirmed",
        tool_call_id="tc-design-brief-official-case",
    )

    json_path = outputs_dir / "submarine" / "design-brief" / "cavity" / "cfd-design-brief.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]

    assert payload["input_source_type"] == "openfoam_case_seed"
    assert payload["official_case_id"] == "cavity"
    assert payload["official_case_seed_virtual_paths"] == [
        "/mnt/user-data/uploads/cavity/system/blockMeshDict"
    ]
    assert payload["geometry_virtual_path"] in {None, ""}
    assert runtime_state["input_source_type"] == "openfoam_case_seed"
    assert runtime_state["official_case_id"] == "cavity"


def test_submarine_design_brief_pins_official_case_defaults_when_model_supplies_generic_task_type(
    tmp_path,
    monkeypatch,
):
    paths = Paths(tmp_path)
    thread_id = "thread-official-pitzdaily-defaults"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    seed_path = uploads_dir / "pitzDaily.blockMeshDict"
    seed_path.write_text("FoamFile{}", encoding="utf-8")

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_design_brief_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/pitzDaily.blockMeshDict",
        task_description="Use the uploaded OpenFOAM pitzDaily seed with default settings and continue the run.",
        task_type="pressure_distribution",
        confirmation_status="confirmed",
        end_time_seconds=200.0,
        tool_call_id="tc-design-brief-pitzdaily-defaults",
    )

    json_path = (
        outputs_dir
        / "submarine"
        / "design-brief"
        / "pitzdaily"
        / "cfd-design-brief.json"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]
    requirements = payload["simulation_requirements"]

    assert payload["input_source_type"] == "openfoam_case_seed"
    assert payload["official_case_id"] == "pitzDaily"
    assert payload["task_type"] == "official_openfoam_case"
    assert requirements["inlet_velocity_mps"] == 10.0
    assert requirements["end_time_seconds"] == 2000.0
    assert requirements["delta_t_seconds"] == 1.0
    assert requirements["write_interval_steps"] == 100
    assert runtime_state["task_type"] == "official_openfoam_case"
    assert runtime_state["official_case_seed_virtual_paths"] == [
        "/mnt/user-data/uploads/pitzDaily.blockMeshDict"
    ]
    assert runtime_state["geometry_virtual_path"] == ""
    assert runtime_state["next_recommended_stage"] == "solver-dispatch"


def test_submarine_design_brief_recovers_execute_now_from_latest_user_message(
    tmp_path,
    monkeypatch,
):
    paths = Paths(tmp_path)
    thread_id = "thread-official-cavity-execute-now"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    seed_path = uploads_dir / "blockMeshDict"
    seed_path.write_text("FoamFile{}", encoding="utf-8")

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["messages"] = [
        HumanMessage(
            content=(
                "继续推进，不需要再等我补充。请直接把我上传的 OpenFOAM case seed 当作输入，"
                "先生成结构化设计简报，再按默认设置组装并执行案例，最后输出关键结果摘要和最终报告，不要停下来再向我确认。"
            )
        )
    ]

    result = tool_module.submarine_design_brief_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/blockMeshDict",
        task_description="对当前 OpenFOAM cavity seed 执行链路做真实验证并保留可追踪证据链。",
        task_type="official_openfoam_case",
        confirmation_status="confirmed",
        tool_call_id="tc-design-brief-cavity-execute-now",
    )

    json_path = (
        outputs_dir
        / "submarine"
        / "design-brief"
        / "cavity"
        / "cfd-design-brief.json"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]

    assert payload["execution_preference"] == "execute_now"
    assert runtime_state["execution_preference"] == "execute_now"
    assert payload["task_type"] == "official_openfoam_case"


def test_submarine_design_brief_accepts_explicit_pitzdaily_seed_path_without_geometry(
    tmp_path,
    monkeypatch,
):
    paths = Paths(tmp_path)
    thread_id = "thread-official-pitzdaily-brief"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    seed_path = uploads_dir / "pitzDaily.blockMeshDict"
    seed_path.write_text("FoamFile{}", encoding="utf-8")

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_design_brief_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/pitzDaily.blockMeshDict",
        task_description="Treat the uploaded pitzDaily seed as a normal user input and prepare the run brief.",
        task_type="official_openfoam_case",
        confirmation_status="confirmed",
        tool_call_id="tc-design-brief-official-pitzdaily",
    )

    json_path = (
        outputs_dir
        / "submarine"
        / "design-brief"
        / "pitzdaily"
        / "cfd-design-brief.json"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]

    assert payload["input_source_type"] == "openfoam_case_seed"
    assert payload["official_case_id"] == "pitzDaily"
    assert payload["official_case_seed_virtual_paths"] == [
        "/mnt/user-data/uploads/pitzDaily.blockMeshDict"
    ]
    assert payload["geometry_virtual_path"] in {None, ""}
    assert runtime_state["input_source_type"] == "openfoam_case_seed"
    assert runtime_state["official_case_id"] == "pitzDaily"
    assert runtime_state["geometry_virtual_path"] == ""


def test_submarine_design_brief_prefers_structured_official_task_type_when_seed_and_stl_coexist(
    tmp_path,
    monkeypatch,
):
    paths = Paths(tmp_path)
    thread_id = "thread-official-case-over-stl"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    (uploads_dir / "system").mkdir(parents=True, exist_ok=True)
    (uploads_dir / "system" / "blockMeshDict").write_text(
        "FoamFile{}",
        encoding="utf-8",
    )
    geometry_path = uploads_dir / "coexisting-geometry.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["uploaded_files"] = [
        {
            "filename": "blockMeshDict",
            "path": "/mnt/user-data/uploads/system/blockMeshDict",
        },
        {
            "filename": "coexisting-geometry.stl",
            "path": "/mnt/user-data/uploads/coexisting-geometry.stl",
        },
    ]

    result = tool_module.submarine_design_brief_tool.func(
        runtime=runtime,
        geometry_path=None,
        task_description="Prepare the uploaded case and continue the validated CFD workflow.",
        task_type="official_openfoam_case",
        confirmation_status="confirmed",
        tool_call_id="tc-design-brief-official-over-stl",
    )

    json_path = (
        outputs_dir
        / "submarine"
        / "design-brief"
        / "cavity"
        / "cfd-design-brief.json"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]

    assert payload["input_source_type"] == "openfoam_case_seed"
    assert payload["official_case_id"] == "cavity"
    assert payload["geometry_virtual_path"] in {None, ""}
    assert runtime_state["input_source_type"] == "openfoam_case_seed"
    assert runtime_state["official_case_id"] == "cavity"
    assert runtime_state["geometry_virtual_path"] == ""
    assert runtime_state["next_recommended_stage"] == "solver-dispatch"
