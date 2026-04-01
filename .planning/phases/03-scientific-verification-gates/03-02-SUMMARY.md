---
phase: 03-scientific-verification-gates
plan: 02
subsystem: sensitivity-study-workflows
tags: [submarine, scientific-verification, sensitivity-studies, experiment-linkage, frontend, browser-validation]
requires:
  - phase: 03-01
    provides: "Structured stability evidence and dispatch-time scientific gate status"
provides:
  - "Explicit mesh/domain/time-step study workflow states with deterministic planned, in-progress, completed, and blocked coverage"
  - "Final report summaries that preserve experiment linkage gaps and compare follow-up instead of silently treating missing variants as optional"
  - "Live submarine pipeline visibility for Experiment Registry, Experiment Compare, and Scientific Studies on the actual workbench page"
affects: [phase-03-scientific-verification-gates, phase-05-experiment-ops-and-reproducibility, phase-06-research-delivery-workbench]
tech-stack:
  added: []
  patterns:
    - "Use backend-authored study and experiment workflow summaries as the single source of truth for reports, demo fixtures, and the active pipeline UI."
    - "Represent unfinished verification work as explicit claim-limiting evidence instead of inferring status from missing files."
key-files:
  created:
    - .planning/phases/03-scientific-verification-gates/03-02-SUMMARY.md
  modified:
    - backend/packages/harness/deerflow/domain/submarine/evidence.py
    - backend/packages/harness/deerflow/domain/submarine/experiment_linkage.py
    - backend/packages/harness/deerflow/domain/submarine/experiments.py
    - backend/packages/harness/deerflow/domain/submarine/models.py
    - backend/packages/harness/deerflow/domain/submarine/reporting_render.py
    - backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py
    - backend/packages/harness/deerflow/domain/submarine/runtime_plan.py
    - backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py
    - backend/packages/harness/deerflow/domain/submarine/studies.py
    - backend/tests/test_submarine_experiment_linkage_contracts.py
    - backend/tests/test_submarine_result_report_tool.py
    - backend/tests/test_submarine_solver_dispatch_tool.py
    - frontend/public/demo/threads/54c9fbd7-38f0-49df-b015-4c0e20d568f8/user-data/outputs/submarine/reports/live-forces-suboff/final-report.json
    - frontend/public/demo/threads/submarine-cfd-demo/user-data/outputs/submarine/reports/live-forces-suboff/final-report.json
    - frontend/src/components/workspace/submarine-runtime-panel.contract.ts
    - frontend/src/components/workspace/submarine-runtime-panel.tsx
    - frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
    - frontend/src/components/workspace/submarine-runtime-panel.utils.ts
    - frontend/src/components/workspace/submarine-stage-cards.tsx
key-decisions:
  - "Pure plan-only study state stays `planned`; `partial` only appears once baseline-linked execution or follow-up gaps are explicit."
  - "The actual researcher-facing workbench is `submarine-pipeline.tsx`, so SCI-02 visibility had to be wired into `submarine-stage-cards.tsx` rather than the inactive runtime panel alone."
  - "Mock demo reports should carry representative completed/partial/blocked study payloads so MCP browser validation remains deterministic."
patterns-established:
  - "Keep experiment linkage, compare coverage, and study workflow wording aligned across backend summaries and the active UI."
  - "Validate frontend contract work against the page the researcher actually uses, not only against helper components."
requirements-completed: [SCI-02]
duration: "~3h"
completed: 2026-04-02
---

# Phase 3: Scientific Verification Gates Plan 02 Summary

**SCI-02 sensitivity-study workflows are now explicit, claim-limiting, and visible on the real submarine workbench instead of being latent backend artifacts or unused UI contract data.**

## Performance

- **Duration:** ~3 h across multiple execution passes
- **Completed:** 2026-04-02T00:56:14+08:00
- **Tasks:** 3 planned sensitivity-study workflow tasks
- **Files modified:** 20

## Accomplishments

- Hardened study workflow semantics so plan-only variants remain `planned`, while baseline-complete but follow-up-pending studies become explicit `partial` or `in_progress` workflow states.
- Strengthened experiment linkage and reporting summaries so missing run records, compare entries, blocked variants, and missing metrics are preserved as structured claim-limiting evidence.
- Expanded final report rendering to surface `experiment_summary`, `experiment_compare_summary`, and `scientific_study_summary` in markdown/html/json outputs.
- Extended shared frontend summary builders and contract types for experiment registry, compare coverage, and per-study workflow detail.
- Wired those SCI-02 summaries into the actual researcher-facing `ResultReportingCard` in `submarine-stage-cards.tsx` after MCP validation showed the previously updated `submarine-runtime-panel.tsx` is not mounted on the active workbench.
- Enriched the mock demo final reports so browser validation can deterministically exercise completed, partial, blocked, and missing-metrics study states.

## Verification

- `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_experiment_linkage_contracts.py tests/test_submarine_result_report_tool.py`
  - Result: passed (`55 passed`)
