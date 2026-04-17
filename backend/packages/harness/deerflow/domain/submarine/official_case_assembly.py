"""Assembly helpers for pinned official OpenFOAM case-seed inputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .official_case_profiles import OfficialCaseExecutionProfile, get_official_case_profile


@dataclass(frozen=True, slots=True)
class OfficialCaseAssemblyResult:
    execution_profile: OfficialCaseExecutionProfile
    assembled_case_dir: Path
    assembled_case_virtual_paths: list[str]
    file_sources: dict[str, dict[str, str | None]]
    run_script_virtual_path: str


def _resolve_seed_actual_path(seed_virtual_path: str, uploads_dir: Path) -> Path:
    normalized = seed_virtual_path.strip()
    prefix = "/mnt/user-data/uploads/"
    if not normalized.startswith(prefix):
        raise ValueError(f"Seed path must stay under {prefix}: {seed_virtual_path}")
    relative = normalized.removeprefix(prefix)
    resolved = (uploads_dir / relative).resolve()
    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"Seed file not found: {seed_virtual_path}")
    return resolved


def _to_workspace_virtual_path(workspace_dir: Path, actual_path: Path) -> str:
    relative = actual_path.resolve().relative_to(workspace_dir.resolve())
    return f"/mnt/user-data/workspace/{relative.as_posix()}"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _source_path_for(profile: OfficialCaseExecutionProfile, relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/")
    if profile.case_id == "pitzDaily" and normalized.endswith("system/pitzDaily.blockMeshDict"):
        return "tutorials/resources/blockMesh/pitzDaily"
    return f"{profile.tutorial_root}/{normalized}"


def _record_file_source(
    *,
    profile: OfficialCaseExecutionProfile,
    relative_path: str,
    source_kind: str,
    imported_virtual_path: str | None = None,
) -> dict[str, str | None]:
    return {
        "source_commit": profile.source_commit,
        "source_path": _source_path_for(profile, relative_path),
        "source_kind": source_kind,
        "imported_virtual_path": imported_virtual_path,
    }


def _render_command_chain(
    profile: OfficialCaseExecutionProfile,
    *,
    primary_seed_relative_path: str,
) -> list[str]:
    return [
        command.format(seed_path=primary_seed_relative_path)
        for command in profile.command_chain
    ]


def _write_allrun(
    *,
    command_chain: list[str],
    case_dir: Path,
) -> None:
    script = "\n".join(
        [
            "#!/bin/sh",
            "set -eu",
            'cd "$(dirname "$0")"',
            *command_chain,
            "",
        ]
    )
    _write_text(case_dir / "Allrun", script)


def _cavity_defaults(
    simulation_requirements: Mapping[str, Any] | None,
) -> dict[str, str]:
    requirements = simulation_requirements or {}
    end_time = float(requirements.get("end_time_seconds") or 0.5)
    delta_t = float(requirements.get("delta_t_seconds") or 0.005)
    write_interval = int(requirements.get("write_interval_steps") or 20)
    return {
        "0/U": """FoamFile
{
    version 2.0;
    format ascii;
    class volVectorField;
    object U;
}

dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 0);
boundaryField
{
    movingWall
    {
        type fixedValue;
        value uniform (1 0 0);
    }
    fixedWalls
    {
        type noSlip;
    }
    frontAndBack
    {
        type empty;
    }
}
""",
        "0/p": """FoamFile
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
    movingWall
    {
        type zeroGradient;
    }
    fixedWalls
    {
        type zeroGradient;
    }
    frontAndBack
    {
        type empty;
    }
}
""",
        "constant/physicalProperties": """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object physicalProperties;
}

nu              [0 2 -1 0 0 0 0] 0.01;
""",
        "system/controlDict": f"""FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object controlDict;
}}

application     icoFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {end_time};
deltaT          {delta_t};
writeControl    timeStep;
writeInterval   {write_interval};
purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;
""",
        "system/fvSchemes": """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object fvSchemes;
}

