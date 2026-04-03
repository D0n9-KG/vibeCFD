# Roadmap: VibeCFD

## Milestones

- [x] **v1.0 MVP** - Phases 1-6 shipped on 2026-04-03. Archive: `.planning/milestones/v1.0-ROADMAP.md`
- [ ] **v1.1 Experience & Platform** - Phases 7-11 planned

## Active Milestone

**v1.1 Experience & Platform**

Goal: turn the shipped submarine CFD loop into a cleaner, safer, and more extensible DeerFlow-aligned product with stronger UX, skill lifecycle management, deployment isolation, and architecture clarity.

## Phases

- [ ] **Phase 7: Workspace UX and Navigation System** - Rebuild the core workspace information architecture, page shells, and responsive layouts for submarine, chat, and skill surfaces
- [ ] **Phase 8: Skill Studio Lifecycle and Governance** - Productize full-chain Vibe CFD skill creation, publish, auto-configuration, and revision management around DeerFlow skills
- [ ] **Phase 9: Runtime Isolation and Deployment Hardening** - Harden Docker and sandbox deployment boundaries so lead agents, subagents, and OpenFOAM execution are safer on servers
- [ ] **Phase 10: Architecture Simplification and Contract Boundaries** - Break oversized modules into clearer domain boundaries while stabilizing shared state and lifecycle contracts
- [ ] **Phase 11: Live Validation and Release Readiness** - Close the remaining live-thread validation debt and verify the milestone against real flows instead of fixtures alone

## Phase Details

### Phase 7: Workspace UX and Navigation System
**Goal**: Make the workspace feel coherent, readable, and trustworthy by introducing a shared IA, layout system, and page-level UX polish across the product.
**Depends on**: Phase 6 shipped baseline
**Requirements**: UX-01, UX-02, UX-03, UX-04
**Success Criteria** (what must be TRUE):
1. Users can move among chat, submarine, skill studio, and agent surfaces through one consistent navigation and page-shell model.
2. Core submarine and skill-studio tasks keep primary actions, evidence context, and artifacts visible without layout confusion on normal desktop and laptop widths.
3. Shared layout primitives and feedback states replace visibly inconsistent page-by-page shells.
4. Chinese copy, spacing, loading states, and focus behavior feel deliberate rather than improvised.
**Plans**: 3 plans

Plans:
- [x] 07-01: Audit workspace IA and extract shared layout, navigation, and design-token primitives
- [x] 07-02: Rebuild submarine and skill-studio shells around the shared workspace system
- [ ] 07-03: Polish accessibility, responsive behavior, and key task flows on redesigned pages

### Phase 8: Skill Studio Lifecycle and Governance
**Goal**: Turn skill studio into a full lifecycle product for Vibe CFD skills that matches DeerFlow's skill model and publish flow.
**Depends on**: Phase 7
**Requirements**: SKILL-01, SKILL-02, SKILL-03, SKILL-04, SKILL-05
**Success Criteria** (what must be TRUE):
1. A user can co-create a Vibe CFD skill with the lead agent inside a dedicated workbench aligned with DeerFlow skill conventions.
2. Generated skill outputs are package-complete and publishable without manual patching.
3. Publishing can enable and wire the skill into the project's DeerFlow setup automatically.
4. Skill revisions, rollback targets, and discoverability are visible and manageable after publishing.
**Plans**: 3 plans

Plans:
- [ ] 08-01: Unify skill creator orchestration, thread state, and package schema for Vibe CFD skills
- [ ] 08-02: Add publish, auto-configure, and management flows for project-local DeerFlow skills
- [ ] 08-03: Add revision history, rollback, and post-publish discoverability plus governance views

