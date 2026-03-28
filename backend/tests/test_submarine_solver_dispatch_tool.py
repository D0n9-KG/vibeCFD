import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

from deerflow.config.paths import Paths

tool_module = importlib.import_module("deerflow.tools.builtins.submarine_solver_dispatch_tool")


def _platform_fs_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    raw = str(path.resolve())
    if raw.startswith("\\\\?\\"):
        return Path(raw)
    return Path(f"\\\\?\\{raw}")


def _make_runtime(paths: Paths, thread_id: str = "thread-1", sandbox_id: str = "local") -> SimpleNamespace:
    return SimpleNamespace(
        state={
            "sandbox": {"sandbox_id": sandbox_id},
            "thread_data": {
                "workspace_path": str(paths.sandbox_work_dir(thread_id)),
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(paths.sandbox_outputs_dir(thread_id)),
            },
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
                "### Parasolid transmit file",
                "APPL=Siemens NX;",
                "KEY=suboff-demo-key;",
                "FILE=suboff-demo.x_t;",
                "DATE=2026-03-26;",
                "DARPA SUBOFF reference geometry",
            ]
        ),
        encoding="utf-8",
    )


class _FakeSandbox:
    def __init__(self, output: str = "OpenFOAM run simulated") -> None:
        self.commands: list[str] = []
        self.output = output

    def execute_command(self, command: str) -> str:
        self.commands.append(command)
        return self.output


class _FakeProvider:
    def __init__(self, sandbox: _FakeSandbox) -> None:
        self.sandbox = sandbox

    def get(self, sandbox_id: str):
        return self.sandbox if sandbox_id == "local" else None


class _FakePostprocessSandbox(_FakeSandbox):
    def __init__(self, case_dir: Path, output: str = "End") -> None:
        super().__init__(output=output)
        self.case_dir = case_dir

    def execute_command(self, command: str) -> str:
        case_dir = _platform_fs_path(self.case_dir)
        coeffs_dir = case_dir / "postProcessing" / "forceCoeffs" / "0"
        coeffs_dir.mkdir(parents=True, exist_ok=True)
        (coeffs_dir / "forceCoeffs.dat").write_text(
            "\n".join(
                [
                    "# Time Cd Cs Cl CmRoll CmPitch CmYaw",
                    "0 0.18 0.00 0.00 0.00 0.01 0.00",
                    "200 0.12 0.00 0.00 0.00 0.01 0.00",
                ]
            ),
            encoding="utf-8",
        )
        forces_dir = case_dir / "postProcessing" / "forces" / "0"
        forces_dir.mkdir(parents=True, exist_ok=True)
        (forces_dir / "forces.dat").write_text(
            "\n".join(
                [
                    "# Time forces(pressure viscous) moments(pressure viscous)",
                    "0 ((0 0 0) (12 0 0)) ((0 0 0) (0 1 0))",
                    "200 ((0 0 0) (8 0 0)) ((0 0 0) (0 0.5 0))",
                ]
            ),
            encoding="utf-8",
        )
        self.output = "\n".join(
            [
                "[submarine-cfd] Preparing background mesh",
                "Check mesh...",
                "    points:           10234",
                "    faces:            28764",
                "    internal faces:   27654",
                "    cells:            9342",
                "Mesh OK.",
                "Time = 0",
                "smoothSolver:  Solving for Ux, Initial residual = 0.02, Final residual = 1e-05, No Iterations 2",
                "smoothSolver:  Solving for Uy, Initial residual = 0.01, Final residual = 2e-06, No Iterations 2",
                "GAMG:  Solving for p, Initial residual = 0.3, Final residual = 0.002, No Iterations 6",
                "Time = 200",
                "smoothSolver:  Solving for Ux, Initial residual = 0.00031, Final residual = 3e-08, No Iterations 2",
                "smoothSolver:  Solving for Uy, Initial residual = 0.00012, Final residual = 1e-08, No Iterations 2",
                "smoothSolver:  Solving for k, Initial residual = 0.004, Final residual = 8e-07, No Iterations 2",
                "smoothSolver:  Solving for omega, Initial residual = 0.008, Final residual = 9e-07, No Iterations 2",
                "GAMG:  Solving for p, Initial residual = 0.012, Final residual = 0.00014, No Iterations 5",
                "ExecutionTime = 18.1 s  ClockTime = 19 s",
                "End",
            ]
        )
        return super().execute_command(command)