ddtSchemes
{
    default Euler;
}

gradSchemes
{
    default Gauss linear;
}

divSchemes
{
    default none;
    div(phi,U) Gauss linear;
}

laplacianSchemes
{
    default Gauss linear orthogonal;
}

interpolationSchemes
{
    default linear;
}

snGradSchemes
{
    default orthogonal;
}
""",
        "system/fvSolution": """FoamFile
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
        solver PCG;
        preconditioner DIC;
        tolerance 1e-06;
        relTol 0.05;
    }
    pFinal
    {
        $p;
        relTol 0;
    }
    U
    {
        solver smoothSolver;
        smoother symGaussSeidel;
        tolerance 1e-05;
        relTol 0;
    }
}

PISO
{
    nCorrectors 2;
    nNonOrthogonalCorrectors 0;
    pRefCell 0;
    pRefValue 0;
}
""",
    }


def _pitzdaily_defaults(
    simulation_requirements: Mapping[str, Any] | None,
) -> dict[str, str]:
    requirements = simulation_requirements or {}
    inlet_velocity = float(requirements.get("inlet_velocity_mps") or 10.0)
    end_time = float(requirements.get("end_time_seconds") or 2000.0)
    delta_t = float(requirements.get("delta_t_seconds") or 1.0)
    write_interval = int(requirements.get("write_interval_steps") or 100)
    return {
        "0/U": f"""FoamFile
{{
    version 2.0;
    format ascii;
    class volVectorField;
    object U;
}}

dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 0);
boundaryField
{{
    inlet
    {{
        type fixedValue;
        value uniform ({inlet_velocity} 0 0);
    }}
    outlet
    {{
        type zeroGradient;
    }}
    upperWall
    {{
        type noSlip;
    }}
    lowerWall
    {{
        type noSlip;
    }}
    frontAndBack
    {{
        type empty;
    }}
}}
""",
        "0/p": """FoamFile
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
    upperWall
    {
        type zeroGradient;
    }
    lowerWall
    {
        type zeroGradient;
    }
    frontAndBack
    {
        type empty;
    }
}
""",
        "0/k": """FoamFile
{
    version 2.0;
    format ascii;
    class volScalarField;
    object k;
}

dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0.375;
boundaryField
{
    inlet
    {
        type fixedValue;
        value uniform 0.375;
    }
    outlet
    {
        type zeroGradient;
    }
    upperWall
    {
        type kqRWallFunction;
        value uniform 0.375;
    }
    lowerWall
    {
        type kqRWallFunction;
        value uniform 0.375;
    }
    frontAndBack
    {
        type empty;
    }
}
""",
        "0/epsilon": """FoamFile
{
    version 2.0;
    format ascii;
    class volScalarField;
    object epsilon;
}

dimensions      [0 2 -3 0 0 0 0];
internalField   uniform 14.855;
boundaryField
{
    inlet
    {
        type fixedValue;
        value uniform 14.855;
    }
    outlet
    {
        type zeroGradient;
    }
    upperWall
    {
        type epsilonWallFunction;
        value uniform 14.855;
    }
    lowerWall
    {
        type epsilonWallFunction;
        value uniform 14.855;
    }
    frontAndBack
    {
        type empty;
    }
}
""",
        "0/nut": """FoamFile
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
    upperWall
    {
        type nutkWallFunction;
        value uniform 0;
    }
    lowerWall
    {
        type nutkWallFunction;
        value uniform 0;
    }
    frontAndBack
    {
        type empty;
    }
}
""",
        "0/omega": """FoamFile
{
    version 2.0;
    format ascii;
    class volScalarField;
    object omega;
}

dimensions      [0 0 -1 0 0 0 0];
internalField   uniform 440.15;
boundaryField
{
    inlet
    {
        type fixedValue;
        value $internalField;
    }
    outlet
    {
        type zeroGradient;
    }
    upperWall
    {
        type omegaWallFunction;
        value $internalField;
    }
    lowerWall
    {
        type omegaWallFunction;
        value $internalField;
    }
    frontAndBack
    {
        type empty;
    }
}
""",
        "0/nuTilda": """FoamFile
{
    version 2.0;
    format ascii;
    class volScalarField;
    object nuTilda;
}

