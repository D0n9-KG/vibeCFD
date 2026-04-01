---
phase: 01-end-to-end-workbench-bootstrap
verified: 2026-04-01T09:54:59Z
status: passed
score: 3/3 must-haves verified
---

# Phase 1: End-to-End Workbench Bootstrap Verification Report

**Phase Goal:** Fix the new-submarine workbench bootstrap so a real STL-backed prompt creates a thread, binds attachments, and enters the brief/preflight flow from the UI.
**Verified:** 2026-04-01T09:54:59Z
**Status:** passed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can submit the first prompt from `/workspace/submarine/new` without the previous client-side URL/thread creation failure. | VERIFIED | Browser run created thread `88e729ca-18a4-402b-a2f8-da6587928c72`; `POST /threads`, upload, and `runs/stream` all returned `200`; console stayed clear of errors. |
| 2 | Uploaded STL and prompt are bound to the created thread and survive route transition plus refresh. | VERIFIED | Reloading `88e729ca-18a4-402b-a2f8-da6587928c72` restored the title `STL潜艇CFD基线检查清单`, the `suboff_solid.stl` chip, the original prompt, and design-brief artifacts. |
| 3 | Runtime and artifact panels show recoverable state inside the submarine cockpit instead of relying on console-only diagnostics or generic chat fallback. | VERIFIED | The created thread stays inside the submarine workbench, shows `NEEDS CLARIFICATION`, pending questions, and artifact downloads; targeted frontend tests and backend clarification regression tests passed. |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/core/api/api-client.ts` | Validated LangGraph client construction | EXISTS + SUBSTANTIVE | Resolves `apiUrl`, validates with `new URL(...)`, and caches by `clientsByApiUrl`. |
| `frontend/src/core/threads/hooks.ts` | Transactional new-thread bootstrap | EXISTS + SUBSTANTIVE | Creates thread before submit, derives send state, and throws explicit rebind failure when the stream target stays stale. |
| `frontend/src/app/workspace/submarine/[thread_id]/page.tsx` | Route-owned created-thread hydration | EXISTS + SUBSTANTIVE | Preserves `markThreadStarted(createdThreadId)` before `router.replace(nextPath)` and only treats `"new"` as bootstrap state. |
| `frontend/src/components/workspace/submarine-pipeline.tsx` | Dedicated cockpit with rehydration and error-state rendering | EXISTS + SUBSTANTIVE | Uses `getSubmarinePipelineStatus`, preserves async submit promises, and renders the existing-thread rehydration panel. |
| `frontend/src/components/workspace/submarine-pipeline-status.ts` | Bootstrap-specific operator guidance | EXISTS + SUBSTANTIVE | Maps invalid URL, LangGraph config, stream rebind, and rehydration states into cockpit copy. |
| `backend/packages/harness/deerflow/agents/middlewares/clarification_middleware.py` | Encoding-safe clarification interrupt delivery | EXISTS + SUBSTANTIVE | Escapes stdout-incompatible characters before logging clarification text on Windows/GBK consoles. |
| `backend/tests/test_clarification_middleware.py` | Regression coverage for Windows clarification failure | EXISTS + SUBSTANTIVE | Simulates strict GBK stdout and verifies `m³/s` clarification prompts no longer crash. |

**Artifacts:** 7/7 verified

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `frontend/src/core/api/api-client.ts` | `frontend/src/core/config/runtime-base-url.ts` | `getLangGraphBaseURL` resolution | WIRED | `api-client.ts` imports `getLangGraphBaseURL`, trims the result, and validates the resolved URL before client creation. |
| `frontend/src/core/threads/hooks.ts` | `frontend/src/core/api/api-client.ts` | `apiClient.threads.create` and first-submit bootstrap | WIRED | `hooks.ts` uses `apiClient.threads.create(...)` during `/new` bootstrap and submits only after the created thread is rebound. |
| `frontend/src/core/threads/hooks.ts` | `frontend/src/core/threads/use-thread-stream.state.ts` | `deriveThreadStreamSendState` | WIRED | `hooks.ts` imports and calls `deriveThreadStreamSendState(...)` to determine new-thread behavior. |
| `frontend/src/app/workspace/submarine/[thread_id]/page.tsx` | `frontend/src/core/threads/hooks.ts` | `markThreadStarted` before route replacement | WIRED | Page bootstrap keeps the created thread id and swaps routes only after marking the thread as started. |
| `frontend/src/components/workspace/submarine-pipeline.tsx` | `frontend/src/components/workspace/submarine-pipeline-status.ts` | `getSubmarinePipelineStatus` | WIRED | Pipeline status is computed centrally and rendered in the workbench shell, including rehydration and error states. |
| `frontend/src/components/workspace/submarine-pipeline-status.ts` | `frontend/src/core/threads/error.ts` | `getThreadErrorMessage` | WIRED | Status helper normalizes thread errors through `getThreadErrorMessage(...)` before generating operator guidance. |

**Wiring:** 6/6 connections verified

## Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| FLOW-01: Researcher can start a new submarine study from `/workspace/submarine/new` without client-side thread bootstrap failure | SATISFIED | - |
| FLOW-02: Uploaded STL files and the first prompt are bound to the created thread and remain visible after route transition or refresh | SATISFIED | - |
| FLOW-03: Workbench stage cards, runtime panel, and artifact rail reflect bootstrap success and failure states in a recoverable way | SATISFIED | - |

**Coverage:** 3/3 requirements satisfied

## Anti-Patterns Found

None in the Phase 1 bootstrap artifacts that were verified for transition readiness.

## Human Verification Required

None. Browser UAT was completed directly with Chrome DevTools MCP during this verification pass.

## Gaps Summary

**No gaps found.** Phase goal achieved. Ready to proceed.

## Verification Metadata

**Verification approach:** Goal-backward using Phase 1 success criteria from `ROADMAP.md`, cross-checked against plan must-haves  
**Must-haves source:** ROADMAP success criteria + `01-01/02/03-PLAN.md` must_haves  
**Automated checks:** `corepack pnpm typecheck`; frontend node tests `28/28`; backend pytest `7/7`  
**Human checks required:** 0 outstanding  
**Total verification time:** ~25 min

---
*Verified: 2026-04-01T09:54:59Z*
*Verifier: Codex*
