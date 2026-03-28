# Scientific Study Orchestration v1 Design

## 1. Purpose

This document defines the next implementation slice for turning the current DeerFlow-based submarine CFD system into a research-usable `vibe CFD` platform.

The scope of this slice is intentionally narrow:

- keep the user-facing experience open-ended and agentic
- add a deterministic study-planning and study-evidence layer behind the scenes
- make the system generate structured scientific verification artifacts instead of only asking for them

This slice does not attempt to finish the entire research workflow in one pass. It establishes the first executable bridge from:

- free-form user intent
- to structured study contracts
- to controlled solver variants
- to reproducible verification evidence

## 2. Problem Statement

The repository now has a first scientific verification contract:

- design briefs can declare research-facing verification requirements
- final reports can assess whether verification evidence is missing, blocked, or passed
- the workbench can surface those requirements and assessments

However, the system still lacks the mechanism that makes those requirements actionable. Today it can honestly say:

- mesh independence evidence is missing
- domain sensitivity evidence is missing
- time-step sensitivity evidence is missing

But it cannot yet:

- generate a study plan from a selected case
- create controlled study variants
- organize those variants into a reproducible experiment manifest
- aggregate study outcomes into `verification-*.json` artifacts

Without that layer, the system is still a strong baseline research assistant, but not yet a research-usable CFD workflow.

## 3. Core Design Principle

The system must not collapse into a rigid workflow product.

To preserve `vibe CFD`, constraints must be applied at the execution and evidence layers, not at the user-intent layer.

The architecture for this slice therefore uses four layers:

1. Free Input Layer

Users continue to express requests in natural language, including ambiguous or mixed requests such as:

- "calculate drag and also give me a wake slice"
- "tell me whether this run is research ready"
- "do the mesh independence study too"

2. Structured Contract Layer

The system translates free-form intent into structured contracts:

- selected case
- simulation requirements
- requested outputs
- scientific verification requirements
- requested scientific studies

3. Controlled Execution Layer

Once the contract is confirmed, the execution layer becomes deterministic:

- study variants are generated from explicit rules
- variant parameters are recorded
- artifacts are emitted with stable names
- report logic consumes only structured study evidence

4. Evidence Delivery Layer

The system assembles outputs according to user intent, but only from traceable artifacts and structured summaries.

This preserves an open, agentic front-end while enforcing a research-grade back-end.

## 4. Goals

- Generate deterministic study plans for the selected submarine CFD case.
- Support three scientific study types in v1:
  - `mesh_independence`
  - `domain_sensitivity`
  - `time_step_sensitivity`
- Produce structured experiment artifacts that the reporting layer can consume directly.
- Preserve the existing DeerFlow runtime model rather than introducing a parallel orchestration framework.
- Keep the workbench visibility minimal but sufficient for users to inspect study status and artifacts.

## 5. Non-Goals

- No full experiment manager UI in this slice.
- No general run-to-run compare workspace yet.
- No arbitrary user-authored study matrix editor yet.
- No attempt to solve publication-grade figure generation in this slice.
- No replacement of the free-form front-end with a fixed wizard or rigid workflow shell.

## 6. Scope Boundary

This slice targets one executable research step:

- starting from a selected case and baseline simulation setup
- generate controlled verification-study variants
- aggregate their outcomes into structured study artifacts
- feed those artifacts into the current report and workbench system

The first target path is:

- geometry uploaded by user
- selected case `darpa_suboff_bare_hull_resistance`
- baseline solver-dispatch setup
- study generation and aggregation on top of that setup

The design must remain extensible to other case profiles, but v1 optimization is explicitly centered on the current main path.

## 7. Current System Baseline

The repository already contains the pieces that this slice should extend:

- case and acceptance-profile models in `backend/packages/harness/deerflow/domain/submarine/models.py`
- scientific verification contract logic in `backend/packages/harness/deerflow/domain/submarine/verification.py`
- design-brief generation in `backend/packages/harness/deerflow/domain/submarine/design_brief.py`
- solver planning and OpenFOAM case materialization in `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- output delivery logic in `backend/packages/harness/deerflow/domain/submarine/output_contract.py`
- final reporting in `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- workbench summarization in `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`

