import importlib

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


def test_submarine_case_library_exposes_effective_scientific_study_definitions():
    studies_module = importlib.import_module("deerflow.domain.submarine.studies")
    library = load_case_library()
    case = library.case_index["darpa_suboff_bare_hull_resistance"]

    definitions = studies_module.build_effective_scientific_study_definitions(
        selected_case=case,
        simulation_requirements={
            "inlet_velocity_mps": 5.0,
            "delta_t_seconds": 1.0,
            "end_time_seconds": 200.0,
        },
    )

    assert [item.study_type for item in definitions] == [
        "mesh_independence",
        "domain_sensitivity",
        "time_step_sensitivity",
    ]
    assert definitions[0].monitored_quantity == "Cd"
    assert definitions[0].pass_fail_tolerance == 0.02
    assert [variant.variant_id for variant in definitions[0].variants] == [
        "coarse",
        "baseline",
        "fine",
    ]
    assert definitions[0].variants[0].parameter_overrides["mesh_scale_factor"] == 0.75


def test_submarine_case_library_builds_scientific_study_manifest():
    studies_module = importlib.import_module("deerflow.domain.submarine.studies")
    library = load_case_library()
    case = library.case_index["darpa_suboff_bare_hull_resistance"]

    manifest = studies_module.build_scientific_study_manifest(
        selected_case=case,
        simulation_requirements={
            "inlet_velocity_mps": 5.0,
            "fluid_density_kg_m3": 1000.0,
            "kinematic_viscosity_m2ps": 1e-06,
            "end_time_seconds": 200.0,
            "delta_t_seconds": 1.0,
            "write_interval_steps": 50,
        },
        baseline_configuration_snapshot={
            "task_type": case.task_type,
            "recommended_solver": case.recommended_solver,
        },
    )

    assert manifest.selected_case_id == "darpa_suboff_bare_hull_resistance"
    assert manifest.study_execution_status == "planned"
    assert manifest.baseline_configuration_snapshot["task_type"] == "resistance"
    assert len(manifest.study_definitions) == 3
    assert manifest.study_definitions[1].variants[2].parameter_overrides["domain_extent_multiplier"] == 1.2
    assert manifest.study_definitions[2].variants[0].parameter_overrides["delta_t_multiplier"] == 2.0


def test_submarine_domain_exposes_experiment_run_records():
    models_module = importlib.import_module("deerflow.domain.submarine.models")

    record = models_module.SubmarineExperimentRunRecord(
        run_id="mesh_independence:coarse",
        experiment_id="darpa-suboff-bare-hull-resistance-study-execution-demo-resistance",
        run_role="scientific_study_variant",
        study_type="mesh_independence",
        variant_id="coarse",
        solver_results_virtual_path=(
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/studies/"
            "mesh-independence/coarse/solver-results.json"
        ),
        run_record_virtual_path=(
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/studies/"
            "mesh-independence/coarse/run-record.json"
        ),
        execution_status="completed",
    )

    assert record.run_id == "mesh_independence:coarse"
    assert record.study_type == "mesh_independence"
    assert record.variant_id == "coarse"
    assert record.run_role == "scientific_study_variant"


