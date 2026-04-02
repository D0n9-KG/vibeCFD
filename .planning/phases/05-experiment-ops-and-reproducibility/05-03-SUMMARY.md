---
phase: 05-experiment-ops-and-reproducibility
plan: 03
subsystem: runtime-parity
tags: [submarine, runtime-parity, reproducibility, reporting, cockpit]
requires:
  - phase: 05-01
    provides: canonical provenance manifests and reducer-safe provenance pointers
  - phase: 05-02
    provides: experiment lineage and runtime/report surfaces ready for parity overlays
provides:
  - Explicit runtime fingerprints and parity assessments for each solver-dispatch run
  - Reproducibility summaries that stay separate from scientific claim-level evidence
  - One aligned DEER_FLOW_RUNTIME_PROFILE vocabulary across docs, compose files, and cockpit copy
affects: [phase-05-experiment-ops-and-reproducibility, phase-06-research-delivery-workbench]
tech-stack:
  added: []
  patterns:
    - "Treat environment parity as reproducibility metadata that can downgrade rerun confidence without rewriting scientific gate outcomes."
    - "Keep runtime-profile vocabulary synchronized across backend config, deployment docs, and cockpit labels."
key-files:
  created:
    - .planning/phases/05-experiment-ops-and-reproducibility/05-03-SUMMARY.md
    - backend/packages/harness/deerflow/domain/submarine/environment_parity.py
  modified:
    - .env.example
    - backend/packages/harness/deerflow/domain/submarine/models.py
    - backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py
    - backend/packages/harness/deerflow/domain/submarine/evidence.py
    - backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py
    - backend/packages/harness/deerflow/domain/submarine/reporting.py
    - backend/packages/harness/deerflow/domain/submarine/reporting_render.py
    - backend/packages/harness/deerflow/agents/thread_state.py
    - backend/tests/test_submarine_solver_dispatch_tool.py
    - backend/tests/test_submarine_result_report_tool.py
    - backend/tests/test_thread_state_reducers.py
    - docker/docker-compose-dev.yaml
    - docker/docker-compose.yaml
    - docker/openfoam-sandbox/README.md
    - frontend/src/components/workspace/submarine-runtime-panel.utils.ts
    - frontend/src/components/workspace/submarine-runtime-panel.tsx
    - frontend/src/components/workspace/submarine-pipeline-status.ts
    - frontend/src/components/workspace/submarine-pipeline.tsx
key-decisions:
  - "Parity status remains `matched | drifted_but_runnable | unknown | blocked`, while scientific gate outcomes continue to describe evidence quality."
  - "Environment fingerprints and parity assessments share the same field vocabulary so reducers, report builders, and UI helpers can consume one stable shape."
  - "The supported runtime profile vocabulary is exactly `local_cli`, `docker_compose_dev`, and `docker_compose_deployed`."
patterns-established:
  - "Populate `environment_parity_assessment` during solver dispatch and persist it in both runtime state and provenance-manifest.json."
  - "Render reproducibility guidance through compact summary helpers instead of reusing scientific claim labels in cockpit status copy."
requirements-completed: [OPS-03]
duration: "~1h across interrupted execution, integration, and verification"
completed: 2026-04-02
---

# Phase 5: Experiment Ops and Reproducibility Plan 03 Summary

**Every submarine run now carries an explicit runtime parity verdict, reproducibility downgrade guidance, and aligned runtime-profile vocabulary from backend config through the cockpit.**

## Performance

- **Duration:** ~1 h across interrupted execution, integration, and verification
- **Started:** 2026-04-02T18:52:00+08:00
- **Completed:** 2026-04-02T19:58:04+08:00
- **Tasks:** 3 planned runtime-parity tasks
- **Files modified:** 26 implementation files

## Accomplishments

- Added `environment_parity.py` plus new environment fingerprint/parity models so solver dispatch records supported runtime profiles, origin, mount strategy, config sources, drift reasons, and recovery guidance for every run.
- Persisted `environment_parity_assessment` alongside the canonical provenance manifest and reducer-safe runtime snapshot, keeping parity metadata available to later report generation and cockpit refreshes.
- Hardened evidence and reporting so parity drift downgrades reproducibility and provenance honesty without mutating scientific claim-level outcomes such as verification or supervisor-gate status.
- Added `reproducibility_summary` to final reporting plus markdown/html rendering, making the manifest path, profile id, parity state, and recovery guidance visible in exported report artifacts.
- Extended existing cockpit contracts, formatter helpers, runtime panels, and pipeline status copy so researchers see parity-specific wording like `Drifted but runnable` instead of scientific labels such as `research_ready`.
- Aligned `.env.example`, both compose files, and sandbox docs around `DEER_FLOW_RUNTIME_PROFILE`, while verifying that `config.yaml` already matched the required vocabulary and default.

## Verification

- `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py tests/test_thread_state_reducers.py`
  - Result: passed (`60 passed`)
- `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-status.test.ts`
  - Result: passed (`50 passed`)
- `cd frontend && corepack pnpm typecheck`
  - Result: passed
