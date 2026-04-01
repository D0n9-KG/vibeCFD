# Unified Research Evidence Chain Design

## 1. Purpose

This document defines the next implementation slice after `Experiment Registry + Run Compare`.

The purpose of this slice is to unify the repository's growing research evidence into one explicit summary layer so the system can answer a question that matters for research usability:

- what can this run legitimately claim right now?

The design keeps the current open-ended `vibe CFD` interaction style while tightening the evidence layer beneath it.

## 2. Problem Statement

The repository now has several meaningful evidence blocks:

- `acceptance_assessment`
- `scientific_verification_assessment`
- `scientific_study_summary`
- `experiment_summary`
- `output_delivery_plan`

Each of these blocks is useful, but they still answer only part of the research question.

Today, the system can separately describe:

- whether the solver run completed cleanly
- whether mesh/domain/time-step evidence is missing
- whether benchmark comparisons exist
- whether requested output artifacts were delivered
- whether a baseline and variants belong to one experiment

But it still does not provide one stable, research-facing conclusion about the evidence chain as a whole.

That gap creates two risks:

1. users may over-read strong numerical verification as full research readiness
2. the system may remain honest but still too fragmented to be genuinely useful in research workflows

## 3. Core Semantic Rule

This slice adopts one strict default rule:

- without an external validation reference, the highest default readiness is `verified_but_not_validated`

This means:

- strong numerical verification is necessary
- external validation is a separate requirement
- generic `research_ready` is reserved for runs that have verification, validation, and traceable provenance together

The system may still support narrower claims later, such as readiness for method-development studies, but the default top-level readiness must remain conservative.

## 4. Approaches Considered

### 4.1 Option A: Keep independent evidence blocks only

This would leave the current design mostly unchanged and ask users to mentally combine:

- scientific verification
- benchmark comparisons
- experiment compare summaries
- delivery status

Pros:

- almost no new abstraction
- low implementation cost

Cons:

- still too fragmented for research decisions
- easy to misread one strong block as overall readiness
- repeated logic would leak into the workbench and prompts

### 4.2 Option B: Replace all existing summaries with one giant readiness object

This would collapse the current blocks into a single new structure.

Pros:

- one place to look
- conceptually simple on paper

Cons:

- destroys useful distinctions between operations, verification, validation, and delivery
- risks breaking current workbench/report consumers
- makes the system harder to audit

### 4.3 Option C: Keep existing blocks and add one unifying evidence-chain summary

This is the recommended design.

Pros:

- preserves existing typed evidence
- adds one research-facing conclusion layer
- keeps the evidence auditable and composable
- fits the current evolution path without turning the product into a wizard

Cons:

- introduces one more top-level object
- requires careful aggregation semantics

## 5. Recommended Design

The system should keep the current detailed evidence blocks as source evidence and add one new aggregate layer:

- `research_evidence_summary`

That summary does not replace:

- `acceptance_assessment`
- `scientific_verification_assessment`
- `scientific_study_summary`
- `experiment_summary`
- `output_delivery_plan`

Instead, it interprets them together and produces a stable research-facing conclusion.

## 6. Evidence Dimensions

### 6.1 Verification Dimension

This dimension answers:

- are the numerical results sufficiently verified?

Primary inputs:

- `scientific_verification_assessment`
- `scientific_study_summary`
- `experiment_summary`

Suggested normalized statuses:

- `passed`
- `needs_more_verification`
- `blocked`

Interpretation:

- `passed` means the current numerical verification requirements are satisfied
- `needs_more_verification` means the run may still be useful but is not numerically mature enough
- `blocked` means a hard blocker prevents using the result for research claims

### 6.2 Validation Dimension

This dimension answers:

- is there an external physical or trusted reference anchor?

Primary inputs:

- benchmark comparisons inside `acceptance_assessment`
- selected case acceptance profile and benchmark targets

Suggested normalized statuses:

- `validated`
- `missing_validation_reference`
- `validation_failed`
- `blocked`

Interpretation:

- `validated` means at least one applicable benchmark/reference check passed and no applicable validation gate failed
- `missing_validation_reference` means no applicable reference exists for the current run
- `validation_failed` means a reference existed and the run did not satisfy it
- `blocked` means validation could not even be evaluated due to missing required context

### 6.3 Provenance Dimension

This dimension answers:

- can another researcher trace what was run, compared, and delivered?

Primary inputs:

- `experiment_summary`
- `scientific_study_summary`
- `output_delivery_plan`
- existing report and artifact entrypoints

Suggested normalized statuses:

- `traceable`
- `partial`
- `missing`

Interpretation:

- `traceable` means the current run has stable experiment/report entrypoints and the key requested outputs or evidence artifacts are discoverable
- `partial` means some artifacts exist but the evidence trail is incomplete
- `missing` means the evidence trail is too thin to support reliable reuse or review

This slice keeps provenance intentionally practical. It is not yet a full provenance graph or publication package.

## 7. Aggregate Readiness

