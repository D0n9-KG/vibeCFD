# Requirements: VibeCFD

**Defined:** 2026-04-01
**Core Value:** A researcher can go from natural-language CFD intent to reproducible, evidence-backed submarine results without manually building and operating OpenFOAM cases.

## v1 Requirements

### Workbench Flow

- [x] **FLOW-01**: Researcher can start a new submarine study from `/workspace/submarine/new` without client-side thread bootstrap failure
- [x] **FLOW-02**: Uploaded STL files and the first prompt are bound to the created thread and remain visible after route transition or refresh
- [x] **FLOW-03**: Workbench stage cards, runtime panel, and artifact rail reflect bootstrap success and failure states in a recoverable way

### Runtime Execution

- [ ] **EXEC-01**: A confirmed submarine study can generate an OpenFOAM case scaffold and launch it inside the configured DeerFlow sandbox/container
- [ ] **EXEC-02**: Solver execution writes logs, residuals, force coefficients, and requested post-processing artifacts back into thread outputs
- [ ] **EXEC-03**: Researchers can inspect or resume in-flight and completed runtime state from the workbench without losing thread context

### Scientific Evidence

- [ ] **SCI-01**: Claim level is gated by residual and force-coefficient stability evidence rather than report generation alone
- [ ] **SCI-02**: Mesh, domain, and time-step sensitivity studies can be executed or managed as first-class verification workflows
- [ ] **SCI-03**: Benchmark-backed cases compare computed metrics against cited reference targets and block unsupported claims

### Geometry and Case Intelligence

- [x] **GEO-01**: Geometry preflight detects STL integrity, unit/scale anomalies, and reference-length or reference-area assumptions before solve
- [x] **GEO-02**: Case-library entries use real references and explicit acceptance profiles rather than placeholder sources
- [x] **GEO-03**: Non-research-ready geometries or ambiguous setups are downgraded or blocked with clear justification

### Reproducibility and Operations

- [x] **OPS-01**: Every run records reproducible provenance for geometry, case template, solver settings, runtime environment, and outputs
- [x] **OPS-02**: Researchers can launch baseline-vs-variant studies and trace comparison results across study manifests and artifacts
- [x] **OPS-03**: Runtime configuration is consistent across local dev, Docker Compose, and deployed environments

### Delivery and Review

- [ ] **RPT-01**: Final reports package coefficients, plots, figures, claim level, evidence gaps, and recommended follow-up in Chinese
- [ ] **RPT-02**: Supervisor review in the workbench can approve, block, rerun, or extend studies based on recorded evidence and artifacts

## v2 Requirements

### Advanced Runtime

- **HPC-01**: Researchers can offload studies to cluster or HPC schedulers with the same provenance model
- **HPC-02**: Large multi-run studies support queued execution and resource-aware scheduling

### Geometry Expansion

- **CAD-01**: Native STEP/Parasolid geometry intake is supported with robust conversion and validation
- **CAD-02**: Geometry cleanup workflows support more than STL mesh uploads

### Physics Expansion

- **PHY-01**: Near-free-surface or multiphase submarine workflows are supported with validated templates
- **PHY-02**: The platform can expand beyond submarine resistance-style studies to broader CFD domains

## Out of Scope

| Feature | Reason |
|---------|--------|
| General-purpose multi-domain simulation platform | Keep the current milestone focused on submarine CFD research quality |
| Native CAD-first intake for current milestone | STL path is the current operational baseline and still needs hardening |
| Free-surface and multiphase production workflows | Existing support is placeholder-level and not ready for v1 claims |
| HPC scheduler integration in current milestone | Local and Docker-backed reproducibility must be stable first |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FLOW-01 | Phase 1 | Completed |
| FLOW-02 | Phase 1 | Completed |
| FLOW-03 | Phase 1 | Completed |
| EXEC-01 | Phase 2 | Pending |
| EXEC-02 | Phase 2 | Pending |
| EXEC-03 | Phase 2 | Pending |
| SCI-01 | Phase 3 | Pending |
| SCI-02 | Phase 3 | Pending |
| SCI-03 | Phase 3 | Pending |
| GEO-01 | Phase 4 | Completed |
| GEO-02 | Phase 4 | Completed |
| GEO-03 | Phase 4 | Completed |
| OPS-01 | Phase 5 | Completed |
| OPS-02 | Phase 5 | Completed |
| OPS-03 | Phase 5 | Completed |
| RPT-01 | Phase 6 | Pending |
| RPT-02 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-01*
*Last updated: 2026-04-02 after Phase 5 completion*
