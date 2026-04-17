# Workspace Management Center Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then choose the execution skill that fits the work: use superpowers:subagent-driven-development when delegation benefits outweigh the round-trip, or superpowers:executing-plans when the work is better kept local. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the plan controls below, especially reuse, continuity, artifact lifecycle, validation/review cadence, and any research-overlay constraints.

**Goal:** Build a unified management center that lets users configure runtime behavior, manage agents and skills, and perform true cascading thread deletion with file cleanup from the frontend, while treating legacy orphan-thread leftovers as a one-time cleanup task rather than a permanent user-facing management surface.

**Architecture:** Add a new `/workspace/control-center` surface backed by canonical backend management APIs. Consolidate split management state into the backend gateway, reuse existing skill lifecycle/graph primitives, and expose a single backend-orchestrated hard-delete path for threads. Legacy orphan storage is cleaned once during rollout instead of remaining a standing control-center domain.

**Tech Stack:** Next.js App Router, React, TanStack Query, FastAPI gateway routes, DeerFlow path/config helpers, LangGraph SDK, existing workspace UI primitives

**Prior Art Survey:** none needed - this is a project-internal management/control-plane slice built on existing APIs and workspace patterns

**Reuse Strategy:** adapt existing project

**Artifact Scope:** project-canonical

**Artifact Epoch:** workspace-management-center

**Supersedes:** none

**Session Status File:** `docs/superpowers/session-status/2026-04-16-workspace-management-center-status.md`

**Context Summary:** none

**Primary Context Files:** `docs/superpowers/specs/2026-04-16-workspace-management-center-design.md`; `frontend/src/components/workspace/agents/agent-gallery.tsx`; `frontend/src/components/workspace/recent-chat-list.tsx`; `frontend/src/components/workspace/workspace-nav-chat-list.tsx`; `frontend/src/app/api/agents/store.ts`; `frontend/src/core/threads/hooks.ts`; `frontend/src/core/skills/api.ts`; `backend/app/gateway/routers/agents.py`; `backend/app/gateway/routers/skills.py`; `backend/app/gateway/routers/threads.py`; `backend/packages/harness/deerflow/config/paths.py`

**Artifact Lifecycle:** Keep the spec/plan/status artifacts and the new management-center route/components. Replace the frontend-local agent store as a primary source of truth once migration is complete. Replace the current frontend dual-delete thread flow with a single backend cascade-delete API. Retire any temporary migration helpers, preview-only debug scaffolding, and any temporary orphan-audit UI introduced during rollout before calling the slice complete.

**Workspace Strategy:** current workspace

**Validation Strategy:** mixed

**Review Cadence:** each milestone

**Checkpoint Strategy:** milestone commits

**Research Overlay:** disabled

**Research Mainline:** none

**Evaluation Rubric:** none

**Non-Negotiables:** the user must be able to see and manage runtime configuration, skills, and threads without digging through hidden surfaces; thread hard delete must remove actual persisted thread files, not only list records; legacy orphan leftovers should be cleaned during rollout rather than left to accumulate; management actions must be backed by canonical backend APIs instead of split-brain stores

**Forbidden Regressions:** keeping `.deerflow-ui/agents.json` as the authoritative long-term agent store; leaving skill visibility confined to Skill Studio internals; keeping sidebar thread management inconsistent across workbenches; reporting successful thread deletion while local thread files remain on disk

**Method Fidelity Checks:** verify the management center reads canonical backend state; verify installed skill previews use safe backend file access instead of direct filesystem leakage; verify thread delete preview and final deletion agree on files removed; verify one-time orphan cleanup only targets confirmed local leftovers and that the steady-state UI no longer depends on orphan audit inventory

**Scale Gate:** ship backend-first with targeted tests before wiring the full management-center UI

**Freeze Gate:** none

**Decision Log:** none - record durable decisions in the session status file and commit history for this engineering slice

**Research Findings:** none

**Uncertainty Hotspots:** the migration path from frontend-local agent storage to backend-managed agents; whether LangGraph deletion can provide the exact preview metadata needed or whether only local storage can be previewed; how much skill-file preview detail can be exposed safely without opening unrestricted path reads; how much transient rollout cleanup should remain visible once current orphan leftovers are removed

**Replan Triggers:** if canonical backend agent storage cannot safely preserve existing custom agents; if LangGraph deletion does not reliably remove the expected server-side thread state; if secure skill preview requires a broader artifact-serving redesign than this slice allows

---

### Task 1: Establish Canonical Backend Management APIs

