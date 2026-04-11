# Frontend-Visible End-To-End Release Readiness Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then choose the execution skill that fits the work: use superpowers:subagent-driven-development when delegation benefits outweigh the round-trip, or superpowers:executing-plans when the work is better kept local. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the plan controls below, especially reuse, continuity, artifact lifecycle, validation/review cadence, and any research-overlay constraints.

**Goal:** Verify and harden the full product from a frontend-only user perspective until the main workspace is honestly ready for user-facing release.

**Architecture:** Stay on the active `main` workspace and treat the browser UI as the only allowed entry point for success criteria. Use visible user journeys to reproduce reality, then turn each confirmed blocker into a small TDD fix slice at the owning frontend or runtime boundary, and close with a production-oriented verification sweep.

**Tech Stack:** Next.js 16 frontend, TypeScript UI contracts, FastAPI gateway, DeerFlow/LangGraph runtime, browser-based end-to-end verification, local artifact-backed thread flows

**Prior Art Survey:** none needed - this is project-local release-readiness work on the active mainline

**Reuse Strategy:** adapt existing project

**Session Status File:** `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`

**Context Summary:** `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

**Primary Context Files:** `docs/superpowers/plans/2026-04-11-mainline-end-to-end-bringup-and-hardening.md`; `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`; `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`; `frontend/src/app/workspace/agents/page.tsx`; `frontend/src/app/workspace/chats/page.tsx`; `frontend/src/app/workspace/skill-studio/new/page.tsx`; `frontend/src/app/workspace/skill-studio/[thread_id]/page.tsx`; `frontend/src/app/workspace/submarine/[thread_id]/page.tsx`

**Artifact Lifecycle:** Keep this plan, its session status file, and its context summary as the active continuity chain for the release-readiness pass. Keep durable code fixes, focused regression tests, and any clarified startup or UI contract changes that land during this work. Delete temporary screenshots, one-off probe scripts, scratch notes, and stale PNG captures once the same evidence is preserved in durable docs or tests. Replace the previous "mainline bring-up complete" handoff as the current execution mainline, but keep it as historical context. Keep the desktop STL fixture at `C:\Users\D0n9\Desktop\suboff_solid.stl` as an external manual-test input, not a repo artifact.

**Workspace Strategy:** current workspace

**Validation Strategy:** mixed

**Review Cadence:** each milestone

**Checkpoint Strategy:** milestone commits

**Research Overlay:** disabled

**Research Mainline:** none

**Non-Negotiables:** none

**Forbidden Regressions:** none

**Method Fidelity Checks:** none

**Scale Gate:** none

**Decision Log:** none - record durable decisions in the session status file

**Research Findings:** none

**Uncertainty Hotspots:** whether the currently running frontend-only flows still match the 2026-04-11 handoff; whether user-visible input and artifact presentation remain intact across all major workspaces instead of only Skill Studio and submarine; whether any release blocker now lives in route transitions, missing-thread recovery, upload UX, or production build contracts; whether the current uncommitted submarine UX slice remains green while broader testing proceeds.

**Replan Triggers:** multiple unrelated subsystems fail in ways that require separate execution tracks; local services no longer match the documented startup assumptions; the only way to make a path work is through hidden backend-side manipulation rather than visible UI actions; current uncommitted user-facing fixes conflict with broader release-hardening changes.

---

### Task 1: Re-Baseline Main And Protect The Current Dirty Slice

**Type:** Exploratory

**Files:**
- Notes: `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`
- Notes: `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`
- Test: `frontend/src/components/workspace/submarine-workbench/submarine-session-model.test.ts`
- Test: `frontend/src/components/workspace/submarine-workbench/submarine-negotiation-panel.model.test.ts`
- Test: `frontend/src/components/workspace/submarine-workbench/index.contract.test.ts`

**Goal:** Reconcile the previously closed bring-up handoff with the actual dirty `main` workspace, confirm the local services are alive, and verify the current uncommitted submarine UX slice before broader testing begins.

**Collect Evidence:**
- exact git status and current branch baseline
- live health of `3000`, `8001`, and `2127`
- targeted verification result for the current submarine confirmation UX slice

**Stop and Replan If:**
- the dirty diff already fails its own targeted verification
- repo state conflicts with the durable handoff in a way that cannot be reconciled locally

**Checkpoint If:**
- the current dirty slice is verified and the browser-only test matrix is ready

- [ ] **Step 1: Capture the current workspace baseline**

Run:
  - `git status --short --branch`
  - `git log --oneline --decorate -5`
  - `git branch -vv`

Expected: `main` is active, the dirty submarine workbench slice is visible, and the safety snapshot branch still exists

- [ ] **Step 2: Probe the live services before touching runtime startup**

Run:
  - `Invoke-WebRequest http://127.0.0.1:3000/workspace/chats -UseBasicParsing | Select-Object -ExpandProperty StatusCode`
  - `Invoke-WebRequest http://127.0.0.1:8001/health -UseBasicParsing | Select-Object -ExpandProperty Content`
  - `Invoke-WebRequest http://127.0.0.1:2127/ok -UseBasicParsing | Select-Object -ExpandProperty Content`

