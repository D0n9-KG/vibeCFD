import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from deerflow.config.paths import Paths


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _mesh_manifest_artifact(run_dir_name: str) -> dict:
    return {
        "selected_case_id": "research_evidence_validated_case",
        "baseline_configuration_snapshot": {"task_type": "resistance"},
        "study_definitions": [
            {
                "study_type": "mesh_independence",
                "summary_label": "Mesh Independence",
                "monitored_quantity": "Cd",
                "pass_fail_tolerance": 0.02,
                "variants": [
                    {
                        "study_type": "mesh_independence",
                        "variant_id": "coarse",
                        "variant_label": "Coarse",
                        "rationale": "Coarse mesh check",
                        "parameter_overrides": {"mesh_scale_factor": 0.75},
                    },
                    {
                        "study_type": "mesh_independence",
                        "variant_id": "baseline",
                        "variant_label": "Baseline",
                        "rationale": "Baseline anchor",
                        "parameter_overrides": {"mesh_scale_factor": 1.0},
                    },
                    {
                        "study_type": "mesh_independence",
                        "variant_id": "fine",
                        "variant_label": "Fine",
                        "rationale": "Fine mesh check",
                        "parameter_overrides": {"mesh_scale_factor": 1.25},
                    },
                ],
            }
        ],
        "artifact_virtual_paths": [
            f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/study-manifest.json"
        ],
        "study_execution_status": "completed",
    }


def test_experiment_summary_flags_incomplete_planned_variant_linkage(tmp_path):
    summaries_module = importlib.import_module(
        "deerflow.domain.submarine.reporting_summaries"
    )

    outputs_dir = tmp_path / "outputs"
    run_dir_name = "contract-gap"
    run_dir = outputs_dir / "submarine" / "solver-dispatch" / run_dir_name
    run_dir.mkdir(parents=True, exist_ok=True)

    _write_json(run_dir / "study-manifest.json", _mesh_manifest_artifact(run_dir_name))
    _write_json(
        run_dir / "experiment-manifest.json",
        {
            "experiment_id": "research-evidence-validated-case-contract-gap-resistance",
            "selected_case_id": "research_evidence_validated_case",
            "task_type": "resistance",
            "baseline_run_id": "baseline",
            "run_records": [
                {
                    "run_id": "baseline",
                    "run_role": "baseline",
                    "solver_results_virtual_path": f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/solver-results.json",
                    "run_record_virtual_path": f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/run-record.json",
                    "execution_status": "completed",
                },
                {
                    "run_id": "mesh_independence:coarse",
                    "run_role": "scientific_study_variant",
                    "study_type": "mesh_independence",
                    "variant_id": "coarse",
                    "solver_results_virtual_path": f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/studies/mesh-independence/coarse/solver-results.json",
                    "run_record_virtual_path": f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/studies/mesh-independence/coarse/run-record.json",
                    "execution_status": "completed",
                },
            ],
            "artifact_virtual_paths": [
                f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/experiment-manifest.json",
                f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/run-compare-summary.json",
            ],
            "experiment_status": "completed",
        },
    )
    _write_json(
        run_dir / "run-compare-summary.json",
        {
            "experiment_id": "research-evidence-validated-case-contract-gap-resistance",
            "baseline_run_id": "baseline",
            "artifact_virtual_paths": [
                f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/run-compare-summary.json"
            ],
            "comparisons": [
                {
                    "baseline_run_id": "baseline",
                    "candidate_run_id": "mesh_independence:coarse",
                    "study_type": "mesh_independence",
                    "variant_id": "coarse",
                    "compare_status": "completed",
                }
            ],
        },
    )

    summary = summaries_module.build_experiment_summary(
        outputs_dir=outputs_dir,
        artifact_virtual_paths=[
            f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/study-manifest.json",
            f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/experiment-manifest.json",
            f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/run-compare-summary.json",
        ],
    )

    assert summary["linkage_status"] == "incomplete"
    assert summary["expected_variant_run_ids"] == [
        "mesh_independence:coarse",
        "mesh_independence:fine",
    ]
    assert summary["recorded_variant_run_ids"] == ["mesh_independence:coarse"]
    assert summary["compared_variant_run_ids"] == ["mesh_independence:coarse"]
    assert any(
        "mesh_independence:fine" in item and "run record" in item
        for item in summary["linkage_issues"]
    )
    assert any(
        "mesh_independence:fine" in item and "compare entry" in item
        for item in summary["linkage_issues"]
    )