def test_submarine_domain_builds_experiment_compare_summary():
    experiments_module = importlib.import_module("deerflow.domain.submarine.experiments")

    experiment_id = experiments_module.build_experiment_id(
        selected_case_id="darpa_suboff_bare_hull_resistance",
        run_dir_name="study-execution-demo",
        task_type="resistance",
    )
    baseline_run_id = experiments_module.build_experiment_run_id(
        study_type=None,
        variant_id=None,
    )
    coarse_run_id = experiments_module.build_experiment_run_id(
        study_type="mesh_independence",
        variant_id="coarse",
    )

    summary = experiments_module.build_run_compare_summary(
        experiment_id=experiment_id,
        baseline_run_id=baseline_run_id,
        baseline_record={
            "run_id": baseline_run_id,
            "metric_snapshot": {
                "Cd": 0.12,
                "Fx": 8.0,
                "final_time_seconds": 200.0,
                "mesh_cells": 9342,
            },
        },
        candidate_records=[
            {
                "run_id": coarse_run_id,
                "study_type": "mesh_independence",
                "variant_id": "coarse",
                "execution_status": "completed",
                "metric_snapshot": {
                    "Cd": 0.1212,
                    "Fx": 8.18,
                    "final_time_seconds": 200.0,
                    "mesh_cells": 7010,
                },
            }
        ],
    )

    assert experiment_id == "darpa-suboff-bare-hull-resistance-study-execution-demo-resistance"
    assert baseline_run_id == "baseline"
    assert coarse_run_id == "mesh_independence:coarse"
    assert summary.experiment_id == experiment_id
    assert summary.baseline_run_id == "baseline"
    assert len(summary.comparisons) == 1
    assert summary.comparisons[0].candidate_run_id == "mesh_independence:coarse"


def test_submarine_domain_exposes_research_evidence_summary_model():
    models_module = importlib.import_module("deerflow.domain.submarine.models")

    summary = models_module.SubmarineResearchEvidenceSummary(
        readiness_status="verified_but_not_validated",
        verification_status="passed",
        validation_status="missing_validation_reference",
        provenance_status="traceable",
        confidence="medium",
        blocking_issues=[],
        evidence_gaps=["No applicable benchmark target was available for this run."],
        passed_evidence=["Scientific verification requirements passed."],
        benchmark_highlights=[],
        provenance_highlights=["Experiment manifest and compare summary are available."],
        artifact_virtual_paths=[
            "/mnt/user-data/outputs/submarine/reports/demo/research-evidence-summary.json"
        ],
    )

    assert summary.readiness_status == "verified_but_not_validated"
    assert summary.validation_status == "missing_validation_reference"
    assert summary.provenance_status == "traceable"