class _FakeRequestedPostprocessSandbox(_FakePostprocessSandbox):
    def execute_command(self, command: str) -> str:
        case_dir = _platform_fs_path(self.case_dir)
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "postProcessing").mkdir(parents=True, exist_ok=True)
        result = super().execute_command(command)
        surface_dir = case_dir / "postProcessing" / "surfacePressure" / "200"
        surface_dir.mkdir(parents=True, exist_ok=True)
        (surface_dir / "surfacePressure.csv").write_text(
            "\n".join(
                [
                    "x,y,z,p",
                    "0.0,0.0,0.0,12.0",
                    "1.0,0.2,0.1,10.5",
                ]
            ),
            encoding="utf-8",
        )
        wake_dir = case_dir / "postProcessing" / "wakeVelocitySlice" / "200"
        wake_dir.mkdir(parents=True, exist_ok=True)
        (wake_dir / "wakeVelocitySlice.csv").write_text(
            "\n".join(
                [
                    "x,y,z,Ux,Uy,Uz",
                    "5.0,0.0,0.0,4.8,0.0,0.0",
                    "5.0,0.2,0.1,4.6,0.1,0.0",
                ]
            ),
            encoding="utf-8",
        )
        return result


class _FakeScientificStudySandbox(_FakeSandbox):
    def __init__(self, workspace_dir: Path, output: str = "End") -> None:
        super().__init__(output=output)
        self.workspace_dir = workspace_dir
        self.cd_by_command_fragment = {
            "/study-execution-demo/openfoam-case/Allrun": 0.1200,
            "/study-execution-demo/studies/mesh-independence/coarse/openfoam-case/Allrun": 0.1212,
            "/study-execution-demo/studies/mesh-independence/fine/openfoam-case/Allrun": 0.1194,
            "/study-execution-demo/studies/domain-sensitivity/compact/openfoam-case/Allrun": 0.1290,
            "/study-execution-demo/studies/domain-sensitivity/expanded/openfoam-case/Allrun": 0.1110,
            "/study-execution-demo/studies/time-step-sensitivity/coarse/openfoam-case/Allrun": 0.1208,
            "/study-execution-demo/studies/time-step-sensitivity/fine/openfoam-case/Allrun": 0.1196,
        }

    def _resolve_case_dir(self, command: str) -> tuple[Path, float]:
        for fragment, cd_value in self.cd_by_command_fragment.items():
            if fragment in command:
                relative = fragment.split("/study-execution-demo/", maxsplit=1)[1]
                allrun_relative = relative.removeprefix("/")
                case_relative = allrun_relative.removesuffix("/Allrun")
                return (
                    self.workspace_dir
                    / "submarine"
                    / "solver-dispatch"
                    / "study-execution-demo"
                    / Path(case_relative),
                    cd_value,
                )
        raise AssertionError(f"Unexpected command for scientific study sandbox: {command}")

    def execute_command(self, command: str) -> str:
        case_dir, cd_value = self._resolve_case_dir(command)
        case_dir = _platform_fs_path(case_dir)
        coeffs_dir = case_dir / "postProcessing" / "forceCoeffs" / "0"
        coeffs_dir.mkdir(parents=True, exist_ok=True)
        (coeffs_dir / "forceCoeffs.dat").write_text(
            "\n".join(
                [
                    "# Time Cd Cs Cl CmRoll CmPitch CmYaw",
                    f"0 {cd_value + 0.0040:.4f} 0.00 0.00 0.00 0.01 0.00",
                    f"200 {cd_value:.4f} 0.00 0.00 0.00 0.01 0.00",
                ]
            ),
            encoding="utf-8",
        )
        forces_dir = case_dir / "postProcessing" / "forces" / "0"
        forces_dir.mkdir(parents=True, exist_ok=True)
        drag_force = round(cd_value * 100.0, 4)
        (forces_dir / "forces.dat").write_text(
            "\n".join(
                [
                    "# Time forces(pressure viscous) moments(pressure viscous)",
                    f"0 ((0 0 0) ({drag_force + 1.0} 0 0)) ((0 0 0) (0 1 0))",
                    f"200 ((0 0 0) ({drag_force} 0 0)) ((0 0 0) (0 0.5 0))",
                ]
            ),
            encoding="utf-8",
        )
        self.output = "\n".join(
            [
                "[submarine-cfd] Preparing background mesh",
                "Check mesh...",
                "    points:           10234",
                "    faces:            28764",
                "    internal faces:   27654",
                "    cells:            9342",
                "Mesh OK.",
                "Time = 0",
                "smoothSolver:  Solving for Ux, Initial residual = 0.02, Final residual = 1e-05, No Iterations 2",
                "GAMG:  Solving for p, Initial residual = 0.3, Final residual = 0.002, No Iterations 6",
                "Time = 200",
                "smoothSolver:  Solving for Ux, Initial residual = 0.00031, Final residual = 3e-08, No Iterations 2",
                "smoothSolver:  Solving for k, Initial residual = 0.004, Final residual = 8e-07, No Iterations 2",
                "smoothSolver:  Solving for omega, Initial residual = 0.008, Final residual = 9e-07, No Iterations 2",
                "GAMG:  Solving for p, Initial residual = 0.012, Final residual = 0.00014, No Iterations 5",
                "ExecutionTime = 18.1 s  ClockTime = 19 s",
                "End",
            ]
        )
        return super().execute_command(command)


