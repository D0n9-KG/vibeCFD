---
phase: 02
slug: runtime-solver-productization
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-01
---

# Phase 02 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` + Node `node:test` + Chrome DevTools MCP |
| **Config file** | `backend/pyproject.toml` and built-in Node test runner |
| **Quick run command** | `cd backend && uv run pytest tests/test_thread_data_middleware.py tests/test_submarine_design_brief_tool.py tests/test_submarine_runtime_context.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_artifact_store.py tests/test_thread_state_reducers.py && cd ../frontend && node --test src/components/workspace/submarine-pipeline-runs.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-runtime-panel.trends.test.ts` |
| **Full suite command** | `cd backend && uv run pytest tests/test_thread_data_middleware.py tests/test_submarine_design_brief_tool.py tests/test_submarine_runtime_context.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_artifact_store.py tests/test_thread_state_reducers.py tests/test_clarification_middleware.py tests/test_tool_error_handling_middleware.py tests/test_uploads_middleware_core_logic.py && cd ../frontend && corepack pnpm typecheck && node --test src/components/workspace/submarine-pipeline-runs.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-runtime-panel.trends.test.ts src/app/workspace/submarine/submarine-pipeline-layout.test.ts src/components/workspace/submarine-pipeline-shell.test.ts` |
| **Estimated runtime** | ~45 seconds automated, plus 2-4 minutes browser validation |

---

## Sampling Rate

- **After every task-sized backend change:** Run the backend quick test slice.
- **After every task-sized frontend change:** Run the frontend quick test slice.
- **After every plan:** Re-run the combined quick command.
- **After every wave:** Run the full suite command.
- **Before phase verification:** Re-run the browser flow with the provided STL file and explicit execution approval.
- **Max feedback latency:** 45 seconds for automated checks, 4 minutes including browser proof.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-A | 01 | 1 | EXEC-01 | unit | `cd backend && uv run pytest tests/test_thread_data_middleware.py tests/test_submarine_design_brief_tool.py tests/test_submarine_runtime_context.py tests/test_submarine_solver_dispatch_tool.py tests/test_uploads_middleware_core_logic.py` | yes | pending |
| 02-01-B | 01 | 1 | EXEC-01 | browser | `Chrome DevTools MCP validation with /workspace/submarine/new and explicit execution approval` | yes | pending |
| 02-02-A | 02 | 2 | EXEC-02 | unit | `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_artifact_store.py tests/test_submarine_postprocess_modules.py tests/test_submarine_result_report_tool.py` | yes | pending |
| 02-02-B | 02 | 2 | EXEC-02 | unit + UI | `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-runtime-panel.trends.test.ts src/components/workspace/submarine-pipeline-runs.test.ts` | yes | pending |
| 02-03-A | 03 | 3 | EXEC-03 | unit + UI | `cd backend && uv run pytest tests/test_thread_state_reducers.py tests/test_submarine_solver_dispatch_tool.py && cd ../frontend && node --test src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-pipeline-shell.test.ts src/app/workspace/submarine/submarine-pipeline-layout.test.ts` | yes | pending |
| 02-03-B | 03 | 3 | EXEC-03 | browser | `Chrome DevTools MCP refresh/re-entry validation on an executed or blocked submarine thread` | yes | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [x] Existing backend `pytest` infrastructure already covers submarine tools, artifact store, reducers, uploads middleware, and clarification middleware.
- [x] Existing frontend `node:test` coverage already exercises submarine pipeline, runtime panel utilities, layout, and status derivation.
- [x] Existing local Docker sandbox path is available through `deer-flow-openfoam-sandbox:latest`.
- [x] Browser validation can use `C:\Users\D0n9\Desktop\suboff_solid.stl`.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Confirmed study launches from thread-bound geometry without path re-entry | EXEC-01 | Requires real upload, confirmation, and sandbox-backed run path | Open `http://localhost:3000/workspace/submarine/new`, upload `C:\Users\D0n9\Desktop\suboff_solid.stl`, submit a baseline SUBOFF prompt, approve execution, and confirm the cockpit does not ask for a new STL path |
| Canonical runtime artifacts appear in the thread output rail | EXEC-02 | Requires real artifact downloads and runtime-to-UI wiring | After execution attempt, confirm `openfoam-request.json`, `dispatch-summary.md`, `openfoam-run.log` (if executed), `solver-results.json`, and `solver-results.md` are visible through the thread artifact channel |
| Refresh preserves truthful runtime state | EXEC-03 | Requires actual re-entry behavior rather than helper output | Refresh the created thread while the run is running, blocked, or completed and confirm the submarine cockpit still shows the correct runtime state and latest event/log context |

---

## Validation Sign-Off

- [x] All planned changes have automated verification coverage.
- [x] Sampling continuity is defined for every plan.
- [x] No extra Wave 0 test scaffolding is required.
- [x] Manual browser checks are explicitly listed for the continuity risks that unit tests cannot fully prove.
- [x] Feedback latency stays below the target window.
- [x] `nyquist_compliant: true` is set in frontmatter.

**Approval:** planned, ready for execute-phase
