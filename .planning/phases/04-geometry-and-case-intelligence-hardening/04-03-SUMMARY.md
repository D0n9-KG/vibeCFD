---
phase: 04-geometry-and-case-intelligence-hardening
plan: 03
subsystem: researcher-approval-gating
tags: [submarine, calculation-plan, researcher-approval, geometry-gating, cockpit, frontend, backend]
requires:
  - phase: 04-01
    provides: "Structured geometry trust artifacts and shared calculation-plan helpers"
  - phase: 04-02
    provides: "Case provenance and selected-case evidence summaries"
provides:
  - "Persisted calculation-plan draft with per-item approval state, origin, provenance, and researcher notes"
  - "Dynamic runtime gating that distinguishes immediate clarification from pending consolidated review"
  - "Cockpit, pipeline, and confirmation-message surfaces that keep pre-compute approval separate from post-compute scientific claim labels"
affects: [phase-04-geometry-and-case-intelligence-hardening, phase-05-experiment-ops-and-reproducibility, phase-06-research-delivery-workbench]
tech-stack:
  added: []
  patterns:
    - "Use one calculation-plan contract across design brief, geometry preflight, runtime context, solver dispatch, confirmation actions, and the cockpit."
    - "Model pre-compute approval as its own UI/runtime status family rather than overloading scientific claim-level copy."
key-files:
  created:
    - .planning/phases/04-geometry-and-case-intelligence-hardening/04-03-SUMMARY.md
    - frontend/public/demo/threads/submarine-phase4-review-demo/thread.json
    - frontend/public/demo/threads/submarine-phase4-review-demo/user-data/outputs/submarine/design-brief/phase4-review/cfd-design-brief.json
    - frontend/public/demo/threads/submarine-phase4-review-demo/user-data/outputs/submarine/geometry-check/phase4-review/geometry-check.json
    - frontend/src/app/mock/api/threads/mock-thread-store.ts
    - frontend/src/app/mock/api/threads/mock-thread-store.test.ts
    - frontend/src/app/mock/api/threads/[thread_id]/runs/stream/route.ts
  modified:
    - backend/packages/harness/deerflow/domain/submarine/contracts.py
    - backend/packages/harness/deerflow/domain/submarine/design_brief.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py
    - backend/tests/test_submarine_design_brief_tool.py
    - backend/tests/test_submarine_geometry_check_tool.py
    - backend/tests/test_submarine_runtime_context.py
    - backend/tests/test_submarine_solver_dispatch_tool.py
    - frontend/src/components/workspace/submarine-confirmation-actions.ts
    - frontend/src/components/workspace/submarine-confirmation-actions.test.ts
    - frontend/src/components/workspace/submarine-pipeline-runs.test.ts
    - frontend/src/components/workspace/submarine-pipeline-runs.ts
    - frontend/src/components/workspace/submarine-pipeline-status.test.ts
    - frontend/src/components/workspace/submarine-pipeline-status.ts
    - frontend/src/components/workspace/submarine-pipeline.tsx
    - frontend/src/components/workspace/submarine-runtime-panel.contract.ts
    - frontend/src/components/workspace/submarine-runtime-panel.tsx
    - frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
    - frontend/src/components/workspace/submarine-runtime-panel.utils.ts
    - frontend/src/components/workspace/submarine-stage-cards.tsx
    - frontend/src/components/workspace/submarine-task-intelligence-view.ts
    - frontend/src/app/mock/api/threads/[thread_id]/history/route.ts
key-decisions:
  - "Researcher approval authorizes computation only; it does not change `scientific_gate_status` or `allowed_claim_level`."
  - "Immediate ambiguity and pending consolidated review share one calculation-plan vocabulary, but only the severe branch interrupts early."
patterns-established:
  - "Route UI stage selection, top-line pipeline copy, and confirmation prompts from calculation-plan state before any real solver execution begins."
  - "Preserve pre-compute approval copy in English operator-facing labels where needed to avoid accidental overlap with the localized scientific-gate wording already used post-compute."
requirements-completed: [GEO-03]
duration: "~2h across resumed backend/frontend integration, tests, and state wrap-up"
completed: 2026-04-02
---

# Phase 4: Geometry and Case Intelligence Hardening Plan 03 Summary

**Researchers now get an explicit calculation-plan review gate: ambiguous geometry or case assumptions stay reviewable, clarifiable, and execution-blocking without masquerading as scientific claim-level outcomes.**

## Performance

