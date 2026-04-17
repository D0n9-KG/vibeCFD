"""Pinned execution profiles for supported official OpenFOAM tutorial cases."""

from __future__ import annotations

from dataclasses import dataclass

PINNED_OPENFOAM_13_COMMIT = "441953dfbb4270dd54e14672e194e4a4a478afc4"


@dataclass(frozen=True, slots=True)
class OfficialCaseExecutionProfile:
    case_id: str
    source_commit: str
    command_chain: list[str]
    tutorial_root: str


_PROFILES: dict[str, OfficialCaseExecutionProfile] = {
    "cavity": OfficialCaseExecutionProfile(
        case_id="cavity",
        source_commit=PINNED_OPENFOAM_13_COMMIT,
        command_chain=["blockMesh", "icoFoam"],
        tutorial_root="tutorials/legacy/incompressible/icoFoam/cavity/cavity",
    ),
    "pitzDaily": OfficialCaseExecutionProfile(
        case_id="pitzDaily",
        source_commit=PINNED_OPENFOAM_13_COMMIT,
        command_chain=["blockMesh -dict {seed_path}", "foamRun"],
        tutorial_root="tutorials/incompressibleFluid/pitzDailySteady",
    ),
}


def get_official_case_profile(case_id: str) -> OfficialCaseExecutionProfile:
    try:
        return _PROFILES[case_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported official case id: {case_id}") from exc


def get_official_case_default_simulation_requirements(
    case_id: str,
) -> dict[str, float | int]:
    if case_id == "cavity":
        return {
            "inlet_velocity_mps": 1.0,
            "fluid_density_kg_m3": 1.0,
            "kinematic_viscosity_m2ps": 0.01,
            "end_time_seconds": 0.5,
            "delta_t_seconds": 0.005,
            "write_interval_steps": 20,
        }
    if case_id == "pitzDaily":
        return {
            "inlet_velocity_mps": 10.0,
            "fluid_density_kg_m3": 1.0,
            "kinematic_viscosity_m2ps": 1e-05,
            "end_time_seconds": 2000.0,
            "delta_t_seconds": 1.0,
            "write_interval_steps": 100,
        }
    raise ValueError(f"Unsupported official case id: {case_id}")


def should_pin_official_case_defaults(task_description: str | None) -> bool:
    description = (task_description or "").strip().lower()
    if not description:
        return True

    if any(
        marker in description
        for marker in (
            "default",
            "defaults",
            "\u9ed8\u8ba4",
            "\u5b98\u65b9\u9ed8\u8ba4",
            "\u6309\u9ed8\u8ba4\u8bbe\u7f6e",
            "\u6309\u5b98\u65b9\u9ed8\u8ba4",
        )
    ):
        return True

    return not any(character.isdigit() for character in description)
