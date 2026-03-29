# Frontend Final Report Schema Unification v1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize the submarine workbench's parsed final-report contracts into one shared frontend module without changing UI behavior.

**Architecture:** Add a dedicated contract module for parsed artifact payloads, migrate `submarine-runtime-panel.utils.ts` to consume those shared types, and remove the page component's duplicated local `FinalReportPayload`. Keep summary/view-model logic in `utils` and leave rendering behavior unchanged.

**Tech Stack:** React, TypeScript, Node test runner

---

## File Map

- Create: `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`
  - shared parsed payload contracts for design brief, dispatch, geometry, solver results, and final report
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - import shared payload contracts and remove inline anonymous payload fragments where possible
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - import shared contracts and delete the local duplicated raw payload types
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - add a compile-time and runtime regression fixture that exercises the shared final-report contract

## Chunk 1: Shared Contract Boundary

### Task 1: Add a shared parsed-payload contract module

**Files:**
- Create: `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`

- [ ] **Step 1: Write the failing regression fixture**

Add a test fixture that references a shared `SubmarineFinalReportPayload` contract and uses it with the existing summary builders.

- [ ] **Step 2: Run the type check to verify it fails**

Run: `corepack pnpm exec tsc --noEmit`
Expected: FAIL because the shared contract module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create the contract module and move the raw parsed payload types into it.

- [ ] **Step 4: Run the type check to verify it passes**

Run: `corepack pnpm exec tsc --noEmit`
Expected: PASS for the new contract import.

## Chunk 2: Utils Migration

### Task 2: Make the summary builders consume the shared final-report contract

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`

- [ ] **Step 1: Write the failing targeted test**

Add or tighten a `scientific_followup_summary` fixture that is typed as `SubmarineFinalReportPayload` and flows through the existing builder helpers.

- [ ] **Step 2: Run the targeted frontend test to verify the failure**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL if the builders still depend on duplicated local payload shapes or broken imports.

- [ ] **Step 3: Write minimal implementation**

Update `submarine-runtime-panel.utils.ts` to import and use the shared payload contracts instead of anonymous structural payload types.

- [ ] **Step 4: Run the targeted frontend test to verify it passes**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

## Chunk 3: Page Migration And Final Verification

### Task 3: Remove the page component's duplicated final-report schema

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`

- [ ] **Step 1: Write the failing integration check**

Use the shared contract import in the page component and remove the local `FinalReportPayload` definition.

- [ ] **Step 2: Run full frontend verification**

Run:

- `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
- `corepack pnpm exec tsc --noEmit`

Expected: PASS with unchanged behavior.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.contract.ts frontend/src/components/workspace/submarine-runtime-panel.utils.ts frontend/src/components/workspace/submarine-runtime-panel.tsx frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts docs/superpowers/specs/2026-03-29-frontend-final-report-schema-unification-v1-design.md docs/superpowers/plans/2026-03-29-frontend-final-report-schema-unification-v1.md
git commit -m "refactor: unify submarine final report schema"
```
