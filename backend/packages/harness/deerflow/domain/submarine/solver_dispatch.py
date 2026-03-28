"""Submarine solver-dispatch planning and artifact generation."""

from __future__ import annotations

import json
import re
import shutil
from collections.abc import Callable
from pathlib import Path

from .contracts import SubmarineRequestedOutput, build_supervisor_review_contract
from .geometry_check import inspect_geometry_file
from .library import rank_cases
from .models import (
    GeometryInspection,
    SubmarineCaseMatch,
)
from .output_contract import build_output_delivery_plan
from .postprocess import (
    collect_requested_postprocess_artifacts,
    render_requested_postprocess_function_objects,
)

WORKSPACE_VIRTUAL_ROOT = "/mnt/user-data/workspace"
WORKSPACE_UPLOAD_ROOT = "/mnt/user-data/uploads"
DEFAULT_INLET_VELOCITY_MPS = 5.0
DEFAULT_FLUID_DENSITY_KG_M3 = 1000.0
DEFAULT_KINEMATIC_VISCOSITY_M2PS = 1e-06
DEFAULT_END_TIME_SECONDS = 200.0
DEFAULT_DELTA_T_SECONDS = 1.0
DEFAULT_WRITE_INTERVAL_STEPS = 50
STL_READY_EXECUTION = "stl_ready"
GEOMETRY_CONVERSION_REQUIRED = "geometry_conversion_required"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "solver-dispatch"


def _artifact_virtual_path(run_dir_name: str, filename: str) -> str:
    return f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/{filename}"


def _workspace_virtual_path(run_dir_name: str, suffix: str = "") -> str:
    base = f"{WORKSPACE_VIRTUAL_ROOT}/submarine/solver-dispatch/{run_dir_name}/openfoam-case"
    return f"{base}/{suffix}".rstrip("/") if suffix else base


def _write_unix_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(content)


def _select_case(candidate_cases: list[SubmarineCaseMatch], selected_case_id: str | None) -> SubmarineCaseMatch | None:
    if selected_case_id:
        for case in candidate_cases:
            if case.case_id == selected_case_id:
                return case
    return candidate_cases[0] if candidate_cases else None


def _resolve_solver_application(selected_case: SubmarineCaseMatch | None) -> str:
    recommended = (selected_case.recommended_solver if selected_case else None) or "OpenFOAM simpleFoam"
    tokens = [token.strip() for token in recommended.replace("/", " ").split() if token.strip()]
    if not tokens:
        return "simpleFoam"
    for token in reversed(tokens):
        if token.endswith("Foam"):
            return token
    return tokens[-1]


def _reference_length_m(geometry: GeometryInspection) -> float:
    return round(max(geometry.estimated_length_m or 4.0, 0.1), 6)


def _reference_area_m2(geometry: GeometryInspection) -> float:
    if geometry.bounding_box is not None:
        beam = max(geometry.bounding_box.max_y - geometry.bounding_box.min_y, 0.0)
        draft = max(geometry.bounding_box.max_z - geometry.bounding_box.min_z, 0.0)
        if beam > 0 and draft > 0:
            return round(max(beam * draft, 1e-4), 6)
    reference_length = _reference_length_m(geometry)
    return round(max(reference_length * reference_length * 0.01, 0.1), 6)


