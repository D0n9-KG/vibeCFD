---
phase: 04-geometry-and-case-intelligence-hardening
plan: 01
subsystem: geometry-trust-preflight
tags: [submarine, geometry, scale-assessment, reference-values, calculation-plan, backend]
requires:
  - phase: 02-03
    provides: "Refresh-safe runtime truth and persisted submarine runtime snapshots"
provides:
  - "Structured geometry findings, scale assessment, and reference-value suggestions in geometry preflight outputs"
  - "Solver-dispatch reference inputs that respect geometry trust instead of silently trusting estimated length alone"
  - "Runtime-visible geometry ambiguity that can force confirmation before execution"
affects: [phase-04-geometry-and-case-intelligence-hardening, phase-05-experiment-ops-and-reproducibility, phase-06-research-delivery-workbench]
tech-stack:
  added:
    - backend/packages/harness/deerflow/domain/submarine/calculation_plan.py
  patterns:
    - "Emit machine-actionable geometry trust artifacts once during preflight, then let runtime gating and solver dispatch consume the same structured data."
    - "Treat geometry-derived reference values as suggestions with explicit confidence and confirmation requirements, not as silent defaults."
key-files:
  created:
    - .planning/phases/04-geometry-and-case-intelligence-hardening/04-01-SUMMARY.md
    - backend/packages/harness/deerflow/domain/submarine/calculation_plan.py
  modified:
    - backend/packages/harness/deerflow/domain/submarine/contracts.py
    - backend/packages/harness/deerflow/domain/submarine/design_brief.py
    - backend/packages/harness/deerflow/domain/submarine/geometry_check.py
    - backend/packages/harness/deerflow/domain/submarine/models.py
    - backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py
    - backend/packages/harness/deerflow/domain/submarine/solver_dispatch_case.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py
    - backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py
    - backend/tests/test_submarine_geometry_check_tool.py
    - backend/tests/test_submarine_runtime_context.py
    - backend/tests/test_submarine_solver_dispatch_tool.py
key-decisions:
  - "Geometry trust is now a structured contract with findings, scale assessment, and reference-value suggestions instead of a human-only summary string."
  - "Solver dispatch can only consume geometry reference inputs from qualified low-risk suggestions or researcher-approved calculation-plan items."
patterns-established:
  - "Centralize calculation-plan normalization and confirmation helpers in a shared backend module so design brief, geometry preflight, runtime context, and dispatch stay aligned."
  - "Model severe geometry ambiguity as execution gating state rather than letting heuristics silently advance the pipeline."
requirements-completed: [GEO-01]
duration: "~1.5h across backend hardening and regression updates"
completed: 2026-04-02
---

# Phase 4: Geometry and Case Intelligence Hardening Plan 01 Summary

**Geometry preflight now emits explicit trust artifacts and solver-dispatch respects them instead of turning raw STL heuristics directly into solver reference values.**

## Performance

- **Duration:** ~1.5 h across backend domain, tool, and regression updates
- **Completed:** 2026-04-02T14:42:05+08:00
- **Tasks:** 3 planned geometry-hardening tasks
- **Files modified:** 12 plus 1 new shared helper module

## Accomplishments

- Added structured geometry trust payloads for `geometry_findings`, `scale_assessment`, `reference_value_suggestions`, and `clarification_required`.
- Hardened STL preflight so empty meshes, zero-size bounds, divide-by-1000 scale guesses, and strong family-length mismatches become explicit findings instead of buried summary text.
- Introduced shared calculation-plan helpers so geometry and design-brief inputs merge into one persisted plan with consistent confirmation semantics.
- Refactored solver-dispatch preparation so `reference_length_m` and `reference_area_m2` are derived from trusted geometry suggestions or confirmed calculation-plan inputs.
- Updated runtime-context gating to keep severe geometry ambiguity in `needs_user_confirmation` and route the next stage to `user-confirmation` when appropriate.
- Refreshed backend regression coverage around low-risk suggestions, severe scale mismatch, and geometry-driven confirmation blocks.

## Verification

- `cd backend && uv run pytest tests/test_submarine_geometry_check_tool.py tests/test_submarine_runtime_context.py tests/test_submarine_solver_dispatch_tool.py`
  - Result: passed
- `cd backend && uv run pytest tests/test_submarine_design_brief_tool.py tests/test_submarine_geometry_check_tool.py tests/test_submarine_runtime_context.py tests/test_submarine_solver_dispatch_tool.py`
  - Result: passed (`49 passed`)

## Task Commits

This plan was completed in the existing dirty workspace without per-task commits in this turn. The summary and planning-state updates are the completion checkpoint.

## Files Created/Modified

- `backend/packages/harness/deerflow/domain/submarine/calculation_plan.py` - adds shared normalization, merge, confirmation, and geometry/design-brief calculation-plan builders.
- `backend/packages/harness/deerflow/domain/submarine/models.py` - extends submarine models with structured geometry trust and calculation-plan fields.
- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - exposes geometry trust and calculation-plan state through runtime-visible contracts.
- `backend/packages/harness/deerflow/domain/submarine/geometry_check.py` - emits structured findings, scale assessment, and reference suggestions.
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_case.py` - derives solver reference inputs from trusted geometry suggestions.
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` - blocks or downgrades execution when calculation-plan or geometry trust is still pending.
- `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py` - persists geometry trust data and calculation-plan carry-over into runtime snapshots.
- `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py` - treats pending calculation-plan items as a first-class confirmation gate.
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py` - preserves calculation-plan and geometry trust state during dispatch.
- `backend/tests/test_submarine_geometry_check_tool.py` - locks structured geometry trust outputs and ambiguity branches.
- `backend/tests/test_submarine_runtime_context.py` - locks geometry-driven confirmation behavior.
- `backend/tests/test_submarine_solver_dispatch_tool.py` - locks low-risk and blocked geometry reference-input paths.

## Decisions Made

- Geometry preflight is now the authoritative place to establish geometry trust instead of deferring interpretation until solver dispatch.
- Calculation-plan confirmation is the shared execution gate for geometry ambiguity as well as later case-provenance review.
- Low-risk geometry suggestions may stay visible, but they no longer silently become solver inputs without a traceable trust path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Shared Logic Extraction] Calculation-plan rules were duplicated across multiple backend paths**

- **Found during:** backend implementation pass
- **Issue:** Design brief, geometry preflight, runtime context, and solver dispatch all needed the same merge/confirmation semantics for plan items.
- **Fix:** Extracted the shared behavior into `backend/packages/harness/deerflow/domain/submarine/calculation_plan.py`.
- **Verification:** `uv run pytest tests/test_submarine_design_brief_tool.py tests/test_submarine_geometry_check_tool.py tests/test_submarine_runtime_context.py tests/test_submarine_solver_dispatch_tool.py`

---

**Total deviations:** 1 auto-fixed (shared logic extraction)
**Impact on plan:** Reduced drift risk and kept the new geometry trust gate consistent across all backend entry points.

## Issues Encountered

- The new calculation-plan semantics cut across several existing backend tools, so shared helper extraction was necessary to avoid rule drift.

## User Setup Required

None for automated verification.

## Next Phase Readiness

- Plan `04-01` is complete: geometry preflight now produces trust artifacts the rest of the phase can build on.
- The next logical step is `04-02`, which hardens case-library provenance and acceptance-profile honesty on top of the stronger geometry gate.

---
*Phase: 04-geometry-and-case-intelligence-hardening*
*Completed: 2026-04-02*
