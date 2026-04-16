# SUBOFF Scale Consistency And Report Hardening Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then choose the execution skill that fits the work: use superpowers:subagent-driven-development when delegation benefits outweigh the round-trip, or superpowers:executing-plans when the work is better kept local. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the plan controls below, especially reuse, continuity, artifact lifecycle, validation/review cadence, and any research-overlay constraints.

**Goal:** Make the SUBOFF baseline scientifically trustworthy again by enforcing consistent geometry scaling for binary STL inputs, rerunning the real baseline with current code, and upgrading the final report so corrected outputs are organized like a formal deliverable instead of a loose artifact list.

**Architecture:** Keep the current submarine workflow and harden it at three seams. First, protect `solver_dispatch_case.py` with binary-STL regression coverage so case geometry and reference values stay in the same physical unit system. Second, use the current solver-dispatch path to regenerate the real SUBOFF baseline and record evidence that the case geometry, solver outputs, and reported coefficients now agree. Third, restructure the final report payload/rendering so corrected deliverables, solver outputs, and workspace locations are grouped by purpose and explicitly separate verified results from intermediate storage.

**Tech Stack:** Python 3.12, DeerFlow submarine domain workflow, OpenFOAM case scaffolding, pytest, JSON/Markdown/HTML report rendering

**Prior Art Survey:** none needed - this is a tracked internal regression/debugging and deliverable-hardening pass on the existing project

**Reuse Strategy:** adapt existing project

**Session Status File:** `docs/superpowers/session-status/2026-04-16-suboff-scale-consistency-and-report-hardening-status.md`

**Context Summary:** none

**Primary Context Files:** `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`; `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`; `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_case.py`; `backend/packages/harness/deerflow/domain/submarine/reporting.py`; `backend/packages/harness/deerflow/domain/submarine/reporting_render.py`; `backend/tests/test_submarine_solver_dispatch_tool.py`; `backend/tests/test_submarine_result_report_tool.py`; `backend/.deer-flow/threads/01fec432-dead-4cb3-8c2d-09896f4fe832/user-data/outputs/submarine/solver-dispatch/suboff_solid/openfoam-request.json`; `backend/.deer-flow/threads/01fec432-dead-4cb3-8c2d-09896f4fe832/user-data/outputs/submarine/solver-dispatch/suboff_solid/solver-results.json`

**Artifact Lifecycle:** Keep this plan, the companion status file, the decision log, and the research findings artifact. Keep new regression tests, corrected solver/report artifacts, and any code changes that enforce unit consistency or clearer report grouping. Replace stale `suboff_solid` baseline artifacts in the active thread once a corrected rerun completes. Do not keep ad-hoc debug scripts after their evidence is captured in tests or findings docs.

**Workspace Strategy:** current workspace

**Validation Strategy:** mixed

**Review Cadence:** each milestone

**Checkpoint Strategy:** user-directed checkpoints

**Research Overlay:** enabled

**Research Mainline:** Demonstrate that the current SUBOFF workflow can turn a real binary STL upload into a meter-consistent OpenFOAM case, a physically plausible resistance result, and a report that a researcher can audit without guessing where corrected outputs came from.

**Non-Negotiables:** binary STL uploads must not silently keep millimeter geometry inside the OpenFOAM case once reference values are normalized to meters; final reported coefficients must be backed by regenerated artifacts from the current code path; the report must group deliverables by function and distinguish key outputs from workspace/intermediate storage.

**Forbidden Regressions:** copying a raw millimeter-scale STL into `constant/triSurface` while `lRef` and `Aref` are meter-scale; treating stale high-drag artifacts as if they were valid current results; reverting the report appendix to an unstructured dump that forces the user to infer which files matter.

**Method Fidelity Checks:** inspect generated `triSurface` bounds for the real SUBOFF rerun; inspect `controlDict` force-coefficient reference values in the regenerated case; verify the corrected rerun produces a drag coefficient in a plausible order of magnitude rather than the previous scale-induced `~3073`; verify the rendered report groups files into report outputs, solver outputs, and workspace/intermediate locations.

**Scale Gate:** rerun the real `suboff_solid` baseline with current code and confirm both the case STL bounds and resulting `Cd` are meter-consistent before treating the workflow as corrected.

**Decision Log:** `docs/superpowers/research-decisions/2026-04-16-suboff-scale-consistency-and-report-hardening-decision-log.md`

**Research Findings:** `docs/superpowers/research-findings/2026-04-16-suboff-scale-consistency-and-report-hardening-findings.md`

**Uncertainty Hotspots:** whether the current code already fixes binary scaling and only the persisted thread artifacts are stale; whether any remaining force anomaly survives after the rerun and points to a second physics/configuration issue; how much report grouping can be improved without destabilizing existing consumers.

