---
phase: 02-runtime-solver-productization
plan: 01
subsystem: runtime-continuity
tags: [submarine, uploads, runtime-state, browser-validation, frontend]
requires:
  - phase: 01-03
    provides: "Live submarine workbench validation and safe clarification handling on Windows"
provides:
  - "Thread-scoped geometry continuity from first submit through clarification follow-up turns"
  - "Deterministic thread user-data directories and safe STL recovery across runtime tools"
  - "Defensive first-submit attachment bridging when prompt-state files are dropped before submit"
affects: [phase-02-runtime-solver-productization, phase-02-02]
tech-stack:
  added: []
  patterns:
    - "Recover thread-bound geometry from runtime state, design-brief artifacts, uploaded_files, and thread uploads before asking the user again"
    - "Reconstruct outbound prompt files from controller attachments when the visible attachment chip exists but message.files is empty"
key-files:
  created:
    - frontend/src/components/workspace/input-box.submit.ts
    - frontend/src/components/workspace/input-box.submit.test.ts
  modified:
    - backend/packages/harness/deerflow/agents/middlewares/thread_data_middleware.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py
    - backend/tests/test_thread_data_middleware.py
    - backend/tests/test_submarine_design_brief_tool.py
    - backend/tests/test_submarine_runtime_context.py
    - backend/tests/test_submarine_solver_dispatch_tool.py
    - backend/tests/test_uploads_middleware_core_logic.py
    - frontend/src/components/workspace/input-box.tsx
key-decisions:
  - "A visible STL attachment that never reaches the first submit payload is a productized-runtime bug, even if backend recovery is correct."
  - "Follow-up clarification turns must continue to surface previously uploaded files as thread-bound context instead of silently dropping geometry continuity."
patterns-established:
  - "Use resolve_bound_geometry_virtual_path() as the canonical backend entrypoint for bound STL recovery."
  - "Treat thread history additional_kwargs.files plus uploaded_files middleware state as execution-truth inputs for later turns."
requirements-progressed: [EXEC-01]
duration: "~45min"
completed: 2026-04-01
commits:
  - "7005890 chore: checkpoint workspace before phase 2 execution"
  - "f33b103 fix: preserve submarine geometry attachments across submit"
---

# Phase 2: Runtime Solver Productization Plan 01 Summary

**Geometry continuity is now stable across fresh submit, thread persistence, and clarification follow-up turns; the remaining Phase 2 work is turning that stable bound geometry into canonical runtime evidence and solver-visible cockpit outputs.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-04-01T10:46:00Z (approx.)
- **Completed:** 2026-04-01T11:32:30Z
- **Tasks:** 3 planned backend/runtime tasks + 1 live-validation frontend bug fix
- **Files modified:** 12

## Accomplishments

- Ensured thread-scoped `workspace/uploads/outputs` directories exist before submarine tools inspect them, removing first-run directory brittleness.
- Centralized bound STL recovery through `resolve_bound_geometry_virtual_path()` so design-brief and solver-dispatch reuse the same precedence chain.
- Extended backend regression coverage for uploaded-files recovery, missing-directory safety, and dispatch behavior when no explicit `geometry_path` is passed.
- Fixed the real operator-path bug discovered during browser validation: a visible STL chip on `/workspace/submarine/new` could still submit with `message.files === []`, skipping the upload request entirely.
- Revalidated the live submarine workbench with thread `d9970f48-b3cf-428a-bb80-e499d33ab9d2`, proving that:
  - fresh submit now sends `POST /api/threads/d9970f48-b3cf-428a-bb80-e499d33ab9d2/uploads`
  - `suboff_solid.stl` lands in `backend/.deer-flow/threads/d9970f48-b3cf-428a-bb80-e499d33ab9d2/user-data/uploads`
  - the first human message persists `additional_kwargs.files`
  - `submarine_runtime.geometry_virtual_path` and design-brief artifacts keep `/mnt/user-data/uploads/suboff_solid.stl`
  - a later clarification reply shows `(empty)` newly uploaded files but still carries forward the previously uploaded STL path instead of asking for a new path

## Verification

- `cd backend && uv run pytest tests/test_thread_data_middleware.py tests/test_submarine_design_brief_tool.py tests/test_submarine_runtime_context.py tests/test_submarine_solver_dispatch_tool.py tests/test_uploads_middleware_core_logic.py`
  - Result: `76 passed`
- `cd frontend && node --test src/components/workspace/input-box.submit.test.ts src/core/threads/thread-upload-files.test.ts src/components/ai-elements/prompt-input.files.test.ts`
  - Result: `5 passed`
