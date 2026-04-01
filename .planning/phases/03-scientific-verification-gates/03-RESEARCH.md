# Phase 3: Scientific Verification Gates - Research

**Researched:** 2026-04-01
**Domain:** Scientific evidence extraction, verification workflows, and claim-gating over the existing DeerFlow submarine runtime
**Confidence:** MEDIUM

<user_constraints>
## User Constraints

- `SCI-01`: claim level must be gated by residual and force-coefficient stability evidence rather than by report generation alone.
- `SCI-02`: mesh, domain, and time-step sensitivity studies must be executable or manageable as first-class workflows.
- `SCI-03`: benchmark-backed cases must compare computed metrics against cited reference targets and block unsupported claims.
- The active researcher-facing path remains the dedicated submarine workbench plus DeerFlow runtime. Scientific gates must strengthen that path instead of introducing an external side-channel.
- OpenFOAM execution stays inside the Docker Desktop sandbox/container setup already productized in Phase 2.

</user_constraints>

<research_summary>
## Summary

Phase 3 should not start from zero. The codebase already contains a substantial but only partially productized scientific-verification layer:

- `solver_dispatch_results.py` already parses `residual_summary`, `force_coefficients_history`, `latest_force_coefficients`, `forces_history`, and `mesh_summary` from OpenFOAM output.
- `verification.py` already knows how to evaluate:
  - a max-final-residual threshold,
  - force-coefficient tail stability,
  - presence and pass/block status of `verification-mesh-independence.json`,
  - presence and pass/block status of `verification-domain-sensitivity.json`,
  - presence and pass/block status of `verification-time-step-sensitivity.json`.
- `studies.py`, `experiments.py`, and `solver_dispatch.py` already create deterministic study manifests, variant definitions, run records, and experiment compare artifacts.
- `evidence.py`, `reporting.py`, and `supervision.py` already aggregate verification, validation, and provenance into `research_evidence_summary` and `scientific_supervisor_gate`.
- The frontend contract and runtime panel already type and render research evidence, scientific gate summaries, and remediation summaries.

The real Phase 3 gap is productization and timing, not raw existence:

1. Stability evidence is currently derived mostly at final-report time, not promoted to a first-class runtime artifact and workbench truth as soon as a solver run becomes eligible.
2. Sensitivity-study logic exists, but its execution/resume/compare workflow is still too implicit and too tightly coupled to baseline dispatch.
3. Benchmark comparison and claim-level gating exist in domain code, but they still depend on incomplete case-library coverage and need clearer artifact-level explanations for operators.

</research_summary>

<existing_capabilities>
## Existing Capabilities We Can Reuse

### Runtime and artifact contracts already in place

- `backend/packages/harness/deerflow/domain/submarine/contracts.py`
  - `SubmarineRuntimeSnapshot` already carries `scientific_gate_status`, `allowed_claim_level`, and artifact pointers.
  - The execution plan already includes `scientific-study`, `experiment-compare`, `scientific-verification`, and `scientific-followup` roles.
- `backend/packages/harness/deerflow/domain/submarine/runtime_plan.py`
  - runtime truth is already centralized for the workbench and can be extended instead of re-invented.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`
  - already types `research_evidence_summary`, `scientific_supervisor_gate`, `scientific_verification_assessment`, `scientific_study_summary`, and related report payloads.

### Scientific logic already present in backend domain code

- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_results.py`
  - parses solver residual history and force-coefficient history from real solver output.
- `backend/packages/harness/deerflow/domain/submarine/verification.py`
  - already computes requirement-level pass/block/missing states.
- `backend/packages/harness/deerflow/domain/submarine/studies.py`
  - already defines mesh/domain/time-step study variants and pass/fail tolerances.
- `backend/packages/harness/deerflow/domain/submarine/evidence.py`
  - already synthesizes verification, validation, and provenance into readiness levels.
- `backend/packages/harness/deerflow/domain/submarine/supervision.py`
  - already maps readiness status into claim level and recommended remediation stage.
