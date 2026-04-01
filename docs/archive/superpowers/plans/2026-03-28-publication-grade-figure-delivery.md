# Publication-Grade Figure Delivery v1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade deterministic figure generation so supported submarine postprocess outputs become provenance-rich scientific delivery artifacts instead of loose preview PNGs.

**Architecture:** Add a focused backend figure-manifest layer, keep solver-dispatch rendering deterministic, propagate figure-delivery summaries into final reporting, and enrich the existing requested-result cards in the workbench with manifest-driven caption and provenance details.

**Tech Stack:** Python, Pillow, DeerFlow submarine domain modules, pytest, TypeScript, Node test runner, React runtime panel

---

## File Structure

- Create: `backend/packages/harness/deerflow/domain/submarine/figure_delivery.py`
  - typed figure manifest helpers and summary builders
- Modify: `backend/packages/harness/deerflow/domain/submarine/postprocess.py`
  - richer deterministic figure rendering and manifest emission
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - load `figure-manifest.json` and emit `figure_delivery_summary`
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`
  - cover figure manifest generation and richer figure metadata
- Modify: `backend/tests/test_submarine_result_report_tool.py`
  - cover report propagation of figure delivery
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - parse figure delivery summaries and enrich result cards
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - cover figure manifest labels and provenance parsing
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - render figure caption / provenance in requested-result cards
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - record the new figure-delivery status

## Chunk 1: Figure Contract Layer

### Task 1: Add figure manifest contract helpers

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/figure_delivery.py`
- Modify: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Add domain coverage for a typed figure-manifest contract with:

- `figure_id`
- `output_id`
- `title`
- `caption`
- `render_status`
- `artifact_virtual_paths`

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k figure_manifest`
Expected: FAIL because the figure manifest contract layer does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `figure_delivery.py` with:

- figure item normalization helpers
- manifest builder
- a compact figure-delivery summary builder that reporting can reuse later

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k figure_manifest`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/figure_delivery.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add submarine figure delivery contracts"
```

## Chunk 2: Deterministic Figure Delivery

### Task 2: Emit `figure-manifest.json` from postprocess export

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/postprocess.py`
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Write the failing test**

Add solver-dispatch coverage that expects:

- `figure-manifest.json` to be written when a supported figure output is exported
- each figure entry to contain caption and artifact metadata

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k figure_manifest`
Expected: FAIL because figure manifests are not emitted yet.

- [ ] **Step 3: Write minimal implementation**

In `postprocess.py`:

- collect per-figure metadata during export
- write `figure-manifest.json`
- add the manifest artifact path to exported artifacts

Use the new helper module rather than embedding the whole manifest shape inline.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k figure_manifest`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/postprocess.py backend/tests/test_submarine_solver_dispatch_tool.py
git commit -m "feat: emit submarine figure delivery manifests"
```

### Task 3: Upgrade deterministic figure metadata and captions

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/postprocess.py`
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Write the failing test**

Extend figure-export coverage so supported figures now expose richer metadata such as:

- selector summary
- field name
- sample count
- value range
- render quality or render status

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k figure_provenance`
Expected: FAIL because figure provenance fields are incomplete.

- [ ] **Step 3: Write minimal implementation**

Upgrade the renderer / export metadata so:

- captions are stable and human-readable
- wake-slice selector provenance is explicit
- surface-pressure selector provenance is explicit
- manifest records enough detail for reporting and UI use

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k "figure_manifest or figure_provenance"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/postprocess.py backend/tests/test_submarine_solver_dispatch_tool.py
git commit -m "feat: enrich submarine figure provenance metadata"
```

## Chunk 3: Reporting Integration

### Task 4: Add figure delivery summary to final reporting

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing test**

Add result-report coverage that expects:

- `figure_delivery_summary` in `final-report.json`
- `figure-manifest.json` to appear in report artifacts
- figure captions or provenance highlights to be summarized

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k figure_delivery_summary`
Expected: FAIL because reporting does not yet load figure manifests.

- [ ] **Step 3: Write minimal implementation**

In `reporting.py`:

- load `figure-manifest.json`
- emit a compact `figure_delivery_summary`
- link manifest artifact paths into the final report
- add a compact figure-delivery section to Markdown / HTML output

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k figure_delivery_summary`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/reporting.py backend/tests/test_submarine_result_report_tool.py
git commit -m "feat: add submarine figure delivery summaries"
```

## Chunk 4: Workbench Figure Delivery

### Task 5: Parse figure delivery summaries in workbench utilities

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`

- [ ] **Step 1: Write the failing test**

Add utility coverage for:

- figure manifest labels
- figure caption summary
- selector provenance strings
- figure artifact entrypoints

- [ ] **Step 2: Run test to verify it fails**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL because figure-delivery parsing does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add a figure-delivery summary parser and extend result-card helpers so cards can consume:

- caption
- selector provenance
- manifest-backed artifact lists

- [ ] **Step 4: Run test to verify it passes**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.utils.ts frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
git commit -m "feat: parse submarine figure delivery summaries"
```

### Task 6: Render richer figure provenance in requested-result cards

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`

- [ ] **Step 1: Run the current type check as the UI red gate**

Run: `corepack pnpm exec tsc --noEmit`
Expected: current UI does not yet wire the new figure-delivery fields.

- [ ] **Step 2: Write minimal implementation**

In `submarine-runtime-panel.tsx`:

- feed figure-delivery summaries into requested-result cards
- render caption and selector provenance near the preview
- expose manifest-backed artifact entrypoints without creating a new parallel panel

- [ ] **Step 3: Run type verification**

Run: `corepack pnpm exec tsc --noEmit`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.tsx
git commit -m "feat: surface submarine figure delivery provenance"
```

## Chunk 5: Docs And Focused Regression

### Task 7: Update status docs and run regression checks

**Files:**
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Update docs**

Record:

- the new `figure-manifest.json`
- the new `figure_delivery_summary`
- improved figure provenance and caption delivery
- workbench figure-card upgrades

- [ ] **Step 2: Run backend verification**

Run: `uv run pytest tests/test_submarine_domain_assets.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py -q`
Expected: PASS

- [ ] **Step 3: Run frontend utility verification**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 4: Run TypeScript verification**

Run: `corepack pnpm exec tsc --noEmit`
Expected: PASS

- [ ] **Step 5: Run focused lint verification**

Run: `corepack pnpm exec eslint src/components/workspace/submarine-runtime-panel.tsx src/components/workspace/submarine-runtime-panel.utils.ts src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md
git commit -m "docs: record submarine figure delivery status"
```
