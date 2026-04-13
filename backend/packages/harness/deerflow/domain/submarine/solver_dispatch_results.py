"""Solver result parsing and summary helpers for submarine solver dispatch."""

from __future__ import annotations

import re
from pathlib import Path

from .solver_dispatch_case import (
    DEFAULT_FLUID_DENSITY_KG_M3,
    DEFAULT_INLET_VELOCITY_MPS,
    WORKSPACE_VIRTUAL_ROOT,
    platform_fs_path,
)


def _workspace_postprocess_virtual_path(
    run_dir_name: str,
    *,
    case_relative_dir: str = "",
) -> str:
    relative = f"/{case_relative_dir.strip('/')}" if case_relative_dir else ""
    return (
        f"{WORKSPACE_VIRTUAL_ROOT}/submarine/solver-dispatch/"
        f"{run_dir_name}{relative}/openfoam-case/postProcessing"
    )


def _find_latest_postprocess_file(case_dir: Path, object_name: str, filename: str) -> Path | None:
    case_dir = platform_fs_path(case_dir)
    root = case_dir / "postProcessing" / object_name
    if not root.exists():
        return None

    candidates: list[tuple[float, Path]] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        target = child / filename
        if not target.exists():
            continue
        try:
            sort_key = float(child.name)
        except ValueError:
            sort_key = float("inf")
        candidates.append((sort_key, target))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[-1][1]


def _find_latest_postprocess_candidate(case_dir: Path, object_name: str, filenames: list[str]) -> Path | None:
    for filename in filenames:
        candidate = _find_latest_postprocess_file(case_dir, object_name, filename)
        if candidate is not None:
            return candidate
    return None


def _parse_numeric_row(
    values: list[float],
    header_tokens: list[str] | None,
) -> dict[str, float]:
    if header_tokens and len(header_tokens) == len(values):
        return {header_tokens[index]: value for index, value in enumerate(values)}

    fallback_names = [
        "Time",
        "Cd",
        "Cs",
        "Cl",
        "CmRoll",
        "CmPitch",
        "CmYaw",
    ]
    result: dict[str, float] = {}
    for index, value in enumerate(values):
        key = fallback_names[index] if index < len(fallback_names) else f"value_{index}"
        result[key] = value
    return result


def _parse_numeric_rows(path: Path) -> tuple[list[str] | None, list[list[float]]]:
    header_tokens: list[str] | None = None
    rows: list[list[float]] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            tokens = [token for token in line.lstrip("#").split() if token]
            if tokens and tokens[0].lower() == "time":
                header_tokens = tokens
            continue

        parts = line.split()
        try:
            values = [float(part) for part in parts]
        except ValueError:
            continue
        rows.append(values)

    return header_tokens, rows


def _parse_numeric_table(path: Path) -> dict[str, float] | None:
    header_tokens, rows = _parse_numeric_rows(path)
    if not rows:
        return None

    return _parse_numeric_row(rows[-1], header_tokens)


def _parse_numeric_history(path: Path) -> list[dict[str, float]]:
    header_tokens, rows = _parse_numeric_rows(path)
    return [_parse_numeric_row(values, header_tokens) for values in rows]


def _parse_vector_triplet(value: str) -> list[float] | None:
    parts = [part for part in value.strip().split() if part]
    if len(parts) != 3:
        return None
    try:
        return [float(part) for part in parts]
    except ValueError:
        return None


def _parse_force_line(line: str) -> dict | None:
    pattern = re.compile(
        r"^(?P<time>[-+0-9.eE]+)\s+\(\((?P<pf>[^)]+)\)\s+\((?P<vf>[^)]+)\)\)\s+\(\((?P<pm>[^)]+)\)\s+\((?P<vm>[^)]+)\)\)$"
    )
    match = pattern.match(line)
    if match is None:
        return None

    pressure_force = _parse_vector_triplet(match.group("pf"))
    viscous_force = _parse_vector_triplet(match.group("vf"))
    pressure_moment = _parse_vector_triplet(match.group("pm"))
    viscous_moment = _parse_vector_triplet(match.group("vm"))
    if not all([pressure_force, viscous_force, pressure_moment, viscous_moment]):
        return None

    def _sum_vectors(first: list[float], second: list[float]) -> list[float]:
        return [round(first[index] + second[index], 12) for index in range(3)]

    return {
        "Time": float(match.group("time")),
        "pressure_force": pressure_force,
        "viscous_force": viscous_force,
        "total_force": _sum_vectors(pressure_force, viscous_force),
        "pressure_moment": pressure_moment,
        "viscous_moment": viscous_moment,
        "total_moment": _sum_vectors(pressure_moment, viscous_moment),
    }