def test_submarine_domain_builds_research_evidence_summary_semantics():
    evidence_module = importlib.import_module("deerflow.domain.submarine.evidence")

    verified_only = evidence_module.build_research_evidence_summary(
        acceptance_profile=None,
        acceptance_assessment={
            "status": "ready_for_review",
            "confidence": "medium",
            "benchmark_comparisons": [],
            "blocking_issues": [],
        },
        scientific_verification_assessment={
            "status": "research_ready",
            "confidence": "high",
            "blocking_issues": [],
            "missing_evidence": [],
            "passed_requirements": ["Scientific verification requirements passed."],
        },
        scientific_study_summary={
            "study_execution_status": "completed",
            "manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
                "/mnt/user-data/outputs/submarine/solver-dispatch/demo/verification-mesh-independence.json",
            ],
        },
        experiment_summary={
            "experiment_status": "completed",
            "manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
            "compare_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
            "run_count": 7,
        },
        output_delivery_plan=[
            {
                "output_id": "drag_coefficient",
                "delivery_status": "delivered",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json"
                ],
            }
        ],
        artifact_virtual_paths=[
            "/mnt/user-data/outputs/submarine/reports/demo/final-report.json",
            "/mnt/user-data/outputs/submarine/reports/demo/delivery-readiness.json",
        ],
    )
    assert verified_only["verification_status"] == "passed"
    assert verified_only["validation_status"] == "missing_validation_reference"
    assert verified_only["provenance_status"] == "traceable"
    assert verified_only["readiness_status"] == "verified_but_not_validated"

    research_ready = evidence_module.build_research_evidence_summary(
        acceptance_profile={
            "benchmark_targets": [{"metric_id": "cd_at_3_05_mps"}],
        },
        acceptance_assessment={
            "status": "ready_for_review",
            "confidence": "high",
            "benchmark_comparisons": [
                {
                    "metric_id": "cd_at_3_05_mps",
                    "status": "passed",
                    "detail": "Benchmark cd_at_3_05_mps passed.",
                }
            ],
            "blocking_issues": [],
        },
        scientific_verification_assessment={
            "status": "research_ready",
            "confidence": "high",
            "blocking_issues": [],
            "missing_evidence": [],
            "passed_requirements": ["Scientific verification requirements passed."],
        },
        scientific_study_summary={
            "study_execution_status": "completed",
            "manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json"
            ],
        },
        experiment_summary={
            "experiment_status": "completed",
            "manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
            "compare_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
            "run_count": 7,
        },
        output_delivery_plan=[
            {
                "output_id": "drag_coefficient",
                "delivery_status": "delivered",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json"
                ],
            }
        ],
        artifact_virtual_paths=[
            "/mnt/user-data/outputs/submarine/reports/demo/final-report.json",
            "/mnt/user-data/outputs/submarine/reports/demo/delivery-readiness.json",
            "/mnt/user-data/outputs/submarine/reports/demo/research-evidence-summary.json",
        ],
    )
    assert research_ready["validation_status"] == "validated"
    assert research_ready["readiness_status"] == "research_ready"

    validation_failed = evidence_module.build_research_evidence_summary(
        acceptance_profile={
            "benchmark_targets": [{"metric_id": "cd_at_3_05_mps"}],
        },
        acceptance_assessment={
            "status": "blocked",
            "confidence": "low",
            "benchmark_comparisons": [
                {
                    "metric_id": "cd_at_3_05_mps",
                    "status": "blocked",
                    "detail": "Benchmark cd_at_3_05_mps exceeded tolerance.",
                }
            ],
            "blocking_issues": ["Benchmark cd_at_3_05_mps exceeded tolerance."],
        },
        scientific_verification_assessment={
            "status": "research_ready",
            "confidence": "high",
            "blocking_issues": [],
            "missing_evidence": [],
            "passed_requirements": ["Scientific verification requirements passed."],
        },
        scientific_study_summary={
            "study_execution_status": "completed",
            "manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
            "artifact_virtual_paths": [],
        },
        experiment_summary={
            "experiment_status": "completed",
            "manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
            "compare_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
            "run_count": 7,
        },
        output_delivery_plan=[],
        artifact_virtual_paths=[],
    )
    assert validation_failed["validation_status"] == "validation_failed"
    assert validation_failed["readiness_status"] == "blocked"

    validated_with_gaps = evidence_module.build_research_evidence_summary(
        acceptance_profile={
            "benchmark_targets": [{"metric_id": "cd_at_3_05_mps"}],
        },
        acceptance_assessment={
            "status": "ready_for_review",
            "confidence": "high",
            "benchmark_comparisons": [
                {
                    "metric_id": "cd_at_3_05_mps",
                    "status": "passed",
                    "detail": "Benchmark cd_at_3_05_mps passed.",
                }
            ],
            "blocking_issues": [],
        },
        scientific_verification_assessment={
            "status": "research_ready",
            "confidence": "high",
            "blocking_issues": [],
            "missing_evidence": [],
            "passed_requirements": ["Scientific verification requirements passed."],
        },
        scientific_study_summary=None,
        experiment_summary=None,
        output_delivery_plan=[
            {
                "output_id": "drag_coefficient",
                "delivery_status": "planned",
                "artifact_virtual_paths": [],
            }
        ],
        artifact_virtual_paths=[
            "/mnt/user-data/outputs/submarine/reports/demo/final-report.json"
        ],
    )
    assert validated_with_gaps["validation_status"] == "validated"
    assert validated_with_gaps["provenance_status"] == "partial"
    assert validated_with_gaps["readiness_status"] == "validated_with_gaps"


