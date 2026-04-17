"""OpenFOAM case scaffold helpers for submarine solver dispatch."""

from __future__ import annotations

import os
import shutil
import struct
from collections.abc import Mapping
from pathlib import Path

from .models import GeometryInspection, SubmarineCaseMatch
from .postprocess import render_requested_postprocess_function_objects

WORKSPACE_VIRTUAL_ROOT = "/mnt/user-data/workspace"
DEFAULT_INLET_VELOCITY_MPS = 5.0
DEFAULT_FLUID_DENSITY_KG_M3 = 1000.0
DEFAULT_KINEMATIC_VISCOSITY_M2PS = 1e-06
DEFAULT_END_TIME_SECONDS = 200.0
DEFAULT_DELTA_T_SECONDS = 1.0
DEFAULT_WRITE_INTERVAL_STEPS = 50
STL_READY_EXECUTION = "stl_ready"
GEOMETRY_CONVERSION_REQUIRED = "geometry_conversion_required"


def _workspace_virtual_path(
    run_dir_name: str,
    suffix: str = "",
    *,
    case_relative_dir: str = "",
) -> str:
    relative = f"/{case_relative_dir.strip('/')}" if case_relative_dir else ""
    base = f"{WORKSPACE_VIRTUAL_ROOT}/submarine/solver-dispatch/{run_dir_name}{relative}/openfoam-case"
    return f"{base}/{suffix}".rstrip("/") if suffix else base


def write_unix_text(path: Path, content: str) -> None:
    with platform_fs_path(path).open("w", encoding="utf-8", newline="\n") as file:
        file.write(content)


def platform_fs_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    raw = str(path.resolve())
    if raw.startswith("\\\\?\\"):
        return Path(raw)
    return Path(f"\\\\?\\{raw}")


def _resolve_solver_application(selected_case: SubmarineCaseMatch | None) -> str:
    recommended = (selected_case.recommended_solver if selected_case else None) or "OpenFOAM foamRun / incompressibleFluid"
    normalized = recommended.lower()
    if "foamrun" in normalized or "incompressiblefluid" in normalized or "simplefoam" in normalized:
        return "foamRun"
    tokens = [token.strip() for token in recommended.replace("/", " ").split() if token.strip()]
    if not tokens:
        return "foamRun"
    for token in reversed(tokens):
        if token.endswith("Foam"):
            return token
    return tokens[-1]


def _resolve_solver_module(selected_case: SubmarineCaseMatch | None) -> str | None:
    recommended = (selected_case.recommended_solver if selected_case else None) or "OpenFOAM foamRun / incompressibleFluid"
    normalized = recommended.lower()
    if "simplefoam" in normalized or "foamrun" in normalized or "incompressiblefluid" in normalized:
        return "incompressibleFluid"
    return None


def _reference_length_m(
    geometry: GeometryInspection,
    reference_inputs: Mapping[str, object] | None = None,
) -> float:
    if reference_inputs and reference_inputs.get("reference_length_m") is not None:
        return round(max(float(reference_inputs["reference_length_m"]), 0.1), 6)
    return round(max(geometry.estimated_length_m or 4.0, 0.1), 6)


def _geometry_length_scale(geometry: GeometryInspection) -> float:
    if geometry.bounding_box is None or geometry.estimated_length_m is None:
        return 1.0
    raw_length = max(
        geometry.bounding_box.max_x - geometry.bounding_box.min_x,
        geometry.bounding_box.max_y - geometry.bounding_box.min_y,
        geometry.bounding_box.max_z - geometry.bounding_box.min_z,
    )
    if raw_length <= 0:
        return 1.0
    normalized_length = max(geometry.estimated_length_m, 0.0)
    if normalized_length <= 0:
        return 1.0
    return normalized_length / raw_length


def _reference_area_m2(
    geometry: GeometryInspection,
    reference_inputs: Mapping[str, object] | None = None,
) -> float:
    if reference_inputs and reference_inputs.get("reference_area_m2") is not None:
        return round(max(float(reference_inputs["reference_area_m2"]), 1e-4), 6)
    if geometry.bounding_box is not None:
        scale = _geometry_length_scale(geometry)
        beam = max(geometry.bounding_box.max_y - geometry.bounding_box.min_y, 0.0) * scale
        draft = max(geometry.bounding_box.max_z - geometry.bounding_box.min_z, 0.0) * scale
        if beam > 0 and draft > 0:
            return round(max(beam * draft, 1e-4), 6)
    reference_length = _reference_length_m(geometry, reference_inputs)
    return round(max(reference_length * reference_length * 0.01, 0.1), 6)