def _parse_latest_forces(path: Path) -> dict | None:
    latest: dict | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        latest = _parse_force_line(line) or latest
    return latest


def _parse_force_history(path: Path) -> list[dict]:
    history: list[dict] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parsed = _parse_force_line(line)
        if parsed is not None:
            history.append(parsed)
    return history


def _parse_final_time_seconds(command_output: str) -> float | None:
    matches = re.findall(r"^Time = ([0-9.+-eE]+)s?$", command_output, flags=re.MULTILINE)
    if not matches:
        return None
    try:
        return float(matches[-1])
    except ValueError:
        return None


def _solver_completed_successfully(command_output: str) -> bool:
    return "\nEnd" in command_output or command_output.rstrip().endswith("End")


def _latest_int_match(
    command_output: str,
    *,
    patterns: list[str],
) -> tuple[int | None, int]:
    latest_value: int | None = None
    latest_position = -1
    for pattern in patterns:
        for match in re.finditer(pattern, command_output, flags=re.MULTILINE):
            if match.start() >= latest_position:
                latest_value = int(match.group(1))
                latest_position = match.start()
    return latest_value, latest_position


def _parse_mesh_summary(command_output: str) -> dict[str, int | bool] | None:
    summary: dict[str, int | bool] = {}
    latest_positions: dict[str, int] = {}

    inline_matches = list(
        re.finditer(
            r"^\s*.*?\bcells:\s*(\d+)\s+faces:\s*(\d+)\s+points:\s*(\d+)\s*$",
            command_output,
            flags=re.MULTILINE,
        )
    )
    if inline_matches:
        inline_match = inline_matches[-1]
        summary["cells"] = int(inline_match.group(1))
        summary["faces"] = int(inline_match.group(2))
        summary["points"] = int(inline_match.group(3))
        latest_positions.update(
            {
                "cells": inline_match.start(),
                "faces": inline_match.start(),
                "points": inline_match.start(),
            }
        )

    for field_name, patterns in {
        "points": [r"^\s*points:\s*(\d+)\s*$", r"^\s*nPoints:\s*(\d+)\s*$"],
        "faces": [r"^\s*faces:\s*(\d+)\s*$", r"^\s*nFaces:\s*(\d+)\s*$"],
        "internal_faces": [
            r"^\s*internal faces:\s*(\d+)\s*$",
            r"^\s*nInternalFaces:\s*(\d+)\s*$",
        ],
        "cells": [r"^\s*cells:\s*(\d+)\s*$", r"^\s*nCells:\s*(\d+)\s*$"],
    }.items():
        value, position = _latest_int_match(command_output, patterns=patterns)
        if value is None:
            continue
        if position >= latest_positions.get(field_name, -1):
            summary[field_name] = value
            latest_positions[field_name] = position

    if "Mesh OK." in command_output:
        summary["mesh_ok"] = True
    elif re.search(r"^\s*Failed\s+\d+\s+mesh checks\.\s*$", command_output, flags=re.MULTILINE):
        summary["mesh_ok"] = False

    return summary or None


def _parse_residual_history(command_output: str) -> list[dict[str, float | int | str | None]]:
    history: list[dict[str, float | int | str | None]] = []
    current_time: float | None = None
    residual_pattern = re.compile(
        r"^(?P<solver>[^:]+):\s+Solving for (?P<field>[^,]+), Initial residual = (?P<initial>[-+0-9.eE]+), "
        r"Final residual = (?P<final>[-+0-9.eE]+), No Iterations (?P<iterations>\d+)$"
    )

    for raw_line in command_output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        time_match = re.match(r"^Time = ([-+0-9.eE]+)s?$", line)
        if time_match is not None:
            try:
                current_time = float(time_match.group(1))
            except ValueError:
                current_time = None
            continue

        residual_match = residual_pattern.match(line)
        if residual_match is None:
            continue

        history.append(
            {
                "Time": current_time,
                "solver": residual_match.group("solver").strip(),
                "field": residual_match.group("field").strip(),
                "initial_residual": float(residual_match.group("initial")),
                "final_residual": float(residual_match.group("final")),
                "iterations": int(residual_match.group("iterations")),
            }
        )

    return history