def _resolve_simulation_requirements(
    *,
    inlet_velocity_mps: float | None,
    fluid_density_kg_m3: float | None,
    kinematic_viscosity_m2ps: float | None,
    end_time_seconds: float | None,
    delta_t_seconds: float | None,
    write_interval_steps: int | None,
) -> dict[str, float | int]:
    requirements = {
        "inlet_velocity_mps": inlet_velocity_mps if inlet_velocity_mps is not None else DEFAULT_INLET_VELOCITY_MPS,
        "fluid_density_kg_m3": fluid_density_kg_m3 if fluid_density_kg_m3 is not None else DEFAULT_FLUID_DENSITY_KG_M3,
        "kinematic_viscosity_m2ps": (
            kinematic_viscosity_m2ps
            if kinematic_viscosity_m2ps is not None
            else DEFAULT_KINEMATIC_VISCOSITY_M2PS
        ),
        "end_time_seconds": end_time_seconds if end_time_seconds is not None else DEFAULT_END_TIME_SECONDS,
        "delta_t_seconds": delta_t_seconds if delta_t_seconds is not None else DEFAULT_DELTA_T_SECONDS,
        "write_interval_steps": write_interval_steps if write_interval_steps is not None else DEFAULT_WRITE_INTERVAL_STEPS,
    }

    if requirements["inlet_velocity_mps"] <= 0:
        raise ValueError("inlet_velocity_mps must be greater than 0")
    if requirements["fluid_density_kg_m3"] <= 0:
        raise ValueError("fluid_density_kg_m3 must be greater than 0")
    if requirements["kinematic_viscosity_m2ps"] <= 0:
        raise ValueError("kinematic_viscosity_m2ps must be greater than 0")
    if requirements["end_time_seconds"] <= 0:
        raise ValueError("end_time_seconds must be greater than 0")
    if requirements["delta_t_seconds"] <= 0:
        raise ValueError("delta_t_seconds must be greater than 0")
    if requirements["write_interval_steps"] <= 0:
        raise ValueError("write_interval_steps must be greater than 0")

    return requirements


def _control_dict(
    application: str,
    *,
    reference_length_m: float,
    reference_area_m2: float,
    inlet_velocity_mps: float = DEFAULT_INLET_VELOCITY_MPS,
    fluid_density_kg_m3: float = DEFAULT_FLUID_DENSITY_KG_M3,
    end_time_seconds: float = DEFAULT_END_TIME_SECONDS,
    delta_t_seconds: float = DEFAULT_DELTA_T_SECONDS,
    write_interval_steps: int = DEFAULT_WRITE_INTERVAL_STEPS,
    requested_outputs: list[dict] | None = None,
) -> str:
    requested_function_objects = render_requested_postprocess_function_objects(
        requested_outputs=requested_outputs,
        reference_length_m=reference_length_m,
    )
    return f"""FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object controlDict;
}}

application     {application};
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {end_time_seconds};
deltaT          {delta_t_seconds};
writeControl    timeStep;
writeInterval   {write_interval_steps};
purgeWrite      0;
writeFormat     ascii;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;

functions
{{
    forcesHull
    {{
        type            forces;
        libs            ("libforces.so");
        patches         (hull);
        p               p;
        U               U;
        rho             rhoInf;
        rhoInf          {fluid_density_kg_m3};
        CofR            (0 0 0);
        writeControl    timeStep;
        writeInterval   10;
    }}

    forceCoeffsHull
    {{
        type            forceCoeffs;
        libs            ("libforces.so");
        patches         (hull);
        p               p;
        U               U;
        rho             rhoInf;
        rhoInf          {fluid_density_kg_m3};
        liftDir         (0 0 1);
        dragDir         (1 0 0);
        pitchAxis       (0 1 0);
        CofR            (0 0 0);
        magUInf         {inlet_velocity_mps};
        lRef            {reference_length_m};
        Aref            {reference_area_m2};
        writeControl    timeStep;
        writeInterval   10;
    }}
{requested_function_objects}
}}
"""


def _fv_schemes() -> str:
    return """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object fvSchemes;
}

ddtSchemes
{
    default steadyState;
}

gradSchemes
{
    default Gauss linear;
}

divSchemes
{
    default none;
    div(phi,U)      bounded Gauss upwind;
    div(phi,k)      bounded Gauss upwind;
    div(phi,omega)  bounded Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}

laplacianSchemes
{
    default Gauss linear corrected;
}

interpolationSchemes
{
    default linear;
}

snGradSchemes
{
    default corrected;
}

wallDist
{
    method meshWave;
}
"""


def _fv_solution() -> str:
    return """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object fvSolution;
}

solvers
{
    p
    {
        solver GAMG;
        tolerance 1e-7;
        relTol 0.01;
        smoother GaussSeidel;
    }

    "(U|k|omega)"
    {
        solver smoothSolver;
        smoother symGaussSeidel;
        tolerance 1e-8;
        relTol 0.1;
    }
}

SIMPLE
{
    nNonOrthogonalCorrectors 1;
    consistent yes;
}

relaxationFactors
{
    fields
    {
        p 0.3;
    }
    equations
    {
        U 0.7;
        k 0.7;
        omega 0.7;
    }
}
"""