def _looks_like_binary_stl(raw: bytes) -> bool:
    if len(raw) < 84:
        return False
    triangle_count = struct.unpack("<I", raw[80:84])[0]
    expected_size = 84 + triangle_count * 50
    if expected_size == len(raw):
        return True
    return not raw[:5].lower().startswith(b"solid")


def _format_stl_float(value: float) -> str:
    return f"{value:.9g}"


def _scale_ascii_stl_content(content: str, scale_factor: float) -> str:
    scaled_lines: list[str] = []
    for raw_line in content.splitlines():
        stripped_line = raw_line.lstrip()
        if not stripped_line.lower().startswith("vertex "):
            scaled_lines.append(raw_line)
            continue

        parts = stripped_line.split()
        if len(parts) != 4:
            scaled_lines.append(raw_line)
            continue

        try:
            scaled_coordinates = [_format_stl_float(float(parts[index]) * scale_factor) for index in range(1, 4)]
        except ValueError:
            scaled_lines.append(raw_line)
            continue

        leading_whitespace = raw_line[: len(raw_line) - len(stripped_line)]
        scaled_lines.append(f"{leading_whitespace}vertex {' '.join(scaled_coordinates)}")

    scaled_content = "\n".join(scaled_lines)
    if content.endswith(("\n", "\r\n")):
        return scaled_content + "\n"
    return scaled_content


def _scale_binary_stl_content(raw: bytes, scale_factor: float) -> bytes:
    if len(raw) < 84:
        return raw
    triangle_count = struct.unpack("<I", raw[80:84])[0]
    expected_size = 84 + triangle_count * 50
    if expected_size > len(raw):
        return raw

    scaled = bytearray(raw[:84])
    for index in range(triangle_count):
        start = 84 + index * 50
        scaled.extend(raw[start : start + 12])
        vertices = struct.unpack("<fffffffff", raw[start + 12 : start + 48])
        scaled.extend(
            struct.pack(
                "<fffffffff",
                *[coordinate * scale_factor for coordinate in vertices],
            )
        )
        scaled.extend(raw[start + 48 : start + 50])
    return bytes(scaled)


def _copy_scaled_stl(
    *,
    source_path: Path,
    destination_path: Path,
    scale_factor: float,
) -> None:
    source_fs_path = platform_fs_path(source_path)
    destination_fs_path = platform_fs_path(destination_path)
    raw = source_fs_path.read_bytes()
    if _looks_like_binary_stl(raw):
        destination_fs_path.write_bytes(_scale_binary_stl_content(raw, scale_factor))
        return

    content = raw.decode("utf-8", errors="ignore")
    destination_fs_path.write_text(
        _scale_ascii_stl_content(content, scale_factor),
        encoding="utf-8",
        newline="\n",
    )


def resolve_simulation_requirements(
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
        "kinematic_viscosity_m2ps": (kinematic_viscosity_m2ps if kinematic_viscosity_m2ps is not None else DEFAULT_KINEMATIC_VISCOSITY_M2PS),
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
    solver_module: str | None = None,
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
{f"solver          {solver_module};" if solver_module else ""}
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
    pRefCell 0;
    pRefValue 0;
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


def _physical_properties(
    *,
    kinematic_viscosity_m2ps: float = DEFAULT_KINEMATIC_VISCOSITY_M2PS,
) -> str:
    return f"""FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object physicalProperties;
}}

viscosityModel  constant;
nu              {kinematic_viscosity_m2ps} [m^2/s];
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


def _momentum_transport() -> str:
    return """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object momentumTransport;
}

simulationType  RAS;

