# Phase 1: End-to-End Workbench Bootstrap - Research

**Researched:** 2026-04-01
**Domain:** Next.js submarine workbench bootstrap, LangGraph SDK thread creation, optimistic upload state
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Fix the dedicated submarine workbench path instead of routing users to generic chat as a workaround.
- Treat `uploaded STL + first prompt` as one atomic bootstrap action that either creates and binds a thread successfully or shows a clear retryable error.
- After successful bootstrap, the created thread ID must replace the `/new` route immediately so refresh and re-entry work.
- Runtime, stage, and artifact panels should surface bootstrap failures in-place instead of leaving the failure in browser console only.
- Phase 1 is not complete until a real STL-backed prompt reaches backend thread creation from the UI and begins the brief/preflight flow.

### The Agent's Discretion
- Exact hook/component refactor shape
- Query invalidation strategy
- Regression test location and granularity

### Deferred Ideas (Out of Scope)
- Running solver dispatch from the UI after confirmation
- Scientific claim gates and remediation UX
- Case-library expansion and geometry intelligence growth
- Reproducibility and experiment management
</user_constraints>

<research_summary>
## Summary

This phase is a frontend/bootstrap integrity problem, not a missing backend runtime. The local audit already proved that `http://localhost:2024/threads` accepts thread creation requests, that the LangGraph runtime is healthy, and that OpenFOAM execution can run to completion in Docker Desktop. The blocking defect sits in the submarine workbench bootstrap path between the first UI submit and the LangGraph SDK client/send flow.

The project already has the right primitives: `useThreadChat()` owns `/new` versus real-thread route state, `useThreadStream()` owns creation/upload/submit flow, `deriveThreadStreamSendState()` encodes new-thread behavior, and `getSubmarinePipelineStatus()` already exposes a place to surface operator-visible failure state. The most reliable implementation path is to tighten those existing seams instead of inventing a new bootstrap abstraction.

**Primary recommendation:** treat bootstrap as one transaction with six ordered steps: resolve a valid absolute LangGraph base URL, create the thread, bind the created/generated thread ID to the active stream target, upload attachments, submit the first human message, then replace the route and rehydrate the created thread state.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library / Module | Version | Purpose | Why Standard Here |
|------------------|---------|---------|-------------------|
| Next.js | 16.1.7 | Route-driven submarine workbench UI | Existing page/layout and route transition behavior already live here |
| React 19 client components | repo current | Local route state, optimistic UI, callbacks | Current workbench code is already structured around client hooks |
| `@langchain/langgraph-sdk` | 1.5.3 | Thread create + run stream client | The whole DeerFlow chat/workbench stack already depends on it |
| `@tanstack/react-query` | 5.90.17 | Thread list/query invalidation and optimistic cache shaping | Existing thread search cache already stores workbench metadata |
| Node `node:test` | built-in | Frontend regression tests without adding another test runner | Existing frontend tests already use this pattern |

### Supporting
| Library / Module | Purpose | When to Use |
|------------------|---------|-------------|
| `frontend/src/core/config/runtime-base-url.ts` | Backend and LangGraph base URL resolution | Any fix that touches environment or dev fallback behavior |
| `frontend/src/core/threads/hooks.ts` | New-thread creation, upload, submit, optimistic messages | Any fix that touches the first prompt path |
| `frontend/src/components/workspace/submarine-pipeline-status.ts` | Operator-visible status and error banner copy | Any fix that surfaces bootstrap failure in the cockpit |
| Chrome DevTools MCP | Browser-level validation of `/workspace/submarine/new` | End-to-end proof with the provided STL file |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Fixing the dedicated submarine cockpit | Redirect to generic chat | Rejected because it breaks the product's dedicated researcher workflow |
| Reusing the current client singleton blindly | Recreate/cache the client per resolved base URL | Slightly more code, but avoids stale or invalid endpoint state |
| Building a separate bootstrap store | Reuse query cache plus route/thread state helpers | Lower coordination cost and less duplicated state |
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Transactional Bootstrap
**What:** Preserve a strict order for first-submit work on `/workspace/submarine/new`.
**When to use:** Every time a generated thread ID is being turned into a real LangGraph thread.
**Steps:**
1. Resolve and validate LangGraph base URL.
2. Create the thread with `apiClient.threads.create`.
3. Bind the created/generated thread ID into the active stream state.
4. Upload STL attachments against that same thread ID.
5. Submit the first human message.
6. Replace `/new` with `/workspace/submarine/{threadId}` and rehydrate.

