import importlib
import inspect
import json
import os
import struct
import threading
import time
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


def _write_binary_stl(
    path: Path,
    triangles: list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]],
) -> None:
    header = b"binary-stl".ljust(80, b" ")
    payload = bytearray(header)
    payload.extend(struct.pack("<I", len(triangles)))
    for triangle in triangles:
        payload.extend(struct.pack("<3f", 0.0, 0.0, 0.0))
        for vertex in triangle:
            payload.extend(struct.pack("<3f", *vertex))
        payload.extend(struct.pack("<H", 0))
    path.write_bytes(bytes(payload))


def _binary_stl_bounds(path: Path) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    raw = path.read_bytes()
    triangle_count = struct.unpack("<I", raw[80:84])[0]
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    for index in range(triangle_count):
        start = 84 + index * 50
        values = struct.unpack("<12fH", raw[start : start + 50])
        points = values[3:12]
        for point_index in range(0, 9, 3):
            x, y, z = points[point_index : point_index + 3]
            mins[0] = min(mins[0], x)
            mins[1] = min(mins[1], y)
            mins[2] = min(mins[2], z)
            maxs[0] = max(maxs[0], x)
            maxs[1] = max(maxs[1], y)
            maxs[2] = max(maxs[2], z)
    return (tuple(mins), tuple(maxs))


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


def _execution_plan_status(runtime_state: dict, role_id: str) -> str:
    return next(
        item["status"]
        for item in runtime_state["execution_plan"]
        if item["role_id"] == role_id
    )


class _FakeSandbox:
    def __init__(self, output: str = "OpenFOAM run simulated\nEnd") -> None:
        self.commands: list[str] = []
        self.output = output

    def execute_command(self, command: str) -> str:
        self.commands.append(command)
        return self.output


class _FakeTruncatedLogSandbox(_FakeSandbox):
    def __init__(self, case_dir: Path) -> None:
        super().__init__(
            output="\n".join(
                [
                    "[submarine-cfd] Running snappyHexMesh",
                    "feature points : 15",
                    "After introducing baffles : cells:194190  faces:742391  poi",
                    "[... Observation truncated due to length ...]",
                    "Time = 200",
                    "End",
                ]
            )
        )
        self.case_dir = case_dir

    def execute_command(self, command: str) -> str:
        case_dir = _platform_fs_path(self.case_dir)
        case_dir.mkdir(parents=True, exist_ok=True)
        raw_log_path = case_dir / ".deerflow-raw-command.log"
        raw_log_path.write_text(
            "\n".join(
                [
                    "[submarine-cfd] Extracting features",
                    "Initial feature set:",
                    "    feature points : 15",
                    "Mesh Information",
                    "  nPoints: 136161",
                    "  nCells: 128000",
                    "  nFaces: 392000",
                    "  nInternalFaces: 376000",
                    "After introducing baffles : cells:194190  faces:674559  points:249525",
                    "After introducing baffles : cells:194190  faces:742391  points:249525",
                    "[submarine-cfd] Checking mesh",
                    "Mesh OK.",
                    "Time = 200",
                    "smoothSolver:  Solving for Ux, Initial residual = 3e-04, Final residual = 3e-08, No Iterations 2",
                    "GAMG:  Solving for p, Initial residual = 0.012, Final residual = 1.4e-04, No Iterations 5",
                    "ExecutionTime = 18.1 s  ClockTime = 19 s",
                    "End",
                ]
            ),
            encoding="utf-8",
        )
        return super().execute_command(command)


class _FakeProvider:
    def __init__(self, sandbox: _FakeSandbox) -> None:
        self.sandbox = sandbox

    def acquire(self, thread_id: str | None = None) -> str:
        return "local"

    def get(self, sandbox_id: str):
        return self.sandbox if sandbox_id == "local" else None

    def release(self, sandbox_id: str) -> None:
        return None


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


class _FakeAsyncCompletionSandbox(_FakeSandbox):
    def __init__(self, case_dir: Path, delay_seconds: float = 0.05) -> None:
        super().__init__(
            output="\n".join(
                [
                    "[submarine-cfd] Running snappyHexMesh",
                    "[... Observation truncated due to length ...]",
                ]
            )
        )
        self.case_dir = case_dir
        self.delay_seconds = delay_seconds

    def execute_command(self, command: str) -> str:
        case_dir = _platform_fs_path(self.case_dir)
        case_dir.mkdir(parents=True, exist_ok=True)
        raw_log_path = case_dir / ".deerflow-raw-command.log"
        status_path = case_dir / ".deerflow-command-exit-status"
        status_path.unlink(missing_ok=True)
        raw_log_path.write_text(
            "\n".join(
                [
                    "[submarine-cfd] Preparing background mesh",
                    "Create time",
                    "[submarine-cfd] Running snappyHexMesh",
                ]
            ),
            encoding="utf-8",
        )

        def _finish_run() -> None:
            time.sleep(self.delay_seconds)

            coeffs_dir = case_dir / "postProcessing" / "forceCoeffsHull" / "0"
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
            forces_dir = case_dir / "postProcessing" / "forcesHull" / "0"
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
            raw_log_path.write_text(
                "\n".join(
                    [
                        "[submarine-cfd] Preparing background mesh",
                        "Mesh Information",
                        "  nPoints: 10234",
                        "  nCells: 9342",
                        "  nFaces: 28764",
                        "  nInternalFaces: 27654",
                        "[submarine-cfd] Checking mesh",
                        "Mesh OK.",
                        "[submarine-cfd] Solving with simpleFoam",
                        "Time = 0",
                        "smoothSolver:  Solving for Ux, Initial residual = 0.02, Final residual = 1e-05, No Iterations 2",
                        "GAMG:  Solving for p, Initial residual = 0.3, Final residual = 0.002, No Iterations 6",
                        "Time = 200",
                        "smoothSolver:  Solving for Ux, Initial residual = 0.00031, Final residual = 3e-08, No Iterations 2",
                        "GAMG:  Solving for p, Initial residual = 0.012, Final residual = 0.00014, No Iterations 5",
                        "ExecutionTime = 18.1 s  ClockTime = 19 s",
                        "End",
                    ]
                ),
                encoding="utf-8",
            )
            status_path.write_text("0", encoding="utf-8")

        threading.Thread(target=_finish_run, daemon=True).start()
        return super().execute_command(command)


class _FakeExitStatusAheadOfLogCompletionSandbox(_FakeSandbox):
    def __init__(self, case_dir: Path, delay_seconds: float = 0.05) -> None:
        super().__init__(
            output="\n".join(
                [
                    "[submarine-cfd] Running snappyHexMesh",
                    "[... Observation truncated due to length ...]",
                ]
            )
        )
        self.case_dir = case_dir
        self.delay_seconds = delay_seconds

    def execute_command(self, command: str) -> str:
        case_dir = _platform_fs_path(self.case_dir)
        case_dir.mkdir(parents=True, exist_ok=True)
        raw_log_path = case_dir / ".deerflow-raw-command.log"
        status_path = case_dir / ".deerflow-command-exit-status"
        status_path.write_text("0", encoding="utf-8")
        raw_log_path.write_text(
            "\n".join(
                [
                    "[submarine-cfd] Preparing background mesh",
                    "Mesh Information",
                    "  nPoints: 10234",
                    "  nCells: 9342",
                    "  nFaces: 28764",
                    "  nInternalFaces: 27654",
                    "[submarine-cfd] Solving with simpleFoam",
                    "Time = 150s",
                    "smoothSolver:  Solving for Ux, Initial residual = 8e-09, Final residual = 8e-09, No Iterations 0",
                    "GAMG:  Solving for p, Initial residual = 5e-07, Final residual = 2e-08, No Iterations 1",
                    "ExecutionTime = 66.9 s  ClockTime = 171 s",
                ]
            ),
            encoding="utf-8",
        )

        def _finish_run() -> None:
            time.sleep(self.delay_seconds)

            coeffs_dir = case_dir / "postProcessing" / "forceCoeffsHull" / "0"
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
            forces_dir = case_dir / "postProcessing" / "forcesHull" / "0"
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
            raw_log_path.write_text(
                "\n".join(
                    [
                        "[submarine-cfd] Preparing background mesh",
                        "Mesh Information",
                        "  nPoints: 10234",
                        "  nCells: 9342",
                        "  nFaces: 28764",
                        "  nInternalFaces: 27654",
                        "[submarine-cfd] Solving with simpleFoam",
                        "Time = 150s",
                        "smoothSolver:  Solving for Ux, Initial residual = 8e-09, Final residual = 8e-09, No Iterations 0",
                        "GAMG:  Solving for p, Initial residual = 5e-07, Final residual = 2e-08, No Iterations 1",
                        "ExecutionTime = 66.9 s  ClockTime = 171 s",
                        "Time = 200s",
                        "smoothSolver:  Solving for Ux, Initial residual = 2e-09, Final residual = 2e-09, No Iterations 0",
                        "GAMG:  Solving for p, Initial residual = 1.5e-07, Final residual = 8e-09, No Iterations 1",
                        "ExecutionTime = 86.2 s  ClockTime = 92 s",
                        "End",
                    ]
                ),
                encoding="utf-8",
            )

        threading.Thread(target=_finish_run, daemon=True).start()
        return super().execute_command(command)