def test_submarine_domain_exposes_scientific_supervisor_gate_model():
    contracts_module = importlib.import_module("deerflow.domain.submarine.contracts")

    gate = contracts_module.SubmarineScientificSupervisorGate(
        gate_status="claim_limited",
        allowed_claim_level="verified_but_not_validated",
        source_readiness_status="verified_but_not_validated",
        recommended_stage="supervisor-review",
        remediation_stage="solver-dispatch",
        advisory_notes=["External validation is still missing."],
    )

    assert gate.gate_status == "claim_limited"
    assert gate.allowed_claim_level == "verified_but_not_validated"
    assert gate.recommended_stage == "supervisor-review"


def test_submarine_domain_execution_plan_includes_supervisor_review():
    contracts_module = importlib.import_module("deerflow.domain.submarine.contracts")

    plan = contracts_module.build_execution_plan(confirmation_status="confirmed")

    assert plan[-1]["role_id"] == "supervisor-review"
    assert plan[-1]["status"] == "pending"


def test_submarine_domain_execution_plan_includes_scientific_capability_roles():
    contracts_module = importlib.import_module("deerflow.domain.submarine.contracts")

    plan = contracts_module.build_execution_plan(confirmation_status="confirmed")
    role_ids = [item["role_id"] for item in plan]

    assert role_ids == [
        "claude-code-supervisor",
        "task-intelligence",
        "geometry-preflight",
        "solver-dispatch",
        "scientific-study",
        "experiment-compare",
        "scientific-verification",
        "result-reporting",
        "scientific-followup",
        "supervisor-review",
    ]


def test_submarine_domain_builds_scientific_supervisor_gate_semantics():
    supervision_module = importlib.import_module("deerflow.domain.submarine.supervision")

    research_ready_gate = supervision_module.build_scientific_supervisor_gate(
        research_evidence_summary={
            "readiness_status": "research_ready",
            "verification_status": "passed",
            "validation_status": "validated",
            "provenance_status": "traceable",
            "blocking_issues": [],
            "evidence_gaps": [],
        }
    )
    assert research_ready_gate["gate_status"] == "ready_for_claim"
    assert research_ready_gate["allowed_claim_level"] == "research_ready"
    assert research_ready_gate["recommended_stage"] == "supervisor-review"
    assert research_ready_gate["remediation_stage"] is None

    verified_only_gate = supervision_module.build_scientific_supervisor_gate(
        research_evidence_summary={
            "readiness_status": "verified_but_not_validated",
            "verification_status": "passed",
            "validation_status": "missing_validation_reference",
            "provenance_status": "traceable",
            "blocking_issues": [],
            "evidence_gaps": ["No applicable benchmark target was available for this run."],
        }
    )
    assert verified_only_gate["gate_status"] == "claim_limited"
    assert verified_only_gate["allowed_claim_level"] == "verified_but_not_validated"
    assert verified_only_gate["recommended_stage"] == "supervisor-review"
    assert verified_only_gate["remediation_stage"] == "solver-dispatch"
    assert verified_only_gate["advisory_notes"] == [
        "External validation evidence is still missing for this run."
    ]

    validated_with_gaps_gate = supervision_module.build_scientific_supervisor_gate(
        research_evidence_summary={
            "readiness_status": "validated_with_gaps",
            "verification_status": "passed",
            "validation_status": "validated",
            "provenance_status": "partial",
            "blocking_issues": [],
            "evidence_gaps": ["Experiment registry entrypoints are incomplete."],
        }
    )
    assert validated_with_gaps_gate["gate_status"] == "claim_limited"
    assert validated_with_gaps_gate["allowed_claim_level"] == "validated_with_gaps"
    assert validated_with_gaps_gate["recommended_stage"] == "supervisor-review"
    assert validated_with_gaps_gate["remediation_stage"] == "result-reporting"
    assert validated_with_gaps_gate["advisory_notes"] == [
        "Scientific evidence is validated, but reporting and provenance gaps still limit the claim level."
    ]

    blocked_gate = supervision_module.build_scientific_supervisor_gate(
        research_evidence_summary={
            "readiness_status": "blocked",
            "blocking_issues": ["Benchmark cd_at_3_05_mps exceeded tolerance."],
            "evidence_gaps": [],
            "verification_status": "blocked",
            "validation_status": "validation_failed",
            "provenance_status": "partial",
        }
    )
    assert blocked_gate["gate_status"] == "blocked"
    assert blocked_gate["allowed_claim_level"] == "delivery_only"
    assert blocked_gate["recommended_stage"] == "solver-dispatch"


