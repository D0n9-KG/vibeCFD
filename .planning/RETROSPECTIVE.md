# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 - MVP

**Shipped:** 2026-04-03
**Phases:** 6 | **Plans:** 18 | **Sessions:** not formally tracked

### What Was Built

- Restored the end-to-end submarine workbench bootstrap so a real STL-backed prompt creates a thread and survives refresh.
- Productized runtime execution, scientific gates, geometry trust, provenance, and runtime parity into one refresh-safe DeerFlow path.
- Shipped conclusion-first Chinese reporting, supervisor decision summaries, and bounded follow-up lineage in the dedicated workbench.

### What Worked

- Phase-by-phase decomposition kept runtime, science, geometry, reproducibility, and delivery changes understandable instead of landing as one large cross-cutting rewrite.
- Deterministic mock threads made browser validation repeatable across phases 2, 3, 4, and 6.
- Keeping backend contracts, persisted runtime snapshots, and cockpit render paths aligned reduced late integration surprises.

### What Was Inefficient

- Verification and validation artifacts needed end-of-milestone backfill in several phases instead of being kept continuously current.
- UTC-based milestone automation output required manual date normalization back to local planning time.
- Late audit cleanup surfaced a few residual regressions and test gaps after the main feature work was already complete.

### Patterns Established

- Treat scientific truth, operator approval, and reproducibility parity as separate but linked contracts.
- Prefer one canonical provenance anchor per run and reuse it everywhere: reducers, reports, and cockpit summaries.
- When a phase changes user-visible state, lock the backend contract, persisted snapshot, and workbench rendering path in the same phase.

### Key Lessons

1. Milestone closeout goes much faster when `VERIFICATION.md` and `VALIDATION.md` stay current during the phase, not after it.
2. Deterministic UI fixtures are excellent for iteration speed, but they should be paired with live non-mock validation before calling the milestone fully clean.

### Cost Observations

- Most implementation cost concentrated in phases 3 through 5, where scientific evidence, provenance, and cross-surface consistency intersected.
- The biggest late cost came from audit-style closure work rather than net-new feature code.
- A small amount of structured planning debt remained even though the shipped product scope itself was complete.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | not tracked | 6 | Established the full submarine CFD milestone flow from bootstrap through delivery review |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | Backend and frontend regression suites green for shipped flows | Not formally tracked | 0 |

### Top Lessons (Verified Across Milestones)

1. Shared contracts across backend state, reports, and cockpit UI prevent most late integration drift.
2. Mock-thread validation is powerful, but milestone readiness still benefits from a live-thread proof pass on critical flows.
