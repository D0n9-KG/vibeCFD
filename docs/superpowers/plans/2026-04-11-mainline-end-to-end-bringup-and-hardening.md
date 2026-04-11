# Mainline End-To-End Bring-Up And Hardening Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then choose the execution skill that fits the work: use superpowers:subagent-driven-development when delegation benefits outweigh the round-trip, or superpowers:executing-plans when the work is better kept local. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the plan controls below, especially reuse, continuity, artifact lifecycle, validation/review cadence, and any research-overlay constraints.

**Goal:** Bring the active `main` workspace to a genuinely runnable state across the critical local product paths, and keep fixing real blockers until the mainline stack is usable without worktree-only assumptions.

**Architecture:** Work directly in the primary workspace on `main`, because the temporary integration worktrees are already retired and the user explicitly approved `main` as the active repair branch. Re-establish the real local runtime baseline first, then drive the remaining work from reproducible user-path failures, converting each confirmed blocker into a small TDD fix slice.

**Tech Stack:** Python 3.12 + `uv` backend, FastAPI gateway, DeerFlow/LangGraph runtime, Next.js 16 frontend, local config-driven startup, browser smoke verification

**Prior Art Survey:** none needed - this is project-local runtime closure on the active mainline

**Reuse Strategy:** adapt existing project

**Session Status File:** `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`

**Context Summary:** `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

**Primary Context Files:** `README.md`; `Makefile`; `scripts/serve.sh`; `scripts/start-daemon.sh`; `docs/superpowers/plans/2026-04-10-main-branch-reconciliation-and-integration.md`; `docs/superpowers/session-status/2026-04-10-main-branch-reconciliation-and-integration-status.md`; `docs/superpowers/context-summaries/2026-04-10-main-branch-reconciliation-and-integration-summary.md`

**Artifact Lifecycle:** Keep this plan/status/context-summary chain while runtime closure is active. Keep durable code fixes, tests, and startup-contract clarifications that land on `main`. Delete temporary screenshots, ad-hoc scratch probes, and unreferenced temporary PNG artifacts when the same evidence is captured in durable tests or docs. Keep the safety snapshot branch until the repaired `main` state is clearly stable. Do not add new parallel worktrees unless a later blocker proves current-workspace isolation is no longer safe.

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

**Uncertainty Hotspots:** whether the three local services are still running from the primary workspace; whether anonymous local frontend dev still works without `BETTER_AUTH_SECRET`; whether any user-facing path beyond the previously verified Skill Studio and submarine flows is still broken; whether leftover repo clutter is only cosmetic or still misleading active development

**Replan Triggers:** startup now requires undocumented manual steps; critical flows fail in multiple unrelated subsystems at once; the next blocker requires a broader architecture or product-scope change instead of a targeted fix; current-workspace execution becomes unsafe because of conflicting uncommitted user changes

---

### Task 1: Re-Baseline The Active Main Workspace

**Type:** Exploratory

**Files:**
- Notes: `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`
- Notes: `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

**Goal:** Reconcile the written bring-up record with the actual `main` workspace, local branch inventory, and live service state before touching product code again.

**Collect Evidence:**
- Whether `main` is clean and what commit it currently points to
- Which local branches remain and which one is intentionally preserved as a safety snapshot
- Whether frontend, gateway, and LangGraph endpoints are already alive from the primary workspace

**Stop and Replan If:**
- Repo state disagrees with the durable handoff in a way that cannot be reconciled locally
- Current workspace already contains conflicting uncommitted user edits in files needed for runtime closure

**Checkpoint If:**
- The baseline is fully recorded and the next real blocker boundary is visible

- [x] **Step 1: Capture the current git baseline**

Run:
  - `git status --short --branch`
  - `git log --oneline --decorate -5`
  - `git branch -vv`

Expected: clean `main`, plus the explicit safety snapshot branch

- [x] **Step 2: Probe the expected local service endpoints before restarting anything**

Run:
  - `Invoke-WebRequest http://127.0.0.1:3000 -UseBasicParsing | Select-Object StatusCode`
  - `Invoke-WebRequest http://127.0.0.1:8001/health -UseBasicParsing | Select-Object -ExpandProperty Content`
  - `Invoke-WebRequest http://127.0.0.1:2127/ok -UseBasicParsing | Select-Object -ExpandProperty Content`

Expected: exact success/failure evidence for each layer

- [x] **Step 3: If any service is down, inspect the startup entrypoints before restarting**

