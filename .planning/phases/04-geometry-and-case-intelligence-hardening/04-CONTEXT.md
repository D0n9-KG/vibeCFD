# Phase 4: Geometry and Case Intelligence Hardening - Context

**Gathered:** 2026-04-01
**Status:** Scaffolded for future planning

<domain>
## Phase Boundary

Improve geometry trust, scale assumptions, and case knowledge so researchers receive defensible setup recommendations before solving.

- **Depends on:** Phase 2 runtime solver productization
- **Requirements:** GEO-01, GEO-02, GEO-03
- **Goal:** geometry preflight catches integrity and scale issues, case-library entries rely on real references, and ambiguous setups are blocked or downgraded clearly

This file is a scaffold for later GSD planning and research.

</domain>

<decisions>
## Implementation Decisions

### Locked by roadmap
- Geometry preflight must catch STL integrity, unit/scale anomalies, and reference-value assumptions.
- Case-library entries must use real references and explicit acceptance profiles.
- Non-research-ready or ambiguous geometries must be downgraded or blocked with clear justification.

### The Agent's Discretion
- Exact geometry heuristics and tolerance thresholds
- Case-library schema details
- User-facing downgrade and block messaging

</decisions>

<specifics>
## Specific Ideas

- Turn geometry preflight into a real gate instead of a descriptive warning.
- Treat case-library provenance as scientific evidence, not convenience metadata.
- Reuse runtime and reporting contracts so blocked geometry decisions remain traceable.

</specifics>

<canonical_refs>
## Canonical References

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/phases/02-runtime-solver-productization/02-02-SUMMARY.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- STEP and Parasolid native intake
- automatic geometry cleanup and repair pipelines

</deferred>

---

*Phase: 04-geometry-and-case-intelligence-hardening*
*Context scaffolded: 2026-04-01*