def test_submarine_solver_dispatch_tool_generates_artifacts(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "type209-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/type209-demo.stl",
        task_description="为这个潜艇几何准备 OpenFOAM 阻力分析",
        task_type="resistance",
        geometry_family_hint="Type 209",
        execute_now=False,
        tool_call_id="tc-dispatch-1",
    )

    artifacts = result.update["artifacts"]
    assert any(path.endswith("/openfoam-request.json") for path in artifacts)
    assert any(path.endswith("/dispatch-summary.md") for path in artifacts)
    assert any(path.endswith("/dispatch-summary.html") for path in artifacts)

    json_path = outputs_dir / "submarine" / "solver-dispatch" / "type209-demo" / "openfoam-request.json"
    md_path = outputs_dir / "submarine" / "solver-dispatch" / "type209-demo" / "dispatch-summary.md"
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["dispatch_status"] == "planned"
    assert payload["execution_readiness"] == "stl_ready"
    assert payload["geometry"]["geometry_family"] == "Type 209"
    assert payload["selected_case"]["case_id"]
    assert md_path.exists()


def test_submarine_solver_dispatch_emits_scientific_study_plan_artifacts(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-study-plan"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "study-plan-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/study-plan-demo.stl",
        task_description="涓鸿繖涓?DARPA SUBOFF 鍩虹嚎鍑犱綍鐢熸垚 scientific study plan",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=False,
        tool_call_id="tc-dispatch-study-plan",
    )

    artifacts = result.update["artifacts"]
    request_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "study-plan-demo" / "openfoam-request.json"
    )
    study_plan_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "study-plan-demo" / "study-plan.json"
    )
    study_manifest_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "study-plan-demo" / "study-manifest.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    study_plan = json.loads(study_plan_path.read_text(encoding="utf-8"))
    study_manifest = json.loads(study_manifest_path.read_text(encoding="utf-8"))

    assert any(path.endswith("/study-plan.json") for path in artifacts)
    assert any(path.endswith("/study-manifest.json") for path in artifacts)
    assert payload["scientific_study_plan"]["study_count"] == 3
    assert payload["scientific_study_manifest"]["study_execution_status"] == "planned"
    assert study_plan["study_count"] == 3
    assert study_manifest["study_definitions"][0]["study_type"] == "mesh_independence"
    assert study_manifest["study_definitions"][0]["variants"][0]["variant_id"] == "coarse"
    assert any(
        path.endswith("/studies/mesh-independence/coarse/solver-results.json")
        for path in study_manifest["artifact_virtual_paths"]
    )


def test_submarine_solver_dispatch_tool_can_execute_in_sandbox(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "suboff-demo.stl"
    _write_ascii_stl(geometry_path)

    fake_sandbox = _FakeSandbox()

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/suboff-demo.stl",
        task_description="直接执行一个 OpenFOAM 适配命令",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command="echo run-openfoam",
        tool_call_id="tc-dispatch-2",
    )

    log_path = outputs_dir / "submarine" / "solver-dispatch" / "suboff-demo" / "openfoam-run.log"
    json_path = outputs_dir / "submarine" / "solver-dispatch" / "suboff-demo" / "openfoam-request.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert fake_sandbox.commands == ["echo run-openfoam"]
    assert log_path.exists()
    assert "OpenFOAM run simulated" in log_path.read_text(encoding="utf-8")
    assert payload["dispatch_status"] == "executed"
    assert any(path.endswith("/openfoam-run.log") for path in result.update["artifacts"])


def test_submarine_solver_dispatch_includes_review_contract(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "review-dispatch.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/review-dispatch.stl",
        task_description="为这个几何生成求解派发计划并等待审核",
        task_type="resistance",
        geometry_family_hint="Type 209",
        execute_now=False,
        tool_call_id="tc-dispatch-review",
    )

    json_path = outputs_dir / "submarine" / "solver-dispatch" / "review-dispatch" / "openfoam-request.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["review_status"] == "ready_for_supervisor"
    assert payload["next_recommended_stage"] == "solver-dispatch"
    assert payload["report_virtual_path"].endswith("/dispatch-summary.md")


