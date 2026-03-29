# Scientific Followup Report Refresh v1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a successful scientific follow-up rerun automatically regenerate the final report so the runtime lands back on a refreshed report-stage evidence snapshot.

**Architecture:** Extend the existing `submarine_scientific_followup` tool instead of adding a second orchestration tool. Keep the chain bounded: solver dispatch may trigger one report refresh, and then execution stops.

**Tech Stack:** Python, DeerFlow built-in tools, pytest

---

## File Map

- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
  - chain result reporting after successful dispatch execution
- Modify: `backend/tests/test_submarine_scientific_followup_tool.py`
  - report-refresh chain tests
- Modify: `docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - record the refreshed behavior

## Chunk 1: Refresh Chain

### Task 1: Refresh result reporting after successful solver follow-up execution

**Files:**
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
- Modify: `backend/tests/test_submarine_scientific_followup_tool.py`

- [ ] **Step 1: Write the failing tests**

Cover:

- executed solver dispatch -> follow-up calls result reporting and returns report-stage output
- planned or failed solver dispatch -> no report refresh

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `uv run pytest tests/test_submarine_scientific_followup_tool.py -q -k "refresh or executed"`
Expected: FAIL because report refresh chaining is not implemented yet.

- [ ] **Step 3: Write minimal implementation**

Implement:

- solver-dispatch result inspection
- bounded one-time report refresh
- pass-through behavior for planned/failed dispatch results

- [ ] **Step 4: Run the tool tests to verify they pass**

Run: `uv run pytest tests/test_submarine_scientific_followup_tool.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py backend/tests/test_submarine_scientific_followup_tool.py
git commit -m "feat: refresh reports after submarine scientific followup"
```

## Chunk 2: Docs And Regression

### Task 2: Record the refresh chain and verify the backend slice

**Files:**
- Modify: `docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Update the status spec**

Record:

- solver-rerun follow-up now refreshes result reporting automatically
- the chain remains bounded to one dispatch plus one report refresh

- [ ] **Step 2: Run backend verification**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py tests/test_submarine_scientific_followup_tool.py -q`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md
git commit -m "docs: record submarine followup report refresh"
```
