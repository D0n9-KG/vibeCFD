# VibeCFD

## What This Is

VibeCFD is a DeerFlow-native submarine CFD workbench for researchers. A researcher can start a study from the dedicated submarine workspace, upload STL geometry, confirm the calculation plan, run OpenFOAM through the DeerFlow runtime path, and review conclusion-first results with scientific evidence, provenance, reproducibility guidance, and supervisor follow-up context. `v1.0` shipped this end-to-end loop.

## Core Value

A researcher can go from natural-language CFD intent to reproducible, evidence-backed submarine results without manually building and operating OpenFOAM cases.

## Current State

- `v1.0 MVP` shipped on 2026-04-03 and is archived under `.planning/milestones/`
- All six milestone phases are complete: bootstrap, runtime execution, scientific verification, geometry and case intelligence, reproducibility, and research delivery
- Milestone audit verdict is `tech_debt`: the product is shipped, with only non-blocking follow-up around live-thread validation depth and residual mock-workspace cleanup
- `v1.1 Experience & Platform` is now the active planning milestone

## Current Milestone: v1.1 Experience & Platform

**Goal:** Turn the shipped submarine CFD loop into a clearer, safer, and more extensible DeerFlow-aligned product by overhauling workspace UX, productizing skill lifecycle management, hardening deployment isolation, and cleaning up architecture boundaries.

**Target features:**
- Coherent workspace information architecture, layout system, and responsive page redesign across submarine, chat, and skill surfaces
- Full-chain Vibe CFD skill creation, validation, publish, auto-configuration, and revision management around the DeerFlow skill model
- Server-ready Docker and sandbox isolation for lead agent, subagents, and OpenFOAM execution with safer deployment boundaries
- Frontend and backend structural cleanup so core workbench surfaces stop depending on oversized, tightly coupled modules

## Requirements

### Validated

- Dedicated submarine workbench UI and DeerFlow-native domain workflow exist - brownfield baseline
- Submarine tools now cover design brief, geometry check, solver dispatch, reporting, and scientific follow-up artifacts - brownfield baseline
- Project-local OpenFOAM sandbox image and runtime config exist, and the supported case scaffolds can execute in container - brownfield baseline
- Researchers can start a new study from `/workspace/submarine/new`, preserve STL plus first prompt across route transition and refresh, and continue in the dedicated cockpit - `v1.0` Phase 1
- Solver execution, canonical runtime artifacts, and refresh-safe runtime recovery now flow through the DeerFlow runtime path - `v1.0` Phase 2
- Scientific claim levels now depend on explicit stability, sensitivity-study, and benchmark evidence - `v1.0` Phase 3
- Geometry trust, case provenance, and researcher approval now act as an explicit pre-compute gate - `v1.0` Phase 4
- Provenance manifests, experiment linkage, and runtime parity now support reproducible studies - `v1.0` Phase 5
- Final Chinese delivery, supervisor decision summaries, and bounded follow-up lineage are now live in the workbench - `v1.0` Phase 6

### Active

- [ ] Redesign the workspace UX and layout system so core pages feel intentional, readable, and easier to operate
- [ ] Turn skill studio into a full lifecycle management surface for Vibe CFD skills, not just a draft-package generator
- [ ] Align deployment with DeerFlow's Docker and sandbox model so server execution is isolated and safer by default
- [ ] Reduce architectural sprawl in oversized frontend and backend modules while keeping shared contracts stable
- [ ] Close the remaining `v1.0` live-validation and mock-surface debt during release hardening

### Out of Scope

- General-purpose all-domain CAE expansion until the submarine CFD loop remains stable
- Native STEP/Parasolid-first workflow until the STL path is no longer the operational bottleneck
- Free-surface or multiphase submarine workflows until the current resistance-style loop has stronger live validation
- HPC scheduler integration until local and Docker-backed reproducibility plus operator workflows are stable
- Multi-tenant marketplace, billing, or organization-wide RBAC until the single-team product workflow is clean and stable

## Context

- Tech environment: Next.js frontend, DeerFlow/LangGraph backend, Docker Desktop runtime, and a project-local OpenFOAM sandbox image
- `v1.0` shipped the dedicated cockpit path end to end; runtime truth, scientific gate state, provenance, and delivery review all survive refresh and reporting
- Deterministic mock threads now cover critical workbench flows across phases 2, 3, 4, and 6
- The project already contains skill studio, skills API, sandbox config, and Docker stack foundations, but the UX and lifecycle management still feel fragmented
- The most visible product risk has shifted from missing plumbing to usability, deployment safety, and codebase clarity

## Constraints

- **Architecture**: DeerFlow remains the primary orchestration runtime; fixes should strengthen, not bypass, the intended agent/tool flow
- **Runtime**: OpenFOAM execution still happens inside Docker and sandbox environments; researcher UX must continue to match that deployment path
- **Scientific Integrity**: The system must not overclaim results beyond recorded evidence; scientific claim levels and approval gates stay explicit
- **Input Format**: The operational geometry path remains STL-first until a future milestone explicitly expands intake support
- **Brownfield**: Existing working domain modules and tests should be preserved while follow-up debt is closed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep DeerFlow as the sole runtime path for submarine CFD orchestration | Splitting runtime logic would reduce traceability, recovery, and cockpit visibility | Good |
| Treat "research usable" as evidence-backed, not merely runnable | Artifact production alone is insufficient for scientific use | Good |
| Mirror operational runtime state and scientific state into persisted `submarine_runtime` | Refresh-safe UI should not reconstruct critical truth from stage order alone | Good |
| Consume scientific summaries from the active workbench surfaces, not helper-only panels | The mounted UI path must match what researchers actually use | Good |
| Keep unmatched benchmark references visible as explicit `not_applicable` evidence | Missing or mismatched references are scientifically meaningful and should still limit claims | Good |
| Treat geometry trust as a structured contract and researcher approval as a separate pre-compute gate | Raw heuristics and claim-level wording were too easy to over-trust without explicit contracts | Good |
| Emit one canonical provenance manifest for every solver-dispatch run | Researchers need one rerun and audit anchor instead of reconstructing provenance from scattered artifacts | Good |
| Keep custom variants in the same experiment manifest and compare chain as baseline and study variants | Side channels would make linkage, reporting, and cockpit lineage inconsistent | Good |
| Separate runtime parity from scientific truth | Environment drift affects rerun confidence, not whether evidence was scientifically observed | Good |
| Keep supervisor next-step choice chat-driven even when the workbench can enumerate options | The cockpit should surface truth and decisions without becoming a button-heavy workflow shell | Good |
| Record follow-up history with explicit decision intent and refreshed provenance anchors | Auditability improves when rerun lineage is explicit and bounded to one user-confirmed step | Good |
| Keep `v1.1` aligned with DeerFlow-native skill, sandbox, and deployment conventions instead of inventing a parallel platform model | The project already inherits DeerFlow foundations, so productization should strengthen that compatibility | Good |
| Pair major UX work with module-boundary cleanup | Re-skinning chaotic architecture would make iteration slower, riskier, and harder to validate | Good |

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
*Last updated: 2026-04-03 after v1.1 milestone planning*
