---
phase: 03-scientific-verification-gates
plan: 01
subsystem: stability-evidence
tags: [submarine, scientific-verification, stability-evidence, gate-status, frontend, backend]
requires:
  - phase: 02-02
    provides: "Canonical solver-dispatch artifacts and result persistence"
  - phase: 02-03
    provides: "Refresh-safe runtime truth and blocked/failed cockpit semantics"
provides:
  - "Canonical `stability-evidence.json` artifacts for eligible baseline runs"
  - "Dispatch-time `scientific_verification_assessment` and persisted runtime scientific status"
  - "Workbench-visible SCI-01 stability summaries plus completed-but-blocked/limited pipeline states"
affects: [phase-03-scientific-verification-gates, phase-05-experiment-ops-and-reproducibility, phase-06-research-delivery-workbench]
tech-stack:
  added: []
  patterns:
    - "Build structured SCI-01 evidence once at solver-dispatch time, then let reporting and cockpit surfaces consume that artifact instead of reconstructing the same logic independently."
    - "Persist both artifact pointers and structured scientific payloads in `submarine_runtime` so refresh/re-entry can surface scientific readiness before a final report exists."
key-files:
  created:
    - .planning/phases/03-scientific-verification-gates/03-01-SUMMARY.md
  modified:
    - backend/packages/harness/deerflow/domain/submarine/artifact_store.py
    - backend/packages/harness/deerflow/domain/submarine/contracts.py
    - backend/packages/harness/deerflow/domain/submarine/reporting.py
    - backend/packages/harness/deerflow/domain/submarine/runtime_plan.py
    - backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py
    - backend/packages/harness/deerflow/domain/submarine/verification.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py
    - backend/tests/test_submarine_result_report_tool.py
    - backend/tests/test_submarine_solver_dispatch_tool.py
    - frontend/src/components/workspace/submarine-pipeline-status.test.ts
    - frontend/src/components/workspace/submarine-pipeline-status.ts
    - frontend/src/components/workspace/submarine-pipeline.tsx
    - frontend/src/components/workspace/submarine-runtime-panel.contract.ts
    - frontend/src/components/workspace/submarine-runtime-panel.tsx
    - frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
    - frontend/src/components/workspace/submarine-runtime-panel.utils.ts
key-decisions:
  - "SCI-01 stability evidence is now a canonical solver-dispatch artifact, not a late report-only inference."
  - "Reporting and cockpit status consume the same structured stability payload first, using raw solver metrics only as fallback."
  - "A runtime marked `completed` can still present `blocked`, `claim_limited`, or `needs_more_verification` scientific outcomes at the top-line workbench level."
patterns-established:
  - "Treat scientific readiness as first-class runtime state alongside operational runtime state."
  - "Keep artifact bundle, runtime snapshot, and frontend status wording aligned around the same backend-authored scientific gate contract."
requirements-completed: [SCI-01]
duration: "~70min"
completed: 2026-04-01
---

# Phase 3: Scientific Verification Gates Plan 01 Summary

**SCI-01 stability evidence is now explicit, persisted, and visible across solver dispatch, final reporting, and the submarine cockpit instead of being reconstructed late from raw metrics.**

## Performance

- **Duration:** ~70 min
- **Started:** 2026-04-01T14:13:20Z
- **Completed:** 2026-04-01T15:23:17Z
- **Tasks:** 3 planned scientific-verification tasks
- **Files modified:** 17

## Accomplishments

- Added canonical `stability-evidence.json` support to the solver-dispatch artifact bundle and runtime/report contracts.
- Built structured stability evidence generation in `verification.py`, including residual-threshold evidence, force-coefficient tail evidence, per-requirement status rows, and top-level SCI-01 status/summary.
- Persisted `stability_evidence_virtual_path`, `stability_evidence`, and `scientific_verification_assessment` directly into dispatch-time runtime snapshots and builtin tool outputs.
- Updated result reporting to load the same structured stability artifact and use it when building scientific verification, research evidence, and supervisor-gate payloads.
- Extended cockpit typing, artifact classification, runtime panel summaries, and pipeline banner logic so completed runs can still surface scientific blockers or evidence gaps clearly.
- Added regression coverage for new structured stability artifacts, scientific verification assessment hydration, stability-evidence artifact labeling, and completed-but-scientifically-blocked cockpit states.

## Verification

- `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py`
  - Result: passed
