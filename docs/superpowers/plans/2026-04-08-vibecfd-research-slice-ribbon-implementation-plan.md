# VibeCFD Research Slice Ribbon Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the `Prior Art Survey`, `Reuse Strategy`, `Session Status File`, `Primary Context Files`, `Artifact Lifecycle`, `Workspace Strategy`, `Validation Strategy`, `Review Cadence`, `Checkpoint Strategy`, `Uncertainty Hotspots`, and `Replan Triggers` fields below while executing.

**Goal:** Replace the submarine workbench's fixed workflow-style center surface with a checkpoint-aware research-slice ribbon and current-slice card that support historical inspection without destructive rollback.

**Architecture:** Keep the existing three-part shell and negotiation rail, but replace the center `submarine-session-model` and `submarine-research-canvas` with a dynamic slice model. Derive slices from live thread/runtime/artifact state first, then add viewed-slice inspection state and top-ribbon navigation, while leaving room for future checkpoint-backed branching and compare surfaces.

**Tech Stack:** Next.js App Router, React, TypeScript, existing `agentic-workbench` primitives, DeerFlow/LangGraph thread state, current node-based frontend tests

**Prior Art Survey:** `docs/superpowers/prior-art/2026-04-08-vibecfd-timeline-workbench-survey.md`

**Reuse Strategy:** reference only

**Session Status File:** `docs/superpowers/session-status/2026-04-08-vibecfd-research-slice-ribbon-status.md`

**Primary Context Files:** `docs/superpowers/specs/2026-04-08-vibecfd-research-slice-ribbon-design.md`, `docs/superpowers/prior-art/2026-04-08-vibecfd-timeline-workbench-survey.md`, `frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts`, `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx`

**Artifact Lifecycle:** Keep the spec, prior-art survey, implementation plan, and session status as durable artifacts. Keep new slice-model tests that replace workflow-module tests. Replace the current fixed-module center model with slice-based state instead of leaving both models active. Delete temporary `.superpowers/brainstorm/...` mockup files before merge; they are brainstorming support artifacts, not product assets.

**Workspace Strategy:** branch in current workspace

**Validation Strategy:** mixed

**Review Cadence:** each milestone

**Checkpoint Strategy:** milestone commits

**Uncertainty Hotspots:** live thread state may not expose enough stable semantic checkpoints on first pass; current runtime payloads may still be too workflow-shaped; top-ribbon density may need tuning to stay readable on narrower widths; motion polish may need a lighter first pass than the full design ideal.

**Replan Triggers:** if live DeerFlow/LangGraph state cannot provide enough information to derive meaningful slices; if the redesign requires backend API additions for checkpoint history earlier than expected; if preserving the current negotiation rail causes severe layout regressions; if replacing the fixed module model breaks essential submarine detail surfaces that cannot be reattached cleanly.

---

## File Structure Map

- **Modify:** `frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts`
  - Replace fixed module order/state with slice-oriented session data and viewed-slice state.
- **Modify:** `frontend/src/components/workspace/submarine-workbench/submarine-session-model.test.ts`
  - Replace workflow-specific expectations with research-slice derivation and history-inspection tests.
- **Modify:** `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx`
  - Replace `WorkbenchFlow` module rendering with top ribbon + current slice card + historical viewing banner.
- **Create or split if needed:** `frontend/src/components/workspace/submarine-workbench/submarine-research-slice-ribbon.tsx`
  - Encapsulate ribbon node rendering, compact/expanded states, and current vs viewed node visuals.
- **Create or split if needed:** `frontend/src/components/workspace/submarine-workbench/submarine-research-slice-card.tsx`
  - Encapsulate center card rendering for one slice and reuse for active/history view.
- **Create or split if needed:** `frontend/src/components/workspace/submarine-workbench/submarine-research-slice-history-banner.tsx`
  - Encapsulate "viewing historical slice" banner and return-to-current action.
- **Modify:** `frontend/src/components/workspace/submarine-workbench/index.tsx`
  - Feed slice state into the new ribbon/card surface while preserving title, header, and negotiation rail.
- **Modify:** `frontend/src/components/workspace/submarine-workbench/index.contract.test.ts`
  - Update contract assertions from workflow chips/modules to ribbon/slice terms.
- **Modify:** `frontend/src/app/workspace/submarine/[thread_id]/page.test.ts`
  - Verify the route still mounts the new submarine workbench surface correctly.
- **Optional Modify:** `frontend/src/components/workspace/agentic-workbench/workbench-copy.ts`
  - Retire no-longer-used fixed submarine module copy if the slice model fully replaces it.

