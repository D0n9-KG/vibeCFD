# Phase 5: Experiment Ops and Reproducibility - Context

**Gathered:** 2026-04-01
**Status:** Scaffolded for future planning

<domain>
## Phase Boundary

Give researchers a reproducible study system with provenance, comparison structure, and consistent environments.

- **Depends on:** Phase 3 scientific verification gates and Phase 4 geometry/case hardening
- **Requirements:** OPS-01, OPS-02, OPS-03
- **Goal:** every run is rerunnable, baseline-versus-variant studies become first-class artifacts, and runtime configuration stays aligned across environments

This file is a scaffold for later planning.

</domain>

<decisions>
## Implementation Decisions

### Locked by roadmap
- Every run must record reproducible provenance for geometry, template, solver settings, runtime environment, and outputs.
- Baseline-versus-variant comparisons must be explicit artifacts instead of ad hoc manual bookkeeping.
- Local dev, Docker Compose, and deployment runtime configuration must be aligned and documented.

### The Agent's Discretion
- Manifest schema design
- Comparison workflow UX
- Environment parity enforcement and drift detection

</decisions>

<specifics>
## Specific Ideas

- Reuse canonical artifact pointers and scientific evidence outputs as provenance anchors.
- Treat experiment manifests as durable domain objects, not report-only metadata.
- Link environment fingerprints to each study so reruns are explainable.

</specifics>

<canonical_refs>
## Canonical References

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/phases/03-scientific-verification-gates/03-CONTEXT.md`
- `.planning/phases/04-geometry-and-case-intelligence-hardening/04-CONTEXT.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- HPC and scheduler integration
- advanced queue orchestration for large study batches

</deferred>

---

*Phase: 05-experiment-ops-and-reproducibility*
*Context scaffolded: 2026-04-01*
