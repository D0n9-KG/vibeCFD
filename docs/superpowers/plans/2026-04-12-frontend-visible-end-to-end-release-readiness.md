# Frontend-Visible End-To-End Release Readiness Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then choose the execution skill that fits the work: use superpowers:subagent-driven-development when delegation benefits outweigh the round-trip, or superpowers:executing-plans when the work is better kept local. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the plan controls below, especially reuse, continuity, artifact lifecycle, validation/review cadence, and any research-overlay constraints.

**Goal:** Make the product honestly usable from a frontend-only user perspective by closing the submarine downstream CFD chain and proving Skill Studio publish-to-agent binding end to end.

**Architecture:** Keep the existing `main` workspace and the current local stack, but treat the browser UI as the only acceptable operator surface. Reuse the already-implemented downstream submarine backend capabilities, repair the empty-response recovery path that currently causes silent stalls, add explicit user-visible execution/report actions in the submarine workbench, then run full browser-driven verification for submarine and Skill Studio before regenerating any guide or screenshots.

**Tech Stack:** Next.js 16 frontend, TypeScript workbench contracts, FastAPI gateway, DeerFlow/LangGraph runtime, OpenAI-compatible CLI provider recovery logic, browser-driven end-to-end verification, local artifact-backed thread flows

**Prior Art Survey:** none needed - this is a project-local release-hardening pass on the active mainline

**Reuse Strategy:** adapt existing project

**Session Status File:** `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`

**Context Summary:** `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

**Primary Context Files:** `docs/superpowers/plans/2026-04-12-frontend-visible-end-to-end-release-readiness.md`; `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`; `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`; `backend/packages/harness/deerflow/models/openai_cli_provider.py`; `backend/tests/test_cli_auth_providers.py`; `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`; `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`; `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`; `backend/packages/harness/deerflow/domain/submarine/postprocess.py`; `backend/packages/harness/deerflow/domain/submarine/reporting.py`; `frontend/src/app/workspace/submarine/[thread_id]/page.tsx`; `frontend/src/components/workspace/submarine-workbench/index.tsx`; `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx`; `frontend/src/components/workspace/submarine-confirmation-actions.ts`; `frontend/src/app/workspace/skill-studio/[thread_id]/page.tsx`; `frontend/src/components/workspace/skill-studio-workbench/index.tsx`; `backend/app/gateway/routers/skills.py`; `backend/packages/harness/deerflow/agents/middlewares/skill_runtime_snapshot_middleware.py`; `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`

**Artifact Lifecycle:** Keep this plan/status/summary chain as the active continuity record. Keep durable backend/frontend fixes and focused regression tests that close the real release gaps. Keep the external STL fixture at `C:\Users\D0n9\Desktop\suboff_solid.stl` as the manual submarine geometry input. Mark the previous “release-ready” screenshots, user-guide drafts, and optimistic completion statements as stale until the new verification sweep is complete; regenerate user docs and screenshots only after the product truly reaches the browser-visible acceptance bar. Delete one-off probes, scratch screenshots, and temporary threads once the same evidence is preserved in tests or durable docs.

**Workspace Strategy:** current workspace

**Validation Strategy:** mixed

**Review Cadence:** each milestone

**Checkpoint Strategy:** milestone commits

**Research Overlay:** disabled

**Research Mainline:** none

**Non-Negotiables:** none

**Forbidden Regressions:** hidden backend-only actions, silent empty-response stalls after the submarine design brief, release claims that stop at upload plus preliminary planning while compute/report/publish remain unverified

**Method Fidelity Checks:** every meaningful user input and action must be visible in the frontend; the submarine path must reach real execution, post-process artifacts, and final report output; Skill Studio must show create, validate, dry-run, publish, and evidence that published skills are available to runtime agents

**Scale Gate:** none

**Decision Log:** none - record durable decisions in the session status file

**Research Findings:** none

**Uncertainty Hotspots:** whether downstream solver/report stalls are fully explained by the current empty-response recovery gap or whether additional runtime/prompting issues remain; whether submarine frontend surfaces already have enough hooks to expose explicit execution/report actions cleanly; whether Skill Studio publish is fully usable but insufficiently proven, or whether a user-visible binding affordance is still missing

**Replan Triggers:** downstream submarine execution succeeds only through hidden backend intervention instead of visible UI actions; full submarine run reveals a second root cause outside the known recovery gap; Skill Studio publish completes but published skills still cannot be shown in runtime snapshots or thread behavior without a broader product change

---

### Task 1: Reopen The Durable Handoff Around The Real Acceptance Bar

**Type:** Exploratory

**Files:**
- Modify: `docs/superpowers/plans/2026-04-12-frontend-visible-end-to-end-release-readiness.md`
- Modify: `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`
- Modify: `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