def test_submarine_solver_dispatch_updates_runtime_state(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "runtime-dispatch.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = {
        "current_stage": "task-intelligence",
        "task_summary": "先由 Claude Code 收敛 CFD 设计方案",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/runtime-dispatch.stl",
        "review_status": "ready_for_supervisor",
        "next_recommended_stage": "geometry-preflight",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/design-brief/runtime-dispatch/cfd-design-brief.md",
        "artifact_virtual_paths": [
            "/mnt/user-data/outputs/submarine/design-brief/runtime-dispatch/cfd-design-brief.json"
        ],
        "activity_timeline": [
            {
                "stage": "task-intelligence",
                "actor": "claude-code-supervisor",
                "title": "设计简报已确认",
                "summary": "Claude Code 已与用户确认第一版 CFD 方案。",
                "status": "confirmed",
                "timestamp": "2026-03-26T10:40:00+00:00",
            }
        ],
    }

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/runtime-dispatch.stl",
        task_description="为该潜艇几何准备 OpenFOAM 求解派发",
        task_type="resistance",
        geometry_family_hint="Type 209",
        execute_now=False,
        tool_call_id="tc-dispatch-runtime",
    )

    runtime_state = result.update["submarine_runtime"]

    assert runtime_state["current_stage"] == "solver-dispatch"
    assert runtime_state["task_type"] == "resistance"
    assert runtime_state["geometry_virtual_path"] == "/mnt/user-data/uploads/runtime-dispatch.stl"
    assert runtime_state["report_virtual_path"].endswith("/dispatch-summary.md")
    assert runtime_state["selected_case_id"]
    assert runtime_state["execution_readiness"] == "stl_ready"
    assert runtime_state["execution_plan"][2]["status"] == "completed"
    assert runtime_state["execution_plan"][3]["status"] == "in_progress"
    assert runtime_state["workspace_case_dir_virtual_path"].endswith("/openfoam-case")
    assert runtime_state["run_script_virtual_path"].endswith("/Allrun")
    assert runtime_state["supervisor_handoff_virtual_path"].endswith("/supervisor-handoff.json")
    assert len(runtime_state["activity_timeline"]) == 2
    assert runtime_state["activity_timeline"][-1]["stage"] == "solver-dispatch"
    assert runtime_state["activity_timeline"][-1]["actor"] == "solver-dispatch"


def test_submarine_solver_dispatch_writes_openfoam_case_scaffold(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "case-scaffold.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/case-scaffold.stl",
        task_description="为该潜艇阻力任务准备真实 OpenFOAM case scaffold",
        task_type="resistance",
        geometry_family_hint="Type 209",
        execute_now=False,
        tool_call_id="tc-dispatch-scaffold",
    )

    request_path = outputs_dir / "submarine" / "solver-dispatch" / "case-scaffold" / "openfoam-request.json"
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    case_dir = workspace_dir / "submarine" / "solver-dispatch" / "case-scaffold" / "openfoam-case"

    assert case_dir.exists()
    assert (case_dir / "0" / "U").exists()
    assert (case_dir / "0" / "p").exists()
    assert (case_dir / "0" / "k").exists()
    assert (case_dir / "0" / "omega").exists()
    assert (case_dir / "0" / "nut").exists()
    assert (case_dir / "constant" / "transportProperties").exists()
    assert (case_dir / "constant" / "turbulenceProperties").exists()
    assert (case_dir / "constant" / "triSurface" / "case-scaffold.stl").exists()
    assert (case_dir / "system" / "controlDict").exists()
    assert (case_dir / "system" / "fvSchemes").exists()
    assert (case_dir / "system" / "fvSolution").exists()
    assert (case_dir / "system" / "surfaceFeaturesDict").exists()
    assert (case_dir / "system" / "meshQualityDict").exists()
    assert (case_dir / "Allrun").exists()
    assert payload["workspace_case_dir_virtual_path"].endswith("/openfoam-case")
    assert payload["run_script_virtual_path"].endswith("/Allrun")

    allrun_bytes = (case_dir / "Allrun").read_bytes()
    control_dict = (case_dir / "system" / "controlDict").read_text(encoding="utf-8")
    fv_schemes = (case_dir / "system" / "fvSchemes").read_text(encoding="utf-8")
    snappy_dict = (case_dir / "system" / "snappyHexMeshDict").read_text(encoding="utf-8")
    assert b"\r\n" not in allrun_bytes
    assert b"snappyHexMesh -overwrite" not in allrun_bytes
    assert b"surfaceFeatures" in allrun_bytes
    assert "forceCoeffsHull" in control_dict
    assert "forcesHull" in control_dict
    assert "wallDist" in fv_schemes
    assert "mergeTolerance 1e-6;" in snappy_dict
    assert 'file "case-scaffold.stl";' in snappy_dict


def test_submarine_solver_dispatch_preserves_requested_outputs(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-requested-dispatch"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "requested-dispatch.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = {
        "current_stage": "task-intelligence",
        "task_summary": "按用户要求组织 CFD 输出",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/requested-dispatch.stl",
        "geometry_family": "DARPA SUBOFF",
        "selected_case_id": "darpa_suboff_bare_hull_resistance",
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
        "review_status": "ready_for_supervisor",
        "next_recommended_stage": "geometry-preflight",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/design-brief/requested-dispatch/cfd-design-brief.md",
        "artifact_virtual_paths": [],
        "activity_timeline": [],
    }

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/requested-dispatch.stl",
        task_description="根据设计简报保留用户请求的输出",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=False,
        tool_call_id="tc-dispatch-requested-outputs",
    )

    json_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "requested-dispatch"
        / "openfoam-request.json"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]

    assert [item["output_id"] for item in payload["requested_outputs"]] == [
        "drag_coefficient",
        "surface_pressure_contour",
        "chinese_report",
    ]
    assert payload["output_delivery_plan"][0]["delivery_status"] == "planned"
    assert payload["output_delivery_plan"][1]["delivery_status"] == "planned"
    assert payload["output_delivery_plan"][2]["delivery_status"] == "planned"
    assert runtime_state["requested_outputs"] == payload["requested_outputs"]


