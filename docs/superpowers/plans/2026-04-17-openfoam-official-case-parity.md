# OpenFOAM Official Case Parity Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then choose the execution skill that fits the work: use superpowers:subagent-driven-development when delegation benefits outweigh the round-trip, or superpowers:executing-plans when the work is better kept local. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the plan controls below, especially reuse, continuity, artifact lifecycle, validation/review cadence, and any research-overlay constraints.

**Goal:** Make official OpenFOAM seed threads deterministic end-to-end, align `cavity` / `pitzDaily` assembly with the pinned OpenFOAM 13 tutorial defaults, and capture parity evidence strong enough to justify shipping the official-case path.

**Architecture:** Keep the existing official-seed path, but rotate the execution mainline from "seed import exists" to "seed execution is deterministic and tutorial-parity is proven". The backend will add stage-aware deterministic fallbacks in the lead-agent middleware, upgrade `pitzDaily` assembly from a simplified placeholder to the real pinned tutorial defaults, and add an official-case validation layer that compares generated runs against pinned baseline expectations before reports claim parity.

**Tech Stack:** Python backend runtime/contracts/tools, LangChain agent middleware, OpenFOAM 13 sandbox image, pytest, Docker-backed official-case verification

**Prior Art Survey:** `docs/superpowers/research-findings/2026-04-17-openfoam-reference-skill-validation-findings.md`

**Reuse Strategy:** adapt existing project

**Artifact Scope:** task-local

**Artifact Epoch:** openfoam-official-case-parity

**Supersedes:** `openfoam-official-case-seed-import`

**Session Status File:** `docs/superpowers/session-status/2026-04-17-openfoam-official-case-parity-status.md`

**Context Summary:** none

**Primary Context Files:** `docs/superpowers/research-findings/2026-04-17-openfoam-reference-skill-validation-findings.md`; `docs/superpowers/session-status/2026-04-17-openfoam-reference-skill-validation-status.md`; `backend/packages/harness/deerflow/agents/middlewares/openfoam_seed_workflow_middleware.py`; `backend/packages/harness/deerflow/domain/submarine/official_case_assembly.py`; `backend/packages/harness/deerflow/domain/submarine/official_case_profiles.py`; `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`; `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`; `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`

**Artifact Lifecycle:** Keep this plan, the companion session status file, and the existing reference-skill findings/status artifacts. Keep only the minimal pinned seed fixtures already in-repo plus any small new canonical baseline fixtures needed for deterministic tests; delete ad-hoc runtime dumps, copied tutorial trees, and temporary comparison folders after verification. Replace the current simplified `pitzDaily` defaults rather than keeping both "demo" and "official" assembly branches alive.

**Workspace Strategy:** current workspace

**Validation Strategy:** mixed

**Review Cadence:** each milestone

**Checkpoint Strategy:** user-directed checkpoints

**Research Overlay:** disabled

**Research Mainline:** none

**Evaluation Rubric:** none

**Non-Negotiables:** none

**Forbidden Regressions:** none

**Method Fidelity Checks:** none

**Scale Gate:** none

**Freeze Gate:** none

**Decision Log:** none - record durable decisions in session status and linked findings docs

**Research Findings:** none

**Uncertainty Hotspots:** whether the middleware can safely synthesize tool calls without causing duplicate dispatch loops; which official `pitzDailySteady` files must be copied verbatim versus normalized/project-generated; what minimum parity checks are strong enough to count as "matches official results" without overfitting to one host runtime

**Replan Triggers:** if stage-aware middleware fallback creates duplicate tool loops or breaks normal clarification; if the pinned tutorial defaults require a larger schema split than the current official-case assembly path can absorb; if real `pitzDaily` completion remains unstable after assembly parity is fixed

---

### Task 1: Add Deterministic Seed-Execution Fallbacks

**Files:**
- Modify: `backend/packages/harness/deerflow/agents/middlewares/openfoam_seed_workflow_middleware.py`
- Test: `backend/tests/test_openfoam_seed_workflow_middleware.py`

