# VibeCFD Legacy Workspace Retirement Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the `Prior Art Survey`, `Reuse Strategy`, `Session Status File`, `Primary Context Files`, `Artifact Lifecycle`, `Workspace Strategy`, `Validation Strategy`, `Review Cadence`, `Checkpoint Strategy`, `Uncertainty Hotspots`, and `Replan Triggers` fields below while executing.

**Goal:** Delete the stage-first and superseded workspace frontend files that are no longer part of the active VibeCFD runtime path, and leave behind explicit regression checks that they stay retired.

**Architecture:** Adapt the existing Chinese workbench implementation in place. Keep the active `submarine` and `skill-studio` routes, detail models, and shared workbench primitives; remove only the older pipeline/stage/dashboard/layout wrappers and their tests/utilities, then verify the active workbench contract still holds.

**Tech Stack:** Next.js 16, React 19, TypeScript, Node 24 `node:test`, ESLint, TypeScript compiler

**Prior Art Survey:** none needed - repo-local retirement of superseded frontend artifacts

**Reuse Strategy:** adapt existing project

**Session Status File:** `docs/superpowers/session-status/2026-04-08-vibecfd-legacy-workspace-retirement-status.md`

**Primary Context Files:**
- `docs/superpowers/plans/2026-04-08-vibecfd-superpowers-alignment-and-workbench-cleanup.md`
- `docs/superpowers/session-status/2026-04-08-vibecfd-superpowers-alignment-and-workbench-cleanup-status.md`
- `docs/superpowers/specs/2026-04-06-vibecfd-agentic-workbench-frontend-design.md`

**Artifact Lifecycle:** Keep this plan and its companion status file as the active handoff for the retirement pass. Delete the retired stage-first/pipeline/dashboard/layout files listed in this plan once tests prove they are no longer needed. Replace `workspace-resizable-ids` pipeline-only entries with the smaller active id set. Keep the active `submarine-workbench`, `skill-studio-workbench`, route tests, and detail-model tests. Superseded older execution plans may be deleted once the 2026-04-08 handoff chain is in place.

**Workspace Strategy:** branch in current workspace

**Validation Strategy:** strict tdd

**Review Cadence:** each milestone

**Checkpoint Strategy:** user-directed checkpoints

**Uncertainty Hotspots:** The legacy `submarine-pipeline` cluster may still own a helper or constant that another active file quietly depends on. Deleting old layout wrappers may expose dormant tests that were only guarding already-retired behavior.

**Replan Triggers:** Pause and revise the plan if deleting the legacy cluster breaks active `submarine` or `skill-studio` runtime paths, if `tsc --noEmit` reveals a broader dependency chain than the scoped search showed, or if unrelated dirty-worktree edits appear in the targeted frontend files.

---

## File Structure Map

### Retirement Regression Surface

- Create: `frontend/src/components/workspace/legacy-workspace-retirement.test.ts`
  Filesystem-level contract that the known-retired stage-first/pipeline/dashboard/layout files no longer exist.
- Modify: `frontend/src/components/workspace/workspace-resizable-ids.ts`
  Remove `submarine-pipeline`-only ids from the active id registry.
- Modify: `frontend/src/components/workspace/workspace-resizable-ids.test.ts`
  Lock the reduced active id set.

### Files To Delete

- Delete: `frontend/src/components/workspace/agentic-workbench/interrupt-action-bar.tsx`
- Delete: `frontend/src/components/workspace/agentic-workbench/agentic-workbench-layout.ts`
- Delete: `frontend/src/components/workspace/agentic-workbench/agentic-workbench-layout.test.ts`
- Delete: `frontend/src/components/workspace/submarine-pipeline.tsx`
- Delete: `frontend/src/components/workspace/submarine-pipeline.chat-rail.test.ts`
- Delete: `frontend/src/components/workspace/submarine-pipeline-runs.ts`
- Delete: `frontend/src/components/workspace/submarine-pipeline-runs.test.ts`
- Delete: `frontend/src/components/workspace/submarine-pipeline-shell.ts`
- Delete: `frontend/src/components/workspace/submarine-pipeline-shell.test.ts`
- Delete: `frontend/src/components/workspace/submarine-pipeline-sidebar.tsx`
- Delete: `frontend/src/components/workspace/submarine-pipeline-status.ts`
- Delete: `frontend/src/components/workspace/submarine-pipeline-status.test.ts`
- Delete: `frontend/src/components/workspace/submarine-stage-card.tsx`
- Delete: `frontend/src/components/workspace/submarine-stage-cards.tsx`
- Delete: `frontend/src/components/workspace/skill-studio-dashboard.tsx`
- Delete: `frontend/src/components/workspace/skill-studio-dashboard.utils.ts`
- Delete: `frontend/src/components/workspace/skill-studio-dashboard.utils.test.ts`
- Delete: `frontend/src/components/workspace/submarine-workbench/submarine-plan-stage.tsx`
- Delete: `frontend/src/components/workspace/submarine-workbench/submarine-execution-stage.tsx`
- Delete: `frontend/src/components/workspace/submarine-workbench/submarine-results-stage.tsx`
- Delete: `frontend/src/components/workspace/skill-studio-workbench/skill-studio-define-stage.tsx`
- Delete: `frontend/src/components/workspace/skill-studio-workbench/skill-studio-evaluate-stage.tsx`
- Delete: `frontend/src/components/workspace/skill-studio-workbench/skill-studio-publish-stage.tsx`
- Delete: `frontend/src/components/workspace/skill-studio-workbench/skill-studio-graph-stage.tsx`
- Delete: `frontend/src/app/workspace/submarine/submarine-pipeline-layout.ts`
- Delete: `frontend/src/app/workspace/submarine/submarine-pipeline-layout.test.ts`
- Delete: `frontend/src/app/workspace/submarine/submarine-workbench-layout.ts`
- Delete: `frontend/src/app/workspace/submarine/submarine-workbench-layout.test.ts`
- Delete: `frontend/src/app/workspace/skill-studio/skill-studio-workbench-layout.ts`
- Delete: `frontend/src/app/workspace/skill-studio/skill-studio-workbench-layout.test.ts`

