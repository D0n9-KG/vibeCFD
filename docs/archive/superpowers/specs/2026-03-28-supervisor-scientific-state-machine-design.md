# Supervisor Scientific State Machine Design

## 1. Purpose

This document defines the next implementation slice after the unified research evidence chain.

The purpose of this slice is to turn the repository's new evidence semantics into explicit supervisor-stage gating without collapsing the product into a rigid workflow wizard.

The key design rule for this slice is:

- artifact generation continues
- scientific stage promotion becomes explicit and constrained

## 2. Problem Statement

The repository now has a meaningful evidence layer:

- `scientific_verification_assessment`
- `experiment_summary`
- `research_evidence_summary`

But the runtime state still exposes only a generic supervisor contract:

- `review_status`
- `next_recommended_stage`

That creates a mismatch.

Today, the system can already say:

- this run is `verified_but_not_validated`
- this run is `research_ready`
- this run is `blocked`

But it still cannot turn those evidence conclusions into an explicit scientific gate that answers:

- can the supervisor promote this run to a research claim stage?
- if not, what claim level is still allowed?
- what remediation stage should come next?

Without that gate, the repository remains honest but operationally loose. The evidence is there, but the stage progression still behaves like a shallow workflow shell.

## 3. Core Rule

This slice should gate only promotion, not artifact production.

That means:

- reports still render
- compare artifacts still render
- evidence artifacts still render
- the system does not silently suppress output

What changes is the stage machine:

- what claim level is allowed
- what stage is recommended next
- whether the current run is blocked from promotion

This preserves the exploratory nature of `vibe CFD` while making the scientific workflow harder to misuse.

## 4. Approaches Considered

### 4.1 Option A: Reuse only `review_status`

This would overload the existing generic states:

- `ready_for_supervisor`
- `needs_user_confirmation`
- `blocked`

Pros:

- minimal implementation
- no new contract

Cons:

- too little semantic resolution
- cannot distinguish "reviewable but claim-limited" from "fully claim-ready"
- mixes user-confirmation semantics with scientific gate semantics

### 4.2 Option B: Add a separate scientific supervisor gate while keeping `review_status`

This is the recommended design.

Pros:

- preserves the existing runtime contract
- adds a dedicated scientific promotion layer
- keeps user confirmation separate from scientific claim gating

Cons:

- introduces one more contract object
- requires the workbench to show one more summary block

### 4.3 Option C: Build a full supervisor workflow engine now

This would add a more complete multi-stage workflow orchestration system.

Pros:

- more powerful long term

Cons:

- too much scope for this slice
- high workflow-creep risk
- likely to delay progress on the actual research platform

## 5. Recommended Design

Keep the current generic supervisor contract and add a new scientific gate layer:

- `scientific_supervisor_gate`

This gate should become the explicit bridge between:

- `research_evidence_summary`
- stage progression
- claim-level authorization

## 6. Proposed Contract

Recommended new types:

- `SubmarineScientificGateStatus`
  - `ready_for_claim`
  - `claim_limited`
  - `blocked`

- `SubmarineScientificClaimLevel`
  - `delivery_only`
  - `verified_but_not_validated`
  - `validated_with_gaps`
  - `research_ready`

- `SubmarineScientificSupervisorGate`
  - `gate_status`
  - `allowed_claim_level`
  - `source_readiness_status`
  - `recommended_stage`
  - `remediation_stage`
  - `blocking_reasons`
  - `advisory_notes`
  - `artifact_virtual_paths`

This contract should be machine-readable and visible in final reporting and runtime state.

## 7. Gate Semantics

### 7.1 Research Ready

If `research_evidence_summary.readiness_status == "research_ready"`:

- `gate_status = "ready_for_claim"`
- `allowed_claim_level = "research_ready"`
- `recommended_stage = "supervisor-review"`
- no blocking reasons

### 7.2 Verified But Not Validated

If `readiness_status == "verified_but_not_validated"`:

- `gate_status = "claim_limited"`
- `allowed_claim_level = "verified_but_not_validated"`
- `recommended_stage = "supervisor-review"`
- `remediation_stage = "solver-dispatch"` only as guidance for future validation runs, not as an immediate hard block

This means the supervisor may review and deliver the run, but may not promote it to a generic externally validated research claim.

### 7.3 Validated With Gaps

If `readiness_status == "validated_with_gaps"`:

- `gate_status = "claim_limited"`
- `allowed_claim_level = "validated_with_gaps"`
- `recommended_stage = "supervisor-review"`
- `remediation_stage = "result-reporting"` when gaps are provenance or report-linkage related

This means the run may be scientifically stronger than the previous case, but still not fully ready for the highest claim tier.

### 7.4 Blocked Or Insufficient Evidence

If `readiness_status in {"blocked", "insufficient_evidence"}`:

- `gate_status = "blocked"`
- `allowed_claim_level = "delivery_only"`
- `recommended_stage` should point to the remediation stage

Recommended remediation mapping:

