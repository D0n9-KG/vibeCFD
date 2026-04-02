# Roadmap: VibeCFD

## Overview

This roadmap turns the current DeerFlow-based submarine CFD prototype into a research-usable work platform. The sequence is deliberate: first restore the end-to-end workbench bootstrap, then productize runtime execution, then harden scientific evidence, geometry intelligence, reproducibility, and final researcher-facing delivery.

## Phases

**Phase Numbering:**
- Integer phases (`1`, `2`, `3`) are planned milestone work
- Decimal phases (`2.1`, `2.2`) are urgent insertions if needed later

- [x] **Phase 1: End-to-End Workbench Bootstrap** - Restore real user bootstrap from new submarine workbench to live DeerFlow thread
- [x] **Phase 2: Runtime Solver Productization** - Turn solver dispatch into a controllable DeerFlow runtime flow with captured outputs
- [x] **Phase 3: Scientific Verification Gates** - Gate claim level on residual, stability, benchmark, and sensitivity evidence
- [x] **Phase 4: Geometry and Case Intelligence Hardening** - Improve geometry preflight, scale assumptions, and case-library trustworthiness (completed 2026-04-02)
- [ ] **Phase 5: Experiment Ops and Reproducibility** - Add study provenance, baseline-vs-variant tracking, and environment consistency
- [ ] **Phase 6: Research Delivery Workbench** - Finish the supervisor/report loop for researcher-facing delivery and follow-up

## Phase Details

### Phase 1: End-to-End Workbench Bootstrap
**Goal**: Fix the new-submarine workbench bootstrap so a real STL-backed prompt creates a thread, binds attachments, and enters the brief/preflight flow from the UI.
**Depends on**: Nothing (first phase)
**Requirements**: FLOW-01, FLOW-02, FLOW-03
**Success Criteria** (what must be TRUE):
1. User can submit the first prompt from `/workspace/submarine/new` without the current client-side URL/thread creation failure.
2. Uploaded STL and prompt are bound to the created thread and survive route transition plus refresh.
3. Runtime and artifact panels show recoverable success or failure state instead of relying on console-only diagnostics.
**Plans**: 3 plans

Plans:
- [x] 01-01: Reproduce and fix new-thread creation plus `Invalid URL` failure in submarine send flow
- [x] 01-02: Verify attachment upload, thread binding, and route transition between `/new` and created thread pages
- [x] 01-03: Add regression coverage and operator-visible failure handling for bootstrap path

### Phase 2: Runtime Solver Productization
**Goal**: Convert solver dispatch from a planning artifact into a controllable DeerFlow runtime execution flow with collected outputs.
**Depends on**: Phase 1
**Requirements**: EXEC-01, EXEC-02, EXEC-03
**Success Criteria** (what must be TRUE):
1. A confirmed study can launch OpenFOAM inside the configured sandbox from the DeerFlow runtime path.
2. Solver logs, residuals, force coefficients, and requested artifacts are persisted into thread outputs.
3. Users can inspect or resume in-flight and completed runtime state from the workbench.
**Plans**: 3 plans

Plans:
- [x] 02-01: Wire confirmed solver dispatch to sandbox execution and collect canonical runtime artifacts
- [x] 02-02: Persist and expose solver metrics plus execution logs through thread outputs and UI models
- [x] 02-03: Support refresh, resume, and recovery behavior for running or completed submarine jobs

### Phase 3: Scientific Verification Gates
**Goal**: Make scientific evidence, not artifact existence alone, determine whether results can advance toward research claims.
**Depends on**: Phase 2
**Requirements**: SCI-01, SCI-02, SCI-03
**Success Criteria** (what must be TRUE):
1. Residual and force-coefficient stability evidence is computed and surfaced for every eligible run.
2. Mesh, domain, and time-step sensitivity studies exist as executable or manageable verification workflows.
3. Benchmark-backed cases compare against cited references and block unsupported claims automatically.
**Plans**: 3 plans

Plans:
- [x] 03-01: Add residual and coefficient-stability evidence extraction plus gating rules
- [x] 03-02: Implement study execution and verification packaging for mesh/domain/time-step sensitivity
- [x] 03-03: Add benchmark comparison logic and integrate it into scientific claim-level decisions

### Phase 4: Geometry and Case Intelligence Hardening
**Goal**: Improve geometry trust, scale assumptions, and case knowledge so researchers get defensible setup recommendations.
**Depends on**: Phase 2
**Requirements**: GEO-01, GEO-02, GEO-03
**Success Criteria** (what must be TRUE):
1. Geometry preflight catches integrity, scale, and reference-value anomalies before solve.
2. Case-library entries rely on real references and explicit acceptance profiles.
3. Ambiguous or non-research-ready geometries are blocked or downgraded with clear explanations.
**Plans**: 3 plans

Plans:
- [x] 04-01: Harden geometry inspection with unit, scale, and reference-value sanity checks
- [x] 04-02: Replace placeholder case references and acceptance profiles with real benchmark-backed entries
- [x] 04-03: Add blocking or downgrade rules for geometry ambiguity and unsupported setups

### Phase 5: Experiment Ops and Reproducibility
**Goal**: Give researchers a reproducible study system with provenance, comparison structure, and consistent environments.
**Depends on**: Phase 3 and Phase 4
**Requirements**: OPS-01, OPS-02, OPS-03
**Success Criteria** (what must be TRUE):
1. Every run records the geometry, case template, solver settings, environment, and outputs needed for rerunability.
2. Baseline-vs-variant studies can be launched and compared as first-class experiment artifacts.
3. Local dev, Docker Compose, and deployed runtime configuration are aligned and documented.
**Plans**: 3 plans

Plans:
- [x] 05-01: Persist full run provenance and reproducibility metadata for submarine studies
- [x] 05-02: Productize experiment manifests, baseline-vs-variant linkage, and comparison summaries
- [ ] 05-03: Align runtime configuration across local, Docker Compose, and deployment paths with failure recovery guidance

### Phase 6: Research Delivery Workbench
**Goal**: Complete the researcher-facing delivery loop with reports, supervisor gate decisions, and guided follow-up actions.
**Depends on**: Phase 3 and Phase 5
**Requirements**: RPT-01, RPT-02
**Success Criteria** (what must be TRUE):
1. Final reports package metrics, figures, claim level, evidence gaps, and follow-up recommendations in Chinese.
2. Supervisor review in the workbench can approve, block, rerun, or extend studies based on evidence.
3. Users can navigate from report conclusions back to the underlying artifacts and rerun paths.
**Plans**: 3 plans

Plans:
- [ ] 06-01: Build final report packaging with strong artifact linkage and Chinese research delivery format
- [ ] 06-02: Surface supervisor scientific gate decisions and operator actions in the workbench
- [ ] 06-03: Add guided rerun and follow-up actions that preserve provenance and review state

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. End-to-End Workbench Bootstrap | 3/3 | Complete | 2026-04-01 |
| 2. Runtime Solver Productization | 3/3 | Complete | 2026-04-01 |
| 3. Scientific Verification Gates | 3/3 | Complete | 2026-04-02 |
| 4. Geometry and Case Intelligence Hardening | 3/3 | Complete    | 2026-04-02 |
| 5. Experiment Ops and Reproducibility | 2/3 | In Progress | - |
| 6. Research Delivery Workbench | 0/3 | Not started | - |
