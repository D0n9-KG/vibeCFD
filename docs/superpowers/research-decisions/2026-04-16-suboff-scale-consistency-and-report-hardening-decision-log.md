# SUBOFF Scale Consistency And Report Hardening Decision Log

**Status:** active

**Related Plan:** `docs/superpowers/plans/2026-04-16-suboff-scale-consistency-and-report-hardening.md`

**Related Session Status:** `docs/superpowers/session-status/2026-04-16-suboff-scale-consistency-and-report-hardening-status.md`

## Decision 1

**Date:** 2026-04-16 08:52 Asia/Shanghai

**Topic:** Treat the persisted `Cd ~3073` SUBOFF result as invalid stale evidence until the baseline is regenerated with current code.

**Context:** The active-thread `solver-results.json` reports `Cd = 3073.83086`. Inspection showed the persisted `controlDict` uses meter-scale `lRef` and `Aref`, while the persisted `constant/triSurface/suboff_solid.stl` remains raw millimeter-scale (`length_x = 4355.94775390625`). A fresh local reproduction through current `run_solver_dispatch(...)` writes scaled binary STL coordinates correctly, so the persisted artifacts cannot be treated as authoritative for current-code behavior.

**Options Considered:**
- Assume the huge `Cd` is only a report-rendering issue and continue polishing the report
- Treat the stale solver artifacts as valid and explain the huge force as a CFD-modeling limitation
- Invalidate the stale result, add binary-STL regression coverage, rerun the real baseline, and only then finalize report structure

**Decision:** Invalidate the stale `Cd ~3073` result, protect binary STL scale propagation with regression tests, and require a corrected rerun before shipping the updated report.

**Why This Won:** The user explicitly questioned the physical credibility of the result. The evidence shows the old artifacts are not meter-consistent, while the current code path locally reproduces correct binary scaling. Shipping or polishing the report without correcting the baseline would preserve a scientifically misleading deliverable.

**Why Not The Others:** Report-only polish would hide a real trust problem. Treating the huge `Cd` as a legitimate CFD outcome would ignore the demonstrated unit inconsistency between case geometry and reference values.

**Consequences / Follow-On Work:** Execution must add binary-STL regression coverage, regenerate the real `suboff_solid` baseline, and clearly separate corrected current outputs from stale historical ones in the report.

**Re-evaluation Trigger:** Reopen this decision if a fresh rerun with the current code still yields a scale-inflated drag coefficient after the case STL is verified to be meter-scale.
