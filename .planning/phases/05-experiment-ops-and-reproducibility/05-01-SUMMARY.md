---
phase: 05-experiment-ops-and-reproducibility
plan: 01
subsystem: canonical-run-provenance
tags: [submarine, provenance, reporting, runtime-state, reproducibility]
requires: []
provides:
  - "Canonical provenance-manifest.json artifact for every solver-dispatch run"
  - "Reducer-safe provenance pointers and summaries in submarine_runtime"
  - "Final reporting and research evidence that read the canonical manifest instead of inferring provenance from scattered artifacts"
affects: [phase-05-experiment-ops-and-reproducibility, phase-06-research-delivery-workbench]
tech-stack:
  added: []
  patterns:
    - "Treat provenance-manifest.json as the single rerun and audit entrypoint for each submarine run."
    - "Keep solver dispatch, runtime reducers, research evidence, and final reporting aligned on the same provenance pointer."
key-files:
  created:
    - .planning/phases/05-experiment-ops-and-reproducibility/05-01-SUMMARY.md
    - backend/packages/harness/deerflow/domain/submarine/provenance.py
  modified:
    - backend/packages/harness/deerflow/domain/submarine/models.py
    - backend/packages/harness/deerflow/domain/submarine/artifact_store.py
    - backend/packages/harness/deerflow/domain/submarine/contracts.py
    - backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py
    - backend/packages/harness/deerflow/agents/thread_state.py
    - backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py
    - backend/packages/harness/deerflow/domain/submarine/reporting.py
    - backend/packages/harness/deerflow/domain/submarine/evidence.py
    - backend/packages/harness/deerflow/domain/submarine/remediation.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py
    - backend/tests/test_submarine_solver_dispatch_tool.py
    - backend/tests/test_thread_state_reducers.py
    - backend/tests/test_submarine_result_report_tool.py
key-decisions:
  - "The canonical provenance manifest must be written during solver dispatch, even for blocked or confirmation-pending runs."
  - "Research evidence only counts provenance as traceable when the canonical manifest is actually present and complete."
patterns-established:
  - "Use manifest_virtual_path plus provenance_summary as the reducer-safe provenance contract across runtime merges and report refreshes."
  - "Prefer downstream consumers loading provenance from provenance-manifest.json over rebuilding provenance from request/results/experiment artifacts ad hoc."
requirements-completed: [OPS-01]
duration: "~1h across delegated bootstrap, local integration, and verification"
completed: 2026-04-02
---

# Phase 5: Experiment Ops and Reproducibility Plan 01 Summary

**Every submarine solver-dispatch run now emits one canonical provenance manifest, and the same manifest pointer survives runtime merges, result reporting, and research-evidence grading.**

## Performance

- **Duration:** ~1 h across delegated bootstrap, local integration, and verification
- **Completed:** 2026-04-02T17:53:13+08:00
- **Tasks:** 3 planned provenance tasks
- **Files modified:** 14

## Accomplishments

- Added `SubmarineRunProvenanceManifest` plus a focused `provenance.py` helper module so provenance has one explicit contract instead of being inferred from several loosely related artifacts.
- Extended the canonical solver-dispatch artifact bundle with `provenance-manifest.json` and added a loader in `artifact_store.py` so downstream consumers can resolve the manifest through the existing virtual-path strategy.
- Updated solver dispatch to write the canonical manifest after artifact paths are known, preserve `provenance_manifest_virtual_path` in its payload, and surface a compact `provenance_summary` back into runtime state.
- Preserved `provenance_manifest_virtual_path`, `provenance_summary`, and `environment_fingerprint` through `submarine_runtime` reducer merges so refresh-safe runtime recovery keeps the same provenance entrypoint.
- Taught final reporting to read the canonical manifest directly, emit `provenance_summary` in the final report payload, and keep the runtime snapshot aligned with the same manifest pointer after result reporting finishes.
- Hardened research-evidence grading so missing or incomplete provenance manifests downgrade provenance to `partial` even when lower-level solver and experiment artifacts are present.
- Tightened remediation routing so provenance-driven auto follow-up is only suggested after validation is already satisfied, avoiding misleading auto-rerun suggestions when the next real step is still manual review.

## Verification

- `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_thread_state_reducers.py tests/test_submarine_result_report_tool.py`
  - Result: passed (`58 passed`)

## Task Commits

- `45a311c` `feat(05-01): add canonical provenance manifest contract`
- `9a0af1c` `feat(05-01): persist canonical provenance manifests`
- `c1bfa66` `feat(05-01): preserve provenance through reporting`

## Files Created/Modified

- `backend/packages/harness/deerflow/domain/submarine/provenance.py` - defines canonical manifest builders, approval snapshots, completeness checks, and compact provenance summaries.
- `backend/packages/harness/deerflow/domain/submarine/models.py` - adds the first-class provenance manifest model.
- `backend/packages/harness/deerflow/domain/submarine/artifact_store.py` - extends the canonical artifact bundle and adds manifest loading helpers.
- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - carries provenance path and summary fields in the runtime snapshot contract.
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` - writes `provenance-manifest.json`, records its virtual path, and returns runtime-ready provenance summary data.
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py` - preserves the manifest pointer and provenance summary in runtime updates.
- `backend/packages/harness/deerflow/agents/thread_state.py` - merges provenance and environment dictionaries safely across parallel runtime updates.
- `backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py` - loads provenance from the canonical manifest and builds report-ready summaries.
- `backend/packages/harness/deerflow/domain/submarine/reporting.py` - injects provenance summary data into final report payloads.
- `backend/packages/harness/deerflow/domain/submarine/evidence.py` - requires the canonical manifest for `traceable` provenance.
- `backend/packages/harness/deerflow/domain/submarine/remediation.py` - avoids auto-followup precedence when manual validation work is still the real next step.
- `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py` - keeps runtime state aligned with the canonical provenance pointer after final reporting.
- `backend/tests/test_submarine_solver_dispatch_tool.py` - locks canonical manifest emission and blocked-run behavior.
- `backend/tests/test_thread_state_reducers.py` - locks provenance/environment merge behavior.
- `backend/tests/test_submarine_result_report_tool.py` - locks final payload provenance summaries and provenance downgrade behavior.

## Decisions Made

- Provenance must be a first-class artifact, not a convention reconstructed from request/results filenames.
- Final reporting should grade provenance against the actual canonical manifest on disk, not merely against the presence of lower-level artifacts.

## Issues Encountered

- The new provenance downgrade rule exposed an existing remediation edge case where auto report regeneration could outrank a required manual validation-reference action; this was corrected before final verification.

## User Setup Required

None.

## Next Phase Readiness

- Phase 05-01 is complete: every run now has one authoritative provenance entrypoint, and downstream runtime/reporting flows can reference it consistently.
- Phase 05-02 can now extend experiment manifests and baseline-vs-variant lineage on top of a stable per-run provenance contract.

---
*Phase: 05-experiment-ops-and-reproducibility*
*Completed: 2026-04-02*
