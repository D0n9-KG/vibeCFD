# Submarine Demo MVP Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable demo that turns a submarine-analysis request into a transparent workflow with case retrieval, user confirmation, simulated execution, visible run artifacts, and a final report.

**Architecture:** Use a React frontend plus a FastAPI backend. Keep the LangGraph / Claude Code / OpenFOAM architecture as explicit data contracts and workflow states, but implement this first cut with a local in-process workflow engine and a mock executor that writes realistic artifacts into the documented `runs/` directory structure.

**Tech Stack:** React, TypeScript, Vite, FastAPI, Pydantic, Python background tasks, local JSON data, Markdown reports

---

## Chunk 1: Project Skeleton

### Task 1: Create repository layout

**Files:**
- Create: `frontend/`
- Create: `backend/`
- Create: `data/cases/`
- Create: `data/skills/`
- Create: `runs/`
- Create: `uploads/`

- [ ] **Step 1: Create the folders**

Run: create the directory tree for frontend, backend, shared data, uploads, and runs.
Expected: folders exist and map cleanly to the demo architecture in the project doc.

- [ ] **Step 2: Add startup manifests**

Run: create `frontend/package.json`, `backend/requirements.txt`, and top-level helper scripts.
Expected: each app has an explicit entrypoint and install surface.

## Chunk 2: Seed Structured Knowledge

### Task 2: Add structured case library entries

**Files:**
- Create: `data/cases/*.json`
- Create: `data/cases/index.json`

- [ ] **Step 1: Write the seed case entries**

Include at least 8 structured entries with the required fields from the doc:
`case_id`, `title`, `geometry_family`, `geometry_description`, `task_type`, `condition_tags`, `input_requirements`, `expected_outputs`, `recommended_solver`, `mesh_strategy`, `bc_strategy`, `postprocess_steps`, `validation_targets`, `reference_sources`, `reuse_role`, `linked_skills`.

- [ ] **Step 2: Verify the entries are consumable**

Run: `python -m json.tool data/cases/index.json > $null`
Expected: JSON parses successfully.

### Task 3: Add skill manifests

**Files:**
- Create: `data/skills/*.json`
- Create: `data/skills/index.json`

- [ ] **Step 1: Write P0 skill manifests**

Include manifests for `case-search`, `geometry-check`, `mesh-prep`, `solver-openfoam`, `postprocess`, and `report`.

- [ ] **Step 2: Verify manifest JSON**

Run: `python -m json.tool data/skills/index.json > $null`
Expected: JSON parses successfully.

## Chunk 3: Backend Workflow

### Task 4: Scaffold the FastAPI app

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/models.py`
- Create: `backend/app/store.py`
- Create: `backend/app/__init__.py`
- Create: `backend/requirements.txt`

- [ ] **Step 1: Write the failing API smoke test**

**Test file:** `backend/tests/test_health.py`

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_check():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest backend/tests/test_health.py -q`
Expected: FAIL because the app does not exist yet.

- [ ] **Step 3: Implement the minimal API app**

Expose `/api/health` and wire the app package.

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest backend/tests/test_health.py -q`
Expected: PASS.

### Task 5: Implement request, retrieval, confirmation, and run models

**Files:**
- Modify: `backend/app/models.py`
- Create: `backend/tests/test_models.py`

- [ ] **Step 1: Write failing tests for the task and run models**

Cover request payloads, retrieval payloads, and run status serialization.

- [ ] **Step 2: Run the targeted tests**

Run: `pytest backend/tests/test_models.py -q`
Expected: FAIL because the models are missing.

- [ ] **Step 3: Implement the Pydantic models**

Add models for:
- task submission
- candidate cases
- workflow draft
- confirmation request
- run summary
- artifact manifest

- [ ] **Step 4: Re-run the tests**

Run: `pytest backend/tests/test_models.py -q`
Expected: PASS.

### Task 6: Implement the case-library service

**Files:**
- Create: `backend/app/services/cases.py`
- Create: `backend/tests/test_case_service.py`

- [ ] **Step 1: Write a failing retrieval test**

The test should submit a `task_type` like `pressure_distribution` and verify that related `DARPA SUBOFF` or `Type 209` entries are returned first with rationale text.

- [ ] **Step 2: Run the retrieval test**

Run: `pytest backend/tests/test_case_service.py -q`
Expected: FAIL because the case service does not exist yet.

- [ ] **Step 3: Implement retrieval**

Load local JSON data, score by task type, geometry family hints, condition tags, and keyword overlap, then return the top candidates and a recommended selection.

- [ ] **Step 4: Re-run the retrieval test**

Run: `pytest backend/tests/test_case_service.py -q`
Expected: PASS.

### Task 7: Implement run directory creation

**Files:**
- Create: `backend/app/services/runs.py`
- Create: `backend/tests/test_run_service.py`

- [ ] **Step 1: Write a failing run-layout test**

Assert that creating a run produces:

```text
runs/<run_id>/
  request/
  retrieval/
  execution/
  postprocess/
  report/
