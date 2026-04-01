# Result Reporting Decomposition v1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompose the submarine result-reporting layer into focused backend modules while preserving current payloads, artifacts, and rendering behavior.

**Architecture:** Extract acceptance/benchmark logic, summary builders, and markdown/HTML rendering out of `reporting.py`, leaving `run_result_report(...)` as the report assembly orchestration entrypoint. Preserve external behavior and verify with focused result-report regression tests.

**Tech Stack:** Python, pytest, DeerFlow domain helpers

---

## File Map

- Create: `backend/packages/harness/deerflow/domain/submarine/reporting_acceptance.py`
  - acceptance and benchmark gate logic
- Create: `backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py`
  - scientific study / experiment / figure summary builders
- Create: `backend/packages/harness/deerflow/domain/submarine/reporting_render.py`
  - markdown and HTML rendering helpers
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - orchestration-only entrypoint plus final file writes
- Modify: `backend/tests/test_submarine_result_report_tool.py`
  - add or tighten regression coverage for extracted behavior if current coverage is insufficient

## Chunk 1: Acceptance Extraction

### Task 1: Move scientific acceptance logic into a dedicated module

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/reporting_acceptance.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing regression coverage**

Cover:

- benchmark comparison still appears in `acceptance_assessment`
- case-aware blocking and warning semantics stay unchanged

- [ ] **Step 2: Run the targeted tests to verify the failure**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k "benchmark or acceptance"`
Expected: FAIL once the extraction starts and before imports/call sites are fully rewired.

- [ ] **Step 3: Write minimal implementation**

Extract the acceptance helpers and import them back into `reporting.py`.

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k "benchmark or acceptance"`
Expected: PASS

## Chunk 2: Summary Builder Extraction

### Task 2: Move structured report-block builders out of the entrypoint file

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing regression coverage**

Cover:

- `scientific_study_summary`
- `experiment_summary`
- `experiment_compare_summary`
- `figure_delivery_summary`

- [ ] **Step 2: Run the targeted tests to verify the failure**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k "study or experiment or figure"`
Expected: FAIL during partial extraction if wiring is incomplete.

- [ ] **Step 3: Write minimal implementation**

Extract the summary builders and rewire `run_result_report(...)` to consume them.

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k "study or experiment or figure"`
Expected: PASS

## Chunk 3: Rendering Extraction

### Task 3: Move markdown and HTML rendering into a dedicated render module

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/reporting_render.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing regression coverage**

Cover:

- final report markdown still includes current scientific sections
- final report HTML still includes current scientific sections

- [ ] **Step 2: Run the targeted tests to verify the failure**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k "markdown or html or followup"`
Expected: FAIL during extraction until the render wiring is restored.

- [ ] **Step 3: Write minimal implementation**

Extract the render helpers and keep `reporting.py` focused on payload assembly and file writes.

- [ ] **Step 4: Run regression verification**

Run:

- `uv run pytest tests/test_submarine_result_report_tool.py -q`
- `uv run pytest tests/test_submarine_scientific_followup_tool.py tests/test_submarine_result_report_tool.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/reporting_acceptance.py backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py backend/packages/harness/deerflow/domain/submarine/reporting_render.py backend/packages/harness/deerflow/domain/submarine/reporting.py backend/tests/test_submarine_result_report_tool.py docs/archive/superpowers/specs/2026-03-29-result-reporting-decomposition-v1-design.md docs/archive/superpowers/plans/2026-03-29-result-reporting-decomposition-v1.md
git commit -m "refactor: decompose submarine result reporting"
```
