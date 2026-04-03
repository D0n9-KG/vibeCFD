# Requirements: VibeCFD

**Defined:** 2026-04-03
**Core Value:** A researcher can go from natural-language CFD intent to reproducible, evidence-backed submarine results without manually building and operating OpenFOAM cases.

## v1 Requirements

### Workspace Experience

- [x] **UX-01**: User can navigate chat, submarine workbench, skill studio, and agent entry points through one coherent workspace information architecture
- [x] **UX-02**: User can complete key submarine and skill-studio tasks on desktop and laptop layouts without losing primary actions, status context, or artifact access
- [x] **UX-03**: User can rely on shared page shells, navigation patterns, feedback states, and visual hierarchy across core workspace pages instead of page-by-page layout drift
- [x] **UX-04**: User-facing Chinese copy, spacing, readability, focus states, and loading or empty states remain understandable and consistent across the redesigned workspace

### Skill Lifecycle

- [ ] **SKILL-01**: User can co-create a Vibe CFD skill with the lead agent inside a dedicated skill workbench that follows DeerFlow skill conventions
- [ ] **SKILL-02**: Generated skill packages include usable `SKILL.md`, metadata, references, validation artifacts, and an installable `.skill` archive without manual patching
- [ ] **SKILL-03**: After expert sign-off, the system can publish and auto-configure a generated skill into the project's DeerFlow skill setup without manual filesystem surgery
- [ ] **SKILL-04**: User can inspect draft versus published revisions, version notes, and rollback targets for custom Vibe CFD skills
- [ ] **SKILL-05**: Published custom skills become discoverable and callable by the main agent in later threads while remaining visible in management and relationship views

### Deployment and Isolation

- [ ] **DEP-01**: Lead agent, subagents, gateway, LangGraph runtime, and OpenFOAM execution run through isolated Docker or sandbox boundaries suitable for server deployment
- [ ] **DEP-02**: Sandbox mounts, writable paths, auth material, and runtime permissions are narrowed so the application cannot casually modify unrelated server projects
- [ ] **DEP-03**: Local, Docker Compose dev, and deployed runtime profiles share one documented deployment model with parity-aware configuration and health checks
- [ ] **DEP-04**: Operators can verify resource limits, service health, failure boundaries, and recovery guidance for agent services and solver sandboxes before production rollout

### Architecture Clarity

- [ ] **ARCH-01**: Core workspace pages no longer depend on oversized monolithic frontend components and instead use clearer shells, view-model helpers, and domain modules
- [ ] **ARCH-02**: Backend skill lifecycle, runtime orchestration, and deployment responsibilities are organized behind clearer service and contract boundaries
- [ ] **ARCH-03**: Shared contracts for thread state, skill lifecycle, and runtime status remain explicit and synchronized across backend, frontend, and tests

### Validation and Release Readiness

- [ ] **VAL-01**: Team can capture a fresh live non-mock SCI-03 benchmark validation thread against current runtime artifacts
- [ ] **VAL-02**: Team can capture a fresh live non-mock research-delivery and supervisor-review thread covering final report, decision summary, and bounded follow-up
- [ ] **VAL-03**: Mock workspace loads no longer emit unnecessary `POST /threads/search` traffic during normal page entry

## v2 Requirements

### Platform Expansion

- **PLAT-01**: Multi-tenant workspace governance and role-based skill publishing are supported across teams
- **PLAT-02**: Skills can sync to a remote registry or package index with signed release metadata

### Runtime Expansion

- **RUNTIME-01**: HPC scheduler integration supports large study queues with the same provenance model
- **RUNTIME-02**: Physics workflows can expand beyond the current submarine resistance baseline without destabilizing the core UX

## Out of Scope

| Feature | Reason |
|---------|--------|
| Marketplace-style public skill distribution | Keep the milestone focused on project-local skill lifecycle and governance first |
| Organization-wide RBAC and billing | Too much product surface for the immediate usability and platform-hardening milestone |
| HPC scheduler execution | Local and Docker-backed deployment safety still needs to mature first |
| New physics domains beyond the current submarine CFD loop | The milestone priority is product quality and platform safety, not domain breadth |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| UX-01 | Phase 7 | Complete |
| UX-02 | Phase 7 | Complete |
| UX-03 | Phase 7 | Complete |
| UX-04 | Phase 7 | Complete |
| SKILL-01 | Phase 8 | Pending |
| SKILL-02 | Phase 8 | Pending |
| SKILL-03 | Phase 8 | Pending |
| SKILL-04 | Phase 8 | Pending |
| SKILL-05 | Phase 8 | Pending |
| DEP-01 | Phase 9 | Pending |
| DEP-02 | Phase 9 | Pending |
| DEP-03 | Phase 9 | Pending |
| DEP-04 | Phase 9 | Pending |
| ARCH-01 | Phase 10 | Pending |
| ARCH-02 | Phase 10 | Pending |
| ARCH-03 | Phase 10 | Pending |
| VAL-01 | Phase 11 | Pending |
| VAL-02 | Phase 11 | Pending |
| VAL-03 | Phase 11 | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0

---
*Requirements defined: 2026-04-03*
*Last updated: 2026-04-03 after Phase 07 completion*
