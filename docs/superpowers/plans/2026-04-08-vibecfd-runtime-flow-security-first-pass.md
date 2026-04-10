# VibeCFD Runtime Flow Security First Pass Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the `Prior Art Survey`, `Reuse Strategy`, `Session Status File`, `Primary Context Files`, `Artifact Lifecycle`, `Workspace Strategy`, `Validation Strategy`, `Review Cadence`, `Checkpoint Strategy`, `Uncertainty Hotspots`, and `Replan Triggers` fields below while executing.

**Goal:** Make VibeCFD runnable from the main workspace only, restore the main user flows for Submarine and Skill Studio in pre-artifact states, and add the first server-safety guardrails needed before broader deployment work.

**Architecture:** Keep the existing DeerFlow gateway and LangGraph runtime, but stop relying on frontend-local thread file APIs during standalone local frontend runs. Route browser calls to the real backend in standalone dev, keep same-origin behavior for deployed/reverse-proxied environments, surface progress from live thread/message state before structured artifacts exist, and add upload/session guardrails at the web edge where they can be enforced immediately.

**Tech Stack:** Next.js App Router, React, TanStack Query, LangGraph SDK, FastAPI gateway, better-auth, Node test runner, pytest.

**Prior Art Survey:** none needed - local repo stabilization and hardening task

**Reuse Strategy:** adapt existing project

**Session Status File:** `docs/superpowers/session-status/2026-04-08-vibecfd-runtime-flow-security-first-pass-status.md`

**Primary Context Files:** `docs/superpowers/session-status/2026-04-08-vibecfd-superpowers-alignment-and-workbench-cleanup-status.md`, `docs/superpowers/session-status/2026-04-08-vibecfd-legacy-workspace-retirement-status.md`, `frontend/src/core/config/runtime-base-url.ts`, `frontend/src/app/workspace/submarine/[thread_id]/page.tsx`, `frontend/src/components/workspace/submarine-workbench/index.tsx`, `frontend/src/components/workspace/skill-studio-workbench/index.tsx`, `frontend/src/server/better-auth/server.ts`, `backend/app/gateway/app.py`

**Artifact Lifecycle:** Keep this plan and its session status. Keep any new focused regression tests added for runtime-base-url resolution, workbench fallback visibility, and upload/session safety. Replace ad-hoc local-frontend filesystem behavior in live browser flows with direct backend access for standalone dev. Do not keep one-off debug scripts beyond the commands recorded in git history and status files.

**Workspace Strategy:** current workspace

**Validation Strategy:** mixed

**Review Cadence:** each milestone

**Checkpoint Strategy:** user-directed checkpoints

**Uncertainty Hotspots:** whether the current frontend build instability is fully resolved once stale runtime processes are removed; whether better-auth session enforcement can be applied cleanly to the specific frontend API routes without introducing a larger cross-process auth design for the gateway in this pass; whether pre-artifact workbench fallbacks should stay rail-first or become inline status modules after user testing.

**Replan Triggers:** if direct backend access in standalone dev breaks an expected deployed reverse-proxy path; if auth enforcement requires introducing a gateway token/session protocol instead of route-local guards; if the current frontend cannot boot cleanly from the main workspace after runtime cleanup and targeted fixes.

---

### Task 1: Runtime Surface And Backend URL Alignment

**Files:**
- Modify: `frontend/src/core/config/runtime-base-url.ts`
- Modify: `frontend/src/core/config/runtime-base-url.test.ts`
- Modify: `frontend/src/core/config/index.ts`
- Test: `frontend/src/core/config/runtime-base-url.test.ts`

- [ ] **Step 1: Add failing tests that distinguish standalone local frontend runs from deployed same-origin runs**

```ts
void test("returns the real backend URL for standalone localhost frontend dev ports", () => {
  assert.equal(
    resolveBackendBaseURL({
      backendBaseURL: undefined,
      location: {
        origin: "http://localhost:3000",
        hostname: "localhost",
        port: "3000",
      },
    }),
    "http://localhost:8001",
  );
});

void test("keeps same-origin backend URLs for reverse-proxied frontend hosts", () => {
  assert.equal(
    resolveBackendBaseURL({
      backendBaseURL: undefined,
      location: {
        origin: "http://localhost:2026",
        hostname: "localhost",
        port: "2026",
      },
    }),
    "",
  );
});
```

- [ ] **Step 2: Run the focused config tests to verify the current bug**