- `cd frontend && node --test src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - Result: passed
- `cd frontend && corepack pnpm typecheck`
  - Result: passed
- Browser validation
  - Not rerun in this turn because there was no active local frontend/dev-server session to drive with MCP; automated coverage passed, but an interactive check of the new stability-evidence panel and scientific gate banner remains a follow-up validation item.

## Task Commits

This plan was executed in one continuous workspace pass and is being checkpointed with a single end-of-plan commit after summary/state updates.

## Files Created/Modified

- `backend/packages/harness/deerflow/domain/submarine/artifact_store.py` - adds canonical resolution/loading for `stability-evidence.json`.
- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - extends runtime/report payload contracts with structured stability evidence and scientific verification fields.
- `backend/packages/harness/deerflow/domain/submarine/verification.py` - builds structured SCI-01 evidence and lets scientific verification consume that artifact deterministically.
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` - persists stability evidence during execution and computes dispatch-time scientific verification state.
- `backend/packages/harness/deerflow/domain/submarine/runtime_plan.py` - maps scientific verification outcomes into runtime execution-plan status.
- `backend/packages/harness/deerflow/domain/submarine/reporting.py` - hydrates structured stability evidence and includes it in final report payloads.
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py` - persists new runtime scientific fields into thread state.
- `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py` - preserves structured scientific gate status during final report refresh.
- `backend/tests/test_submarine_solver_dispatch_tool.py` - updates dispatch/runtime assertions and locks emitted stability-evidence artifacts.
- `backend/tests/test_submarine_result_report_tool.py` - verifies result-report SCI-01 hydration using structured stability evidence.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - adds typed stability-evidence payloads and runtime scientific verification fields.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts` - classifies stability artifacts and builds a stability-evidence summary model for the cockpit.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx` - renders runtime/final-report SCI-01 stability summaries.
- `frontend/src/components/workspace/submarine-pipeline-status.ts` - surfaces scientifically blocked/limited/incomplete completed-run states.
- `frontend/src/components/workspace/submarine-pipeline.tsx` - passes scientific gate and verification fields into top-line pipeline status.
- `frontend/src/components/workspace/submarine-pipeline-status.test.ts` - locks completed scientific gate banner behavior.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts` - locks artifact labeling and stability-evidence summary building.

## Decisions Made

- Structured SCI-01 evidence is produced once and shared everywhere, instead of maintaining parallel dispatch/report/front-end interpretations.
- Runtime persistence now carries both the artifact pointer and the structured payload so refresh-safe UI can render scientific state before final report generation.
- Completed runtime status remains operational truth, while scientific gate status separately communicates whether the result is blocked, limited, or claim-ready for research use.

## Deviations from Plan

### Auto-fixed Issues

**1. [Test Alignment] Updated solver-dispatch expectations for dispatch-time scientific verification**

- **Found during:** backend regression run
- **Issue:** After dispatch started computing `scientific_verification_assessment` immediately, older tests still expected `scientific-verification` to remain `pending`.
- **Fix:** Updated backend assertions to reflect the new completed/blocked runtime-plan semantics and structured stability artifact content.
- **Files modified:** `backend/tests/test_submarine_solver_dispatch_tool.py`
- **Verification:** `uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py`

**2. [Fixture Gap] Restored missing structured stability artifact coverage in result-report tests**

- **Found during:** backend regression run
- **Issue:** One result-report test asserted hydrated stability evidence but did not actually create `stability-evidence.json` in its fixture.
- **Fix:** Added the missing fixture artifact and locked the final-report SCI-01 summary against it.
- **Files modified:** `backend/tests/test_submarine_result_report_tool.py`
- **Verification:** `uv run pytest tests/test_submarine_result_report_tool.py`

**3. [Copy Drift] Matched cockpit test assertions to the current Chinese scientific-gate wording**

- **Found during:** frontend regression run
- **Issue:** A pipeline-status test still expected English `delivery` phrasing while the shipped banner copy now uses Chinese operator-facing wording.
- **Fix:** Updated the test to assert the actual localized claim-level text.
- **Files modified:** `frontend/src/components/workspace/submarine-pipeline-status.test.ts`
- **Verification:** `node --test src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts`

---

**Total deviations:** 3 auto-fixed (2 test-alignment, 1 copy-drift)
**Impact on plan:** These fixes were required to lock the new scientific-gate contract cleanly across backend persistence and localized cockpit rendering.

## Issues Encountered

- Existing test coverage assumed SCI-01 status would only emerge during report synthesis, so several assertions had to be realigned to dispatch-time scientific verification.
- The submarine frontend uses localized operator-facing copy, which made one previously English-biased status assertion brittle.
- Browser validation was still gated by the lack of a live local dev-server session in the thread terminal.

## User Setup Required

None for automated verification. A follow-up interactive browser check will need the local frontend/dev server running.

## Next Phase Readiness

- Plan `03-01` is complete: baseline runs now emit explicit SCI-01 stability evidence and the workbench can surface scientific blockers without opening raw JSON manually.
- The next logical GSD step is executing `03-02` to package sensitivity-study workflows and make mesh/domain/time-step verification artifacts researcher-operable rather than only contract-aware.
- After `03-02`, `03-03` can build benchmark-backed claim decisions on top of the now-stable SCI-01 evidence contract.

---
*Phase: 03-scientific-verification-gates*
*Completed: 2026-04-01*
