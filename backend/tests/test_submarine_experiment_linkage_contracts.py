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


def _write_ascii_stl(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "solid demo\n  facet normal 0 0 0\n    outer loop\n      vertex 0 0 0\n      vertex 1 0 0\n      vertex 0 1 0\n    endloop\n  endfacet\nendsolid demo\n",
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
        "artifact_virtual_paths": [f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/study-manifest.json"],
        "study_execution_status": "completed",
    }


def test_experiment_summary_flags_incomplete_planned_variant_linkage(tmp_path):
    summaries_module = importlib.import_module("deerflow.domain.submarine.reporting_summaries")

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
            "artifact_virtual_paths": [f"/mnt/user-data/outputs/submarine/solver-dispatch/{run_dir_name}/run-compare-summary.json"],
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
    assert any("mesh_independence:fine" in item and "run record" in item for item in summary["linkage_issues"])
    assert any("mesh_independence:fine" in item and "compare entry" in item for item in summary["linkage_issues"])


def test_runtime_request_accepts_declared_custom_variants_and_defaults_compare_target():
    contracts_module = importlib.import_module("deerflow.domain.submarine.contracts")
    experiments_module = importlib.import_module("deerflow.domain.submarine.experiments")

    request = contracts_module.SubmarineRuntimeRequest(
        task_summary="Register a custom pressure sweep experiment variant",
        uploaded_geometry_path="/mnt/user-data/uploads/custom-variant-demo.stl",
        custom_variants=[
            {
                "variant_id": "pressure-sweep",
                "variant_label": "Pressure Sweep",
                "parameter_overrides": {"outlet_pressure_pa": 250},
                "rationale": "Probe outlet pressure sensitivity.",
            }
        ],
    )

    assert request.custom_variants[0].compare_target_run_id == "baseline"
    assert (
        experiments_module.build_experiment_run_id(
            study_type=None,
            variant_id=request.custom_variants[0].variant_id,
            run_role="custom_variant",
        )
        == "custom:pressure-sweep"
    )


def test_solver_dispatch_registers_declared_custom_variants_before_execution(
    tmp_path,
    monkeypatch,
):
    solver_dispatch_module = importlib.import_module("deerflow.domain.submarine.solver_dispatch")
    models_module = importlib.import_module("deerflow.domain.submarine.models")

    outputs_dir = tmp_path / "outputs"
    workspace_dir = tmp_path / "workspace"
    uploads_dir = tmp_path / "uploads"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "custom-variant-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(
        solver_dispatch_module,
        "inspect_geometry_file",
        lambda path, hint: models_module.GeometryInspection(
            file_name=path.name,
            file_size_bytes=path.stat().st_size,
            input_format="stl",
            geometry_family=hint or "DARPA SUBOFF",
        ),
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "rank_cases",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "_write_openfoam_case_scaffold",
        lambda **kwargs: {
            "workspace_case_dir_virtual_path": ("/mnt/user-data/workspace/submarine/solver-dispatch/custom-variant-demo/openfoam-case"),
            "run_script_virtual_path": ("/mnt/user-data/workspace/submarine/solver-dispatch/custom-variant-demo/openfoam-case/Allrun"),
            "solver_application": "simpleFoam",
            "requires_geometry_conversion": False,
            "execution_readiness": "stl_ready",
        },
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "collect_requested_postprocess_artifacts",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "_collect_solver_results",
        lambda **kwargs: {
            "solver_completed": True,
            "final_time_seconds": 200.0,
            "mesh_summary": {"mesh_ok": True, "cells": 9342},
            "latest_force_coefficients": {"Time": 200.0, "Cd": 0.00312},
            "latest_forces": {"total_force": [8.0, 0.0, 0.0]},
        },
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "_render_solver_results_markdown_enriched",
        lambda results: "# solver results\n",
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "build_stability_evidence",
        lambda **kwargs: {"status": "passed"},
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "build_scientific_verification_assessment",
        lambda **kwargs: {"status": "ready", "requirements": []},
    )

    payload, artifacts = solver_dispatch_module.run_solver_dispatch(
        geometry_path=geometry_path,
        outputs_dir=outputs_dir,
        workspace_dir=workspace_dir,
        task_description="Execute the baseline run and register a custom pressure sweep.",
        task_type="resistance",
        confirmation_status="confirmed",
        execution_preference="execute_now",
        geometry_family_hint="DARPA SUBOFF",
        geometry_virtual_path="/mnt/user-data/uploads/custom-variant-demo.stl",
        custom_variants=[
            {
                "variant_id": "pressure-sweep",
                "variant_label": "Pressure Sweep",
                "parameter_overrides": {"outlet_pressure_pa": 250},
                "rationale": "Probe outlet pressure sensitivity.",
            }
        ],
        execute_now=True,
        execute_command=lambda command: "simpleFoam finished cleanly",
    )

    run_dir = outputs_dir / "submarine" / "solver-dispatch" / "custom-variant-demo"
    experiment_manifest = json.loads((run_dir / "experiment-manifest.json").read_text(encoding="utf-8"))
    compare_summary = json.loads((run_dir / "run-compare-summary.json").read_text(encoding="utf-8"))
    custom_run_record = json.loads((run_dir / "custom-variants" / "pressure-sweep" / "run-record.json").read_text(encoding="utf-8"))

    custom_manifest_record = next(item for item in experiment_manifest["run_records"] if item["run_id"] == "custom:pressure-sweep")

    assert payload["custom_variant_run_ids"] == ["custom:pressure-sweep"]
    assert payload["custom_variants"][0]["compare_target_run_id"] == "baseline"
    assert any(path.endswith("/custom-variants/pressure-sweep/run-record.json") for path in artifacts)
    assert custom_manifest_record["run_role"] == "custom_variant"
    assert custom_manifest_record["variant_origin"] == "custom_variant"
    assert custom_manifest_record["variant_label"] == "Pressure Sweep"
    assert custom_manifest_record["parameter_overrides"] == {"outlet_pressure_pa": 250}
    assert custom_manifest_record["baseline_reference_run_id"] == "baseline"
    assert custom_manifest_record["compare_target_run_id"] == "baseline"
    assert custom_manifest_record["execution_status"] == "planned"
    assert custom_run_record["run_id"] == "custom:pressure-sweep"
    assert custom_run_record["run_role"] == "custom_variant"
    assert custom_run_record["baseline_reference_run_id"] == "baseline"
    assert custom_run_record["compare_target_run_id"] == "baseline"
    assert any(item["candidate_run_id"] == "custom:pressure-sweep" and item["compare_status"] == "planned" for item in compare_summary["comparisons"])