class _FakePreprocessEndAsyncCompletionSandbox(_FakeSandbox):
    def __init__(self, case_dir: Path, delay_seconds: float = 0.05) -> None:
        super().__init__(
            output="\n".join(
                [
                    "[submarine-cfd] Running snappyHexMesh",
                    "[... Observation truncated due to length ...]",
                ]
            )
        )
        self.case_dir = case_dir
        self.delay_seconds = delay_seconds

    def execute_command(self, command: str) -> str:
        case_dir = _platform_fs_path(self.case_dir)
        case_dir.mkdir(parents=True, exist_ok=True)
        raw_log_path = case_dir / ".deerflow-raw-command.log"
        status_path = case_dir / ".deerflow-command-exit-status"
        status_path.unlink(missing_ok=True)
        raw_log_path.write_text(
            "\n".join(
                [
                    "[submarine-cfd] Extracting features",
                    "ExecutionTime = 0.110134 s  ClockTime = 0 s",
                    "End",
                    "[submarine-cfd] Running snappyHexMesh",
                    "Mesh snapped in = 23.862714 s.",
                    "Checking final mesh ...",
                    "End",
                    "Time = 0s",
                    "smoothSolver:  Solving for Ux, Initial residual = 0.02, Final residual = 1e-05, No Iterations 2",
                ]
            ),
            encoding="utf-8",
        )

        def _finish_run() -> None:
            time.sleep(self.delay_seconds)

            coeffs_dir = case_dir / "postProcessing" / "forceCoeffsHull" / "0"
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
            forces_dir = case_dir / "postProcessing" / "forcesHull" / "0"
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
            raw_log_path.write_text(
                "\n".join(
                    [
                        "[submarine-cfd] Extracting features",
                        "ExecutionTime = 0.110134 s  ClockTime = 0 s",
                        "End",
                        "[submarine-cfd] Running snappyHexMesh",
                        "Mesh snapped in = 23.862714 s.",
                        "Checking final mesh ...",
                        "End",
                        "Time = 0s",
                        "smoothSolver:  Solving for Ux, Initial residual = 0.02, Final residual = 1e-05, No Iterations 2",
                        "GAMG:  Solving for p, Initial residual = 0.3, Final residual = 0.002, No Iterations 6",
                        "Time = 200s",
                        "smoothSolver:  Solving for Ux, Initial residual = 0.00031, Final residual = 3e-08, No Iterations 2",
                        "GAMG:  Solving for p, Initial residual = 0.012, Final residual = 0.00014, No Iterations 5",
                        "ExecutionTime = 18.1 s  ClockTime = 19 s",
                        "End",
                    ]
                ),
                encoding="utf-8",
            )
            status_path.write_text("0", encoding="utf-8")

        threading.Thread(target=_finish_run, daemon=True).start()
        return super().execute_command(command)


class _FakeMeshOnlySandbox(_FakeSandbox):
    def __init__(self, case_dir: Path) -> None:
        super().__init__(
            output="\n".join(
                [
                    "[submarine-cfd] Running snappyHexMesh",
                    "[... Observation truncated due to length ...]",
                ]
            )
        )
        self.case_dir = case_dir

    def execute_command(self, command: str) -> str:
        case_dir = _platform_fs_path(self.case_dir)
        case_dir.mkdir(parents=True, exist_ok=True)
        raw_log_path = case_dir / ".deerflow-raw-command.log"
        status_path = case_dir / ".deerflow-command-exit-status"
        raw_log_path.write_text(
            "\n".join(
                [
                    "[submarine-cfd] Preparing background mesh",
                    "Mesh Information",
                    "  nPoints: 10234",
                    "  nCells: 9342",
                    "  nFaces: 28764",
                    "  nInternalFaces: 27654",
                    "[submarine-cfd] Running snappyHexMesh",
                ]
            ),
            encoding="utf-8",
        )
        status_path.write_text("0", encoding="utf-8")
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
            "/studies/mesh-independence/coarse/openfoam-case/Allrun": 0.1212,
            "/studies/mesh-independence/fine/openfoam-case/Allrun": 0.1194,
            "/studies/domain-sensitivity/compact/openfoam-case/Allrun": 0.1290,
            "/studies/domain-sensitivity/expanded/openfoam-case/Allrun": 0.1110,
            "/studies/time-step-sensitivity/coarse/openfoam-case/Allrun": 0.1208,
            "/studies/time-step-sensitivity/fine/openfoam-case/Allrun": 0.1196,
            "/openfoam-case/Allrun": 0.1200,
        }

    def _resolve_case_dir(self, command: str) -> tuple[Path, float]:
        normalized_command = command.strip()
        if normalized_command.startswith("(") and ") > " in normalized_command:
            normalized_command = normalized_command[1:].split(") > ", maxsplit=1)[0]
        for fragment, cd_value in self.cd_by_command_fragment.items():
            if fragment in normalized_command:
                marker = "/submarine/solver-dispatch/"
                fragment_index = normalized_command.index(fragment)
                marker_index = normalized_command.rfind(marker, 0, fragment_index)
                if marker_index < 0:
                    break
                relative_prefix = normalized_command[
                    marker_index + len(marker) : fragment_index
                ].strip("/")
                run_dir_name = relative_prefix.split("/", maxsplit=1)[0]
                case_relative = fragment.lstrip("/").removesuffix("/Allrun")
                return (
                    self.workspace_dir
                    / "submarine"
                    / "solver-dispatch"
                    / run_dir_name
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


class _FakeProgressiveScientificStudySandbox(_FakeScientificStudySandbox):
    def __init__(
        self,
        workspace_dir: Path,
        *,
        delayed_fragment: str = "/studies/mesh-independence/fine/openfoam-case/Allrun",
    ) -> None:
        super().__init__(workspace_dir=workspace_dir)
        self.delayed_fragment = delayed_fragment

    def _write_completed_case_outputs(self, case_dir: Path, cd_value: float) -> None:
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

    def execute_command(self, command: str) -> str:
        if self.delayed_fragment not in command:
            return super().execute_command(command)

        case_dir, cd_value = self._resolve_case_dir(command)
        case_dir = _platform_fs_path(case_dir)
        case_dir.mkdir(parents=True, exist_ok=True)
        raw_log_path = case_dir / ".deerflow-raw-command.log"
        status_path = case_dir / ".deerflow-command-exit-status"
        status_path.unlink(missing_ok=True)
        raw_log_path.write_text(
            "\n".join(
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
                ]
            ),
            encoding="utf-8",
        )

        def _write_progressive_log() -> None:
            progress_frames = [
                (
                    0.04,
                    [
                        "Time = 50",
                        "smoothSolver:  Solving for Ux, Initial residual = 0.004, Final residual = 4e-06, No Iterations 2",
                        "GAMG:  Solving for p, Initial residual = 0.04, Final residual = 0.0005, No Iterations 5",
                    ],
                ),
                (
                    0.08,
                    [
                        "Time = 100",
                        "smoothSolver:  Solving for Ux, Initial residual = 0.0008, Final residual = 8e-07, No Iterations 2",
                        "GAMG:  Solving for p, Initial residual = 0.02, Final residual = 0.0002, No Iterations 5",
                    ],
                ),
                (
                    0.12,
                    [
                        "Time = 150",
                        "smoothSolver:  Solving for Ux, Initial residual = 0.0004, Final residual = 4e-08, No Iterations 2",
                        "GAMG:  Solving for p, Initial residual = 0.015, Final residual = 0.00014, No Iterations 5",
                    ],
                ),
            ]
            started_at = time.monotonic()
            base_lines = raw_log_path.read_text(encoding="utf-8").splitlines()
            for delay_seconds, frame_lines in progress_frames:
                remaining = delay_seconds - (time.monotonic() - started_at)
                if remaining > 0:
                    time.sleep(remaining)
                raw_log_path.write_text(
                    "\n".join([*base_lines, *frame_lines]),
                    encoding="utf-8",
                )
                base_lines.extend(frame_lines)

            remaining = 0.16 - (time.monotonic() - started_at)
            if remaining > 0:
                time.sleep(remaining)
            self._write_completed_case_outputs(case_dir, cd_value)
            base_lines.extend(
                [
                    "Time = 200",
                    "smoothSolver:  Solving for Ux, Initial residual = 0.00031, Final residual = 3e-08, No Iterations 2",
                    "smoothSolver:  Solving for k, Initial residual = 0.004, Final residual = 8e-07, No Iterations 2",
                    "smoothSolver:  Solving for omega, Initial residual = 0.008, Final residual = 9e-07, No Iterations 2",
                    "GAMG:  Solving for p, Initial residual = 0.012, Final residual = 0.00014, No Iterations 5",
                    "ExecutionTime = 18.1 s  ClockTime = 19 s",
                    "End",
                ]
            )
            raw_log_path.write_text("\n".join(base_lines), encoding="utf-8")
            status_path.write_text("0", encoding="utf-8")

        threading.Thread(target=_write_progressive_log, daemon=True).start()
        self.commands.append(command)
        return "\n".join(
            [
                "[submarine-cfd] Running snappyHexMesh",
                "[... Observation truncated due to length ...]",
            ]
        )


def test_submarine_solver_dispatch_tool_generates_artifacts(tmp_path, monkeypatch):
    paths = Paths(tmp_path)
    thread_id = "thread-1"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "type209-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.delenv("DEER_FLOW_RUNTIME_PROFILE", raising=False)
    monkeypatch.delenv("DEER_FLOW_DOCKER_SOCKET", raising=False)
    monkeypatch.delenv("DEER_FLOW_HOST_BASE_DIR", raising=False)
    monkeypatch.delenv("DEER_FLOW_HOST_SKILLS_PATH", raising=False)
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
    assert any(path.endswith("/provenance-manifest.json") for path in artifacts)

    json_path = outputs_dir / "submarine" / "solver-dispatch" / "type209-demo" / "openfoam-request.json"
    md_path = outputs_dir / "submarine" / "solver-dispatch" / "type209-demo" / "dispatch-summary.md"
    provenance_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "type209-demo" / "provenance-manifest.json"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    provenance_manifest = json.loads(provenance_path.read_text(encoding="utf-8"))

    assert payload["dispatch_status"] == "planned"
    assert payload["execution_readiness"] == "stl_ready"
    assert payload["geometry"]["geometry_family"] == "Type 209"
    assert payload["selected_case"]["case_id"]
    assert payload["provenance_manifest_virtual_path"].endswith("/provenance-manifest.json")
    assert payload["provenance_summary"]["manifest_virtual_path"].endswith(
        "/provenance-manifest.json"
    )
    assert payload["provenance_summary"]["manifest_completeness_status"] == "complete"
    assert payload["environment_parity_assessment"]["parity_status"] == "matched"
    assert provenance_manifest["task_type"] == "resistance"
    assert provenance_manifest["environment_parity_assessment"]["parity_status"] == (
        "matched"
    )
    assert provenance_manifest["artifact_entrypoints"]["request"].endswith(
        "/openfoam-request.json"
    )
    assert provenance_manifest["artifact_entrypoints"]["dispatch_summary_markdown"].endswith(
        "/dispatch-summary.md"
    )
    assert "solver_results" not in provenance_manifest["artifact_entrypoints"]
    assert md_path.exists()
    message = result.update["messages"][0].content
    assert "研究产物" in message
    assert "DeerFlow artifacts" not in message


