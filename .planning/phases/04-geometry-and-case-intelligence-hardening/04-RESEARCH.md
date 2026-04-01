# Phase 4: Geometry and Case Intelligence Hardening - Research

**Researched:** 2026-04-01
**Domain:** Placeholder scaffold for geometry preflight and case-library hardening
**Confidence:** LOW

<user_constraints>
## User Constraints (from ROADMAP.md / REQUIREMENTS.md)

- GEO-01: geometry preflight detects STL integrity, unit/scale anomalies, and reference assumptions.
- GEO-02: case-library entries use real references and explicit acceptance profiles.
- GEO-03: ambiguous or non-research-ready geometries are downgraded or blocked with clear justification.

</user_constraints>

<research_summary>
## Summary

Detailed research has not been performed yet. Future work should replace this scaffold with concrete geometry checks, case-library sourcing rules, and operator guidance for unsupported setups.

Default assumption until deeper research says otherwise: keep the current submarine workflow and insert stronger geometry/case gates before solver execution.

</research_summary>

<standard_stack>
## Standard Stack

- **Geometry inputs:** current STL-based upload flow
- **Runtime integration:** DeerFlow submarine tools and canonical artifact outputs
- **Workbench surface:** submarine cockpit status, artifact rail, and report loop

</standard_stack>

<validation_architecture>
## Validation Architecture

Populate before first plan with:

- automated tests for STL sanity, unit/scale inference, and block/downgrade logic
- curated benchmark geometry fixtures with known good/bad expectations
- browser or report checks proving users see geometry/case trust decisions clearly

</validation_architecture>

<sources>
## Sources

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/phases/02-runtime-solver-productization/02-02-SUMMARY.md`

</sources>

<metadata>
## Metadata

**Research date:** 2026-04-01
**Valid until:** replace after real research
**Status:** scaffold only

</metadata>

---

*Phase: 04-geometry-and-case-intelligence-hardening*
*Research scaffolded: 2026-04-01*
