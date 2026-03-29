# Scientific Followup History v1 Design

## 1. Goal

Add a deterministic audit trail for `submarine_scientific_followup` so every remediation follow-up leaves behind a traceable record of:

- which remediation handoff triggered it
- what tool target it attempted to execute
- whether it refused, stopped, failed, or completed
- whether a report refresh happened
- which report-stage evidence snapshot now represents the latest review state

## 2. Why This Is The Right Next Slice

The repository can now do one bounded scientific follow-up cycle:

- load a remediation handoff
- execute solver rerun follow-up when allowed
- refresh result reporting after an executed rerun

But there is still no dedicated provenance layer for the follow-up itself.

That means the repository can continue the scientific loop, but it cannot yet answer a research-critical question cleanly:

> what exactly happened across remediation follow-up attempts, and which report snapshot is the current evidence anchor?

For a research-facing `vibe CFD`, that trace should be explicit instead of being inferred indirectly from timeline text or artifact timestamps.

## 3. Design Options

### Option A: Reuse Only `activity_timeline`

Pros:

- minimal new surface area
- no new artifact type

Cons:

- not stable enough as a dedicated audit contract
- hard to summarize across report regeneration
- poor basis for later follow-up policy / budget logic

### Option B: Add A Dedicated Followup History Artifact And Compact Report Summary

Pros:

- explicit, machine-readable provenance
- easy to extend into later policy / budget layers
- keeps orchestration open-ended while making follow-up decisions reviewable

Cons:

- adds a small new artifact contract and runtime pointer

### Option C: Jump Directly To Multi-Step Auto Loop Policy

Pros:

- more visible autonomy

Cons:

- too easy to collapse into a rigid workflow shell
- lacks the audit substrate needed for responsible repeated reruns

## 4. Recommendation

Implement Option B.

This stage should add a dedicated `scientific-followup-history.json` artifact plus a compact `scientific_followup_summary` in report payloads and the workbench.

That gives the repository a real follow-up provenance layer without forcing a closed-loop controller yet.

## 5. Recommended Behavior

Each `submarine_scientific_followup` invocation should append one deterministic history entry that captures:

- the source handoff artifact
- the handoff status and recommended action id
- the target tool name
- the execution outcome
- whether report refresh was performed
- the resulting report path and resulting handoff path when available
- relevant artifact entrypoints for review

History should be recorded for all important branches, not only success:

- missing handoff pointer / load error
- manual follow-up required
- not needed
- unsupported executable target
- direct result-report execution
- solver dispatch planned
- solver dispatch failed
- solver dispatch executed and report refreshed

## 6. Product Boundary

This is still not an autonomous remediation loop.

The repository should:

- record what happened
- surface the latest follow-up status clearly
- preserve the latest history artifact across later report refreshes

The repository should not:

- re-run follow-up recursively
- infer that history implies permission for another rerun
- auto-consume the new history to keep looping

## 7. File Plan

### Backend

- Create: `backend/packages/harness/deerflow/domain/submarine/followup.py`
  - history append / load / summary helpers
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
  - runtime pointer for follow-up history
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - include `scientific_followup_summary` in final-report payload and markdown/html
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`
  - preserve follow-up history pointer through refreshed report-stage runtime
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
  - write history entries for all branches

### Backend Tests

- Modify: `backend/tests/test_submarine_scientific_followup_tool.py`
  - follow-up history append coverage
- Modify: `backend/tests/test_submarine_result_report_tool.py`
  - report payload summary coverage
- Add or modify: `backend/tests/test_submarine_domain_assets.py`
  - contract-level helper coverage if needed

### Frontend

- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - summarize `scientific_followup_summary`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - parsing / labeling coverage
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - compact follow-up history section

## 8. Success Criteria

This stage is successful when:

- every scientific follow-up invocation writes or updates a stable history artifact
- refreshed report payloads expose a compact follow-up summary with latest outcome and artifact links
- the workbench surfaces that summary without hiding the open-ended nature of the system
- the stage remains bounded to recording and surfacing history, not auto-loop control

## 9. Remaining Gap After This Stage

Even after this slice:

- there is still no rerun budget or cost policy
- the supervisor still decides whether another follow-up should run
- there is still no repeated loop until research readiness is achieved

That later policy layer will be much safer to add once follow-up history is explicit.
