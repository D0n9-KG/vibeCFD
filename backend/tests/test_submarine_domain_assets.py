from deerflow.domain.submarine.assets import get_submarine_domain_root
from deerflow.domain.submarine.contracts import SubmarineRuntimeRequest
from deerflow.domain.submarine.library import load_case_library, load_skill_registry
from deerflow.domain.submarine.verification import (
    build_effective_scientific_verification_requirements,
)


def test_submarine_domain_root_and_assets_load():
    root = get_submarine_domain_root()

    assert (root / "cases" / "index.json").exists()
    assert (root / "skills" / "index.json").exists()


def test_load_case_library_returns_rankable_cases():
    library = load_case_library()

    assert library.cases
    assert "darpa_suboff_bare_hull_resistance" in library.case_index
    assert library.case_index["darpa_suboff_bare_hull_resistance"].task_type == "resistance"


def test_submarine_case_library_exposes_case_acceptance_profiles():
    library = load_case_library()

    profile = library.case_index[
        "darpa_suboff_bare_hull_resistance"
    ].acceptance_profile

    assert profile is not None
    assert profile.profile_id == "darpa-suboff-resistance-baseline"
    assert profile.minimum_completed_fraction_of_planned_time == 0.95
    assert profile.max_final_residual == 0.001
    assert "solver-results.json" in profile.required_artifacts
    assert profile.benchmark_targets
    assert profile.benchmark_targets[0].metric_id == "cd_at_3_05_mps"
    assert profile.benchmark_targets[0].reference_value == 0.00314


def test_submarine_case_library_exposes_effective_scientific_verification_requirements():
    library = load_case_library()
    case = library.case_index["darpa_suboff_bare_hull_resistance"]

    requirements = build_effective_scientific_verification_requirements(
        acceptance_profile=case.acceptance_profile,
        task_type=case.task_type,
    )

    assert [item.requirement_id for item in requirements] == [
        "final_residual_threshold",
        "force_coefficient_tail_stability",
        "mesh_independence_study",
        "domain_sensitivity_study",
        "time_step_sensitivity_study",
    ]
    assert requirements[0].check_type == "max_final_residual"
    assert requirements[0].max_value == 0.001
    assert requirements[1].check_type == "force_coefficient_tail_stability"
    assert requirements[1].force_coefficient == "Cd"
    assert requirements[1].minimum_history_samples == 5
    assert requirements[2].required_artifacts == ["verification-mesh-independence.json"]


def test_load_skill_registry_returns_submarine_skill_defs():
    registry = load_skill_registry()

    assert registry.skills
    assert "geometry-check" in registry.skill_index
    assert "geometry-check.inspect" in registry.skill_index["geometry-check"].required_tools
    assert "solver-dispatch" in registry.skill_index


def test_submarine_runtime_contract_has_supervisor_fields():
    contract = SubmarineRuntimeRequest(
        task_summary="评估阻力",
        confirmation_status="confirmed",
        uploaded_geometry_path="/mnt/user-data/uploads/submarine.stl",
    )

    assert contract.confirmation_status == "confirmed"
    assert contract.uploaded_geometry_path.endswith(".stl")


def test_submarine_case_library_keeps_stl_only_v1_boundary():
    library = load_case_library()

    offenders = []
    disallowed_markers = ("x_t", "step", "obj", "ply", "3mf")
    for case in library.cases:
        for requirement in case.input_requirements:
            normalized = requirement.lower()
            if any(marker in normalized for marker in disallowed_markers):
                offenders.append((case.case_id, requirement))

    assert offenders == []
