# Scientific Auto-Followup Tool v1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dedicated DeerFlow tool that reads the latest scientific remediation handoff and executes supported auto-followup actions when they are ready.

**Architecture:** Keep follow-up execution out of result reporting. Add a separate built-in tool that resolves the latest handoff artifact from runtime state, validates its status, and delegates to existing built-in submarine tools for execution. Non-executable handoffs stay explicit no-ops.

**Tech Stack:** Python, DeerFlow built-in tools, Pydantic runtime contracts, pytest

---

## File Map

- Modify: `backend/packages/harness/deerflow/domain/submarine/handoff.py`
  - handoff artifact loading and validation helpers
- Create: `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
  - execute supported auto-followup handoffs
- Modify: `backend/packages/harness/deerflow/tools/builtins/__init__.py`
  - export the new built-in tool
- Create: `backend/tests/test_submarine_scientific_followup_tool.py`
  - manual/no-op refusal and executable delegation coverage
- Modify: `docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - record the new tool

## Chunk 1: Tool Skeleton And Refusal Paths

### Task 1: Load the latest handoff artifact and refuse non-executable states cleanly

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/handoff.py`
- Create: `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
- Create: `backend/tests/test_submarine_scientific_followup_tool.py`

- [ ] **Step 1: Write the failing tests**

Cover:

- missing `supervisor_handoff_virtual_path` -> error message
- `manual_followup_required` -> explanatory no-op
- `not_needed` -> explanatory no-op

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `uv run pytest tests/test_submarine_scientific_followup_tool.py -q -k "manual or not_needed or missing"`
Expected: FAIL because the tool does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Implement:

- handoff artifact resolver/loader
- tool entrypoint
- non-executing message behavior for manual/no-op states

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run: `uv run pytest tests/test_submarine_scientific_followup_tool.py -q -k "manual or not_needed or missing"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/handoff.py backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py backend/tests/test_submarine_scientific_followup_tool.py
git commit -m "feat: add submarine scientific followup tool"
```

## Chunk 2: Executable Handoff Delegation

### Task 2: Execute supported follow-up handoffs through existing built-in tools

**Files:**
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
- Modify: `backend/tests/test_submarine_scientific_followup_tool.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/__init__.py`

- [ ] **Step 1: Write the failing tests**

Cover:

- `ready_for_auto_followup` + `submarine_solver_dispatch` delegates into solver dispatch with `execute_now=true`
- `ready_for_auto_followup` + `submarine_result_report` delegates into result reporting

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `uv run pytest tests/test_submarine_scientific_followup_tool.py -q -k "ready_for_auto_followup"`
Expected: FAIL because executable delegation is not implemented yet.

- [ ] **Step 3: Write minimal implementation**

Implement:

- supported tool dispatch map
- solver-dispatch delegation with forced execution
- result-report delegation with handoff-provided args when present
- unsupported tool-name guardrail

- [ ] **Step 4: Run the tool tests to verify they pass**

Run: `uv run pytest tests/test_submarine_scientific_followup_tool.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py backend/packages/harness/deerflow/tools/builtins/__init__.py backend/tests/test_submarine_scientific_followup_tool.py
git commit -m "feat: execute submarine scientific followup handoffs"
```

## Chunk 3: Docs And Regression

### Task 3: Record the new tool and verify the backend slice

**Files:**
- Modify: `docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Update the status spec**

Record:

- the new `submarine_scientific_followup` tool
- explicit non-execution for manual/no-op handoffs
- executable delegation for supported auto-followup targets

- [ ] **Step 2: Run backend verification**

Run: `uv run pytest tests/test_submarine_domain_assets.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py tests/test_submarine_scientific_followup_tool.py -q`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md
git commit -m "docs: record submarine scientific followup tool"
```
