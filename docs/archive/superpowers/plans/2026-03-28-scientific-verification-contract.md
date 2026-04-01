# Scientific Verification Contract Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first research-facing scientific verification contract that is planned in the submarine design brief, assessed in the final report, and surfaced in the DeerFlow workbench.

**Architecture:** Extend the submarine case acceptance profile with an effective verification-requirement layer, compute a deterministic scientific verification assessment from solver metrics and exported artifacts, and expose the same structure in both the backend artifacts and the submarine workbench. Keep this separate from the existing delivery readiness gates so baseline deliverability and research readiness do not get conflated.

**Tech Stack:** Python, Pydantic, DeerFlow domain modules, pytest, TypeScript, existing submarine workbench utilities

---

## Chunk 1: Backend Contract

### Task 1: Add verification requirement models and effective-profile helpers

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/models.py`
- Create: `backend/packages/harness/deerflow/domain/submarine/verification.py`
- Test: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Add assertions that the selected case exposes effective scientific verification requirements even when the JSON case file does not manually enumerate all of them.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q`
Expected: FAIL because effective verification requirements are not yet exposed.

- [ ] **Step 3: Write minimal implementation**

Add typed verification-requirement models and helper functions that derive a default research verification checklist from the acceptance profile and task type.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q`
Expected: PASS

### Task 2: Add design-brief visibility for scientific verification requirements

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/design_brief.py`
- Test: `backend/tests/test_submarine_design_brief_tool.py`

- [ ] **Step 1: Write the failing test**

Add a test that a design brief for `darpa_suboff_bare_hull_resistance` includes structured scientific verification requirements in JSON and Markdown.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_design_brief_tool.py -q -k verification`
Expected: FAIL because the design brief payload does not include verification requirements yet.

- [ ] **Step 3: Write minimal implementation**

Populate `scientific_verification_requirements` in the design brief payload and render a concise Markdown/HTML section.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_design_brief_tool.py -q -k verification`
Expected: PASS

## Chunk 2: Final Report Assessment

### Task 3: Add scientific verification assessment to final report

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/verification.py`
- Test: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing test**

Add report-tool coverage that expects:
- a structured scientific verification assessment
- missing mesh/domain/time-step studies to be flagged as missing evidence
- single-run checks such as final residual and force-coefficient stability to be evaluated when data exists

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k scientific_verification`
Expected: FAIL because the final report does not include scientific verification assessment yet.

- [ ] **Step 3: Write minimal implementation**

Compute scientific verification requirement statuses from solver metrics and exported artifacts, add them to `final-report.json`, and render them in Markdown/HTML.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k scientific_verification`
Expected: PASS

## Chunk 3: Workbench Visibility

### Task 4: Surface verification requirements and assessment in the submarine workbench

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`

- [ ] **Step 1: Write the failing test**

Add utility tests for:
- design-brief scientific verification requirement summaries
- final-report scientific verification assessment summaries

- [ ] **Step 2: Run test to verify it fails**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL because the workbench utilities do not build verification summaries yet.

- [ ] **Step 3: Write minimal implementation**

Add summary builders and render a DeerFlow-style verification block in the existing workbench panels.

- [ ] **Step 4: Run test to verify it passes**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

## Chunk 4: Verification and Documentation

### Task 5: Update status docs and run focused regression verification

**Files:**
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Update docs**

Record the new scientific verification contract, its scope, and its current limitations.

- [ ] **Step 2: Run focused backend verification**

Run: `uv run pytest tests/test_submarine_domain_assets.py tests/test_submarine_design_brief_tool.py tests/test_submarine_result_report_tool.py -q`
Expected: PASS

- [ ] **Step 3: Run focused frontend verification**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 4: Run TypeScript verification**

Run: `cd frontend && node_modules/.bin/tsc.cmd --noEmit`
Expected: PASS
