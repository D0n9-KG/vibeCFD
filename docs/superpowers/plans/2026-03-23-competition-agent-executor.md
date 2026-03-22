# Competition Agent Executor Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current stub executor with a production-like, competition-ready project agent executor that performs real model calls, runs deterministic local skills, and generates rich run artifacts from uploaded submarine geometry.

**Architecture:** Keep the existing frontend, backend, and dispatcher boundaries, but upgrade the executor service into a provider-driven agent runtime. The runtime will call a configurable OpenAI-compatible model, orchestrate a narrow skill envelope, generate structured artifacts and reports, and preserve the current `ExecutorTaskRequest -> ExecutorTaskResult` contract so the UI and store continue to work.

**Tech Stack:** FastAPI, Pydantic, httpx, LangGraph-adjacent backend orchestration, SVG/JSON/CSV artifact generation, Docker Compose, React/Vite frontend.

---

## Chunk 1: Repository Hygiene And Runtime Configuration

### Task 1: Lock In Version-Control Baseline

**Files:**
- Create: `.gitignore`
- Modify: none
- Test: `git status --short --ignored`

- [x] **Step 1: Add a repository-level `.gitignore` that ignores generated outputs and local caches**
- [x] **Step 2: Initialize git on `main` and commit the current baseline**
- [x] **Step 3: Create feature branch `codex/competition-agent-executor`**

### Task 2: Add Provider-Oriented Runtime Settings

**Files:**
- Modify: `backend/app/config.py`
- Test: `backend/tests/test_models.py` or new config-focused test

- [ ] **Step 1: Add settings for agent provider base URL, model name, API key, timeout, and user-facing executor name**
- [ ] **Step 2: Keep backward compatibility for existing executor settings used by the backend**
- [ ] **Step 3: Write tests or assertions covering default and env-driven configuration**

## Chunk 2: Agent Runtime And Skills

### Task 3: Introduce Structured Agent Runtime Models

**Files:**
- Modify: `backend/app/executor_protocol.py`
- Create: `backend/app/agent_runtime/models.py`
- Test: `backend/tests/test_claude_executor_app.py`

- [ ] **Step 1: Extend executor request context with operating notes, selected case summary, and richer skill metadata**
- [ ] **Step 2: Define structured model-output schema for agent planning and report synthesis**
- [ ] **Step 3: Update tests to cover the richer request/response contract**

### Task 4: Build OpenAI-Compatible Model Client

**Files:**
- Create: `backend/app/agent_runtime/provider.py`
- Create: `backend/app/agent_runtime/json_utils.py`
- Test: `backend/tests/test_agent_provider.py`

- [ ] **Step 1: Write failing tests for JSON extraction and provider request assembly**
- [ ] **Step 2: Implement an httpx-based provider for compatible chat-completions APIs**
- [ ] **Step 3: Add robust JSON extraction and useful error messages when the model response is malformed**
- [ ] **Step 4: Run the new provider tests**

### Task 5: Build Project Skills For Geometry, Simulation, And Reporting

**Files:**
- Create: `backend/app/agent_runtime/geometry.py`
- Create: `backend/app/agent_runtime/skills.py`
- Create: `backend/app/agent_runtime/artifacts.py`
- Test: `backend/tests/test_agent_skills.py`

- [ ] **Step 1: Write tests for Parasolid `.x_t` header parsing and geometry summary generation**
- [ ] **Step 2: Implement `.x_t` parsing, STL summary support, and geometry artifact generation**
- [ ] **Step 3: Implement deterministic solver/postprocess/report helper functions that write realistic competition-ready artifacts**
- [ ] **Step 4: Run the skill tests**

### Task 6: Replace Stub Executor With Real Agent Flow

**Files:**
- Modify: `backend/app/claude_executor_main.py`
- Modify: `backend/app/executor_stub.py`
- Create: `backend/app/agent_runtime/service.py`
- Test: `backend/tests/test_claude_executor_app.py`

- [ ] **Step 1: Write failing executor API tests for the new real-agent execution path**
- [ ] **Step 2: Implement service orchestration: plan with model, run skills, synthesize final report, persist response files**
- [ ] **Step 3: Keep a deterministic non-network test seam by injecting a fake provider into the service**
- [ ] **Step 4: Run executor API tests**

## Chunk 3: Backend Integration And Demo Experience

### Task 7: Enrich Backend Engine Integration

**Files:**
- Modify: `backend/app/execution/claude_executor_engine.py`
- Modify: `backend/app/execution/factory.py`
- Modify: `backend/app/models.py`
- Test: `backend/tests/test_claude_executor_engine.py`

- [ ] **Step 1: Propagate richer context from backend runs into executor requests**
- [ ] **Step 2: Update attempt/timeline handling for the new executor summary and failure reasons**
- [ ] **Step 3: Run engine integration tests**

### Task 8: Refresh Workflow And Artifact Presentation Inputs

**Files:**
- Modify: `backend/app/services/workflow.py`
- Modify: `frontend/src/lib/display.ts`
- Modify: `frontend/src/components/GraphicsWorkspace.tsx`
- Modify: `frontend/src/components/ArtifactsPanel.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Clean up workflow copy and required artifacts so the UI receives richer, competition-grade labels**
- [ ] **Step 2: Ensure the workspace and artifact panels show the new geometry/result/report outputs cleanly**
- [ ] **Step 3: Run frontend tests and build**

## Chunk 4: Docker And End-To-End Validation

### Task 9: Make Compose Default To The New Executor Path

**Files:**
- Modify: `docker-compose.yml`
- Modify: `README.md`
- Modify: `docs/2026-03-20-external-dependencies-checklist.md`
- Test: `docker compose config`

- [ ] **Step 1: Set compose defaults and docs for the new agent executor runtime**
- [ ] **Step 2: Document required environment variables and competition-demo startup flow**
- [ ] **Step 3: Run `docker compose config`**

### Task 10: Add A Repeatable Local Demo Run

**Files:**
- Modify: `start-demo.ps1`
- Create: `scripts/run-desktop-demo.ps1`
- Test: manual end-to-end smoke using `C:\Users\D0n9\Desktop\suboff_solid.x_t`

- [ ] **Step 1: Create a script that can submit the desktop test geometry and poll until completion**
- [ ] **Step 2: Verify that the run writes full artifacts and a final report**
- [ ] **Step 3: Capture the exact commands and expected output locations in the README**
