# SUBOFF Scale Consistency And Report Hardening Session Status

**Status:** active

**Plan:** `docs/superpowers/plans/2026-04-16-suboff-scale-consistency-and-report-hardening.md`

**Primary Spec / Brief:** none

**Prior Art Survey:** none

**Context Summary:** none

**Research Overlay:** enabled

**Research Mainline:** Demonstrate that the current SUBOFF workflow can turn a real binary STL upload into a meter-consistent OpenFOAM case, a physically plausible resistance result, and a report that a researcher can audit without guessing where corrected outputs came from.

**Decision Log:** `docs/superpowers/research-decisions/2026-04-16-suboff-scale-consistency-and-report-hardening-decision-log.md`

**Research Findings:** `docs/superpowers/research-findings/2026-04-16-suboff-scale-consistency-and-report-hardening-findings.md`

**Last Updated:** 2026-04-16 10:27 Asia/Shanghai

**Current Focus:** Final verification and handoff after correcting the real SUBOFF baseline, adding binary-STL regression coverage, and regrouping the final report appendix into report / solver / workspace sections.

**Next Recommended Step:** If a later session continues from here, focus on scientific-completeness work that still blocks the supervisor gate: execute the planned sensitivity-study variants or run a benchmark-aligned condition before claiming research-grade readiness.

**Read This Order On Resume:**
1. This session status file
2. The linked implementation plan
3. `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
4. `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
5. `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_case.py`
6. `backend/packages/harness/deerflow/domain/submarine/reporting.py`
7. `backend/packages/harness/deerflow/domain/submarine/reporting_render.py`
8. `docs/superpowers/research-decisions/2026-04-16-suboff-scale-consistency-and-report-hardening-decision-log.md`
9. `docs/superpowers/research-findings/2026-04-16-suboff-scale-consistency-and-report-hardening-findings.md`
10. `Execution / Review Trace`
11. `Artifact Hygiene / Retirement`
12. Any additional findings files listed below
13. Git status and recent relevant commits

## Progress Snapshot
- Completed Tasks: Task 1, Task 2, Task 3, Task 4
- In Progress: review / handoff only
- Reopened / Invalidated: prior report-only polish work was reopened and replaced by the scale-consistency + corrected-rerun mainline

## Execution / Review Trace
- Latest Implementation Mode: local execution
- Latest Review Mode: local verification + reviewer subagent
- Latest Delegation Note: implementation stayed local because the rerun and report refresh were tightly coupled to the active thread artifacts; a reviewer subagent was used at the milestone closeout and returned no findings

## Research Overlay Check
- Research Mainline Status: advancing the mainline
- Non-Negotiables Status: still holding
- Forbidden Regression Check: no regression observed in the current rerun; the stale `Cd ~3073` artifact was replaced by a corrected baseline
- Method Fidelity Check: current active-thread case geometry, reference values, solver outputs, and final report are now aligned
- Scale Gate Status: small-scope proof verified
- Decision Log Updates: kept the invalid-stale-result decision; report appendix grouping was implemented without changing the underlying artifact contracts
- Research Findings Updates: recorded the corrected rerun (`Cd ~0.113`, `Fx ~537.9 N`), grouped-report output, and reviewer outcome

## Artifact Hygiene / Retirement
- Keep / Promote: this plan/status pair, the linked decision-log and findings artifacts, the binary-STL solver-dispatch regression test, and the grouped-report regression coverage
- Archive / Delete / Replace Next: the stale scale-inflated `suboff_solid` solver/report artifacts have been replaced in place by the corrected rerun; no extra debug scripts remain to delete

## Latest Verified State
- Added end-to-end regression coverage on the public solver-dispatch tool path for binary STL scale propagation; `uv run --project backend pytest backend/tests/test_submarine_solver_dispatch_tool.py -k "geometry_scale_factor or binary_case_geometry" -q` passed
- Regenerated the real active-thread `suboff_solid` case and confirmed the persisted `constant/triSurface/suboff_solid.stl` is now meter-scale (`length_x ~ 4.356`, `span_y ~ 0.7303`, `span_z ~ 0.5080`)
- Re-executed the real `suboff_solid` baseline through the project tool path; the corrected `solver-results.json` now reports `Cd = 0.113173151` and `Fx = 537.9440988 N`
- Added `artifact_group_summary` to the final report payload and updated markdown / HTML rendering so the appendix is grouped into `??????`, `???????`, and `????????`
- Fresh report-suite verification passed: `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py -q` -> `39 passed`
- Fresh syntax verification passed: `python -m py_compile backend/packages/harness/deerflow/domain/submarine/reporting.py backend/packages/harness/deerflow/domain/submarine/reporting_render.py backend/tests/test_submarine_result_report_tool.py backend/tests/test_submarine_solver_dispatch_tool.py`
- Reviewer subagent reported no findings on the current code slice; only residual low-risk note was to keep an eye on fallback rendering for older payloads

## Unverified Hypotheses / Next Checks
- The active supervisor gate remains blocked because planned sensitivity-study variants are still missing solver results, not because the baseline scale path is broken
- A benchmark-aligned 3.05 m/s SUBOFF run may still be needed if the project wants a direct apples-to-apples comparison against the cited EFD reference

## Open Questions / Risks
- The corrected 5 m/s baseline is now physically plausible, but the project still lacks the planned scientific-study completions needed to lift the supervisor gate beyond `blocked_by_setup`
- The current report grouping is stronger, but the body still surfaces long evidence-gap text because the scientific-study workflow is partial

## Relevant Findings / Notes
- Corrected active-thread solver artifact: `backend/.deer-flow/threads/01fec432-dead-4cb3-8c2d-09896f4fe832/user-data/outputs/submarine/solver-dispatch/suboff_solid/solver-results.json`
- Corrected active-thread report artifact: `backend/.deer-flow/threads/01fec432-dead-4cb3-8c2d-09896f4fe832/user-data/outputs/submarine/reports/suboff_solid/final-report.md`
- Snapshot used for report refresh: `backend/.deer-flow/threads/01fec432-dead-4cb3-8c2d-09896f4fe832/user-data/outputs/submarine/solver-dispatch/suboff_solid/result-report-snapshot.json`