- [x] **Step 1: Write failing middleware tests for stage-aware deterministic recovery**

```python
def test_openfoam_seed_workflow_middleware_forces_design_brief_when_seed_thread_reply_has_no_tool_call(...):
    captured = middleware.wrap_model_call(request, lambda _: ModelResponse(result=[AIMessage(content="我先继续推进")]))
    assert captured.result[0].tool_calls[0]["name"] == "submarine_design_brief"

def test_openfoam_seed_workflow_middleware_forces_solver_dispatch_after_confirmed_seed_brief(...):
    captured = middleware.wrap_model_call(request, lambda _: ModelResponse(result=[AIMessage(content="我继续处理")]))
    assert captured.result[0].tool_calls[0]["name"] == "submarine_solver_dispatch"

def test_openfoam_seed_workflow_middleware_forces_result_report_after_executed_seed_dispatch(...):
    captured = middleware.wrap_model_call(request, lambda _: ModelResponse(result=[AIMessage(content="我继续推进")]))
    assert captured.result[0].tool_calls[0]["name"] == "submarine_result_report"
```

- [x] **Step 2: Run the middleware slice to confirm the new recovery expectations fail first**

Run: `uv run --project backend pytest backend/tests/test_openfoam_seed_workflow_middleware.py -q`
Expected: FAIL because the current middleware only appends reminder/retry text and never synthesizes deterministic CFD tool calls

- [x] **Step 3: Implement stage-aware synthetic tool-call recovery for official seed threads**

```python
if action == "design_brief":
    return ModelResponse(
        result=[AIMessage(content="", tool_calls=[_design_brief_recovery_tool_call(request)])]
    )
if action == "solver_dispatch":
    return ModelResponse(
        result=[AIMessage(content="", tool_calls=[_solver_dispatch_recovery_tool_call(request)])]
    )
if action == "result_report":
    return ModelResponse(
        result=[AIMessage(content="", tool_calls=[_result_report_recovery_tool_call()])]
    )
```

Rules:

```text
- First seed-thread turn: if a supported seed upload plus concrete CFD-progress intent is present and the model reply contains no CFD tool call, force `submarine_design_brief`.
- After a confirmed official-seed brief with `next_recommended_stage=solver-dispatch`, force `submarine_solver_dispatch` on text-only follow-ups.
- After an executed official-seed dispatch with `next_recommended_stage=result-reporting`, force `submarine_result_report` on text-only follow-ups.
- Never replace a response that already contains a real submarine CFD tool call for the correct stage.
- Only force a stage when the runtime does not currently require user confirmation for that stage.
- Do not repeat the same forced tool after that tool has already run since the latest human message.
- Scope every forced recovery to the latest human turn so a later user message resets the recovery state cleanly.
```

- [x] **Step 4: Re-run the middleware tests**

Run: `uv run --project backend pytest backend/tests/test_openfoam_seed_workflow_middleware.py -q`
Expected: PASS with deterministic recovery for design brief, solver dispatch, and result reporting

### Task 2: Align Official Case Assembly With Pinned Tutorial Defaults

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/official_case_assembly.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/official_case_profiles.py`
- Test: `backend/tests/test_official_case_assembly.py`

- [x] **Step 1: Write failing assembly tests for the missing official `pitzDailySteady` defaults**

```python
def test_assemble_pitzdaily_case_uses_official_steady_control_dict_defaults(...):
    control_dict = (assembled_dir / "system" / "controlDict").read_text()
    assert "endTime         2000;" in control_dict
    assert "deltaT          1;" in control_dict
    assert "solver          incompressibleFluid;" in control_dict

def test_assemble_cavity_case_keeps_the_pinned_legacy_defaults_while_pitzdaily_is_upgraded(...):
    fv_solution = (assembled_dir / "system" / "fvSolution").read_text()
    assert "pFinal" in fv_solution
    assert "PISO" in fv_solution

