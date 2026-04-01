# Submarine Requested Postprocess Exports Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make selected user-requested CFD outputs drive postprocess artifact export so DeerFlow runs can deliver more than coefficients and reports.

**Architecture:** Extend the current requested-output contract into the solver-dispatch stage by introducing a small postprocess export plan, collecting known postProcessing files into stable artifacts, and reflecting delivery status in the final report and workbench. Keep scope tight: support structured exports for pressure/wake outputs first and leave streamlines explicitly unsupported.

**Tech Stack:** Python, DeerFlow submarine runtime modules, pytest, TypeScript workbench utilities.

---

### Task 1: Requested Postprocess Export Tests

**Files:**
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing tests**

Add tests that:
- simulate a solver run producing postProcessing files for requested outputs
- assert stable exported artifacts are written into solver-dispatch outputs
- assert delivery status flips from planned to delivered in report stage

- [ ] **Step 2: Run tests to verify they fail**

Run:
- `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k postprocess`
- `uv run pytest tests/test_submarine_result_report_tool.py -q -k postprocess`

Expected: FAIL because requested postprocess exports are not collected yet.

### Task 2: Solver Dispatch Export Collection

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/output_contract.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Write minimal implementation**

Implement:
- a small requested postprocess plan for supported output IDs
- collection/copy of known postProcessing files into stable output artifacts
- dispatch payload/runtime propagation for those artifacts
- updated delivery-plan logic for supported pressure/wake outputs

- [ ] **Step 2: Run focused tests**

Run:
- `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k postprocess`

Expected: PASS

### Task 3: Final Report Delivery Status

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`

- [ ] **Step 1: Update report delivery logic**

Ensure final report delivery status recognizes exported pressure/wake artifacts.

- [ ] **Step 2: Run focused tests**

Run:
- `uv run pytest tests/test_submarine_result_report_tool.py -q -k postprocess`

Expected: PASS

### Task 4: Workbench and Docs

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Update artifact copy and status wording**

Expose the new artifact names cleanly in the workbench utility layer.

- [ ] **Step 2: Run verification**

Run:
- `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
- `frontend/node_modules/.bin/tsc.cmd --noEmit`

Expected: PASS

### Task 5: Final Regression

**Files:**
- No additional files

- [ ] **Step 1: Run backend regression**

Run:
- `uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py -q`
- `uv run pytest tests -q -k submarine`

Expected: PASS
