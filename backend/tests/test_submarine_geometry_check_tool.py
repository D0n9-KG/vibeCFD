import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from deerflow.config.paths import Paths

tool_module = importlib.import_module("deerflow.tools.builtins.submarine_geometry_check_tool")


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


def _write_xt(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "APPL=Test Parasolid;",
                "KEY=SUBOFF-123;",
                "FORMAT=text;",
                "FILE=darpa_suboff.x_t;",
            ]
        ),
        encoding="utf-8",
    )


def test_submarine_geometry_check_generates_thread_artifacts(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "type209-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = {
        "current_stage": "task-intelligence",
        "task_summary": "先完成 CFD 方案确认",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/runtime-demo.stl",
        "review_status": "ready_for_supervisor",
        "next_recommended_stage": "geometry-preflight",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/design-brief/runtime-demo/cfd-design-brief.md",
        "artifact_virtual_paths": [
            "/mnt/user-data/outputs/submarine/design-brief/runtime-demo/cfd-design-brief.json"
        ],
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
                "status": "ready",
            },
            {
                "role_id": "solver-dispatch",
                "owner": "DeerFlow solver-dispatch",
                "goal": "准备求解派发",
                "status": "pending",
            },
        ],
    }

    result = tool_module.submarine_geometry_check_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/type209-demo.stl",
        task_description="分析这个潜艇几何的阻力基线",
        task_type="resistance",
        geometry_family_hint="Type 209",
        tool_call_id="tc-geometry-1",
    )

    artifacts = result.update["artifacts"]
    assert any(path.endswith("/geometry-check.json") for path in artifacts)
    assert any(path.endswith("/geometry-check.md") for path in artifacts)
    assert any(path.endswith("/geometry-check.html") for path in artifacts)

    json_path = outputs_dir / "submarine" / "geometry-check" / "type209-demo" / "geometry-check.json"
    md_path = outputs_dir / "submarine" / "geometry-check" / "type209-demo" / "geometry-check.md"
    html_path = outputs_dir / "submarine" / "geometry-check" / "type209-demo" / "geometry-check.html"

    assert json_path.exists()
    assert md_path.exists()
    assert html_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["geometry"]["input_format"] == "stl"
    assert payload["geometry"]["geometry_family"] == "Type 209"
    assert payload["candidate_cases"]
    assert "summary_zh" in payload

    markdown = md_path.read_text(encoding="utf-8")
    assert "几何检查" in markdown
    assert "Type 209" in markdown