def test_submarine_solver_dispatch_requested_outputs_configure_function_objects(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-function-objects"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "function-objects.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = {
        "current_stage": "task-intelligence",
        "task_summary": "按请求配置后处理 function objects",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/function-objects.stl",
        "geometry_family": "DARPA SUBOFF",
        "selected_case_id": "darpa_suboff_bare_hull_resistance",
        "requested_outputs": [
            {
                "output_id": "surface_pressure_contour",
                "label": "表面压力云图",
                "requested_label": "表面压力云图",
                "status": "requested",
                "support_level": "supported",
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
                        "origin_value": 2.0,
                        "normal": [0.0, 1.0, 0.0],
                    },
                    "formats": ["csv", "report"],
                },
                "notes": "当前运行时可在存在后处理文件时导出尾流结果 artifact。",
            },
            {
                "output_id": "streamlines",
                "label": "流线图",
                "requested_label": "流线图",
                "status": "requested",
                "support_level": "not_yet_supported",
                "notes": "当前仓库尚未自动导出流线图 artifact。",
            },
        ],
        "review_status": "ready_for_supervisor",
        "next_recommended_stage": "geometry-preflight",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/design-brief/function-objects/cfd-design-brief.md",
        "artifact_virtual_paths": [],
        "activity_timeline": [],
    }

    tool_module.submarine_solver_dispatch_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/function-objects.stl",
        task_description="根据请求的输出结果配置 OpenFOAM 后处理对象",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=False,
        tool_call_id="tc-dispatch-function-objects",
    )

    case_dir = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "function-objects"
        / "openfoam-case"
    )
    control_dict = (case_dir / "system" / "controlDict").read_text(encoding="utf-8")

    assert "surfacePressure" in control_dict
    assert "wakeVelocitySlice" in control_dict
    assert "fields          (p);" in control_dict
    assert "fields          (U);" in control_dict
    assert "point   (8.0 0 0);" in control_dict
    assert "normal  (0.0 1.0 0.0);" in control_dict
    assert "streamlines" not in control_dict


def test_submarine_solver_dispatch_writes_supervisor_handoff_artifact(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "handoff-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/handoff-demo.stl",
        task_description="生成可供 Claude Code Supervisor 审阅的 OpenFOAM handoff",
        task_type="resistance",
        geometry_family_hint="Type 209",
        execute_now=False,
        tool_call_id="tc-dispatch-handoff",
    )

    artifacts = result.update["artifacts"]
    handoff_path = outputs_dir / "submarine" / "solver-dispatch" / "handoff-demo" / "supervisor-handoff.json"
    payload = json.loads(handoff_path.read_text(encoding="utf-8"))

    assert any(path.endswith("/supervisor-handoff.json") for path in artifacts)
    assert payload["review_status"] == "ready_for_supervisor"
    assert payload["execution_readiness"] == "stl_ready"
    assert payload["workspace_case_dir_virtual_path"].endswith("/openfoam-case")
    assert payload["run_script_virtual_path"].endswith("/Allrun")