- `Select-String -Path .env.example,config.yaml,docker/docker-compose-dev.yaml,docker/docker-compose.yaml -Pattern "DEER_FLOW_RUNTIME_PROFILE"`
  - Result: confirmed aligned profile values across checked config and compose files

## Task Commits

- Pending integration commit during phase closeout.

## Files Created/Modified

- `backend/packages/harness/deerflow/domain/submarine/environment_parity.py` - defines supported runtime profiles, fingerprint derivation, and parity assessment rules.
- `backend/packages/harness/deerflow/domain/submarine/models.py` - adds parity-aware environment fingerprint and assessment models.
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` - records environment fingerprint/parity data into runtime payloads and provenance manifests.
- `backend/packages/harness/deerflow/domain/submarine/evidence.py` - downgrades provenance traceability when runtime parity drifts or is unknown.
- `backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py` - builds compact reproducibility summaries from parity-aware runtime/report data.
- `backend/packages/harness/deerflow/domain/submarine/reporting.py` - injects parity and reproducibility summaries into final report payloads.
- `backend/packages/harness/deerflow/domain/submarine/reporting_render.py` - renders a dedicated reproducibility section in markdown/html reports.
- `backend/packages/harness/deerflow/agents/thread_state.py` - preserves parity data through reducer merges.
- `.env.example` - documents the default local runtime profile.
- `docker/docker-compose-dev.yaml` - pins the dev compose profile vocabulary.
- `docker/docker-compose.yaml` - pins the deployed compose profile vocabulary.
- `docker/openfoam-sandbox/README.md` - documents the supported profile values and intended usage.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - adds parity and reproducibility fields to the runtime panel contract.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts` - formats parity labels, drift reasons, and recovery guidance.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx` - renders a compact reproducibility block inside the existing runtime panel.
- `frontend/src/components/workspace/submarine-pipeline-status.ts` - uses parity-specific completion copy for drifted or unknown runtime states.
- `frontend/src/components/workspace/submarine-pipeline.tsx` - threads runtime parity data into the workbench status calculation.
- `backend/tests/test_submarine_solver_dispatch_tool.py` - locks matched and drifted parity behavior at dispatch time.
- `backend/tests/test_submarine_result_report_tool.py` - locks reproducibility summaries and parity-driven provenance downgrade behavior.
- `backend/tests/test_thread_state_reducers.py` - locks reducer-safe parity field merges.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts` - locks reproducibility summary formatting.
- `frontend/src/components/workspace/submarine-pipeline-status.test.ts` - locks parity-specific runtime status copy.

## Decisions Made

- Runtime parity is a reproducibility truth, not a scientific truth, so drift limits rerun confidence without rewriting validation evidence.
- The same parity payload shape should flow through backend state, final reports, and UI helpers to avoid translation bugs between layers.
- Unsupported or mismatched runtime profiles must remain visible with explicit recovery guidance rather than silently collapsing back to generic runtime labels.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Report rendering needed explicit reproducibility output**
- **Found during:** Task 2 (reporting integration)
- **Issue:** The plan centered on payload/report-summary changes, but markdown/html exports flow through `reporting_render.py`; without updating that renderer, parity and reproducibility would stay invisible in generated report artifacts.
- **Fix:** Added a dedicated reproducibility section to `reporting_render.py` and extended the report tests to cover markdown/html output.
- **Files modified:** `backend/packages/harness/deerflow/domain/submarine/reporting_render.py`, `backend/tests/test_submarine_result_report_tool.py`
- **Verification:** `uv run pytest tests/test_submarine_result_report_tool.py`

**2. [Rule 3 - Blocking] Parity assessment builder duplicated inherited status fields**
- **Found during:** Final backend verification
- **Issue:** `SubmarineEnvironmentParityAssessment` inherits the fingerprint shape, so seeding it with a full fingerprint dump and a second explicit `parity_status` raised a `TypeError` across solver-dispatch tests.
- **Fix:** Excluded `parity_status`, `drift_reasons`, and `recovery_guidance` from the fingerprint seed before constructing the assessment model.
- **Files modified:** `backend/packages/harness/deerflow/domain/submarine/environment_parity.py`
- **Verification:** `uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py tests/test_thread_state_reducers.py`

---

**Total deviations:** 2 auto-fixed (1 missing-critical report visibility gap, 1 blocking parity-model construction bug)
**Impact on plan:** Both fixes were necessary to keep parity/reproducibility visible and to restore solver-dispatch correctness. No scope creep beyond the planned runtime-parity surface area.

## Issues Encountered

- `config.yaml` already contained the required `DEER_FLOW_RUNTIME_PROFILE: local_cli` default, so the alignment task became verification-only for that file rather than a new edit.
- The plan's suggested manual matched-vs-drifted runtime check was not run against a live sandbox during this checkpoint; automated dispatch, reporting, reducer, and frontend coverage provide the current confidence.

## User Setup Required

None.

## Next Phase Readiness

- Phase 05 is now complete: provenance, experiment lineage, and runtime parity all travel through the same report and cockpit surfaces.
- Phase 06 can build researcher-facing delivery and supervisor actions on top of explicit reproducibility state instead of inferring environment health from generic runtime artifacts.

---
*Phase: 05-experiment-ops-and-reproducibility*
*Completed: 2026-04-02*
