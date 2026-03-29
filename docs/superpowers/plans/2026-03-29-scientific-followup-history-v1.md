# Scientific Followup History v1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic scientific follow-up audit trail and surface the latest follow-up state in reports and the workbench.

**Architecture:** Create a dedicated follow-up history helper in the submarine domain, make the follow-up tool append one history entry per invocation, preserve the history pointer through result-report refreshes, and expose a compact report/workbench summary from the persisted history artifact. Keep the feature bounded to auditability, not auto-loop control.

**Tech Stack:** Python, Pydantic, DeerFlow built-in tools, pytest, React/TypeScript

---

## File Map

- Create: `backend/packages/harness/deerflow/domain/submarine/followup.py`
  - follow-up history record and summary helpers
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
  - add runtime pointer for follow-up history
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - load follow-up history and emit `scientific_followup_summary`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`
  - preserve follow-up history pointer in refreshed runtime state
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
  - append history entries on all major branches
- Modify: `backend/tests/test_submarine_scientific_followup_tool.py`
  - history-writing coverage
- Modify: `backend/tests/test_submarine_result_report_tool.py`
  - report summary coverage
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - summarize report payload follow-up history
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - parsing coverage
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - compact UI section
- Modify: `docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - record the new audit-trail behavior

## Chunk 1: Backend Followup History Artifact

### Task 1: Record one history entry for each scientific follow-up invocation

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/followup.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
- Modify: `backend/tests/test_submarine_scientific_followup_tool.py`

- [ ] **Step 1: Write the failing tests**

Cover:

- executed solver dispatch + report refresh -> history entry records refreshed report outcome
- planned / failed dispatch -> history entry records non-refreshed stop
- manual or not-needed handoff -> history entry records non-executing outcome

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `uv run pytest tests/test_submarine_scientific_followup_tool.py -q -k "history or followup"`
Expected: FAIL because follow-up history is not persisted yet.

- [ ] **Step 3: Write minimal implementation**

Implement:

- history load / append / summary helper
- runtime pointer preservation for the follow-up history artifact
- follow-up tool writes one record per invocation branch

- [ ] **Step 4: Run the backend follow-up tests to verify they pass**

Run: `uv run pytest tests/test_submarine_scientific_followup_tool.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/followup.py backend/packages/harness/deerflow/domain/submarine/contracts.py backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py backend/tests/test_submarine_scientific_followup_tool.py
git commit -m "feat: record submarine scientific followup history"
```

## Chunk 2: Report Summary Propagation

### Task 2: Surface compact follow-up history in refreshed report payloads

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing tests**

Cover:

- existing follow-up history pointer -> result report emits `scientific_followup_summary`
- refreshed runtime keeps the history pointer after report generation

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k "followup"`
Expected: FAIL because report payloads do not surface follow-up summary yet.

- [ ] **Step 3: Write minimal implementation**

Implement:

- report-side history loading
- compact payload summary generation
- markdown / HTML summary section if non-empty
- runtime pointer propagation

- [ ] **Step 4: Run the targeted result-report tests to verify they pass**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k "followup"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/reporting.py backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py backend/tests/test_submarine_result_report_tool.py
git commit -m "feat: surface submarine scientific followup history"
```

## Chunk 3: Workbench And Docs

### Task 3: Show the follow-up audit summary in the workbench and record the stage

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- Modify: `docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Write the failing frontend tests**

Cover:

- follow-up summary parsing
- artifact classification for the new history artifact if needed

- [ ] **Step 2: Run the targeted frontend tests to verify they fail**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL because the summary is not parsed/rendered yet.

- [ ] **Step 3: Write minimal implementation**

Implement:

- compact workbench summary builder
- UI section for latest follow-up outcome and artifact links
- status-spec update

- [ ] **Step 4: Run regression verification**

Run:

- `uv run pytest tests/test_submarine_scientific_followup_tool.py tests/test_submarine_result_report_tool.py -q`
- `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
- `corepack pnpm exec tsc --noEmit`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.utils.ts frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts frontend/src/components/workspace/submarine-runtime-panel.tsx docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md
git commit -m "docs: record submarine scientific followup history"
```