Run: `node --test frontend/src/core/config/runtime-base-url.test.ts`
Expected: FAIL because standalone localhost frontend locations currently resolve to `""` instead of the real backend host.

- [ ] **Step 3: Implement standalone-local backend URL detection without regressing deployed same-origin behavior**

```ts
function isStandaloneLocalFrontendHost(location?: BrowserLocationLike): boolean {
  if (!location) {
    return false;
  }

  const isLocalHost =
    location.hostname === "localhost" || location.hostname === "127.0.0.1";

  return isLocalHost && location.port !== "2026";
}

export function resolveBackendBaseURL({
  backendBaseURL,
  location,
}: BackendBaseURLOptions): string {
  const normalizedBackendBaseURL = normalizeConfiguredBaseURL(backendBaseURL);

  if (location) {
    if (normalizedBackendBaseURL) {
      return normalizedBackendBaseURL;
    }
    return isStandaloneLocalFrontendHost(location) ? "http://localhost:8001" : "";
  }

  return normalizedBackendBaseURL ?? "http://localhost:8001";
}
```

- [ ] **Step 4: Run the focused config tests to verify the fix**

Run: `node --test frontend/src/core/config/runtime-base-url.test.ts`
Expected: PASS

- [ ] **Step 5: Checkpoint according to `Checkpoint Strategy`**

Record the changed files in the session status file. Do not commit unless the user asks for a checkpoint.

### Task 2: Main-Workspace Runtime Cleanup And Verification

**Type:** Exploratory

**Files:**
- Notes: `docs/superpowers/session-status/2026-04-08-vibecfd-runtime-flow-security-first-pass-status.md`

**Goal:** Ensure the running frontend/backend processes all come from the main workspace and that the browser is exercising the code under `C:\Users\D0n9\Desktop\颠覆性大赛`.

**Collect Evidence:**
- Only one frontend dev/start stack is active for the main workspace
- LangGraph and gateway listeners come from the main workspace backend
- Browser thread uploads no longer write into a removed or stale worktree path

**Stop and Replan If:**
- The main workspace frontend still cannot boot after stale process cleanup and targeted code fixes
- A remaining hidden process or service still serves stale assets from outside the main workspace

**Checkpoint If:**
- A clean single-runtime surface is established and verified with process listings plus one browser sanity check

- [ ] **Step 1: Stop duplicate main-workspace frontend/backend processes so only one listener per service remains**
- [ ] **Step 2: Start one main-workspace frontend on `3000`, one LangGraph dev server on `2024`, and one gateway on `8001`**
- [ ] **Step 3: Record the exact listener/process evidence in the session status file**
- [ ] **Step 4: Open `/workspace/submarine/new` once and confirm the served assets and upload paths now come from the main workspace**
- [ ] **Step 5: Decide whether execution can continue on the current plan or invoke `superpowers:revising-plans`**

### Task 3: Submarine Pre-Artifact Progress Visibility

**Files:**
- Modify: `frontend/src/components/workspace/submarine-workbench/index.tsx`
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts`
- Modify: `frontend/src/components/workspace/submarine-workbench/index.contract.test.ts`
- Modify: `frontend/src/app/workspace/submarine/[thread_id]/page.test.ts`
- Test: `frontend/src/components/workspace/submarine-workbench/index.contract.test.ts`
- Test: `frontend/src/app/workspace/submarine/[thread_id]/page.test.ts`

- [ ] **Step 1: Add failing tests that require visible live-progress fallback content before runtime artifacts exist**

```ts
void test("submarine workbench shows a live progress fallback before structured artifacts arrive", () => {
  assert.match(source, /live progress|正在整理输入|最近消息|等待结构化产物/i);
});

void test("submarine thread route keeps the negotiation rail available while runtime evidence is still empty", () => {
  assert.match(pageSource, /chatRailErrorMessage|thread\\.isLoading|pendingThreadRouteId/);
});
```

- [ ] **Step 2: Run the focused Submarine tests to verify the missing UX**

Run: `node --test frontend/src/components/workspace/submarine-workbench/index.contract.test.ts frontend/src/app/workspace/submarine/[thread_id]/page.test.ts`
Expected: FAIL because the current workbench only renders placeholder focus cards when runtime/artifacts are absent.

- [ ] **Step 3: Implement a pre-artifact fallback summary driven by live thread state**

```tsx
const latestAssistantText = [...thread.messages]
  .reverse()
  .find((message) => message.type === "ai");

