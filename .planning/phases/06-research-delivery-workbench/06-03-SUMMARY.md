---
phase: 06-research-delivery-workbench
plan: 03
subsystem: followup
tags: [submarine, followup, lineage, provenance, cockpit]
requires:
  - phase: 06-01
    provides: conclusion-first report artifacts and provenance anchors that follow-up history now references
  - phase: 06-02
    provides: chat-driven delivery decisions and `followup_kind` vocabulary consumed by bounded follow-up execution
provides:
  - Follow-up history entries with decision reason, trigger ids, provenance lineage, and task-completion state
  - A bounded `task_complete` path that records user-confirmed closure without triggering reruns
  - Cockpit follow-up summaries that show the latest decision and refreshed report/provenance anchor
affects: [phase-06-research-delivery-workbench, verify-work, milestone-audit]
tech-stack:
  added: []
  patterns:
    - "Record follow-up decisions as explicit lineage metadata rather than inferring intent from timestamps or notes."
    - "Bound follow-up to one user-confirmed step: either task completion or one rerun-plus-report refresh."
key-files:
  created:
    - .planning/phases/06-research-delivery-workbench/06-03-SUMMARY.md
  modified:
    - backend/packages/harness/deerflow/domain/submarine/contracts.py
    - backend/packages/harness/deerflow/domain/submarine/followup.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py
    - backend/tests/test_submarine_result_report_tool.py
    - backend/tests/test_submarine_scientific_followup_tool.py
    - frontend/src/components/workspace/submarine-runtime-panel.contract.ts
    - frontend/src/components/workspace/submarine-runtime-panel.utils.ts
    - frontend/src/components/workspace/submarine-runtime-panel.tsx
    - frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
key-decisions:
  - "Follow-up history now records `followup_kind`, `decision_summary_zh`, trigger ids, and refreshed provenance so reviewers can see intent and lineage together."
  - "A `task_complete` follow-up records closure immediately and does not dispatch solver reruns or report refreshes."
  - "Latest evidence anchor in the cockpit should show report path and provenance manifest path together."
patterns-established:
  - "Default `task_completion_status` to `completed` for `task_complete`, `continued` for explicit follow-up kinds, and `unknown` otherwise."
  - "Expose latest follow-up kind, decision summary, trigger ids, and provenance anchor through one compact `scientific_followup_summary` payload."
requirements-completed: [RPT-02]
duration: "~20 min for history/tool lineage extension and cockpit integration"
completed: 2026-04-03
---

# Phase 6: Research Delivery Workbench Plan 03 Summary

**Scientific follow-up history now records why the user continued or stopped, which conclusion/evidence gaps triggered that choice, and which refreshed report/provenance pair became the latest evidence anchor.**

## Performance

- **Duration:** ~20 min for history/tool lineage extension and cockpit integration
- **Started:** 2026-04-03T00:24:00+08:00
- **Completed:** 2026-04-03T00:43:28+08:00
- **Tasks:** 3 planned follow-up lineage tasks
- **Files modified:** 9 implementation files

## Accomplishments

- Expanded `scientific-followup-history.json` entries with follow-up kind, Chinese decision summary, triggering conclusion ids, triggering evidence-gap ids, refreshed provenance-manifest path, and task-completion state.
- Extended `submarine_scientific_followup` with optional decision metadata and a bounded `task_complete` path that records user-confirmed closure without executing a rerun or report refresh.
- Preserved refreshed report/provenance lineage for rerun flows and surfaced the latest follow-up kind, decision context, trigger ids, and evidence anchor in the cockpit runtime panel.
- Locked the richer history/report contract in backend tests and the cockpit summary parsing in frontend tests.

## Verification

- `cd backend && uv run pytest tests/test_submarine_scientific_followup_tool.py tests/test_submarine_result_report_tool.py`
  - Result: passed (`36 passed`)
- `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - Result: passed (`44 passed`)
- `cd frontend && corepack pnpm typecheck`
  - Result: passed

## Task Commits

- Pending integration commit during phase closeout.

## Files Created/Modified

- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - documents follow-up task-completion vocabulary alongside the existing follow-up-kind types.
- `backend/packages/harness/deerflow/domain/submarine/followup.py` - normalizes richer history entries and exposes latest decision/provenance fields in `scientific_followup_summary`.
- `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py` - records decision metadata across all branches and adds the bounded `task_complete` path.
- `backend/tests/test_submarine_scientific_followup_tool.py` - locks task-complete no-rerun behavior and refreshed provenance-manifest capture.
- `backend/tests/test_submarine_result_report_tool.py` - locks the richer follow-up summary fields emitted through result reporting.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - extends the shared follow-up summary payload with latest decision and provenance-lineage fields.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts` - formats latest follow-up kind labels and exposes decision/trigger/provenance fields to the UI.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx` - renders latest decision context, trigger ids, and refreshed evidence anchor using existing artifact-link UI.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts` - locks parsing of the richer follow-up summary contract.

## Decisions Made

- Follow-up lineage should point to the refreshed provenance manifest explicitly instead of expecting reviewers to infer it from `artifact_virtual_paths`.
- `task_complete` is a first-class bounded follow-up outcome, not a special case outside the follow-up history artifact.
- Existing `reporting.py` and `submarine_result_report_tool.py` history-loading/runtime-pointer plumbing was already sufficient once the richer history artifact existed, so no additional code change there was required.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Safe Simplification] Reused existing result-report history plumbing instead of adding redundant report-tool changes**
- **Found during:** Task 2/3 integration review
- **Issue:** The plan’s initial file list included `reporting.py` and `submarine_result_report_tool.py`, but inspection showed they already loaded `scientific_followup_history_virtual_path`, rebuilt `scientific_followup_summary`, and preserved the runtime pointer correctly.
- **Fix:** Kept the planned verification coverage on those surfaces but concentrated implementation changes in `followup.py`, `submarine_scientific_followup_tool.py`, and the frontend follow-up readers.
- **Files modified:** `backend/packages/harness/deerflow/domain/submarine/followup.py`, `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`, `backend/tests/test_submarine_result_report_tool.py`
- **Verification:** `uv run pytest tests/test_submarine_scientific_followup_tool.py tests/test_submarine_result_report_tool.py`

---

**Total deviations:** 1 auto-fixed (1 safe simplification of planned touch points)
**Impact on plan:** No behavior loss. The same bounded lineage outcome shipped with less redundant churn in already-correct report/runtime code.

## Issues Encountered

- None beyond routine contract synchronization; backend and frontend both accepted the richer follow-up shape on the first verification pass.

## User Setup Required

None.

## Next Phase Readiness

- Phase 06 is now documented end-to-end across report packaging, chat-driven review decisions, and bounded follow-up lineage.
- The next workflow step can move to phase closeout, verification audit, or milestone audit without reconstructing phase-06 intent from raw diffs.

---
*Phase: 06-research-delivery-workbench*
*Completed: 2026-04-03*
