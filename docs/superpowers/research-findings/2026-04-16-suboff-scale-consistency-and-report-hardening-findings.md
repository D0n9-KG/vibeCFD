# SUBOFF Scale Consistency And Report Hardening Research Findings

**Status:** active

**Related Plan:** `docs/superpowers/plans/2026-04-16-suboff-scale-consistency-and-report-hardening.md`

**Related Session Status:** `docs/superpowers/session-status/2026-04-16-suboff-scale-consistency-and-report-hardening-status.md`

**Related Decision Log:** `docs/superpowers/research-decisions/2026-04-16-suboff-scale-consistency-and-report-hardening-decision-log.md`

## Finding 1

**Date:** 2026-04-16 08:52 Asia/Shanghai

**Question / Hypothesis:** Is the gigantic `Cd` in the active `suboff_solid` report a real current-code physics result, or a stale artifact from a broken geometry-scale path?

**Stage:** error analysis

**Scope / Audit Slice:** The active thread `01fec432-dead-4cb3-8c2d-09896f4fe832`, specifically its `openfoam-request.json`, `solver-results.json`, `controlDict`, and persisted `constant/triSurface/suboff_solid.stl`

**Protocol:** Inspect the persisted request/results payloads, read the generated `controlDict`, parse the persisted binary STL bounds for both the uploaded file and the case `triSurface`, and compare those results against a fresh local `run_solver_dispatch(...)` reproduction using the same binary STL plus `applied_scale_factor = 0.001`.

**Variants Compared:** stale persisted thread artifacts vs. fresh local current-code reproduction

**Metrics / Rubric:** geometry length scale in the case STL, `controlDict` reference values, and the resulting order of magnitude for `Cd`

**Human Review / Audit:** local code-and-artifact audit by the main agent

**Verified Facts:**
- The persisted active-thread `controlDict` uses meter-scale `lRef = 4.356` and `Aref = 0.370988`
- The persisted active-thread case STL was raw millimeter-scale with `length_x = 4355.94775390625`
- The persisted active-thread `solver-results.json` therefore reported a scale-inflated `latest_force_coefficients.Cd = 3073.83086`
- The current binary-STL scaling helpers in `solver_dispatch_case.py` worked in a fresh local reproduction, which wrote meter-scale binary geometry coordinates when `applied_scale_factor = 0.001`

**Open Hypotheses:**
- The stale active-thread artifacts may have been generated before the current binary-STL scaling path landed
- After a corrected rerun, the baseline drag may fall into a plausible order of magnitude without further code changes

**Negative Results / Rejected Paths:**
- Treating the huge `Cd` as a report-only problem is rejected; the persisted solver artifacts themselves were inconsistent

**Error Analysis:** The persisted artifacts mixed a meter-scale force-coefficient reference setup with a millimeter-scale body mesh, which inflated net forces and `Cd` by roughly the observed magnitude. This made the old baseline scientifically unfit for final reporting.

**Decision Impact:** Supported Decision 1: invalidate the stale result, add regression coverage for binary STL scaling, and rerun the real baseline before finalizing the report.

**Next Step / Replan Trigger:** Add the failing binary-STL regression test. Replan only if the current code fails that test or if a fresh rerun remains non-physical after the case STL is verified to be meter-scale.

## Finding 2

**Date:** 2026-04-16 10:27 Asia/Shanghai

**Question / Hypothesis:** After replacing the stale millimeter-scale case with a regenerated meter-consistent case, does the real active-thread SUBOFF baseline return to a physically plausible drag level and produce a clearer grouped report?

**Stage:** downstream check

**Scope / Audit Slice:** The same active thread `01fec432-dead-4cb3-8c2d-09896f4fe832`, but after regenerating the case, rerunning the baseline through `submarine_solver_dispatch_tool`, and refreshing `final-report.{json,md,html}` from the saved solver-dispatch snapshot

**Protocol:** 1. Regenerate the real `suboff_solid` case with the current code path. 2. Confirm the persisted `constant/triSurface/suboff_solid.stl` is meter-scale. 3. Execute the corrected baseline through the project tool path and inspect the refreshed `solver-results.json`. 4. Regenerate `final-report` from the saved runtime snapshot and inspect the grouped appendix headings in the markdown artifact.

**Variants Compared:** corrected real active-thread rerun vs. the earlier stale active-thread artifact set

**Metrics / Rubric:** case STL length scale, `Cd`, total drag force `Fx`, report appendix grouping, and regression-suite status

**Human Review / Audit:** main-agent verification plus reviewer-subagent closeout pass

**Verified Facts:**
- The regenerated active-thread `constant/triSurface/suboff_solid.stl` is meter-scale instead of millimeter-scale
- The corrected active-thread `solver-results.json` now reports `latest_force_coefficients.Cd = 0.113173151`
- The corrected active-thread `solver-results.json` now reports `latest_forces.total_force[0] = 537.9440988`
- The refreshed `final-report.md` now groups appendix content into `??????`, `???????`, and `????????`
- `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py -q` passed with `39 passed`
- The reviewer subagent returned `No findings`; only residual low-risk note was to keep fallback rendering in mind for older payloads

**Open Hypotheses:**
- The remaining `blocked_by_setup` report state is caused by incomplete planned study variants rather than a baseline-solver correctness problem
- A dedicated benchmark-aligned 3.05 m/s run may be needed for direct comparison against the cited EFD reference

**Negative Results / Rejected Paths:**
- Keeping the old `Cd ~3073` result as the active baseline is rejected
- Keeping the report appendix as a flat, unguided manifest list is rejected

**Error Analysis:** The scale bug was eliminated for the active baseline, but the report still honestly surfaces missing study-variant evidence and benchmark-scope mismatch. That means the current limitation has shifted from ?baseline numerics are obviously wrong? to ?scientific completeness is still partial.?

**Decision Impact:** Confirms Decision 1 and supports keeping the grouped appendix structure as the new default for the active report path.

**Next Step / Replan Trigger:** If the project wants research-grade claim levels instead of delivery-only claim levels, continue with sensitivity-study execution and/or a benchmark-aligned reference condition; replan only if those follow-on runs expose a new physics/configuration mismatch.
