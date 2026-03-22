# Run Events And Queue Cancel Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add structured run event history and allow queued runs to be cancelled before a dispatcher claims them.

**Architecture:** Keep the existing run snapshot in `run_state.json`, but add a parallel append-only event log per run so state transitions, retries, queueing, dispatch and cancellation have durable history. Expose that history through a dedicated API and add a `cancelled` lifecycle state that only applies before execution starts, preserving the current dispatcher boundary.

**Tech Stack:** FastAPI, Pydantic, append-only JSONL event log, React + Vite, pytest

---

## Chunk 1: Event History And Queue Cancellation

### Task 1: Define the new behavior with failing tests

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\tests\test_store.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\tests\test_workflow_api.py`
- Create: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\tests\test_run_events.py`

- [x] **Step 1: Write failing tests**

The tests should prove:
- each run writes structured events that can be reloaded
- the API exposes run events in chronological order
- a queued run can be cancelled and no longer dispatches
- a cancelled run can still be retried later

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_store.py tests/test_workflow_api.py tests/test_run_events.py -q`
Expected: FAIL because event history and queue cancellation do not exist yet.

### Task 2: Add event models and event persistence

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\models.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\store.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\services\runs.py`

- [x] **Step 1: Add a structured `RunEvent` model and `cancelled` status**
- [x] **Step 2: Persist events into a dedicated append-only event file**
- [x] **Step 3: Record high-value lifecycle events for create, prepare, queue, dispatch, complete, fail, retry and cancel**
- [x] **Step 4: Load persisted events on startup**
- [x] **Step 5: Run the targeted store tests**

Run: `python -m pytest tests/test_store.py tests/test_run_events.py -q`
Expected: PASS

### Task 3: Add queue cancellation and events API

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\main.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\store.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\dispatcher.py`

- [x] **Step 1: Add a cancellation method that only succeeds for queued runs**
- [x] **Step 2: Expose `GET /api/runs/{run_id}/events`**
- [x] **Step 3: Expose `POST /api/runs/{run_id}/cancel`**
- [x] **Step 4: Run API tests**

Run: `python -m pytest tests/test_workflow_api.py tests/test_run_events.py -q`
Expected: PASS

## Chunk 2: Frontend And Docs

### Task 4: Surface cancellation and event history in the frontend

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\lib\types.ts`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\lib\api.ts`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\App.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\RunHistoryPanel.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\WorkflowDraft.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\RunTimeline.tsx`

- [x] **Step 1: Extend frontend status types with `cancelled`**
- [x] **Step 2: Add queued-run cancellation interaction**
- [x] **Step 3: Show structured event history below the timeline**
- [x] **Step 4: Run the frontend build**

Run: `npm run build`
Expected: PASS

### Task 5: Update project docs

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\README.md`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\docs\2026-03-20-external-dependencies-checklist.md`

- [x] **Step 1: Explain the append-only event history layer**
- [x] **Step 2: Document queued-run cancellation as a local capability**
- [x] **Step 3: Reconcile the local-vs-external boundary sections**

## Final Verification

- [x] Run: `python -m pytest tests -q`
- [x] Run: `npm run build`
- [x] Run: `docker compose config`

Plan complete and saved to `docs/superpowers/plans/2026-03-21-run-events-and-queue-cancel.md`. Ready to execute.