- `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - already writes `research-evidence-summary.json`, `supervisor-scientific-gate.json`, and remediation artifacts.

### Coverage that already exists

- `backend/tests/test_submarine_result_report_tool.py`
  - already exercises parts of scientific gate generation.
- `backend/tests/test_submarine_experiment_linkage_contracts.py`
  - already exercises experiment/study linkage logic and report downgrade behavior.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - already contains sections for scientific gate and research evidence summaries.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - already has label/summary builders for scientific evidence and claim-level display.

</existing_capabilities>

<gaps>
## Product Gaps That Still Block Research-Usable Behavior

### Gap 1: Stability evidence is not yet a first-class runtime output

Current state:

- residual and force-coefficient evidence exist inside `solver-results.json`,
- requirement evaluation exists inside `verification.py`,
- gate synthesis exists inside `reporting.py`,
- but the workbench-level runtime truth does not yet expose a dedicated stability-evidence artifact or summary immediately after solver completion.

Impact:

- researchers still reach claim-level decisions too late in the flow,
- pipeline/stage surfaces cannot explain why a run is claim-limited until final reporting has been produced,
- SCI-01 is not yet satisfied as a runtime contract.

### Gap 2: Sensitivity studies are planned, but not yet operationally managed

Current state:

- deterministic study manifests and verification artifacts already exist,
- `solver_dispatch.py` can emit pending/completed study artifacts,
- but there is no clearly productized workflow for re-running, resuming, comparing, and explaining study variants as first-class verification work.

Impact:

- SCI-02 remains only partially satisfied,
- users cannot reliably treat sensitivity work as explicit experiment ops inside the workbench,
- provenance exists, but operator affordances are still weak.

### Gap 3: Benchmark-backed claim gating is real in code, but still too opaque

Current state:

- benchmark targets and comparison logic already exist in acceptance/reporting code,
- but case-library coverage is uneven and benchmark evidence is not yet explained as clearly as runtime, stability, or study evidence.

Impact:

- SCI-03 is still not strong enough for researcher trust,
- claim blocks and downgrades are possible but not yet consistently traceable to benchmark artifacts and references.

### Gap 4: There is a mismatch between backend scientific sophistication and cockpit storytelling

Current state:

- the runtime panel knows how to render scientific evidence,
- but the pipeline/banner/stage surfaces still focus mainly on runtime execution truth.

Impact:

- scientific readiness remains a secondary detail instead of a primary workbench outcome,
- the platform can feel more operational than research-grade even when the backend already knows better.

</gaps>

<recommended_decomposition>
## Recommended Plan Decomposition

### 03-01: Stability evidence extraction and gate contract

Scope:

- Promote residual and force-coefficient stability into explicit evidence objects/artifacts.
- Expose requirement-level stability assessment earlier in the runtime flow.
- Make workbench/runtime/report surfaces consume the same stability-gate truth.

Why first:

- It closes the biggest SCI-01 gap using data the system already captures.
- It provides the contract that 03-02 and 03-03 should build on instead of inventing separate gate semantics.

### 03-02: Sensitivity-study execution and provenance workflow

Scope:

- Turn existing manifests and variant definitions into an operator-manageable workflow.
- Harden experiment linkage, study execution status, compare summaries, and rerun/resume behavior.

Why second:

- The core study data model already exists, but Phase 3 still needs explicit orchestration and workbench surfacing to satisfy SCI-02.

### 03-03: Benchmark comparison and final claim-level decisions

Scope:

- Promote benchmark evidence into first-class artifacts and explanations.
- Synthesize benchmark, stability, and sensitivity evidence into the final claim-level contract.
- Surface benchmark-backed block/downgrade explanations in the workbench and reports.

Why third:

- Benchmark gating should consume the stability and study contracts established in 03-01 and 03-02.
- It is also where the system transitions from “verified execution” to “research-ready conclusion.”

</recommended_decomposition>

<architecture_guidance>
## Architecture Guidance

### Backend ownership

- `solver_dispatch_results.py`
  - remains the source of truth for raw solver-derived evidence.
- `verification.py`
  - should own requirement-level scientific verification logic, including stability checks.
- `reporting.py` + `evidence.py` + `supervision.py`
  - should continue to own claim-level synthesis, but should consume structured evidence artifacts instead of re-deriving ad hoc summaries where possible.
- `contracts.py` + runtime snapshot writers
  - should carry the minimum scientific-gate truth needed for refresh-safe cockpit behavior.

### Frontend ownership

- `submarine-runtime-panel.tsx` and `submarine-runtime-panel.utils.ts`
  - should remain the detailed inspection surface for scientific evidence.
- `submarine-pipeline.tsx`, `submarine-pipeline-status.ts`, and `submarine-stage-cards.tsx`
  - should surface top-line scientific gate consequences, not duplicate the entire scientific evidence payload.

### Artifact contract recommendation

Prefer a layered contract:

1. raw solver evidence
   - `solver-results.json`
2. verification evidence
   - requirement- or study-specific verification artifacts
3. synthesized evidence
   - `research-evidence-summary.json`
4. operator-facing decision
   - `supervisor-scientific-gate.json`

This matches the existing architecture and avoids coupling the UI directly to raw solver logs.

</architecture_guidance>

<validation_architecture>
## Validation Architecture

### Automated backend validation

- parser tests for residual history, tail-stability extraction, and solver-metric edge cases
- verification tests for pass / blocked / missing-evidence transitions
- tool-level tests for runtime snapshots and final-report artifacts
- experiment-linkage tests for study manifest and compare completeness

### Automated frontend validation

- runtime-panel utility tests for evidence and claim-level labeling
- pipeline/stage tests for scientific gate summaries and blocked claim narratives
- contract-level tests that mock final-report payloads with:
  - passed stability,
  - missing study evidence,
  - failed benchmark comparison

### Manual validation

- MCP/browser check on an active local workbench session
- use a representative submarine geometry such as `C:/Users/D0n9/Desktop/suboff_solid.stl`
- confirm that:
  - a completed run exposes stability evidence,
  - claim level downgrades when study or benchmark evidence is missing,
  - remediation guidance points to the correct next stage.

</validation_architecture>

<risks>
## Key Risks

- Existing scientific modules are ahead of the planning docs; careless implementation could duplicate logic instead of consolidating it.
- Case-library benchmark coverage is still uneven, so SCI-03 planning must separate “make benchmark gating first-class” from “harden all case references,” which belongs partly to Phase 4.
- Historical encoding noise remains in some frontend files, so UI work should prefer minimal, targeted edits around stable anchors.

</risks>

<canonical_refs>
## Canonical References

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/phases/03-scientific-verification-gates/03-CONTEXT.md`
- `.planning/phases/02-runtime-solver-productization/02-02-SUMMARY.md`
- `.planning/phases/02-runtime-solver-productization/02-03-SUMMARY.md`
- `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_results.py`
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- `backend/packages/harness/deerflow/domain/submarine/verification.py`
- `backend/packages/harness/deerflow/domain/submarine/studies.py`
- `backend/packages/harness/deerflow/domain/submarine/evidence.py`
- `backend/packages/harness/deerflow/domain/submarine/supervision.py`
- `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- `backend/tests/test_submarine_result_report_tool.py`
- `backend/tests/test_submarine_experiment_linkage_contracts.py`
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- `frontend/src/components/workspace/submarine-pipeline.tsx`
- `frontend/src/components/workspace/submarine-stage-cards.tsx`

</canonical_refs>

<deferred>
## Deferred Ideas

- Broad case-library reference hardening across non-SUBOFF geometries belongs mainly to Phase 4.
- HPC-scale scientific study orchestration belongs to later experiment-ops work.
- Fully automated benchmark-corpus ingestion is outside the scope of this phase.

</deferred>

---

*Phase: 03-scientific-verification-gates*
*Research refreshed: 2026-04-01*
