# Mainline End-To-End Bring-Up And Hardening Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then choose the execution skill that fits the work: use superpowers:subagent-driven-development when delegation benefits outweigh the round-trip, or superpowers:executing-plans when the work is better kept local. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the plan controls below, especially reuse, continuity, artifact lifecycle, validation/review cadence, and any research-overlay constraints.

**Goal:** Bring the freshly merged `main` branch to an actually runnable, smoke-tested local state by bootstrapping a clean worktree, starting the stack, identifying the real end-to-end blockers, and hardening the broken links until the critical user paths are usable.

**Architecture:** Work from a clean `main`-derived worktree so runtime setup and code fixes do not touch the dirty primary workspace. Use evidence-first bring-up to find the real startup and linkage boundaries, then switch individual fixes into TDD once each blocker is concrete enough to specify and keep.

**Tech Stack:** Python 3.12 + `uv` backend, Next.js 16 frontend, LangGraph/DeerFlow runtime, local config-driven service startup, optional OpenFOAM sandbox integration

**Prior Art Survey:** none needed - this is project-local bring-up and hardening on the merged mainline

**Reuse Strategy:** adapt existing project

**Session Status File:** `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`

**Context Summary:** `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

**Primary Context Files:** `README.md`; `Makefile`; `config.example.yaml`; `docker/openfoam-sandbox/README.md`; `docs/superpowers/plans/2026-04-10-main-branch-reconciliation-and-integration.md`; `docs/superpowers/session-status/2026-04-10-main-branch-reconciliation-and-integration-status.md`; `docs/superpowers/context-summaries/2026-04-10-main-branch-reconciliation-and-integration-summary.md`

**Artifact Lifecycle:** Keep this plan/status/context-summary chain while bring-up is active. Keep durable code fixes, tests, and config-resolution improvements that land on the new mainline. Keep untracked local runtime config files outside the repo root or referenced by explicit env vars; do not commit user-specific secrets or local credentials. Delete temporary screenshots, ad-hoc scratch scripts, transient terminal dumps, and orphaned copied runtime directories before closing this plan. Replace any temporary compatibility shim or diagnostic probe with the final production path before claiming the stack is fully usable.

**Workspace Strategy:** dedicated worktree

**Validation Strategy:** mixed

**Review Cadence:** each milestone

**Checkpoint Strategy:** milestone commits

**Research Overlay:** disabled

**Research Mainline:** none

**Non-Negotiables:** none

**Forbidden Regressions:** none

**Method Fidelity Checks:** none

**Scale Gate:** none

**Decision Log:** none - record durable decisions in the session status file for this engineering bring-up

**Research Findings:** none

**Uncertainty Hotspots:** clean-worktree dependency bootstrap on Windows; how local `config.yaml` / `extensions_config.json` should be supplied without polluting the repo; whether `make dev` is the right orchestration entrypoint on this machine; OpenFOAM sandbox/image availability; which user-facing flows still break after the stack starts

**Replan Triggers:** startup requires undocumented external infrastructure that cannot be emulated locally; the clean worktree cannot be launched without mutating the dirty primary workspace; the first successful stack launch still leaves too many independent runtime failures to keep one plan coherent; any blocker reveals that the merged mainline contract is incomplete enough to require a new integration decision rather than a local fix

---

### Task 1: Bootstrap The Clean Mainline Bring-Up Worktree

**Type:** Exploratory

**Files:**
- Notes: `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`
- Notes: `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

**Goal:** Confirm the clean `codex/main-bringup` worktree has the tools, dependencies, and local config inputs needed for runtime bring-up without touching the dirty primary workspace.

**Collect Evidence:**
- Whether backend dependencies install cleanly via `uv sync`
- Whether frontend dependencies install cleanly via `pnpm install`
- Whether local runtime config files can be supplied through explicit env vars instead of repo mutations

**Stop and Replan If:**
- Dependency installation fails because the mainline lockfiles or workspace manifests are broken
- The stack cannot be configured without modifying tracked files or the dirty primary workspace

**Checkpoint If:**
- The worktree is fully bootstrapped and ready for service startup

- [x] **Step 1: Capture the clean worktree baseline**

Run: `git status --short --branch`
Expected: clean `codex/main-bringup`

- [x] **Step 2: Verify the runtime prerequisites exist on this machine**

Run:
  - `uv --version`
  - `corepack pnpm --version`
  - `node --version`

Expected: all commands resolve without installation errors

- [x] **Step 3: Install backend dependencies in the bring-up worktree**

Run: `uv sync`
Working directory: `backend`
Expected: `.venv` is created or refreshed without resolver errors

- [x] **Step 4: Install frontend dependencies in the bring-up worktree**

Run: `corepack pnpm install --frozen-lockfile`
Working directory: `frontend`
Expected: `node_modules` installs without lockfile drift