const liveProgressSummary = {
  isWaitingForArtifacts: submarineArtifacts.length === 0 && !runtime && !finalReport,
  latestAssistantText: textOfMessage(latestAssistantText) ?? null,
  latestUserText:
    textOfMessage([...thread.messages].reverse().find((message) => message.type === "human")) ??
    null,
};
```

Render an inline fallback card in the main canvas that:
- explains that the thread has started,
- shows whether the model is still loading, errored, or waiting for structured outputs,
- shows the latest visible message preview,
- keeps the chat rail action prominent until real runtime artifacts arrive.

- [ ] **Step 4: Re-run the focused Submarine tests**

Run: `node --test frontend/src/components/workspace/submarine-workbench/index.contract.test.ts frontend/src/app/workspace/submarine/[thread_id]/page.test.ts`
Expected: PASS

- [ ] **Step 5: Checkpoint according to `Checkpoint Strategy`**

Update the session status with the fallback behavior and any remaining UX gaps discovered during browser retest.

### Task 4: Skill Studio Pre-Artifact Progress Visibility

**Files:**
- Modify: `frontend/src/components/workspace/skill-studio-workbench/index.tsx`
- Modify: `frontend/src/components/workspace/skill-studio-workbench/index.contract.test.ts`
- Modify: `frontend/src/components/workspace/skill-studio-workbench/thread-route.tsx`
- Test: `frontend/src/components/workspace/skill-studio-workbench/index.contract.test.ts`

- [ ] **Step 1: Add failing tests that require useful progress state before the first skill artifact exists**

```ts
void test("skill studio shows active thread progress before the first artifact lands", () => {
  assert.match(source, /waiting for first artifact|最新消息|当前线程进展|继续协作/i);
});
```

- [ ] **Step 2: Run the focused Skill Studio contract test**

Run: `node --test frontend/src/components/workspace/skill-studio-workbench/index.contract.test.ts`
Expected: FAIL because the current implementation only presents the generic waiting state without live progress detail.

- [ ] **Step 3: Implement a richer waiting state using current thread messages and loading/error state**

```tsx
const latestVisibleMessage = [...thread.messages]
  .reverse()
  .find((message) => message.type === "ai" || message.type === "human");

const waitingSummary = {
  latestVisibleMessage: textOfMessage(latestVisibleMessage) ?? null,
  threadLoading: thread.isLoading,
  threadError:
    thread.error instanceof Error
      ? thread.error.message
      : typeof thread.error === "string"
        ? thread.error
        : null,
};
```

Use this to replace the static empty state copy with:
- current agent label,
- current thread progress,
- latest visible message preview,
- explicit reason why the lifecycle canvas is still waiting.

- [ ] **Step 4: Re-run the focused Skill Studio contract test**

Run: `node --test frontend/src/components/workspace/skill-studio-workbench/index.contract.test.ts`
Expected: PASS

- [ ] **Step 5: Checkpoint according to `Checkpoint Strategy`**

Record any remaining “no artifact yet” friction in the session status file.

### Task 5: Frontend Session Guards For Thread File APIs

**Files:**
- Modify: `frontend/src/app/api/threads/[thread_id]/uploads/route.ts`
- Modify: `frontend/src/app/api/threads/[thread_id]/uploads/list/route.ts`
- Modify: `frontend/src/app/api/threads/[thread_id]/uploads/[filename]/route.ts`
- Modify: `frontend/src/app/api/threads/[thread_id]/artifacts/[[...artifact_path]]/route.ts`
- Modify: `frontend/src/app/api/threads/uploads-storage.test.ts`
- Create: `frontend/src/app/api/threads/thread-route-auth.test.ts`
- Test: `frontend/src/app/api/threads/uploads-storage.test.ts`
- Test: `frontend/src/app/api/threads/thread-route-auth.test.ts`

- [ ] **Step 1: Add failing tests that require auth/session checks for thread-scoped file routes**

```ts
void test("thread upload routes require a session before serving thread files", async () => {
  assert.match(source, /getSession/);
  assert.match(source, /401/);
});
```

- [ ] **Step 2: Run the focused thread-route tests**

Run: `node --test frontend/src/app/api/threads/uploads-storage.test.ts frontend/src/app/api/threads/thread-route-auth.test.ts`
Expected: FAIL because the routes currently do not import or call `getSession`.

- [ ] **Step 3: Add a shared session guard and apply it to all thread-scoped frontend file routes**

```ts
import { getSession } from "@/server/better-auth/server";

