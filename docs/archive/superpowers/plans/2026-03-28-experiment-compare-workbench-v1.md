# Experiment Compare Workbench v1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose experiment baseline-versus-variant comparisons as structured report evidence and compact workbench compare cards.

**Architecture:** Extend backend reporting to emit a stable `experiment_compare_summary` derived from `experiment-manifest.json` and `run-compare-summary.json`, then let the front-end workbench render that summary instead of reconstructing compare semantics itself. Keep the compare UI inside the existing runtime panel so the product remains open-ended rather than becoming a dedicated compare workflow shell.

**Tech Stack:** Python, DeerFlow submarine domain reporting, pytest, TypeScript, Node test runner, React runtime panel

---

## File Map

- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - load compare artifacts and build a structured compare summary
- Modify: `backend/tests/test_submarine_result_report_tool.py`
  - add report coverage for compare summary propagation
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - parse compare summaries into UI-ready data
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - cover compare summary parsing and metric delta rendering
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - render compare cards inside the runtime panel
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - record the new compare workbench behavior

## Chunk 1: Backend Compare Summary

### Task 1: Emit `experiment_compare_summary` from result reporting

**Files:**
- Modify: `backend/tests/test_submarine_result_report_tool.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`

- [ ] **Step 1: Write the failing test**

Extend the existing experiment/report fixtures so the final report is required to expose:

- `experiment_compare_summary.compare_count`
- resolved baseline/candidate solver-result paths
- per-comparison metric deltas
- compare status lines in Markdown / HTML

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k experiment_compare_summary`
Expected: FAIL because reporting does not yet emit the new compare summary.

- [ ] **Step 3: Write minimal implementation**

In `reporting.py`:

- add a compare-summary builder that joins:
  - `experiment-manifest.json`
  - `run-compare-summary.json`
- resolve run-record-backed artifact entrypoints
- emit `experiment_compare_summary` into the final payload
- render a compact compare section in Markdown / HTML

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k experiment_compare_summary`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/reporting.py backend/tests/test_submarine_result_report_tool.py
git commit -m "feat: add submarine experiment compare summaries"
```

## Chunk 2: Frontend Compare Parsing

### Task 2: Parse compare summaries into stable workbench data

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`

- [ ] **Step 1: Write the failing test**

Add utility coverage that expects:

- `buildSubmarineExperimentCompareSummary(...)` to exist
- compare status labels to be normalized
- metric delta lines to be formatted from structured `metric_deltas`
- baseline/candidate artifact paths to be preserved

- [ ] **Step 2: Run test to verify it fails**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL because the compare summary utility does not exist yet.

- [ ] **Step 3: Write minimal implementation**

In `submarine-runtime-panel.utils.ts`:

- add a compare-summary type
- parse `experiment_compare_summary`
- format compact metric delta labels
- preserve compare artifact entrypoints for the UI

- [ ] **Step 4: Run test to verify it passes**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.utils.ts frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
git commit -m "feat: parse submarine experiment compare summaries"
```

## Chunk 3: Workbench Compare Cards

### Task 3: Render compact compare cards in the runtime panel

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`

- [ ] **Step 1: Write the failing test**

If utility changes are enough to drive card rendering, add or extend tests so the data contract requires:

- compare entries with metric deltas
- baseline/candidate artifact entrypoints

Reuse the utility tests rather than introducing a new UI test harness.

- [ ] **Step 2: Run targeted verification to verify the contract is red**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL until the runtime panel consumes the new compare summary cleanly.

- [ ] **Step 3: Write minimal implementation**

In `submarine-runtime-panel.tsx`:

- build the compare summary from `finalReport`
- render compare cards in the existing runtime health area
- show:
  - baseline vs candidate ids
  - study type / variant
  - compare status
  - metric delta lines
  - artifact links

- [ ] **Step 4: Run type verification**

Run: `corepack pnpm exec tsc --noEmit`
Expected: PASS

- [ ] **Step 5: Run lint verification**

Run: `corepack pnpm exec eslint src/components/workspace/submarine-runtime-panel.tsx src/components/workspace/submarine-runtime-panel.utils.ts src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.tsx
git commit -m "feat: render submarine experiment compare cards"
```

## Chunk 4: Docs And Focused Regression

### Task 4: Record the new compare workbench behavior and verify the slice

**Files:**
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Update the status spec**

Record:

- `experiment_compare_summary`
- compare-card workbench behavior
- remaining compare-workspace gaps

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
git commit -m "docs: record submarine experiment compare workbench status"
```
