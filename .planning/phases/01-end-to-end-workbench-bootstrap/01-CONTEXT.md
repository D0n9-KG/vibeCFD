# Phase 1: End-to-End Workbench Bootstrap - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the dedicated submarine workbench bootstrap path work end-to-end from `/workspace/submarine/new`: upload an STL, send the first prompt, create and bind a real DeerFlow thread, and enter the brief/preflight flow with visible runtime state. This phase does not add new CFD capabilities; it restores the core researcher entry path.

</domain>

<decisions>
## Implementation Decisions

### User path to repair first
- **D-01:** Fix the dedicated submarine workbench path rather than routing users to generic chat as a workaround.
- **D-02:** Treat `uploaded STL + first prompt` as one atomic bootstrap action that either creates/binds a thread successfully or shows a clear retryable error.

### Runtime binding and workbench behavior
- **D-03:** After successful bootstrap, the created thread ID must replace the `/new` route immediately so refresh and re-entry work.
- **D-04:** Runtime, stage, and artifact panels should surface bootstrap failures in-place instead of leaving the failure in browser console only.

### Evidence of done
- **D-05:** This phase is not complete until a real STL-backed prompt reaches backend thread creation from the UI and begins the brief/preflight flow.

### the agent's Discretion
- Exact hook/component refactor shape
- Query invalidation strategy
- Regression test location and test style

</decisions>

<specifics>
## Specific Ideas

- Live browser reproduction on 2026-04-01 showed that file upload works, but first submit fails before any request reaches `localhost:8001` or `localhost:2024`.
- Captured client error: `TypeError: Failed to construct 'URL': Invalid URL`.
- Error path observed through the workbench stack: submarine pipeline submit -> thread stream send -> `apiClient.threads.create(...)`.
- Direct browser `fetch('http://localhost:2024/threads', ...)` succeeds, so the bug is in frontend integration rather than service availability.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend workbench bootstrap
- `frontend/src/app/workspace/submarine/[thread_id]/page.tsx` - top-level submarine workbench wiring and thread chat hook usage
- `frontend/src/components/workspace/submarine-pipeline.tsx` - submit path from submarine workbench input into `sendMessage`
- `frontend/src/components/workspace/input-box.tsx` - prompt submit behavior and stop/send handoff
- `frontend/src/core/threads/hooks.ts` - thread creation, upload, optimistic state, and stream submission logic
- `frontend/src/core/threads/use-thread-stream.state.ts` - new-thread send-state rules

### Runtime URL resolution and client wiring
- `frontend/src/core/api/api-client.ts` - LangGraph SDK client construction
- `frontend/src/core/config/index.ts` - backend and LangGraph base URL resolution entrypoints
- `frontend/src/core/config/runtime-base-url.ts` - localhost dev fallback rules for backend URLs

### Audit evidence
- `logs/frontend.manual.out.log` - dev frontend route evidence
- `logs/langgraph.manual.out.log` - local LangGraph runtime startup evidence
- `README.md` - top-level runtime and project framing

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `useThreadChat`: already generates UUID-backed thread IDs for `/new` routes
- `useThreadStream`: already supports upload, optimistic messages, thread start callbacks, and stream submission
- Submarine workbench upload input: already accepts STL attachments and displays them in the UI

### Established Patterns
- Generic chat and agent workbenches use the same thread streaming primitives successfully
- Runtime base URL resolution is centralized in frontend config helpers instead of being spread across components
- Submarine workbench is intended to remain a dedicated research cockpit, not a thin alias for generic chat

### Integration Points
- Bootstrap fix likely touches workbench submit path, thread creation path, and SDK/client URL construction
- Successful bootstrap must flow into the existing backend submarine tools rather than bypassing them
- Thread creation and route replacement behavior must stay compatible with upload handling and artifact panels

</code_context>

<deferred>
## Deferred Ideas

- Running solver dispatch from the UI after confirmation - Phase 2
- Scientific claim gates and remediation UX - Phase 3 and later
- Case-library expansion and geometry intelligence growth - Phase 4
- Reproducibility and experiment management - Phase 5

</deferred>

---

*Phase: 01-end-to-end-workbench-bootstrap*
*Context gathered: 2026-04-01*