- [x] **Step 5: Verify the local config source we will use for bring-up**

Run:
  - `Test-Path C:\Users\D0n9\Desktop\颠覆性大赛\config.yaml`
  - `Test-Path C:\Users\D0n9\Desktop\颠覆性大赛\extensions_config.json`

Expected: both return `True`, proving the clean worktree can reference the existing local runtime config via environment variables instead of copying secrets into the repo

- [x] **Step 6: Record the verified bootstrap state in the session status and context summary**

Update:
  - `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`
  - `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

- [ ] **Step 7: Checkpoint according to `Checkpoint Strategy` if bootstrap work changes tracked files**

If tracked files changed:

```bash
git add docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md
git commit -m "docs: initialize mainline bring-up tracking"
```

### Task 2: Launch The Stack And Capture The First Real Failure Boundary

**Type:** Exploratory

**Files:**
- Modify: `Makefile`
- Modify: `scripts/serve.sh`
- Notes: `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`
- Notes: `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

**Goal:** Start the clean mainline stack with explicit config env vars, prove which services come up, and capture the first concrete failure boundary instead of guessing.

**Collect Evidence:**
- Whether frontend, gateway, and LangGraph/dev runtime start together from the current startup scripts
- The actual ports, logs, and health endpoints that respond
- The first failing boundary: startup, proxying, auth/session, uploads, thread creation, Skill Studio, or Submarine runtime

**Stop and Replan If:**
- The startup path forks into multiple unrelated failures before any page can load
- The stack relies on hidden manual steps not expressed in repo docs/scripts

**Checkpoint If:**
- At least one reproducible failure boundary is captured with logs and exact repro steps

- [x] **Step 1: Read the current startup scripts before executing them**

Inspect:
  - `Makefile`
  - `scripts/serve.sh`
  - `scripts/start-daemon.sh`

Expected: one documented entrypoint for local bring-up is chosen before launching anything

- [x] **Step 2: Start the stack with explicit config env vars**

Run the chosen startup entrypoint with:
  - `DEER_FLOW_CONFIG_PATH=C:\Users\D0n9\Desktop\颠覆性大赛\config.yaml`
  - `DEER_FLOW_EXTENSIONS_CONFIG_PATH=C:\Users\D0n9\Desktop\颠覆性大赛\extensions_config.json`

Expected: capture exact frontend/gateway/runtime startup output rather than assuming success

- [x] **Step 3: Probe the expected local endpoints**

Check the endpoints exposed by the startup logs, then verify likely health surfaces such as:
  - frontend root
  - gateway `/api/models`
  - thread-related routes

Expected: identify which layer is up and which one is actually failing

- [x] **Step 4: Exercise one critical browser path**

Use the browser tooling against the running frontend and attempt:
  - landing page load
  - workspace entry
  - one thread/workbench route

Expected: one concrete user-facing success or one concrete failing interaction with logs/screenshots

- [x] **Step 5: Record the failure boundary and invoke `superpowers:revising-plans` if needed**

Update:
  - `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`
  - `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

Expected: a future session can resume from the exact failing boundary without rerunning blind startup work

### Task 3: Convert Each Concrete Blocker Into A Deterministic Fix Slice

**Type:** Exploratory

**Files:**
- Notes: `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`
- Notes: `docs/superpowers/context-summaries/2026-04-11-mainline-end-to-end-bringup-and-hardening-summary.md`

**Goal:** Reduce the first end-to-end failure boundary into a short blocker inventory where each remaining item is specific enough to fix under TDD instead of open-ended bring-up guesswork.

**Collect Evidence:**
- Ordered blocker list with exact repro commands or UI actions
- Which blockers are pure config/startup issues versus code defects
- Which flows are already working end-to-end

**Stop and Replan If:**
- The blocker list spans unrelated subsystems that should be split into separate plans
- A blocker can only be solved by changing product scope rather than fixing code or local runtime setup

**Checkpoint If:**
- The blocker inventory is short enough to execute as deterministic fixes in the current session

- [x] **Step 1: Classify each observed failure by boundary**

Use categories such as:
  - dependency/bootstrap
  - backend startup
  - frontend startup
  - proxy/base-url wiring
  - auth/session enforcement
  - uploads/artifacts
  - Skill Studio flow
  - Submarine runtime flow

- [x] **Step 2: Mark which blockers are configuration-only and which require code changes**

Expected: only code-backed blockers move into TDD slices; environment-only blockers get documented and resolved first

- [x] **Step 3: If the blocker list is now concrete, continue inline with `systematic-debugging` + `test-driven-development` per blocker**

Expected: the plan no longer drives vague bring-up; it hands off to evidence-backed bugfix execution

- [ ] **Step 4: If the blocker list is still too broad, invoke `superpowers:revising-plans` before touching product code**

Expected: the next plan reflects the real failure map rather than the initial bring-up guess