### Pattern 2: Route State Owns Identity, Stream State Owns Transport
**What:** `useThreadChat()` remains the source of truth for `isNewThread` and `threadId`, while `useThreadStream()` handles thread creation, upload, submit, and optimistic state.
**When to use:** Any bootstrap or refresh fix.
**Why it matters:** It prevents attachment/upload code from drifting away from the route-owned thread identity.

### Pattern 3: Dual-Layer Validation
**What:** Use fast `node:test` coverage for URL/state helpers and browser validation for real upload/route-transition proof.
**When to use:** Before marking FLOW-01/02/03 as done.
**Why it matters:** The current bug only showed up in the browser even though direct API calls succeeded.

### Anti-Patterns to Avoid
- Creating a second bootstrap pathway outside `useThreadStream()`
- Submitting against a stale `thread` stream object after thread creation
- Keeping failure diagnostics only in console output or toast text
- Replacing the route before attachment metadata and thread binding are durable
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Route identity for `/new` | Another UUID/thread source | `useThreadChat()` + `deriveThreadChatRouteState()` | The route-state helper already handles generated IDs versus real IDs |
| Attachment upload transport | A new custom upload path | `prepareThreadUploadFiles()` + `uploadFiles()` | Existing upload path already matches backend expectations |
| Bootstrap state bannering | New ad hoc status JSX | `getSubmarinePipelineStatus()` | Existing cockpit already consumes its output in desktop and mobile layouts |
| Thread metadata persistence | A separate global store | React Query thread cache + `deriveThreadsAfterWorkbenchStart()` | Existing thread search cache already tracks workbench kind |

**Key insight:** the project does not need a new architecture for Phase 1. It needs stricter contracts around URL resolution, stream rebinding, and operator-visible failure state inside the workbench it already has.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Client singleton pinned to the wrong base URL
**What goes wrong:** `client.threads.create()` or stream calls try to build a URL from an empty or stale base URL and throw `Failed to construct 'URL': Invalid URL`.
**Why it happens:** A singleton client can outlive the resolved environment/mode assumptions that created it.
**How to avoid:** Validate `getLangGraphBaseURL(isMock)` before constructing the client and key any client cache by the resolved URL and mock mode.
**Warning signs:** Browser error before any request reaches `localhost:2024`.

### Pitfall 2: New-thread submit still targets the stale stream object
**What goes wrong:** Thread creation succeeds, but upload or submit still uses the pre-create `thread` object or mismatched thread ID.
**Why it happens:** `useStream()` rebinding is asynchronous relative to the create call.
**How to avoid:** Treat rebinding as part of bootstrap and fail clearly if the stream does not rebind after thread creation.
**Warning signs:** Upload guard complains that the thread is not ready, or the route updates without durable thread state.

### Pitfall 3: Attachment state disappears during `/new` to created-thread navigation
**What goes wrong:** The route changes, but the uploaded STL chip/message disappears until a hard refresh or never comes back.
**Why it happens:** The newly created thread record gets inserted without carrying forward optimistic/upload metadata.
**How to avoid:** Preserve workbench kind plus bootstrap metadata in query cache and rehydrate from backend/query state on refresh.
**Warning signs:** URL changes to a real thread but the workbench looks blank or detached from the first prompt.

### Pitfall 4: Failure is technically captured but not visible in the cockpit
**What goes wrong:** The user only sees a console error or transient toast, while the stage/runtime panels still look idle or healthy.
**Why it happens:** Error presentation is not treated as part of bootstrap state.
**How to avoid:** Map bootstrap failures into `getSubmarinePipelineStatus()` and render them consistently in both layouts.
**Warning signs:** `thread.error` exists, but the submarine cockpit gives no actionable retry guidance.
</common_pitfalls>

<validation_architecture>
## Validation Architecture

Phase 1 needs both deterministic and browser-level validation:

