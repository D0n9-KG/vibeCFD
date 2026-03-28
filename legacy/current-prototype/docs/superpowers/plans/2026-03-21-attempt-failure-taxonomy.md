# Attempt Failure Taxonomy Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich execution attempts with duration, failure category, and failure source so local runs are easier to debug and document.

**Architecture:** Keep `ExecutionAttempt` as the per-dispatch history record, but extend it with stable metadata that survives restarts and failed launches. The store remains the source of truth for finalized attempts, while the dispatcher and recovery paths provide more specific failure classification. The frontend will present the richer metadata alongside each attempt, and the docs will explain how this local capability fits into the broader roadmap.

**Tech Stack:** FastAPI, Pydantic, JSON persistence, React + Vite, pytest

---

## Chunk 1: Backend Attempt Metadata

### Task 1: Lock the new behavior with failing tests

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\tests\test_store.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\tests\test_dispatcher.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\tests\test_workflow_api.py`

- [x] **Step 1: Write failing tests**

The tests should prove:
- attempts expose `duration_seconds`
- completed attempts can store a human-readable outcome summary
- failed attempts record `failure_category` and `failure_source`
- restart recovery and dispatch failures produce stable local classifications

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_store.py tests/test_dispatcher.py tests/test_workflow_api.py -q`
Expected: FAIL because the new attempt metadata is not implemented yet.

### Task 2: Implement enriched attempt persistence

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\models.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\store.py`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\backend\app\dispatcher.py`

- [x] **Step 1: Extend `ExecutionAttempt` with duration and failure taxonomy fields**
- [x] **Step 2: Compute duration when attempts finish**
- [x] **Step 3: Classify restart recovery failures and dispatch failures**
- [x] **Step 4: Keep persisted JSON backward-compatible for older attempt files**
- [x] **Step 5: Run backend tests**

Run: `python -m pytest tests/test_store.py tests/test_dispatcher.py tests/test_workflow_api.py -q`
Expected: PASS

## Chunk 2: Frontend And Docs

### Task 3: Show richer attempt metadata in the frontend

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\lib\types.ts`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\components\RunTimeline.tsx`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\frontend\src\styles.css`

- [x] **Step 1: Extend the frontend attempt type**
- [x] **Step 2: Render duration and failure taxonomy in the timeline panel**
- [x] **Step 3: Run the frontend build**

Run: `npm run build`
Expected: PASS

### Task 4: Update project docs

**Files:**
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\README.md`
- Modify: `C:\Users\D0n9\Desktop\颠覆性大赛\docs\2026-03-20-external-dependencies-checklist.md`

- [x] **Step 1: Explain the new attempt metadata clearly**
- [x] **Step 2: Update the local-vs-external capability summary**
- [x] **Step 3: Re-read the narrative for continuity**

## Final Verification

- [x] Run: `python -m pytest tests -q`
- [x] Run: `npm run build`
- [x] Run: `docker compose config`

Plan complete and saved to `docs/superpowers/plans/2026-03-21-attempt-failure-taxonomy.md`. Ready to execute.