**Replan Triggers:** if a fresh rerun with the current code still yields a scale-inflated `Cd`; if the real case STL is meter-consistent but the force integration remains obviously non-physical; if report-grouping changes require frontend contract changes instead of reporting-only updates.

---

### Task 1: Add Regression Coverage For Binary STL Scale Propagation

**Files:**
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`
- Test: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Add a failing binary-STL regression test that uses a real binary mesh fixture and asserts the generated case geometry is scaled into meters**

```python
def _write_binary_stl(path: Path, triangles: list[tuple[tuple[float, float, float], ...]]) -> None:
    ...

def test_submarine_solver_dispatch_applies_geometry_scale_factor_to_binary_case_geometry(
    tmp_path, monkeypatch
):
    geometry_path = uploads_dir / "suboff_solid.stl"
    _write_binary_stl(
        geometry_path,
        [
            ((0.0, 0.0, 0.0), (4355.947754, 0.0, 0.0), (0.0, 508.0, 0.0)),
            ((4355.947754, 0.0, 0.0), (4355.947754, 508.0, 0.0), (0.0, 508.0, 0.0)),
        ],
    )
    ...
    scaled_geometry = (
        workspace_dir
        / "submarine"
        / "solver-dispatch"
        / "suboff_solid"
        / "openfoam-case"
        / "constant"
        / "triSurface"
        / "suboff_solid.stl"
    ).read_bytes()
    assert measured_length_x(scaled_geometry) < 10.0
    assert measured_span_z(scaled_geometry) < 1.0
```

- [ ] **Step 2: Run it to verify RED**

Run: `uv run --project backend pytest backend/tests/test_submarine_solver_dispatch_tool.py -k binary_case_geometry -q`
Expected: FAIL if the real binary STL path is not yet protected by regression coverage or if the measured bounds stay at the raw millimeter scale

- [ ] **Step 3: Implement or tighten the binary-STL case-scaling path only as needed to make the test pass**

```python
if (
    geometry_scale_factor is not None
    and geometry_scale_factor > 0
    and abs(geometry_scale_factor - 1.0) > 1e-9
):
    _copy_scaled_stl(
        source_path=geometry_path,
        destination_path=tri_surface_path,
        scale_factor=geometry_scale_factor,
    )
```

- [ ] **Step 4: Re-run the focused solver-dispatch scale tests**

Run: `uv run --project backend pytest backend/tests/test_submarine_solver_dispatch_tool.py -k geometry_scale_factor -q`
Expected: PASS

### Task 2: Capture Evidence That The Real SUBOFF Baseline Is Corrected

**Type:** Exploratory

**Files:**
- Modify: `docs/superpowers/research-findings/2026-04-16-suboff-scale-consistency-and-report-hardening-findings.md`
- Notes: `backend/.deer-flow/threads/01fec432-dead-4cb3-8c2d-09896f4fe832/user-data/outputs/submarine/solver-dispatch/suboff_solid/openfoam-request.json`
- Notes: `backend/.deer-flow/threads/01fec432-dead-4cb3-8c2d-09896f4fe832/user-data/outputs/submarine/solver-dispatch/suboff_solid/solver-results.json`

**Goal:** Determine whether a fresh SUBOFF baseline rerun with the current code removes the stale scale-induced drag anomaly.

**Collect Evidence:**
- regenerated `triSurface` bounds for the real `suboff_solid` case
- regenerated `controlDict` reference values and corrected `solver-results.json`
- a concise note comparing the stale `Cd ~3073` artifacts with the corrected rerun

**Stop and Replan If:**
- the regenerated case STL is still millimeter-scale
- the regenerated case STL is meter-scale but the resulting drag coefficient remains wildly non-physical

**Checkpoint If:**
- the rerun completes and produces a corrected baseline worth preserving in the active thread artifacts

- [ ] **Step 1: Capture the stale baseline evidence in the findings artifact before regenerating anything**

- [ ] **Step 2: Regenerate the real SUBOFF case and execute the baseline run with the current code path**

Run: `@' ... '@ | uv run --project backend python -`
```python
from pathlib import Path
import subprocess
import json
from deerflow.domain.submarine.contracts import build_runtime_snapshot
from deerflow.domain.submarine.solver_dispatch import run_solver_dispatch

thread_root = Path("backend/.deer-flow/threads/01fec432-dead-4cb3-8c2d-09896f4fe832/user-data")
geometry_path = thread_root / "uploads" / "suboff_solid.stl"
outputs_dir = thread_root / "outputs"
workspace_dir = thread_root / "workspace"
snapshot_path = outputs_dir / "submarine" / "solver-dispatch" / "suboff_solid" / "result-report-snapshot.json"