def _build_residual_summary(
    residual_history: list[dict[str, float | int | str | None]],
) -> dict[str, object] | None:
    if not residual_history:
        return None

    latest_by_field: dict[str, dict[str, float | int | str | None]] = {}
    max_final_residual: float | None = None
    latest_time: float | None = None
    for entry in residual_history:
        field_name = entry.get("field")
        if isinstance(field_name, str):
            latest_by_field[field_name] = entry
        final_residual = entry.get("final_residual")
        if isinstance(final_residual, float):
            max_final_residual = (
                final_residual
                if max_final_residual is None
                else max(max_final_residual, final_residual)
            )
        time_value = entry.get("Time")
        if isinstance(time_value, float):
            latest_time = time_value

    return {
        "history": residual_history,
        "latest_by_field": latest_by_field,
        "field_count": len(latest_by_field),
        "max_final_residual": max_final_residual,
        "latest_time": latest_time,
    }


def _has_fresh_solver_evidence(
    *,
    solver_completed: bool,
    final_time_seconds: float | None,
    residual_history: list[dict[str, float | int | str | None]],
) -> bool:
    if not solver_completed:
        return False
    return final_time_seconds is not None or bool(residual_history)


def _render_solver_results_markdown(results: dict) -> str:
    coeffs = results.get("latest_force_coefficients") or {}
    forces = results.get("latest_forces") or {}
    lines = [
        "# OpenFOAM 结果摘要",
        "",
        f"- 求解完成: `{results.get('solver_completed')}`",
        f"- 最终时间步: `{results.get('final_time_seconds')}`",
        f"- 后处理目录: `{results.get('workspace_postprocess_virtual_path')}`",
    ]
    reference_values = results.get("reference_values") or {}
    if reference_values:
        lines.extend(
            [
                "",
                "## 参考量",
                f"- 自由来流速度: `{reference_values.get('inlet_velocity_mps')}` m/s",
                f"- 流体密度: `{reference_values.get('fluid_density_kg_m3')}` kg/m^3",
                f"- 参考长度: `{reference_values.get('reference_length_m')}` m",
                f"- 参考面积: `{reference_values.get('reference_area_m2')}` m^2",
            ]
        )
    if coeffs:
        lines.extend(
            [
                "",
                "## 力系数",
                f"- 时间: `{coeffs.get('Time')}`",
                f"- Cd: `{coeffs.get('Cd')}`",
                f"- Cl: `{coeffs.get('Cl')}`",
                f"- Cs: `{coeffs.get('Cs')}`",
                f"- CmPitch: `{coeffs.get('CmPitch')}`",
            ]
        )
    if forces:
        lines.extend(
            [
                "",
                "## 力与力矩",
                f"- 时间: `{forces.get('Time')}`",
                f"- 总阻力向量 (N): `{forces.get('total_force')}`",
                f"- 总力矩向量 (N·m): `{forces.get('total_moment')}`",
            ]
        )
    return "\n".join(lines) + "\n"


def render_solver_results_markdown_enriched(results: dict) -> str:
    coeffs = results.get("latest_force_coefficients") or {}
    forces = results.get("latest_forces") or {}
    reference_values = results.get("reference_values") or {}
    mesh_summary = results.get("mesh_summary") or {}
    residual_summary = results.get("residual_summary") or {}

    lines = [
        "# OpenFOAM 结果摘要",
        "",
        f"- 求解完成: `{results.get('solver_completed')}`",
        f"- 最终时间步: `{results.get('final_time_seconds')}`",
        f"- 后处理目录: `{results.get('workspace_postprocess_virtual_path')}`",
    ]
    if reference_values:
        lines.extend(
            [
                "",
                "## 参考量",
                f"- 自由来流速度: `{reference_values.get('inlet_velocity_mps')}` m/s",
                f"- 流体密度: `{reference_values.get('fluid_density_kg_m3')}` kg/m^3",
                f"- 参考长度: `{reference_values.get('reference_length_m')}` m",
                f"- 参考面积: `{reference_values.get('reference_area_m2')}` m^2",
            ]
        )
    if mesh_summary:
        lines.extend(
            [
                "",
                "## 网格质量摘要",
                f"- Mesh OK: `{mesh_summary.get('mesh_ok')}`",
                f"- cells: `{mesh_summary.get('cells')}`",
                f"- faces: `{mesh_summary.get('faces')}`",
                f"- internal faces: `{mesh_summary.get('internal_faces')}`",
                f"- points: `{mesh_summary.get('points')}`",
            ]
        )
    if residual_summary:
        lines.extend(
            [
                "",
                "## 残差收敛摘要",
                f"- 字段数: `{residual_summary.get('field_count')}`",
                f"- 最新时间: `{residual_summary.get('latest_time')}`",
                f"- 最大最终残差: `{residual_summary.get('max_final_residual')}`",
            ]
        )
        latest_by_field = residual_summary.get("latest_by_field") or {}
        for field_name, entry in latest_by_field.items():
            lines.append(
                f"- {field_name}: initial `{entry.get('initial_residual')}`, "
                f"final `{entry.get('final_residual')}`, iterations `{entry.get('iterations')}`"
            )
    if coeffs:
        lines.extend(
            [
                "",
                "## 力系数",
                f"- 时间: `{coeffs.get('Time')}`",
                f"- Cd: `{coeffs.get('Cd')}`",
                f"- Cl: `{coeffs.get('Cl')}`",
                f"- Cs: `{coeffs.get('Cs')}`",
                f"- CmPitch: `{coeffs.get('CmPitch')}`",
            ]
        )
    if forces:
        lines.extend(
            [
                "",
                "## 力与力矩",
                f"- 时间: `{forces.get('Time')}`",
                f"- 总阻力向量(N): `{forces.get('total_force')}`",
                f"- 总力矩向量(N·m): `{forces.get('total_moment')}`",
            ]
        )
    return "\n".join(lines) + "\n"