**Goal:** Replace the stale “completed / release-ready” narrative with the verified current state so every later session resumes from the real blockers.

**Collect Evidence:**
- current branch and working tree state
- currently running local stack ports
- verified submarine downstream and Skill Studio gaps recovered from the existing code and repro record

**Stop and Replan If:**
- the existing durable artifacts point at a different active plan family
- repo state contradicts the known handoff strongly enough that the current release-readiness slug is no longer the right continuity chain

**Checkpoint If:**
- the revised plan/status/summary all agree on the reopened scope and next step

- [x] **Step 1: Recover the active durable artifacts and git state**
- [x] **Step 2: Record the invalidated assumptions and reopened scope**
- [x] **Step 3: Update the next recommended step to the real blocker-driven sequence**

### Task 2: Add Regression Tests For Downstream Empty-Response Recovery

**Type:** Deterministic

**Files:**
- Modify: `backend/tests/test_cli_auth_providers.py`
- Test: `backend/tests/test_cli_auth_providers.py`

**Goal:** Turn the confirmed submarine downstream stall into focused failing tests before changing provider recovery logic.

- [ ] **Step 1: Add a failing test for solver-dispatch recovery after a ready design-brief state**

```python
def test_openai_cli_provider_recovers_solver_dispatch_after_ready_design_brief(...):
    ...
    assert result.generations[0].message.tool_calls == [
        {
            "name": "submarine_solver_dispatch",
            ...
        }
    ]
```

- [ ] **Step 2: Run it to verify RED**

Run: `uv run --project backend pytest backend/tests/test_cli_auth_providers.py -k solver_dispatch_recover -v`
Expected: FAIL because the provider currently falls back to generic text instead of dispatching the downstream tool

- [ ] **Step 3: Add a failing test for result-report recovery after solver artifacts exist**

```python
def test_openai_cli_provider_recovers_result_report_after_solver_dispatch(...):
    ...
    assert result.generations[0].message.tool_calls == [
        {
            "name": "submarine_result_report",
            ...
        }
    ]
```

- [ ] **Step 4: Run it to verify RED**

Run: `uv run --project backend pytest backend/tests/test_cli_auth_providers.py -k result_report_recover -v`
Expected: FAIL because the provider currently emits the generic fallback instead of continuing the chain

### Task 3: Repair Provider Recovery For Solver Dispatch And Final Reporting

**Type:** Deterministic

**Files:**
- Modify: `backend/packages/harness/deerflow/models/openai_cli_provider.py`
- Modify: `backend/tests/test_cli_auth_providers.py`
- Test: `backend/tests/test_cli_auth_providers.py`

**Goal:** Extend empty-response recovery beyond geometry/design-brief so downstream submarine execution and reporting continue automatically when the model returns an empty turn.

- [ ] **Step 1: Implement minimal solver-dispatch recovery**

```python
def _build_submarine_solver_dispatch_recovery_tool_calls(...):
    ...
```

- [ ] **Step 2: Implement minimal result-report recovery and visible summary reuse**

```python
def _build_submarine_result_report_recovery_tool_calls(...):
    ...
```

- [ ] **Step 3: Run the focused backend regression suite**

Run: `uv run --project backend pytest backend/tests/test_cli_auth_providers.py -v`
Expected: PASS with the new downstream recovery cases green and no regression in existing geometry/design-brief recovery cases

- [ ] **Step 4: Run the neighboring submarine backend suite**

Run: `uv run --project backend pytest backend/tests/test_submarine_design_brief_tool.py backend/tests/test_submarine_geometry_check_tool.py -v`
Expected: PASS

### Task 4: Expose Explicit Frontend Actions For Execution And Reporting

**Type:** Deterministic

