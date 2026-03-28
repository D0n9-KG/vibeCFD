# Scientific Remediation Handoff v1 Design

## 1. Goal

Turn structured remediation plans into explicit supervisor handoff instructions so the repository can say not only what evidence is missing, but also which concrete DeerFlow tool call should happen next when a remediation step is auto-executable.

This slice should move the system from remediation planning toward remediation execution without jumping directly into a fully autonomous rerun engine.

## 2. Why This Is The Right Next Slice

The repository now has:

- scientific supervisor gating
- scientific remediation planning
- existing `supervisor_handoff_virtual_path` wiring from solver dispatch

But after result reporting, the system still lacks a clean machine-readable answer to:

- what tool should run next
- which arguments should it receive
- whether the next step is auto-executable or still manual

That means the repository can diagnose and plan remediation, but the next step still has to be reconstructed mentally.

## 3. Product Principle

This slice should remain advisory and executable-by-contract, not silently self-running.

That means:

- emit explicit follow-up tool suggestions
- keep manual-required actions manual
- expose the handoff artifact in runtime state and reports
- do not automatically launch solver reruns yet

## 4. Recommended Approach

Add a new report-stage handoff artifact that translates remediation actions into next-tool recommendations.

Recommended artifact:

- `scientific-remediation-handoff.json`

Recommended runtime behavior:

- update `supervisor_handoff_virtual_path` after result reporting to point to this new artifact

Recommended handoff semantics:

- if there is at least one `auto_executable` remediation action, emit a suggested tool call
- if only `manual_required` actions remain, emit a manual handoff summary without a tool call
- if no remediation is needed, emit a no-op handoff

## 5. Proposed Contract

Add a new final-report block:

- `scientific_remediation_handoff`

Suggested fields:

- `handoff_status`
  - `ready_for_auto_followup`
  - `manual_followup_required`
  - `not_needed`
- `recommended_action_id`
- `tool_name`
- `tool_args`
- `reason`
- `artifact_virtual_paths`
- `manual_actions`

## 6. Tool Mapping v1

### 6.1 Execute Scientific Studies

If the remediation action is `execute-scientific-studies`, emit:

- `tool_name = "submarine_solver_dispatch"`
- `tool_args` copied from current runtime snapshot:
  - `geometry_path`
  - `task_description`
  - `task_type`
  - `selected_case_id`
  - simulation requirements
  - `execute_scientific_studies = true`

This is the most important auto-followup path because it closes missing verification evidence with a deterministic rerun.

### 6.2 Result-Reporting Packaging

If the remediation action is `regenerate-research-report-linkage`, emit:

- `tool_name = "submarine_result_report"`
- `tool_args` containing the report title when available

### 6.3 Manual Validation Reference

If only `attach-validation-reference` remains, emit:

- `handoff_status = "manual_followup_required"`
- no `tool_name`
- manual action summary preserved in `manual_actions`

## 7. Files

### Backend

- Create: `backend/packages/harness/deerflow/domain/submarine/handoff.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- Modify: `backend/tests/test_submarine_domain_assets.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

### Frontend

- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`

### Docs

- Modify: `docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

## 8. Success Criteria

This stage is successful when:

- result reporting emits a remediation handoff contract
- runtime state points `supervisor_handoff_virtual_path` at the latest report-stage handoff
- workbench users can see whether a next tool call is ready or manual input is still required
- the system becomes more actionable without yet auto-running expensive follow-up jobs

## 9. Remaining Gap After This Stage

Even after this slice:

- follow-up tool calls are still recommendations rather than automatic execution
- no loop re-enters solver dispatch by itself
- no policy layer exists yet for when expensive reruns should auto-start