def collect_solver_results(
    *,
    case_dir: Path,
    run_dir_name: str,
    case_relative_dir: str = "",
    command_output: str,
    reference_values: dict[str, float],
    simulation_requirements: dict[str, float | int],
) -> dict:
    solver_completed = _solver_completed_successfully(command_output)
    final_time_seconds = _parse_final_time_seconds(command_output)
    residual_history = _parse_residual_history(command_output)
    residual_summary = _build_residual_summary(residual_history)
    has_fresh_solver_evidence = _has_fresh_solver_evidence(
        solver_completed=solver_completed,
        final_time_seconds=final_time_seconds,
        residual_history=residual_history,
    )

    coeffs = None
    coeff_history: list[dict[str, float]] = []
    forces = None
    force_history: list[dict] = []
    if has_fresh_solver_evidence:
        coeff_filenames = ["forceCoeffs.dat", "coefficient.dat"]
        coeff_path = _find_latest_postprocess_candidate(case_dir, "forceCoeffsHull", coeff_filenames)
        if coeff_path is None:
            coeff_path = _find_latest_postprocess_candidate(case_dir, "forceCoeffs", coeff_filenames)
        coeffs = _parse_numeric_table(coeff_path) if coeff_path else None
        coeff_history = _parse_numeric_history(coeff_path) if coeff_path else []
        force_path = _find_latest_postprocess_candidate(case_dir, "forcesHull", ["forces.dat"])
        if force_path is None:
            force_path = _find_latest_postprocess_candidate(case_dir, "forces", ["forces.dat"])
        forces = _parse_latest_forces(force_path) if force_path else None
        force_history = _parse_force_history(force_path) if force_path else []

    return {
        "solver_completed": solver_completed,
        "final_time_seconds": final_time_seconds,
        "workspace_postprocess_virtual_path": _workspace_postprocess_virtual_path(
            run_dir_name,
            case_relative_dir=case_relative_dir,
        ),
        "mesh_summary": _parse_mesh_summary(command_output),
        "residual_summary": residual_summary,
        "latest_force_coefficients": coeffs,
        "force_coefficients_history": coeff_history,
        "latest_forces": forces,
        "forces_history": force_history,
        "reference_values": reference_values,
        "simulation_requirements": simulation_requirements,
    }


def solver_reference_values(case_scaffold: dict[str, str | bool | float | None]) -> dict[str, float | str]:
    values: dict[str, float | str] = {
        "reference_length_m": float(case_scaffold.get("reference_length_m", 0.0)),
        "reference_area_m2": float(case_scaffold.get("reference_area_m2", 0.0)),
        "inlet_velocity_mps": float(
            case_scaffold.get("inlet_velocity_mps", DEFAULT_INLET_VELOCITY_MPS)
        ),
        "fluid_density_kg_m3": float(
            case_scaffold.get("fluid_density_kg_m3", DEFAULT_FLUID_DENSITY_KG_M3)
        ),
    }
    if case_scaffold.get("reference_value_approval_state"):
        values["approval_state"] = str(case_scaffold["reference_value_approval_state"])
    if case_scaffold.get("reference_value_justification"):
        values["justification"] = str(case_scaffold["reference_value_justification"])
    return values
def looks_like_solver_failure(output: str) -> bool:
    markers = [
        "FOAM FATAL",
        "FOAM aborting",
        "command not found",
        "No such file or directory",
        "Segmentation fault",
        "Traceback (most recent call last)",
        "Error:",
    ]
    lowered = output.lower()
    return any(marker.lower() in lowered for marker in markers)

__all__ = [
    "collect_solver_results",
    "looks_like_solver_failure",
    "render_solver_results_markdown_enriched",
    "solver_reference_values",
]