- Live browser validation:
  - Fresh workbench submit with `C:\Users\D0n9\Desktop\suboff_solid.stl`
  - Upload request `reqid=125` returned `virtual_path: /mnt/user-data/uploads/suboff_solid.stl`
  - History fetch confirmed the first human message stored `additional_kwargs.files`
  - Follow-up confirmation turn preserved the same bound STL under “previous messages and are still available”

## Task Commits

- `7005890 chore: checkpoint workspace before phase 2 execution`
  - Captured the initial Phase 2 runtime-continuity backend work and planning state already present in the workspace.
- `f33b103 fix: preserve submarine geometry attachments across submit`
  - Recorded the validation-driven frontend submit fallback plus the final runtime-continuity regression updates.

## Files Created/Modified

- `backend/packages/harness/deerflow/agents/middlewares/thread_data_middleware.py` - eagerly creates thread user-data directories before submarine tools run.
- `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py` - safely handles missing uploads directories and reuses bound-geometry recovery.
- `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py` - centralizes `resolve_bound_geometry_virtual_path()` recovery logic.
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py` - resolves thread-bound geometry without forcing manual path re-entry.
- `backend/tests/test_thread_data_middleware.py` - asserts thread uploads/output directories exist before downstream tool execution.
- `backend/tests/test_submarine_design_brief_tool.py` - covers geometry recovery from uploaded-files state and persisted brief/runtime data.
- `backend/tests/test_submarine_runtime_context.py` - covers the shared geometry recovery precedence chain.
- `backend/tests/test_submarine_solver_dispatch_tool.py` - covers dispatch recovery without explicit `geometry_path`.
- `backend/tests/test_uploads_middleware_core_logic.py` - remains part of the continuity regression bundle.
- `frontend/src/components/workspace/input-box.tsx` - routes submit payload construction through the new fallback helper.
- `frontend/src/components/workspace/input-box.submit.ts` - rebuilds submission files from controller attachments when needed.
- `frontend/src/components/workspace/input-box.submit.test.ts` - locks the first-submit attachment fallback in place.

## Decisions Made

- Treated the fresh `/workspace/submarine/new` failure as a real Phase 2 runtime-continuity bug rather than dismissing it as an isolated UI issue, because the operator-visible attachment chip falsely implied the geometry would be available to DeerFlow.
- Kept the frontend fix intentionally defensive: even if the root provider timing bug lives deeper in prompt state management, visible attachments must still be submitted.
- Considered `EXEC-01` advanced but not fully complete. Geometry continuity is now unblocked, but canonical dispatch evidence and cockpit-visible runtime proof remain the responsibility of Plan 02.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed first-submit attachment loss discovered during live submarine workbench validation**

- **Found during:** Plan verification on `http://localhost:3000/workspace/submarine/new`
- **Issue:** A fresh thread could show `suboff_solid.stl` in the input chip while the actual outbound submit payload contained no files, producing no upload request and leaving the generated brief unbound.
- **Fix:** Added `input-box.submit.ts` and updated `InputBox` so submission falls back to current controller attachments when `PromptInputMessage.files` is unexpectedly empty.
- **Files modified:** `frontend/src/components/workspace/input-box.tsx`, `frontend/src/components/workspace/input-box.submit.ts`, `frontend/src/components/workspace/input-box.submit.test.ts`
- **Verification:** Frontend node tests passed; live browser validation of thread `d9970f48-b3cf-428a-bb80-e499d33ab9d2` confirmed upload request `reqid=125`, persisted file metadata, and stable follow-up geometry continuity.
- **Committed in:** `f33b103`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Required to make the backend geometry-recovery work reachable from the real researcher-facing entry path.

## Issues Encountered

- DevTools `fill()` updated the textarea DOM value without reliably updating the React-controlled state, so keyboard typing was used for trustworthy browser validation.
- The LangGraph history endpoint as polled by the browser used `limit=1` responses that were not sufficient for deep diagnosis; a direct history fetch was required to inspect the full persisted message/runtime state.

## User Setup Required

None - the validated flow used the existing local frontend, backend, and Docker-backed OpenFOAM environment.

## Next Phase Readiness

- Phase 02-01 has unblocked the geometry continuity boundary for fresh submits and later clarification turns.
- The next logical GSD step is executing `02-02-PLAN.md` to canonicalize runtime evidence and surface solver logs, metrics, and requested-output delivery truth in the cockpit.
- `EXEC-01` is closer but still not fully complete: the project now preserves bound geometry correctly, yet full controlled dispatch/evidence persistence must still be verified through the remaining Phase 2 plans.

---
*Phase: 02-runtime-solver-productization*
*Completed: 2026-04-01*
