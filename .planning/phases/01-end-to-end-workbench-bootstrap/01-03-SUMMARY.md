---
phase: 01-end-to-end-workbench-bootstrap
plan: 03
subsystem: testing
tags: [react, langgraph, errors, windows, pytest]
requires:
  - phase: 01-01
    provides: "Stable first-submit bootstrap and explicit bootstrap failure primitives"
  - phase: 01-02
    provides: "Durable created-thread refresh behavior"
provides:
  - "Bootstrap failures surface as actionable submarine-cockpit guidance"
  - "Fast regression coverage for URL validation, rehydration state, and bootstrap error normalization"
  - "Windows GBK clarification interrupts no longer crash the ask_clarification tool path"
affects: [phase-02-runtime-solver-productization, phase-03-scientific-verification-gates]
tech-stack:
  added: []
  patterns:
    - "Normalize bootstrap failures into operator-facing cockpit copy instead of raw provider errors"
    - "Keep middleware diagnostics encoding-safe when tool questions may contain non-GBK characters"
key-files:
  created:
    - backend/tests/test_clarification_middleware.py
  modified:
    - frontend/src/core/threads/error.ts
    - frontend/src/core/threads/error.test.ts
    - frontend/src/components/workspace/submarine-pipeline-status.ts
    - frontend/src/components/workspace/submarine-pipeline-status.test.ts
    - backend/packages/harness/deerflow/agents/middlewares/clarification_middleware.py
key-decisions:
  - "Bootstrap failures must stay inside the dedicated submarine workbench with actionable retry/config guidance."
  - "Clarification interrupts are part of the critical Phase 1 operator flow and must be robust under Windows GBK stdout."
patterns-established:
  - "Workbench error state should distinguish invalid URL configuration, failed stream rebinding, and ordinary runtime errors."
  - "Backend middleware logging must never be allowed to abort tool delivery in multilingual or scientific-unit prompts."
requirements-completed: [FLOW-03]
duration: "~15min"
completed: 2026-04-01
---

# Phase 1: End-to-End Workbench Bootstrap Summary

**Bootstrap failures now render actionable submarine-cockpit guidance with regression tests, and Windows GBK clarification interrupts no longer collapse into `ask_clarification` tool errors**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-01T09:10:00Z (approx.)
- **Completed:** 2026-04-01T09:20:50Z
- **Tasks:** 3 planned tasks + 1 validation-time bug fix
- **Files modified:** 6

## Accomplishments

- Normalized bootstrap-specific failures such as invalid LangGraph URLs and stream rebind problems into readable submarine-cockpit guidance.
- Added targeted regression coverage for runtime URL trimming, bootstrap error normalization, and the new existing-thread rehydration state.
- Fixed the backend Windows/GBK clarification path so real missing-information prompts render in the workbench instead of surfacing as a tool failure.

## Task Commits

No git commits were created in this workspace session. The implementation remains uncommitted in the working tree.

## Files Created/Modified

- `frontend/src/core/threads/error.ts` - maps bootstrap failures to operator-readable messages.
- `frontend/src/core/threads/error.test.ts` - covers invalid URL, invalid base URL, and stream rebind normalization.
- `frontend/src/components/workspace/submarine-pipeline-status.ts` - renders bootstrap-specific guidance and existing-thread rehydration status.
- `frontend/src/components/workspace/submarine-pipeline-status.test.ts` - covers LangGraph configuration guidance and rehydration state.
- `backend/packages/harness/deerflow/agents/middlewares/clarification_middleware.py` - logs clarification questions safely under non-UTF-8 stdout encodings.
- `backend/tests/test_clarification_middleware.py` - simulates strict GBK stdout and verifies `m³/s` clarification questions no longer crash the middleware.

## Decisions Made

- Treated the backend clarification crash as a Phase 1 issue rather than deferring it, because a real operator flow with missing inputs must end in a clarification request, not a tool error.
- Kept the fix minimal and local to middleware logging so the user-facing clarification message format remains unchanged.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Windows GBK clarification middleware crashes discovered during browser validation**

- **Found during:** Plan verification (live browser flow after FLOW-03 frontend work)
- **Issue:** `ClarificationMiddleware` printed raw question text to GBK stdout. Questions containing characters such as `³` raised `UnicodeEncodeError` and surfaced to users as `Tool 'ask_clarification' failed ...`.
- **Fix:** Added stdout-safe logging helpers that escape only the unsupported characters for the active console encoding, plus a backend regression test that simulates strict GBK stdout.
- **Files modified:** `backend/packages/harness/deerflow/agents/middlewares/clarification_middleware.py`, `backend/tests/test_clarification_middleware.py`
- **Verification:** `uv run pytest tests/test_clarification_middleware.py tests/test_tool_error_handling_middleware.py`; browser submit of a new STL-backed study created thread `88e729ca-18a4-402b-a2f8-da6587928c72` and showed clarification prompts without a tool error.
- **Committed in:** not committed; remains in workspace

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential to make FLOW-03 true in the real Windows workstation environment. No scope creep beyond the operator-visible bootstrap path.

## Issues Encountered

- The old thread `dfc49ec4-e0b1-402b-beb2-3a376dd5d8fc` still contains the previously recorded `ask_clarification` error in its persisted history. New runs now behave correctly, but the historical error message remains part of that thread.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 1 execution now satisfies FLOW-01, FLOW-02, and FLOW-03 in live browser validation.
- The next logical GSD step is phase verification/completion, followed by Phase 2 runtime solver productization.

---
*Phase: 01-end-to-end-workbench-bootstrap*
*Completed: 2026-04-01*
