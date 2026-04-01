---
phase: 02-runtime-solver-productization
plan: 02
subsystem: runtime-evidence
tags: [submarine, runtime-evidence, artifacts, mock-validation, frontend, backend]
requires:
  - phase: 02-01
    provides: "Thread-bound geometry continuity and persisted runtime handoff from first submit through clarification turns"
provides:
  - "Canonical request, log, solver-results, and delivery-status artifacts persisted into thread outputs"
  - "Explicit runtime evidence pointers that keep UI links aligned with backend artifact truth"
  - "Mock-validated runtime panel and pipeline views backed by a UUID demo thread fixture"
affects: [phase-02-runtime-solver-productization, phase-02-03, phase-03-scientific-verification-gates, phase-06-research-delivery-workbench]
tech-stack:
  added: []
  patterns:
    - "Derive `artifact_virtual_paths` and `output_delivery_plan` from one canonical evidence bundle before returning dispatch payloads"
    - "Prefer explicit runtime pointers (`request_virtual_path`, `execution_log_virtual_path`, `solver_results_virtual_path`) in the cockpit, with artifact-list fallback for compatibility"
key-files:
  created:
    - frontend/public/demo/threads/54c9fbd7-38f0-49df-b015-4c0e20d568f8/thread.json
    - frontend/public/demo/threads/54c9fbd7-38f0-49df-b015-4c0e20d568f8/user-data/outputs/submarine/design-brief/live-forces-suboff/cfd-design-brief.json
  modified:
    - backend/packages/harness/deerflow/agents/thread_state.py
    - backend/packages/harness/deerflow/domain/submarine/artifact_store.py
    - backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py
    - frontend/src/components/workspace/submarine-runtime-panel.tsx
    - frontend/src/components/workspace/submarine-pipeline.tsx
    - frontend/src/core/config/runtime-base-url.ts
key-decisions:
  - "Canonical runtime evidence must be addressable through explicit runtime pointers instead of UI-side filename inference alone."
  - "Mock-mode validation must override configured LangGraph artifact URLs so the same cockpit contracts can be exercised without a live backend."
patterns-established:
  - "Use deterministic artifact-store helpers when consumers need canonical request/log/results files from `artifact_virtual_paths`."
  - "Treat runtime output delivery as first-class UI state, not an interpretation layered on top of raw filenames."
requirements-progressed: [EXEC-02]
duration: "~80min"
completed: 2026-04-01
---

# Phase 2: Runtime Solver Productization Plan 02 Summary

**Canonical runtime evidence now survives dispatch, thread persistence, mock validation, and cockpit rendering through explicit request/log/results pointers plus delivery-state-aware artifact views.**

## Performance

- **Duration:** ~80 min
- **Started:** 2026-04-01T11:30:49Z
- **Completed:** 2026-04-01T12:49:24Z
- **Tasks:** 3 planned runtime-evidence tasks + 1 mock/browser compatibility follow-up
- **Files modified:** 22 tracked source files + 14 new mock demo artifacts

## Accomplishments

- Extended the persisted `submarine_runtime` contract so runtime snapshots now carry explicit evidence pointers, requested outputs, and output-delivery truth instead of forcing the UI to infer everything from filenames.
- Canonicalized dispatch artifacts so request payloads, summaries, execution logs, solver-results files, and supported postprocess outputs all flow through one deduplicated artifact bundle.
- Updated the runtime panel and submarine pipeline to present execution evidence intentionally, including grouped artifacts, requested-output delivery states, and operator-visible links to request/log/result artifacts.
- Added a UUID-backed mock submarine thread fixture that mirrors a completed SUBOFF run, making browser validation stable on both the runtime panel and the dedicated submarine workbench.
- Fixed mock-mode URL resolution so artifact open/download links stay inside `http://localhost:3000/mock/api/...` even when `NEXT_PUBLIC_LANGGRAPH_BASE_URL` is set.

## Verification

- `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_artifact_store.py tests/test_thread_state_reducers.py`
  - Result: targeted backend runtime-evidence coverage passed in the earlier implementation pass
- `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-runtime-panel.trends.test.ts src/components/workspace/submarine-pipeline-runs.test.ts`
  - Result: passed
- `cd frontend && node --test src/core/config/runtime-base-url.test.ts`
  - Result: passed
- `cd frontend && corepack pnpm typecheck`
  - Result: passed
- Browser validation against mock fixture:
  - `http://localhost:3000/workspace/chats/54c9fbd7-38f0-49df-b015-4c0e20d568f8?mock=true`
  - `http://localhost:3000/workspace/submarine/54c9fbd7-38f0-49df-b015-4c0e20d568f8?mock=true`
  - Confirmed runtime cards and artifact rail expose `openfoam-request.json`, `dispatch-summary.md`, `openfoam-run.log`, `solver-results.json`, `solver-results.md`, requested-output delivery cards, and final report assets.

## Task Commits

This plan accumulated in the workspace across implementation and validation turns before the user requested a single overall checkpoint. Per-task atomic commits do not exist for 02-02; the phase-close documentation and code are being checkpointed together.

## Files Created/Modified