async function requireSession() {
  const session = await getSession();
  if (!session) {
    return Response.json({ detail: "Unauthorized" }, { status: 401 });
  }
  return null;
}
```

Each route should:
- call the guard before doing any filesystem work,
- return `401` on missing session,
- continue to preserve existing `UploadStorageError` behavior for authenticated callers.

- [ ] **Step 4: Re-run the focused thread-route tests**

Run: `node --test frontend/src/app/api/threads/uploads-storage.test.ts frontend/src/app/api/threads/thread-route-auth.test.ts`
Expected: PASS

- [ ] **Step 5: Checkpoint according to `Checkpoint Strategy`**

Update the session status with any routes that still need gateway-side auth design in a later pass.

### Task 6: Upload Size And Type Guardrails

**Files:**
- Modify: `frontend/src/app/api/threads/[thread_id]/uploads/storage.ts`
- Modify: `backend/app/gateway/routers/uploads.py`
- Modify: `frontend/src/app/api/threads/uploads-storage.test.ts`
- Modify: `backend/tests/test_client.py`
- Test: `node --test frontend/src/app/api/threads/uploads-storage.test.ts`
- Test: `uv run pytest backend/tests/test_client.py -k upload_list_delete_lifecycle`

- [ ] **Step 1: Add failing tests for oversize uploads and blocked extensions**

```ts
void test("rejects uploads above the configured per-file limit", async () => {
  await assert.rejects(() => saveUploadedFiles("thread-1", [hugeFile]), /File too large/i);
});
```

```python
def test_upload_rejects_disallowed_extension(client):
    response = client.session.post(
        f"{client.base_url}/api/threads/t-unsafe/uploads",
        files={"files": ("payload.exe", b"binary")},
    )
    assert response.status_code == 400
```

- [ ] **Step 2: Run the focused upload tests to verify the starting gap**

Run: `node --test frontend/src/app/api/threads/uploads-storage.test.ts`
Expected: FAIL because `saveUploadedFiles()` currently writes any file bytes without size/type checks.

Run: `uv run pytest backend/tests/test_client.py -k upload_list_delete_lifecycle`
Expected: FAIL or require extension with a new targeted test because backend upload router currently accepts any filename/type.

- [ ] **Step 3: Implement conservative first-pass upload policy**

```ts
const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;
const BLOCKED_EXTENSIONS = new Set([".exe", ".bat", ".cmd", ".ps1", ".com", ".scr"]);
```

```python
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".ps1", ".com", ".scr"}
```

Enforce in both frontend-local storage and gateway upload handling:
- max per-file size,
- blocked executable/script extensions,
- explicit error messages for rejected files.

- [ ] **Step 4: Re-run the focused upload tests**

Run: `node --test frontend/src/app/api/threads/uploads-storage.test.ts`
Expected: PASS

Run: `uv run pytest backend/tests/test_client.py -k upload`
Expected: PASS for upload lifecycle and new rejection coverage

- [ ] **Step 5: Checkpoint according to `Checkpoint Strategy`**

Record the chosen limits and any follow-up quota/auth work still deferred.

### Task 7: Integrated Verification On The Main Workspace

**Type:** Exploratory

**Files:**
- Notes: `docs/superpowers/session-status/2026-04-08-vibecfd-runtime-flow-security-first-pass-status.md`

**Goal:** Re-run the user-critical flows on the cleaned main workspace runtime and confirm the fixes are visible in the browser.

**Collect Evidence:**
- STL upload flow routes to the main workspace backend and surfaces progress before artifacts exist
- Skill Studio no longer 404s on lifecycle calls during active runs
- Thread file routes reject unauthenticated access

**Stop and Replan If:**
- The main workspace frontend still serves stale or broken assets after process cleanup
- Browser evidence contradicts the new tests

**Checkpoint If:**
- Both browser flows show improved progress visibility and the auth/upload guardrails behave as expected

- [ ] **Step 1: Start the main workspace runtime stack and confirm listeners/processes**
- [ ] **Step 2: Re-run the Submarine STL flow through the browser and capture the request chain**
- [ ] **Step 3: Re-run Skill Studio thread creation and verify the lifecycle API path no longer 404s**
- [ ] **Step 4: Probe an unauthenticated thread file route and verify it returns `401`**
- [ ] **Step 5: Record the verified state and any remaining issues in the session status file**