def test_submarine_solver_dispatch_marks_drifted_but_runnable_environment_parity(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-parity-drift"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "parity-drift.stl"
    _write_ascii_stl(geometry_path)

    fake_socket = tmp_path / "fake-docker.sock"
    fake_socket.write_text("", encoding="utf-8")

    monkeypatch.setenv("DEER_FLOW_RUNTIME_PROFILE", "docker_compose_dev")
    monkeypatch.setenv("DEER_FLOW_DOCKER_SOCKET", str(fake_socket))
    monkeypatch.delenv("DEER_FLOW_HOST_BASE_DIR", raising=False)
    monkeypatch.delenv("DEER_FLOW_HOST_SKILLS_PATH", raising=False)
    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/parity-drift.stl",
        task_description="Exercise provenance parity drift reporting",
        task_type="resistance",
        geometry_family_hint="Type 209",
        execute_now=False,
        tool_call_id="tc-dispatch-parity-drift",
    )

    payload = result.update["submarine_runtime"]
    provenance_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "parity-drift"
        / "provenance-manifest.json"
    )
    provenance_manifest = json.loads(provenance_path.read_text(encoding="utf-8"))

    assert payload["environment_parity_assessment"]["parity_status"] == (
        "drifted_but_runnable"
    )
    assert payload["provenance_summary"]["parity_status"] == "drifted_but_runnable"
    assert provenance_manifest["environment_parity_assessment"]["parity_status"] == (
        "drifted_but_runnable"
    )
    assert "environment_parity_assessment" in provenance_manifest
    assert any(
        "Host mount strategy" in item
        for item in provenance_manifest["environment_parity_assessment"]["drift_reasons"]
    )


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
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "suboff-demo.stl"
    _write_ascii_stl(geometry_path)

    case_dir = workspace_dir / "submarine" / "solver-dispatch" / "suboff-demo" / "openfoam-case"
    fake_sandbox = _FakePostprocessSandbox(case_dir=case_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(
        tool_module,
        "get_sandbox_provider",
        lambda: _FakeProvider(fake_sandbox),
    )

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

    assert len(fake_sandbox.commands) == 1
    assert "echo run-openfoam" in fake_sandbox.commands[0]
    assert log_path.exists()
    assert "Time = 200" in log_path.read_text(encoding="utf-8")
    assert payload["dispatch_status"] == "executed"
    assert payload["request_virtual_path"].endswith("/openfoam-request.json")
    assert payload["execution_log_virtual_path"].endswith("/openfoam-run.log")
    assert any(path.endswith("/openfoam-run.log") for path in result.update["artifacts"])


def test_submarine_solver_dispatch_tool_prefers_workspace_raw_log_when_command_output_is_truncated(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-truncated-openfoam-log"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "suboff-demo.stl"
    _write_ascii_stl(geometry_path)

    case_dir = (
        workspace_dir / "submarine" / "solver-dispatch" / "suboff-demo" / "openfoam-case"
    )
    fake_sandbox = _FakeTruncatedLogSandbox(case_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(
        tool_module,
        "get_sandbox_provider",
        lambda: _FakeProvider(fake_sandbox),
    )

    tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/suboff-demo.stl",
        task_description="在截断日志场景下继续执行受控 OpenFOAM 调度",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command="echo run-openfoam",
        tool_call_id="tc-dispatch-truncated-log",
    )

    request_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "suboff-demo" / "openfoam-request.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))

    assert payload["solver_results"]["mesh_summary"]["mesh_ok"] is True
    assert payload["solver_results"]["mesh_summary"]["cells"] == 194190
    assert payload["solver_results"]["mesh_summary"]["faces"] == 742391
    assert payload["solver_results"]["mesh_summary"]["points"] == 249525


def test_submarine_solver_dispatch_tool_lazily_acquires_sandbox_for_execute_now(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-lazy-sandbox"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "lazy-sandbox.stl"
    _write_ascii_stl(geometry_path)

    case_dir = (
        workspace_dir / "submarine" / "solver-dispatch" / "lazy-sandbox" / "openfoam-case"
    )
    fake_sandbox = _FakePostprocessSandbox(case_dir=case_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(
        tool_module,
        "get_sandbox_provider",
        lambda: _FakeProvider(fake_sandbox),
    )

    runtime = _make_runtime(paths, thread_id)
    runtime.state.pop("sandbox", None)

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/lazy-sandbox.stl",
        task_description="直接执行一个 OpenFOAM 适配命令",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command="echo lazy-sandbox-ok",
        tool_call_id="tc-dispatch-lazy-sandbox",
    )

    json_path = outputs_dir / "submarine" / "solver-dispatch" / "lazy-sandbox" / "openfoam-request.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert runtime.state["sandbox"]["sandbox_id"] == "local"
    assert len(fake_sandbox.commands) == 1
    assert "echo lazy-sandbox-ok" in fake_sandbox.commands[0]
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
    assert runtime_state["runtime_status"] == "ready"
    assert runtime_state["runtime_summary"]
    assert runtime_state["recovery_guidance"] is None
    assert runtime_state["blocker_detail"] is None
    assert _execution_plan_status(runtime_state, "geometry-preflight") == "completed"
    assert _execution_plan_status(runtime_state, "solver-dispatch") == "in_progress"
    assert _execution_plan_status(runtime_state, "scientific-study") == "ready"
    assert _execution_plan_status(runtime_state, "experiment-compare") == "pending"
    assert _execution_plan_status(runtime_state, "scientific-verification") == "completed"
    assert _execution_plan_status(runtime_state, "scientific-followup") == "pending"
    assert runtime_state["workspace_case_dir_virtual_path"].endswith("/openfoam-case")
    assert runtime_state["run_script_virtual_path"].endswith("/Allrun")
    assert runtime_state["request_virtual_path"].endswith("/openfoam-request.json")
    assert runtime_state["provenance_manifest_virtual_path"].endswith(
        "/provenance-manifest.json"
    )
    assert runtime_state["provenance_summary"]["manifest_virtual_path"].endswith(
        "/provenance-manifest.json"
    )
    assert runtime_state["provenance_summary"]["manifest_completeness_status"] == "complete"
    assert runtime_state["environment_fingerprint"]["runtime_origin"] == "unit_test"
    assert runtime_state["environment_parity_assessment"]["parity_status"] == "matched"
    assert runtime_state["execution_log_virtual_path"] is None
    assert runtime_state["solver_results_virtual_path"] is None
    assert runtime_state["supervisor_handoff_virtual_path"].endswith("/supervisor-handoff.json")
    assert len(runtime_state["activity_timeline"]) == 2
    assert runtime_state["activity_timeline"][-1]["stage"] == "solver-dispatch"
    assert runtime_state["activity_timeline"][-1]["actor"] == "solver-dispatch"


def test_submarine_solver_dispatch_execute_now_overrides_existing_plan_only_preference(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-execute-now-override"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "execute-now-override.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = {
        "current_stage": "solver-dispatch",
        "task_summary": "沿当前方案继续推进",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/execute-now-override.stl",
        "execution_preference": "plan_only",
        "review_status": "ready_for_supervisor",
        "next_recommended_stage": "solver-dispatch",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/design-brief/execute-now-override/cfd-design-brief.md",
        "artifact_virtual_paths": [
            "/mnt/user-data/outputs/submarine/design-brief/execute-now-override/cfd-design-brief.json"
        ],
    }

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/execute-now-override.stl",
        task_description="请按当前已经确认或已规划好的潜艇 CFD 方案开始实际求解执行。",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        tool_call_id="tc-dispatch-execute-now-override",
    )

    runtime_state = result.update["submarine_runtime"]
    json_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "execute-now-override"
        / "openfoam-request.json"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert payload["execution_preference"] == "execute_now"
    assert runtime_state["execution_preference"] == "execute_now"


def test_submarine_solver_dispatch_marks_failed_runtime_when_solver_execution_fails(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-runtime-failed"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "runtime-failed.stl"
    _write_ascii_stl(geometry_path)

    fake_sandbox = _FakeSandbox(output="FOAM FATAL ERROR: divergence detected")

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/runtime-failed.stl",
        task_description="Execute and surface the solver failure state",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command="echo failing-run",
        tool_call_id="tc-dispatch-runtime-failed",
    )

    runtime_state = result.update["submarine_runtime"]

    assert runtime_state["stage_status"] == "failed"
    assert runtime_state["runtime_status"] == "failed"
    assert runtime_state["execution_log_virtual_path"].endswith("/openfoam-run.log")
    assert runtime_state["request_virtual_path"].endswith("/openfoam-request.json")
    assert runtime_state["recovery_guidance"]
    assert runtime_state["blocker_detail"]


def test_submarine_solver_dispatch_surfaces_blocked_runtime_when_canonical_results_are_missing(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-runtime-blocked"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "runtime-blocked.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    blocked_payload = {
        "selected_case": {"case_id": "darpa_suboff_bare_hull_resistance"},
        "dispatch_status": "executed",
        "execution_readiness": "stl_ready",
        "simulation_requirements": {"inlet_velocity_mps": 5.0},
        "requested_outputs": [],
        "output_delivery_plan": [],
        "workspace_case_dir_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/runtime-blocked/openfoam-case",
        "run_script_virtual_path": "/mnt/user-data/workspace/submarine/solver-dispatch/runtime-blocked/openfoam-case/Allrun",
        "request_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/runtime-blocked/openfoam-request.json",
        "execution_log_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/runtime-blocked/openfoam-run.log",
        "solver_results_virtual_path": None,
        "supervisor_handoff_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/runtime-blocked/supervisor-handoff.json",
        "next_recommended_stage": "result-reporting",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/runtime-blocked/dispatch-summary.md",
        "artifact_virtual_paths": [
            "/mnt/user-data/outputs/submarine/solver-dispatch/runtime-blocked/openfoam-request.json",
            "/mnt/user-data/outputs/submarine/solver-dispatch/runtime-blocked/openfoam-run.log",
            "/mnt/user-data/outputs/submarine/solver-dispatch/runtime-blocked/dispatch-summary.md",
            "/mnt/user-data/outputs/submarine/solver-dispatch/runtime-blocked/supervisor-handoff.json",
        ],
        "review_status": "ready_for_supervisor",
        "summary_zh": "求解命令已经跑完，但 solver-results 证据没有成功注册回线程。",
        "geometry": {"geometry_family": "DARPA SUBOFF"},
    }

    monkeypatch.setattr(
        tool_module,
        "run_solver_dispatch",
        lambda **_: (blocked_payload, blocked_payload["artifact_virtual_paths"]),
    )

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/runtime-blocked.stl",
        task_description="Simulate a refreshable blocked dispatch payload",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=False,
        tool_call_id="tc-dispatch-runtime-blocked",
    )

    runtime_state = result.update["submarine_runtime"]

    assert runtime_state["stage_status"] == "executed"
    assert runtime_state["runtime_status"] == "blocked"
    assert runtime_state["request_virtual_path"].endswith("/openfoam-request.json")
    assert runtime_state["execution_log_virtual_path"].endswith("/openfoam-run.log")
    assert runtime_state["report_virtual_path"].endswith("/dispatch-summary.md")
    assert runtime_state["supervisor_handoff_virtual_path"].endswith("/supervisor-handoff.json")
    assert runtime_state["blocker_detail"] == (
        "solver-dispatch 缺少可恢复的关键证据: 求解结果。"
    )
    assert runtime_state["recovery_guidance"]


def test_submarine_solver_dispatch_recovers_geometry_from_uploaded_files_without_explicit_path(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-uploaded-files-dispatch"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "uploaded-files-dispatch.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["uploaded_files"] = [
        {
            "filename": "uploaded-files-dispatch.stl",
            "path": "/mnt/user-data/uploads/uploaded-files-dispatch.stl",
        }
    ]

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=runtime,
        geometry_path=None,
        task_description="继续推进当前线程里已经上传好的阻力基线案例。",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=False,
        tool_call_id="tc-dispatch-uploaded-files",
    )

    request_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "uploaded-files-dispatch"
        / "openfoam-request.json"
    )
    handoff_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "uploaded-files-dispatch"
        / "supervisor-handoff.json"
    )
    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    runtime_state = result.update["submarine_runtime"]

    assert request_path.exists()
    assert handoff["uploaded_geometry_path"] == "/mnt/user-data/uploads/uploaded-files-dispatch.stl"
    assert runtime_state["geometry_virtual_path"] == "/mnt/user-data/uploads/uploaded-files-dispatch.stl"


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


def test_submarine_solver_dispatch_uses_geometry_scaled_domain_for_small_hulls(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-small-hull-domain"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "small-hull-domain.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/small-hull-domain.stl",
        task_description="Prepare a meter-scale SUBOFF baseline case without inflating the domain floor beyond the hull scale.",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=False,
        tool_call_id="tc-dispatch-small-hull-domain",
    )

    block_mesh_dict = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "small-hull-domain"
        / "openfoam-case"
        / "system"
        / "blockMeshDict"
    ).read_text(encoding="utf-8")

    assert "(-16" in block_mesh_dict
    assert "(32.0 " in block_mesh_dict
    assert "(-40" not in block_mesh_dict