dimensions      [0 2 -1 0 0 0 0];
internalField   uniform 0;
boundaryField
{
    inlet
    {
        type fixedValue;
        value uniform 0;
    }
    outlet
    {
        type zeroGradient;
    }
    upperWall
    {
        type zeroGradient;
    }
    lowerWall
    {
        type zeroGradient;
    }
    frontAndBack
    {
        type empty;
    }
}
""",
        "0/f": """FoamFile
{
    version 2.0;
    format ascii;
    class volScalarField;
    object f;
}

dimensions      [0 0 -1 0 0 0 0];
internalField   uniform 0;
boundaryField
{
    inlet
    {
        type zeroGradient;
    }
    outlet
    {
        type zeroGradient;
    }
    upperWall
    {
        type fWallFunction;
        value uniform 0;
    }
    lowerWall
    {
        type fWallFunction;
        value uniform 0;
    }
    frontAndBack
    {
        type empty;
    }
}
""",
        "0/v2": """FoamFile
{
    version 2.0;
    format ascii;
    class volScalarField;
    object v2;
}

dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0.25;
boundaryField
{
    inlet
    {
        type fixedValue;
        value $internalField;
    }
    outlet
    {
        type zeroGradient;
    }
    upperWall
    {
        type v2WallFunction;
        value $internalField;
    }
    lowerWall
    {
        type v2WallFunction;
        value $internalField;
    }
    frontAndBack
    {
        type empty;
    }
}
""",
        "constant/physicalProperties": """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object physicalProperties;
}

viscosityModel  constant;

nu              1e-05;
""",
        "constant/momentumTransport": """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object momentumTransport;
}

simulationType  RAS;

RAS
{
    model           kEpsilon;
    turbulence      on;
    viscosityModel  Newtonian;
}
""",
        "system/controlDict": f"""FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object controlDict;
}}

solver          incompressibleFluid;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {end_time:g};
deltaT          {delta_t:g};
writeControl    timeStep;
writeInterval   {write_interval};
purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;

cacheTemporaryObjects
(
    kEpsilon:G
);
""",
        "system/fvSchemes": """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object fvSchemes;
}

ddtSchemes
{
    default         steadyState;
}

gradSchemes
{
    default         Gauss linear;
}

divSchemes
{
    default         none;
    div(phi,U)      bounded Gauss linearUpwind grad(U);
    div(phi,k)      bounded Gauss limitedLinear 1;
    div(phi,epsilon) bounded Gauss limitedLinear 1;
    div(phi,omega)  bounded Gauss limitedLinear 1;
    div(phi,v2)     bounded Gauss limitedLinear 1;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
    div(nonlinearStress) Gauss linear;
}

laplacianSchemes
{
    default         Gauss linear corrected;
}

interpolationSchemes
{
    default         linear;
}

snGradSchemes
{
    default         corrected;
}

wallDist
{
    method meshWave;
}
""",
        "system/fvSolution": """FoamFile
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
        tolerance       1e-06;
        relTol          0.1;
        smoother        GaussSeidel;
    }
    pcorr
    {
        solver          GAMG;
        tolerance 1e-06;
        relTol 0;
        smoother        GaussSeidel;
    }
    "(U|k|epsilon|omega|f|v2)"
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-05;
        relTol          0.1;
    }
}

SIMPLE
{
    nNonOrthogonalCorrectors 0;
    consistent      yes;

    residualControl
    {
        p               1e-2;
        U               1e-3;
        "(k|epsilon|omega|f|v2)" 1e-3;
    }
}

relaxationFactors
{
    equations
    {
        U               0.9;
        ".*"            0.9;
    }
}
""",
        "system/functions": """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object functions;
}

