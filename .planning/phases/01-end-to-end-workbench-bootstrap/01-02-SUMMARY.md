---
phase: 01-end-to-end-workbench-bootstrap
plan: 02
subsystem: ui
tags: [react, nextjs, thread-hydration, attachments]
requires:
  - phase: 01-01
    provides: "A successful first-submit bootstrap with a created thread id"
provides:
  - "Created submarine threads preserve the first STL upload and first prompt after route replacement"
  - "Existing-thread refresh shows an explicit rehydration state instead of a blank new-study shell"
affects: [01-03, phase-02-runtime-solver-productization]
tech-stack:
  added: []
  patterns:
    - "Treat route-owned thread identity as the source of truth after `/new` transitions"
    - "Surface rehydration explicitly when server render is blank but client state is still loading"
key-files:
  created: []
  modified:
    - frontend/src/components/workspace/submarine-pipeline.tsx
    - frontend/src/components/workspace/submarine-pipeline-status.ts
    - frontend/src/components/workspace/submarine-pipeline-status.test.ts
key-decisions:
  - "Existing route-state helpers already satisfied the created-thread identity invariants, so the execution focus shifted to truthful refresh UX."
  - "Refresh of an existing submarine thread should show a dedicated rehydration state instead of briefly looking like a brand-new empty study."
patterns-established:
  - "Created-thread refresh can be loading without meaning the user is back on a `/new` bootstrap shell."
  - "Workbench status helpers should distinguish new-thread bootstrap from existing-thread rehydration."
requirements-completed: [FLOW-02]
duration: "~20min"
completed: 2026-04-01
---

# Phase 1: End-to-End Workbench Bootstrap Summary

**Created submarine threads now keep the uploaded STL, first prompt, and workbench identity across route replacement and refresh, with a dedicated rehydration state during reload**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-04-01T08:55:00Z (approx.)
- **Completed:** 2026-04-01T09:10:00Z (approx.)
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Verified that the created thread id is preserved after `/workspace/submarine/new` transitions and that the uploaded `suboff_solid.stl` stays bound to the created thread.
- Confirmed that refreshing the created thread restores the title, uploaded STL, first prompt, and generated design-brief artifacts.
- Added a dedicated rehydration panel so existing-thread refresh no longer presents a misleading blank new-study shell while the client reloads persisted state.

## Task Commits

No git commits were created in this workspace session. The implementation remains uncommitted in the working tree.

## Files Created/Modified

- `frontend/src/components/workspace/submarine-pipeline.tsx` - renders a dedicated rehydration panel for existing threads that are still loading persisted state.
- `frontend/src/components/workspace/submarine-pipeline-status.ts` - distinguishes new-thread bootstrap from existing-thread hydration via `isNewThread` and `hasMessages`.
- `frontend/src/components/workspace/submarine-pipeline-status.test.ts` - covers the rehydration status path.

## Decisions Made

- Kept the existing route ownership contract intact because `page.tsx`, `use-thread-chat.ts`, and `use-thread-chat.state.ts` already met the plan's created-thread identity invariants.
- Solved the refresh usability problem in the cockpit layer instead of inventing a second optimistic bootstrap store.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added an explicit rehydration state for created-thread refresh**

- **Found during:** Task 2 (refresh and direct re-entry validation)
- **Issue:** Persisted thread state restored correctly after client hydration, but the server-rendered shell briefly resembled a new empty study and could mislead operators into thinking attachment binding had been lost.
- **Fix:** Added `isNewThread`/`hasMessages` status inputs plus a dedicated rehydration panel in the submarine pipeline.
- **Files modified:** `frontend/src/components/workspace/submarine-pipeline.tsx`, `frontend/src/components/workspace/submarine-pipeline-status.ts`, `frontend/src/components/workspace/submarine-pipeline-status.test.ts`
- **Verification:** Browser refresh of `dfc49ec4-e0b1-402b-beb2-3a376dd5d8fc` restored the title, first prompt, `suboff_solid.stl`, and design-brief artifacts after hydration.
- **Committed in:** not committed; remains in workspace

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Kept FLOW-02 honest at the UI level without changing the underlying route-state contract.

## Issues Encountered

- No additional route-state bugs were found after the bootstrap fix; the remaining issue was purely how refresh looked before the client finished hydrating.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Route replacement and refresh now preserve the created submarine thread experience.
- Ready for operator-visible failure guidance and regression hardening without falling back to generic chat.

---
*Phase: 01-end-to-end-workbench-bootstrap*
*Completed: 2026-04-01*