This slice must build on those modules instead of introducing a parallel subsystem.

## 8. Proposed Architecture

### 8.1 Domain Contracts

The domain layer should gain explicit study contracts.

Recommended model additions:

- `SubmarineScientificStudyDefinition`
  - study type
  - monitored quantity
  - pass/fail tolerance
  - required variant count
  - summary label

- `SubmarineScientificStudyVariant`
  - study type
  - variant id
  - variant label
  - parameter overrides
  - rationale

- `SubmarineScientificStudyManifest`
  - selected case id
  - baseline configuration snapshot
  - study definitions
  - generated variants
  - artifact paths
  - study execution status

- `SubmarineScientificStudyResult`
  - study type
  - monitored quantity
  - baseline value
  - compared values
  - relative spread
  - pass/fail status
  - summary text

These models should live in the existing submarine domain model layer rather than in generic runtime state files.

### 8.2 Study Planning

Study planning should be deterministic and case-aware.

The planner should derive study definitions from:

- selected case acceptance profile
- task type
- baseline simulation requirements

For v1, the planner should generate exactly three studies when the acceptance profile supports scientific verification:

1. Mesh independence
   - coarse
   - baseline
   - fine

2. Domain sensitivity
   - compact
   - baseline
   - expanded

3. Time-step sensitivity
   - coarse
   - baseline
   - fine

Each generated variant must capture:

- what changed
- why it changed
- what monitored quantity will be compared

### 8.3 Variant Derivation Rules

Variant derivation must be explicit and reproducible.

For v1, the system should support controlled override families:

- mesh study
  - mesh scale factor or refinement preset
- domain study
  - domain extent multiplier
- time-step study
  - deltaT multiplier

The exact values can start simple and deterministic. For example:

- mesh: `0.75x`, `1.00x`, `1.25x`
- domain: `0.85x`, `1.00x`, `1.20x`
- deltaT: `2.0x`, `1.0x`, `0.5x`

The important requirement is not the exact coefficients, but that:

- they are recorded
- they are stable
- they are visible in artifacts
- later slices can refine them without breaking the data model

### 8.4 Solver-Dispatch Integration

`solver_dispatch.py` should become responsible for study orchestration for v1.

That does not mean it becomes a giant experiment manager. It means:

- baseline case generation remains the anchor
- study variants are derived from the same baseline contract
- each variant gets a stable subdirectory and artifact namespace
- a `study-plan.json` and `study-manifest.json` are written before aggregation

Expected artifact pattern:

- `study-plan.json`
- `study-manifest.json`
- `studies/mesh-independence/coarse/solver-results.json`
- `studies/mesh-independence/baseline/solver-results.json`
- `studies/mesh-independence/fine/solver-results.json`
- `studies/domain-sensitivity/...`
- `studies/time-step-sensitivity/...`
- `verification-mesh-independence.json`
- `verification-domain-sensitivity.json`
- `verification-time-step-sensitivity.json`

### 8.5 Study Aggregation

Aggregation should be deterministic and separate from raw execution.

Each study aggregator should:

- load the recorded solver results for all variants
- extract the monitored quantity
- compute the relative spread against the baseline
- decide pass/fail according to study tolerance
- emit a concise JSON result artifact

The first monitored quantity should be:

- `Cd` for resistance-oriented cases

Later slices can expand to:

- pressure coefficient distribution
- wake deficit metrics
- trim and moment metrics

### 8.6 Reporting Integration

The final report should stop treating study evidence as a mostly external input.

Instead, reporting should:

- consume generated `verification-*.json` artifacts
- summarize each study result
- distinguish:
  - no study generated
  - study generated but incomplete
  - study generated and failed
  - study generated and passed

This change should make scientific verification status reflect actual study outcomes rather than only artifact presence.

### 8.7 Workbench Visibility

Workbench scope should remain intentionally small in v1.

The workbench should show:

- study manifest summary
- study statuses
- artifact links
- per-study summary text

It should not yet attempt:

