# Claude Executor Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the next locally-implementable slice toward the target architecture by adding a structured `claude-executor` protocol, a stub executor service, and backend integration that can dispatch execution requests through that boundary.

**Architecture:** Keep the existing Web/API and LangGraph interfaces stable while introducing a new execution protocol layer between the backend orchestrator and an externalized executor service. Implement a local stub `claude-executor` FastAPI app so the repository can exercise the full request/response path without requiring real Claude credentials yet.

**Tech Stack:** FastAPI, Pydantic, HTTPX, LangGraph, pytest, Docker Compose

---

## Chunk 1: Protocol And Documentation

### Task 1: Write the external dependency handoff document

**Files:**
- Create: `docs/2026-03-20-external-dependencies-checklist.md`

- [ ] **Step 1: Write the document**

Capture:

- external resources required to reach the real target architecture
- exact inputs needed for Claude access, OpenFOAM runtime, MCP tools, benchmark assets, acceptance criteria, and deployment
- why each missing input blocks progress

- [ ] **Step 2: Review the document for completeness**

Check that the document answers:

- what is missing
- who should provide it
- what format it should take
- what happens if it is missing

## Chunk 2: TDD For Claude Executor Boundary

### Task 2: Add failing tests for the new execution engine and stub executor

**Files:**
- Modify: `backend/tests/test_engine_factory.py`
- Create: `backend/tests/test_claude_executor_app.py`
- Create: `backend/tests/test_claude_executor_engine.py`

- [ ] **Step 1: Add a failing factory test for `claude_executor`**

```python
def test_factory_returns_claude_executor_engine(...):
    monkeypatch.setenv("SUBMARINE_EXECUTION_ENGINE", "claude_executor")
    engine = create_execution_engine(RunStore())
    assert isinstance(engine, ClaudeExecutorEngine)
```

- [ ] **Step 2: Run the targeted factory test and verify it fails**

Run: `python -m pytest tests/test_engine_factory.py -q`
Expected: FAIL because `claude_executor` is unsupported.

- [ ] **Step 3: Add a failing executor service test**

```python
def test_claude_executor_stub_returns_structured_completion(...):
    response = client.post("/api/execute", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
```

- [ ] **Step 4: Run the stub service test and verify it fails**

Run: `python -m pytest tests/test_claude_executor_app.py -q`
Expected: FAIL because the service does not exist.

- [ ] **Step 5: Add a failing engine integration test**

```python
def test_claude_executor_engine_builds_request_and_completes_run(...):
    completed = engine.run_pipeline(run.run_id)
    assert completed.status.value == "completed"
```

- [ ] **Step 6: Run the engine test and verify it fails**

Run: `python -m pytest tests/test_claude_executor_engine.py -q`
Expected: FAIL because the engine does not exist.

## Chunk 3: Protocol And Stub Service

### Task 3: Implement the execution request/response schema

**Files:**
- Create: `backend/app/executor_protocol.py`

- [ ] **Step 1: Add protocol models**

Define:

- `ExecutorTaskContext`
- `ExecutorTaskRequest`
- `ExecutorTimelineEvent`
- `ExecutorTaskResult`

- [ ] **Step 2: Run protocol-adjacent tests**

Run: `python -m pytest tests/test_claude_executor_app.py -q`
Expected: still FAIL until the app is added.

### Task 4: Implement a local stub `claude-executor` service

**Files:**
- Create: `backend/app/executor_stub.py`
- Create: `backend/app/claude_executor_main.py`

- [ ] **Step 1: Implement the stub service**

The service should:

- accept a structured execution request
- write request/response manifests into the run directory
- generate deterministic timeline events
- write demo artifacts needed by the UI
- return a structured completion payload

- [ ] **Step 2: Run the stub service tests**

Run: `python -m pytest tests/test_claude_executor_app.py -q`
Expected: PASS

## Chunk 4: Backend Integration

### Task 5: Add a `ClaudeExecutorEngine` and client

**Files:**
- Create: `backend/app/execution/claude_executor_engine.py`
- Modify: `backend/app/execution/factory.py`
- Modify: `backend/app/config.py`

- [ ] **Step 1: Implement the client and engine**

The engine should:

- build a request from the current run
- write a request manifest to disk
- submit the request to the stub executor service
- map the returned result into store updates
- fail gracefully if the service is unavailable

- [ ] **Step 2: Run the engine tests**

Run: `python -m pytest tests/test_engine_factory.py tests/test_claude_executor_engine.py -q`
Expected: PASS

### Task 6: Wire the service into Compose and docs

**Files:**
- Modify: `docker-compose.yml`
- Modify: `README.md`

- [ ] **Step 1: Add `claude-executor` service to Compose**

Expose a local service that runs `uvicorn app.claude_executor_main:app`.

- [ ] **Step 2: Document the new engine option**

Add:

- `SUBMARINE_EXECUTION_ENGINE=claude_executor`
- `SUBMARINE_EXECUTOR_BASE_URL`
- service startup guidance
- explicit note that this is still a stub until real Claude access is provided

## Chunk 5: Verification

### Task 7: Run verification

**Files:**
- Test: `backend/tests/test_engine_factory.py`
- Test: `backend/tests/test_claude_executor_app.py`
- Test: `backend/tests/test_claude_executor_engine.py`
- Test: `backend/tests/test_orchestrator.py`
- Test: `backend/tests/test_workflow_api.py`

- [ ] **Step 1: Run targeted backend tests**

Run: `python -m pytest tests/test_engine_factory.py tests/test_claude_executor_app.py tests/test_claude_executor_engine.py -q`
Expected: PASS

- [ ] **Step 2: Run the full backend suite**

Run: `python -m pytest tests -q`
Expected: PASS

- [ ] **Step 3: Validate documentation references**

Run: inspect the updated `README.md` and Compose file manually.
Expected: the new executor mode and service are described consistently.
