---
phase: 03
slug: scientific-verification-gates
status: ready_for_planning
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-01
updated: 2026-04-01
---

# Phase 03 - Validation Strategy

## Validation Goal

Prove that Phase 3 upgrades the platform from runtime-complete CFD delivery to evidence-gated scientific delivery.

The validation target is not only “artifacts exist,” but:

- stability evidence is computed from real solver outputs,
- sensitivity studies are traceable as verification workflows,
- benchmark comparisons can block or downgrade claims,
- the workbench explains the current claim level and next remediation path.

## Validation Dimensions

### Dimension 1: Stability Evidence Contract

Must validate:

- residual and force-coefficient stability checks use deterministic inputs from `solver-results.json`
- requirement-level results are persisted into structured evidence payloads
- runtime/report surfaces do not need to reverse-engineer scientific readiness from raw solver logs

### Dimension 2: Sensitivity Workflow Traceability

Must validate:

- mesh/domain/time-step study manifests are explicit and complete
- baseline and variant runs remain linked through experiment manifests and compare summaries
- pending, blocked, and completed study states are distinguishable

### Dimension 3: Benchmark Claim Gating

Must validate:

- benchmark comparison outputs identify pass/block outcomes per metric
- missing or failed benchmark evidence downgrades or blocks the claim level
- the researcher can see why the claim level changed and what stage to revisit

### Dimension 4: Researcher-Facing Explanation

Must validate:

- runtime panel and report views show scientific readiness, evidence gaps, and remediation guidance
- stage/pipeline summaries surface the gate consequence without duplicating the entire final report
- claim-level language is consistent between backend artifacts and the workbench UI

## Automated Validation Requirements

### Backend

- `uv run pytest` coverage for:
  - solver-result parsing edge cases
  - verification pass / blocked / missing-evidence branches
  - study-manifest and experiment-linkage consistency
  - result-report scientific gate and claim-level transitions

### Frontend

- `node --test` coverage for:
  - runtime-panel utility summary builders
  - runtime panel rendering of research evidence / gate summaries
  - pipeline or stage rendering of scientific gate consequences
- `corepack pnpm typecheck`

## Manual Validation Requirements

Use a representative submarine case after local frontend/backend dev sessions are active:

- geometry candidate:
  - `C:/Users/D0n9/Desktop/suboff_solid.stl`
- workflow:
  1. launch or resume a submarine thread
  2. drive it through solver completion and result reporting
  3. inspect the workbench scientific evidence sections
  4. confirm gate status, claim level, and remediation stage match the produced evidence

## Evidence To Capture Before Phase Sign-Off

- solver-derived stability evidence artifact(s)
- study manifest and compare artifacts for sensitivity verification
- benchmark comparison artifact(s) with pass/block explanation
- final report and/or runtime-panel screenshots showing scientific gate outcome

## Exit Criteria

Phase 3 is not ready for execution sign-off until all of the following are true:

- SCI-01 is backed by deterministic automated verification plus visible cockpit/report evidence
- SCI-02 is backed by traceable study workflow artifacts and compare summaries
- SCI-03 is backed by benchmark comparison logic that can block or downgrade unsupported claims
- at least one end-to-end MCP/browser validation confirms the workbench explains the scientific gate to a researcher