def _mesh_quality_dict() -> str:
    return """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object meshQualityDict;
}

maxNonOrtho 65;
maxBoundarySkewness 20;
maxInternalSkewness 4;
maxConcave 80;
minVol -1e30;
minTetQuality 1e-15;
minTwist 0.02;
minDeterminant 0.001;
minFaceWeight 0.05;
minVolRatio 0.01;
nSmoothScale 4;
errorReduction 0.75;
"""


def _transport_properties(
    *,
    fluid_density_kg_m3: float = DEFAULT_FLUID_DENSITY_KG_M3,
    kinematic_viscosity_m2ps: float = DEFAULT_KINEMATIC_VISCOSITY_M2PS,
) -> str:
    return f"""FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object transportProperties;
}}

transportModel  Newtonian;
nu              [0 2 -1 0 0 0 0] {kinematic_viscosity_m2ps};
rho             [1 -3 0 0 0 0 0] {fluid_density_kg_m3};
"""


def _turbulence_properties() -> str:
    return """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object turbulenceProperties;
}

simulationType  RAS;

RAS
{
    RASModel        kOmegaSST;
    turbulence      on;
    printCoeffs     on;
}
"""


def _initial_u(inlet_velocity_mps: float = DEFAULT_INLET_VELOCITY_MPS) -> str:
    return f"""FoamFile
{{
    version 2.0;
    format ascii;
    class volVectorField;
    object U;
}}

dimensions      [0 1 -1 0 0 0 0];
internalField   uniform ({inlet_velocity_mps} 0 0);

boundaryField
{{
    inlet
    {{
        type fixedValue;
        value uniform ({inlet_velocity_mps} 0 0);
    }}
    outlet
    {{
        type zeroGradient;
    }}
    hull
    {{
        type fixedValue;
        value uniform (0 0 0);
    }}
    farfield
    {{
        type slip;
    }}
}}
"""


def _initial_p() -> str:
    return """FoamFile
{
    version 2.0;
    format ascii;
    class volScalarField;
    object p;
}

dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0;

boundaryField
{
    inlet
    {
        type zeroGradient;
    }
    outlet
    {
        type fixedValue;
        value uniform 0;
    }
    hull
    {
        type zeroGradient;
    }
    farfield
    {
        type zeroGradient;
    }
}
"""


def _initial_k() -> str:
    return """FoamFile
{
    version 2.0;
    format ascii;
    class volScalarField;
    object k;
}

dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0.00375;

boundaryField
{
    inlet
    {
        type fixedValue;
        value uniform 0.00375;
    }
    outlet
    {
        type zeroGradient;
    }
    hull
    {
        type kqRWallFunction;
        value uniform 0;
    }
    farfield
    {
        type fixedValue;
        value uniform 0.00375;
    }
}
"""


def _initial_omega() -> str:
    return """FoamFile
{
    version 2.0;
    format ascii;
    class volScalarField;
    object omega;
}

dimensions      [0 0 -1 0 0 0 0];
internalField   uniform 10;

boundaryField
{
    inlet
    {
        type fixedValue;
        value uniform 10;
    }
    outlet
    {
        type zeroGradient;
    }
    hull
    {
        type omegaWallFunction;
        value uniform 10;
    }
    farfield
    {
        type fixedValue;
        value uniform 10;
    }
}
"""


def _initial_nut() -> str:
    return """FoamFile
{
    version 2.0;
    format ascii;
    class volScalarField;
    object nut;
}

dimensions      [0 2 -1 0 0 0 0];
internalField   uniform 0;

boundaryField
{
    inlet
    {
        type calculated;
        value uniform 0;
    }
    outlet
    {
        type calculated;
        value uniform 0;
    }
    hull
    {
        type nutkWallFunction;
        value uniform 0;
    }
    farfield
    {
        type calculated;
        value uniform 0;
    }
}
"""