def test_submarine_solver_dispatch_applies_geometry_scale_factor_to_case_geometry(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-scaled-case"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "scaled-case.stl"
    geometry_path.write_text(
        "\n".join(
            [
                "solid scaled-case",
                "facet normal 0 0 0",
                "  outer loop",
                "    vertex 0 0 0",
                "    vertex 4356 0 0",
                "    vertex 0 508 0",
                "  endloop",
                "endfacet",
                "facet normal 0 0 0",
                "  outer loop",
                "    vertex 4356 0 0",
                "    vertex 4356 508 0",
                "    vertex 0 508 0",
                "  endloop",
                "endfacet",
                "endsolid scaled-case",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = {
        "current_stage": "geometry-preflight",
        "task_summary": "Scale the uploaded SUBOFF STL before generating the solver case.",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/scaled-case.stl",
        "geometry_family": "DARPA SUBOFF",
        "scale_assessment": {
            "raw_length_value": 4356.0,
            "normalized_length_m": 4.356,
            "applied_scale_factor": 0.001,
            "heuristic": "divide_by_1000_mm_to_m",
            "severity": "severe",
            "summary_zh": "Geometry scale requires confirmation.",
        },
    }

    tool_module.submarine_solver_dispatch_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/scaled-case.stl",
        task_description="Prepare the solver case using the confirmed meter-scale geometry.",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=False,
        tool_call_id="tc-dispatch-scaled-case",
    )

    scaled_geometry = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "scaled-case"
        / "openfoam-case"
        / "constant"
        / "triSurface"
        / "scaled-case.stl"
    ).read_text(encoding="utf-8")

    assert "vertex 4.356" in scaled_geometry
    assert "0.508" in scaled_geometry
    assert "vertex 4356 " not in scaled_geometry


def test_submarine_solver_dispatch_applies_geometry_scale_factor_to_binary_case_geometry(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-scaled-binary-case"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "scaled-binary-case.stl"
    _write_binary_stl(
        geometry_path,
        [
            ((0.0, 0.0, 0.0), (4356.0, 0.0, 0.0), (0.0, 508.0, 0.0)),
            ((4356.0, 0.0, 0.0), (4356.0, 508.0, 0.0), (0.0, 508.0, 0.0)),
        ],
    )

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)

    runtime = _make_runtime(paths, thread_id)
    runtime.state["submarine_runtime"] = {
        "current_stage": "geometry-preflight",
        "task_summary": "Scale the uploaded binary SUBOFF STL before generating the solver case.",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/scaled-binary-case.stl",
        "geometry_family": "DARPA SUBOFF",
        "scale_assessment": {
            "raw_length_value": 4356.0,
            "normalized_length_m": 4.356,
            "applied_scale_factor": 0.001,
            "heuristic": "divide_by_1000_mm_to_m",
            "severity": "severe",
            "summary_zh": "Geometry scale requires confirmation.",
        },
    }

    tool_module.submarine_solver_dispatch_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/scaled-binary-case.stl",
        task_description="Prepare the solver case using the confirmed meter-scale binary geometry.",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=False,
        tool_call_id="tc-dispatch-scaled-binary-case",
    )

    scaled_geometry_path = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "scaled-binary-case"
        / "openfoam-case"
        / "constant"
        / "triSurface"
        / "scaled-binary-case.stl"
    )
    mins, maxs = _binary_stl_bounds(scaled_geometry_path)

    assert round(maxs[0] - mins[0], 6) == 4.356
    assert round(maxs[1] - mins[1], 6) == 0.508
    assert round(maxs[2] - mins[2], 6) == 0.0


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
    assert runtime_state["output_delivery_plan"] == payload["output_delivery_plan"]
    assert runtime_state["request_virtual_path"] == payload["request_virtual_path"]
    assert result.update["artifacts"] == payload["artifact_virtual_paths"]


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


def test_submarine_solver_dispatch_marks_failed_when_required_force_coefficients_are_missing(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-missing-force-coeffs"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "missing-force-coeffs.stl"
    _write_ascii_stl(geometry_path)

    fake_sandbox = _FakeSandbox(output="Time = 200\nEnd")

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/missing-force-coeffs.stl",
        task_description="Execute a run that finishes without producing required force coefficients",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command="echo finished-without-force-coeffs",
        tool_call_id="tc-dispatch-missing-force-coeffs",
    )

    json_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "missing-force-coeffs"
        / "openfoam-request.json"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    solver_results = payload["solver_results"]

    assert payload["dispatch_status"] == "failed"
    assert solver_results["solver_completed"] is True
    assert solver_results["final_time_seconds"] == 200.0
    assert solver_results["latest_force_coefficients"] is None
    assert result.update["submarine_runtime"]["stage_status"] == "failed"


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
    stability_evidence_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "results-demo" / "stability-evidence.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    solver_results = json.loads(solver_results_path.read_text(encoding="utf-8"))
    stability_evidence = json.loads(stability_evidence_path.read_text(encoding="utf-8"))

    assert any(path.endswith("/solver-results.json") for path in artifacts)
    assert any(path.endswith("/solver-results.md") for path in artifacts)
    assert any(path.endswith("/stability-evidence.json") for path in artifacts)
    assert payload["request_virtual_path"].endswith("/openfoam-request.json")
    assert payload["solver_results_virtual_path"].endswith("/solver-results.json")
    assert payload["solver_results_markdown_virtual_path"].endswith("/solver-results.md")
    assert payload["stability_evidence_virtual_path"].endswith("/stability-evidence.json")
    assert payload["solver_results"]["solver_completed"] is True
    assert payload["stability_evidence"]["status"] == "missing_evidence"
    assert payload["scientific_verification_assessment"]["status"] == "needs_more_verification"
    assert payload["solver_results"]["latest_force_coefficients"]["Cd"] == 0.12
    assert payload["solver_results"]["latest_forces"]["total_force"][0] == 8.0
    assert stability_evidence["source_solver_results_virtual_path"].endswith("/solver-results.json")
    assert stability_evidence["artifact_virtual_path"].endswith("/stability-evidence.json")
    assert stability_evidence["requirements"][0]["requirement_id"] == "final_residual_threshold"
    assert stability_evidence["requirements"][0]["status"] == "passed"
    assert stability_evidence["requirements"][1]["requirement_id"] == "force_coefficient_tail_stability"
    assert stability_evidence["requirements"][1]["status"] == "missing_evidence"
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
    assert result.update["submarine_runtime"]["solver_results_virtual_path"] == (
        payload["solver_results_virtual_path"]
    )
    assert result.update["submarine_runtime"]["stability_evidence_virtual_path"] == (
        payload["stability_evidence_virtual_path"]
    )
    assert result.update["submarine_runtime"]["stability_evidence"]["status"] == "missing_evidence"
    assert (
        result.update["submarine_runtime"]["scientific_verification_assessment"]["status"]
        == "needs_more_verification"
    )
    assert (
        _execution_plan_status(result.update["submarine_runtime"], "scientific-verification")
        == "completed"
    )


