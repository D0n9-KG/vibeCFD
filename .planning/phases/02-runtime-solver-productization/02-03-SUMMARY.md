---
phase: 02-runtime-solver-productization
plan: 03
subsystem: runtime-recovery
tags: [submarine, runtime-status, refresh, resume, recovery, frontend, backend]
requires:
  - phase: 02-01
    provides: "Thread-bound geometry continuity and controllable solver dispatch execution"
  - phase: 02-02
    provides: "Canonical request/log/results artifacts plus cockpit-facing runtime evidence pointers"
provides:
  - "Authoritative persisted `runtime_status` truth with summary, recovery guidance, and blocker detail"
  - "Blocked/failed-aware submarine cockpit cards, banner state, and sidebar run classification"
  - "Regression coverage for refresh-safe runtime recovery and blocked artifact continuity"
affects: [phase-03-scientific-verification-gates, phase-05-experiment-ops-and-reproducibility, phase-06-research-delivery-workbench]
tech-stack:
  added: []
  patterns:
    - "Derive runtime truth once in backend `build_runtime_snapshot(...)`, then let frontend consume persisted status rather than reconstructing it from stage order"
    - "Treat `runtime_status`, `runtime_summary`, `recovery_guidance`, and `blocker_detail` as the operator-facing recovery contract for submarine threads"
key-files:
  created: []
  modified:
    - backend/packages/harness/deerflow/domain/submarine/runtime_plan.py
    - backend/packages/harness/deerflow/domain/submarine/contracts.py
    - backend/packages/harness/deerflow/agents/thread_state.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py
    - frontend/src/components/workspace/submarine-pipeline-status.ts
    - frontend/src/components/workspace/submarine-stage-cards.tsx
    - frontend/src/components/workspace/submarine-pipeline.tsx
key-decisions:
  - "`runtime_status` became the canonical runtime-level truth, with stage cards and banners consuming it instead of inferring recovery state from `current_stage` alone."
  - "Runtime recovery detail must survive reducer merges, so summary/guidance/blocker fields now preserve the strongest concurrent runtime truth."
patterns-established:
  - "Persist runtime recovery semantics in backend snapshots first; keep frontend logic focused on rendering those semantics consistently."
  - "Use dedicated regression tests for blocked/failed refresh behavior so runtime truth cannot silently regress back into generic pending UI."
requirements-completed: [EXEC-03]
duration: "~36min"
completed: 2026-04-01
---

# Phase 2: Runtime Solver Productization Plan 03 Summary

**Refresh-safe submarine runtime truth now survives backend persistence and frontend re-entry, with explicit blocked/failed/completed semantics instead of stage-order guesswork.**

## Performance

- **Duration:** ~36 min
- **Started:** 2026-04-01T13:18:00Z
- **Completed:** 2026-04-01T13:54:14Z
- **Tasks:** 3 planned runtime-recovery tasks
- **Files modified:** 17

## Accomplishments

- Added explicit persisted runtime recovery fields to `submarine_runtime`: `runtime_status`, `runtime_summary`, `recovery_guidance`, and `blocker_detail`.
- Centralized runtime-truth derivation in backend `runtime_plan.py`, including missing-artifact detection, recoverable block classification, and consistent summary/guidance generation across snapshot writers.
- Updated reducer merging so stronger runtime truth wins during concurrent graph updates instead of letting weaker summaries overwrite blocked/failure context.
- Made the submarine cockpit banner, stage cards, and sidebar run classification runtime-aware, so refresh/re-entry can distinguish ready, running, blocked, failed, and completed states.
- Added regression coverage for blocked reducer merges, failed solver execution, missing canonical results after dispatch, persisted blocked runtime banner state, and sidebar running-vs-blocked truth.

## Verification

- `cd backend && uv run pytest tests/test_thread_state_reducers.py tests/test_submarine_solver_dispatch_tool.py`
  - Result: passed
- `cd frontend && node --test src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-pipeline-shell.test.ts src/app/workspace/submarine/submarine-pipeline-layout.test.ts src/components/workspace/submarine-pipeline-runs.test.ts`
  - Result: passed
- `cd frontend && corepack pnpm typecheck`
  - Result: passed
- Browser validation
  - Not rerun in this turn because no active local frontend/dev-server session was present in the thread terminal; automated backend/frontend coverage passed, but a fresh interactive MCP browser refresh check still remains a follow-up validation item.

## Task Commits

This plan was executed in one continuous workspace pass and will be checkpointed with a single end-of-plan commit after summary/state updates.

## Files Created/Modified

- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - extends the persisted runtime snapshot contract with explicit runtime recovery fields.
- `backend/packages/harness/deerflow/agents/thread_state.py` - preserves strongest runtime truth during concurrent reducer merges.
- `backend/packages/harness/deerflow/domain/submarine/runtime_plan.py` - centralizes runtime-status derivation, missing-artifact detection, and recovery guidance generation.
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py` - writes derived runtime truth into persisted solver-dispatch snapshots.
- `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py` - passes stage summary into the new runtime-truth contract.
- `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py` - passes geometry-stage summary into the new runtime-truth contract.
- `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py` - preserves report-stage runtime summary and blocker detail for downstream re-entry.
- `backend/tests/test_thread_state_reducers.py` - verifies blocked runtime truth wins over weaker concurrent updates.
- `backend/tests/test_submarine_solver_dispatch_tool.py` - covers failed runtime status and blocked dispatch caused by missing canonical results.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - types the new runtime recovery fields.
- `frontend/src/components/workspace/submarine-stage-card.tsx` - adds `blocked` and `failed` visual states.
- `frontend/src/components/workspace/submarine-stage-cards.tsx` - renders runtime-aware stage states and recovery notices from persisted snapshot truth.
- `frontend/src/components/workspace/submarine-pipeline-status.ts` - exposes blocked/failed/completed runtime banner semantics without relying on generic thread errors.
- `frontend/src/components/workspace/submarine-pipeline.tsx` - passes the persisted runtime-truth fields into the cockpit banner and stage snapshot.
- `frontend/src/components/workspace/submarine-pipeline-runs.ts` - keeps sidebar running-state classification aligned with persisted runtime truth.
- `frontend/src/components/workspace/submarine-pipeline-status.test.ts` - locks blocked runtime re-entry behavior.
- `frontend/src/components/workspace/submarine-pipeline-runs.test.ts` - locks sidebar run classification around runtime truth and user-confirmation handoff.

## Decisions Made

- Runtime truth is now backend-authored and persisted, not reconstructed ad hoc in the frontend from stage order.
- Missing canonical artifacts are treated as a recoverable blocked runtime rather than quietly appearing as an ordinary pending stage.
- Refresh-safe UI work needed both banner-level semantics and per-stage visuals; fixing only one of those would still leave researchers guessing after re-entry.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Strengthened reducer merge rules for runtime detail fields**

- **Found during:** Task 1 (persist runtime status and recovery detail)
- **Issue:** Concurrent reducer updates could preserve the stronger `runtime_status` but still let a weaker `runtime_summary` overwrite blocked recovery context.
- **Fix:** Added ranked merge protection for `runtime_summary`, `recovery_guidance`, and `blocker_detail`.
- **Files modified:** `backend/packages/harness/deerflow/agents/thread_state.py`, `backend/tests/test_thread_state_reducers.py`
- **Verification:** `uv run pytest tests/test_thread_state_reducers.py tests/test_submarine_solver_dispatch_tool.py`

**2. [Rule 4 - Validation Gap] Added explicit sidebar runtime-truth regression coverage**

- **Found during:** Task 3 (refresh/resume regression coverage)
- **Issue:** The active plan named stage cards, banner state, and layout shells, but the submarine sidebar also depended on stage-only runtime inference and could silently regress.
- **Fix:** Updated sidebar run classification to respect persisted `runtime_status` and added `submarine-pipeline-runs.test.ts`.
- **Files modified:** `frontend/src/components/workspace/submarine-pipeline-runs.ts`, `frontend/src/components/workspace/submarine-pipeline-runs.test.ts`
- **Verification:** `node --test src/components/workspace/submarine-pipeline-runs.test.ts`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 validation-gap)
**Impact on plan:** Both deviations were necessary to make the persisted runtime-truth contract trustworthy under real concurrent updates and across every operator-facing submarine workbench surface.

## Issues Encountered

- `submarine-stage-cards.tsx` still contains historical Windows/encoding noise in older UI strings, so patching the file required careful minimal edits around stable ASCII anchors.
- The thread terminal did not have an active local dev-server session, so this turn could not finish a fresh MCP browser refresh check on top of the passing automated coverage.

## User Setup Required

None - verification used existing local backend/frontend test tooling only.

## Next Phase Readiness

- Phase 2 is now complete: the platform can launch solver flows, persist canonical runtime evidence, and recover truthful runtime state after refresh or re-entry.
- The next logical GSD step is planning `03-01` in Phase 3 to extract residual/coefficient-stability evidence and turn it into claim-gating rules.
- A fresh live browser validation against an active local runtime remains worthwhile before calling the submarine cockpit fully field-ready for long-running operator use.

---
*Phase: 02-runtime-solver-productization*
*Completed: 2026-04-01*
