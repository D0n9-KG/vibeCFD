---
phase: 04-geometry-and-case-intelligence-hardening
plan: 02
subsystem: case-provenance-and-acceptance-profile
tags: [submarine, case-library, provenance, acceptance-profile, reporting, backend]
requires:
  - phase: 04-01
    provides: "Structured geometry trust and calculation-plan scaffolding for downstream recommendations"
provides:
  - "Case-library entries with explicit source labels, source types, applicability conditions, confidence notes, and placeholder disclosure"
  - "Selected-case provenance summaries that survive into result reporting"
  - "Active case acceptance profiles that distinguish benchmark-backed and advisory-only recommendations"
affects: [phase-04-geometry-and-case-intelligence-hardening, phase-05-experiment-ops-and-reproducibility, phase-06-research-delivery-workbench]
tech-stack:
  added: []
  patterns:
    - "Keep weak-reference cases visible, but label them as placeholders or evidence-limited advisory options instead of letting ranking hide the weakness."
    - "Carry selected-case provenance into final report payloads so researchers can inspect why a recommendation is strong, weak, or benchmark-limited."
key-files:
  created:
    - .planning/phases/04-geometry-and-case-intelligence-hardening/04-02-SUMMARY.md
  modified:
    - backend/packages/harness/deerflow/domain/submarine/library.py
    - backend/packages/harness/deerflow/domain/submarine/models.py
    - backend/packages/harness/deerflow/domain/submarine/reporting.py
    - backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py
    - backend/tests/test_submarine_domain_assets.py
    - backend/tests/test_submarine_result_report_tool.py
    - domain/submarine/cases/index.json
key-decisions:
  - "Placeholder-backed cases remain available only with explicit `is_placeholder` and evidence-gap disclosure."
  - "Case ranking now preserves provenance detail in the payload instead of treating score alone as the researcher-facing explanation."
patterns-established:
  - "Use one provenance vocabulary across the case index, ranking layer, and final-report summaries."
  - "Separate 'no benchmark available yet' from 'benchmark available but failed' in the reporting contract."
requirements-completed: [GEO-02]
duration: "~1h across case-library curation and report synthesis updates"
completed: 2026-04-02
---

# Phase 4: Geometry and Case Intelligence Hardening Plan 02 Summary

**The submarine case library now exposes provenance and acceptance-profile honesty directly in ranked-case and final-report payloads instead of hiding weak references behind lexical ranking alone.**

## Performance

- **Duration:** ~1 h across case metadata, ranking, and reporting updates
- **Completed:** 2026-04-02T14:42:05+08:00
- **Tasks:** 3 planned case-provenance tasks
- **Files modified:** 7

## Accomplishments

- Extended case and reference models with `source_label`, `source_type`, `applicability_conditions`, `confidence_note`, `is_placeholder`, and `evidence_gap_note`.
- Hardened `domain/submarine/cases/index.json` so active entries no longer rely on placeholder URLs without explicit disclosure.
- Upgraded case ranking and normalization so candidate-case payloads carry provenance detail beyond `score` and `rationale`.
- Added `selected_case_provenance_summary` and related evidence-gap fields to report synthesis so researchers can see why a selected case is benchmark-backed or advisory-only.
- Strengthened active acceptance profiles for the recommended submarine cases and distinguished missing benchmark coverage from failed validation in result-report assertions.

## Verification

- `cd backend && uv run pytest tests/test_submarine_domain_assets.py tests/test_submarine_result_report_tool.py`
  - Result: passed (`46 passed`)

## Task Commits

This plan was completed in the existing dirty workspace without a separate commit in this turn. Summary/state updates serve as the checkpoint.

## Files Created/Modified

- `domain/submarine/cases/index.json` - upgrades the case-library source of truth with provenance fields, placeholder disclosure, and stronger active acceptance-profile metadata.
- `backend/packages/harness/deerflow/domain/submarine/models.py` - extends case/reference models for provenance disclosure.
- `backend/packages/harness/deerflow/domain/submarine/library.py` - emits provenance-aware candidate-case payloads during ranking.
- `backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py` - builds selected-case provenance and evidence-gap summaries.
- `backend/packages/harness/deerflow/domain/submarine/reporting.py` - includes selected-case provenance in researcher-facing report payloads.
- `backend/tests/test_submarine_domain_assets.py` - locks case-index provenance and placeholder disclosure rules.
- `backend/tests/test_submarine_result_report_tool.py` - locks weak-reference disclosure and benchmark-limited reporting behavior.

## Decisions Made

- Advisory and placeholder-backed cases remain useful for discovery, but only when their evidence limits are explicit.
- Provenance should travel with the selected case all the way into the report contract, not stay trapped in the index or ranking layer.

## Deviations from Plan

- None. The planned work completed without additional scope beyond test-alignment updates already captured in the modified test files.

## Issues Encountered

- The active case library had mixed evidence quality, so the main implementation work was standardizing disclosure without deleting useful but weak advisory cases.

## User Setup Required

None for automated verification.

## Next Phase Readiness

- Plan `04-02` is complete: case provenance and acceptance-profile detail are now available for calculation-plan review and reporting.
- The next logical step is `04-03`, which turns geometry and case ambiguity into explicit researcher approval and clarification flows in both backend state and cockpit UI.

---
*Phase: 04-geometry-and-case-intelligence-hardening*
*Completed: 2026-04-02*
