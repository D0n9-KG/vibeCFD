---
phase: 03-scientific-verification-gates
plan: 03
subsystem: benchmark-validation
tags: [submarine, scientific-verification, benchmark-validation, scientific-gates, frontend, browser-validation]
requires:
  - phase: 03-01
    provides: "Structured stability evidence and dispatch-time scientific gate status"
  - phase: 03-02
    provides: "Study/provenance workflow summaries that can participate in final claim-level decisions"
provides:
  - "Benchmark comparison becomes explicit scientific evidence with tolerance, velocity, and citation metadata"
  - "Research evidence and supervisor gate now preserve benchmark-driven limited-or-blocked claim narratives"
  - "Active submarine workbench mock threads now exercise SCI-03 claim-gate UI in deterministic browser validation"
affects: [phase-04-geometry-and-case-intelligence-hardening, phase-05-experiment-ops-and-reproducibility, phase-06-research-delivery-workbench]
tech-stack:
  added: []
  patterns:
    - "Represent unavailable or mismatched benchmark references as explicit `not_applicable` evidence instead of silently dropping validation context."
    - "Keep backend report payloads, runtime snapshot gate state, and active workbench cards aligned on the same scientific claim contract."
key-files:
  created:
    - .planning/phases/03-scientific-verification-gates/03-03-SUMMARY.md
  modified:
    - backend/packages/harness/deerflow/domain/submarine/evidence.py
    - backend/packages/harness/deerflow/domain/submarine/reporting.py
    - backend/packages/harness/deerflow/domain/submarine/reporting_acceptance.py
    - backend/packages/harness/deerflow/domain/submarine/supervision.py
    - backend/tests/test_submarine_result_report_tool.py
    - frontend/public/demo/threads/54c9fbd7-38f0-49df-b015-4c0e20d568f8/thread.json
    - frontend/public/demo/threads/54c9fbd7-38f0-49df-b015-4c0e20d568f8/user-data/outputs/submarine/reports/live-forces-suboff/final-report.json
    - frontend/public/demo/threads/submarine-cfd-demo/thread.json
    - frontend/public/demo/threads/submarine-cfd-demo/user-data/outputs/submarine/reports/live-forces-suboff/final-report.json
    - frontend/src/components/workspace/submarine-pipeline.tsx
    - frontend/src/components/workspace/submarine-runtime-panel.contract.ts
    - frontend/src/components/workspace/submarine-runtime-panel.tsx
    - frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
    - frontend/src/components/workspace/submarine-runtime-panel.utils.ts
    - frontend/src/components/workspace/submarine-stage-cards.tsx
key-decisions:
  - "Benchmark mismatches must remain visible as claim-limiting evidence, not disappear when a reference is unavailable for the current run condition."
  - "SCI-03 is not done until deterministic mock threads exercise the real workbench claim-gate surfaces in browser validation."
patterns-established:
  - "Drive claim-level copy from backend-authored `research_evidence_summary` and `scientific_supervisor_gate` payloads."
  - "Mirror top-level `scientific_gate_status` and `allowed_claim_level` into runtime snapshots so refresh-safe fallbacks stay intelligible."
requirements-completed: [SCI-03]
duration: "~1.5h"
completed: 2026-04-02
---

# Phase 3: Scientific Verification Gates Plan 03 Summary

**Benchmark-backed claim gating is now explicit, citation-aware, and visible in both the final report payload and the real submarine workbench review surfaces.**

## Performance

- **Duration:** ~1.5 h across backend synthesis, frontend claim-gate wiring, mock refresh, and browser validation
- **Completed:** 2026-04-02T01:41:55+08:00
- **Tasks:** 3 planned SCI-03 tasks
- **Files modified:** 15

## Accomplishments

- Promoted benchmark comparison into a first-class evidence artifact with tolerance, velocity, source label, and source URL metadata.
- Hardened research-evidence and supervisor-gate synthesis so benchmark pass, fail, and not-applicable states produce explicit claim-level consequences.
- Surfaced those benchmark-driven claim consequences in the active `Result Reporting` and `Supervisor Review` workbench cards.
- Refreshed both mock submarine demo threads so MCP browser validation can deterministically render SCI-03 sections on the real page.

## Verification

- `cd backend && uv run pytest tests/test_submarine_result_report_tool.py`
  - Result: passed