def test_submarine_solver_dispatch_waits_for_workspace_completion_before_collecting_results(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-async-completion"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "async-completion.stl"
    _write_ascii_stl(geometry_path)

    case_dir = (
        workspace_dir / "submarine" / "solver-dispatch" / "async-completion" / "openfoam-case"
    )
    fake_sandbox = _FakeAsyncCompletionSandbox(case_dir=case_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/async-completion.stl",
        task_description="等待本次 OpenFOAM run 真正完成后再采集结果",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command="bash /mnt/user-data/workspace/submarine/solver-dispatch/async-completion/openfoam-case/Allrun",
        tool_call_id="tc-dispatch-async-completion",
    )

    request_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "async-completion" / "openfoam-request.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    solver_results = payload["solver_results"]

    assert payload["dispatch_status"] == "executed"
    assert solver_results["solver_completed"] is True
    assert solver_results["final_time_seconds"] == 200.0
    assert solver_results["residual_summary"]["field_count"] == 2
    assert solver_results["latest_force_coefficients"]["Cd"] == 0.12
    assert solver_results["latest_forces"]["total_force"][0] == 8.0
    assert "End" in (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "async-completion"
        / "openfoam-run.log"
    ).read_text(encoding="utf-8")
    assert result.update["submarine_runtime"]["stage_status"] == "executed"


def test_submarine_solver_dispatch_waits_for_progressing_scientific_study_variants(
    tmp_path, monkeypatch
):
    dispatch_module = importlib.import_module("deerflow.domain.submarine.solver_dispatch")

    paths = Paths(tmp_path)
    thread_id = "thread-progressive-study-execution"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "progressive-study-execution.stl"
    _write_ascii_stl(geometry_path)

    fake_sandbox = _FakeProgressiveScientificStudySandbox(workspace_dir=workspace_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    original_wait_command = dispatch_module._wait_for_workspace_command_completion
    original_wait_log = dispatch_module._wait_for_workspace_log_completion

    def _short_wait_command_completion(**kwargs):
        signature = inspect.signature(original_wait_command)
        if "timeout_seconds" in signature.parameters:
            kwargs["timeout_seconds"] = 0.05
        if "poll_interval_seconds" in signature.parameters:
            kwargs["poll_interval_seconds"] = 0.005
        return original_wait_command(**kwargs)

    def _short_wait_log_completion(**kwargs):
        signature = inspect.signature(original_wait_log)
        if "stall_timeout_seconds" in signature.parameters:
            kwargs["stall_timeout_seconds"] = 0.05
        elif "timeout_seconds" in signature.parameters:
            kwargs["timeout_seconds"] = 0.05
        if "max_wait_seconds" in signature.parameters:
            kwargs["max_wait_seconds"] = 0.3
        if "poll_interval_seconds" in signature.parameters:
            kwargs["poll_interval_seconds"] = 0.005
        if "stability_window_seconds" in signature.parameters:
            kwargs["stability_window_seconds"] = 0.01
        return original_wait_log(**kwargs)

    monkeypatch.setattr(
        dispatch_module,
        "_wait_for_workspace_command_completion",
        _short_wait_command_completion,
    )
    monkeypatch.setattr(
        dispatch_module,
        "_wait_for_workspace_log_completion",
        _short_wait_log_completion,
    )

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/progressive-study-execution.stl",
        task_description="Execute the baseline and wait for every progressing scientific study variant to really finish.",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        execute_scientific_studies=True,
        solver_command=(
            "bash /mnt/user-data/workspace/submarine/solver-dispatch/"
            "progressive-study-execution/openfoam-case/Allrun"
        ),
        tool_call_id="tc-dispatch-progressive-study-execution",
    )

    request_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "progressive-study-execution"
        / "openfoam-request.json"
    )
    mesh_verification_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "progressive-study-execution"
        / "verification-mesh-independence.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    mesh_verification = json.loads(mesh_verification_path.read_text(encoding="utf-8"))
    study_manifest = payload["scientific_study_manifest"]
    mesh_variants = study_manifest["study_definitions"][0]["variants"]
    fine_variant = next(item for item in mesh_variants if item["variant_id"] == "fine")

    assert payload["dispatch_status"] == "executed"
    assert study_manifest["study_execution_status"] == "completed"
    assert fine_variant["execution_status"] == "completed"
    assert fine_variant["compare_status"] == "completed"
    assert mesh_verification["status"] == "passed"
    assert result.update["submarine_runtime"]["stage_status"] == "executed"


def test_submarine_solver_dispatch_waits_past_preprocess_end_markers_before_collecting_results(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-preprocess-end-async-completion"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "preprocess-end-async-completion.stl"
    _write_ascii_stl(geometry_path)

    case_dir = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "preprocess-end-async-completion"
        / "openfoam-case"
    )
    fake_sandbox = _FakePreprocessEndAsyncCompletionSandbox(case_dir=case_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/preprocess-end-async-completion.stl",
        task_description="Wait for the real solver completion instead of trusting preprocess End markers",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command=(
            "bash /mnt/user-data/workspace/submarine/solver-dispatch/"
            "preprocess-end-async-completion/openfoam-case/Allrun"
        ),
        tool_call_id="tc-dispatch-preprocess-end-async-completion",
    )

    request_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "preprocess-end-async-completion"
        / "openfoam-request.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    solver_results = payload["solver_results"]

    assert payload["dispatch_status"] == "executed"
    assert solver_results["solver_completed"] is True
    assert solver_results["final_time_seconds"] == 200.0
    assert solver_results["residual_summary"]["field_count"] == 2
    assert solver_results["latest_force_coefficients"]["Cd"] == 0.12
    assert "Time = 200s" in (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "preprocess-end-async-completion"
        / "openfoam-run.log"
    ).read_text(encoding="utf-8")
    assert result.update["submarine_runtime"]["stage_status"] == "executed"


def test_submarine_solver_dispatch_refreshes_workspace_log_even_if_exit_status_arrives_first(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-status-first"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "status-first.stl"
    _write_ascii_stl(geometry_path)

    case_dir = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "status-first"
        / "openfoam-case"
    )
    fake_sandbox = _FakeExitStatusAheadOfLogCompletionSandbox(case_dir=case_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/status-first.stl",
        task_description="Do not freeze the captured solver log at the earlier timeout-shaped snapshot.",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command=(
            "bash /mnt/user-data/workspace/submarine/solver-dispatch/status-first/openfoam-case/Allrun"
        ),
        tool_call_id="tc-dispatch-status-first",
    )

    request_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "status-first"
        / "openfoam-request.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    solver_results = payload["solver_results"]
    captured_log = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "status-first"
        / "openfoam-run.log"
    ).read_text(encoding="utf-8")

    assert payload["dispatch_status"] == "executed"
    assert solver_results["solver_completed"] is True
    assert solver_results["final_time_seconds"] == 200.0
    assert solver_results["latest_force_coefficients"]["Cd"] == 0.12
    assert "Time = 200s" in captured_log
    assert captured_log.rstrip().endswith("End")
    assert result.update["submarine_runtime"]["stage_status"] == "executed"


def test_submarine_solver_dispatch_clears_stale_postprocessing_before_incomplete_rerun(
    tmp_path, monkeypatch
):
    paths = Paths(tmp_path)
    thread_id = "thread-stale-postprocess"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "stale-postprocess.stl"
    _write_ascii_stl(geometry_path)

    case_dir = (
        workspace_dir / "submarine" / "solver-dispatch" / "stale-postprocess" / "openfoam-case"
    )
    stale_coeffs_path = case_dir / "postProcessing" / "forceCoeffsHull" / "0" / "forceCoeffs.dat"
    stale_coeffs_path.parent.mkdir(parents=True, exist_ok=True)
    stale_coeffs_path.write_text(
        "\n".join(
            [
                "# Time Cd Cs Cl CmRoll CmPitch CmYaw",
                "0 999 0 0 0 0 0",
                "200 999 0 0 0 0 0",
            ]
        ),
        encoding="utf-8",
    )
    stale_forces_path = case_dir / "postProcessing" / "forcesHull" / "0" / "forces.dat"
    stale_forces_path.parent.mkdir(parents=True, exist_ok=True)
    stale_forces_path.write_text(
        "\n".join(
            [
                "# Time forces(pressure viscous) moments(pressure viscous)",
                "200 ((0 0 0) (999 0 0)) ((0 0 0) (0 999 0))",
            ]
        ),
        encoding="utf-8",
    )

    fake_sandbox = _FakeMeshOnlySandbox(case_dir=case_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/stale-postprocess.stl",
        task_description="不允许把旧 postProcessing 结果混进新的不完整重跑",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command="bash /mnt/user-data/workspace/submarine/solver-dispatch/stale-postprocess/openfoam-case/Allrun",
        tool_call_id="tc-dispatch-stale-postprocess",
    )

    request_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "stale-postprocess" / "openfoam-request.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    solver_results = payload["solver_results"]

    assert payload["dispatch_status"] == "failed"
    assert solver_results["solver_completed"] is False
    assert solver_results["final_time_seconds"] is None
    assert solver_results["latest_force_coefficients"] is None
    assert solver_results["latest_forces"] is None
    assert solver_results["force_coefficients_history"] == []
    assert solver_results["forces_history"] == []
    assert not stale_coeffs_path.exists()
    assert not stale_forces_path.exists()
    assert result.update["submarine_runtime"]["stage_status"] == "failed"