- `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - Result: passed (`37 passed`)
- `cd frontend && corepack pnpm typecheck`
  - Result: passed
- Browser validation
  - Reloaded [mock submarine thread](http://localhost:3000/workspace/submarine/54c9fbd7-38f0-49df-b015-4c0e20d568f8?mock=true) after restarting the local Next dev server from the current workspace.
  - Confirmed the active `Result Reporting` stage renders `Experiment Registry`, `Experiment Compare`, and `Scientific Studies`.
  - Confirmed the page shows explicit `Completed`, `In Progress`, `Planned`, `Blocked`, and `Missing Evidence` workflow copy for representative mesh/domain/time-step follow-up states.

## Task Commits

This plan was executed in one workspace branch with final browser validation, planning-state updates, and a single end-of-plan commit.

## Files Created/Modified

- `backend/packages/harness/deerflow/domain/submarine/studies.py` - refines study workflow semantics and deterministic variant execution metadata.
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` - preserves study-manifest and experiment linkage workflow truth in runtime/report artifacts.
- `backend/packages/harness/deerflow/domain/submarine/experiments.py` - strengthens baseline-vs-variant linkage and compare packaging.
- `backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py` - builds explicit study, experiment, and compare summary payloads for SCI-02.
- `backend/packages/harness/deerflow/domain/submarine/reporting_render.py` - renders the new SCI-02 workflow summaries into markdown/html reports.
- `backend/packages/harness/deerflow/domain/submarine/runtime_plan.py` - maps study and compare workflow status into execution-plan visibility.
- `backend/packages/harness/deerflow/domain/submarine/evidence.py` - consumes the stronger summary payloads for downstream evidence interpretation.
- `backend/tests/test_submarine_solver_dispatch_tool.py` - locks pending/partial study workflow packaging.
- `backend/tests/test_submarine_experiment_linkage_contracts.py` - locks incomplete and completed linkage/report generation states.
- `backend/tests/test_submarine_result_report_tool.py` - locks SCI-02 final report payload and render behavior.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - extends report payload typing for study and compare workflow summaries.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts` - builds frontend view models for experiment registry, compare coverage, and scientific studies.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx` - adds rich SCI-02 rendering for the reusable runtime panel surface.
- `frontend/src/components/workspace/submarine-stage-cards.tsx` - bridges those same SCI-02 summaries into the actual `ResultReportingCard` used on the live workbench.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts` - locks the SCI-02 summary builders.
- `frontend/public/demo/threads/submarine-cfd-demo/.../final-report.json` - adds deterministic mock SCI-02 workflow payloads.
- `frontend/public/demo/threads/54c9fbd7-38f0-49df-b015-4c0e20d568f8/.../final-report.json` - mirrors the same mock SCI-02 workflow payloads for browser validation.

## Decisions Made

- Study execution status and study workflow status remain distinct: a report can show completed mesh evidence while domain/time-step workflows are still partial or blocked.
- The active pipeline stage card must surface SCI-02 summary truth directly; updating an unused helper component is not sufficient for researcher-facing verification.
- Deterministic mock final reports are part of the validation strategy because they let us verify edge states before a fresh live SCI-02 run exists end to end.

## Deviations from Plan

### Auto-fixed Issues

**1. [UI Surface Mismatch] SCI-02 was wired into an unused component first**

- **Found during:** MCP browser validation
- **Issue:** The updated `submarine-runtime-panel.tsx` was not the component mounted on the active submarine workbench page, so the new summaries never reached researchers.
- **Fix:** Reused the same summary builders inside `frontend/src/components/workspace/submarine-stage-cards.tsx` and exposed SCI-02 workflow panels inside the live `ResultReportingCard`.
- **Verification:** Browser validation on `/workspace/submarine/54c9fbd7-38f0-49df-b015-4c0e20d568f8?mock=true`

**2. [Fixture Gap] Existing mock reports could not exercise the new workflow sections**

- **Found during:** MCP browser validation
- **Issue:** The shipped mock `final-report.json` files had no `experiment_summary`, `experiment_compare_summary`, or `scientific_study_summary`, so the new UI had nothing representative to render.
- **Fix:** Enriched both mock report fixtures with explicit completed/partial/blocked study and compare payloads.
- **Verification:** Browser DOM snapshot showed all three SCI-02 sections with expected statuses and follow-up lines.

---

**Total deviations:** 2 auto-fixed (1 UI-surface mismatch, 1 fixture gap)
**Impact on plan:** These fixes were necessary to make SCI-02 researcher-visible on the real page and to close the browser-validation loop promised by the plan.

## Issues Encountered

- The active submarine workbench had diverged from the reusable runtime panel, so UI verification initially produced a false negative even though the JSON contract was correct.
- Existing mock report fixtures represented only baseline reporting and needed richer study payloads before browser validation could cover partial or blocked verification states.

## User Setup Required

None for the committed phase outputs. A future non-mock validation pass will need a freshly generated live SCI-02 thread once benchmark and full follow-up execution paths are available.

## Next Phase Readiness

- Plan `03-02` is complete: sensitivity studies are explicit workflow objects, their claim-limiting gaps survive reporting, and the active workbench surfaces them clearly.
- The next logical GSD step is executing `03-03` to connect benchmark-backed comparison logic to the same scientific claim-level contract.
- Phase 5 can now build richer experiment-ops and provenance features on top of stable experiment/study summary artifacts rather than inventing a second workflow vocabulary.

---
*Phase: 03-scientific-verification-gates*
*Completed: 2026-04-02*