RAS
{
    model           kOmegaSST;
    turbulence      on;
    printCoeffs     on;
}
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
    hull
    {{
        type            noSlip;
    }}
    farfield
    {{
        type            freestreamVelocity;
        freestreamValue uniform ({inlet_velocity_mps} 0 0);
        value           uniform ({inlet_velocity_mps} 0 0);
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
    hull
    {
        type zeroGradient;
    }
    farfield
    {
        type            freestreamPressure;
        freestreamValue uniform 0;
        value           uniform 0;
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
    hull
    {
        type kqRWallFunction;
        value uniform 0;
    }
    farfield
    {
        type            inletOutlet;
        inletValue      uniform 0.00375;
        value           uniform 0.00375;
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
    hull
    {
        type omegaWallFunction;
        value uniform 10;
    }
    farfield
    {
        type            inletOutlet;
        inletValue      uniform 10;
        value           uniform 10;
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


def _block_mesh_dict(
    domain_length: float,
    *,
    mesh_scale_factor: float = 1.0,
) -> str:
    upstream = round(-2.0 * domain_length, 3)
    downstream = round(4.0 * domain_length, 3)
    half_span = round(2.0 * domain_length, 3)
    cells_x = max(int(round(80 * mesh_scale_factor)), 32)
    cells_y = max(int(round(40 * mesh_scale_factor)), 16)
    cells_z = max(int(round(40 * mesh_scale_factor)), 16)
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
    hex (0 1 2 3 4 5 6 7) ({cells_x} {cells_y} {cells_z}) simpleGrading (1 1 1)
);

edges ();

boundary
(
    inlet
    {{
        type patch;
        faces ((0 4 7 3));
    }}
    farfield
    {{
        type patch;
        faces
        (
            (1 2 6 5)
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


def _snappy_hex_mesh_dict(
    geometry_file_name: str,
    domain_length: float,
    *,
    mesh_scale_factor: float = 1.0,
) -> str:
    geometry_stem = Path(geometry_file_name).stem
    keep_x = round(-0.5 * domain_length, 3)
    keep_y = round(0.15 * domain_length, 3)
    keep_z = round(0.15 * domain_length, 3)
    max_local_cells = max(int(round(100000 * mesh_scale_factor)), 50000)
    max_global_cells = max(int(round(2000000 * mesh_scale_factor)), 500000)
    if mesh_scale_factor >= 1.15:
        refinement_levels = (3, 4)
    elif mesh_scale_factor <= 0.85:
        refinement_levels = (1, 2)
    else:
        refinement_levels = (2, 3)
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
    maxLocalCells {max_local_cells};
    maxGlobalCells {max_global_cells};
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
            level ({refinement_levels[0]} {refinement_levels[1]});
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


def _allrun_script(
    application: str,
    geometry_file_name: str,
    requires_conversion: bool,
    *,
    solver_module: str | None = None,
) -> str:
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
echo "[submarine-cfd] Solving with {application}{f' (solver {solver_module})' if solver_module else ''}"
    {application}{f' -solver {solver_module}' if solver_module else ''}
"""


def write_openfoam_case_scaffold(
    *,
    workspace_dir: Path,
    run_dir_name: str,
    geometry_path: Path,
    geometry: GeometryInspection,
    selected_case: SubmarineCaseMatch | None,
    simulation_requirements: dict[str, float | int],
    requested_outputs: list[dict] | None = None,
    case_relative_dir: str = "",
    mesh_scale_factor: float = 1.0,
    domain_extent_multiplier: float = 1.0,
    reference_inputs: Mapping[str, object] | None = None,
    geometry_scale_factor: float | None = None,
) -> dict[str, str | bool]:
    case_root_dir = workspace_dir / "submarine" / "solver-dispatch" / run_dir_name
    if case_relative_dir:
        case_root_dir = case_root_dir / Path(case_relative_dir)
    case_dir = case_root_dir / "openfoam-case"
    case_dir_fs = platform_fs_path(case_dir)
    (case_dir_fs / "0").mkdir(parents=True, exist_ok=True)
    (case_dir_fs / "constant" / "triSurface").mkdir(parents=True, exist_ok=True)
    (case_dir_fs / "constant" / "source-geometry").mkdir(parents=True, exist_ok=True)
    (case_dir_fs / "system").mkdir(parents=True, exist_ok=True)

    application = _resolve_solver_application(selected_case)
    solver_module = _resolve_solver_module(selected_case)
    characteristic_length = geometry.estimated_length_m or 10.0
    base_domain_length = max(characteristic_length * 2.0, 8.0)
    domain_length = max(base_domain_length * domain_extent_multiplier, 1.0)
    reference_length_m = _reference_length_m(geometry, reference_inputs)
    reference_area_m2 = _reference_area_m2(geometry, reference_inputs)
    requires_conversion = geometry_path.suffix.lower() != ".stl"
    execution_readiness = GEOMETRY_CONVERSION_REQUIRED if requires_conversion else STL_READY_EXECUTION

    write_unix_text(
        case_dir / "0" / "U",
        _initial_u(float(simulation_requirements["inlet_velocity_mps"])),
    )
    write_unix_text(case_dir / "0" / "p", _initial_p())
    write_unix_text(case_dir / "0" / "k", _initial_k())
    write_unix_text(case_dir / "0" / "omega", _initial_omega())
    write_unix_text(case_dir / "0" / "nut", _initial_nut())
    write_unix_text(
        case_dir / "constant" / "physicalProperties",
        _physical_properties(
            kinematic_viscosity_m2ps=float(simulation_requirements["kinematic_viscosity_m2ps"]),
        ),
    )
    write_unix_text(case_dir / "constant" / "momentumTransport", _momentum_transport())
    write_unix_text(
        case_dir / "constant" / "transportProperties",
        _transport_properties(
            fluid_density_kg_m3=float(simulation_requirements["fluid_density_kg_m3"]),
            kinematic_viscosity_m2ps=float(simulation_requirements["kinematic_viscosity_m2ps"]),
        ),
    )
    write_unix_text(case_dir / "constant" / "turbulenceProperties", _turbulence_properties())
    write_unix_text(
        case_dir / "system" / "controlDict",
        _control_dict(
            application,
            solver_module=solver_module,
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
    write_unix_text(case_dir / "system" / "fvSchemes", _fv_schemes())
    write_unix_text(case_dir / "system" / "fvSolution", _fv_solution())
    write_unix_text(case_dir / "system" / "meshQualityDict", _mesh_quality_dict())
    write_unix_text(
        case_dir / "system" / "blockMeshDict",
        _block_mesh_dict(domain_length, mesh_scale_factor=mesh_scale_factor),
    )

    if requires_conversion:
        source_geometry_path = case_dir_fs / "constant" / "source-geometry" / geometry_path.name
        shutil.copy2(platform_fs_path(geometry_path), source_geometry_path)
        write_unix_text(
            case_dir / "GEOMETRY_CONVERSION_REQUIRED.txt",
            "The uploaded geometry must be converted to STL before snappyHexMesh can run.\n",
        )
    else:
        tri_surface_path = case_dir_fs / "constant" / "triSurface" / geometry_path.name
        if geometry_scale_factor is not None and geometry_scale_factor > 0 and abs(geometry_scale_factor - 1.0) > 1e-9:
            _copy_scaled_stl(
                source_path=geometry_path,
                destination_path=tri_surface_path,
                scale_factor=geometry_scale_factor,
            )
        else:
            shutil.copy2(platform_fs_path(geometry_path), tri_surface_path)
        write_unix_text(case_dir / "system" / "surfaceFeaturesDict", _surface_features_dict(geometry_path.name))
        write_unix_text(
            case_dir / "system" / "snappyHexMeshDict",
            _snappy_hex_mesh_dict(
                geometry_path.name,
                domain_length,
                mesh_scale_factor=mesh_scale_factor,
            ),
        )

    allrun_path = case_dir_fs / "Allrun"
    write_unix_text(
        allrun_path,
        _allrun_script(
            application,
            geometry_path.name,
            requires_conversion,
            solver_module=solver_module,
        ),
    )
    allrun_path.chmod(0o755)

    return {
        "workspace_case_dir_virtual_path": _workspace_virtual_path(
            run_dir_name,
            case_relative_dir=case_relative_dir,
        ),
        "run_script_virtual_path": _workspace_virtual_path(
            run_dir_name,
            "Allrun",
            case_relative_dir=case_relative_dir,
        ),
        "requires_geometry_conversion": requires_conversion,
        "execution_readiness": execution_readiness,
        "solver_application": application,
        "solver_module": solver_module,
        "reference_length_m": reference_length_m,
        "reference_area_m2": reference_area_m2,
        "reference_value_approval_state": (str(reference_inputs.get("approval_state")) if reference_inputs and reference_inputs.get("approval_state") is not None else None),
        "reference_value_justification": (str(reference_inputs.get("justification")) if reference_inputs and reference_inputs.get("justification") is not None else None),
        "inlet_velocity_mps": float(simulation_requirements["inlet_velocity_mps"]),
        "fluid_density_kg_m3": float(simulation_requirements["fluid_density_kg_m3"]),
        "kinematic_viscosity_m2ps": float(simulation_requirements["kinematic_viscosity_m2ps"]),
        "end_time_seconds": float(simulation_requirements["end_time_seconds"]),
        "delta_t_seconds": float(simulation_requirements["delta_t_seconds"]),
        "write_interval_steps": int(simulation_requirements["write_interval_steps"]),
        "mesh_scale_factor": mesh_scale_factor,
        "domain_extent_multiplier": domain_extent_multiplier,
    }


__all__ = [
    "DEFAULT_DELTA_T_SECONDS",
    "DEFAULT_END_TIME_SECONDS",
    "DEFAULT_FLUID_DENSITY_KG_M3",
    "DEFAULT_INLET_VELOCITY_MPS",
    "DEFAULT_KINEMATIC_VISCOSITY_M2PS",
    "DEFAULT_WRITE_INTERVAL_STEPS",
    "GEOMETRY_CONVERSION_REQUIRED",
    "STL_READY_EXECUTION",
    "WORKSPACE_VIRTUAL_ROOT",
    "platform_fs_path",
    "resolve_simulation_requirements",
    "write_openfoam_case_scaffold",
    "write_unix_text",
]
