# Frontend Workbench Redesign Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current card-heavy demo page with a Chinese simulation-workbench interface that improves visual quality, task flow clarity, and everyday usability.

**Architecture:** Keep the existing data flow and API hooks, but rebuild the frontend around a fixed workbench shell: top command bar, left operations sidebar, center graphics workspace, right inspector, and bottom dock. Use lightweight presentational components for each workbench region so the page structure is stable while different run states swap content in and out. Introduce minimal frontend test coverage around the new shell and high-priority interaction labels so the redesign has guardrails during future iteration.

**Tech Stack:** React 18, TypeScript, Vite, CSS, Vitest, React Testing Library

---

## Chunk 1: Test Harness And Workbench Shell

### Task 1: Add a minimal frontend test harness and write failing shell tests

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\package.json`
- Create: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\vite.config.ts`
- Create: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\test\setup.ts`
- Create: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\test\fixtures.ts`
- Create: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\App.test.tsx`

- [ ] **Step 1: Add Vitest and Testing Library dependencies**
- [ ] **Step 2: Write a failing test that expects the new Chinese workbench shell regions and command labels**
- [ ] **Step 3: Run the test to verify it fails**

Run: `npm test -- --run`
Expected: FAIL because the new workbench shell does not exist yet.

### Task 2: Build the new application shell

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\App.tsx`
- Create: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\WorkbenchHeader.tsx`
- Create: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\GraphicsWorkspace.tsx`
- Create: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\DockPanel.tsx`

- [ ] **Step 1: Replace the card waterfall layout with the fixed workbench shell**
- [ ] **Step 2: Move global run status and high-frequency actions into the top command bar**
- [ ] **Step 3: Add a center graphics workspace with primary and secondary viewports**
- [ ] **Step 4: Add a bottom dock shell for long-form content**
- [ ] **Step 5: Run the shell tests**

Run: `npm test -- --run`
Expected: PASS

## Chunk 2: Sidebar, Inspector, And Dock Content

### Task 3: Refactor the left sidebar into compact operational panels

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\TaskForm.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\CandidateCases.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\RunHistoryPanel.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\lib\types.ts`

- [ ] **Step 1: Rewrite the task intake panel with shorter Chinese software-style labels**
- [ ] **Step 2: Compress candidate cases into scan-friendly selectable rows**
- [ ] **Step 3: Compress run history into a compact list with clear status badges and quick actions**
- [ ] **Step 4: Run the frontend tests**

Run: `npm test -- --run`
Expected: PASS

### Task 4: Split summary content between the right inspector and bottom dock

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\WorkflowDraft.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\RunTimeline.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\ArtifactsPanel.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\lib\api.ts`

- [ ] **Step 1: Convert workflow details into a compact inspector summary**
- [ ] **Step 2: Move timeline, events, attempts, artifacts, and report into bottom dock tabs**
- [ ] **Step 3: Preserve existing confirm, cancel, retry, and artifact behaviors in the new structure**
- [ ] **Step 4: Run the frontend tests**

Run: `npm test -- --run`
Expected: PASS

## Chunk 3: Visual System And Final Copy Pass

### Task 5: Replace the current dark glass style with a light engineering workbench system

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\styles.css`

- [ ] **Step 1: Define a light workbench color system, spacing scale, and Chinese-friendly typography**
- [ ] **Step 2: Style the shell, side panels, graphics windows, inspector cards, and dock tabs**
- [ ] **Step 3: Add hover, focus, and responsive states without reintroducing “AI landing page” aesthetics**
- [ ] **Step 4: Run the frontend tests**

Run: `npm test -- --run`
Expected: PASS

### Task 6: Update supporting docs

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\README.md`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\docs/superpowers/specs/2026-03-21-frontend-workbench-redesign-design.md`

- [ ] **Step 1: Record that the frontend now uses a Chinese workbench layout**
- [ ] **Step 2: Update the spec document with any implementation-level refinements**
- [ ] **Step 3: Re-read for continuity**

## Final Verification

- [ ] Run: `npm test -- --run`
- [ ] Run: `npm run build`

Plan complete and saved to `docs/superpowers/plans/2026-03-21-frontend-workbench-redesign.md`. Ready to execute.