Inspect:
  - `README.md`
  - `Makefile`
  - `scripts/serve.sh`
  - `scripts/start-daemon.sh`

Expected: one current startup path is chosen from repo evidence, not memory

- [x] **Step 4: Record the reconciled baseline in the session status and context summary**

Update:
  - `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`
  - `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

### Task 2: Reproduce The Highest-Value User Paths And Build A Fresh Blocker Inventory

**Type:** Exploratory

**Files:**
- Notes: `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`
- Notes: `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

**Goal:** Reproduce the real current failures, if any, across the critical workspace flows instead of assuming prior green runs still represent the current state.

**Collect Evidence:**
- Whether `/workspace/agents`, `/workspace/chats`, `/workspace/skill-studio/new`, and `/workspace/submarine/new` still load
- Whether a fresh Skill Studio thread and a fresh submarine thread can still complete their main happy paths
- Exact failing step, logs, and network/error boundaries for the first real blocker

**Stop and Replan If:**
- The blocker inventory spans multiple unrelated subsystems that should be split into separate plans
- A major failure now comes from scope changes or missing external infrastructure rather than a project-local defect

**Checkpoint If:**
- The highest-severity blocker is specific enough to own with one targeted failing test

- [x] **Step 1: Exercise the critical workspace routes in the browser**

Check:
  - `/workspace/agents`
  - `/workspace/chats`
  - `/workspace/skill-studio/new`
  - `/workspace/submarine/new`

Expected: each route either loads cleanly or yields one concrete reproducible failure

- [x] **Step 2: Run one fresh Skill Studio happy-path smoke**

Expected evidence:
  - thread creation succeeds
  - route promotion behaves correctly
  - artifacts appear in the workbench

- [x] **Step 3: Run one fresh submarine happy-path smoke**

Expected evidence:
  - thread creation succeeds
  - generated artifacts surface in the workbench
  - the page remains usable through completion

- [x] **Step 4: Record the ordered blocker inventory and the next fix target**

Update:
  - `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`
  - `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

### Task 3: Convert Each Confirmed Blocker Into A TDD Fix Slice

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
- Notes: `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`

**Goal:** Fix only reproduced blockers, one root cause at a time, with a failing test or equivalent deterministic validation entry point before changing production code.

- [x] **Step 1: Add the smallest failing regression test for the top blocker**

Expected: one targeted test that fails for the reproduced reason

- [x] **Step 2: Run the targeted test to verify RED**

Expected: failure matches the reproduced blocker, not a typo or broken harness

- [x] **Step 3: Implement the minimal production fix at the owning boundary**

Expected: one root-cause fix without opportunistic refactors

- [x] **Step 4: Re-run the targeted test and the narrow surrounding suite**

Expected: GREEN on the new regression plus no local regressions in the touched slice

- [x] **Step 5: Re-run the original user-path repro**

Expected: the reproduced blocker is gone in the browser or runtime path that originally failed

- [x] **Step 6: If more blockers remain, repeat Task 3 for the next one and keep the durable handoff current**

Expected: session status always reflects the current blocker queue and what was verified

### Task 4: Run Milestone Review And Full Closure Verification

**Type:** Deterministic

**Files:**
- Modify: `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`
- Modify: `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

**Goal:** At each meaningful milestone, independently verify the narrowed diff, run the required regression suites, and refresh the durable handoff before claiming progress.

- [x] **Step 1: Run the reviewer checkpoint for the current milestone**

Expected: reviewer findings are either fixed or explicitly called out before proceeding

- [x] **Step 2: Run the required local verification for the touched slices**

Expected candidates:
  - frontend targeted tests
  - backend targeted tests
  - frontend `typecheck`
  - frontend `lint`
  - frontend `build` when the touched area can affect production buildability

- [x] **Step 3: Refresh the session status and context summary with only verified state**

Expected: a future session can continue without rediscovering the same boundary

### Task 5: Finish Runtime Closure On Main

**Type:** Deterministic

**Files:**
- Modify: `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`
- Modify: `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

**Goal:** Once the critical paths are green, leave `main` in a clean, verified, low-confusion state.

- [x] **Step 1: Remove stale temporary artifacts created during this closure pass**

Expected: scratch files, screenshots, and unreferenced probes are deleted or explicitly kept

- [x] **Step 2: Run one final end-to-end verification sweep on the main happy paths**

Expected: the critical workspace flows are still green after cleanup

- [x] **Step 3: Refresh the durable handoff with the final verified state and remaining risks**

Expected: status file says exactly what is complete, what remains, and what operational caveats still exist
