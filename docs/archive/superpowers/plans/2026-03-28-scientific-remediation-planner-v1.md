# Scientific Remediation Planner v1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Emit a structured scientific remediation plan that explains how blocked or claim-limited CFD runs should close their evidence gaps.

**Architecture:** Add a focused remediation helper that translates scientific gate and evidence summaries into deterministic remediation actions, then emit that plan into final reporting and surface it in the runtime workbench. Keep the first version planning-only so it can power future auto-execution without forcing the product into a rigid workflow engine.

**Tech Stack:** Python, DeerFlow submarine reporting helpers, pytest, TypeScript, Node test runner, React runtime panel

---

## File Map

- Create: `backend/packages/harness/deerflow/domain/submarine/remediation.py`
  - remediation-plan builder and gap-to-action mapping
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - emit remediation summary and write remediation artifact
- Modify: `backend/tests/test_submarine_domain_assets.py`
  - planner helper coverage
- Modify: `backend/tests/test_submarine_result_report_tool.py`
  - final report / artifact coverage
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - parse remediation summary into UI-ready data
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - remediation summary parsing tests
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - render remediation cards
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - record the new remediation-plan behavior

## Chunk 1: Backend Remediation Planner

### Task 1: Build remediation actions from scientific evidence

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/remediation.py`
- Modify: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Add planner coverage for:

- missing study evidence -> `solver-dispatch` auto-executable action
- missing validation reference -> `supervisor-review` manual action
- research-ready -> `not_needed` plan with zero actions

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k scientific_remediation_plan`
Expected: FAIL because the remediation helper does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `remediation.py` with a helper like:

```python
def build_scientific_remediation_summary(
    *,
    scientific_supervisor_gate,
    research_evidence_summary,
    scientific_verification_assessment=None,
    scientific_study_summary=None,
    artifact_virtual_paths=None,
) -> dict: ...
```

Implement deterministic action mapping for:

- missing study evidence
- missing validation reference
- provenance/reporting gaps
- research-ready no-op

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k scientific_remediation_plan`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/remediation.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add submarine scientific remediation planner"
```

## Chunk 2: Reporting Integration

### Task 2: Emit remediation summary and artifact from final reporting

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing test**

Extend result-report coverage so final payloads require:

- `scientific_remediation_summary.plan_status`
- remediation actions in the payload
- `scientific-remediation-plan.json` artifact path
- remediation content rendered in Markdown / HTML

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k scientific_remediation_summary`
Expected: FAIL because final reporting does not emit remediation summaries yet.

- [ ] **Step 3: Write minimal implementation**

In `reporting.py`:

- call the remediation helper
- include `scientific_remediation_summary` in `final-report.json`
- write `scientific-remediation-plan.json`
- render a compact remediation section in Markdown / HTML

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k scientific_remediation_summary`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/reporting.py backend/tests/test_submarine_result_report_tool.py
git commit -m "feat: emit submarine scientific remediation summaries"
```

## Chunk 3: Frontend Remediation Workbench

### Task 3: Parse remediation summaries for the runtime panel

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`

- [ ] **Step 1: Write the failing test**

Add utility coverage that expects:

- remediation plan status labels
- current vs target claim labels
- owner-stage and execution-mode labels
- required-artifact preservation

- [ ] **Step 2: Run test to verify it fails**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL because the remediation summary parser does not exist yet.

- [ ] **Step 3: Write minimal implementation**

In `submarine-runtime-panel.utils.ts`:

- add remediation summary types
- parse `scientific_remediation_summary`
- normalize action labels for the UI

- [ ] **Step 4: Run test to verify it passes**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.utils.ts frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
git commit -m "feat: parse submarine scientific remediation summaries"
```

### Task 4: Render remediation cards in the runtime panel

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`

- [ ] **Step 1: Reuse the red utility contract**

Use the failing remediation-summary utility test as the contract for the new UI block. Do not add a separate UI harness.

- [ ] **Step 2: Write minimal implementation**

In `submarine-runtime-panel.tsx`:

- build the remediation summary from `finalReport`
- render a compact remediation block near scientific gate / evidence
- show action cards with owner stage, execution mode, evidence gap, and artifacts

- [ ] **Step 3: Run type verification**

Run: `corepack pnpm exec tsc --noEmit`
Expected: PASS

- [ ] **Step 4: Run lint verification**

Run: `corepack pnpm exec eslint src/components/workspace/submarine-runtime-panel.tsx src/components/workspace/submarine-runtime-panel.utils.ts src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.tsx
git commit -m "feat: render submarine scientific remediation cards"
```

## Chunk 4: Docs And Regression

### Task 5: Record remediation planning and verify the full slice

**Files:**
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Update the status spec**

Record:

- `scientific_remediation_summary`
- remediation-plan artifact
- workbench action-card behavior
- remaining gap: planning exists, execution loop still absent

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
git commit -m "docs: record submarine scientific remediation planning"
```