**Files:**
- Modify: `frontend/src/app/workspace/submarine/[thread_id]/page.tsx`
- Modify: `frontend/src/components/workspace/submarine-workbench/index.tsx`
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx`
- Modify: `frontend/src/components/workspace/submarine-confirmation-actions.ts`
- Test: `frontend/src/components/workspace/submarine-workbench/index.contract.test.ts`
- Test: `frontend/src/components/workspace/submarine-workbench/*.test.ts*`

**Goal:** Give the user explicit, visible UI actions to continue from design brief to execution and from execution to reporting, and ensure those actions produce visible chat messages rather than hidden backend calls.

- [ ] **Step 1: Add a failing frontend test or contract assertion for visible execution/report actions**
- [ ] **Step 2: Run it to verify RED**

Run: `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/components/workspace/submarine-workbench/index.contract.test.ts"`
Expected: FAIL because the current workbench does not yet expose the needed visible action contract

- [ ] **Step 3: Implement the smallest UI slice that submits visible chat-side execution and report requests**
- [ ] **Step 4: Re-run the focused frontend tests**

Run: `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/components/workspace/submarine-workbench/submarine-session-model.test.ts" "src/components/workspace/submarine-workbench/submarine-negotiation-panel.model.test.ts" "src/components/workspace/submarine-workbench/index.contract.test.ts"`
Expected: PASS

### Task 5: Prove The Full Submarine Browser Journey Through Compute, Postprocess, And Report

**Type:** Exploratory

**Files:**
- Modify: `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`
- Modify: `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

**Goal:** Re-run the submarine user flow strictly from the visible frontend and verify that it reaches real solver execution, post-processing artifacts, and final report output using `C:\Users\D0n9\Desktop\suboff_solid.stl`.

**Collect Evidence:**
- visible upload and confirmation history
- visible execution trigger from the workbench
- actual solver-dispatch, postprocess, and reporting artifacts in thread state
- visible completion signals in chat and workbench

**Stop and Replan If:**
- the flow still needs hidden operator intervention
- solver dispatch succeeds but post-processing or reporting fails for a different root cause

**Checkpoint If:**
- the submarine chain is genuinely browser-complete end to end

- [ ] **Step 1: Start or reuse a submarine thread from the frontend**
- [ ] **Step 2: Upload `C:\Users\D0n9\Desktop\suboff_solid.stl` and confirm the requested inputs in visible chat**
- [ ] **Step 3: Trigger visible execution and wait for solver/postprocess completion**
- [ ] **Step 4: Trigger visible final reporting and confirm the report artifacts are present**
- [ ] **Step 5: Record the verified thread id, artifacts, and any remaining defects in the status and summary files**

### Task 6: Prove Skill Studio Create-To-Publish And Runtime Binding

**Type:** Exploratory

**Files:**
- Modify: `frontend/src/app/workspace/skill-studio/[thread_id]/page.tsx`
- Modify: `frontend/src/components/workspace/skill-studio-workbench/index.tsx`
- Modify: `backend/app/gateway/routers/skills.py`
- Modify: `backend/packages/harness/deerflow/agents/middlewares/skill_runtime_snapshot_middleware.py`
- Modify: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- Modify: `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`
- Modify: `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

**Goal:** Demonstrate that Skill Studio can create, validate, dry-run, publish, and make a published skill available to agents in a user-visible way; add the smallest affordance only if the proof is currently missing.

**Collect Evidence:**
- visible lifecycle artifacts in the Skill Studio thread
- publish success state from the visible workbench or gateway lifecycle
- evidence that a published skill appears in runtime skill snapshot or affects a later agent thread

**Stop and Replan If:**
- publish lifecycle is green but runtime binding requires a deeper architecture change
- the missing proof is not an affordance bug but a product-definition gap

**Checkpoint If:**
- a normal user can understand that a published skill was actually made available to agents

- [ ] **Step 1: Re-run the existing strong Skill Studio thread from the frontend**
- [ ] **Step 2: Verify create, validate, dry-run, publish evidence from the visible UI**
- [ ] **Step 3: Verify or add the minimal user-visible proof of runtime binding**
- [ ] **Step 4: Record the evidence and any remaining limitations in the status and summary files**

### Task 7: Only Then Refresh User Docs, Screenshots, And Release Claim

**Type:** Deterministic

**Files:**
- Modify: `docs/user-guide/**`
- Modify: `test-results/**`
- Modify: `docs/superpowers/session-status/2026-04-12-frontend-visible-end-to-end-release-readiness-status.md`
- Modify: `docs/superpowers/context-summaries/2026-04-12-frontend-visible-end-to-end-release-readiness-summary.md`

**Goal:** Regenerate the user-facing guide and screenshot set only after submarine and Skill Studio both satisfy the browser-visible acceptance bar.

- [ ] **Step 1: Capture a clean screenshot set from the real release-usable product**
- [ ] **Step 2: Rewrite the user guide around the verified flows instead of the partial ones**
- [ ] **Step 3: Run the final verification sweep**

Run:
  - `uv run --project backend pytest backend/tests/test_cli_auth_providers.py backend/tests/test_submarine_design_brief_tool.py backend/tests/test_submarine_geometry_check_tool.py -v`
  - `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/components/workspace/submarine-workbench/submarine-session-model.test.ts" "src/components/workspace/submarine-workbench/submarine-negotiation-panel.model.test.ts" "src/components/workspace/submarine-workbench/index.contract.test.ts"`
  - `corepack pnpm --dir frontend typecheck`

Expected: the touched regression suites and frontend typecheck are green before any release-ready claim is written

- [ ] **Step 4: Request reviewer pass for the milestone and update the final status honestly**