def test_submarine_domain_builds_scientific_remediation_plan_semantics():
    remediation_module = importlib.import_module("deerflow.domain.submarine.remediation")

    missing_study_plan = remediation_module.build_scientific_remediation_summary(
        scientific_supervisor_gate={
            "gate_status": "blocked",
            "allowed_claim_level": "delivery_only",
            "recommended_stage": "solver-dispatch",
            "remediation_stage": "solver-dispatch",
        },
        research_evidence_summary={
            "readiness_status": "blocked",
            "evidence_gaps": [
                "Scientific verification study evidence is incomplete."
            ],
        },
        scientific_verification_assessment={
            "missing_evidence": [
                "verification-mesh-independence.json is missing."
            ]
        },
        scientific_study_summary={
            "manifest_virtual_path": "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
            "artifact_virtual_paths": [
                "/mnt/user-data/outputs/submarine/solver-dispatch/demo/verification-mesh-independence.json"
            ],
            "studies": [
                {
                    "study_type": "mesh_independence",
                    "verification_status": "missing_evidence",
                }
            ],
        },
    )
    assert missing_study_plan["plan_status"] == "recommended"
    assert missing_study_plan["current_claim_level"] == "delivery_only"
    assert missing_study_plan["target_claim_level"] == "research_ready"
    assert missing_study_plan["recommended_stage"] == "solver-dispatch"
    assert missing_study_plan["actions"][0]["action_id"] == "execute-scientific-studies"
    assert missing_study_plan["actions"][0]["owner_stage"] == "solver-dispatch"
    assert missing_study_plan["actions"][0]["execution_mode"] == "auto_executable"

    missing_validation_plan = remediation_module.build_scientific_remediation_summary(
        scientific_supervisor_gate={
            "gate_status": "claim_limited",
            "allowed_claim_level": "verified_but_not_validated",
            "recommended_stage": "supervisor-review",
            "remediation_stage": "solver-dispatch",
        },
        research_evidence_summary={
            "readiness_status": "verified_but_not_validated",
            "validation_status": "missing_validation_reference",
            "evidence_gaps": [
                "No applicable benchmark target was available for this run."
            ],
        },
        scientific_verification_assessment={"missing_evidence": []},
        scientific_study_summary={"studies": []},
    )
    assert missing_validation_plan["plan_status"] == "recommended"
    assert missing_validation_plan["current_claim_level"] == "verified_but_not_validated"
    assert missing_validation_plan["recommended_stage"] == "supervisor-review"
    assert missing_validation_plan["actions"][0]["action_id"] == "attach-validation-reference"
    assert missing_validation_plan["actions"][0]["owner_stage"] == "supervisor-review"
    assert missing_validation_plan["actions"][0]["execution_mode"] == "manual_required"

    research_ready_plan = remediation_module.build_scientific_remediation_summary(
        scientific_supervisor_gate={
            "gate_status": "ready_for_claim",
            "allowed_claim_level": "research_ready",
            "recommended_stage": "supervisor-review",
            "remediation_stage": None,
        },
        research_evidence_summary={
            "readiness_status": "research_ready",
            "validation_status": "validated",
            "evidence_gaps": [],
        },
        scientific_verification_assessment={"missing_evidence": []},
        scientific_study_summary={"studies": []},
    )
    assert research_ready_plan["plan_status"] == "not_needed"
    assert research_ready_plan["current_claim_level"] == "research_ready"
    assert research_ready_plan["target_claim_level"] == "research_ready"
    assert research_ready_plan["actions"] == []