## Milestone 1: Replace the Fixed Center Model With Slice Data

### Task 1: Define the new slice model in tests first

**Files:**
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-session-model.test.ts`
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts`

- [x] **Step 1: Add a failing test for deriving an initial slice from a new or early submarine thread**

Add a test that expects the session model to produce one current slice summarizing the current objective instead of returning eight fixed modules.

- [x] **Step 2: Run the targeted test to verify the starting state fails for the right reason**

Run: `node --test frontend/src/components/workspace/submarine-workbench/submarine-session-model.test.ts`
Expected: FAIL because the current model still exposes fixed workflow modules instead of slices.

- [x] **Step 3: Add a failing test for viewed-slice vs active-slice distinction**

Cover the case where the user inspects a historical slice and the model keeps the current active slice unchanged while exposing the viewed slice separately.

- [x] **Step 4: Re-run the targeted test file to confirm both new expectations fail correctly**

Run: `node --test frontend/src/components/workspace/submarine-workbench/submarine-session-model.test.ts`
Expected: FAIL with slice-model mismatches, not syntax/setup errors.

- [x] **Step 5: Implement the minimal slice-oriented session model**

Refactor `submarine-session-model.ts` to:
- define slice types and slice summaries
- derive slices from current runtime/design brief/final report/message state
- expose current active slice separately from an optional viewed historical slice
- preserve live-progress/trust/negotiation summaries as session-level metadata

- [x] **Step 6: Re-run the targeted session-model tests**

Run: `node --test frontend/src/components/workspace/submarine-workbench/submarine-session-model.test.ts`
Expected: PASS

## Milestone 2: Render the Ribbon + Current Slice Card

### Task 2: Create the top ribbon and current-slice card UI with historical inspection mode

