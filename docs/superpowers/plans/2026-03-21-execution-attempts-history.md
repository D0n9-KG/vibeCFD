# Execution Attempts History Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Track each execution attempt as a first-class record so retries, failures and successful dispatches have durable per-attempt history.

**Architecture:** Keep `RunSummary` as the current run snapshot and keep `RunEvent` as append-only lifecycle history, then add a separate persisted attempts layer per run. The dispatcher will open an attempt when it claims a queued run, and store completion/failure paths will finalize the latest active attempt. The frontend will fetch and display attempts alongside timeline and events.

**Tech Stack:** FastAPI, Pydantic, JSON persistence, React + Vite, pytest

---

## Chunk 1: Attempts Persistence And API

### Task 1: Define attempts behavior with failing tests

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\tests\test_store.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\tests\test_dispatcher.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\tests\test_workflow_api.py`

- [x] **Step 1: Write the failing tests**

The tests should prove:
- attempts are persisted and reloaded
- dispatcher creates and completes an attempt when it launches a run
- API returns attempt history for a run

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_store.py tests/test_dispatcher.py tests/test_workflow_api.py -q`
Expected: FAIL because attempts do not exist yet.

### Task 2: Add attempt models and persistence

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\models.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\store.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\services\runs.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\dispatcher.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\main.py`

- [x] **Step 1: Add execution attempt models**
- [x] **Step 2: Persist attempts per run**
- [x] **Step 3: Create an attempt when dispatcher claims a queued run**
- [x] **Step 4: Finalize attempts on complete/fail**
- [x] **Step 5: Expose `GET /api/runs/{run_id}/attempts`**
- [x] **Step 6: Run backend tests**

Run: `python -m pytest tests/test_store.py tests/test_dispatcher.py tests/test_workflow_api.py -q`
Expected: PASS

## Chunk 2: Frontend And Docs

### Task 3: Surface attempts in the frontend

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\lib\types.ts`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\lib\api.ts`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\App.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\RunTimeline.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\styles.css`

- [x] **Step 1: Add attempt types and API client**
- [x] **Step 2: Load attempts with run details**
- [x] **Step 3: Render attempts below events**
- [x] **Step 4: Run the frontend build**

Run: `npm run build`
Expected: PASS

### Task 4: Update docs

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\README.md`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\docs\2026-03-20-external-dependencies-checklist.md`

- [x] **Step 1: Explain per-attempt execution history**
- [x] **Step 2: Update the local capability summary**
- [x] **Step 3: Re-read for continuity**

## Final Verification

- [x] Run: `python -m pytest tests -q`
- [x] Run: `npm run build`
- [x] Run: `docker compose config`

Plan complete and saved to `docs/superpowers/plans/2026-03-21-execution-attempts-history.md`. Ready to execute.