def _block_mesh_dict(domain_length: float) -> str:
    upstream = round(-2.0 * domain_length, 3)
    downstream = round(4.0 * domain_length, 3)
    half_span = round(2.0 * domain_length, 3)
    return f"""FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object blockMeshDict;
}}

convertToMeters 1;

vertices
(
    ({upstream} -{half_span} -{half_span})
    ({downstream} -{half_span} -{half_span})
    ({downstream} {half_span} -{half_span})
    ({upstream} {half_span} -{half_span})
    ({upstream} -{half_span} {half_span})
    ({downstream} -{half_span} {half_span})
    ({downstream} {half_span} {half_span})
    ({upstream} {half_span} {half_span})
);

blocks
(
    hex (0 1 2 3 4 5 6 7) (80 40 40) simpleGrading (1 1 1)
);

edges ();

boundary
(
    inlet
    {{
        type patch;
        faces ((0 4 7 3));
    }}
    outlet
    {{
        type patch;
        faces ((1 2 6 5));
    }}
    farfield
    {{
        type patch;
        faces
        (
            (0 1 5 4)
            (3 7 6 2)
            (0 3 2 1)
            (4 5 6 7)
        );
    }}
);

mergePatchPairs ();
"""


def _surface_features_dict(geometry_file_name: str) -> str:
    return f"""FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object surfaceFeaturesDict;
}}

surfaces ("{geometry_file_name}");

includedAngle   150;

subsetFeatures
{{
    nonManifoldEdges yes;
    openEdges        yes;
}}
"""


def _snappy_hex_mesh_dict(geometry_file_name: str, domain_length: float) -> str:
    geometry_stem = Path(geometry_file_name).stem
    keep_x = round(-0.5 * domain_length, 3)
    keep_y = round(0.15 * domain_length, 3)
    keep_z = round(0.15 * domain_length, 3)
    return f"""FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object snappyHexMeshDict;
}}

#includeEtc "caseDicts/mesh/generation/snappyHexMeshDict.cfg"

castellatedMesh true;
snap            true;
addLayers       false;

geometry
{{
    hull
    {{
        type triSurfaceMesh;
        file "{geometry_file_name}";
    }}
}}

castellatedMeshControls
{{
    maxLocalCells 100000;
    maxGlobalCells 2000000;
    minRefinementCells 0;
    nCellsBetweenLevels 3;

    features
    (
        {{
            file "{geometry_stem}.eMesh";
            levels ((1 1));
        }}
    );

    refinementSurfaces
    {{
        hull
        {{
            level (2 3);
            patchInfo
            {{
                type wall;
            }}
        }}
    }}

    resolveFeatureAngle 45;

    locationInMesh ({keep_x} {keep_y} {keep_z});
}}

snapControls
{{
    nSmoothPatch 3;
    tolerance 2.0;
    nSolveIter 30;
    nRelaxIter 5;
}}

addLayersControls
{{
    relativeSizes true;
}}

meshQualityControls
{{
    maxNonOrtho 65;
}}

writeFlags
(
);

mergeTolerance 1e-6;
"""


def _allrun_script(application: str, geometry_file_name: str, requires_conversion: bool) -> str:
    if requires_conversion:
        return f"""#!/bin/sh
set -eu
cd "$(dirname "$0")"
echo "[submarine-cfd] Uploaded geometry {geometry_file_name} requires conversion to STL before the v1 solver pipeline can run."
exit 2
"""
    return f"""#!/bin/sh
set -eu
cd "$(dirname "$0")"
echo "[submarine-cfd] Preparing background mesh"
blockMesh
echo "[submarine-cfd] Extracting features"
surfaceFeatures
echo "[submarine-cfd] Running snappyHexMesh"
snappyHexMesh
echo "[submarine-cfd] Checking mesh"
checkMesh
echo "[submarine-cfd] Solving with {application}"
    {application}
"""


def _solver_results_virtual_path(run_dir_name: str, filename: str) -> str:
    return _artifact_virtual_path(run_dir_name, filename)


