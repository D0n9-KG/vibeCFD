---
status: validated
phase: 04-geometry-and-case-intelligence-hardening
source:
  - ROADMAP.md
  - REQUIREMENTS.md
updated: 2026-04-02
---

## Current Test

Browser validation on `http://localhost:3000/workspace/submarine/submarine-phase4-review-demo?mock=true`

Automated verification:
- `cd frontend && node --test src/components/workspace/submarine-confirmation-actions.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-shell.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-pipeline-runs.test.ts` passed (`56 passed`)
- `cd frontend && node --test src/app/mock/api/threads/mock-thread-store.test.ts` passed (`1 passed`)
- `cd frontend && corepack pnpm typecheck` passed
- Mock approval CTAs now post to `/mock/api/threads/submarine-phase4-review-demo/runs/stream` with `200` responses and keep the researcher inside the workbench review flow.

## Planned UAT

### 1. Geometry Preflight Detects Trust Risks
expected: Invalid, mis-scaled, or ambiguous STL inputs are flagged before solve with actionable explanations.
result: passed
notes:
- The cockpit header used pre-compute approval language (`Immediate researcher clarification is required before any real computation can begin`) instead of post-compute scientific claim labels.
- The live `Geometry Preflight` card rendered `NEEDS IMMEDIATE CLARIFICATION`, `SCALE ASSESSMENT`, `GEOMETRY FINDINGS`, `REFERENCE SUGGESTIONS`, and `CALCULATION PLAN REVIEW`.
- The workbench kept the geometry gate visible while the solver stage remained blocked behind researcher confirmation.

### 2. Case Library Uses Real Acceptance Profiles
expected: A researcher can inspect the source references and acceptance logic behind a recommended case profile.
result: passed
notes:
- The workbench surfaced `Selected baseline case | Pending researcher confirmation | Case library` in the calculation-plan summary.
- Artifact rail entries for `cfd-design-brief.json` and `geometry-check.json` remained available during browser validation.
- The loaded runtime payload exposed case-library provenance, applicability conditions, and the benchmark-backed source URL for the selected baseline case.

### 3. Unsupported Geometry Is Downgraded or Blocked Clearly
expected: Non-research-ready geometry does not proceed silently and instead yields a visible downgrade or block decision.
result: passed
notes:
- The live `Solver Dispatch` card rendered `NEEDS IMMEDIATE CLARIFICATION` and explicitly stated that solver dispatch was paused until the researcher reviewed the calculation plan.
- Browser interaction verified all three calculation-plan CTAs (`补充待确认条件`, `确认通过`, `需要重算`) without leaving the workbench or triggering the previous mock `404`.
- The mock review thread stayed in deterministic pre-compute review mode, proving the UI can block execution clearly while still accepting reviewer actions.

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

- None.