The aggregate summary should emit a top-level readiness distinct from operational delivery readiness.

Recommended top-level statuses:

- `blocked`
- `insufficient_evidence`
- `verified_but_not_validated`
- `validated_with_gaps`
- `research_ready`

Recommended semantics:

- `blocked`
  - hard blockers exist in verification or validation
- `insufficient_evidence`
  - the run is too incomplete to support a responsible research claim
- `verified_but_not_validated`
  - numerical verification is strong enough, but no external validation reference is present
- `validated_with_gaps`
  - verification and validation are present, but provenance or delivery evidence still has meaningful holes
- `research_ready`
  - verification passed, validation passed, and provenance is traceable enough for a general research-facing conclusion

## 8. Proposed Contract

The recommended new top-level contract is:

- `SubmarineResearchEvidenceSummary`

Suggested fields:

- `readiness_status`
- `readiness_label`
- `verification_status`
- `validation_status`
- `provenance_status`
- `confidence`
- `blocking_issues`
- `evidence_gaps`
- `passed_evidence`
- `benchmark_highlights`
- `provenance_highlights`
- `artifact_virtual_paths`

The artifact paths should point to stable entrypoints such as:

- `final-report.json`
- `delivery-readiness.json`
- `experiment-manifest.json`
- `run-compare-summary.json`
- `study-manifest.json`
- `verification-*.json`

## 9. Artifact Strategy

This slice should add one dedicated artifact alongside the final report:

- `research-evidence-summary.json`

Optionally, if it falls out naturally from the current reporting layer:

- `research-evidence-summary.md`

The JSON artifact matters more than the Markdown artifact in this slice because the workbench and future agents need a stable machine-readable summary.

## 10. Reporting Integration

`backend/packages/harness/deerflow/domain/submarine/reporting.py` should become the aggregation point for this slice.

Recommended behavior:

1. keep building the existing detailed evidence blocks
2. build a normalized validation assessment from benchmark comparisons
3. build a provenance assessment from experiment/study/output evidence
4. aggregate everything into `research_evidence_summary`
5. write that summary into:
   - `final-report.json`
   - `research-evidence-summary.json`
6. render a compact section in Markdown and HTML

This preserves the current architecture:

- source evidence first
- aggregate reasoning second

## 11. Workbench Integration

The workbench should remain compact.

This slice should add one small summary card or section showing:

- top-level research readiness
- verification status
- validation status
- provenance status
- key evidence gaps
- key evidence strengths
- links to the evidence summary artifact

This does not introduce:

- a workflow wizard
- a full validation dashboard
- publication-grade compare figures

## 12. Why This Preserves Vibe CFD

This design keeps constraints in the evidence layer, not the user-intent layer.

Users can still ask for:

- a quick drag estimate
- a wake slice
- a benchmark check
- a mesh study
- a research-readiness assessment

The system remains agentic in how it interprets requests.

What becomes stricter is only the evidence semantics:

- what was verified
- what was validated
- what can actually be claimed

That is the right balance for a research-facing `vibe CFD`.

## 13. File Strategy

Recommended implementation targets:

- Create `backend/packages/harness/deerflow/domain/submarine/evidence.py`
  - normalization and aggregation helpers for verification, validation, provenance, and readiness

- Modify `backend/packages/harness/deerflow/domain/submarine/models.py`
  - add research-evidence summary models

- Modify `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - build and emit `research_evidence_summary`

- Modify `backend/tests/test_submarine_domain_assets.py`
  - cover new evidence summary contracts if domain-facing helpers belong there

- Modify `backend/tests/test_submarine_result_report_tool.py`
  - cover readiness semantics and summary artifact emission

- Modify `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - parse `research_evidence_summary`

- Modify `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - cover label mapping and gap rendering

- Modify `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - render a minimal research evidence section

- Modify `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - document the new evidence-chain boundary and remaining gaps

## 14. Testing Strategy

This slice should be built test-first.

Minimum coverage:

1. evidence aggregation tests
   - verification passed + no validation reference -> `verified_but_not_validated`
   - verification passed + validation passed + traceable provenance -> `research_ready`
   - validation failed -> non-ready outcome
   - provenance partial -> `validated_with_gaps`

2. reporting tests
   - final report includes `research_evidence_summary`
   - `research-evidence-summary.json` is emitted

3. frontend utility tests
   - readiness labels are stable
   - dimension labels are stable
   - evidence gaps and highlights are parsed cleanly

## 15. Success Criteria

This slice is successful when:

- the repository emits one stable research evidence summary
- `research_ready` is no longer granted without validation
- the workbench can explain whether a run is only verified, actually validated, or still evidence-poor
- users still interact through natural language rather than a dedicated workflow shell

## 16. Remaining Gaps After This Slice

Even after this design lands, the repository will still need:

- a stronger supervisor scientific state machine
- richer provenance capture and audit trails
- publication-grade figure generation
- more expressive validation support beyond case-local benchmark targets

That is acceptable. This slice is meant to unify evidence semantics, not finish the entire research platform.