- `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - Result: passed
- `cd frontend && corepack pnpm typecheck`
  - Result: passed
- Browser validation
  - Reloaded [mock submarine thread](http://localhost:3000/workspace/submarine/submarine-cfd-demo?mock=true) and [mock submarine thread](http://localhost:3000/workspace/submarine/54c9fbd7-38f0-49df-b015-4c0e20d568f8?mock=true).
  - Confirmed `Result Reporting` renders `Scientific Claim Gate`, `Research Evidence`, and `Benchmark Comparisons`.
  - Confirmed `Supervisor Review` renders `Supervisor Claim Gate` and a research-evidence snapshot with the same claim-limited narrative.

## Task Commits

This plan was executed in one workspace branch with final browser validation, planning-state updates, and a single end-of-plan commit.

## Files Created/Modified

- `backend/packages/harness/deerflow/domain/submarine/reporting_acceptance.py` - enriches benchmark comparison evidence with velocity/tolerance/source metadata.
- `backend/packages/harness/deerflow/domain/submarine/evidence.py` - converts benchmark outcomes into explicit validation and readiness states.
- `backend/packages/harness/deerflow/domain/submarine/supervision.py` - preserves benchmark-driven blocker and advisory narratives in the final claim gate.
- `backend/packages/harness/deerflow/domain/submarine/reporting.py` - includes the stronger scientific gate payloads in final report packaging.
- `backend/tests/test_submarine_result_report_tool.py` - locks benchmark pass, block, and not-applicable reporting behavior.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - extends the final-report/runtime contracts for benchmark-driven research evidence and supervisor gate payloads.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts` - builds benchmark-aware acceptance, research-evidence, and claim-gate summaries.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx` - renders richer benchmark-driven gate and evidence sections in the detailed runtime panel.
- `frontend/src/components/workspace/submarine-stage-cards.tsx` - brings SCI-03 summaries into the active `Result Reporting` and `Supervisor Review` cards.
- `frontend/src/components/workspace/submarine-pipeline.tsx` - passes final-report context into the supervisor review surface.
- `frontend/public/demo/threads/submarine-cfd-demo/.../final-report.json` - adds deterministic SCI-03 benchmark and claim-gate payloads.
- `frontend/public/demo/threads/submarine-cfd-demo/thread.json` - mirrors top-level runtime scientific gate status for refresh-safe mock validation.
- `frontend/public/demo/threads/54c9fbd7-38f0-49df-b015-4c0e20d568f8/.../final-report.json` - mirrors the same SCI-03 mock evidence for the second demo thread.
- `frontend/public/demo/threads/54c9fbd7-38f0-49df-b015-4c0e20d568f8/thread.json` - mirrors runtime gate status for the second demo thread.

## Decisions Made

- `not_applicable` benchmark references are scientifically meaningful and must stay visible as claim-limiting evidence.
- The workbench should reuse backend-authored claim/evidence language instead of inventing frontend-only gate wording.
- Deterministic mock thread payloads are part of SCI-03 validation because the UI contract must be proven even before a fresh live benchmark-matched run exists.

## Deviations from Plan

### Auto-fixed Issues

**1. [Fixture Gap] Existing mock reports and thread snapshots could not exercise SCI-03 UI**

- **Found during:** MCP browser validation
- **Issue:** The shipped mock `final-report.json` files still lacked `acceptance_assessment`, `research_evidence_summary`, and `scientific_supervisor_gate`, so the new workbench sections had nothing to render.
- **Fix:** Enriched both mock report fixtures and mirrored top-level runtime gate fields into both mock thread snapshots.
- **Verification:** Reloaded both mock submarine pages and confirmed the new claim-gate and benchmark sections were visible in the DOM.

---

**Total deviations:** 1 auto-fixed (fixture gap)
**Impact on plan:** Necessary to close the real browser-validation loop for SCI-03. No scope creep beyond deterministic validation coverage.

## Issues Encountered

- Legacy mock content in one demo thread still contains older mojibake strings, but it does not block SCI-03 validation because the new scientific gate payloads render correctly and the contract paths are now proven.

## User Setup Required

None for this plan.

## Next Phase Readiness

- Phase 3 is now complete: stability, study workflow, and benchmark evidence all participate in one visible scientific claim contract.
- The next logical GSD step is discussing Phase 4, starting with geometry inspection hardening for unit, scale, and reference-value sanity checks.
- A future non-mock validation pass should capture a fresh live benchmark-matched thread so SCI-03 can be demonstrated with current runtime artifacts, not only deterministic fixtures.

---
*Phase: 03-scientific-verification-gates*
*Completed: 2026-04-02*