def test_submarine_solver_dispatch_emits_baseline_experiment_artifacts(
    tmp_path,
    monkeypatch,
):
    paths = Paths(tmp_path)
    thread_id = "thread-baseline-experiment"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "baseline-experiment-demo.stl"
    _write_ascii_stl(geometry_path)

    case_dir = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "baseline-experiment-demo"
        / "openfoam-case"
    )
    fake_sandbox = _FakePostprocessSandbox(case_dir=case_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/baseline-experiment-demo.stl",
        task_description="执行一次 baseline run 并生成 experiment registry artifacts",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        solver_command=(
            "bash /mnt/user-data/workspace/submarine/solver-dispatch/"
            "baseline-experiment-demo/openfoam-case/Allrun"
        ),
        tool_call_id="tc-dispatch-baseline-experiment",
    )

    artifacts = result.update["artifacts"]
    request_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "baseline-experiment-demo"
        / "openfoam-request.json"
    )
    experiment_manifest_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "baseline-experiment-demo"
        / "experiment-manifest.json"
    )
    run_record_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "baseline-experiment-demo"
        / "run-record.json"
    )
    compare_summary_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "baseline-experiment-demo"
        / "run-compare-summary.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    experiment_manifest = json.loads(experiment_manifest_path.read_text(encoding="utf-8"))
    run_record = json.loads(run_record_path.read_text(encoding="utf-8"))
    compare_summary = json.loads(compare_summary_path.read_text(encoding="utf-8"))
    provenance_manifest_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "baseline-experiment-demo"
        / "provenance-manifest.json"
    )
    provenance_manifest = json.loads(provenance_manifest_path.read_text(encoding="utf-8"))

    assert any(path.endswith("/experiment-manifest.json") for path in artifacts)
    assert any(path.endswith("/provenance-manifest.json") for path in artifacts)
    assert any(path.endswith("/run-record.json") for path in artifacts)
    assert any(path.endswith("/run-compare-summary.json") for path in artifacts)
    assert payload["experiment_manifest"]["baseline_run_id"] == "baseline"
    assert payload["run_compare_summary"]["baseline_run_id"] == "baseline"
    assert payload["experiment_manifest"]["experiment_status"] == "partial"
    assert payload["experiment_manifest"]["workflow_status"] == "partial"
    assert payload["run_compare_summary"]["workflow_status"] == "planned"
    assert len(payload["run_compare_summary"]["comparisons"]) == 6
    assert all(
        item["compare_status"] == "planned"
        for item in payload["run_compare_summary"]["comparisons"]
    )
    assert experiment_manifest["baseline_run_id"] == "baseline"
    assert experiment_manifest["experiment_status"] == "partial"
    assert experiment_manifest["workflow_status"] == "partial"
    assert run_record["run_id"] == "baseline"
    assert run_record["run_role"] == "baseline"
    assert compare_summary["workflow_status"] == "planned"
    assert len(compare_summary["comparisons"]) == 6
    assert all(item["compare_status"] == "planned" for item in compare_summary["comparisons"])
    assert any(
        item["candidate_run_id"] == "mesh_independence:coarse"
        and item["candidate_execution_status"] == "planned"
        for item in compare_summary["comparisons"]
    )
    assert payload["provenance_summary"]["artifact_entrypoints"]["request"].endswith(
        "/openfoam-request.json"
    )
    assert payload["provenance_summary"]["artifact_entrypoints"]["run_record"].endswith(
        "/run-record.json"
    )
    assert provenance_manifest["artifact_entrypoints"]["run_compare_summary"].endswith(
        "/run-compare-summary.json"
    )


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


def test_submarine_solver_dispatch_emits_run_compare_summary_for_study_execution(
    tmp_path,
    monkeypatch,
):
    paths = Paths(tmp_path)
    thread_id = "thread-study-compare"
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "study-compare-demo.stl"
    _write_ascii_stl(geometry_path)

    fake_sandbox = _FakeScientificStudySandbox(workspace_dir=workspace_dir)

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(tool_module, "get_sandbox_provider", lambda: _FakeProvider(fake_sandbox))

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=_make_runtime(paths, thread_id),
        geometry_path="/mnt/user-data/uploads/study-compare-demo.stl",
        task_description="执行 scientific study variants 并生成 run compare summary",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=True,
        execute_scientific_studies=True,
        solver_command="bash /mnt/user-data/workspace/submarine/solver-dispatch/study-compare-demo/openfoam-case/Allrun",
        tool_call_id="tc-dispatch-study-compare",
    )

    artifacts = result.update["artifacts"]
    request_path = (
        outputs_dir / "submarine" / "solver-dispatch" / "study-compare-demo" / "openfoam-request.json"
    )
    compare_summary_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "study-compare-demo"
        / "run-compare-summary.json"
    )
    variant_run_record_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "study-compare-demo"
        / "studies"
        / "mesh-independence"
        / "coarse"
        / "run-record.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    compare_summary = json.loads(compare_summary_path.read_text(encoding="utf-8"))
    variant_run_record = json.loads(variant_run_record_path.read_text(encoding="utf-8"))

    assert any(path.endswith("/run-compare-summary.json") for path in artifacts)
    assert payload["run_compare_summary"]["baseline_run_id"] == "baseline"
    assert len(payload["run_compare_summary"]["comparisons"]) == 6
    assert len(compare_summary["comparisons"]) == 6
    assert compare_summary["comparisons"][0]["candidate_run_id"] == "mesh_independence:coarse"
    assert compare_summary["comparisons"][0]["metric_deltas"]["Cd"]["baseline_value"] == 0.12
    assert variant_run_record["run_id"] == "mesh_independence:coarse"
    assert variant_run_record["run_role"] == "scientific_study_variant"


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
    figure_manifest_path = artifact_dir / "figure-manifest.json"

    assert any(path.endswith("/surface-pressure.csv") for path in artifacts)
    assert any(path.endswith("/surface-pressure.md") for path in artifacts)
    assert any(path.endswith("/surface-pressure.png") for path in artifacts)
    assert any(path.endswith("/wake-velocity-slice.csv") for path in artifacts)
    assert any(path.endswith("/wake-velocity-slice.md") for path in artifacts)
    assert any(path.endswith("/wake-velocity-slice.png") for path in artifacts)
    assert any(path.endswith("/figure-manifest.json") for path in artifacts)
    assert (artifact_dir / "surface-pressure.png").exists()
    assert (artifact_dir / "wake-velocity-slice.png").exists()
    manifest = json.loads(figure_manifest_path.read_text(encoding="utf-8"))
    assert manifest["run_dir_name"] == "ppx"
    assert manifest["figure_count"] == 2
    figures_by_output = {
        item["output_id"]: item
        for item in manifest["figures"]
    }
    assert set(figures_by_output) == {"surface_pressure_contour", "wake_velocity_slice"}
    surface_pressure = figures_by_output["surface_pressure_contour"]
    wake_slice = figures_by_output["wake_velocity_slice"]
    assert surface_pressure["title"] == "Surface Pressure Result"
    assert surface_pressure["caption"].startswith("Surface pressure contour")
    assert surface_pressure["render_status"] == "rendered"
    assert surface_pressure["field"] == "p"
    assert surface_pressure["selector_summary"] == "Patch selection: hull"
    assert surface_pressure["axes"] == ["x", "y"]
    assert surface_pressure["color_metric"] == "p"
    assert surface_pressure["sample_count"] == 2
    assert surface_pressure["value_range"] == {"min": 10.5, "max": 12.0}
    assert surface_pressure["source_csv_virtual_path"].endswith("/surface-pressure.csv")
    assert any(path.endswith("/surface-pressure.png") for path in surface_pressure["artifact_virtual_paths"])

    assert wake_slice["title"] == "Wake Velocity Slice"
    assert wake_slice["caption"].startswith("Wake velocity slice")
    assert wake_slice["render_status"] == "rendered"
    assert wake_slice["field"] == "U"
    assert wake_slice["selector_summary"] == "Plane slice at x/Lref=1.25 with normal (1.0, 0.0, 0.0)"
    assert wake_slice["axes"] == ["y", "z"]
    assert wake_slice["color_metric"] == "|U|"
    assert wake_slice["sample_count"] == 2
    assert wake_slice["value_range"] == {"min": 4.601087, "max": 4.8}
    assert wake_slice["source_csv_virtual_path"].endswith("/wake-velocity-slice.csv")
    assert any(path.endswith("/wake-velocity-slice.png") for path in wake_slice["artifact_virtual_paths"])
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


def test_solver_dispatch_decomposition_case_module_writes_scaffold(tmp_path):
    case_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_case"
    )
    geometry_module = importlib.import_module("deerflow.domain.submarine.geometry_check")

    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    geometry_path = tmp_path / "decomposition-case.stl"
    _write_ascii_stl(geometry_path)
    geometry = geometry_module.inspect_geometry_file(geometry_path, "DARPA SUBOFF")

    simulation_requirements = case_module.resolve_simulation_requirements(
        inlet_velocity_mps=6.5,
        fluid_density_kg_m3=997.0,
        kinematic_viscosity_m2ps=9.1e-07,
        end_time_seconds=400.0,
        delta_t_seconds=0.25,
        write_interval_steps=40,
    )
    scaffold = case_module.write_openfoam_case_scaffold(
        workspace_dir=workspace_dir,
        run_dir_name="decomposition-case",
        geometry_path=geometry_path,
        geometry=geometry,
        selected_case=None,
        simulation_requirements=simulation_requirements,
        requested_outputs=[
            {
                "output_id": "surface_pressure_contour",
                "label": "表面压力云图",
                "requested_label": "表面压力云图",
                "status": "requested",
                "support_level": "supported",
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
            },
        ],
    )

    case_dir = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "decomposition-case"
        / "openfoam-case"
    )
    control_dict = (case_dir / "system" / "controlDict").read_text(encoding="utf-8")

    assert scaffold["execution_readiness"] == "stl_ready"
    assert scaffold["run_script_virtual_path"].endswith("/Allrun")
    assert "surfacePressure" in control_dict
    assert "wakeVelocitySlice" in control_dict
    assert "magUInf         6.5;" in control_dict
    assert "rhoInf          997.0;" in control_dict


def test_solver_dispatch_case_scaffold_includes_pressure_reference(tmp_path):
    case_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_case"
    )
    geometry_module = importlib.import_module("deerflow.domain.submarine.geometry_check")

    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    geometry_path = tmp_path / "pressure-reference.stl"
    _write_ascii_stl(geometry_path)
    geometry = geometry_module.inspect_geometry_file(geometry_path, "DARPA SUBOFF")

    simulation_requirements = case_module.resolve_simulation_requirements(
        inlet_velocity_mps=5.0,
        fluid_density_kg_m3=1025.0,
        kinematic_viscosity_m2ps=1.05e-06,
        end_time_seconds=2.0,
        delta_t_seconds=0.001,
        write_interval_steps=200,
    )
    case_module.write_openfoam_case_scaffold(
        workspace_dir=workspace_dir,
        run_dir_name="pressure-reference",
        geometry_path=geometry_path,
        geometry=geometry,
        selected_case=None,
        simulation_requirements=simulation_requirements,
    )

    fv_solution = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "pressure-reference"
        / "openfoam-case"
        / "system"
        / "fvSolution"
    ).read_text(encoding="utf-8")

    assert "pRefCell" in fv_solution
    assert "pRefValue" in fv_solution