def test_submarine_solver_dispatch_rejects_xt_inputs(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "suboff-demo.x_t"
    _write_xt(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/suboff-demo.x_t",
        task_description="先检查这个 Parasolid 几何并判断是否能直接进入 v1 求解",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=False,
        tool_call_id="tc-dispatch-xt",
    )

    messages = result.update["messages"]
    assert len(messages) == 1
    assert "STL" in messages[0].content
    assert "x_t" in messages[0].content

    request_path = outputs_dir / "submarine" / "solver-dispatch" / "suboff-demo" / "openfoam-request.json"
    assert not request_path.exists()


def test_submarine_solver_dispatch_marks_failed_execution(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "failed-run.stl"
    _write_ascii_stl(geometry_path)

    fake_sandbox = _FakeSandbox(output="FOAM FATAL ERROR: case setup is invalid")

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/failed-run.stl",
        task_description="执行一次会失败的 OpenFOAM 命令",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command="echo bad-openfoam-run",
        tool_call_id="tc-dispatch-failed",
    )

    json_path = outputs_dir / "submarine" / "solver-dispatch" / "failed-run" / "openfoam-request.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]

    assert payload["dispatch_status"] == "failed"
    assert payload["review_status"] == "blocked"
    assert payload["next_recommended_stage"] == "solver-dispatch"
    assert runtime_state["stage_status"] == "failed"
    assert runtime_state["review_status"] == "blocked"


def test_submarine_solver_dispatch_writes_solver_results_artifact(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "results-demo.stl"
    _write_ascii_stl(geometry_path)

    case_dir = workspace_dir / "submarine" / "solver-dispatch" / "results-demo" / "openfoam-case"
    fake_sandbox = _FakePostprocessSandbox(case_dir=case_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/results-demo.stl",
        task_description="执行一次会生成 forceCoeffs 的 OpenFOAM 调度",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command="bash /mnt/user-data/workspace/submarine/solver-dispatch/results-demo/openfoam-case/Allrun",
        tool_call_id="tc-dispatch-results",
    )

    artifacts = result.update["artifacts"]
    request_path = outputs_dir / "submarine" / "solver-dispatch" / "results-demo" / "openfoam-request.json"
    solver_results_path = outputs_dir / "submarine" / "solver-dispatch" / "results-demo" / "solver-results.json"
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    solver_results = json.loads(solver_results_path.read_text(encoding="utf-8"))

    assert any(path.endswith("/solver-results.json") for path in artifacts)
    assert any(path.endswith("/solver-results.md") for path in artifacts)
    assert payload["solver_results"]["solver_completed"] is True
    assert payload["solver_results"]["latest_force_coefficients"]["Cd"] == 0.12
    assert payload["solver_results"]["latest_forces"]["total_force"][0] == 8.0
    assert solver_results["latest_force_coefficients"]["Cd"] == 0.12
    assert solver_results["latest_forces"]["total_force"][0] == 8.0
    assert len(solver_results["force_coefficients_history"]) == 2
    assert solver_results["force_coefficients_history"][0]["Cd"] == 0.18
    assert solver_results["force_coefficients_history"][1]["Cd"] == 0.12
    assert len(solver_results["forces_history"]) == 2
    assert solver_results["forces_history"][0]["total_force"][0] == 12.0
    assert solver_results["forces_history"][1]["total_force"][0] == 8.0
    assert solver_results["reference_values"]["reference_length_m"] > 0
    assert solver_results["mesh_summary"]["mesh_ok"] is True
    assert solver_results["mesh_summary"]["cells"] == 9342
    assert solver_results["mesh_summary"]["points"] == 10234
    assert solver_results["residual_summary"]["latest_by_field"]["p"]["final_residual"] == 0.00014
    assert solver_results["residual_summary"]["latest_by_field"]["Ux"]["initial_residual"] == 0.00031
    assert len(solver_results["residual_summary"]["history"]) == 8


def test_submarine_solver_dispatch_writes_scientific_verification_artifacts(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-study-results"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "study-results-demo.stl"
    _write_ascii_stl(geometry_path)

    case_dir = workspace_dir / "submarine" / "solver-dispatch" / "study-results-demo" / "openfoam-case"
    fake_sandbox = _FakePostprocessSandbox(case_dir=case_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/study-results-demo.stl",
        task_description="鎵ц科学 verification studies 骞舵眹鎬?verification-json",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command="bash /mnt/user-data/workspace/submarine/solver-dispatch/study-results-demo/openfoam-case/Allrun",
        tool_call_id="tc-dispatch-study-results",
    )

    artifacts = result.update["artifacts"]
    request_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "study-results-demo" / "openfoam-request.json"
    )
    study_manifest_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "study-results-demo" / "study-manifest.json"
    )
    mesh_verification_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "study-results-demo"
        / "verification-mesh-independence.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    study_manifest = json.loads(study_manifest_path.read_text(encoding="utf-8"))
    mesh_verification = json.loads(mesh_verification_path.read_text(encoding="utf-8"))

    assert any(path.endswith("/verification-mesh-independence.json") for path in artifacts)
    assert any(path.endswith("/verification-domain-sensitivity.json") for path in artifacts)
    assert any(path.endswith("/verification-time-step-sensitivity.json") for path in artifacts)
    assert payload["scientific_study_manifest"]["study_execution_status"] == "planned"
    assert any(
        path.endswith("/verification-mesh-independence.json")
        for path in study_manifest["artifact_virtual_paths"]
    )
    assert mesh_verification["study_type"] == "mesh_independence"
    assert mesh_verification["monitored_quantity"] == "Cd"
    assert mesh_verification["status"] == "missing_evidence"
    assert mesh_verification["baseline_value"] == 0.12
    assert mesh_verification["relative_spread"] is None
    assert (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "study-results-demo"
        / "studies"
        / "mesh-independence"
        / "coarse"
        / "solver-results.json"
    ).exists()


def test_submarine_solver_dispatch_executes_scientific_study_variants_when_enabled(
    tmp_path,
    monkeypatch,
):
    paths = Paths(tmp_path)
    thread_id = "thread-study-execution"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "study-execution-demo.stl"
    _write_ascii_stl(geometry_path)

    fake_sandbox = _FakeScientificStudySandbox(workspace_dir=workspace_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/study-execution-demo.stl",
        task_description="执行 baseline 与 scientific study variants 并汇总研究证据",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        execute_scientific_studies=True,
        solver_command="bash /mnt/user-data/workspace/submarine/solver-dispatch/study-execution-demo/openfoam-case/Allrun",
        tool_call_id="tc-dispatch-study-execution",
    )

    artifacts = result.update["artifacts"]
    request_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "study-execution-demo" / "openfoam-request.json"
    )
    study_manifest_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "study-execution-demo" / "study-manifest.json"
    )
    mesh_verification_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "study-execution-demo"
        / "verification-mesh-independence.json"
    )
    domain_verification_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "study-execution-demo"
        / "verification-domain-sensitivity.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    study_manifest = json.loads(study_manifest_path.read_text(encoding="utf-8"))
    mesh_verification = json.loads(mesh_verification_path.read_text(encoding="utf-8"))
    domain_verification = json.loads(domain_verification_path.read_text(encoding="utf-8"))

    assert len(fake_sandbox.commands) == 7
    assert any(path.endswith("/verification-mesh-independence.json") for path in artifacts)
    assert any(path.endswith("/verification-domain-sensitivity.json") for path in artifacts)
    assert any(path.endswith("/verification-time-step-sensitivity.json") for path in artifacts)
    assert payload["scientific_study_manifest"]["study_execution_status"] == "completed"
    assert study_manifest["study_execution_status"] == "completed"
    assert mesh_verification["status"] == "passed"
    assert mesh_verification["relative_spread"] is not None
    assert len(mesh_verification["compared_values"]) == 2
    assert domain_verification["status"] == "blocked"
    assert domain_verification["relative_spread"] is not None
    assert (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "study-execution-demo"
        / "studies"
        / "domain-sensitivity"
        / "compact"
        / "solver-results.json"
    ).exists()
    assert (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "study-execution-demo"
        / "studies"
        / "mesh-independence"
        / "baseline"
        / "solver-results.json"
    ).exists()