def test_submarine_domain_builds_scientific_remediation_handoff_semantics():
    handoff_module = importlib.import_module("deerflow.domain.submarine.handoff")

    auto_handoff = handoff_module.build_scientific_remediation_handoff(
        snapshot={
            "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
            "task_summary": "Assess missing scientific study evidence",
            "confirmation_status": "confirmed",
            "execution_preference": "preflight_then_execute",
            "task_type": "resistance",
            "selected_case_id": "darpa_suboff_bare_hull_resistance",
            "simulation_requirements": {
                "inlet_velocity_mps": 3.05,
                "end_time_seconds": 200.0,
                "delta_t_seconds": 1.0,
            },
        },
        scientific_remediation_summary={
            "plan_status": "recommended",
            "actions": [
                {
                    "action_id": "execute-scientific-studies",
                    "title": "Execute scientific verification studies",
                    "summary": "Run the planned scientific study variants.",
                    "owner_stage": "solver-dispatch",
                    "execution_mode": "auto_executable",
                    "evidence_gap": "verification-mesh-independence.json is missing.",
                }
            ],
        },
    )
    assert auto_handoff["handoff_status"] == "ready_for_auto_followup"
    assert auto_handoff["recommended_action_id"] == "execute-scientific-studies"
    assert auto_handoff["tool_name"] == "submarine_solver_dispatch"
    assert auto_handoff["tool_args"]["geometry_path"] == "/mnt/user-data/uploads/suboff_solid.stl"
    assert auto_handoff["tool_args"]["confirmation_status"] == "confirmed"
    assert auto_handoff["tool_args"]["execution_preference"] == "preflight_then_execute"
    assert auto_handoff["tool_args"]["execute_scientific_studies"] is True

    manual_handoff = handoff_module.build_scientific_remediation_handoff(
        snapshot={
            "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
            "task_summary": "Assess validation evidence",
            "task_type": "resistance",
        },
        scientific_remediation_summary={
            "plan_status": "recommended",
            "actions": [
                {
                    "action_id": "attach-validation-reference",
                    "title": "Attach validation reference",
                    "owner_stage": "supervisor-review",
                    "execution_mode": "manual_required",
                    "evidence_gap": "No applicable benchmark target was available for this run.",
                }
            ],
        },
    )
    assert manual_handoff["handoff_status"] == "manual_followup_required"
    assert manual_handoff["tool_name"] is None
    assert manual_handoff["manual_actions"][0]["action_id"] == "attach-validation-reference"

    no_handoff = handoff_module.build_scientific_remediation_handoff(
        snapshot={
            "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
            "task_summary": "Research-ready run",
            "task_type": "resistance",
        },
        scientific_remediation_summary={
            "plan_status": "not_needed",
            "actions": [],
        },
    )
    assert no_handoff["handoff_status"] == "not_needed"
    assert no_handoff["tool_name"] is None


def test_submarine_domain_exposes_figure_manifest_contract():
    figure_delivery_module = importlib.import_module(
        "deerflow.domain.submarine.figure_delivery"
    )

    manifest = figure_delivery_module.build_figure_manifest(
        run_dir_name="demo-run",
        figures=[
            {
                "figure_id": "surface_pressure_contour:latest",
                "output_id": "surface_pressure_contour",
                "title": "Surface Pressure Figure",
                "caption": "Surface pressure rendered from the latest exported samples.",
                "render_status": "rendered",
                "artifact_virtual_paths": [
                    "/mnt/user-data/outputs/submarine/solver-dispatch/demo-run/surface-pressure.png"
                ],
            }
        ],
    )

    assert manifest["run_dir_name"] == "demo-run"
    assert manifest["figure_count"] == 1
    assert manifest["figures"][0]["figure_id"] == "surface_pressure_contour:latest"
    assert manifest["figures"][0]["render_status"] == "rendered"


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
