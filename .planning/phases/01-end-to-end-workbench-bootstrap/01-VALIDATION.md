---
phase: 01
slug: end-to-end-workbench-bootstrap
status: executed
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-01
---

# Phase 01 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | node:test + TypeScript source imports |
| **Config file** | none - built-in Node test runner |
| **Quick run command** | `node --test src/core/config/runtime-base-url.test.ts src/core/threads/use-thread-stream.state.test.ts src/core/threads/error.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/chats/use-thread-chat.state.test.ts` |
| **Full suite command** | `corepack pnpm typecheck && node --test src/core/config/runtime-base-url.test.ts src/core/threads/use-thread-stream.state.test.ts src/core/threads/error.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/chats/use-thread-chat.state.test.ts && uv run pytest tests/test_clarification_middleware.py tests/test_tool_error_handling_middleware.py` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task-sized code change:** Run the quick test command.
- **After every plan:** Run `corepack pnpm typecheck`.
- **After Phase 1 wave completion:** Run the full suite command.
- **Before phase verification:** Re-run the browser flow with the provided STL file.
- **Max feedback latency:** 20 seconds for automated checks, 2 minutes for browser validation.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-A | 01 | 1 | FLOW-01 | unit + browser | `corepack pnpm typecheck && node --test src/core/config/runtime-base-url.test.ts src/core/threads/use-thread-stream.state.test.ts` | yes | green |
| 01-02-A | 02 | 2 | FLOW-02 | browser | `node --test src/components/workspace/chats/use-thread-chat.state.test.ts` | yes | green |
| 01-03-A | 03 | 3 | FLOW-03 | unit + browser | `node --test src/core/threads/error.test.ts src/components/workspace/submarine-pipeline-status.test.ts && uv run pytest tests/test_clarification_middleware.py tests/test_tool_error_handling_middleware.py` | yes | green |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [x] Existing `node:test` infrastructure already covers helper/state tests.
- [x] Existing `corepack pnpm typecheck` gate already exists in `frontend/package.json`.
- [x] Browser validation can run with Chrome DevTools MCP and `C:\Users\D0n9\Desktop\suboff_solid.stl`.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| First STL-backed submit creates a real thread from `/workspace/submarine/new` | FLOW-01 | Requires browser event flow and real LangGraph runtime | Open `http://localhost:3000/workspace/submarine/new`, upload `C:\Users\D0n9\Desktop\suboff_solid.stl`, enter a short brief prompt, submit, confirm URL changes to `/workspace/submarine/{threadId}` without `Invalid URL` error |
| Attachment and prompt survive route transition plus refresh | FLOW-02 | Requires browser route swap and persisted UI state | After the first successful submit, refresh the created thread page and confirm the STL chip/prompt remain visible |
| Bootstrap failure is visible in the cockpit | FLOW-03 | Requires checking rendered panel state, not only helper output | Submit a new thread with incomplete information and confirm the submarine cockpit shows recoverable clarification or bootstrap guidance instead of a console-only or tool-error failure |

---

## Validation Sign-Off

- [x] All planned changes have automated verification coverage.
- [x] Sampling continuity is defined for every plan.
- [x] No extra Wave 0 test scaffolding is required.
- [x] Manual-only checks are explicitly listed for browser behavior.
- [x] Feedback latency stays below the target window.
- [x] `nyquist_compliant: true` is set in frontmatter.

**Approval:** execution complete, ready for phase verification
