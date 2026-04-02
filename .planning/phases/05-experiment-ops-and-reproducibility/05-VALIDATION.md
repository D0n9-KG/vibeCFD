---
phase: 05
slug: experiment-ops-and-reproducibility
status: ready_for_planning
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-01
updated: 2026-04-02
---

# Phase 05 - Validation Strategy

## Validation Goal

Prove that Phase 5 makes submarine studies reproducible in an operator-honest way.

The validation target is not only "more artifacts exist", but:

- every run emits one canonical provenance entrypoint,
- baseline, deterministic study variants, and custom variants remain traceable inside one experiment boundary,
- local, compose, and deployed environment differences are fingerprinted and reported,
- environment drift downgrades reproducibility honestly without being confused with scientific claim-level gating.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` + Node test runner + TypeScript typecheck + config/doc diff inspection |
| **Config file** | `backend/pyproject.toml`, `frontend/package.json`, `frontend/tsconfig.json`, `config.yaml`, `docker/docker-compose-dev.yaml`, `docker/docker-compose.yaml` |
| **Quick run command** | `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_experiment_linkage_contracts.py tests/test_thread_state_reducers.py` |
| **Full suite command** | `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_experiment_linkage_contracts.py tests/test_thread_state_reducers.py tests/test_submarine_result_report_tool.py && cd ../frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-runs.test.ts src/components/workspace/submarine-pipeline-status.test.ts && corepack pnpm typecheck` |
| **Estimated runtime** | ~150 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_experiment_linkage_contracts.py tests/test_thread_state_reducers.py`
- **After every plan wave:** Run the full suite command
- **Before `$gsd-verify-work`:** Full suite must be green and the config/profile labels must be aligned across runtime docs
- **Max feedback latency:** 150 seconds

---

## Validation Dimensions

### Dimension 1: Canonical Provenance Entry Point

Must validate:

- every completed run writes one canonical `provenance-manifest.json`
- the manifest records geometry, case, solver settings, requested outputs, approval snapshot, experiment ids, and environment fingerprint
- runtime state and final reporting point to the same manifest path

### Dimension 2: Experiment Membership Integrity

Must validate:

- baseline and deterministic study variants still satisfy strict linkage checks
- declared custom variants are treated as valid experiment members rather than accidental anomalies
- compare coverage remains explicit for both built-in and custom variants

### Dimension 3: Environment Parity Honesty

Must validate:

- the system records a normalized runtime profile id for each run
- parity status distinguishes `matched`, `drifted_but_runnable`, `unknown`, and `blocked`
- drift downgrades reproducibility evidence instead of silently claiming strict reproducibility

### Dimension 4: Cockpit and Report Clarity

Must validate:

- the existing runtime panel can show provenance and reproducibility summaries without a new page architecture
- reproducibility wording stays separate from scientific claim-level wording
- recovery guidance tells the operator whether to rerun, realign config, or accept downgraded reproducibility

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | OPS-01 | backend schema/artifact | `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py` | `backend/tests/test_submarine_solver_dispatch_tool.py` | pending |
| 05-01-02 | 01 | 1 | OPS-01 | runtime merge/report | `cd backend && uv run pytest tests/test_thread_state_reducers.py tests/test_submarine_result_report_tool.py` | `backend/tests/test_thread_state_reducers.py` | pending |
| 05-02-01 | 02 | 2 | OPS-02 | backend linkage contract | `cd backend && uv run pytest tests/test_submarine_experiment_linkage_contracts.py` | `backend/tests/test_submarine_experiment_linkage_contracts.py` | pending |
| 05-02-02 | 02 | 2 | OPS-02 | backend report + frontend summary | `cd backend && uv run pytest tests/test_submarine_result_report_tool.py && cd ../frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-runs.test.ts && corepack pnpm typecheck` | `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts` | pending |
| 05-03-01 | 03 | 3 | OPS-03 | backend parity/evidence | `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py tests/test_thread_state_reducers.py` | `backend/tests/test_submarine_result_report_tool.py` | pending |
| 05-03-02 | 03 | 3 | OPS-01, OPS-03 | frontend clarity + config alignment | `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-status.test.ts && corepack pnpm typecheck` | `frontend/src/components/workspace/submarine-pipeline-status.test.ts` | pending |

---

## Wave 0 Requirements

Existing experiment, reporting, and runtime-panel infrastructure already covers the execution skeleton for this phase.

No new service or new top-level route is required before implementation begins.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| One baseline run and one custom variant remain visible under the same experiment boundary in the cockpit | OPS-02 | Requires a real operator view of compact summary density and labeling | Execute one baseline resistance run, register one manual custom variant, open the existing runtime panel, and confirm both appear under one experiment id with explicit baseline linkage |
| A drifted environment remains executable but is downgraded visibly | OPS-03 | Requires comparing run behavior plus operator-facing messaging | Execute one run under a matched profile and one under a deliberately drifted profile, then confirm the drifted run still completes while the reproducibility summary reports downgrade reasons and recovery guidance |
| The provenance manifest is sufficient as the rerun entrypoint | OPS-01 | Requires human inspection of artifact completeness, not only field presence | Open `provenance-manifest.json`, verify it points to geometry, request, solver results, experiment artifacts, and environment fingerprint, then confirm a reviewer can explain rerun prerequisites from that file alone |
| Reproducibility wording stays separate from scientific claim wording | OPS-03 | Requires visual comparison across cockpit and final report surfaces | Compare a report/runtime panel that shows parity drift with a report/runtime panel that shows scientific validation gaps, and verify the labels remain semantically distinct |

---

## Evidence To Capture Before Phase Sign-Off

- one baseline `provenance-manifest.json` artifact
- one `experiment-manifest.json` artifact that includes at least one custom variant member
- one `run-compare-summary.json` artifact showing baseline-to-variant linkage
- one final report payload containing both `provenance_summary` and `reproducibility_summary`
- cockpit screenshots or notes for:
  - matched profile,
  - drifted but runnable profile,
  - baseline plus custom variant in one experiment summary

---

## Exit Criteria

Phase 5 is not ready for execution sign-off until all of the following are true:

- `OPS-01` is backed by a single canonical `provenance-manifest.json` per run
- `OPS-02` is backed by one experiment registry contract that accepts baseline, deterministic study variants, and declared custom variants
- `OPS-03` is backed by per-run environment fingerprints plus explicit parity assessment and recovery guidance
- at least one matched run and one drifted run demonstrate the intended downgrade semantics
- `nyquist_compliant: true` remains valid because every task maps to deterministic automated checks or explicit manual verification