- `backend/packages/harness/deerflow/agents/thread_state.py` - persists the expanded runtime snapshot fields through reducer merges.
- `backend/packages/harness/deerflow/domain/submarine/artifact_store.py` - adds deterministic helpers for canonical execution artifacts.
- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - defines explicit runtime evidence pointer fields.
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` - assembles the canonical artifact bundle and output-delivery payload.
- `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py` - tolerates the richer runtime artifact contract when reading existing study data.
- `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py` - stays aligned with the expanded artifact/runtime payload shape.
- `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py` - reads the richer runtime evidence contract for downstream report generation.
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py` - passes explicit evidence fields into the persisted runtime snapshot.
- `backend/tests/test_submarine_artifact_store.py` - locks deterministic canonical artifact selection in place.
- `backend/tests/test_submarine_solver_dispatch_tool.py` - covers the new runtime evidence fields.
- `backend/tests/test_thread_state_reducers.py` - verifies reducer merges preserve requested outputs and delivery fields.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - types the new runtime evidence and requested-output delivery shapes.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts` - derives result cards and grouped evidence from explicit runtime pointers plus delivery plans.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx` - surfaces request/log/result cards and runtime output delivery sections.
- `frontend/src/components/workspace/submarine-pipeline.tsx` - exposes canonical evidence more intentionally in the dedicated submarine workbench.
- `frontend/src/components/workspace/messages/message-list-item.tsx` - keeps message artifact links mock-aware.
- `frontend/src/components/workspace/artifacts/artifact-file-detail.tsx` - keeps artifact open/download flows mock-aware.
- `frontend/src/components/workspace/artifacts/artifact-file-list.tsx` - keeps artifact download flows mock-aware.
- `frontend/src/core/artifacts/utils.ts` - points mock artifact URLs at the frontend mock API.
- `frontend/src/core/config/runtime-base-url.ts` - lets `isMock` override configured runtime base URLs.
- `frontend/public/demo/threads/54c9fbd7-38f0-49df-b015-4c0e20d568f8/**` - provides a UUID-backed mock completed run for browser validation.

## Decisions Made

- Treated explicit runtime evidence pointers as the preferred contract for all cockpit affordances, because relying on suffix scans alone would make refresh/resume work and later reporting too brittle.
- Kept `artifact_virtual_paths` as a compatibility surface, but forced backend and frontend delivery bookkeeping to share the same canonical evidence bundle.
- Used a mock UUID thread for browser validation after recent live threads lacked a stable solver-results artifact set, ensuring the new UI contracts could still be exercised end-to-end.
- Fixed mock mode at the link-builder layer instead of only in page routing so message, artifact, and runtime-panel downloads all stay coherent under `?mock=true`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added a UUID-backed mock runtime fixture for browser validation**

- **Found during:** Planned browser validation of the runtime panel and submarine pipeline
- **Issue:** Recent live backend threads did not expose a stable solver-results artifact set, so the new 02-02 UI evidence cards could not be verified reliably against the real runtime.
- **Fix:** Created `frontend/public/demo/threads/54c9fbd7-38f0-49df-b015-4c0e20d568f8` with canonical request/log/results/report artifacts and updated its runtime payload fields to mirror the new contract.
- **Files modified:** `frontend/public/demo/threads/54c9fbd7-38f0-49df-b015-4c0e20d568f8/**`
- **Verification:** Both mock pages rendered the expected evidence cards, artifact links, and delivery states in the browser.

**2. [Rule 1 - Bug] Forced mock artifact URLs to win over explicit LangGraph base URLs**

- **Found during:** Mock browser validation on the chat runtime panel
- **Issue:** When `NEXT_PUBLIC_LANGGRAPH_BASE_URL` was set, some mock artifact links still targeted the real backend port and broke the intended fixture-backed validation path.
- **Fix:** Updated runtime base-URL selection and artifact/message link builders so `?mock=true` consistently routes through the frontend mock API.
- **Files modified:** `frontend/src/core/config/runtime-base-url.ts`, `frontend/src/core/config/runtime-base-url.test.ts`, `frontend/src/core/artifacts/utils.ts`, `frontend/src/components/workspace/messages/message-list-item.tsx`, `frontend/src/components/workspace/artifacts/artifact-file-detail.tsx`, `frontend/src/components/workspace/artifacts/artifact-file-list.tsx`
- **Verification:** Mock runtime panel and submarine workbench links opened and downloaded fixture artifacts correctly.

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both deviations were necessary to verify the new runtime-evidence contract in the actual operator-facing UI without inventing separate test-only code paths.

## Issues Encountered

- The existing non-UUID `submarine-cfd-demo` fixture could not drive the dedicated submarine workbench route reliably, so a UUID-backed copy was required.
- The chat workspace still issues a background `POST /threads/search` in some mock-mode states; this did not block 02-02 validation, but it remains cleanup work for a later pass.

## User Setup Required

None - verification used the existing local frontend plus the current backend/runtime setup and a frontend-hosted mock fixture.

## Next Phase Readiness

- Phase 02-02 now gives the cockpit canonical request/log/results/output-delivery truth and a stable mock validation surface.
- The next logical GSD step is executing `02-03-PLAN.md` to persist explicit `runtime_status` meaning and make refresh/re-entry recovery behavior truthful.
- `EXEC-02` is substantially advanced by this plan, while overall Phase 2 completion still depends on finishing refresh/resume runtime truth in 02-03 and revalidating the combined flow against a fresh live DeerFlow run.

---
*Phase: 02-runtime-solver-productization*
*Completed: 2026-04-01*
