# Run History And Retry Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a locally-complete run history and retry slice so the demo can list previous runs, recover interrupted runs after restart, and create retriable follow-up runs without any external dependencies.

**Architecture:** Extend the persisted `RunStore` so it can list runs and recover interrupted `running` states on startup, then add API endpoints for listing runs and retrying a previous run by cloning its stored request into a new run. Keep the frontend simple by adding a small run history panel that can load an old run or create a retry run from the UI.

**Tech Stack:** FastAPI, Pydantic, React, Vite, pytest

---

## Chunk 1: Backend TDD

### Task 1: Write failing tests for recovered runs, run listing, and retry

**Files:**
- Modify: `backend/tests/test_store.py`
- Modify: `backend/tests/test_workflow_api.py`

- [ ] **Step 1: Change the recovery test to assert interrupted running runs are marked recoverable after restart**
- [ ] **Step 2: Add a failing API test for `GET /api/runs`**
- [ ] **Step 3: Add a failing API test for `POST /api/runs/{run_id}/retry`**
- [ ] **Step 4: Run the targeted tests and verify they fail**

Run: `python -m pytest tests/test_store.py tests/test_workflow_api.py -q`
Expected: FAIL because list and retry endpoints do not exist and interrupted runs are not yet normalized into a recoverable state.

## Chunk 2: Backend Implementation

### Task 2: Implement recoverable run loading and run listing

**Files:**
- Modify: `backend/app/store.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add startup normalization for interrupted `running` runs**
- [ ] **Step 2: Add a `list_runs()` method sorted by newest first**
- [ ] **Step 3: Add `GET /api/runs`**
- [ ] **Step 4: Run targeted tests**

### Task 3: Implement retry run creation

**Files:**
- Modify: `backend/app/services/runs.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add a service method that clones a previous run request into a fresh run**
- [ ] **Step 2: Add `POST /api/runs/{run_id}/retry`**
- [ ] **Step 3: Make the retry response return the freshly prepared run**
- [ ] **Step 4: Run targeted tests**

## Chunk 3: Frontend Integration

### Task 4: Add a recent run history panel

**Files:**
- Create: `frontend/src/components/RunHistoryPanel.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add API helpers for list and retry**
- [ ] **Step 2: Add a small history panel that can select and retry runs**
- [ ] **Step 3: Keep the current run detail view unchanged**
- [ ] **Step 4: Build the frontend**

## Chunk 4: Verification

### Task 5: Run verification

**Files:**
- Test: `backend/tests/test_store.py`
- Test: `backend/tests/test_workflow_api.py`

- [ ] **Step 1: Run targeted backend tests**

Run: `python -m pytest tests/test_store.py tests/test_workflow_api.py -q`
Expected: PASS

- [ ] **Step 2: Run the full backend suite**

Run: `python -m pytest tests -q`
Expected: PASS

- [ ] **Step 3: Build the frontend**

Run: `npm run build`
Expected: PASS
