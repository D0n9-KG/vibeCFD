# VibeCFD

## What This Is

VibeCFD is a DeerFlow-native submarine CFD workbench for researchers. A researcher can describe a study, upload geometry, confirm a calculation plan, run OpenFOAM through the DeerFlow runtime path, and inspect evidence-backed results in the dedicated cockpit. Phases 1 through 4 are now complete: bootstrap, runtime execution, scientific verification gates, and geometry/case-intelligence hardening are in place. The remaining work is Phase 5 reproducibility/experiment ops and Phase 6 researcher delivery/supervisor polish.

## Core Value

A researcher can go from natural-language CFD intent to reproducible, evidence-backed submarine results without manually building and operating OpenFOAM cases.

## Requirements

### Validated

- Dedicated submarine workbench UI and DeerFlow-native domain workflow exist - brownfield baseline
- Submarine tools generate design brief, geometry check, solver dispatch, reporting, and scientific follow-up artifacts - brownfield baseline
- Project-local OpenFOAM sandbox image and config exist, and generated case scaffolds can execute in container - brownfield baseline
- Researchers can start a new study from `/workspace/submarine/new`, preserve the STL and first prompt across route transition/refresh, and continue clarification inside the dedicated cockpit - Phase 1
- Solver execution, canonical runtime artifacts, refresh-safe runtime recovery, and requested post-processing outputs flow through the DeerFlow runtime path - Phase 2
- Scientific claim level is explicitly gated by stability evidence, sensitivity-study workflow status, and benchmark-backed comparisons - Phase 3
- Geometry trust, case provenance, and researcher approval now form an explicit pre-compute setup gate instead of hidden heuristics - Phase 4
- Phase 4 calculation-plan review, solver-hold messaging, and reviewer CTAs are now live-browser validated on a deterministic workbench fixture - Phase 4

### Active

- [ ] Persist full experiment provenance, baseline-vs-variant linkage, and environment consistency for reproducible studies - Phase 5
- [ ] Deliver the final researcher-facing report and supervisor review loop with guided rerun/follow-up actions - Phase 6

### Out of Scope

- General-purpose all-domain CAE expansion in this milestone - keep the effort focused on submarine CFD until the research loop is solid
- Native STEP/Parasolid-first workflow in this milestone - STL is still the operational baseline
- Free-surface or multiphase submarine workflows in this milestone - current support remains placeholder-level
- HPC scheduler integration in this milestone - local and Docker-backed reproducibility must work first

## Context

- Tech environment: Next.js frontend, DeerFlow/LangGraph backend, Docker Desktop runtime, and a project-local OpenFOAM sandbox image
- The active product path is now the dedicated submarine cockpit plus persisted `submarine_runtime`, not an ad-hoc shell-only execution flow
- Runtime artifacts already encode operational status, scientific verification state, research evidence, and supervisor-gate consequences
- Geometry preflight now emits structured trust findings; case recommendations now carry provenance; ambiguous setup assumptions now block execution pending researcher approval
- Deterministic mock review threads now support in-workbench clarify, approve, and rerun CTA validation without requiring a real solver launch
- The next bottleneck is reproducibility: experiment manifests, baseline-vs-variant provenance, and environment consistency still need productization in Phase 5

## Constraints

- **Architecture**: DeerFlow remains the primary orchestration runtime - fixes should strengthen, not bypass, the intended agent/tool flow
- **Runtime**: OpenFOAM execution happens inside Docker/sandbox environments - researcher UX must line up with that deployment path
- **Scientific Integrity**: The system must not overclaim results beyond recorded evidence - scientific claim levels and approval gates stay explicit
- **Input Format**: v1 operational geometry path is STL-first - non-STL geometry remains outside this milestone
- **Brownfield**: Existing working domain modules and tests should be preserved while closing integration gaps

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep DeerFlow as the sole runtime path for submarine CFD orchestration | Splitting runtime logic would reduce traceability, recovery, and cockpit visibility | Good |
| Treat "research usable" as evidence-backed, not merely runnable | Artifact production alone is insufficient for scientific use | Good |
| Keep bootstrap failures and missing-input negotiation inside the submarine cockpit | Recovery paths must stay in the same dedicated research workbench | Good |
| Mirror operational runtime state and scientific state into persisted `submarine_runtime` | Refresh-safe UI should not reconstruct critical truth from stage order alone | Good |
| Treat geometry trust as a structured contract and researcher approval as a separate pre-compute gate | Raw heuristics and claim-level wording were both too easy to over-trust without explicit contracts | Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? Move them to Out of Scope with reason.
2. Requirements validated? Move them to Validated with a phase reference.
3. New requirements emerged? Add them to Active.
4. Decisions to log? Add them to Key Decisions.
5. "What This Is" still accurate? Update it if reality drifts.

**After each milestone:**
1. Review all sections against the shipped system.
2. Re-check whether Core Value is still the right prioritization anchor.
3. Audit Out of Scope items and confirm the reasons still hold.
4. Refresh Context with the latest workflow, runtime, and user evidence.

---
*Last updated: 2026-04-02 after Phase 4 browser validation completion*