```

- [ ] **Step 2: Run the test**

Run: `pytest backend/tests/test_run_service.py -q`
Expected: FAIL because the service is missing.

- [ ] **Step 3: Implement the run service**

Create the directory tree, persist `task.json`, and return a structured run summary.

- [ ] **Step 4: Re-run the test**

Run: `pytest backend/tests/test_run_service.py -q`
Expected: PASS.

### Task 8: Implement the workflow draft and confirmation flow

**Files:**
- Create: `backend/app/services/workflow.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_workflow_api.py`

- [ ] **Step 1: Write failing API tests**

Cover:
- `POST /api/tasks`
- `POST /api/runs/{run_id}/confirm`
- `GET /api/runs/{run_id}`

- [ ] **Step 2: Run the tests**

Run: `pytest backend/tests/test_workflow_api.py -q`
Expected: FAIL because the endpoints do not exist yet.

- [ ] **Step 3: Implement the endpoints**

When a task is submitted:
- persist request metadata
- retrieve candidate cases
- generate a workflow draft
- save `candidate_cases.json`, `selected_case.json`, and `workflow_draft.md`

When confirmed:
- mark the run as confirmed
- trigger the simulated execution pipeline

- [ ] **Step 4: Re-run the tests**

Run: `pytest backend/tests/test_workflow_api.py -q`
Expected: PASS.

### Task 9: Implement the mock execution pipeline

**Files:**
- Create: `backend/app/services/executor.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_executor.py`

- [ ] **Step 1: Write a failing executor test**

Assert that a confirmed run eventually creates:
- `execution/logs/run.log`
- `postprocess/images/*.svg`
- `postprocess/tables/drag.csv`
- `postprocess/result.json`
- `report/final_report.md`
- `report/artifact_manifest.json`

- [ ] **Step 2: Run the executor test**

Run: `pytest backend/tests/test_executor.py -q`
Expected: FAIL because the executor does not exist yet.

- [ ] **Step 3: Implement the executor**

Use a background task or worker thread to:
- progress stage-by-stage
- append timeline events
- write realistic mock logs and artifacts
- update status from `draft` -> `awaiting_confirmation` -> `running` -> `completed`

- [ ] **Step 4: Re-run the executor test**

Run: `pytest backend/tests/test_executor.py -q`
Expected: PASS.

## Chunk 4: Frontend Demo

### Task 10: Scaffold the React app

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Add the frontend shell**

Create a Vite React app with a single-page layout and typed API helpers.

- [ ] **Step 2: Add the visual system**

Create a purposeful, oceanic visual language with CSS variables and a clear information hierarchy for workflow transparency.

### Task 11: Implement task submission and retrieval UI

**Files:**
- Create: `frontend/src/components/TaskForm.tsx`
- Create: `frontend/src/components/CandidateCases.tsx`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/styles.css`

- [ ] **Step 1: Write the UI for task input**

Support task description, task type, geometry family hint, operating notes, and one uploaded file.

- [ ] **Step 2: Render the candidate case list**

Show candidate cases, reasoning, recommended outputs, and selected workflow summary.

### Task 12: Implement confirmation, timeline, and artifact panels

**Files:**
- Create: `frontend/src/components/WorkflowDraft.tsx`
- Create: `frontend/src/components/RunTimeline.tsx`
- Create: `frontend/src/components/ArtifactsPanel.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add the confirmation flow**

Render the assumptions, recommended tools, required artifacts, and confirm button.

- [ ] **Step 2: Add the run-progress UI**

Poll the run endpoint and show live stage transitions, logs, generated artifacts, and final report text.

## Chunk 5: Delivery and Verification

### Task 13: Add start scripts and README

**Files:**
- Create: `README.md`
- Create: `start-demo.ps1`

- [ ] **Step 1: Document setup**

Explain how to install backend and frontend dependencies and how to launch the demo.

- [ ] **Step 2: Add a helper script**

Start the FastAPI server and Vite dev server from one command or clearly print the two commands to run.

### Task 14: Verify the demo

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run backend tests**

Run: `pytest backend/tests -q`
Expected: all tests pass.

- [ ] **Step 2: Build the frontend**

Run: `npm run build --prefix frontend`
Expected: frontend build succeeds with no TypeScript errors.

- [ ] **Step 3: Smoke test the API**

Run: start the backend and call `GET /api/health`.
Expected: `{"status":"ok"}`.

- [ ] **Step 4: Smoke test a full run**

Run: submit one demo request, confirm it, and verify the run directory contains request, retrieval, execution, postprocess, and report artifacts.
Expected: the end-to-end demo flow completes successfully.
