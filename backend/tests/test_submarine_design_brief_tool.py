import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from deerflow.config.paths import Paths

tool_module = importlib.import_module("deerflow.tools.builtins.submarine_design_brief_tool")


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
    assert payload["open_questions"] == []
    assert payload["expected_outputs"] == ["阻力系数 Cd", "中文结果报告", "网格质量摘要"]
    assert runtime_state["review_status"] == "ready_for_supervisor"
    assert runtime_state["next_recommended_stage"] == "geometry-preflight"
    assert len(runtime_state["activity_timeline"]) == 2
    assert runtime_state["activity_timeline"][-1]["status"] == "confirmed"
    assert payload["execution_outline"][0]["status"] == "completed"
    assert payload["execution_outline"][1]["status"] == "ready"
    assert payload["execution_outline"][2]["status"] == "ready"
    assert runtime_state["execution_plan"][0]["status"] == "completed"
    assert runtime_state["execution_plan"][1]["status"] == "ready"


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

    json_path = (
        outputs_dir
        / "submarine"
        / "design-brief"
        / "requested-outputs"
        / "cfd-design-brief.json"
    )
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

    json_path = (
        outputs_dir
        / "submarine"
        / "design-brief"
        / "postprocess-spec"
        / "cfd-design-brief.json"
    )
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


def test_submarine_design_brief_recovers_geometry_from_uploaded_files_state(
    tmp_path, monkeypatch
):
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

    json_path = (
        outputs_dir
        / "submarine"
        / "design-brief"
        / "uploaded-files-brief"
        / "cfd-design-brief.json"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]

    assert payload["geometry_virtual_path"] == "/mnt/user-data/uploads/uploaded-files-brief.stl"
    assert runtime_state["geometry_virtual_path"] == "/mnt/user-data/uploads/uploaded-files-brief.stl"


def test_submarine_design_brief_includes_scientific_verification_requirements(
    tmp_path, monkeypatch
):
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

    json_path = (
        outputs_dir
        / "submarine"
        / "design-brief"
        / "verification-brief"
        / "cfd-design-brief.json"
    )
    md_path = (
        outputs_dir
        / "submarine"
        / "design-brief"
        / "verification-brief"
        / "cfd-design-brief.md"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert [item["requirement_id"] for item in payload["scientific_verification_requirements"]] == [
        "final_residual_threshold",
        "force_coefficient_tail_stability",
        "mesh_independence_study",
        "domain_sensitivity_study",
        "time_step_sensitivity_study",
    ]
    assert (
        payload["scientific_verification_requirements"][1]["force_coefficient"]
        == "Cd"
    )
    assert "科研验证要求" in markdown
    assert "mesh_independence_study" in markdown


def test_submarine_design_brief_captures_direct_execution_preference(
    tmp_path, monkeypatch
):
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

    json_path = (
        outputs_dir
        / "submarine"
        / "design-brief"
        / "execution-preference"
        / "cfd-design-brief.json"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]

    assert payload["execution_preference"] == "execute_now"
    assert runtime_state["execution_preference"] == "execute_now"
