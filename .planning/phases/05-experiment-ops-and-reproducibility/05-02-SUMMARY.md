---
phase: 05-experiment-ops-and-reproducibility
plan: 02
subsystem: experiment-registry
tags: [submarine, experiments, custom-variants, reporting, cockpit]
requires:
  - phase: 05-01
    provides: canonical provenance manifests and reducer-safe runtime provenance pointers
provides:
  - Unified experiment registry coverage for baseline, scientific-study, and declared custom variants
  - Linkage and reporting summaries that distinguish strict scientific-study gaps from custom-variant coverage
  - Existing cockpit views that render baseline-to-custom lineage without adding a new route
affects: [phase-05-experiment-ops-and-reproducibility, phase-06-research-delivery-workbench]
tech-stack:
  added: []
  patterns:
    - "Use `custom:` run ids and `custom_variant` roles so user-authored variants stay inside the same experiment manifest as baseline and scientific-study runs."
    - "Render lineage from compare metadata such as `variant_origin`, `variant_label`, and `compare_target_run_id` instead of guessing from scientific-study ids."
key-files:
  created:
    - .planning/phases/05-experiment-ops-and-reproducibility/05-02-SUMMARY.md
  modified:
    - backend/packages/harness/deerflow/domain/submarine/models.py
    - backend/packages/harness/deerflow/domain/submarine/contracts.py
    - backend/packages/harness/deerflow/domain/submarine/experiments.py
    - backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py
    - backend/packages/harness/deerflow/domain/submarine/experiment_linkage.py
    - backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py
    - backend/packages/harness/deerflow/domain/submarine/reporting_render.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py
    - backend/tests/test_submarine_experiment_linkage_contracts.py
    - backend/tests/test_submarine_result_report_tool.py
    - frontend/src/components/workspace/submarine-runtime-panel.contract.ts
    - frontend/src/components/workspace/submarine-runtime-panel.utils.ts
    - frontend/src/components/workspace/submarine-runtime-panel.tsx
    - frontend/src/components/workspace/submarine-pipeline-runs.ts
    - frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
    - frontend/src/components/workspace/submarine-pipeline-runs.test.ts
key-decisions:
  - "Declared custom variants must register into the same experiment manifest as baseline and deterministic scientific-study variants instead of remaining out-of-band notes."
  - "Linkage assessment stays strict for planned scientific-study variants, while custom-variant gaps are tracked through compare coverage and unknown-registry warnings."
  - "The existing runtime panel and compare views were extended in place so one experiment boundary remains readable across baseline, built-in studies, and custom variants."
patterns-established:
  - "Custom-variant coverage is summarized separately from deterministic study coverage, but both travel through one experiment summary contract."
  - "Report and UI layers share the same `custom / {variant_id}` and `Custom Variant | {variant_label}` lineage vocabulary."
requirements-completed: [OPS-02]
duration: "~55 min across existing Task 1 commit, local integration, verification, and documentation"
completed: 2026-04-02
---

# Phase 5: Experiment Ops and Reproducibility Plan 02 Summary

**One experiment registry now carries baseline, scientific-study variants, and declared custom variants through linkage checks, reporting, and cockpit lineage views.**

## Performance

- **Duration:** ~55 min
- **Started:** 2026-04-02T17:56:00+08:00
- **Completed:** 2026-04-02T18:51:21+08:00
- **Tasks:** 3 planned experiment-lineage tasks
- **Files modified:** 16

## Accomplishments

- Extended the experiment registry contract so custom variants are first-class run records with `custom:` ids, compare targets, baseline references, labels, and parameter overrides.
- Tightened linkage assessment so planned scientific-study variants still fail loudly when run records or compare entries are missing, while declared custom variants are tracked as valid members with their own pending/completed coverage summaries.
- Carried the new custom-variant fields through reporting summaries, markdown/html rendering, runtime-panel contracts, and existing cockpit views so baseline-to-custom lineage remains readable without a separate experiment screen.
- Added focused regression coverage for custom compare labels and updated the result-report fixture that had relied on an under-specified study manifest.

## Verification

- `cd backend && uv run pytest tests/test_submarine_experiment_linkage_contracts.py tests/test_submarine_result_report_tool.py`
  - Result: passed (`30 passed`)
- `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-runs.test.ts`
  - Result: passed (`44 passed`)
- `cd frontend && corepack pnpm typecheck`
  - Result: passed

## Task Commits

1. **Task 1: Extend the experiment registry contract to support declared custom variants** - `e0fd369` (`feat(05-02): register declared custom experiment variants`)
2. **Tasks 2-3: Surface custom variant linkage through summaries, reporting, and cockpit views** - `b91a966` (`feat(05-02): surface custom experiment lineage`)