def test_submarine_geometry_check_rejects_xt_inputs(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "darpa-suboff.x_t"
    _write_xt(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_geometry_check_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/darpa-suboff.x_t",
        task_description="检查这个 benchmark 几何是否适合压力分布分析",
        task_type="pressure_distribution",
        geometry_family_hint="DARPA SUBOFF",
        tool_call_id="tc-geometry-2",
    )

    messages = result.update["messages"]
    assert len(messages) == 1
    assert "STL" in messages[0].content
    assert "x_t" in messages[0].content

    json_path = outputs_dir / "submarine" / "geometry-check" / "darpa-suboff" / "geometry-check.json"
    assert not json_path.exists()


def test_submarine_geometry_check_includes_review_fields(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "review-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    tool_module.submarine_geometry_check_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/review-demo.stl",
        task_description="检查这个潜艇几何并给出后续建议",
        task_type="resistance",
        geometry_family_hint="Type 209",
        tool_call_id="tc-geometry-review",
    )

    json_path = outputs_dir / "submarine" / "geometry-check" / "review-demo" / "geometry-check.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["review_status"] == "ready_for_supervisor"
    assert payload["next_recommended_stage"] == "solver-dispatch"
    assert payload["report_virtual_path"].endswith("/geometry-check.md")


def test_submarine_geometry_check_updates_runtime_state(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "runtime-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_geometry_check_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/runtime-demo.stl",
        task_description="检查几何并准备后续潜艇阻力分析",
        task_type="resistance",
        geometry_family_hint="Type 209",
        tool_call_id="tc-geometry-runtime",
    )

    runtime_state = result.update["submarine_runtime"]

    assert runtime_state["current_stage"] == "geometry-preflight"
    assert runtime_state["task_type"] == "resistance"
    assert runtime_state["geometry_virtual_path"] == "/mnt/user-data/uploads/runtime-demo.stl"
    assert runtime_state["next_recommended_stage"] == "solver-dispatch"
    assert runtime_state["report_virtual_path"].endswith("/geometry-check.md")
    assert runtime_state["artifact_virtual_paths"]
    assert runtime_state["execution_plan"][2]["status"] == "completed"
    assert runtime_state["execution_plan"][3]["status"] == "ready"
    assert len(runtime_state["activity_timeline"]) == 1
    assert runtime_state["activity_timeline"][0]["stage"] == "geometry-preflight"
    assert runtime_state["activity_timeline"][0]["actor"] == "geometry-preflight"


def test_submarine_geometry_check_requires_user_confirmation_before_preflight(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-awaiting-confirmation"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "awaiting-confirmation.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = {
        "current_stage": "task-intelligence",
        "task_summary": "Confirm the baseline conditions before geometry preflight",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/awaiting-confirmation.stl",
        "confirmation_status": "draft",
        "review_status": "needs_user_confirmation",
        "next_recommended_stage": "user-confirmation",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/design-brief/awaiting-confirmation/cfd-design-brief.md",
        "artifact_virtual_paths": [
            "/mnt/user-data/outputs/submarine/design-brief/awaiting-confirmation/cfd-design-brief.json"
        ],
    }

    result = tool_module.submarine_geometry_check_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/awaiting-confirmation.stl",
        task_description="Try to run geometry preflight before the brief is confirmed",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        tool_call_id="tc-geometry-awaiting-confirmation",
    )

    geometry_check_path = (
        outputs_dir
        / "submarine"
        / "geometry-check"
        / "awaiting-confirmation"
        / "geometry-check.json"
    )

    assert not geometry_check_path.exists()
    assert "messages" in result.update
    assert "artifacts" not in result.update
    assert "submarine_runtime" not in result.update
    assert "user confirmation" in result.update["messages"][0].content.lower()


def test_submarine_geometry_check_preserves_confirmed_brief_context(
    tmp_path, monkeypatch
):
    design_brief_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_design_brief_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-confirmed-geometry-preflight"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "confirmed-geometry-preflight.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(design_brief_tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    design_brief_result = design_brief_tool_module.submarine_design_brief_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/confirmed-geometry-preflight.stl",
        task_description="确认方案后先预检再执行这次潜艇基线 CFD。",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="confirmed",
        selected_case_id="user-confirmed-case",
        inlet_velocity_mps=5.0,
        fluid_density_kg_m3=1025.0,
        kinematic_viscosity_m2ps=1.05e-06,
        end_time_seconds=200.0,
        delta_t_seconds=1.0,
        write_interval_steps=50,
        expected_outputs=["阻力系数 Cd"],
        open_questions=[],
        tool_call_id="tc-design-brief-confirmed-geometry-preflight",
    )

    runtime.state["artifacts"] = design_brief_result.update["artifacts"]
    runtime.state["submarine_runtime"] = {}

    result = tool_module.submarine_geometry_check_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/confirmed-geometry-preflight.stl",
        task_description="Run geometry preflight for the already confirmed brief",
        task_type="resistance",
        geometry_family_hint=None,
        tool_call_id="tc-geometry-confirmed-brief",
    )

    runtime_state = result.update["submarine_runtime"]

    assert runtime_state["confirmation_status"] == "confirmed"
    assert runtime_state["execution_preference"] == "preflight_then_execute"
    assert runtime_state["selected_case_id"] == "user-confirmed-case"
    assert runtime_state["simulation_requirements"]["inlet_velocity_mps"] == 5.0
    assert runtime_state["execution_plan"][2]["status"] == "completed"
    assert runtime_state["execution_plan"][3]["status"] == "ready"