def test_solver_dispatch_persists_iterative_contract_metadata_in_experiment_records(
    tmp_path,
    monkeypatch,
):
    solver_dispatch_module = importlib.import_module("deerflow.domain.submarine.solver_dispatch")
    models_module = importlib.import_module("deerflow.domain.submarine.models")

    outputs_dir = tmp_path / "outputs"
    workspace_dir = tmp_path / "workspace"
    uploads_dir = tmp_path / "uploads"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    geometry_path = uploads_dir / "iterative-lineage-demo.stl"
    _write_ascii_stl(geometry_path)

    monkeypatch.setattr(
        solver_dispatch_module,
        "inspect_geometry_file",
        lambda path, hint: models_module.GeometryInspection(
            file_name=path.name,
            file_size_bytes=path.stat().st_size,
            input_format="stl",
            geometry_family=hint or "DARPA SUBOFF",
        ),
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "rank_cases",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "_write_openfoam_case_scaffold",
        lambda **kwargs: {
            "workspace_case_dir_virtual_path": ("/mnt/user-data/workspace/submarine/solver-dispatch/iterative-lineage-demo/openfoam-case"),
            "run_script_virtual_path": ("/mnt/user-data/workspace/submarine/solver-dispatch/iterative-lineage-demo/openfoam-case/Allrun"),
            "solver_application": "simpleFoam",
            "requires_geometry_conversion": False,
            "execution_readiness": "stl_ready",
        },
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "collect_requested_postprocess_artifacts",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "_collect_solver_results",
        lambda **kwargs: {
            "solver_completed": True,
            "final_time_seconds": 200.0,
            "mesh_summary": {"mesh_ok": True, "cells": 9342},
            "latest_force_coefficients": {"Time": 200.0, "Cd": 0.00312},
            "latest_forces": {"total_force": [8.0, 0.0, 0.0]},
        },
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "_render_solver_results_markdown_enriched",
        lambda results: "# solver results\n",
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "build_stability_evidence",
        lambda **kwargs: {"status": "passed"},
    )
    monkeypatch.setattr(
        solver_dispatch_module,
        "build_scientific_verification_assessment",
        lambda **kwargs: {"status": "ready", "requirements": []},
    )

    payload, _ = solver_dispatch_module.run_solver_dispatch(
        geometry_path=geometry_path,
        outputs_dir=outputs_dir,
        workspace_dir=workspace_dir,
        task_description="Revise the baseline run, add wake outputs, and register a pressure sweep variant.",
        task_type="resistance",
        confirmation_status="confirmed",
        execution_preference="execute_now",
        geometry_family_hint="DARPA SUBOFF",
        geometry_virtual_path="/mnt/user-data/uploads/iterative-lineage-demo.stl",
        requested_outputs=[
            {
                "output_id": "drag_coefficient",
                "label": "阻力系数 Cd",
                "requested_label": "阻力系数 Cd",
                "status": "requested",
                "support_level": "supported",
            },
            {
                "output_id": "wake_velocity_slice",
                "label": "尾流速度切片",
                "requested_label": "尾流速度切片",
                "status": "requested",
                "support_level": "supported",
            },
        ],
        custom_variants=[
            {
                "variant_id": "pressure-sweep",
                "variant_label": "Pressure Sweep",
                "parameter_overrides": {"outlet_pressure_pa": 250},
                "rationale": "Probe outlet pressure sensitivity.",
            }
        ],
        contract_revision=3,
        revision_summary="Add wake velocity slice delivery and pressure sweep lineage.",
        execute_now=True,
        execute_command=lambda command: "simpleFoam finished cleanly",
    )

    run_dir = outputs_dir / "submarine" / "solver-dispatch" / "iterative-lineage-demo"
    experiment_manifest = json.loads((run_dir / "experiment-manifest.json").read_text(encoding="utf-8"))
    baseline_run_record = json.loads((run_dir / "run-record.json").read_text(encoding="utf-8"))
    custom_run_record = json.loads((run_dir / "custom-variants" / "pressure-sweep" / "run-record.json").read_text(encoding="utf-8"))

    custom_manifest_record = next(item for item in experiment_manifest["run_records"] if item["run_id"] == "custom:pressure-sweep")

    assert payload["contract_revision"] == 3
    assert baseline_run_record["contract_revision"] == 3
    assert baseline_run_record["requested_output_ids"] == [
        "drag_coefficient",
        "wake_velocity_slice",
    ]
    assert custom_manifest_record["contract_revision"] == 3
    assert custom_manifest_record["lineage_reason"] == ("Add wake velocity slice delivery and pressure sweep lineage.")
    assert custom_manifest_record["requested_output_ids"] == [
        "drag_coefficient",
        "wake_velocity_slice",
    ]
    assert custom_run_record["contract_revision"] == 3
    assert custom_run_record["lineage_reason"] == ("Add wake velocity slice delivery and pressure sweep lineage.")


def test_result_report_marks_validated_run_with_incomplete_experiment_linkage_as_gap(tmp_path, monkeypatch):
    report_tool_module = importlib.import_module("deerflow.tools.builtins.submarine_result_report_tool")
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
    final_payload = json.loads((final_report_dir / "final-report.json").read_text(encoding="utf-8"))
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
    assert any("mesh_independence:fine" in item for item in final_payload["experiment_summary"]["linkage_issues"])
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
    evidence_index = final_payload["evidence_index"]
    assert any(group["group_id"] == "research_evidence" for group in evidence_index)
    assert "## 结论与证据" in final_markdown
    assert "## 证据索引" in final_markdown
    assert "<h2>结果、验证与结论边界</h2>" in final_html
    assert "<h3>结论与证据</h3>" in final_html
    assert "<h3>证据索引</h3>" in final_html
