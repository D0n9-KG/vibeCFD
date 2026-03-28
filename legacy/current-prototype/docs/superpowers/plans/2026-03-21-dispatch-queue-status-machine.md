# Dispatch Queue Status Machine Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit queued state and a background dispatcher so run confirmation no longer launches execution inline.

**Architecture:** The API and LangGraph orchestration layer will stop after moving a run into a durable `queued` state. A new in-process dispatcher thread will poll the store, atomically claim queued runs, move them to `running`, and then call the selected execution engine asynchronously. This keeps request handling fast while making execution flow closer to the eventual multi-service architecture.

**Tech Stack:** FastAPI, LangGraph, Pydantic, threaded background dispatcher, pytest

---

## Chunk 1: Queue State And Dispatcher

### Task 1: Define queued behavior with failing tests

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\tests\test_orchestrator.py`
- Create: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\tests\test_dispatcher.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\tests\test_workflow_api.py`

- [x] **Step 1: Write the failing tests**

The tests should prove:
- orchestrator confirmation returns `queued`
- orchestrator no longer launches the engine directly
- a dispatcher can claim queued work and launch it
- API confirmation returns `queued`, then the run later reaches `completed`

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_orchestrator.py tests/test_dispatcher.py tests/test_workflow_api.py -q`
Expected: FAIL because `app.dispatcher` does not exist and queued behavior is not implemented yet.

### Task 2: Add queued status and atomic claim helpers

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\models.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\store.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\services\runs.py`

- [x] **Step 1: Add `queued` to the run status enum**
- [x] **Step 2: Change confirmation to persist a queued run instead of a running run**
- [x] **Step 3: Add a store method that atomically claims the next queued run and marks it running**
- [x] **Step 4: Update retry rules so queued runs cannot be retried while still in flight**
- [x] **Step 5: Run the affected tests**

Run: `python -m pytest tests/test_store.py tests/test_orchestrator.py -q`
Expected: PASS

### Task 3: Implement the background dispatcher

**Files:**
- Create: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\dispatcher.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\orchestration\graph.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\main.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\config.py`

- [x] **Step 1: Implement a polling dispatcher thread with `start()` and `stop()`**
- [x] **Step 2: Make the dispatcher claim queued runs and call `execution_engine.launch(run_id)`**
- [x] **Step 3: Remove inline launch from the orchestration graph**
- [x] **Step 4: Start the dispatcher from app service initialization and stop old instances on reconfiguration/shutdown**
- [x] **Step 5: Run the dispatcher and API tests**

Run: `python -m pytest tests/test_dispatcher.py tests/test_workflow_api.py -q`
Expected: PASS

## Chunk 2: Frontend And Documentation

### Task 4: Surface queued state in the frontend

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\lib\types.ts`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\App.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\RunHistoryPanel.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\styles.css`

- [x] **Step 1: Extend the frontend run status union with `queued`**
- [x] **Step 2: Show queued runs as waiting for dispatcher pickup**
- [x] **Step 3: Keep polling while a run is queued or running**
- [x] **Step 4: Run the frontend build**

Run: `npm run build`
Expected: PASS

### Task 5: Refresh architecture and delivery docs

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\README.md`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\docs\2026-03-20-external-dependencies-checklist.md`

- [x] **Step 1: Explain the new queued-to-running dispatcher flow**
- [x] **Step 2: Update the “already implemented” section with queueing and background dispatch**
- [x] **Step 3: Refine the “external dependencies” section so it distinguishes local dispatcher work from future external executor integration**
- [x] **Step 4: Re-read for continuity and readability**

## Final Verification

- [x] Run: `python -m pytest tests -q`
- [x] Run: `npm run build`
- [x] Run: `docker compose config`

Plan complete and saved to `docs/superpowers/plans/2026-03-21-dispatch-queue-status-machine.md`. Ready to execute.