- **Duration:** ~2 h across resumed backend/frontend integration, test alignment, and planning-state wrap-up
- **Completed:** 2026-04-02T14:42:05+08:00
- **Tasks:** 3 planned researcher-approval tasks
- **Files modified:** 23

## Accomplishments

- Added first-class `calculation_plan` support to the design brief and runtime contracts, including per-item origin, source metadata, confidence, approval state, immediate-confirmation flag, and researcher notes.
- Persisted calculation-plan carry-over through design brief, geometry preflight, runtime context, and solver dispatch so the same draft survives each phase of setup.
- Hardened backend gating so any pending calculation-plan item blocks execution, while severe items force immediate clarification and route the next stage to `user-confirmation`.
- Reworked confirmation-message builders to carry both a `brief_snapshot` and a `calculation_plan_snapshot`, keeping approve vs revise semantics explicit.
- Extended task-intelligence, stage cards, pipeline status, pipeline runs, and the detailed runtime panel so the cockpit can show pending researcher confirmation vs immediate clarification without reusing post-compute scientific claim language.
- Added focused frontend assertions for calculation-plan summaries, user-confirmation routing, and pre-compute pipeline copy, alongside the backend regression suite.
- Added a dedicated Phase 4 mock review fixture plus a mock `runs/stream` route so browser validation can exercise clarify, approve, and rerun CTAs without triggering real solver execution or falling into a 404 state.

## Verification

- `cd backend && uv run pytest tests/test_submarine_design_brief_tool.py tests/test_submarine_geometry_check_tool.py tests/test_submarine_runtime_context.py tests/test_submarine_solver_dispatch_tool.py`
  - Result: passed (`49 passed`)
- `cd backend && uv run pytest tests/test_submarine_domain_assets.py tests/test_submarine_result_report_tool.py`
  - Result: passed (`46 passed`)
- `cd frontend && node --test src/components/workspace/submarine-confirmation-actions.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-shell.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-pipeline-runs.test.ts`
  - Result: passed (`56 passed`)
- `cd frontend && node --test src/app/mock/api/threads/mock-thread-store.test.ts`
  - Result: passed (`1 passed`)
- `cd frontend && corepack pnpm typecheck`
  - Result: passed
- Browser validation
  - Reran against `http://localhost:3000/workspace/submarine/submarine-phase4-review-demo?mock=true`
  - Verified the cockpit header, task-intelligence summary, geometry preflight card, and solver-dispatch hold banner all use calculation-plan approval language instead of scientific-claim wording.
  - Verified `补充待确认条件`, `确认通过`, and `需要重算` each kept the researcher inside the workbench and posted successfully to the mock `runs/stream` endpoint (`200`), fixing the previous browser-validation 404.

## Task Commits

This plan was completed inline in the existing workspace without per-task commits in this turn. Summary/state updates capture the completion checkpoint.

## Files Created/Modified

- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - extends runtime/design-brief contracts with calculation-plan approval fields.
- `backend/packages/harness/deerflow/domain/submarine/design_brief.py` - persists calculation-plan items through design-brief updates.
- `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py` - carries calculation-plan and immediate-confirmation state into runtime updates.
- `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py` - merges geometry-derived assumptions into the calculation plan.
- `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py` - computes dynamic confirmation status from the calculation plan.
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py` - blocks execution until the calculation plan is researcher-confirmed.
- `frontend/src/components/workspace/submarine-confirmation-actions.ts` - emits explicit approve/revise prompts with persisted brief and calculation-plan snapshots.
- `frontend/src/components/workspace/submarine-task-intelligence-view.ts` - derives confirmation-state, pending counts, and immediate-clarification counts from calculation-plan semantics.
- `frontend/src/components/workspace/submarine-stage-cards.tsx` - surfaces geometry-review details, solver-hold banners, and reviewer-facing calculation-plan status on the active workbench cards.
- `frontend/src/components/workspace/submarine-pipeline-status.ts` - adds pre-compute approval statuses that remain distinct from scientific claim outcomes.
- `frontend/src/components/workspace/submarine-pipeline.tsx` - threads calculation-plan state into top-line pipeline status and stage snapshots.
- `frontend/src/components/workspace/submarine-pipeline-runs.ts` - routes pending calculation-plan approval to the user-confirmation stage.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx` - renders detailed calculation-plan review and provenance details in the full runtime panel.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts` - builds summary labels, counts, and stage-track support for researcher confirmation.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - adds the typed payloads required by the new calculation-plan and provenance UI.
- `frontend/src/components/workspace/submarine-confirmation-actions.test.ts` - locks approve vs revise prompt content.
- `frontend/src/components/workspace/submarine-pipeline-status.test.ts` - locks immediate clarification and pending confirmation pipeline copy.
- `frontend/src/components/workspace/submarine-pipeline-runs.test.ts` - locks user-confirmation routing for pending calculation-plan approval.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts` - locks calculation-plan summary and legacy stage-track behavior.
- `frontend/public/demo/threads/submarine-phase4-review-demo/thread.json` - provides a deterministic Phase 4 review fixture focused on geometry ambiguity and case approval.
- `frontend/public/demo/threads/submarine-phase4-review-demo/user-data/outputs/submarine/design-brief/phase4-review/cfd-design-brief.json` - exposes the design-brief artifact used during Phase 4 browser validation.
- `frontend/public/demo/threads/submarine-phase4-review-demo/user-data/outputs/submarine/geometry-check/phase4-review/geometry-check.json` - exposes the geometry-preflight artifact used during Phase 4 browser validation.
- `frontend/src/app/mock/api/threads/mock-thread-store.ts` - shares deterministic mock-thread overrides and action-state mutation for browser-driven confirmation flows.
- `frontend/src/app/mock/api/threads/mock-thread-store.test.ts` - locks the mock CTA state mutation used during browser validation.
- `frontend/src/app/mock/api/threads/[thread_id]/runs/stream/route.ts` - provides the missing mock stream endpoint so Phase 4 approval CTAs can complete without a 404.
- `frontend/src/app/mock/api/threads/[thread_id]/history/route.ts` - replays overridden mock thread state after CTA interactions during browser validation.

## Decisions Made

- Pre-compute approval is a separate execution gate, not a lighter version of scientific review.
- The active submarine workbench needs the same calculation-plan semantics as the reusable runtime panel, so pipeline cards and top-line status had to be updated alongside the detailed panel.

## Deviations from Plan

### Auto-fixed Issues

**1. [UI Coverage Gap] Pipeline and stage-card surfaces were only partially aware of the new calculation-plan gate**

- **Found during:** resumed frontend verification and code inspection
- **Issue:** The initial frontend changes compiled, but `submarine-pipeline.tsx`, `submarine-pipeline-status.ts`, `submarine-pipeline-runs.ts`, and the active stage cards were not fully aligned on pending approval vs immediate clarification semantics.
- **Fix:** Finished the pipeline/status/run-list wiring, added explicit solver-hold and geometry-review UI, and expanded the focused frontend tests.
- **Verification:** `node --test src/components/workspace/submarine-confirmation-actions.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-shell.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-pipeline-runs.test.ts && corepack pnpm typecheck`

**2. [Mock Validation Blocker] Phase 4 review CTAs hit a missing mock stream endpoint during browser validation**

- **Found during:** MCP browser validation on `submarine-phase4-review-demo`
- **Issue:** Clicking the calculation-plan confirmation CTAs posted to `/mock/api/threads/.../runs/stream`, which returned `404` and pushed the workbench into a failed lead-agent state.
- **Fix:** Added a deterministic mock `runs/stream` route, shared mock-thread override storage, and a focused test so clarify, approve, and rerun actions stay inside the workbench during browser validation.
- **Verification:** `node --test src/app/mock/api/threads/mock-thread-store.test.ts && corepack pnpm typecheck`, plus live browser validation confirming `runs/stream` returned `200` for all three CTA paths.

---

**Total deviations:** 2 auto-fixed (frontend semantics alignment and mock CTA validation support)
**Impact on plan:** Necessary to make the new calculation-plan approval gate consistent on the real workbench and verifiable end-to-end in deterministic browser validation.

## Issues Encountered

- The frontend contract work was already partially in place, but the live pipeline/status/stage-card semantics needed a final consistency pass to avoid mixed messaging.
- Initial browser validation exposed a missing mock `runs/stream` endpoint for Phase 4 confirmation CTAs; this was fixed inline before final validation was recorded.

## User Setup Required

None.

## Next Phase Readiness

- Phase 4 is now fully complete: geometry trust, case provenance, researcher approval, and the related browser-validated CTA flows all feed one explicit pre-compute setup contract.
- The next logical GSD step is planning/executing Phase 5 to build experiment provenance, baseline-vs-variant reproducibility, and environment consistency on top of the stronger setup semantics.

---
*Phase: 04-geometry-and-case-intelligence-hardening*
*Completed: 2026-04-02*