Expected: each layer returns concrete success or failure evidence without assuming prior sessions still hold

- [ ] **Step 3: Re-run the focused submarine UX regression slice before broader work**

Run:
  - `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/components/workspace/submarine-workbench/submarine-session-model.test.ts" "src/components/workspace/submarine-workbench/submarine-negotiation-panel.model.test.ts" "src/components/workspace/submarine-workbench/index.contract.test.ts"`

Expected: the current dirty user-facing submarine confirmation work is green and safe to build on

- [ ] **Step 4: Record the reconciled baseline in the new status and summary files**

Update:
  - `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`
  - `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

### Task 2: Build The Frontend-Visible Journey Matrix

**Type:** Exploratory

**Files:**
- Modify: `frontend/src/app/workspace/agents/page.tsx`
- Modify: `frontend/src/app/workspace/chats/page.tsx`
- Modify: `frontend/src/app/workspace/skill-studio/new/page.tsx`
- Modify: `frontend/src/app/workspace/skill-studio/[thread_id]/page.tsx`
- Modify: `frontend/src/app/workspace/submarine/[thread_id]/page.tsx`
- Notes: `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`
- Notes: `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

**Goal:** Define the exact visible user journeys to test so the audit covers route entry, input, progression, artifacts, and completion across the whole product instead of a single thread.

**Collect Evidence:**
- which workspace routes exist and which ones create or resume flows
- which journeys require a pre-existing thread id and which can be created from visible UI
- which visible UI inputs and artifact panels should prove each flow is actually working

**Stop and Replan If:**
- a critical route has no real user-entry path and requires a product decision instead of a bug fix
- the product surface has split into separate subsystems that need independent plans

**Checkpoint If:**
- each major workspace has one concrete visible happy path and one concrete success signal

- [ ] **Step 1: Inspect the workspace route files and map user-entry surfaces**

Inspect:
  - `frontend/src/app/workspace/page.tsx`
  - `frontend/src/app/workspace/agents/page.tsx`
  - `frontend/src/app/workspace/chats/page.tsx`
  - `frontend/src/app/workspace/skill-studio/new/page.tsx`
  - `frontend/src/app/workspace/skill-studio/[thread_id]/page.tsx`
  - `frontend/src/app/workspace/submarine/[thread_id]/page.tsx`

Expected: one concrete route and visible-entry map for chats, agents, Skill Studio, and submarine

- [ ] **Step 2: Define the browser-only journey matrix**

Include:
  - `/workspace/chats`
  - `/workspace/agents`
  - visible Skill Studio creation path and a real thread path
  - visible submarine thread path using `C:\Users\D0n9\Desktop\suboff_solid.stl`

Expected: each journey includes starting route, visible input action, expected visible progress, and visible completion evidence

- [ ] **Step 3: Record the matrix and the first blocker candidate**

Update:
  - `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`
  - `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

### Task 3: Execute The Browser-Only End-To-End Matrix

**Type:** Exploratory

**Files:**
- Notes: `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`
- Notes: `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

**Goal:** Run the visible frontend journeys exactly as a user would, using the browser UI for all user input and the desktop STL file for submarine validation, and produce an ordered blocker inventory grounded in real repro.