**Files:**
- Modify: `backend/app/gateway/app.py`
- Modify: `backend/app/gateway/routers/agents.py`
- Modify: `backend/app/gateway/routers/skills.py`
- Modify: `backend/app/gateway/routers/threads.py`
- Add: `backend/app/gateway/routers/runtime_config.py`
- Test: `backend/tests/test_agents_router.py`
- Test: `backend/tests/test_skills_router.py`
- Test: `backend/tests/test_threads_router.py`
- Test: `backend/tests/test_runtime_config_router.py`

- [x] **Step 1: Add or expand backend response models so the gateway can return canonical management summaries for runtime config, agents, skills, and thread cleanup previews**

- [x] **Step 2: Extend the backend agent router to return built-in plus custom agents, and add migration-aware fields needed by the future UI**

- [x] **Step 3: Add runtime-config endpoints that summarize lead-agent defaults, stage-role overrides, provider availability, and config-source provenance without exposing secrets**

- [x] **Step 4: Add secure skill file-tree and file-content preview endpoints scoped to known skill roots / archives**

- [x] **Step 5: Replace the current local-only thread cleanup route with a backend-orchestrated cascade-delete contract and a preview contract**

- [x] **Step 6: Add an orphan-thread audit endpoint that enumerates local thread directories with no matching live thread state**

- [x] **Step 7: Write focused backend tests for the new API contracts and preview safety rules**

- [x] **Step 8: Run the focused backend test targets for the new routers and verify RED/GREEN behavior**

Run:
`uv run --project backend pytest backend/tests/test_agents_router.py backend/tests/test_skills_router.py backend/tests/test_threads_router.py backend/tests/test_runtime_config_router.py -q`

Expected:
new router coverage passes and existing router behavior stays intact

### Task 2: Retire Frontend Split-Brain Agent Storage

**Files:**
- Modify: `frontend/src/core/agents/api.ts`
- Modify: `frontend/src/core/agents/hooks.ts`
- Modify: `frontend/src/core/agents/types.ts`
- Modify: `frontend/src/app/api/agents/store.ts`
- Modify: `frontend/src/app/api/agents/route.ts`
- Test: `frontend/src/core/agents/*.test.ts`

- [x] **Step 1: Add a failing frontend test that demonstrates agent inventory should come from canonical backend-managed data, not only `.deerflow-ui/agents.json`**

- [x] **Step 2: Implement the migration/proxy layer so existing local custom agents are preserved while the UI transitions to backend-managed agent data**

- [x] **Step 3: Keep built-in agent display behavior stable while switching the data source**

- [x] **Step 4: Re-run focused frontend tests for agent listing, deletion, and display naming**

Run:
`corepack pnpm --dir frontend test -- --runInBand src/core/agents`

Expected:
agent data-source and display tests pass with no regression in built-in labels

### Task 3: Build The Management Center Shell

**Files:**
- Add: `frontend/src/app/workspace/control-center/page.tsx`
- Add: `frontend/src/components/workspace/control-center/*.tsx`
- Modify: `frontend/src/components/workspace/workspace-surface-config.ts`
- Modify: `frontend/src/components/workspace/workspace-nav-chat-list.tsx`
- Test: `frontend/src/components/workspace/control-center/*.test.tsx`

- [x] **Step 1: Add the new workspace surface config and navigation entry for `/workspace/control-center`**

- [x] **Step 2: Create the management-center shell with four tabs: Runtime Config, Agents, Skills, Threads & History**

- [x] **Step 3: Reuse the existing workspace shell/chrome so the management center feels native to VibeCFD instead of an admin afterthought**

- [x] **Step 4: Add loading / empty / error states for each tab**

- [x] **Step 5: Run focused frontend tests for route presence and top-level shell rendering**

### Task 4: Implement Runtime Config Tab

**Files:**
- Add: `frontend/src/components/workspace/control-center/runtime-config-tab.tsx`
- Add: `frontend/src/core/runtime-config/api.ts`
- Add: `frontend/src/core/runtime-config/hooks.ts`
- Modify: `frontend/src/components/workspace/input-box.tsx`
- Modify: `frontend/src/components/workspace/skill-studio-workbench/thread-route.tsx`
- Test: `frontend/src/core/runtime-config/*.test.ts`

- [x] **Step 1: Add runtime-config client hooks and request types for backend summaries / updates**

- [x] **Step 2: Render lead-agent defaults, stage-role model overrides, provider availability, and config provenance**

- [x] **Step 3: Support editing inherit-vs-override behavior for stage roles and saving the result through the backend**

- [x] **Step 4: Make the current thread-level model selectors visibly consistent with the new canonical runtime config**

- [x] **Step 5: Run focused tests for runtime-config parsing, saving, and disabled-state behavior**