def test_solver_dispatch_case_scaffold_normalizes_reference_area_for_mm_scale_geometry(
    tmp_path,
):
    case_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_case"
    )
    models_module = importlib.import_module("deerflow.domain.submarine.models")

    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    geometry_path = tmp_path / "suboff-mm-scale.stl"
    _write_ascii_stl(geometry_path)

    geometry = models_module.GeometryInspection(
        file_name="suboff-mm-scale.stl",
        file_size_bytes=geometry_path.stat().st_size,
        input_format="stl",
        geometry_family="DARPA SUBOFF",
        source_application="stl-mesh",
        estimated_length_m=4.356,
        triangle_count=32760,
        bounding_box=models_module.GeometryBoundingBox(
            min_x=0.0,
            max_x=4355.94775390625,
            min_y=-476.29052734375,
            max_y=254.0,
            min_z=-254.0,
            max_z=254.0,
        ),
        notes=[],
    )
    simulation_requirements = case_module.resolve_simulation_requirements(
        inlet_velocity_mps=5.0,
        fluid_density_kg_m3=1025.0,
        kinematic_viscosity_m2ps=1.05e-06,
        end_time_seconds=2.0,
        delta_t_seconds=0.001,
        write_interval_steps=200,
    )
    scaffold = case_module.write_openfoam_case_scaffold(
        workspace_dir=workspace_dir,
        run_dir_name="suboff-mm-scale",
        geometry_path=geometry_path,
        geometry=geometry,
        selected_case=None,
        simulation_requirements=simulation_requirements,
    )

    control_dict = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "suboff-mm-scale"
        / "openfoam-case"
        / "system"
        / "controlDict"
    ).read_text(encoding="utf-8")

    assert 0.3 < scaffold["reference_area_m2"] < 0.5
    assert "Aref            370987.587891;" not in control_dict


def test_solver_dispatch_case_scaffold_uses_open_farfield_boundaries(tmp_path):
    case_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_case"
    )
    geometry_module = importlib.import_module("deerflow.domain.submarine.geometry_check")

    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    geometry_path = tmp_path / "open-farfield.stl"
    _write_ascii_stl(geometry_path)
    geometry = geometry_module.inspect_geometry_file(geometry_path, "DARPA SUBOFF")

    simulation_requirements = case_module.resolve_simulation_requirements(
        inlet_velocity_mps=5.0,
        fluid_density_kg_m3=1025.0,
        kinematic_viscosity_m2ps=1.05e-06,
        end_time_seconds=2.0,
        delta_t_seconds=0.001,
        write_interval_steps=200,
    )
    case_module.write_openfoam_case_scaffold(
        workspace_dir=workspace_dir,
        run_dir_name="open-farfield",
        geometry_path=geometry_path,
        geometry=geometry,
        selected_case=None,
        simulation_requirements=simulation_requirements,
    )

    case_dir = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "open-farfield"
        / "openfoam-case"
    )
    velocity = (case_dir / "0" / "U").read_text(encoding="utf-8")
    pressure = (case_dir / "0" / "p").read_text(encoding="utf-8")
    turbulent_kinetic_energy = (case_dir / "0" / "k").read_text(encoding="utf-8")
    specific_dissipation_rate = (case_dir / "0" / "omega").read_text(encoding="utf-8")
    block_mesh = (case_dir / "system" / "blockMeshDict").read_text(encoding="utf-8")

    assert "outlet" not in velocity
    assert "type            freestreamVelocity;" in velocity
    assert "freestreamValue uniform (5.0 0 0);" in velocity
    assert "outlet" not in pressure
    assert "type            freestreamPressure;" in pressure
    assert "freestreamValue uniform 0;" in pressure
    assert "type            inletOutlet;" in turbulent_kinetic_energy
    assert "type            inletOutlet;" in specific_dissipation_rate
    assert "outlet" not in block_mesh


def test_solver_dispatch_decomposition_results_module_collects_solver_outputs(
    tmp_path,
):
    results_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_results"
    )

    case_dir = _platform_fs_path(tmp_path / "openfoam-case")
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
    command_output = "\n".join(
        [
            "Create mesh for time = 0",
            "Time = 10",
            "smoothSolver:  Solving for Ux, Initial residual = 0.001, Final residual = 1e-06, No Iterations 2",
            "GAMG:  Solving for p, Initial residual = 0.01, Final residual = 0.0002, No Iterations 5",
            "Time = 200",
            "smoothSolver:  Solving for Ux, Initial residual = 0.0003, Final residual = 3e-08, No Iterations 2",
            "GAMG:  Solving for p, Initial residual = 0.012, Final residual = 0.00014, No Iterations 5",
            "points:           10234",
            "faces:            28764",
            "internal faces:   27654",
            "cells:            9342",
            "Mesh OK.",
            "End",
        ]
    )

    results = results_module.collect_solver_results(
        case_dir=case_dir,
        run_dir_name="decomposition-results",
        command_output=command_output,
        reference_values={
            "reference_length_m": 4.0,
            "reference_area_m2": 1.0,
            "inlet_velocity_mps": 6.5,
            "fluid_density_kg_m3": 997.0,
        },
        simulation_requirements={
            "inlet_velocity_mps": 6.5,
            "fluid_density_kg_m3": 997.0,
            "kinematic_viscosity_m2ps": 9.1e-07,
            "end_time_seconds": 400.0,
            "delta_t_seconds": 0.25,
            "write_interval_steps": 40,
        },
    )

    assert results["solver_completed"] is True
    assert results["final_time_seconds"] == 200.0
    assert results["latest_force_coefficients"]["Cd"] == 0.12
    assert results["latest_forces"]["total_force"][0] == 8.0
    assert results["mesh_summary"]["cells"] == 9342
    assert results["residual_summary"]["field_count"] == 2
    assert results["workspace_postprocess_virtual_path"].endswith("/postProcessing")


def test_solver_dispatch_decomposition_results_module_detects_failure_markers():
    results_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_results"
    )

    assert results_module.looks_like_solver_failure("FOAM FATAL ERROR: divergence")
    assert not results_module.looks_like_solver_failure("Time = 200\nEnd")


def test_solver_dispatch_decomposition_results_module_parses_inline_mesh_summary():
    results_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_results"
    )

    command_output = "\n".join(
        [
            "Create mesh for time = 0",
            "After introducing baffles : cells:194190  faces:674559  points:249525",
            "Time = 200",
            "ExecutionTime = 57.054743 s  ClockTime = 60 s",
            "End",
        ]
    )

    results = results_module.collect_solver_results(
        case_dir=Path("."),
        run_dir_name="inline-mesh-summary",
        command_output=command_output,
        reference_values={
            "reference_length_m": 4.0,
            "reference_area_m2": 1.0,
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
        },
        simulation_requirements={
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
            "kinematic_viscosity_m2ps": 1e-06,
            "end_time_seconds": 200.0,
            "delta_t_seconds": 1.0,
            "write_interval_steps": 50,
        },
    )

    assert results["mesh_summary"]["cells"] == 194190
    assert results["mesh_summary"]["faces"] == 674559
    assert results["mesh_summary"]["points"] == 249525


def test_solver_dispatch_decomposition_results_module_ignores_feature_counts_and_prefers_latest_mesh_stats():
    results_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_results"
    )

    command_output = "\n".join(
        [
            "[submarine-cfd] Extracting features",
            "Initial feature set:",
            "    feature points : 15",
            "Mesh Information",
            "  nPoints: 136161",
            "  nCells: 128000",
            "  nFaces: 392000",
            "  nInternalFaces: 376000",
            "After introducing baffles : cells:194190  faces:674559  points:249525",
            "After introducing baffles : cells:194190  faces:742391  points:249525",
            "Mesh OK.",
            "Time = 200",
            "ExecutionTime = 57.054743 s  ClockTime = 60 s",
            "End",
        ]
    )

    results = results_module.collect_solver_results(
        case_dir=Path("."),
        run_dir_name="mesh-summary-priority",
        command_output=command_output,
        reference_values={
            "reference_length_m": 4.0,
            "reference_area_m2": 1.0,
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
        },
        simulation_requirements={
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
            "kinematic_viscosity_m2ps": 1e-06,
            "end_time_seconds": 200.0,
            "delta_t_seconds": 1.0,
            "write_interval_steps": 50,
        },
    )

    assert results["mesh_summary"]["mesh_ok"] is True
    assert results["mesh_summary"]["cells"] == 194190
    assert results["mesh_summary"]["faces"] == 742391
    assert results["mesh_summary"]["points"] == 249525
    assert results["mesh_summary"]["internal_faces"] == 376000


def test_solver_dispatch_decomposition_results_module_prefers_later_plain_mesh_counts_over_older_n_counts():
    results_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_results"
    )

    command_output = "\n".join(
        [
            "Mesh Information",
            "  nPoints: 136161",
            "  nCells: 128000",
            "  nFaces: 392000",
            "points: 183378",
            "cells: 141249",
            "faces: 465265",
            "Mesh OK.",
            "Time = 200",
            "End",
        ]
    )

    results = results_module.collect_solver_results(
        case_dir=Path("."),
        run_dir_name="mesh-summary-latest-plain-counts",
        command_output=command_output,
        reference_values={
            "reference_length_m": 4.0,
            "reference_area_m2": 1.0,
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
        },
        simulation_requirements={
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
            "kinematic_viscosity_m2ps": 1e-06,
            "end_time_seconds": 200.0,
            "delta_t_seconds": 1.0,
            "write_interval_steps": 50,
        },
    )

    assert results["mesh_summary"]["points"] == 183378
    assert results["mesh_summary"]["cells"] == 141249
    assert results["mesh_summary"]["faces"] == 465265