def test_submarine_solver_dispatch_exports_requested_postprocess_artifacts(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-ppx"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "ppx.stl"
    _write_ascii_stl(geometry_path)

    case_dir = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "ppx"
        / "openfoam-case"
    )
    fake_sandbox = _FakeRequestedPostprocessSandbox(case_dir=case_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = {
        "current_stage": "task-intelligence",
        "task_summary": "按请求导出压力和尾流结果",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/ppx.stl",
        "geometry_family": "DARPA SUBOFF",
        "selected_case_id": "darpa_suboff_bare_hull_resistance",
        "requested_outputs": [
            {
                "output_id": "surface_pressure_contour",
                "label": "表面压力云图",
                "requested_label": "表面压力云图",
                "status": "requested",
                "support_level": "supported",
                "notes": "当前运行时可在存在后处理文件时导出压力结果 artifact。",
            },
            {
                "output_id": "wake_velocity_slice",
                "label": "尾流速度切片",
                "requested_label": "尾流速度切片",
                "status": "requested",
                "support_level": "supported",
                "notes": "当前运行时可在存在后处理文件时导出尾流结果 artifact。",
            },
        ],
        "review_status": "ready_for_supervisor",
        "next_recommended_stage": "geometry-preflight",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/design-brief/ppx/cfd-design-brief.md",
        "artifact_virtual_paths": [],
        "activity_timeline": [],
    }

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/ppx.stl",
        task_description="执行一轮带请求后处理导出的 OpenFOAM run",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command="bash /mnt/user-data/workspace/submarine/solver-dispatch/ppx/openfoam-case/Allrun",
        tool_call_id="tc-dispatch-postprocess-exports",
    )

    request_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "ppx"
        / "openfoam-request.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    artifacts = result.update["artifacts"]
    artifact_dir = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "ppx"
    )

    assert any(path.endswith("/surface-pressure.csv") for path in artifacts)
    assert any(path.endswith("/surface-pressure.md") for path in artifacts)
    assert any(path.endswith("/surface-pressure.png") for path in artifacts)
    assert any(path.endswith("/wake-velocity-slice.csv") for path in artifacts)
    assert any(path.endswith("/wake-velocity-slice.md") for path in artifacts)
    assert any(path.endswith("/wake-velocity-slice.png") for path in artifacts)
    assert (artifact_dir / "surface-pressure.png").exists()
    assert (artifact_dir / "wake-velocity-slice.png").exists()
    assert payload["output_delivery_plan"][0]["delivery_status"] == "delivered"
    assert payload["output_delivery_plan"][1]["delivery_status"] == "delivered"