#includeFunc streamlinesLine
(
    name=streamlines,
    start=(-0.0205 0.001 0.00001),
    end=(-0.0205 0.0251 0.00001),
    nPoints=10,
    fields=(p k U)
)

#includeFunc writeObjects(kEpsilon:G)
""",
    }


def _default_case_files(
    *,
    case_id: str,
    simulation_requirements: Mapping[str, Any] | None,
) -> dict[str, str]:
    if case_id == "cavity":
        return _cavity_defaults(simulation_requirements)
    if case_id == "pitzDaily":
        return _pitzdaily_defaults(simulation_requirements)
    raise ValueError(f"Unsupported official case id: {case_id}")


def assemble_official_case_seed(
    *,
    case_id: str,
    seed_virtual_paths: list[str],
    uploads_dir: Path,
    workspace_dir: Path,
    outputs_dir: Path,
    run_dir_name: str,
    source_commit: str,
    simulation_requirements: Mapping[str, Any] | None = None,
) -> OfficialCaseAssemblyResult:
    del outputs_dir

    profile = get_official_case_profile(case_id)
    if source_commit and source_commit != profile.source_commit:
        raise ValueError(
            f"Official case `{case_id}` is pinned to {profile.source_commit}, got {source_commit}"
        )
    if not seed_virtual_paths:
        raise ValueError(f"No seed files provided for official case `{case_id}`")

    case_dir = workspace_dir / "official-openfoam" / run_dir_name / "openfoam-case"
    case_dir.mkdir(parents=True, exist_ok=True)

    assembled_case_virtual_paths: list[str] = []
    file_sources: dict[str, dict[str, str | None]] = {}
    primary_seed_relative_path = ""
    for seed_virtual_path in seed_virtual_paths:
        source_path = _resolve_seed_actual_path(seed_virtual_path, uploads_dir)
        if case_id == "cavity":
            relative_path = "system/blockMeshDict"
        elif case_id == "pitzDaily":
            relative_path = "system/pitzDaily.blockMeshDict"
        else:
            raise ValueError(f"Unsupported official case id: {case_id}")
        destination = case_dir / Path(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source_path.read_bytes())
        if not primary_seed_relative_path:
            primary_seed_relative_path = relative_path
        assembled_case_virtual_paths.append(
            _to_workspace_virtual_path(workspace_dir, destination)
        )
        file_sources[relative_path] = _record_file_source(
            profile=profile,
            relative_path=relative_path,
            source_kind="imported_seed",
            imported_virtual_path=seed_virtual_path,
        )

    for relative_path, content in _default_case_files(
        case_id=case_id,
        simulation_requirements=simulation_requirements,
    ).items():
        if relative_path in file_sources:
            continue
        destination = case_dir / Path(relative_path)
        _write_text(destination, content)
        assembled_case_virtual_paths.append(
            _to_workspace_virtual_path(workspace_dir, destination)
        )
        file_sources[relative_path] = _record_file_source(
            profile=profile,
            relative_path=relative_path,
            source_kind="synthesized_from_official_default",
        )

    command_chain = _render_command_chain(
        profile,
        primary_seed_relative_path=primary_seed_relative_path,
    )
    _write_allrun(command_chain=command_chain, case_dir=case_dir)
    allrun_path = case_dir / "Allrun"
    run_script_virtual_path = _to_workspace_virtual_path(workspace_dir, allrun_path)
    assembled_case_virtual_paths.append(run_script_virtual_path)
    file_sources["Allrun"] = {
        "source_commit": profile.source_commit,
        "source_path": None,
        "source_kind": "project_compatibility_adaptation",
        "imported_virtual_path": None,
    }

    return OfficialCaseAssemblyResult(
        execution_profile=profile,
        assembled_case_dir=case_dir,
        assembled_case_virtual_paths=assembled_case_virtual_paths,
        file_sources=file_sources,
        run_script_virtual_path=run_script_virtual_path,
    )