def test_solver_dispatch_decomposition_results_module_uses_latest_field_residuals_for_max_final_residual():
    results_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_results"
    )

    command_output = "\n".join(
        [
            "Time = 1",
            "smoothSolver:  Solving for Ux, Initial residual = 1.0, Final residual = 0.010195413, No Iterations 1",
            "smoothSolver:  Solving for k, Initial residual = 1.0, Final residual = 0.072007947, No Iterations 1",
            "GAMG:  Solving for p, Initial residual = 1.0, Final residual = 0.0099002667, No Iterations 6",
            "Time = 200",
            "smoothSolver:  Solving for Ux, Initial residual = 1.9085343e-09, Final residual = 1.9085343e-09, No Iterations 0",
            "smoothSolver:  Solving for k, Initial residual = 9.9566546e-09, Final residual = 9.9566546e-09, No Iterations 0",
            "GAMG:  Solving for p, Initial residual = 5.4971957e-08, Final residual = 5.4971957e-08, No Iterations 0",
            "End",
        ]
    )

    results = results_module.collect_solver_results(
        case_dir=Path("."),
        run_dir_name="latest-residuals-only",
        command_output=command_output,
        reference_values={
            "reference_length_m": 4.0,
            "reference_area_m2": 1.0,
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
        },
        simulation_requirements={
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
            "kinematic_viscosity_m2ps": 1e-06,
            "end_time_seconds": 200.0,
            "delta_t_seconds": 1.0,
            "write_interval_steps": 50,
        },
    )

    assert results["residual_summary"]["latest_by_field"]["k"]["final_residual"] == 9.9566546e-09
    assert results["residual_summary"]["latest_by_field"]["p"]["final_residual"] == 5.4971957e-08
    assert results["residual_summary"]["max_final_residual"] == 5.4971957e-08


def test_solver_dispatch_decomposition_results_module_does_not_treat_preprocess_end_markers_as_solver_completion():
    results_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_results"
    )

    command_output = "\n".join(
        [
            "[submarine-cfd] Extracting features",
            "ExecutionTime = 0.110134 s  ClockTime = 0 s",
            "End",
            "[submarine-cfd] Running snappyHexMesh",
            "Mesh snapped in = 23.862714 s.",
            "Checking final mesh ...",
            "End",
        ]
    )

    results = results_module.collect_solver_results(
        case_dir=Path("."),
        run_dir_name="preprocess-end-only",
        command_output=command_output,
        reference_values={
            "reference_length_m": 4.0,
            "reference_area_m2": 1.0,
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
        },
        simulation_requirements={
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
            "kinematic_viscosity_m2ps": 1e-06,
            "end_time_seconds": 200.0,
            "delta_t_seconds": 1.0,
            "write_interval_steps": 50,
        },
    )

    assert results["solver_completed"] is False
    assert results["final_time_seconds"] is None
    assert results["residual_summary"] is None
    assert results["latest_force_coefficients"] is None
    assert results["latest_forces"] is None


def test_solver_dispatch_decomposition_results_module_requires_terminal_end_after_solver_evidence():
    results_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_results"
    )

    command_output = "\n".join(
        [
            "[submarine-cfd] Extracting features",
            "ExecutionTime = 0.110134 s  ClockTime = 0 s",
            "End",
            "[submarine-cfd] Running snappyHexMesh",
            "Mesh snapped in = 23.862714 s.",
            "Checking final mesh ...",
            "End",
            "Time = 0s",
            "smoothSolver:  Solving for Ux, Initial residual = 0.02, Final residual = 1e-05, No Iterations 2",
        ]
    )

    assert results_module.solver_output_looks_complete(command_output) is False

    results = results_module.collect_solver_results(
        case_dir=Path("."),
        run_dir_name="preprocess-end-plus-partial-solver",
        command_output=command_output,
        reference_values={
            "reference_length_m": 4.0,
            "reference_area_m2": 1.0,
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
        },
        simulation_requirements={
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
            "kinematic_viscosity_m2ps": 1e-06,
            "end_time_seconds": 200.0,
            "delta_t_seconds": 1.0,
            "write_interval_steps": 50,
        },
    )

    assert results["solver_completed"] is False
    assert results["final_time_seconds"] == 0.0
    assert results["residual_summary"]["field_count"] == 1
    assert results["latest_force_coefficients"] is None
    assert results["latest_forces"] is None


def test_solver_dispatch_decomposition_results_module_treats_time_zero_end_without_residuals_as_incomplete():
    results_module = importlib.import_module(
        "deerflow.domain.submarine.solver_dispatch_results"
    )

    command_output = "\n".join(
        [
            "[submarine-cfd] Checking mesh",
            "Mesh OK.",
            "End",
            "[submarine-cfd] Solving with simpleFoam",
            "Time = 0s",
            "End",
        ]
    )

    assert results_module.solver_output_looks_complete(command_output) is False

    results = results_module.collect_solver_results(
        case_dir=Path("."),
        run_dir_name="time-zero-end-without-residuals",
        command_output=command_output,
        reference_values={
            "reference_length_m": 4.0,
            "reference_area_m2": 1.0,
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
        },
        simulation_requirements={
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
            "kinematic_viscosity_m2ps": 1e-06,
            "end_time_seconds": 200.0,
            "delta_t_seconds": 1.0,
            "write_interval_steps": 50,
        },
    )

    assert results["solver_completed"] is False
    assert results["final_time_seconds"] == 0.0
    assert results["residual_summary"] is None
    assert results["latest_force_coefficients"] is None
    assert results["latest_forces"] is None


def test_submarine_solver_dispatch_requires_user_confirmation_before_dispatch(
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
        "task_summary": "Clarify the baseline CFD operating condition before dispatch",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/awaiting-confirmation.stl",
        "geometry_family": "DARPA SUBOFF",
        "simulation_requirements": {
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1025.0,
            "kinematic_viscosity_m2ps": 1.05e-06,
        },
        "stage_status": "draft",
        "review_status": "needs_user_confirmation",
        "next_recommended_stage": "user-confirmation",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/design-brief/awaiting-confirmation/cfd-design-brief.md",
        "artifact_virtual_paths": [
            "/mnt/user-data/outputs/submarine/design-brief/awaiting-confirmation/cfd-design-brief.json"
        ],
    }

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/awaiting-confirmation.stl",
        task_description="Try to dispatch even though the user has not confirmed the case",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        execute_now=False,
        tool_call_id="tc-dispatch-awaiting-confirmation",
    )

    dispatch_request_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "awaiting-confirmation"
        / "openfoam-request.json"
    )

    assert not dispatch_request_path.exists()
    assert "messages" in result.update
    assert "artifacts" not in result.update
    assert "submarine_runtime" not in result.update
    message = result.update["messages"][0].content
    assert "研究者确认" in message
    assert "协商区" in message
    assert "设计简报" in message
    assert "继续求解准备" in message
    assert "user confirmation" not in message.lower()
    assert "submarine_solver_dispatch" not in message


def test_submarine_solver_dispatch_recovers_confirmed_execute_intent_from_design_brief_artifact(
    tmp_path, monkeypatch
):
    design_brief_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_design_brief_tool"
    )

    paths = Paths(tmp_path)
    thread_id = "thread-confirmed-execute-intent"
    uploads_dir = paths.sandbox_uploads_dir(thread_id)
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    workspace_dir = paths.sandbox_work_dir(thread_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "confirmed-execute-intent.stl"
    _write_ascii_stl(geometry_path)

    fake_sandbox = _FakePostprocessSandbox(
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "confirmed-execute-intent"
        / "openfoam-case"
    )

    monkeypatch.setattr(tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(design_brief_tool_module, "get_paths", lambda: paths)
    monkeypatch.setattr(
        tool_module,
        "get_sandbox_provider",
        lambda: _FakeProvider(fake_sandbox),
    )

    runtime = _make_runtime(paths, thread_id)
    runtime.state["sandbox"] = {"sandbox_id": "local"}

    design_brief_result = design_brief_tool_module.submarine_design_brief_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/confirmed-execute-intent.stl",
        task_description="直接发起 5 m/s 基线 CFD 计算，并尽力得到 Cd 与阻力结果。",
        task_type="resistance",
        geometry_family_hint="DARPA SUBOFF",
        confirmation_status="confirmed",
        selected_case_id="darpa_suboff_bare_hull_resistance",
        inlet_velocity_mps=5.0,
        fluid_density_kg_m3=1025.0,
        kinematic_viscosity_m2ps=1.05e-06,
        end_time_seconds=200.0,
        delta_t_seconds=1.0,
        write_interval_steps=50,
        expected_outputs=["闃诲姏绯绘暟 Cd", "涓枃缁撴灉鎶ュ憡"],
        open_questions=[],
        tool_call_id="tc-design-brief-confirmed-execute-intent",
    )

    design_brief_payload = json.loads(
        (
            outputs_dir
            / "submarine"
            / "design-brief"
            / "confirmed-execute-intent"
            / "cfd-design-brief.json"
        ).read_text(encoding="utf-8")
    )

    runtime.state["artifacts"] = design_brief_result.update["artifacts"]
    runtime.state["submarine_runtime"] = {
        "current_stage": "geometry-preflight",
        "task_summary": "Geometry preflight completed for the uploaded STL.",
        "task_type": "resistance",
        "geometry_virtual_path": "/mnt/user-data/uploads/confirmed-execute-intent.stl",
        "geometry_family": "DARPA SUBOFF",
        "selected_case_id": "darpa_suboff_bare_hull_resistance",
        "simulation_requirements": None,
        "review_status": "ready_for_supervisor",
        "next_recommended_stage": "geometry-preflight",
        "report_virtual_path": "/mnt/user-data/outputs/submarine/geometry-check/confirmed-execute-intent/geometry-check.md",
        "artifact_virtual_paths": [
            *design_brief_result.update["artifacts"],
            "/mnt/user-data/outputs/submarine/geometry-check/confirmed-execute-intent/geometry-check.json",
        ],
    }

    result = tool_module.submarine_solver_dispatch_tool.func(
        runtime=runtime,
        geometry_path="/mnt/user-data/uploads/confirmed-execute-intent.stl",
        task_description="",
        task_type="resistance",
        geometry_family_hint=None,
        tool_call_id="tc-dispatch-confirmed-execute-intent",
    )

    request_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "confirmed-execute-intent"
        / "openfoam-request.json"
    )
    handoff_path = (
        outputs_dir
        / "submarine"
        / "solver-dispatch"
        / "confirmed-execute-intent"
        / "supervisor-handoff.json"
    )
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))

    assert fake_sandbox.commands
    assert payload["dispatch_status"] == "executed"
    assert payload["task_description"] == design_brief_payload["task_description"]
    assert payload["solver_results"]["solver_completed"] is True
    assert payload["simulation_requirements"]["inlet_velocity_mps"] == 5.0
    assert handoff["task_summary"] == design_brief_payload["task_description"]
    assert handoff["confirmation_status"] == "confirmed"
    assert (
        result.update["submarine_runtime"]["task_summary"]
        == design_brief_payload["task_description"]
    )
    assert result.update["submarine_runtime"]["stage_status"] == "executed"