**Files:**
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx`
- Create: `frontend/src/components/workspace/submarine-workbench/submarine-research-slice-ribbon.tsx`
- Create: `frontend/src/components/workspace/submarine-workbench/submarine-research-slice-card.tsx`
- Create: `frontend/src/components/workspace/submarine-workbench/submarine-research-slice-history-banner.tsx`
- Modify: `frontend/src/components/workspace/submarine-workbench/index.contract.test.ts`

- [x] **Step 1: Add a failing contract test for the top ribbon replacing the current flow chip/module rendering**

Update `index.contract.test.ts` to look for the new ribbon/card surface and to fail if the old fixed flow rendering remains the center organizing primitive.

- [x] **Step 2: Run the contract test and confirm it fails against the old canvas structure**

Run: `node --test frontend/src/components/workspace/submarine-workbench/index.contract.test.ts`
Expected: FAIL because the old flow structure is still present.

- [x] **Step 3: Build the ribbon and slice-card components**

Implement:
- compact top ribbon with current slice + adjacent slices
- expandable history mode
- clear current vs viewed states
- a historical inspection banner with `返回当前研究`

- [x] **Step 4: Rework the research canvas to use the new components**

Replace the fixed `WorkbenchFlow`-driven center experience with:
- top ribbon
- optional historical inspection banner
- single current/viewed slice card
- retained secondary detail layers where they still make sense

- [x] **Step 5: Re-run the contract test**

Run: `node --test frontend/src/components/workspace/submarine-workbench/index.contract.test.ts`
Expected: PASS

- [x] **Step 6: Run targeted type/lint validation for the new components**

Run: `corepack pnpm --dir frontend exec eslint frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx frontend/src/components/workspace/submarine-workbench/submarine-research-slice-ribbon.tsx frontend/src/components/workspace/submarine-workbench/submarine-research-slice-card.tsx frontend/src/components/workspace/submarine-workbench/submarine-research-slice-history-banner.tsx frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts`
Expected: PASS

### Task 3: Preserve the existing route shell and negotiation rail while wiring view state

**Files:**
- Modify: `frontend/src/components/workspace/submarine-workbench/index.tsx`
- Modify: `frontend/src/app/workspace/submarine/[thread_id]/page.test.ts`

- [ ] **Step 1: Add a failing route-level test or source assertion for the ribbon-based workbench state**

Make the route test fail until the submarine thread page clearly mounts the ribbon/slice version of the workbench without removing the negotiation rail.

- [ ] **Step 2: Run the targeted route test and confirm the failure**

Run: `node --test frontend/src/app/workspace/submarine/[thread_id]/page.test.ts`
Expected: FAIL because the route has not yet been updated for the ribbon view state expectations.

- [ ] **Step 3: Wire active/viewed slice state into the workbench entry component**

Update `index.tsx` to:
- hold the currently viewed historical slice ID
- pass current/viewed state to the canvas
- preserve the existing header and negotiation rail contract

- [ ] **Step 4: Re-run the route-level test**

Run: `node --test frontend/src/app/workspace/submarine/[thread_id]/page.test.ts`
Expected: PASS

> Note: current implementation intentionally keeps viewed-slice inspection canvas-local until a route-level sharing need appears. Revisit Task 3 only if history selection must become shareable outside the center surface.

## Milestone 3: Make Slice Creation Feel Agentic Instead of Workflow-Driven

### Task 4: Replace fixed workflow labels and heuristics with semantic slice triggers

**Files:**
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts`
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-session-model.test.ts`
- Optional Modify: `frontend/src/components/workspace/agentic-workbench/workbench-copy.ts`

- [x] **Step 1: Add failing tests for semantic slice creation**

Add tests that expect slice creation from:
- geometry becoming concrete
- runtime entering a different execution meaning
- result/report artifacts appearing

and explicitly avoid requiring a full fixed order.

- [x] **Step 2: Run the targeted slice-model tests and confirm failure**

Run: `node --test frontend/src/components/workspace/submarine-workbench/submarine-session-model.test.ts`
Expected: FAIL because current heuristics still lean on fixed workflow logic.

- [x] **Step 3: Implement semantic trigger heuristics**

Update slice derivation to:
- create slices from semantic milestones
- avoid mandatory presence/order of every historical slice
- preserve a coherent current summary even when only one or two slices exist

- [x] **Step 4: Remove or retire no-longer-needed fixed submarine module copy**

If the new slice model fully replaces the old module titles, remove the now-dead submarine workflow copy instead of leaving both active.

- [x] **Step 5: Re-run the slice-model tests**

Run: `node --test frontend/src/components/workspace/submarine-workbench/submarine-session-model.test.ts`
Expected: PASS

## Milestone 4: Polish Motion, Narrow-Screen Behavior, and Repo Hygiene

### Task 5: Add restrained motion and responsive behavior without destabilizing the shell

**Files:**
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx`
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-research-slice-ribbon.tsx`
- Modify: relevant tests only if motion or responsive markers need contract coverage

- [x] **Step 1: Capture the current narrow-screen behavior and source contracts**

Use the existing contract/source tests as baseline evidence. If needed, add one failing assertion that the ribbon still renders meaningfully without consuming the negotiation rail layout.

- [x] **Step 2: Add restrained transitions**

Implement lightweight transitions for:
- switching viewed slices
- entering/leaving historical inspection mode
- highlighting newly active slices

Avoid heavy animation libraries unless the existing stack already uses one nearby.

- [x] **Step 3: Verify responsive behavior and no layout regressions**

Run: `node --test frontend/src/components/workspace/submarine-workbench/index.contract.test.ts frontend/src/app/workspace/submarine/[thread_id]/page.test.ts`
Expected: PASS

- [x] **Step 4: Run full targeted frontend verification**

Run: `node --test frontend/src/core/threads/utils.test.ts frontend/src/core/threads/use-thread-stream.state.test.ts frontend/src/components/workspace/submarine-workbench/index.contract.test.ts frontend/src/components/workspace/submarine-workbench/submarine-session-model.test.ts frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.model.test.ts frontend/src/app/workspace/submarine/[thread_id]/page.test.ts frontend/src/components/workspace/skill-studio-workbench/index.contract.test.ts`
Expected: PASS

- [x] **Step 5: Run full lint/type verification for touched frontend files**

Run: `corepack pnpm --dir frontend exec tsc --noEmit`
Expected: PASS

Run: `corepack pnpm --dir frontend exec eslint src/components/workspace/submarine-workbench src/app/workspace/submarine/[thread_id]/page.tsx src/components/workspace/agentic-workbench/workbench-copy.ts`
Expected: PASS

- [x] **Step 6: Retire temporary brainstorming artifacts**

Delete the temporary `.superpowers/brainstorm/...` mockup files created during design exploration so they do not remain as active repo artifacts.

## Milestone Review Checklist

After each milestone, confirm:

- the center submarine workbench no longer presents itself as a fixed workflow
- the current active slice remains distinct from any viewed historical slice
- the negotiation rail still behaves like a normal conversation surface
- titles, live progress, and evidence summaries still surface meaningful CFD context
- no dead workflow-specific center-surface code remains active alongside the new slice model