**Collect Evidence:**
- whether `/workspace/chats` and `/workspace/agents` are usable from the visible UI
- whether Skill Studio can be started and advanced from visible controls
- whether submarine flow can accept the STL file, show visible progress, surface pending confirmations clearly, and render visible artifacts
- whether existing-thread routes still show usable state instead of dead ends

**Stop and Replan If:**
- the matrix reveals multiple unrelated release blockers that should be split into separate repair tracks
- the only reproducible issue is external infrastructure outside project control

**Checkpoint If:**
- the first blocker has a stable browser repro and owning code boundary

- [ ] **Step 1: Run the visible route smokes**

Check in the browser:
  - `/workspace/chats`
  - `/workspace/agents`
  - `/workspace/skill-studio/new`
  - one live Skill Studio thread route
  - one live submarine thread route

Expected: each route either works through a visible UI path or yields one concrete reproducible blocker

- [ ] **Step 2: Run a visible Skill Studio journey**

Use the visible page controls to:
  - start or resume a thread
  - submit user-visible text input
  - wait for visible workbench updates
  - confirm visible artifacts or packaged output appear

Expected: the user can understand progress and outcomes without backend-only intervention

- [ ] **Step 3: Run a visible submarine journey with the desktop STL fixture**

Use the visible page controls to:
  - upload `C:\Users\D0n9\Desktop\suboff_solid.stl`
  - submit visible text input through the page input, not hidden tooling
  - confirm pending confirmations are listed concretely
  - confirm visible artifact output appears in the workbench

Expected: the submarine chain works end-to-end from visible UI actions and surfaces enough information for a normal user to proceed

- [ ] **Step 4: Record the ordered blocker inventory**

Update:
  - `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`
  - `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

### Task 4: Turn Confirmed Blockers Into TDD Fix Slices

**Type:** Deterministic

**Files:**
- Modify: `frontend/src/app/workspace/**`
- Modify: `frontend/src/components/workspace/**`
- Modify: `frontend/src/core/**`
- Modify: `backend/app/gateway/**`
- Modify: `backend/packages/harness/deerflow/**`
- Test: `frontend/src/**/*.test.ts`
- Test: `frontend/src/**/*.test.tsx`
- Test: `backend/tests/**/*.py`
- Notes: `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`

**Goal:** Fix only reproduced release blockers, one root cause at a time, and keep each repair grounded in a failing test or equivalently deterministic validation.

- [ ] **Step 1: Add the smallest failing regression test for the top blocker**

Expected: one targeted test fails for the reproduced root cause

- [ ] **Step 2: Run the focused test to verify RED**

Expected: the failure matches the browser repro, not an unrelated harness problem

- [ ] **Step 3: Implement the minimal root-cause fix**

Expected: the owning boundary changes without opportunistic refactors

- [ ] **Step 4: Re-run the focused test, the narrow surrounding suite, and the original browser repro**

Expected: the regression test is green and the visible blocker is gone

- [ ] **Step 5: Refresh the durable handoff and continue with the next blocker if needed**

Update:
  - `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`
  - `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

### Task 5: Prove Release Readiness And Close The Milestone

**Type:** Deterministic

**Files:**
- Modify: `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`
- Modify: `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

**Goal:** Only claim release readiness after the touched slices, production build path, and visible critical journeys are all green together.

- [ ] **Step 1: Run milestone review for the finished repair slice**

Expected: reviewer findings are fixed or explicitly carried as remaining release blockers

- [ ] **Step 2: Run the required verification sweep**

Run:
  - targeted frontend and backend tests for changed slices
  - `corepack pnpm --dir frontend typecheck`
  - touched-file or relevant-scope frontend `eslint`
  - `corepack pnpm --dir frontend build` with the required auth env set for production-path verification

Expected: verification evidence is green for the actual changed surface

- [ ] **Step 3: Re-run the final visible user journeys**

Check:
  - `/workspace/chats`
  - `/workspace/agents`
  - visible Skill Studio create/resume flow
  - visible submarine flow with STL upload and follow-up input

Expected: the main user journeys still work from the visible frontend after the code fixes and verification sweep

- [ ] **Step 4: Refresh the final status and context summary with only verified state**

Expected: a future session can tell whether the project is truly ready to release or exactly what remains blocked