## Task 1: Write The Retirement Regressions First

**Files:**
- Create: `frontend/src/components/workspace/legacy-workspace-retirement.test.ts`
- Modify: `frontend/src/components/workspace/workspace-resizable-ids.test.ts`

- [x] **Step 1: Add the failing retirement contract**

```ts
import assert from "node:assert/strict";
import { access } from "node:fs/promises";
import test from "node:test";

const retiredFiles = [
  "./agentic-workbench/interrupt-action-bar.tsx",
  "./submarine-pipeline.tsx",
  "./submarine-workbench/submarine-plan-stage.tsx",
  "./skill-studio-workbench/skill-studio-define-stage.tsx",
  "../app/workspace/submarine/submarine-pipeline-layout.ts",
  "../app/workspace/skill-studio/skill-studio-workbench-layout.ts",
];

for (const retiredFile of retiredFiles) {
  void test(`${retiredFile} has been retired`, async () => {
    await assert.rejects(access(new URL(retiredFile, import.meta.url)));
  });
}
```

```ts
void test("active resizable ids no longer expose submarine pipeline handles", () => {
  assert.deepEqual(WORKSPACE_RESIZABLE_IDS, {
    workspaceActivityBar: "workspace-activity-bar",
    workspaceContextSidebar: "workspace-context-sidebar",
    workspaceMainPane: "workspace-main-pane",
    workspaceChatRail: "workspace-chat-rail",
    chatBoxGroup: "workspace-chat-box-group",
    chatBoxArtifactsHandle: "workspace-chat-box-artifacts-handle",
  });
});
```

- [x] **Step 2: Run the retirement regressions to confirm the starting failure**

Run:
`Push-Location 'frontend/src/components/workspace'; node --test legacy-workspace-retirement.test.ts workspace-resizable-ids.test.ts; $exit=$LASTEXITCODE; Pop-Location; exit $exit`

Expected: FAIL because the retired files still exist and `workspace-resizable-ids.ts` still exposes `submarinePipeline*` keys.

## Task 2: Delete The Retired Stage-First And Pipeline Files

**Files:**
- Modify: `frontend/src/components/workspace/workspace-resizable-ids.ts`
- Delete the files listed in `Files To Delete`

- [x] **Step 1: Remove the pipeline-only ids from the active registry**

```ts
export const WORKSPACE_RESIZABLE_IDS = {
  workspaceActivityBar: "workspace-activity-bar",
  workspaceContextSidebar: "workspace-context-sidebar",
  workspaceMainPane: "workspace-main-pane",
  workspaceChatRail: "workspace-chat-rail",
  chatBoxGroup: "workspace-chat-box-group",
  chatBoxArtifactsHandle: "workspace-chat-box-artifacts-handle",
} as const;
```

- [x] **Step 2: Delete the retired workspace files**

Delete every file named in `Files To Delete`.

- [x] **Step 3: Re-run the retirement regressions**

Run:
`Push-Location 'frontend/src/components/workspace'; node --test legacy-workspace-retirement.test.ts workspace-resizable-ids.test.ts; $exit=$LASTEXITCODE; Pop-Location; exit $exit`

Expected: PASS

## Task 3: Verify The Active Runtime Surface Still Holds

**Files:**
- Modify: `docs/superpowers/session-status/2026-04-08-vibecfd-legacy-workspace-retirement-status.md`

- [x] **Step 1: Run the active route and workbench verification set**

Run:
`Push-Location -LiteralPath 'frontend/src/app/workspace/submarine/[thread_id]'; node --test page.test.ts; $exit=$LASTEXITCODE; Pop-Location; exit $exit`

Run:
`Push-Location -LiteralPath 'frontend/src/app/workspace/skill-studio/[thread_id]'; node --test page.test.ts; $exit=$LASTEXITCODE; Pop-Location; exit $exit`

Run:
`Push-Location 'frontend/src/components/workspace/agentic-workbench'; node --test workbench-shell.contract.test.ts workbench-copy.test.ts workbench-flow.contract.test.ts; $exit=$LASTEXITCODE; Pop-Location; exit $exit`

Run:
`Push-Location 'frontend/src/components/workspace/submarine-workbench'; node --test index.contract.test.ts submarine-session-model.test.ts submarine-detail-model.test.ts; $exit=$LASTEXITCODE; Pop-Location; exit $exit`

Run:
`Push-Location 'frontend/src/components/workspace/skill-studio-workbench'; node --test index.contract.test.ts skill-studio-session-model.test.ts skill-studio-detail-model.test.ts skill-studio-lifecycle-canvas.contract.test.ts thread-route.contract.test.ts; $exit=$LASTEXITCODE; Pop-Location; exit $exit`

Run:
`corepack pnpm --dir frontend exec eslint src/components/workspace/legacy-workspace-retirement.test.ts src/components/workspace/workspace-resizable-ids.ts src/components/workspace/workspace-resizable-ids.test.ts src/app/workspace/submarine/[thread_id]/page.tsx src/app/workspace/submarine/[thread_id]/page.test.ts --ext .ts,.tsx`

Run:
`corepack pnpm --dir frontend exec tsc --noEmit`

Expected: PASS across all commands.

- [x] **Step 2: Refresh the session status handoff**

Record:
- that the legacy files were deleted rather than archived
- the exact verification commands that passed
- any remaining delete-candidate legacy files, if any survive this pass
