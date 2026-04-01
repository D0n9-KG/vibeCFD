# Scientific Remediation Handoff v1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Emit explicit next-tool handoff contracts from remediation plans so the supervisor can act on auto-executable follow-up steps without reconstructing them manually.

**Architecture:** Add a focused handoff helper that maps remediation actions into concrete tool suggestions, integrate the resulting handoff into final reporting and runtime state, and surface it in the runtime panel as the next recommended execution contract.

**Tech Stack:** Python, DeerFlow submarine reporting and contracts, pytest, TypeScript, Node test runner, React runtime panel

---

## File Map

- Create: `backend/packages/harness/deerflow/domain/submarine/handoff.py`
  - remediation action to tool-call mapping
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
  - allow result-reporting to update the latest handoff pointer cleanly
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - emit remediation handoff payload, artifact, and runtime pointer
- Modify: `backend/tests/test_submarine_domain_assets.py`
  - helper coverage for handoff selection logic
- Modify: `backend/tests/test_submarine_result_report_tool.py`
  - final report / runtime handoff coverage
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - parse remediation handoff summaries
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - remediation handoff parsing tests
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - render the handoff block
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - record the new handoff behavior

## Chunk 1: Backend Handoff Helper

### Task 1: Map remediation actions to next-tool handoffs

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/handoff.py`
- Modify: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Cover:

- `execute-scientific-studies` -> `submarine_solver_dispatch`
- manual-only validation reference -> manual handoff
- no actions -> `not_needed`

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k scientific_remediation_handoff`
Expected: FAIL because the handoff helper does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `handoff.py` with a helper like:

```python
def build_scientific_remediation_handoff(*, snapshot, scientific_remediation_summary, artifact_virtual_paths=None) -> dict: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k scientific_remediation_handoff`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/handoff.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add submarine scientific remediation handoff builder"
```

## Chunk 2: Reporting Integration

### Task 2: Emit remediation handoff from result reporting

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing test**

Extend reporting coverage so final payloads require:

- `scientific_remediation_handoff`
- `supervisor_handoff_virtual_path` updated to the report-stage handoff artifact
- handoff artifact written to disk

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k scientific_remediation_handoff`
Expected: FAIL because reporting does not emit the handoff yet.

- [ ] **Step 3: Write minimal implementation**

In `reporting.py`:

- build the remediation handoff
- write `scientific-remediation-handoff.json`
- include the handoff in final payload
- point `supervisor_handoff_virtual_path` to the new artifact

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k scientific_remediation_handoff`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/reporting.py backend/tests/test_submarine_result_report_tool.py
git commit -m "feat: emit submarine scientific remediation handoff"
```

## Chunk 3: Frontend Handoff Block

### Task 3: Parse and render remediation handoff summaries

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`

- [ ] **Step 1: Write the failing test**

Add utility coverage that expects:

- handoff status labels
- tool name display
- tool-argument summary preservation
- manual-action lists

- [ ] **Step 2: Run test to verify it fails**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL because the remediation handoff parser does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Parse `scientific_remediation_handoff` and render it in the runtime panel near remediation planning.

- [ ] **Step 4: Run type and lint verification**

Run: `corepack pnpm exec tsc --noEmit`
Expected: PASS

Run: `corepack pnpm exec eslint src/components/workspace/submarine-runtime-panel.tsx src/components/workspace/submarine-runtime-panel.utils.ts src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.tsx frontend/src/components/workspace/submarine-runtime-panel.utils.ts frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
git commit -m "feat: surface submarine scientific remediation handoff"
```

## Chunk 4: Docs And Regression

### Task 4: Record the handoff layer and verify the full slice

**Files:**
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Update the status spec**

Record:

- remediation handoff payload
- report-stage handoff artifact
- runtime pointer update

- [ ] **Step 2: Run backend verification**

Run: `uv run pytest tests/test_submarine_domain_assets.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py -q`
Expected: PASS

- [ ] **Step 3: Run frontend verification**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 4: Run type and lint verification**

Run: `corepack pnpm exec tsc --noEmit`
Expected: PASS

Run: `corepack pnpm exec eslint src/components/workspace/submarine-runtime-panel.tsx src/components/workspace/submarine-runtime-panel.utils.ts src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md
git commit -m "docs: record submarine scientific remediation handoff"
```
