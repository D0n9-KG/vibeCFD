---
phase: 01-end-to-end-workbench-bootstrap
plan: 01
subsystem: ui
tags: [react, langgraph, bootstrap, thread]
requires: []
provides:
  - "Validated LangGraph client construction with absolute runtime URLs"
  - "Deterministic new-thread create/bind/submit flow for the submarine workbench"
affects: [01-02, 01-03, phase-02-runtime-solver-productization]
tech-stack:
  added: []
  patterns:
    - "Resolve and validate runtime URLs before constructing the LangGraph client"
    - "Create the thread and wait for stream rebinding before the first submit"
key-files:
  created: []
  modified:
    - frontend/src/core/api/api-client.ts
    - frontend/src/core/config/runtime-base-url.ts
    - frontend/src/core/config/runtime-base-url.test.ts
    - frontend/src/core/threads/hooks.ts
    - frontend/src/components/workspace/input-box.tsx
    - frontend/src/components/workspace/submarine-pipeline.tsx
    - frontend/src/components/workspace/submarine-stage-cards.tsx
key-decisions:
  - "Whitespace-only runtime environment overrides are treated as absent so standalone local defaults keep working."
  - "LangGraph clients are cached by resolved absolute apiUrl instead of a global singleton to prevent stale endpoint reuse."
patterns-established:
  - "First-submit bootstrap must create the thread, rebind the stream target, and only then upload files and submit the message."
  - "Submit handlers in the submarine workbench return promises so bootstrap failures propagate back into the cockpit."
requirements-completed: [FLOW-01]
duration: "~25min"
completed: 2026-04-01
---

# Phase 1: End-to-End Workbench Bootstrap Summary

**Validated LangGraph bootstrap URLs and serialized the first submarine submit so `/workspace/submarine/new` creates a real thread before upload and stream submission**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-04-01T08:40:00Z (approx.)
- **Completed:** 2026-04-01T08:55:00Z (approx.)
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Trimmed and validated runtime base URLs before LangGraph client construction, with regression coverage for whitespace env values.
- Rebound the new-thread submit path so the created thread id is used consistently for thread creation, upload, and stream submission.
- Removed fire-and-forget submit calls from the submarine input path so bootstrap failures surface instead of disappearing into the console.

## Task Commits

No git commits were created in this workspace session. The implementation remains uncommitted in the working tree.

## Files Created/Modified

- `frontend/src/core/api/api-client.ts` - validates runtime apiUrl and caches LangGraph clients by resolved endpoint.
- `frontend/src/core/config/runtime-base-url.ts` - trims configured backend/LangGraph URLs before fallback resolution.
- `frontend/src/core/config/runtime-base-url.test.ts` - covers trimmed and whitespace-only environment URL handling.
- `frontend/src/core/threads/hooks.ts` - blocks first submit until the new thread stream target is rebound.
- `frontend/src/components/workspace/input-box.tsx` - awaits async submit handlers.
- `frontend/src/components/workspace/submarine-pipeline.tsx` - propagates async send promises through the submarine cockpit.
- `frontend/src/components/workspace/submarine-stage-cards.tsx` - accepts async confirmation handlers from the workbench.

## Decisions Made

- Used explicit URL validation with `new URL(...)` before LangGraph client construction so malformed or empty runtime values fail fast with a readable error.
- Kept bootstrap strictly transactional: create thread, rebind stream, then upload/submit using the same thread id.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Propagated async bootstrap failures through the submarine submit path**

- **Found during:** Task 2 (new-thread create/bind/submit flow)
- **Issue:** `InputBox` and submarine stage callbacks fired `sendMessage()` without awaiting the promise, which could hide bootstrap failures and make the cockpit appear idle while the first submit had already failed.
- **Fix:** Updated the input box, pipeline, and stage-card confirmation interfaces to support async submit handlers and await the initial send.
- **Files modified:** `frontend/src/components/workspace/input-box.tsx`, `frontend/src/components/workspace/submarine-pipeline.tsx`, `frontend/src/components/workspace/submarine-stage-cards.tsx`
- **Verification:** `corepack pnpm typecheck`; browser submit from `/workspace/submarine/new` reached `POST /threads` and `runs/stream` without unhandled rejection.
- **Committed in:** not committed; remains in workspace

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Required for truthful FLOW-01 behavior. No scope creep beyond the bootstrap path.

## Issues Encountered

- Existing runtime configuration could include whitespace-only URL overrides, and the previous singleton client cache could silently reuse a stale endpoint. Both were corrected during bootstrap hardening.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `/workspace/submarine/new` now creates a real LangGraph thread and reaches live stream submission.
- Ready to validate attachment persistence, created-thread refresh behavior, and operator-visible cockpit status.

---
*Phase: 01-end-to-end-workbench-bootstrap*
*Completed: 2026-04-01*