def _workspace_postprocess_virtual_path(run_dir_name: str) -> str:
    return _workspace_virtual_path(run_dir_name, "postProcessing")


def _find_latest_postprocess_file(case_dir: Path, object_name: str, filename: str) -> Path | None:
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


_REQUESTED_POSTPROCESS_EXPORTS: dict[str, dict[str, str | tuple[str, ...]]] = {
    "surface_pressure_contour": {
        "object_name": "surfacePressure",
        "source_filenames": ("surfacePressure.csv",),
        "artifact_csv": "surface-pressure.csv",
        "artifact_md": "surface-pressure.md",
        "title": "表面压力结果",
        "summary": "导出的表面压力后处理结果，可用于进一步绘图或归档。",
    },
    "wake_velocity_slice": {
        "object_name": "wakeVelocitySlice",
        "source_filenames": ("wakeVelocitySlice.csv",),
        "artifact_csv": "wake-velocity-slice.csv",
        "artifact_md": "wake-velocity-slice.md",
        "title": "尾流速度切片",
        "summary": "导出的尾流速度切片结果，可用于流场分析与报告引用。",
    },
}


def _requested_output_ids(requested_outputs: list[dict] | None) -> set[str]:
    return {
        str(item.get("output_id"))
        for item in (requested_outputs or [])
        if isinstance(item, dict) and item.get("output_id")
    }


def _summarize_delimited_file(path: Path) -> tuple[list[str], int]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return [], 0

    header = [token.strip() for token in lines[0].split(",")] if "," in lines[0] else lines[0].split()
    data_row_count = max(len(lines) - 1, 0)
    return header, data_row_count


def _render_postprocess_export_markdown(
    *,
    title: str,
    summary: str,
    source_path: Path,
    artifact_virtual_path: str,
    columns: list[str],
    data_row_count: int,
) -> str:
    lines = [
        f"# {title}",
        "",
        summary,
        "",
        f"- 原始后处理文件: `{source_path.as_posix()}`",
        f"- 稳定 artifact: `{artifact_virtual_path}`",
        f"- 数据行数: `{data_row_count}`",
    ]
    if columns:
        lines.append(f"- 字段: `{', '.join(columns)}`")
    lines.append("")
    return "\n".join(lines)


def _collect_requested_postprocess_artifacts(
    *,
    case_dir: Path,
    artifact_dir: Path,
    run_dir_name: str,
    requested_outputs: list[dict] | None,
) -> list[str]:
    requested_ids = _requested_output_ids(requested_outputs)
    exported_artifacts: list[str] = []

    for output_id, spec in _REQUESTED_POSTPROCESS_EXPORTS.items():
        if output_id not in requested_ids:
            continue

        source_path = _find_latest_postprocess_candidate(
            case_dir,
            str(spec["object_name"]),
            list(spec["source_filenames"]),
        )
        if source_path is None:
            continue

        csv_name = str(spec["artifact_csv"])
        markdown_name = str(spec["artifact_md"])
        csv_path = artifact_dir / csv_name
        markdown_path = artifact_dir / markdown_name
        shutil.copy2(source_path, csv_path)

        columns, data_row_count = _summarize_delimited_file(csv_path)
        csv_virtual_path = _artifact_virtual_path(run_dir_name, csv_name)
        _write_unix_text(
            markdown_path,
            _render_postprocess_export_markdown(
                title=str(spec["title"]),
                summary=str(spec["summary"]),
                source_path=source_path,
                artifact_virtual_path=csv_virtual_path,
                columns=columns,
                data_row_count=data_row_count,
            ),
        )

        exported_artifacts.extend(
            [
                csv_virtual_path,
                _artifact_virtual_path(run_dir_name, markdown_name),
            ]
        )

    return exported_artifacts


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


def _parse_mesh_summary(command_output: str) -> dict[str, int | bool] | None:
    summary: dict[str, int | bool] = {}
    for field_name, pattern in {
        "points": r"^\s*points:\s+(\d+)\s*$",
        "faces": r"^\s*faces:\s+(\d+)\s*$",
        "internal_faces": r"^\s*internal faces:\s+(\d+)\s*$",
        "cells": r"^\s*cells:\s+(\d+)\s*$",
    }.items():
        match = re.search(pattern, command_output, flags=re.MULTILINE)
        if match is not None:
            summary[field_name] = int(match.group(1))

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


