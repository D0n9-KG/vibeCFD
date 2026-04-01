# VibeCFD

## What This Is

VibeCFD is a DeerFlow-native submarine CFD workbench for researchers. A researcher should be able to describe a study, upload geometry and constraints, and let the main agent drive brief confirmation, geometry preflight, OpenFOAM execution, post-processing, and report generation. Phase 1 has now restored the real workbench bootstrap path, but runtime execution, scientific evidence gates, and researcher-facing delivery still need productization before the platform is truly research-ready.

## Core Value

A researcher can go from natural-language CFD intent to reproducible, evidence-backed submarine results without manually building and operating OpenFOAM cases.

## Requirements

### Validated

- Dedicated submarine workbench UI and DeerFlow-native domain workflow exist - brownfield baseline
- Submarine tools already generate design brief, geometry check, solver dispatch, reporting, and scientific follow-up artifacts - brownfield baseline
- Project-local OpenFOAM sandbox image and config exist, and generated case scaffolds can execute in container - brownfield baseline
- Core submarine backend tests currently pass, providing a stable domain-layer starting point - brownfield baseline
- Researchers can start a new study from `/workspace/submarine/new`, preserve the STL and first prompt across route transition/refresh, and continue clarification inside the dedicated cockpit - Phase 1

### Active

- [ ] Productize solver execution and artifact capture through the DeerFlow runtime, not just offline scaffolding
- [ ] Raise claim level from `delivery_only` toward `research_ready` via explicit scientific verification evidence
- [ ] Harden geometry normalization, case knowledge, and provenance for reproducible studies
- [ ] Deliver a researcher-facing report and supervisor review workflow that can safely block, rerun, or extend studies

### Out of Scope

- General-purpose all-domain CAE expansion in this milestone - keep the effort focused on submarine CFD until the research loop is solid
- Native STEP/Parasolid-first workflow in this milestone - current operational baseline is STL-only and must be stabilized first
- Free-surface or multiphase submarine workflows in this milestone - existing support is placeholder-level and not ready for research claims
- HPC scheduler integration in this milestone - local and Docker-backed reproducibility must work before cluster orchestration

## Context

- Tech environment: Next.js frontend, DeerFlow/LangGraph backend, Docker Desktop runtime, and a project-local OpenFOAM sandbox image
- Phase 1 outcome on 2026-04-01: `/workspace/submarine/new` now creates a real submarine thread, binds uploads, survives refresh, and keeps clarification inside the submarine cockpit
- Existing domain coverage is submarine-first: design brief, geometry preflight, solver dispatch, result reporting, scientific remediation, and follow-up contracts
- Current report artifacts already encode scientific gates that can block claim level when evidence is incomplete
- Case-library depth and source quality are uneven; most non-SUBOFF entries still rely on placeholder references
- Runtime solver execution is still not fully productized through the live DeerFlow workbench path, so Phase 2 remains the immediate bottleneck

## Constraints

- **Architecture**: DeerFlow remains the primary orchestration runtime - fixes should strengthen, not bypass, the intended agent/tool flow
- **Runtime**: OpenFOAM execution happens inside Docker/sandbox environments - researcher UX must line up with that deployment path
- **Scientific Integrity**: The system must not overclaim results beyond recorded evidence - claim levels and remediation gates stay explicit
- **Input Format**: v1 operational geometry path is STL-only - non-STL geometry remains outside this milestone
- **Brownfield**: Existing working domain modules and tests should be preserved while closing integration gaps - avoid rewrites that discard current momentum

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep DeerFlow as the sole runtime path for submarine CFD orchestration | The replatform already centers on DeerFlow, and splitting runtime logic would reduce traceability | Good |
| Treat "research usable" as evidence-backed, not merely runnable | The current code can generate artifacts and even execute cases, but claim level is still blocked without verification evidence | Good |
| Prioritize end-to-end workbench bootstrap before expanding capabilities | The top blocker was that a user could not reliably start a real run from the submarine workbench | Good |
| Use `deer-flow-openfoam-sandbox:latest` as the local CFD execution baseline | This image is configured in `config.yaml` and can execute the generated OpenFOAM scaffold | Good |
| Keep the current milestone focused on submarine CFD, not generalized CFD domains | Narrowing scope is necessary to reach research-grade quality in one domain first | Good |
| Keep bootstrap failures and missing-input negotiation inside the dedicated submarine cockpit rather than redirecting to generic chat | The product promise is a dedicated research workbench, so recovery paths must stay in the same cockpit | Good |
| Make clarification middleware safe under Windows/GBK consoles | Real operator prompts can contain non-ASCII scientific notation such as `m³/s`, and that must never abort the user flow | Good |

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
*Last updated: 2026-04-01 after Phase 1 verification and transition preparation*
