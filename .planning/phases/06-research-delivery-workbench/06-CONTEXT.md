# Phase 6: Research Delivery Workbench - Context

**Gathered:** 2026-04-01
**Status:** Scaffolded for future planning

<domain>
## Phase Boundary

Complete the researcher-facing delivery loop with reports, supervisor gate decisions, and guided follow-up actions.

- **Depends on:** Phase 3 scientific verification gates and Phase 5 experiment ops and reproducibility
- **Requirements:** RPT-01, RPT-02
- **Goal:** final reports package evidence in Chinese, supervisor review becomes an actionable cockpit surface, and users can navigate from conclusions back to artifacts and reruns

This file is a scaffold for later planning.

</domain>

<decisions>
## Implementation Decisions

### Locked by roadmap
- Final reports must package coefficients, plots, figures, claim level, evidence gaps, and follow-up recommendations in Chinese.
- Supervisor review must support approve, block, rerun, or extend actions.
- Users must be able to navigate from report conclusions back to underlying artifacts and rerun paths.

### The Agent's Discretion
- Report structure and visual design details
- Review workflow and action model
- Artifact-to-conclusion navigation affordances

</decisions>

<specifics>
## Specific Ideas

- Treat reports as evidence-indexed deliverables rather than static summaries.
- Preserve links from every conclusion to runtime evidence and verification history.
- Make follow-up actions first-class workbench controls instead of prose-only suggestions.

</specifics>

<canonical_refs>
## Canonical References

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/phases/03-scientific-verification-gates/03-CONTEXT.md`
- `.planning/phases/05-experiment-ops-and-reproducibility/05-CONTEXT.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- multi-report export formats beyond the core milestone deliverables
- broader non-submarine delivery templates

</deferred>

---

*Phase: 06-research-delivery-workbench*
*Context scaffolded: 2026-04-01*