def _render_solver_results_markdown_enriched(results: dict) -> str:
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


def _collect_solver_results(
    *,
    case_dir: Path,
    run_dir_name: str,
    command_output: str,
    reference_values: dict[str, float],
    simulation_requirements: dict[str, float | int],
) -> dict:
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
    residual_history = _parse_residual_history(command_output)

    return {
        "solver_completed": _solver_completed_successfully(command_output),
        "final_time_seconds": _parse_final_time_seconds(command_output),
        "workspace_postprocess_virtual_path": _workspace_postprocess_virtual_path(run_dir_name),
        "mesh_summary": _parse_mesh_summary(command_output),
        "residual_summary": _build_residual_summary(residual_history),
        "latest_force_coefficients": coeffs,
        "force_coefficients_history": coeff_history,
        "latest_forces": forces,
        "forces_history": force_history,
        "reference_values": reference_values,
        "simulation_requirements": simulation_requirements,
    }


def _looks_like_solver_failure(output: str) -> bool:
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


def _write_openfoam_case_scaffold(
    *,
    workspace_dir: Path,
    run_dir_name: str,
    geometry_path: Path,
    geometry: GeometryInspection,
    selected_case: SubmarineCaseMatch | None,
    simulation_requirements: dict[str, float | int],
    requested_outputs: list[dict] | None = None,
) -> dict[str, str | bool]:
    case_dir = workspace_dir / "submarine" / "solver-dispatch" / run_dir_name / "openfoam-case"
    (case_dir / "0").mkdir(parents=True, exist_ok=True)
    (case_dir / "constant" / "triSurface").mkdir(parents=True, exist_ok=True)
    (case_dir / "constant" / "source-geometry").mkdir(parents=True, exist_ok=True)
    (case_dir / "system").mkdir(parents=True, exist_ok=True)

    application = _resolve_solver_application(selected_case)
    domain_length = max((geometry.estimated_length_m or 10.0) * 2.0, 20.0)
    reference_length_m = _reference_length_m(geometry)
    reference_area_m2 = _reference_area_m2(geometry)
    requires_conversion = geometry_path.suffix.lower() != ".stl"
    execution_readiness = (
        GEOMETRY_CONVERSION_REQUIRED if requires_conversion else STL_READY_EXECUTION
    )

    _write_unix_text(
        case_dir / "0" / "U",
        _initial_u(float(simulation_requirements["inlet_velocity_mps"])),
    )
    _write_unix_text(case_dir / "0" / "p", _initial_p())
    _write_unix_text(case_dir / "0" / "k", _initial_k())
    _write_unix_text(case_dir / "0" / "omega", _initial_omega())
    _write_unix_text(case_dir / "0" / "nut", _initial_nut())
    _write_unix_text(
        case_dir / "constant" / "transportProperties",
        _transport_properties(
            fluid_density_kg_m3=float(simulation_requirements["fluid_density_kg_m3"]),
            kinematic_viscosity_m2ps=float(simulation_requirements["kinematic_viscosity_m2ps"]),
        ),
    )
    _write_unix_text(case_dir / "constant" / "turbulenceProperties", _turbulence_properties())
    _write_unix_text(
        case_dir / "system" / "controlDict",
        _control_dict(
            application,
            reference_length_m=reference_length_m,
            reference_area_m2=reference_area_m2,
            inlet_velocity_mps=float(simulation_requirements["inlet_velocity_mps"]),
            fluid_density_kg_m3=float(simulation_requirements["fluid_density_kg_m3"]),
            end_time_seconds=float(simulation_requirements["end_time_seconds"]),
            delta_t_seconds=float(simulation_requirements["delta_t_seconds"]),
            write_interval_steps=int(simulation_requirements["write_interval_steps"]),
            requested_outputs=requested_outputs,
        ),
    )
    _write_unix_text(case_dir / "system" / "fvSchemes", _fv_schemes())
    _write_unix_text(case_dir / "system" / "fvSolution", _fv_solution())
    _write_unix_text(case_dir / "system" / "meshQualityDict", _mesh_quality_dict())
    _write_unix_text(case_dir / "system" / "blockMeshDict", _block_mesh_dict(domain_length))

    if requires_conversion:
        source_geometry_path = case_dir / "constant" / "source-geometry" / geometry_path.name
        shutil.copy2(geometry_path, source_geometry_path)
        _write_unix_text(
            case_dir / "GEOMETRY_CONVERSION_REQUIRED.txt",
            "The uploaded geometry must be converted to STL before snappyHexMesh can run.\n",
        )
    else:
        tri_surface_path = case_dir / "constant" / "triSurface" / geometry_path.name
        shutil.copy2(geometry_path, tri_surface_path)
        _write_unix_text(case_dir / "system" / "surfaceFeaturesDict", _surface_features_dict(geometry_path.name))
        _write_unix_text(case_dir / "system" / "snappyHexMeshDict", _snappy_hex_mesh_dict(geometry_path.name, domain_length))

    allrun_path = case_dir / "Allrun"
    _write_unix_text(allrun_path, _allrun_script(application, geometry_path.name, requires_conversion))
    allrun_path.chmod(0o755)

    return {
        "workspace_case_dir_virtual_path": _workspace_virtual_path(run_dir_name),
        "run_script_virtual_path": _workspace_virtual_path(run_dir_name, "Allrun"),
        "requires_geometry_conversion": requires_conversion,
        "execution_readiness": execution_readiness,
        "solver_application": application,
        "reference_length_m": reference_length_m,
        "reference_area_m2": reference_area_m2,
        "inlet_velocity_mps": float(simulation_requirements["inlet_velocity_mps"]),
        "fluid_density_kg_m3": float(simulation_requirements["fluid_density_kg_m3"]),
        "kinematic_viscosity_m2ps": float(simulation_requirements["kinematic_viscosity_m2ps"]),
        "end_time_seconds": float(simulation_requirements["end_time_seconds"]),
        "delta_t_seconds": float(simulation_requirements["delta_t_seconds"]),
        "write_interval_steps": int(simulation_requirements["write_interval_steps"]),
    }


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
    solver_command: str | None = None,
    execute_now: bool = False,
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

    run_dir_name = _slugify(geometry_path.stem)
    artifact_dir = outputs_dir / "submarine" / "solver-dispatch" / run_dir_name
    artifact_dir.mkdir(parents=True, exist_ok=True)

    request_path = artifact_dir / "openfoam-request.json"
    markdown_path = artifact_dir / "dispatch-summary.md"
    html_path = artifact_dir / "dispatch-summary.html"
    log_path = artifact_dir / "openfoam-run.log"
    handoff_path = artifact_dir / "supervisor-handoff.json"
    solver_results_json_path = artifact_dir / "solver-results.json"
    solver_results_md_path = artifact_dir / "solver-results.md"

    case_scaffold: dict[str, str | bool] = {}
    if workspace_dir is not None:
        case_scaffold = _write_openfoam_case_scaffold(
            workspace_dir=workspace_dir,
            run_dir_name=run_dir_name,
            geometry_path=geometry_path,
            geometry=geometry,
            selected_case=selected_case,
            simulation_requirements=simulation_requirements,
            requested_outputs=normalized_requested_outputs,
        )

    effective_solver_command = solver_command or (
        f"bash {case_scaffold['run_script_virtual_path']}" if case_scaffold.get("run_script_virtual_path") else None
    )

    dispatch_status = "planned"
    execution_log_virtual_path: str | None = None
    solver_results: dict | None = None
    requested_postprocess_artifacts: list[str] = []
    if execute_now and effective_solver_command and execute_command is not None:
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
                reference_values={
                    "reference_length_m": float(case_scaffold.get("reference_length_m", 0.0)),
                    "reference_area_m2": float(case_scaffold.get("reference_area_m2", 0.0)),
                    "inlet_velocity_mps": float(case_scaffold.get("inlet_velocity_mps", DEFAULT_INLET_VELOCITY_MPS)),
                    "fluid_density_kg_m3": float(case_scaffold.get("fluid_density_kg_m3", DEFAULT_FLUID_DENSITY_KG_M3)),
                },
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
            requested_postprocess_artifacts = collect_requested_postprocess_artifacts(
                case_dir=case_dir,
                artifact_dir=artifact_dir,
                run_dir_name=run_dir_name,
                requested_outputs=normalized_requested_outputs,
                artifact_virtual_path_builder=_artifact_virtual_path,
                write_text=_write_unix_text,
            )

    artifacts = [
        _artifact_virtual_path(run_dir_name, "dispatch-summary.md"),
        _artifact_virtual_path(run_dir_name, "dispatch-summary.html"),
        _artifact_virtual_path(run_dir_name, "openfoam-request.json"),
        _artifact_virtual_path(run_dir_name, "supervisor-handoff.json"),
    ]
    if execution_log_virtual_path:
        artifacts.append(execution_log_virtual_path)
    if solver_results is not None:
        artifacts.extend(
            [
                _solver_results_virtual_path(run_dir_name, "solver-results.json"),
                _solver_results_virtual_path(run_dir_name, "solver-results.md"),
            ]
        )
    artifacts.extend(requested_postprocess_artifacts)

    review_status = "ready_for_supervisor"
    next_stage = "result-reporting" if dispatch_status == "executed" else "solver-dispatch"
    if case_scaffold.get("requires_geometry_conversion"):
        review_status = "needs_user_confirmation"
        next_stage = "geometry-preflight"
    elif dispatch_status == "failed":
        review_status = "blocked"
        next_stage = "solver-dispatch"

    review = build_supervisor_review_contract(
        next_recommended_stage=next_stage,
        report_virtual_path=artifacts[0],
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
        "geometry": geometry.model_dump(mode="json"),
        "candidate_cases": [case.model_dump(mode="json") for case in candidate_cases],
        "selected_case": selected_case.model_dump(mode="json") if selected_case else None,
        "dispatch_status": dispatch_status,
        "solver_command": effective_solver_command,
        "request_virtual_path": _artifact_virtual_path(run_dir_name, "openfoam-request.json"),
        "report_virtual_path": review.report_virtual_path,
        "execution_log_virtual_path": execution_log_virtual_path,
        "solver_results": solver_results,
        "simulation_requirements": simulation_requirements,
        "requested_outputs": normalized_requested_outputs,
        "output_delivery_plan": output_delivery_plan,
        "review_status": review.review_status,
        "next_recommended_stage": review.next_recommended_stage,
        "artifact_virtual_paths": review.artifact_virtual_paths,
        "workspace_case_dir_virtual_path": case_scaffold.get("workspace_case_dir_virtual_path"),
        "run_script_virtual_path": case_scaffold.get("run_script_virtual_path"),
        "solver_application": case_scaffold.get("solver_application"),
        "requires_geometry_conversion": case_scaffold.get("requires_geometry_conversion", False),
        "execution_readiness": case_scaffold.get("execution_readiness", STL_READY_EXECUTION),
        "supervisor_handoff_virtual_path": _artifact_virtual_path(run_dir_name, "supervisor-handoff.json"),
        "summary_zh": _compose_summary(
            geometry=geometry,
            selected_case=selected_case,
            dispatch_status=dispatch_status,
            execute_now=execute_now,
        ),
    }

    supervisor_handoff = {
        "task_summary": task_description,
        "confirmation_status": "confirmed" if dispatch_status == "executed" else "draft",
        "uploaded_geometry_path": geometry_virtual_path or geometry.file_name,
        "task_type": task_type,
        "geometry_family_hint": geometry.geometry_family,
        "selected_case_id": selected_case.case_id if selected_case else None,
        "requested_outputs": normalized_requested_outputs,
        "review_status": payload["review_status"],
        "next_recommended_stage": payload["next_recommended_stage"],
        "report_virtual_path": payload["report_virtual_path"],
        "artifact_virtual_paths": payload["artifact_virtual_paths"],
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

    return payload, artifacts
