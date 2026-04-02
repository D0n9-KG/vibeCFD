---
phase: 04-geometry-and-case-intelligence-hardening
verified: 2026-04-03T01:44:59+08:00
status: passed
score: 3/3 must-haves verified
---

# Phase 4: Geometry and Case Intelligence Hardening Verification Report

**Phase Goal:** Improve geometry trust, scale assumptions, and case knowledge so researchers get defensible setup recommendations.  
**Verified:** 2026-04-03T01:44:59+08:00  
**Status:** passed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Geometry preflight now emits structured integrity, scale, and reference-value findings that can block or downgrade setup before solve. | VERIFIED | Phase 04-01 added `geometry_findings`, `scale_assessment`, `reference_value_suggestions`, and clarification-required semantics; current regression suite covers severe mismatch, low-risk suggestion, and geometry-driven confirmation blocks. |
| 2 | Recommended cases now expose provenance quality, applicability conditions, and missing-evidence disclosure instead of silently presenting placeholder references as benchmark truth. | VERIFIED | Phase 04-02 hardened case/reference models, active case-library entries, and result-report provenance summaries; backend domain-assets and report tests passed on 2026-04-03. |
| 3 | Researcher approval is now an explicit pre-compute calculation-plan gate that stays separate from post-compute scientific claim language across the real cockpit. | VERIFIED | Phase 04-03 browser validation on `submarine-phase4-review-demo?mock=true` confirmed clarify, approve, and rerun CTAs stay inside the workbench and use calculation-plan approval copy rather than scientific-claim labels. |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/packages/harness/deerflow/domain/submarine/design_brief.py` | Persisted calculation-plan state | EXISTS + SUBSTANTIVE | Carries suggestion provenance, approval state, and researcher notes through the design brief. |
| `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py` | Structured geometry trust findings | EXISTS + SUBSTANTIVE | Emits integrity, scale, and reference-value findings instead of prose-only summary text. |
| `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py` | Dynamic confirmation gating | EXISTS + SUBSTANTIVE | Computes pending approval vs immediate clarification from calculation-plan semantics. |
| `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py` | Execution block until approval | EXISTS + SUBSTANTIVE | Prevents solver dispatch from using unconfirmed geometry or case assumptions. |
| `frontend/src/components/workspace/submarine-confirmation-actions.ts` | Researcher approval CTA contract | EXISTS + SUBSTANTIVE | Emits explicit approve/revise prompts with persisted snapshots. |
| `frontend/src/components/workspace/submarine-stage-cards.tsx` | Active workbench approval semantics | EXISTS + SUBSTANTIVE | Shows geometry review, solver hold, and pending confirmation states on the real stage cards. |

**Artifacts:** 6/6 verified

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/packages/harness/deerflow/domain/submarine/design_brief.py` | `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py` | shared calculation-plan contract | WIRED | Geometry-derived assumptions merge into the same persisted calculation plan as brief-generated suggestions. |
| `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py` | `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py` | confirmation status derivation | WIRED | Severe ambiguity moves the flow into confirmation-required or blocked state before solver dispatch. |
| `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py` | `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py` | approval gate enforcement | WIRED | Pending calculation-plan items block execution until the researcher confirms or revises them. |
| `frontend/src/components/workspace/submarine-confirmation-actions.ts` | `frontend/src/app/mock/api/threads/[thread_id]/runs/stream/route.ts` | deterministic CTA validation path | WIRED | Clarify, approve, and rerun actions now succeed under mock browser validation instead of hitting a 404. |
| `frontend/src/components/workspace/submarine-stage-cards.tsx` | `frontend/src/components/workspace/submarine-pipeline-status.ts` | pre-compute approval copy | WIRED | The active workbench and top-line pipeline status share one calculation-plan approval vocabulary. |

**Wiring:** 5/5 connections verified

## Automated Checks

- `cd backend && uv run pytest tests/test_submarine_design_brief_tool.py tests/test_submarine_geometry_check_tool.py tests/test_submarine_runtime_context.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_artifact_store.py tests/test_thread_state_reducers.py tests/test_submarine_result_report_tool.py tests/test_submarine_scientific_followup_tool.py tests/test_submarine_domain_assets.py tests/test_submarine_experiment_linkage_contracts.py`
  - Passed (`117 passed`) on 2026-04-03
- `cd frontend && node --test src/components/workspace/input-box.submit.test.ts src/core/threads/thread-upload-files.test.ts src/components/ai-elements/prompt-input.files.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-runtime-panel.trends.test.ts src/components/workspace/submarine-pipeline-runs.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-pipeline-shell.test.ts src/components/workspace/submarine-confirmation-actions.test.ts src/app/workspace/submarine/submarine-pipeline-layout.test.ts src/app/mock/api/threads/mock-thread-store.test.ts src/core/config/runtime-base-url.test.ts`
  - Passed (`92 passed`) on 2026-04-03
- `cd frontend && corepack pnpm typecheck`
  - Passed on 2026-04-03

## Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| GEO-01 | SATISFIED | - |
| GEO-02 | SATISFIED | - |
| GEO-03 | SATISFIED | - |

**Coverage:** 3/3 requirements satisfied

## Anti-Patterns Found

None blocking. The verified implementation keeps pre-compute approval separate from post-compute scientific readiness and avoids reusing claim-level copy for setup uncertainty.

## Human Verification Required

None blocking. The deterministic Phase 4 review fixture already exercises the real approval CTA path end to end; a fresh live ambiguous-STL spot check remains optional rather than required for sign-off.

## Gaps Summary

**No blocking gaps found.** Phase goal achieved.

## Verification Metadata

**Verification approach:** Goal-backward using Phase 4 success criteria from `ROADMAP.md`, cross-checked against `04-01/02/03-SUMMARY.md` and the current regression suite  
**Must-haves source:** ROADMAP success criteria + validation contract in `04-VALIDATION.md`  
**Automated checks:** backend pytest `117/117`; frontend node tests `92/92`; frontend typecheck  
**Human checks required:** 0 blocking  
**Total verification time:** ~20 min

---
*Verified: 2026-04-03T01:44:59+08:00*
*Verifier: Codex*