### Task 5: Implement Agents Tab

**Files:**
- Add: `frontend/src/components/workspace/control-center/agents-tab.tsx`
- Modify: `frontend/src/components/workspace/agents/agent-card.tsx`
- Modify: `frontend/src/components/workspace/agents/agent-gallery.tsx`
- Modify: `frontend/src/app/workspace/agents/page.tsx`
- Test: `frontend/src/components/workspace/agents/*.test.tsx`

- [x] **Step 1: Render a management-center agents table/grid with model, tool groups, migration status, and linked skill summary**

- [x] **Step 2: Support create/edit/delete flows from the management center without breaking the existing dedicated agents surface**

- [x] **Step 3: Add explicit agent detail / edit affordances instead of forcing chat-first entry**

- [x] **Step 4: Verify built-in agents stay non-destructive where intended and custom agents remain removable**

### Task 6: Implement Skills Tab With Preview And Binding Map

**Files:**
- Add: `frontend/src/components/workspace/control-center/skills-tab.tsx`
- Add: `frontend/src/components/workspace/control-center/skill-file-preview.tsx`
- Modify: `frontend/src/core/skills/api.ts`
- Modify: `frontend/src/core/skills/hooks.ts`
- Reuse / Modify: `frontend/src/components/workspace/skill-studio-workbench.utils.ts`
- Test: `frontend/src/core/skills/*.test.ts`
- Test: `frontend/src/components/workspace/control-center/*.test.tsx`

- [x] **Step 1: Add failing frontend tests for listing all skills, showing bound roles/agents, and previewing a selected skill file**

- [x] **Step 2: Extend the frontend skill client to consume lifecycle, graph, and file-preview APIs as one cohesive management data source**

- [x] **Step 3: Build the catalog list, binding map, and file preview panel**

- [x] **Step 4: Support enable/disable, lifecycle inspection, and rollback actions where the backend allows them**

- [x] **Step 5: Run focused tests for skill catalog rendering and file preview safety**

### Task 7: Implement Threads & History Tab With True Hard Delete

**Files:**
- Add: `frontend/src/components/workspace/control-center/threads-tab.tsx`
- Add: `frontend/src/core/thread-management/api.ts`
- Add: `frontend/src/core/thread-management/hooks.ts`
- Modify: `frontend/src/core/threads/hooks.ts`
- Modify: `frontend/src/components/workspace/recent-chat-list.tsx`
- Modify: `frontend/src/components/workspace/workspace-nav-chat-list.tsx`
- Test: `frontend/src/core/thread-management/*.test.ts`
- Test: `frontend/src/components/workspace/*.test.tsx`

- [x] **Step 1: Add a failing test for thread delete preview + cascade delete result handling**

- [x] **Step 2: Move thread deletion to the new backend-orchestrated cascade-delete contract instead of the current split frontend sequence**

- [x] **Step 3: Render unified thread inventory and size summaries in the management center, with any orphan cleanup controls treated as temporary rollout-only support**

- [x] **Step 4: Add rename/export/delete quick actions to the per-workbench recent-thread sidebars so users can manage threads where they work**

- [x] **Step 5: Confirm delete actions remove local thread directories and LangGraph state, and that orphan cleanup removes confirmed leftovers**

- [x] **Step 6: Run focused thread-management tests**

### Task 8: Final Integration, Verification, And Cleanup

**Files:**
- Modify: any touched docs / route wiring / i18n files required by the above tasks
- Verification: backend + frontend targeted suites plus browser proof

- [x] **Step 1: Refresh any impacted copy / i18n strings so the management center reads clearly in the existing workspace language**

- [x] **Step 2: Run backend verification for router, config, skill, and thread-management slices**

Run:
`uvx ruff check backend`
`uv run --project backend pytest tests/ -q`

Expected:
backend checks pass with no regression

- [x] **Step 3: Run focused frontend verification for control-center, agents, skills, and thread-management slices**

Run:
`corepack pnpm --dir frontend test -- --runInBand src/components/workspace/control-center src/core/agents src/core/skills src/core/thread-management`

Expected:
new frontend tests pass

- [x] **Step 4: Run browser validation from the user perspective**

Validate:
- the management center is discoverable from workspace navigation
- runtime config is visible and editable
- skills are visible, bindable, and previewable
- agents are manageable
- deleting a thread shows a preview and removes associated files
- per-surface quick actions remain consistent with the management center

- [ ] **Step 5: Remove temporary migration helpers or debug probes that are no longer needed**

- [x] **Step 6: Remove rollout-only orphan-audit UI after cleaning current leftovers, keeping steady-state thread management focused on canonical threads and delete preview**
