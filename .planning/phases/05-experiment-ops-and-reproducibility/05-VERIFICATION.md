---
phase: 05-experiment-ops-and-reproducibility
verified: 2026-04-02T19:58:04+08:00
status: passed
score: 3/3 must-haves verified
---

# Phase 5: Experiment Ops and Reproducibility Verification Report

**Phase Goal:** Give researchers a reproducible study system with provenance, comparison structure, and consistent environments.
**Verified:** 2026-04-02T19:58:04+08:00
**Status:** passed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every run records the geometry, case template, solver settings, environment, and artifact entrypoints needed for rerunability. | VERIFIED | Phase 05-01 added canonical `provenance-manifest.json`; Phase 05-03 extends it with `environment_fingerprint` and `environment_parity_assessment`; dispatch/report tests passed (`60 passed`). |
| 2 | Baseline, scientific-study, and declared custom-variant runs remain linked as first-class experiment artifacts with reporting-safe lineage. | VERIFIED | Phase 05-02 unified registry/linkage contracts and cockpit rendering; result-report and runtime-panel tests cover compare summaries and custom lineage without regression. |
| 3 | Local dev, Docker Compose, and deployed runtime paths now use one explicit profile vocabulary and surface drift recovery guidance separately from scientific claim state. | VERIFIED | `DEER_FLOW_RUNTIME_PROFILE` is aligned in `.env.example`, `config.yaml`, `docker-compose-dev.yaml`, and `docker-compose.yaml`; parity-specific cockpit copy and reproducibility summaries passed frontend/backend verification. |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/packages/harness/deerflow/domain/submarine/provenance.py` | Canonical per-run provenance contract | EXISTS + SUBSTANTIVE | Builds manifest payloads and provenance summaries from one durable artifact. |
| `backend/packages/harness/deerflow/domain/submarine/environment_parity.py` | Supported runtime-profile detection and parity assessment | EXISTS + SUBSTANTIVE | Defines `matched`, `drifted_but_runnable`, `unknown`, and `blocked` parity outcomes plus recovery guidance. |
| `backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py` | Reproducibility summary derivation | EXISTS + SUBSTANTIVE | Builds compact parity/reproducibility summaries from runtime or manifest data. |
| `backend/packages/harness/deerflow/domain/submarine/reporting_render.py` | Report-visible reproducibility section | EXISTS + SUBSTANTIVE | Renders parity and recovery guidance into markdown/html outputs. |
| `frontend/src/components/workspace/submarine-runtime-panel.utils.ts` | Cockpit formatting for parity and reproducibility | EXISTS + SUBSTANTIVE | Exposes `buildSubmarineReproducibilitySummary()` and stable status labels. |
| `frontend/src/components/workspace/submarine-pipeline-status.ts` | Parity-specific status copy | EXISTS + SUBSTANTIVE | Uses `Drifted but runnable` / `Unknown environment profile` labels instead of scientific readiness labels. |

**Artifacts:** 6/6 verified

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` | `backend/packages/harness/deerflow/domain/submarine/provenance.py` | `build_run_provenance_manifest(...)` with parity payloads | WIRED | Solver dispatch writes both `environment_fingerprint` and `environment_parity_assessment` into the canonical provenance manifest. |
| `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` | `backend/packages/harness/deerflow/domain/submarine/evidence.py` | parity-aware provenance grading | WIRED | Drifted or unknown parity downgrades provenance to `partial` without mutating scientific gate outcomes. |
| `backend/packages/harness/deerflow/domain/submarine/reporting.py` | `backend/packages/harness/deerflow/domain/submarine/reporting_render.py` | `reproducibility_summary` payload -> rendered report section | WIRED | Final reports now carry and render reproducibility metadata instead of leaving parity state implicit. |
| `frontend/src/components/workspace/submarine-pipeline.tsx` | `frontend/src/components/workspace/submarine-pipeline-status.ts` | runtime parity and reproducibility props | WIRED | The cockpit status helper receives parity/reproducibility state and emits parity-specific completion copy. |
| `frontend/src/components/workspace/submarine-runtime-panel.tsx` | `frontend/src/components/workspace/submarine-runtime-panel.utils.ts` | `buildSubmarineReproducibilitySummary(...)` | WIRED | The runtime panel shows manifest path, profile label, drift reasons, and recovery guidance from the shared formatter contract. |

**Wiring:** 5/5 connections verified

## Automated Checks

- `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py tests/test_thread_state_reducers.py`
  - Passed (`60 passed`)
- `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-status.test.ts`
  - Passed (`50 passed`)
- `cd frontend && corepack pnpm typecheck`
  - Passed
- `Select-String -Path .env.example,config.yaml,docker/docker-compose-dev.yaml,docker/docker-compose.yaml -Pattern "DEER_FLOW_RUNTIME_PROFILE"`
  - Passed (aligned runtime profile vocabulary confirmed)

## Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| OPS-01 | SATISFIED | - |
| OPS-02 | SATISFIED | - |
| OPS-03 | SATISFIED | - |

**Coverage:** 3/3 requirements satisfied

## Anti-Patterns Found

None blocking. The verified implementation keeps reproducibility metadata separate from scientific readiness and avoids reusing claim-level labels for runtime-parity communication.

## Human Verification Required

None blocking. A live matched-vs-drifted sandbox run remains recommended for extra operator confidence, but the phase goal is already covered by automated dispatch, reporting, reducer, and cockpit verification.

## Gaps Summary

**No blocking gaps found.** Phase goal achieved. Remaining risk is limited to an optional live runtime spot check that does not change the implemented contracts.

## Verification Metadata

**Verification approach:** Goal-backward using Phase 5 success criteria from `ROADMAP.md`, cross-checked against `05-01/02/03-PLAN.md` must-haves  
**Must-haves source:** ROADMAP success criteria + plan-level must_haves for OPS-01, OPS-02, and OPS-03  
**Automated checks:** backend pytest `60/60`; frontend node tests `50/50`; frontend typecheck; runtime-profile config grep  
**Human checks required:** 0 blocking  
**Total verification time:** ~20 min

---
*Verified: 2026-04-02T19:58:04+08:00*
*Verifier: Codex*