def test_submarine_solver_dispatch_applies_user_simulation_requirements(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "requirements-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/requirements-demo.stl",
        task_description="按指定工况准备潜艇阻力分析案例",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        inlet_velocity_mps=7.5,
        fluid_density_kg_m3=998.2,
        kinematic_viscosity_m2ps=8.5e-07,
        end_time_seconds=600.0,
        delta_t_seconds=0.5,
        write_interval_steps=20,
        execute_now=False,
        tool_call_id="tc-dispatch-requirements",
    )

    request_path = outputs_dir / "submarine" / "solver-dispatch" / "requirements-demo" / "openfoam-request.json"
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    case_dir = workspace_dir / "submarine" / "solver-dispatch" / "requirements-demo" / "openfoam-case"
    control_dict = (case_dir / "system" / "controlDict").read_text(encoding="utf-8")
    transport_properties = (case_dir / "constant" / "transportProperties").read_text(encoding="utf-8")
    initial_u = (case_dir / "0" / "U").read_text(encoding="utf-8")
    runtime_state = result.update["submarine_runtime"]

    assert payload["simulation_requirements"]["inlet_velocity_mps"] == 7.5
    assert payload["simulation_requirements"]["fluid_density_kg_m3"] == 998.2
    assert payload["simulation_requirements"]["kinematic_viscosity_m2ps"] == 8.5e-07
    assert payload["simulation_requirements"]["end_time_seconds"] == 600.0
    assert payload["simulation_requirements"]["delta_t_seconds"] == 0.5
    assert payload["simulation_requirements"]["write_interval_steps"] == 20
    assert runtime_state["simulation_requirements"]["end_time_seconds"] == 600.0
    assert "endTime         600.0;" in control_dict
    assert "deltaT          0.5;" in control_dict
    assert "writeInterval   20;" in control_dict
    assert "magUInf         7.5;" in control_dict
    assert "rhoInf          998.2;" in control_dict
    assert "nu              [0 2 -1 0 0 0 0] 8.5e-07;" in transport_properties
    assert "rho             [1 -3 0 0 0 0 0] 998.2;" in transport_properties
    assert "internalField   uniform (7.5 0 0);" in initial_u
    assert "value uniform (7.5 0 0);" in initial_u


def test_submarine_solver_dispatch_inherits_runtime_plan_inputs(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "inherited-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = {
        "current_stage": "task-intelligence",
        "task_summary": "使用已确认设计简报中的基线阻力工况继续推进求解",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/inherited-demo.stl",
        "geometry_family": "DARPA SUBOFF",
        "selected_case_id": "darpa_suboff_bare_hull_resistance",
        "simulation_requirements": {
            "inlet_velocity_mps": 6.5,
            "fluid_density_kg_m3": 997.0,
            "kinematic_viscosity_m2ps": 9.1e-07,
            "end_time_seconds": 400.0,
            "delta_t_seconds": 0.25,
            "write_interval_steps": 40,
        },
        "review_status": "ready_for_supervisor",
        "next_recommended_stage": "geometry-preflight",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/design-brief/inherited-demo/cfd-design-brief.md",
        "artifact_virtual_paths": [
            "/mnt/user-data/outputs/submarine/design-brief/inherited-demo/cfd-design-brief.json"
        ],
    }

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=runtime,
        geometry_path=None,
        task_description="继续推进已确认方案",
        task_type="resistance",
        geometry_family_hint=None,
        selected_case_id=None,
        inlet_velocity_mps=None,
        fluid_density_kg_m3=None,
        kinematic_viscosity_m2ps=None,
        end_time_seconds=None,
        delta_t_seconds=None,
        write_interval_steps=None,
        execute_now=False,
        tool_call_id="tc-dispatch-inherited",
    )

    request_path = outputs_dir / "submarine" / "solver-dispatch" / "inherited-demo" / "openfoam-request.json"
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    case_dir = workspace_dir / "submarine" / "solver-dispatch" / "inherited-demo" / "openfoam-case"
    control_dict = (case_dir / "system" / "controlDict").read_text(encoding="utf-8")
    transport_properties = (case_dir / "constant" / "transportProperties").read_text(encoding="utf-8")
    initial_u = (case_dir / "0" / "U").read_text(encoding="utf-8")

    assert payload["selected_case"]["case_id"] == "darpa_suboff_bare_hull_resistance"
    assert payload["geometry"]["geometry_family"] == "DARPA SUBOFF"
    assert payload["simulation_requirements"]["inlet_velocity_mps"] == 6.5
    assert payload["simulation_requirements"]["fluid_density_kg_m3"] == 997.0
    assert payload["simulation_requirements"]["kinematic_viscosity_m2ps"] == 9.1e-07
    assert payload["simulation_requirements"]["end_time_seconds"] == 400.0
    assert payload["simulation_requirements"]["delta_t_seconds"] == 0.25
    assert payload["simulation_requirements"]["write_interval_steps"] == 40
    assert "endTime         400.0;" in control_dict
    assert "deltaT          0.25;" in control_dict
    assert "writeInterval   40;" in control_dict
    assert "magUInf         6.5;" in control_dict
    assert "rhoInf          997.0;" in control_dict
    assert "nu              [0 2 -1 0 0 0 0] 9.1e-07;" in transport_properties
    assert "rho             [1 -3 0 0 0 0 0] 997.0;" in transport_properties
    assert "internalField   uniform (6.5 0 0);" in initial_u
    assert "value uniform (6.5 0 0);" in initial_u
    assert result.update["submarine_runtime"]["simulation_requirements"]["delta_t_seconds"] == 0.25
