---
phase: 06-research-delivery-workbench
plan: 02
subsystem: review-workbench
tags: [submarine, supervisor-review, decision-summary, chat-driven, cockpit]
requires:
  - phase: 06-01
    provides: shared conclusion-first report/runtime surfaces that the supervisor review state now extends
provides:
  - Structured delivery-decision summaries mapped from scientific gate and remediation state
  - Runtime preservation of `decision_status` plus chat-ready next-step options
  - Lightweight cockpit review surfaces that keep next-step choice in chat instead of adding buttons
affects: [phase-06-research-delivery-workbench, scientific-followup, supervisor-review]
tech-stack:
  added: []
  patterns:
    - "Represent operator-facing next-step choice as a separate decision contract instead of overloading scientific gate truth."
    - "Keep workbench review UI lightweight by surfacing options and artifacts while routing the actual choice back to chat."
key-files:
  created:
    - .planning/phases/06-research-delivery-workbench/06-02-SUMMARY.md
  modified:
    - backend/packages/harness/deerflow/domain/submarine/contracts.py
    - backend/packages/harness/deerflow/domain/submarine/reporting.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py
    - backend/tests/test_submarine_result_report_tool.py
    - frontend/src/components/workspace/submarine-runtime-panel.contract.ts
    - frontend/src/components/workspace/submarine-runtime-panel.utils.ts
    - frontend/src/components/workspace/submarine-runtime-panel.tsx
    - frontend/src/components/workspace/submarine-stage-cards.tsx
    - frontend/src/components/workspace/submarine-pipeline.tsx
    - frontend/src/components/workspace/submarine-pipeline-status.ts
    - frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
    - frontend/src/components/workspace/submarine-pipeline-status.test.ts
key-decisions:
  - "The decision vocabulary is exactly `ready_for_user_decision`, `needs_more_evidence`, and `blocked_by_setup`."
  - "Delivery-decision options map directly onto `finish_task`, `add_evidence`, `fix_setup`, and `extend_study` with explicit follow-up kinds."
  - "Supervisor review and pipeline status must say `请在聊天中确认下一步。` instead of exposing approve/rerun buttons."
patterns-established:
  - "Preserve scientific truth (`review_status`, `scientific_gate_status`, `allowed_claim_level`) alongside a separate operator-facing `decision_status`."
  - "Thread one exact delivery-decision contract through backend payloads, runtime snapshots, cockpit cards, and pipeline status copy."
requirements-completed: [RPT-02]
duration: "~35 min including test backfill, UI wiring, and syntax repair"
completed: 2026-04-03
---

# Phase 6: Research Delivery Workbench Plan 02 Summary

**Supervisor review now emits a structured chat-driven decision contract that surfaces next-step options in the cockpit without collapsing into an approve/rerun control panel.**

## Performance

- **Duration:** ~35 min including test backfill, UI wiring, and syntax repair
- **Started:** 2026-04-03T00:05:00+08:00
- **Completed:** 2026-04-03T00:24:00+08:00
- **Tasks:** 3 planned decision-surface tasks
- **Files modified:** 12 implementation files

## Accomplishments

- Added backend decision-contract types plus report-generation logic that deterministically maps `blocked`, `claim_limited`, and `ready_for_claim` into chat-ready next-step choices.
- Preserved `decision_status` and `delivery_decision_summary` in runtime state so the cockpit can render honest scientific truth and operator-facing next-step context side by side.
- Replaced direct supervisor-review action buttons with lightweight “continue in chat” surfaces in the stage cards, runtime panel, pipeline status, and pipeline wiring.
- Backfilled frontend and backend tests for blocked, evidence-gap, and ready-for-decision review states to lock the shared contract.

## Verification

- `cd backend && uv run pytest tests/test_submarine_result_report_tool.py`
  - Result: passed (`27 passed`)
- `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-status.test.ts`
  - Result: passed (`57 passed`)
- `cd frontend && corepack pnpm typecheck`
  - Result: passed

## Task Commits

- Pending integration commit during phase closeout.

## Files Created/Modified

- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - defines delivery-decision status, option, and summary types.
- `backend/packages/harness/deerflow/domain/submarine/reporting.py` - maps scientific gate/remediation truth into structured chat-driven delivery decisions.
- `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py` - persists delivery decision state in runtime snapshots.
- `backend/tests/test_submarine_result_report_tool.py` - locks blocked, claim-limited, and ready-for-claim decision mappings.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - adds decision summary payload fields.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts` - formats decision status, options, and follow-up labels for the cockpit.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx` - renders the full decision summary block with option cards and linked artifacts.
- `frontend/src/components/workspace/submarine-stage-cards.tsx` - swaps action buttons for a lightweight “Continue in Chat” review block.
- `frontend/src/components/workspace/submarine-pipeline.tsx` - threads `decision_status` into pipeline-status calculation.
- `frontend/src/components/workspace/submarine-pipeline-status.ts` - prioritizes delivery-decision completion copy before scientific-gate fallback wording.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts` - locks decision-summary parsing.
- `frontend/src/components/workspace/submarine-pipeline-status.test.ts` - locks blocked/evidence-gap/ready decision copy.

## Decisions Made

- The cockpit should display plausible next-step choices, but the final human decision stays in the main chat thread.
- `fix_setup` is the only option for blocked-by-setup states; evidence-gap and ready states expose broader menus.
- Pipeline completion copy should prefer explicit delivery-decision wording over generic scientific-gate wording when both are present.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Rebuilt `submarine-pipeline-status.ts` from a clean base after partial edit corruption**
- **Found during:** Final frontend verification
- **Issue:** The in-progress `decisionStatus` edits left multiple broken string literals and one incomplete ternary branch, causing `node --test` to fail on TypeScript parsing.
- **Fix:** Reapplied the intended `decisionStatus` changes onto the last committed clean version of `submarine-pipeline-status.ts`, then restored the lightweight chat-driven status branches and reran tests.
- **Files modified:** `frontend/src/components/workspace/submarine-pipeline-status.ts`, `frontend/src/components/workspace/submarine-pipeline-status.test.ts`
- **Verification:** `node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-status.test.ts` and `corepack pnpm typecheck`

---

**Total deviations:** 1 auto-fixed (1 blocking syntax regression)
**Impact on plan:** The repair was necessary to restore frontend verification without changing the intended lightweight decision behavior.

## Issues Encountered

- `submarine-stage-cards.tsx` also contained one incomplete ternary after the button-removal refactor; fixing that close-out issue was required for `pnpm typecheck` to pass.

## User Setup Required

None.

## Next Phase Readiness

- Phase 06-03 can now consume the exact `followup_kind` values already attached to delivery-decision options.
- The cockpit and runtime state are ready to show why follow-up continues, not just that a rerun happened.

---
*Phase: 06-research-delivery-workbench*
*Completed: 2026-04-03*