- matrix compare views
- multi-run charts
- full experiment dashboards

## 9. User Interaction Model

To keep the product agentic rather than workflow-bound, the system must preserve this behavior:

- users express intent freely
- the lead agent resolves that intent into structured contracts
- study orchestration activates only when research verification is required or requested

Examples:

- If the user asks for a quick drag estimate, the system may still run only the baseline path.
- If the user asks whether the result is research ready, the system should plan or recommend the verification studies.
- If the user explicitly requests mesh independence, the system should include the mesh study in the generated study plan.

This means the study orchestrator is a controlled back-end capability, not the only front-door interaction model.

## 10. Data Flow

The intended v1 flow is:

1. User provides free-form CFD request.
2. Lead agent selects case and resolves simulation requirements.
3. Design brief emits requested outputs and scientific verification requirements.
4. Solver-dispatch creates the baseline run contract.
5. Study planner derives study definitions and study variants.
6. Solver-dispatch materializes variant directories and records a study manifest.
7. Variant results are collected into study-specific verification JSON artifacts.
8. Reporting consumes those study artifacts and emits final scientific verification assessment.
9. Workbench displays the study manifest and the resulting assessment.

## 11. File and Module Strategy

Recommended implementation targets:

- Modify `backend/packages/harness/deerflow/domain/submarine/models.py`
  - add study contract models

- Modify `backend/packages/harness/deerflow/domain/submarine/verification.py`
  - add study-definition helpers
  - add aggregation helpers
  - tighten study evidence semantics

- Modify `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
  - generate study plan
  - generate study manifest
  - emit variant artifact paths

- Modify `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - consume generated study artifacts
  - produce stronger scientific verification summaries

- Modify `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - summarize study manifest and study artifacts

- Modify `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - render minimal study block

## 12. Testing Strategy

This slice should be developed test-first.

Minimum test coverage should include:

1. Domain asset tests
   - case profile derives study definitions correctly

2. Solver-dispatch tests
   - study plan and study manifest are emitted
   - variant directories and artifact paths are stable

3. Verification tests
   - study results aggregate correctly from variant solver outputs
   - pass/fail thresholds behave deterministically

4. Reporting tests
   - final report includes generated study evidence
   - scientific verification assessment reflects actual aggregated studies

5. Frontend utility tests
   - study manifest and study result summaries are rendered into stable UI-facing models

## 13. Risks

### 13.1 Workflow Drift

Risk:

The product becomes a rigid study wizard.

Mitigation:

- keep free-form user intent unchanged
- keep study planning behind the structured contract layer
- activate study orchestration only when relevant

### 13.2 Over-Scope

Risk:

This slice grows into a full experiment platform and stalls.

Mitigation:

- no compare UI in v1
- no generic study editor in v1
- no cross-run registry in v1

### 13.3 False Scientific Confidence

Risk:

Generated study artifacts are treated as authoritative even when variant execution is incomplete or data is malformed.

Mitigation:

- study JSON must encode incomplete and unsupported states explicitly
- missing data must never silently degrade to `passed`
- reporting must distinguish missing evidence from failed evidence

### 13.4 Architecture Drift

Risk:

A parallel experiment subsystem appears outside the existing DeerFlow runtime model.

Mitigation:

- keep study contracts in the submarine domain layer
- keep orchestration in solver-dispatch
- keep reporting in reporting
- keep UI consumption in existing workbench modules

## 14. Success Criteria

This slice is successful when all of the following are true:

- the system can derive scientific study variants from a selected case
- stable study artifacts are generated for mesh, domain, and time-step verification
- reporting consumes those artifacts directly
- the workbench can show that study evidence exists and what it concluded
- the user-facing system still accepts flexible natural-language requests
- no fixed front-end workflow replaces the agentic intake experience

## 15. Out of Scope but Next

After this slice, the next recommended order is:

1. Experiment Registry and Run Compare
2. Unified validation, benchmark, and provenance evidence chain
3. Supervisor scientific state machine
4. Publication-grade figure and delivery layer

This keeps the project moving toward full research usability without turning the current iteration into an oversized, fragile refactor.