def execute_command(command: str) -> str:
    completed = subprocess.run(
        command,
        shell=True,
        check=True,
        capture_output=True,
        text=True,
    )
    return (completed.stdout or "") + (completed.stderr or "")

payload, artifacts = run_solver_dispatch(
    geometry_path=geometry_path,
    outputs_dir=outputs_dir,
    workspace_dir=workspace_dir,
    task_description="Regenerate and execute the corrected DARPA SUBOFF 5 m/s baseline.",
    task_type="resistance",
    confirmation_status="confirmed",
    execution_preference="execute_now",
    geometry_family_hint="DARPA SUBOFF",
    inlet_velocity_mps=5.0,
    fluid_density_kg_m3=1025.0,
    kinematic_viscosity_m2ps=1.05e-06,
    end_time_seconds=200.0,
    delta_t_seconds=1.0,
    write_interval_steps=50,
    scale_assessment={
        "raw_length_value": 4355.94775390625,
        "normalized_length_m": 4.356,
        "applied_scale_factor": 0.001,
        "heuristic": "divide_by_1000_mm_to_m",
        "severity": "severe",
        "summary_zh": "Geometry scale requires confirmation.",
    },
    reference_value_suggestions=[
        {
            "suggestion_id": "ref-length",
            "quantity": "reference_length_m",
            "value": 4.356,
            "unit": "m",
            "is_low_risk": True,
            "requires_confirmation": False,
            "source": "geometry-check",
            "justification": "Use the normalized SUBOFF length.",
            "summary_zh": "Use the normalized hull length.",
        },
        {
            "suggestion_id": "ref-area",
            "quantity": "reference_area_m2",
            "value": 0.370988,
            "unit": "m^2",
            "is_low_risk": True,
            "requires_confirmation": False,
            "source": "geometry-check",
            "justification": "Use the normalized frontal area.",
            "summary_zh": "Use the normalized frontal area.",
        },
    ],
    execute_now=True,
    execute_command=execute_command,
)
snapshot = build_runtime_snapshot(
    current_stage="solver-dispatch",
    task_summary="Regenerate and execute the corrected DARPA SUBOFF 5 m/s baseline.",
    confirmation_status="confirmed",
    execution_preference="execute_now",
    task_type="resistance",
    geometry_virtual_path="/mnt/user-data/uploads/suboff_solid.stl",
    geometry_family=(payload.get("geometry") or {}).get("geometry_family"),
    execution_readiness=payload.get("execution_readiness"),
    geometry_findings=payload.get("geometry_findings"),
    scale_assessment=payload.get("scale_assessment"),
    reference_value_suggestions=payload.get("reference_value_suggestions"),
    next_recommended_stage=payload["next_recommended_stage"],
    report_virtual_path=payload["report_virtual_path"],
    artifact_virtual_paths=payload["artifact_virtual_paths"],
    selected_case_id=(payload.get("selected_case") or {}).get("case_id"),
    simulation_requirements=payload.get("simulation_requirements"),
    requested_outputs=payload.get("requested_outputs"),
    recommended_actions=payload.get("recommended_actions"),
    output_delivery_plan=payload.get("output_delivery_plan"),
    stage_status=payload.get("dispatch_status"),
    workspace_case_dir_virtual_path=payload.get("workspace_case_dir_virtual_path"),
    run_script_virtual_path=payload.get("run_script_virtual_path"),
    request_virtual_path=payload.get("request_virtual_path"),
    provenance_manifest_virtual_path=payload.get("provenance_manifest_virtual_path"),
    execution_log_virtual_path=payload.get("execution_log_virtual_path"),
    solver_results_virtual_path=payload.get("solver_results_virtual_path"),
    stability_evidence_virtual_path=payload.get("stability_evidence_virtual_path"),
    stability_evidence=payload.get("stability_evidence"),
    provenance_summary=payload.get("provenance_summary"),
    environment_fingerprint=payload.get("environment_fingerprint"),
    environment_parity_assessment=payload.get("environment_parity_assessment"),
    supervisor_handoff_virtual_path=payload.get("supervisor_handoff_virtual_path"),
    review_status=payload["review_status"],
    scientific_verification_assessment=payload.get("scientific_verification_assessment"),
    scientific_gate_status=payload.get("scientific_gate_status"),
    decision_status=payload.get("decision_status"),
    delivery_decision_summary=payload.get("delivery_decision_summary"),
)
snapshot_path.write_text(
    json.dumps(snapshot.model_dump(mode="json"), ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(payload["dispatch_status"])
print(payload.get("solver_results_virtual_path"))
print(snapshot_path.as_posix())
```
Expected: current code rewrites the `suboff_solid` case, runs the baseline, and refreshes `solver-results.json` under the active thread outputs

- [ ] **Step 3: Inspect the regenerated case STL bounds, `controlDict`, and `solver-results.json`**

Run: `@' ... '@ | python -`
```python
from pathlib import Path
import json
...
print(case_bounds)
print(reference_values)
print(latest_cd)
```
Expected: case bounds are meter-scale and the new `Cd` is no longer in the `10^3` range

- [ ] **Step 4: Record verified facts, remaining hypotheses, and whether the scale gate is satisfied in the findings artifact**

- [ ] **Step 5: Decide whether execution continues on the current plan or invokes `superpowers:revising-plans`**

### Task 3: Add Report-Grouping Regression Coverage For Corrected Deliverables

**Files:**
- Modify: `backend/tests/test_submarine_result_report_tool.py`
- Test: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Add a failing report-rendering test that asserts the corrected report groups files by function instead of only listing them sequentially**

```python
assert "## Key Results And Deliverables" in markdown
assert "### Report Outputs" in markdown
assert "### Solver Outputs" in markdown
assert "### Workspace And Intermediate Files" in markdown
assert "<h3>Report Outputs</h3>" in html
```

- [ ] **Step 2: Run it to verify RED**

Run: `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py -k grouped_artifact_sections -q`
Expected: FAIL because the current appendix is still compact but not yet grouped into the final structure

- [ ] **Step 3: Add a failing payload test for grouped artifact sections so render logic is backed by structured report data**

```python
assert payload["artifact_group_summary"][0]["group_id"] == "report_outputs"
assert payload["artifact_group_summary"][1]["group_id"] == "solver_outputs"
assert payload["artifact_group_summary"][2]["group_id"] == "workspace_intermediate"
```

- [ ] **Step 4: Run it to verify RED**

Run: `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py -k artifact_group_summary -q`
Expected: FAIL because the payload does not yet expose the grouped summary

### Task 4: Implement Final Report Grouping And Refresh Real Artifacts

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting_render.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`
- Modify: `docs/superpowers/session-status/2026-04-16-suboff-scale-consistency-and-report-hardening-status.md`
- Modify: `docs/superpowers/research-decisions/2026-04-16-suboff-scale-consistency-and-report-hardening-decision-log.md`
- Modify: `docs/superpowers/research-findings/2026-04-16-suboff-scale-consistency-and-report-hardening-findings.md`

- [ ] **Step 1: Build a grouped artifact summary in the report payload using the existing compact manifest plus workspace summary**

```python
artifact_group_summary = [
    {
        "group_id": "report_outputs",
        "title": "Report Outputs",
        "items": [...],
    },
    {
        "group_id": "solver_outputs",
        "title": "Solver Outputs",
        "items": [...],
    },
    {
        "group_id": "workspace_intermediate",
        "title": "Workspace And Intermediate Files",
        "items": [...],
    },
]
```

- [ ] **Step 2: Render grouped sections in markdown and HTML while keeping absolute and virtual paths for the key deliverables**

```python
for group in payload["artifact_group_summary"]:
    lines.append(f"### {group['title']}")
```

- [ ] **Step 3: Run the focused report tests**

Run: `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py -k "artifact_group_summary or grouped_artifact_sections" -q`
Expected: PASS

- [ ] **Step 4: Run the broader solver-dispatch and report suites**

Run: `uv run --project backend pytest backend/tests/test_submarine_solver_dispatch_tool.py -k "geometry_scale_factor or binary_case_geometry" -q`
Expected: PASS

Run: `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py -q`
Expected: PASS

- [ ] **Step 5: Regenerate the real final report from the corrected SUBOFF outputs and refresh the status / decision / findings artifacts**

Run: `@' ... '@ | uv run --project backend python -`
```python
from pathlib import Path
import json
from deerflow.domain.submarine.contracts import SubmarineRuntimeSnapshot
from deerflow.domain.submarine.reporting import run_result_report

thread_root = Path("backend/.deer-flow/threads/01fec432-dead-4cb3-8c2d-09896f4fe832/user-data")
outputs_dir = thread_root / "outputs"
snapshot_path = outputs_dir / "submarine" / "solver-dispatch" / "suboff_solid" / "result-report-snapshot.json"
snapshot = SubmarineRuntimeSnapshot.model_validate(json.loads(snapshot_path.read_text(encoding="utf-8")))
payload, artifacts = run_result_report(snapshot=snapshot, outputs_dir=outputs_dir)
print(payload["report_virtual_path"])
print(payload["decision_status"])
```
Expected: the active-thread `final-report.{json,md,html}` shows corrected grouped sections and no longer presents the stale scale-inflated result as current