def test_assemble_pitzdaily_case_includes_official_turbulence_fields_and_functions(...):
    assert (assembled_dir / "0" / "k").exists()
    assert (assembled_dir / "0" / "epsilon").exists()
    assert (assembled_dir / "system" / "functions").exists()
    momentum_transport = (assembled_dir / "constant" / "momentumTransport").read_text()
    assert "simulationType RAS;" in momentum_transport
    assert "model           kEpsilon;" in momentum_transport
```

- [x] **Step 2: Run the assembly slice to verify the current simplified `pitzDaily` scaffolding fails**

Run: `uv run --project backend pytest backend/tests/test_official_case_assembly.py -q`
Expected: FAIL because the current `pitzDaily` assembly still emits a short laminar placeholder instead of the pinned steady tutorial defaults

- [x] **Step 3: Replace the simplified `pitzDaily` templates with pinned OpenFOAM 13 tutorial defaults**

```python
return {
    "0/U": OFFICIAL_PITZDAILY_U,
    "0/p": OFFICIAL_PITZDAILY_P,
    "0/k": OFFICIAL_PITZDAILY_K,
    "0/epsilon": OFFICIAL_PITZDAILY_EPSILON,
    "constant/physicalProperties": OFFICIAL_PITZDAILY_PHYSICAL_PROPERTIES,
    "constant/momentumTransport": OFFICIAL_PITZDAILY_MOMENTUM_TRANSPORT,
    "system/controlDict": OFFICIAL_PITZDAILY_CONTROL_DICT,
    "system/fvSchemes": OFFICIAL_PITZDAILY_FV_SCHEMES,
    "system/fvSolution": OFFICIAL_PITZDAILY_FV_SOLUTION,
    "system/functions": OFFICIAL_PITZDAILY_FUNCTIONS,
}
```

Keep the imported seed as `system/pitzDaily.blockMeshDict`, but make the rest of the assembled case match the pinned tutorial semantics instead of the earlier compatibility placeholder.

- [x] **Step 4: Re-run the official-case assembly tests**

Run: `uv run --project backend pytest backend/tests/test_official_case_assembly.py -q`
Expected: PASS with `pitzDailySteady` defaults now matching the pinned OpenFOAM 13 tutorial structure closely enough for parity checks

### Task 3: Add Official Case Parity Validation

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/official_case_validation.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting_render.py`
- Test: `backend/tests/test_official_case_validation.py`
- Test: `backend/tests/test_submarine_solver_dispatch_tool.py`
- Test: `backend/tests/test_submarine_result_report_tool.py`

- [x] **Step 1: Write failing validation tests for `cavity` and `pitzDaily` baseline parity**

```python
def test_build_official_case_validation_marks_cavity_as_matched_when_metrics_hit_pinned_baseline():
    assessment = build_official_case_validation_assessment(
        case_id="cavity",
        solver_results={"solver_completed": True, "final_time_seconds": 0.5, "mesh_summary": {"cells": 400}},
        assembled_case_files={"system/controlDict": cavity_control_dict},
    )
    assert assessment["parity_status"] == "matched"

def test_build_official_case_validation_marks_pitzdaily_as_drifted_when_steady_defaults_are_missing():
    assessment = build_official_case_validation_assessment(
        case_id="pitzDaily",
        solver_results={"solver_completed": True, "final_time_seconds": 285.0, "mesh_summary": {"cells": 12225}},
        assembled_case_files={"system/controlDict": "endTime 0.5;"},
    )
    assert assessment["parity_status"] == "drifted"
```

- [x] **Step 2: Run the new validation tests to prove the baseline does not exist yet**

Run: `uv run --project backend pytest backend/tests/test_official_case_validation.py -q`
Expected: FAIL because no official-case parity validator exists yet

- [x] **Step 3: Implement the official-case validator and thread/report plumbing**