- **Automated helper tests:** `runtime-base-url`, `use-thread-stream.state`, `use-thread-chat.state`, `core/threads/error`, and `submarine-pipeline-status`.
- **Type safety gate:** `corepack pnpm typecheck` from the `frontend` workspace.
- **Browser proof:** Chrome DevTools MCP against `http://localhost:3000/workspace/submarine/new`, uploading `C:\Users\D0n9\Desktop\suboff_solid.stl`, sending the first prompt, confirming route replacement and refresh persistence.
- **Failure-path proof:** populate `thread.error` or force invalid LangGraph URL resolution and confirm the cockpit shows a bootstrap-specific banner with retry guidance.
</validation_architecture>

<code_examples>
## Code Examples

### Absolute URL resolution belongs at client construction time
```ts
const apiUrl = getLangGraphBaseURL(isMock);
new URL(apiUrl);
```

### Bootstrap rules already exist and should stay centralized
```ts
const sendState = deriveThreadStreamSendState({
  requestedThreadId: threadId,
  isNewThread,
});
```

### Route ownership should remain explicit
```ts
onStart: (createdThreadId) => {
  markThreadStarted(createdThreadId);
  router.replace(`/workspace/submarine/${createdThreadId}`);
}
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Generic chat fallback for domain workbenches | Dedicated domain cockpit with shared thread primitives | Keep domain UX while reusing stable transport hooks |
| Console-only diagnostics | In-panel status cards and operator-visible failure banners | Better recovery during long-running AI/CFD workflows |
| One-size-fits-all client singleton | URL-aware client construction/cache | Safer across mock/local/proxy modes |

**Current recommendation:** keep the current Next.js + LangGraph SDK stack, but tighten transport contracts rather than swapping libraries.
</sota_updates>

<open_questions>
## Open Questions

1. **What exact value is causing the browser-side invalid URL?**
   - What we know: the SDK create path fails before a request reaches `localhost:2024`.
   - What's unclear: whether the resolved base URL is empty, malformed, or stale at runtime.
   - Recommendation: log or assert the resolved `apiUrl` at client construction during implementation.

2. **Is query-cache carry-forward enough for attachment persistence?**
   - What we know: the route state and workbench-kind helpers already exist.
   - What's unclear: whether optimistic file metadata survives route replacement without an extra bootstrap snapshot.
   - Recommendation: try the minimal query-cache approach first and add a dedicated bootstrap snapshot only if refresh still drops attachment state.

3. **Does the artifact rail need extra failure wiring beyond `pipelineStatus`?**
   - What we know: the pipeline already renders `errorBanner`.
   - What's unclear: whether artifact and runtime panes need an explicit failed-bootstrap empty state.
   - Recommendation: confirm visually during browser validation and patch only the panes that remain misleading.
</open_questions>

<sources>
## Sources

### Primary (High confidence)
- `frontend/src/core/threads/hooks.ts` - thread create/upload/submit flow
- `frontend/src/core/api/api-client.ts` - LangGraph SDK client construction
- `frontend/src/core/config/runtime-base-url.ts` - local/proxy base URL rules
- `frontend/src/app/workspace/submarine/[thread_id]/page.tsx` - route replacement on thread start
- `frontend/src/components/workspace/submarine-pipeline.tsx` - submarine workbench submit path and error display
- `logs/frontend.manual.out.log` - confirmed the frontend was served at `http://localhost:3000`
- `logs/langgraph.manual.out.log` - confirmed LangGraph runtime stayed healthy while the browser submit failed

### Secondary (High confidence)
- Live browser validation summary from the current project audit: direct `fetch('http://localhost:2024/threads')` succeeds while the first workbench submit fails in frontend runtime wiring.
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Next.js submarine workbench bootstrap
- Ecosystem: LangGraph SDK, React Query, local dev URL resolution
- Patterns: transactional thread bootstrap, route transition persistence, error surfacing
- Pitfalls: invalid URL creation, stale stream binding, disappearing upload state

**Confidence breakdown:**
- Runtime health: HIGH - validated locally
- Frontend failure location: HIGH - reproduced in browser and narrowed to frontend integration
- Fix shape: HIGH - current primitives already cover the needed contracts
- Residual uncertainty: MEDIUM - exact malformed URL value still needs instrumentation during implementation

**Research date:** 2026-04-01
**Valid until:** 2026-05-01
</metadata>

---

*Phase: 01-end-to-end-workbench-bootstrap*
*Research completed: 2026-04-01*
*Ready for planning: yes*
