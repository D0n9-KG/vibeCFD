# Submarine Demo Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the current MVP one layer closer to the documented architecture by introducing LangGraph orchestration, pluggable execution engines, and Docker Compose deployment scaffolding.

**Architecture:** Keep the existing FastAPI + React MVP intact at the API and UI level, but replace the ad-hoc prepare/execute wiring with a LangGraph-backed orchestrator. Split execution into an engine interface with `mock` and `openfoam` implementations, then package frontend and backend with Dockerfiles and a shared-volume `docker-compose.yml`.

**Tech Stack:** FastAPI, Pydantic, LangGraph, React, Vite, Docker Compose

---

## Chunk 1: Orchestration Tests

### Task 1: Add failing tests for the engine factory

**Files:**
- Create: `backend/tests/test_engine_factory.py`
- Create: `backend/app/execution/__init__.py`

- [ ] **Step 1: Write the failing tests**

Cover:
- `mock` engine selection
- `openfoam` engine selection
- unsupported engine error

- [ ] **Step 2: Run the targeted tests**

Run: `python -m pytest tests/test_engine_factory.py -q`
Expected: FAIL because the factory module does not exist yet.

### Task 2: Add failing tests for the LangGraph orchestrator

**Files:**
- Create: `backend/tests/test_orchestrator.py`
- Create: `backend/app/orchestration/__init__.py`

- [ ] **Step 1: Write the failing tests**

Cover:
- `prepare_run` reaches `awaiting_confirmation`
- `execute_run` reaches `completed` with mock engine
- timeline and required artifacts are still present

- [ ] **Step 2: Run the targeted tests**

Run: `python -m pytest tests/test_orchestrator.py -q`
Expected: FAIL because the orchestrator module does not exist yet.

## Chunk 2: Engine Abstraction

### Task 3: Implement the execution engine protocol and factory

**Files:**
- Create: `backend/app/execution/base.py`
- Create: `backend/app/execution/factory.py`
- Create: `backend/app/execution/mock_engine.py`
- Create: `backend/app/execution/openfoam_engine.py`
- Modify: `backend/app/config.py`

- [ ] **Step 1: Implement the minimal protocol and factory**

Return an engine instance based on settings.

- [ ] **Step 2: Re-run factory tests**

Run: `python -m pytest tests/test_engine_factory.py -q`
Expected: PASS.

### Task 4: Move existing mock execution into the new engine package

**Files:**
- Modify: `backend/app/execution/mock_engine.py`
- Modify: `backend/app/services/executor.py`

- [ ] **Step 1: Port the current mock implementation**

Keep the current artifact set and timeline behavior.

- [ ] **Step 2: Re-run existing executor tests**

Run: `python -m pytest tests/test_executor.py -q`
Expected: PASS.

### Task 5: Add the OpenFOAM adapter skeleton

**Files:**
- Modify: `backend/app/execution/openfoam_engine.py`
- Create: `backend/app/execution/openfoam_entrypoint.py`

- [ ] **Step 1: Implement a real adapter boundary**

It should:
- write an execution request manifest
- emit OpenFOAM-intent logs
- fail clearly when a real solver command/container is not configured

- [ ] **Step 2: Keep the adapter behind configuration**

No existing path should break when `mock` remains the default.

## Chunk 3: LangGraph Integration

### Task 6: Implement the LangGraph orchestration layer

**Files:**
- Create: `backend/app/orchestration/graph.py`
- Create: `backend/app/orchestration/service.py`
- Modify: `backend/app/requirements.txt`

- [ ] **Step 1: Add `langgraph` to backend requirements**

- [ ] **Step 2: Implement the graph**

Support two entry modes:
- `prepare`
- `execute`

Use nodes with clear responsibility:
- load run
- retrieve cases
- build workflow
- persist retrieval artifacts
- execute engine

- [ ] **Step 3: Re-run orchestrator tests**

Run: `python -m pytest tests/test_orchestrator.py -q`
Expected: PASS.

### Task 7: Wire the API to the new orchestrator

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_workflow_api.py`

- [ ] **Step 1: Update the app state initialization**

Replace direct workflow/executor wiring with:
- case library
- run service
- engine factory
- LangGraph orchestrator

- [ ] **Step 2: Update the API paths**

`POST /api/tasks` should call orchestrator `prepare`.

`POST /api/runs/{run_id}/confirm` should call orchestrator `execute`.

- [ ] **Step 3: Re-run workflow API tests**

Run: `python -m pytest tests/test_workflow_api.py -q`
Expected: PASS.

## Chunk 4: Docker and Delivery

### Task 8: Add Docker packaging

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `.dockerignore`

- [ ] **Step 1: Add backend container definition**

Expose FastAPI on `8010`.

- [ ] **Step 2: Add frontend container definition**

Expose Vite dev server or preview server in a compose-friendly way.

- [ ] **Step 3: Add shared volumes**

Mount:
- `runs/`
- `uploads/`
- `data/`

- [ ] **Step 4: Add placeholder OpenFOAM service**

Even if not run by default, define the service boundary and shared working directory.

### Task 9: Update documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document the new architecture layer**

Explain:
- LangGraph role
- engine selection
- Docker Compose services

- [ ] **Step 2: Document env vars**

Include at least:
- `SUBMARINE_EXECUTION_ENGINE`
- `SUBMARINE_EXECUTION_DELAY`
- any OpenFOAM adapter command/container variable you introduce

## Chunk 5: Verification

### Task 10: Verify the backend and frontend still work

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run backend tests**

Run: `python -m pytest tests -q`
Expected: all tests pass.

- [ ] **Step 2: Build the frontend**

Run: `npm run build`
Expected: build succeeds.

- [ ] **Step 3: Smoke test the API with mock engine**

Run: start backend with `SUBMARINE_EXECUTION_ENGINE=mock` and submit a task.
Expected: a run completes and writes the documented artifacts.

- [ ] **Step 4: Validate Docker Compose config**

Run: `docker compose config`
Expected: compose file resolves without syntax errors.