- verification or validation failure -> `solver-dispatch`
- provenance/report packaging gap severe enough to prevent review -> `result-reporting`

## 8. Runtime Contract Strategy

The current runtime still needs:

- `review_status`
- `next_recommended_stage`

This slice should not remove them.

Instead:

- `review_status` remains the generic workflow-level signal
- `scientific_supervisor_gate` becomes the scientific promotion signal

Recommended mapping:

- if gate is `blocked`
  - `review_status = "blocked"`
  - `next_recommended_stage = remediation_stage`

- if gate is `ready_for_claim` or `claim_limited`
  - `review_status = "ready_for_supervisor"`
  - `next_recommended_stage = "supervisor-review"`

This keeps the generic runtime stable while making scientific promotion explicit.

## 9. Execution Plan Integration

The current execution-plan template stops at `result-reporting`, even though the workbench already visually includes `supervisor-review`.

This slice should align the two.

Recommended update:

- add `supervisor-review` to the execution-plan template

Suggested semantics:

- before reporting: `pending`
- after reporting and gate not blocked: `ready`
- after reporting and gate blocked: `blocked`

This makes the state machine visible in a structured way without adding a separate workflow editor.

## 10. Artifact Strategy

This slice should add a dedicated gate artifact:

- `supervisor-scientific-gate.json`

Recommended location:

- report artifact directory next to:
  - `final-report.json`
  - `research-evidence-summary.json`
  - `delivery-readiness.json`

The final report should also embed the same structure as:

- `scientific_supervisor_gate`

## 11. Reporting Integration

`backend/packages/harness/deerflow/domain/submarine/reporting.py` should:

1. build `research_evidence_summary`
2. build `scientific_supervisor_gate`
3. write `supervisor-scientific-gate.json`
4. embed `scientific_supervisor_gate` into `final-report.json`
5. derive:
   - `review_status`
   - `next_recommended_stage`
   from the gate

This keeps reporting as the current stage where the evidence chain becomes reviewable and promotable.

## 12. Workbench Integration

The workbench should add a small supervisor scientific gate section showing:

- gate status
- allowed claim level
- recommended stage
- remediation stage
- blocking reasons
- advisory notes
- gate artifact path

This section should sit near the health / evidence area, not in a new page.

## 13. Why This Preserves Vibe CFD

This design does not force the user through a manual approval wizard.

Users can still ask for:

- a quick run
- a benchmark check
- a mesh study
- a research-readiness assessment

The difference is that the repository will now state, in a structured way:

- what claim level is actually allowed
- whether the current run can progress scientifically
- where remediation should happen if promotion is blocked

That is a scientific workflow guardrail, not a workflow prison.

## 14. File Strategy

Recommended implementation targets:

- Create `backend/packages/harness/deerflow/domain/submarine/supervision.py`
  - scientific supervisor gate builder
  - remediation-stage mapping

- Modify `backend/packages/harness/deerflow/domain/submarine/contracts.py`
  - add scientific gate types
  - extend runtime snapshot and supervisor review contract
  - add `supervisor-review` to the execution plan

- Modify `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - emit `scientific_supervisor_gate`
  - emit `supervisor-scientific-gate.json`
  - derive generic review fields from the gate

- Modify `backend/tests/test_submarine_domain_assets.py`
  - cover gate semantics in isolation

- Modify `backend/tests/test_submarine_result_report_tool.py`
  - cover claim-limited and blocked gate outcomes
  - cover gate artifact emission
  - cover runtime-state mapping

- Modify `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - parse `scientific_supervisor_gate`

- Modify `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - cover gate labels and remediation display

- Modify `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - render the scientific gate section

- Modify `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - record the new supervisor scientific gate behavior

## 15. Testing Strategy

Minimum coverage:

1. domain/helper tests
   - `research_ready` -> `ready_for_claim`
   - `verified_but_not_validated` -> `claim_limited`
   - `validated_with_gaps` -> `claim_limited`
   - `blocked` -> `blocked`

2. reporting tests
   - final report embeds `scientific_supervisor_gate`
   - `supervisor-scientific-gate.json` exists
   - generic review fields are derived from the gate

3. frontend utility tests
   - gate labels are stable
   - claim-level labels are stable
   - remediation stage text is stable

4. focused TypeScript / lint verification

## 16. Success Criteria

This slice is successful when:

- the runtime exposes an explicit scientific promotion gate
- `research_evidence_summary` now directly influences stage progression
- claim-limited runs are reviewable but cannot masquerade as full research-ready runs
- blocked runs clearly point to a remediation stage
- the workbench shows these distinctions without requiring a new workflow shell

## 17. Remaining Gaps After This Slice

Even after this stage lands, the repository will still need:

- richer provenance capture
- publication-grade figure and compare delivery
- broader validation support beyond case-local benchmarks
- a stronger end-to-end publication pipeline

That is acceptable. This slice is about making scientific promotion explicit, not finishing every later delivery layer.
