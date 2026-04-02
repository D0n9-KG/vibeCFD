---
phase: 04
slug: geometry-and-case-intelligence-hardening
status: ready_for_planning
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-02
updated: 2026-04-02
---

# Phase 04 - Validation Strategy

## Validation Goal

Prove that Phase 4 stops weak geometry and weak case assumptions from silently becoming solver inputs.

The validation target is not only "artifacts exist", but:

- geometry preflight emits structured integrity, scale, and reference-value findings,
- case recommendations expose source quality and applicability honestly,
- solver execution is blocked until the researcher confirms the calculation plan,
- post-compute claim-level language remains separate from pre-compute approval state.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` + Node test runner + TypeScript typecheck |
| **Config file** | `backend/pyproject.toml`, `frontend/package.json`, `frontend/tsconfig.json` |
| **Quick run command** | `cd backend && uv run pytest tests/test_submarine_geometry_check_tool.py tests/test_submarine_runtime_context.py tests/test_submarine_domain_assets.py` |
| **Full suite command** | `cd backend && uv run pytest tests/test_submarine_geometry_check_tool.py tests/test_submarine_design_brief_tool.py tests/test_submarine_runtime_context.py tests/test_submarine_domain_assets.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py && cd ../frontend && node --test src/components/workspace/submarine-confirmation-actions.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-shell.test.ts && corepack pnpm typecheck` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest tests/test_submarine_geometry_check_tool.py tests/test_submarine_runtime_context.py tests/test_submarine_domain_assets.py`
- **After every plan wave:** Run the full suite command
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Validation Dimensions

### Dimension 1: Geometry Trust Contract

Must validate:

- geometry preflight emits structured anomaly rows, not only a summary string
- unit and scale heuristics record why a reference length was suggested
- severe ambiguity can switch the flow into confirmation-required or blocked state

### Dimension 2: Case Provenance Honesty

Must validate:

- recommended cases expose source label, URL, applicability conditions, and missing-evidence disclosure
- placeholder-backed entries are not silently presented as benchmark-grade evidence
- acceptance-profile quality is visible for actively recommended cases

### Dimension 3: Researcher Approval Gate

Must validate:

- calculation-plan draft items persist suggestions, edits, and approval state
- solver dispatch cannot proceed from AI guesses alone when confirmation is still pending
- early clarification is triggered only for severe ambiguity, while lower-risk items remain in the consolidated draft

### Dimension 4: Semantic Separation

Must validate:

- pre-compute approval state does not reuse `allowed_claim_level`
- post-compute scientific gate remains driven by scientific evidence only
- the cockpit uses distinct language for "pending researcher confirmation" vs "claim limited"

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | GEO-01 | backend unit/integration | `cd backend && uv run pytest tests/test_submarine_geometry_check_tool.py` | `backend/tests/test_submarine_geometry_check_tool.py` | pending |
| 04-01-02 | 01 | 1 | GEO-01 | backend integration | `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_runtime_context.py` | `backend/tests/test_submarine_solver_dispatch_tool.py` | pending |
| 04-02-01 | 02 | 2 | GEO-02 | backend schema/assets | `cd backend && uv run pytest tests/test_submarine_domain_assets.py` | `backend/tests/test_submarine_domain_assets.py` | pending |
| 04-02-02 | 02 | 2 | GEO-02 | backend reporting | `cd backend && uv run pytest tests/test_submarine_result_report_tool.py` | `backend/tests/test_submarine_result_report_tool.py` | pending |
| 04-03-01 | 03 | 3 | GEO-03 | backend contract/tool | `cd backend && uv run pytest tests/test_submarine_design_brief_tool.py tests/test_submarine_geometry_check_tool.py` | `backend/tests/test_submarine_design_brief_tool.py` | pending |
| 04-03-02 | 03 | 3 | GEO-03 | backend integration | `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_runtime_context.py` | `backend/tests/test_submarine_runtime_context.py` | pending |
| 04-03-03 | 03 | 3 | GEO-01, GEO-02, GEO-03 | frontend contract/state | `cd frontend && node --test src/components/workspace/submarine-confirmation-actions.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-pipeline-shell.test.ts && corepack pnpm typecheck` | `frontend/src/components/workspace/submarine-confirmation-actions.test.ts` | pending |

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Consolidated draft review shows geometry suggestions, case sources, confidence, and applicability in one cockpit flow | GEO-01, GEO-02, GEO-03 | Requires real workbench rendering and human judgment on information density | Launch a submarine thread, run design brief plus geometry preflight, and confirm the runtime panel shows a reviewable calculation-plan draft before solver execution |
| Severe ambiguity interrupts early instead of waiting for final consolidated review | GEO-01, GEO-03 | Depends on end-to-end runtime transitions and operator-visible blocking language | Use a deliberately mis-scaled or family-ambiguous STL, trigger geometry preflight, and verify the next stage becomes confirmation-required or blocked before solver dispatch |
| Researcher edit plus approval survives refresh and becomes the actual solver input | GEO-03 | Requires persisted thread state across UI refresh | Edit one suggested reference value in the cockpit, approve the plan, refresh the page, and confirm the approved value is still visible and used by solver dispatch |
| Claim-level wording remains post-compute only | GEO-03 | Needs full pre-compute and post-compute comparison in the real cockpit | Compare the geometry/case approval flow before execution with the final report after execution and verify that claim-level labels appear only in the scientific gate path |

---

## Evidence To Capture Before Phase Sign-Off

- a `geometry-check.json` artifact showing structured geometry findings and suggested reference values
- a case/provenance artifact or report payload showing source labels, URLs, applicability conditions, and missing-evidence disclosure
- a persisted calculation-plan draft or approved-plan artifact showing suggestion provenance and researcher edits
- cockpit screenshots for:
  - consolidated draft review,
  - severe ambiguity early interruption,
  - approved plan surviving refresh

---

## Exit Criteria

Phase 4 is not ready for execution sign-off until all of the following are true:

- `GEO-01` is backed by deterministic geometry-trust checks plus visible operator guidance
- `GEO-02` is backed by provenance-aware case metadata and explicit acceptance-profile quality
- `GEO-03` is backed by a researcher-approved calculation-plan gate that blocks execution until confirmed
- at least one real cockpit run demonstrates the semantic separation between pre-compute approval and post-compute claim level
- `nyquist_compliant: true` remains valid because every plan task maps to an automated or explicitly manual verification path