## Files Created/Modified

- `backend/packages/harness/deerflow/domain/submarine/models.py` - extends experiment run records with custom-variant lineage metadata.
- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - carries custom variant payloads in runtime-facing contracts.
- `backend/packages/harness/deerflow/domain/submarine/experiments.py` - reserves the `custom:` run-id namespace for user-authored variants.
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` - registers declared custom variants into the experiment manifest before execution.
- `backend/packages/harness/deerflow/domain/submarine/experiment_linkage.py` - separates expected scientific variants, registered custom variants, and unknown extras for stricter assessment.
- `backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py` - emits workflow detail and compare notes that explain custom coverage explicitly.
- `backend/packages/harness/deerflow/domain/submarine/reporting_render.py` - renders custom coverage and `compare_target` details in markdown/html reports.
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py` - threads `custom_variants` through tool input, runtime state, and dispatch payloads.
- `backend/tests/test_submarine_experiment_linkage_contracts.py` - locks `custom:` registry behavior and linkage acceptance for declared custom variants.
- `backend/tests/test_submarine_result_report_tool.py` - locks custom-coverage reporting and fixes the study fixture to match the stricter manifest contract.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - expands payload contracts with custom variant and compare-lineage fields.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts` - formats custom compare labels and summary lists with shared lineage vocabulary.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx` - shows custom lineage and compare-target details in the existing experiment section.
- `frontend/src/components/workspace/submarine-pipeline-runs.ts` - formats sidebar lineage labels for baseline-to-custom runs.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts` - covers custom summary fields plus `Custom Variant` / `custom / {variant_id}` labels.
- `frontend/src/components/workspace/submarine-pipeline-runs.test.ts` - covers baseline-to-custom lineage rendering in the run list.

## Decisions Made

- Custom variants should be visible as experiment members from registration time onward so reporting and follow-up logic do not have to reconcile a second ad-hoc tracking channel.
- Compare labels must use explicit metadata rather than scientific-study assumptions because custom variants can target baseline or future non-baseline compare chains.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Result-report fixture needed an explicit study definition**
- **Found during:** Task 2 (reporting and result-report verification)
- **Issue:** One research-ready fixture left `study_definitions` empty, which no longer matched the stricter registry contract after custom variants became first-class manifest members.
- **Fix:** Added the coarse mesh study definition directly to the fixture so report generation reflects a valid declared study manifest.
- **Files modified:** `backend/tests/test_submarine_result_report_tool.py`
- **Verification:** `uv run pytest tests/test_submarine_experiment_linkage_contracts.py tests/test_submarine_result_report_tool.py`
- **Committed in:** `b91a966`

**2. [Rule 2 - Missing Critical] Report rendering needed the same custom lineage vocabulary as summaries**
- **Found during:** Task 2 (reporting summary integration)
- **Issue:** The plan referenced `reporting.py`, but the actual markdown/html output path flows through `reporting_render.py`, which would have continued to hide custom coverage details.
- **Fix:** Extended `reporting_render.py` to show custom coverage fields and `compare_target` labels alongside the summary-layer changes.
- **Files modified:** `backend/packages/harness/deerflow/domain/submarine/reporting_render.py`
- **Verification:** `uv run pytest tests/test_submarine_experiment_linkage_contracts.py tests/test_submarine_result_report_tool.py`
- **Committed in:** `b91a966`

---

**Total deviations:** 2 auto-fixed (1 blocking fixture alignment, 1 missing-critical report rendering gap)
**Impact on plan:** Both fixes were necessary to keep the stricter registry contract visible and testable. No scope creep beyond required custom-variant readability.

## Issues Encountered

- The interrupted session had already landed Task 1 as commit `e0fd369`, so completion work focused on confirming branch state, finishing the remaining linkage/reporting/UI layers, and preserving clean checkpoint boundaries.
- The plan's manual cockpit verification was not run in a browser session during this checkpoint; automated contract, formatter, and typecheck coverage passed for the affected experiment views.

## User Setup Required

None.

## Next Phase Readiness

- Phase 05-02 is complete: baseline, deterministic study variants, and custom variants now share one experiment boundary across manifests, summaries, and cockpit views.
- Phase 05-03 can build on the new provenance plus experiment lineage contracts to record environment fingerprints, parity drift, and reproducibility guidance without redesigning the reporting surfaces.

---
*Phase: 05-experiment-ops-and-reproducibility*
*Completed: 2026-04-02*