### Phase 9: Runtime Isolation and Deployment Hardening
**Goal**: Make server deployment safer by turning existing Docker and sandbox support into a deliberate runtime isolation model.
**Depends on**: Phase 8
**Requirements**: DEP-01, DEP-02, DEP-03, DEP-04
**Success Criteria** (what must be TRUE):
1. Lead agent, subagents, gateway, LangGraph, and OpenFOAM execution paths all run through explicit container or sandbox boundaries.
2. Host mounts and writable paths are narrowed to the minimum needed for safe runtime behavior.
3. Local, compose-dev, and deployed profiles share one parity-aware deployment model.
4. Operators have health, limit, and recovery checks before exposing the stack on a server.
**Plans**: 3 plans

Plans:
- [ ] 09-01: Harden container and sandbox topology for gateway, LangGraph, agents, and OpenFOAM execution
- [ ] 09-02: Restrict mounts, permissions, auth material, and runtime profiles for server-safe deployment
- [ ] 09-03: Add deployment verification, health checks, and operational recovery guidance

### Phase 10: Architecture Simplification and Contract Boundaries
**Goal**: Reduce structural chaos by decomposing oversized modules and clarifying ownership between UI, lifecycle, runtime, and deployment layers.
**Depends on**: Phase 7 and Phase 8
**Requirements**: ARCH-01, ARCH-02, ARCH-03
**Success Criteria** (what must be TRUE):
1. Core workspace pages no longer depend on oversized monolithic frontend files for ordinary behavior.
2. Backend skill lifecycle and runtime responsibilities are organized behind clearer modules and contracts.
3. Shared thread, skill, and runtime contracts remain explicit, synchronized, and regression-tested.
**Plans**: 3 plans

Plans:
- [ ] 10-01: Split oversized frontend workbench modules into shells, view-model helpers, and domain components
- [ ] 10-02: Reorganize backend skill lifecycle and runtime orchestration behind clearer service boundaries
- [ ] 10-03: Normalize shared contracts and regression coverage across backend, frontend, and tests

### Phase 11: Live Validation and Release Readiness
**Goal**: Finish the milestone with live validation evidence and release hardening instead of relying only on deterministic fixtures.
**Depends on**: Phase 9 and Phase 10
**Requirements**: VAL-01, VAL-02, VAL-03
**Success Criteria** (what must be TRUE):
1. The team can capture a fresh live non-mock SCI-03 validation thread against current runtime artifacts.
2. The team can capture a fresh live non-mock delivery-review thread for final report, supervisor decision, and follow-up flow.
3. Mock workspace entry no longer triggers unnecessary thread-search traffic.
4. The milestone is auditable as a cleaner server-ready release candidate.
**Plans**: 3 plans

Plans:
- [ ] 11-01: Capture live non-mock SCI-03 and research-delivery verification evidence
- [ ] 11-02: Eliminate mock-mode thread-search leakage and remaining release blockers
- [ ] 11-03: Run cross-surface UX, skill lifecycle, and deployment readiness audit

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. End-to-End Workbench Bootstrap | v1.0 | 3/3 | Complete | 2026-04-01 |
| 2. Runtime Solver Productization | v1.0 | 3/3 | Complete | 2026-04-01 |
| 3. Scientific Verification Gates | v1.0 | 3/3 | Complete | 2026-04-02 |
| 4. Geometry and Case Intelligence Hardening | v1.0 | 3/3 | Complete | 2026-04-02 |
| 5. Experiment Ops and Reproducibility | v1.0 | 3/3 | Complete | 2026-04-02 |
| 6. Research Delivery Workbench | v1.0 | 3/3 | Complete | 2026-04-03 |
| 7. Workspace UX and Navigation System | v1.1 | 2/3 | In Progress | - |
| 8. Skill Studio Lifecycle and Governance | v1.1 | 0/3 | Not started | - |
| 9. Runtime Isolation and Deployment Hardening | v1.1 | 0/3 | Not started | - |
| 10. Architecture Simplification and Contract Boundaries | v1.1 | 0/3 | Not started | - |
| 11. Live Validation and Release Readiness | v1.1 | 0/3 | Not started | - |

---
*Last updated: 2026-04-03 after Phase 07 Plan 02 execution*