def test_result_report_marks_validated_run_with_incomplete_experiment_linkage_as_gap(
    tmp_path, monkeypatch
):
    report_tool_module = importlib.import_module(
        "deerflow.tools.builtins.submarine_result_report_tool"
    )
    reporting_module = importlib.import_module("deerflow.domain.submarine.reporting")
    models_module = importlib.import_module("deerflow.domain.submarine.models")

    fake_case = models_module.SubmarineCase(
        case_id="research_evidence_validated_case",
        title="Research evidence validated case",
        geometry_family="DARPA SUBOFF",
        geometry_description="Validation-backed research case",
        task_type="resistance",
        acceptance_profile=models_module.SubmarineCaseAcceptanceProfile(
            profile_id="research-evidence-validated",
            summary_zh="Validation-backed case",
            max_final_residual=0.001,
            require_force_coefficients=True,
            benchmark_targets=[
                models_module.SubmarineBenchmarkTarget(
                    metric_id="cd_at_3_05_mps",
                    quantity="Cd",
                    summary_zh="Compare Cd against reference",
                    reference_value=0.00314,
                    relative_tolerance=0.02,
                    inlet_velocity_mps=3.05,
                )
            ],
        ),
    )
    monkeypatch.setattr(reporting_module, "_resolve_selected_case", lambda _: fake_case)

    paths = Paths(tmp_path)
    thread_id = "thread-linkage-gap"
    outputs_dir = paths.sandbox_outputs_dir(thread_id)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    run_dir_name = "linkage-gap"
    solver_results_dir = outputs_dir / "submarine" / "solver-dispatch" / run_dir_name
    solver_results_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        solver_results_dir / "solver-results.json",
        {
            "solver_completed": True,
            "final_time_seconds": 200.0,
            "mesh_summary": {"mesh_ok": True, "cells": 9342},
            "latest_force_coefficients": {"Time": 200.0, "Cd": 0.00312},
            "force_coefficients_history": [
                {"Time": 160.0, "Cd": 0.00313},
                {"Time": 170.0, "Cd": 0.00312},
                {"Time": 180.0, "Cd": 0.00311},
                {"Time": 190.0, "Cd": 0.00312},
                {"Time": 200.0, "Cd": 0.00312},
            ],
            "latest_forces": {"total_force": [8.0, 0.0, 0.0]},
            "residual_summary": {
                "field_count": 2,
                "latest_time": 200.0,
                "max_final_residual": 5e-4,
            },
            "simulation_requirements": {
                "inlet_velocity_mps": 3.05,
                "fluid_density_kg_m3": 1000.0,
                "kinematic_viscosity_m2ps": 1.0e-06,
                "end_time_seconds": 200.0,
                "delta_t_seconds": 1.0,
                "write_interval_steps": 50,
            },
        },
    )
    for artifact_name, study_type in [
        ("verification-mesh-independence.json", "mesh_independence"),
        ("verification-domain-sensitivity.json", "domain_sensitivity"),
        ("verification-time-step-sensitivity.json", "time_step_sensitivity"),
    ]:
        _write_json(
            solver_results_dir / artifact_name,
            {
                "study_type": study_type,
                "status": "passed",
                "summary_zh": f"{study_type} evidence passed.",
            },
        )
    _write_json(
        solver_results_dir / "study-manifest.json",
        _mesh_manifest_artifact(run_dir_name),
    )
    _write_json(
        solver_results_dir / "experiment-manifest.json",
        {
            "experiment_id": "research-evidence-validated-case-linkage-gap-resistance",
            "selected_case_id": "research_evidence_validated_case",
            "task_type": "resistance",
            "baseline_run_id": "baseline",
            "run_records": [
                {
                    "run_id": "baseline",
                    "run_role": "baseline",
                    "execution_status": "completed",
                },
                {
                    "run_id": "mesh_independence:coarse",
                    "run_role": "scientific_study_variant",
                    "study_type": "mesh_independence",
                    "variant_id": "coarse",
                    "execution_status": "completed",
                },
            ],
            "artifact_virtual_paths": [
                f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/experiment-manifest.json",
                f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/run-compare-summary.json",
            ],
            "experiment_status": "completed",
        },
    )
    _write_json(
        solver_results_dir / "run-compare-summary.json",
        {
            "experiment_id": "research-evidence-validated-case-linkage-gap-resistance",
            "baseline_run_id": "baseline",
            "comparisons": [
                {
                    "baseline_run_id": "baseline",
                    "candidate_run_id": "mesh_independence:coarse",
                    "study_type": "mesh_independence",
                    "variant_id": "coarse",
                    "compare_status": "completed",
                }
            ],
        },
    )

    runtime = SimpleNamespace(
        state={
            "thread_data": {
                "uploads_path": str(paths.sandbox_uploads_dir(thread_id)),
                "outputs_path": str(outputs_dir),
            },
            "submarine_runtime": {
                "current_stage": "solver-dispatch",
                "task_summary": "Assess validated run with incomplete experiment linkage",
                "task_type": "resistance",
                "geometry_virtual_path": "/mnt/user-data/uploads/suboff_solid.stl",
                "geometry_family": "DARPA SUBOFF",
                "execution_readiness": "stl_ready",
                "selected_case_id": "research_evidence_validated_case",
                "stage_status": "executed",
                "review_status": "ready_for_supervisor",
                "next_recommended_stage": "result-reporting",
                "report_virtual_path": f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/dispatch-summary.md",
                "artifact_virtual_paths": [
                    f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/solver-results.json",
                    f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/study-manifest.json",
                    f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/experiment-manifest.json",
                    f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/run-compare-summary.json",
                    f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/verification-mesh-independence.json",
                    f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/verification-domain-sensitivity.json",
                    f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/verification-time-step-sensitivity.json",
                ],
                "activity_timeline": [],
            },
        },
        context={"thread_id": thread_id},
    )

    report_tool_module.submarine_result_report_tool.func(
        runtime=runtime,
        report_title="Validated linkage gap report",
        tool_call_id="tc-result-report-linkage-gap",
    )

    final_report_dir = outputs_dir / "submarine" / "reports" / "suboff_solid"
    final_payload = json.loads(
        (final_report_dir / "final-report.json").read_text(encoding="utf-8")
    )
    final_markdown = (final_report_dir / "final-report.md").read_text(encoding="utf-8")
    final_html = (final_report_dir / "final-report.html").read_text(encoding="utf-8")
    research = final_payload["research_evidence_summary"]
    gate = final_payload["scientific_supervisor_gate"]
    remediation = final_payload["scientific_remediation_summary"]
    handoff = final_payload["scientific_remediation_handoff"]

    assert final_payload["experiment_summary"]["linkage_status"] == "incomplete"
    assert final_payload["experiment_summary"]["workflow_status"] == "partial"
    assert final_payload["scientific_study_summary"]["workflow_status"] == "completed"
    assert final_payload["experiment_compare_summary"]["workflow_status"] == "completed"
    assert any(
        "mesh_independence:fine" in item
        for item in final_payload["experiment_summary"]["linkage_issues"]
    )
    assert research["validation_status"] == "validated"
    assert research["provenance_status"] == "partial"
    assert research["readiness_status"] == "validated_with_gaps"
    assert any("mesh_independence:fine" in item for item in research["evidence_gaps"])
    assert gate["gate_status"] == "claim_limited"
    assert gate["allowed_claim_level"] == "validated_with_gaps"
    assert gate["remediation_stage"] == "result-reporting"
    assert remediation["actions"][0]["action_id"] == "regenerate-research-report-linkage"
    assert remediation["actions"][0]["owner_stage"] == "result-reporting"
    assert handoff["handoff_status"] == "ready_for_auto_followup"
    assert handoff["tool_name"] == "submarine_result_report"
    assert "linkage_status" in final_markdown
    assert "workflow_status" in final_markdown
    assert "Run Status Counts" in final_markdown
    assert "Compare Status Counts" in final_markdown
    assert "mesh_independence:fine" in final_markdown
    assert "<strong>workflow_status:</strong> partial" in final_html
    assert "Missing Compare Entries" in final_html