```python
assessment = build_official_case_validation_assessment(
    case_id=official_case_id,
    solver_results=solver_results,
    assembled_case_dir=run_result.assembled_case_dir,
)
payload["official_case_validation_assessment"] = assessment
payload["official_case_validation_virtual_path"] = request_virtual_path.replace(
    "openfoam-request.json",
    "official-case-parity.json",
)
```

The validator must at minimum check:

```text
- `cavity`: solver completed, final pseudo-time `0.5`, mesh cells `400`, and canonical assembled defaults match the pinned tutorial defaults.
- `pitzDaily`: solver completed, convergence iteration `285`, mesh cells `12225`, and the key steady-file set matches the pinned tutorial defaults.
- Persist the assessment as a dedicated artifact beside the other dispatch outputs so parity claims remain auditable after temporary comparison folders are deleted.
```

- [x] **Step 4: Surface the parity assessment in the report payload and rendered report**

Run: `uv run --project backend pytest backend/tests/test_official_case_validation.py backend/tests/test_submarine_solver_dispatch_tool.py backend/tests/test_submarine_result_report_tool.py -q`
Expected: PASS with official-case parity summaries flowing through dispatch artifacts and the final report

### Task 4: Run Official Baselines And Capture Final Evidence

**Type:** Exploratory

**Files:**
- Notes: `docs/superpowers/session-status/2026-04-17-openfoam-official-case-parity-status.md`
- Notes: `docs/superpowers/research-findings/2026-04-17-openfoam-reference-skill-validation-findings.md`
- Test: `backend/tests/test_openfoam_seed_workflow_middleware.py`
- Test: `backend/tests/test_official_case_assembly.py`
- Test: `backend/tests/test_official_case_validation.py`
- Test: `backend/tests/test_submarine_solver_dispatch_tool.py`
- Test: `backend/tests/test_submarine_result_report_tool.py`

**Goal:** Verify that the deterministic seed thread and the pinned tutorial parity claims both hold against real OpenFOAM 13 executions.

**Collect Evidence:**
- A fresh official-seed thread no longer stops at generic acknowledgement or `write_todos` without CFD tool progress.
- `cavity` completes through design brief -> solver dispatch -> result report and lands a parity status of `matched`.
- `pitzDaily` completes through the same path and lands a parity status of `matched`.
- The session status file records exact command evidence and any remaining risk honestly.

**Stop and Replan If:**
- Deterministic middleware recovery causes duplicate tool loops or blocks legitimate clarification.
- `pitzDaily` still fails parity after the assembly defaults are upgraded to match the pinned tutorial.

**Checkpoint If:**
- Both official cases complete with `matched` parity and the targeted automated suite passes.

- [x] **Step 1: Run the targeted automated suite**

Run: `uv run --project backend pytest backend/tests/test_openfoam_seed_workflow_middleware.py backend/tests/test_official_case_assembly.py backend/tests/test_official_case_validation.py backend/tests/test_submarine_solver_dispatch_tool.py backend/tests/test_submarine_result_report_tool.py -q`
Expected: PASS

- [x] **Step 2: Run the pinned official `cavity` baseline inside the OpenFOAM 13 sandbox and record the observed metrics**

Procedure:

```text
1. Run the official tutorial `blockMesh + icoFoam`.
2. Record completion status, final pseudo-time, and mesh cell count.
3. Compare the generated VibeCFD official-seed run against the same metrics and note whether the parity assessment agrees.
```

- [x] **Step 3: Run the pinned official `pitzDailySteady` baseline inside the OpenFOAM 13 sandbox and record the observed metrics**

Procedure:

```text
1. Run `blockMesh -dict tutorials/resources/blockMesh/pitzDaily` and `foamRun`.
2. Record completion status, final convergence iteration, and mesh cell count.
3. Compare the generated VibeCFD official-seed run against the same metrics and note whether the parity assessment agrees.
```

- [x] **Step 4: Refresh the parity session status file with the verified state and any residual risk**

Run: `git status --short`
Expected: the parity slice files are identifiable and no temporary comparison directories remain in the workspace
