# VibeCFD Lead-Agent-First Refactor Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the current submarine CFD product from a workflow-first experience into a lead-agent-first Vibe CFD system where `Codex` or `Claude Code` negotiates plans with the user and uses skills, sub-agents, tools, and sandboxed execution dynamically.

**Architecture:** Keep DeerFlow's lead agent, sub-agent, skill, sandbox, and artifact model, but remove mandatory linear submarine workflow enforcement from prompts, skills, and UI. Retain hard guardrails for geometry integrity, risky execution, server-safe sandbox boundaries, and scientific-claim controls.

**Tech Stack:** Python 3.12, DeerFlow harness, LangGraph, FastAPI, Next.js 16, React 19, TypeScript, OpenFOAM sandbox, pytest, ESLint, TypeScript compiler

---

## Scope Split

This refactor spans multiple independent subsystems. Implement it as four subprojects in this order:

1. Prompt and skill orchestration refactor
2. Backend state and tool contract refactor
3. Frontend workbench reframing
4. Safety and evidence hardening

Do not try to implement all four in one branch.

## File Structure Map

### Prompt and Skill Orchestration

- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
  Current submarine protocol is still stage-first and must become guidance-first.
- `skills/public/submarine-orchestrator/SKILL.md`
  Must stop dictating fixed order and instead teach judgment and decomposition rules.
- `skills/public/submarine-geometry-check/SKILL.md`
  Should guide when geometry inspection is useful, not imply it is always the next stage.
- `skills/public/submarine-solver-dispatch/SKILL.md`
  Should describe execution-readiness and solver safety conditions.
- `skills/public/submarine-report/SKILL.md`
  Should emphasize artifact-backed reporting and claim limits.

### Backend State and Tool Contracts

- `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
  Must become a planning-memory checkpoint tool rather than a mandatory stage gate.
- `backend/packages/harness/deerflow/domain/submarine/design_brief.py`
  Must emit dynamic plan snapshots instead of stage-driven next-step assumptions.
- `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py`
  Must stop coupling user confirmation to a hard pipeline transition model.
- `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py`
  Must return findings and recommendations without owning the workflow.
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
  Must execute only when the primary agent and guardrails decide, not because a stage machine says so.
- `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`
  Must stay evidence-backed while becoming independent from fixed stage order.
- `backend/packages/harness/deerflow/agents/thread_state.py`
  May need to demote `current_stage` and `next_recommended_stage` from primary control fields.

### Frontend Workbench

- `frontend/src/components/workspace/submarine-workbench-shell.tsx`
  Currently frames the experience as a cockpit with stage tabs.
- `frontend/src/components/workspace/submarine-pipeline.tsx`
  Currently renders stage-first surfaces and should become task/evidence-first.
- `frontend/src/components/workspace/submarine-pipeline-status.ts`
  Encodes workflow-heavy summaries and must shift toward negotiation/evidence messaging.
- `frontend/src/components/workspace/submarine-pipeline-runs.ts`
  Currently derives display stage and user-confirmation states from workflow semantics.
- `frontend/src/components/workspace/submarine-confirmation-actions.ts`
  Must stop sending messages that assume a fixed next step.
- `frontend/src/components/workspace/submarine-task-intelligence-view.ts`
  Must present plan, assumptions, and open questions without stage pressure.
- `frontend/src/components/workspace/submarine-stage-cards.tsx`
  May need to be decomposed or renamed because the stage metaphor is becoming secondary.

### Safety and Evidence Hardening

- `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
  Needs stronger geometry integrity gates.
- `backend/packages/harness/deerflow/domain/submarine/library.py`
  Needs evidence-aware case ranking.
- `domain/submarine/cases/index.json`
  Needs explicit evidence tiers and fewer ambiguous template signals.
- `docker/openfoam-sandbox/README.md`
  Needs to document the server-safe execution model for real deployment.
- `README.md`
  Must stop overselling fixed workflow semantics if the product is repositioned.

## Task 1: Refactor Prompt and Skill Language Away From Fixed Workflow

**Files:**
- Modify: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- Modify: `skills/public/submarine-orchestrator/SKILL.md`
- Modify: `skills/public/submarine-geometry-check/SKILL.md`
- Modify: `skills/public/submarine-solver-dispatch/SKILL.md`
- Modify: `skills/public/submarine-report/SKILL.md`
- Test: `backend/tests/test_lead_agent_prompt_skill_routing.py`
- Test: `backend/tests/test_submarine_subagents.py`

- [ ] **Step 1: Add a regression test that captures the new orchestration stance**

Create or extend tests so they fail if the prompt still requires a universal `design_brief -> geometry -> solver -> report` order for every submarine request.

Run: `.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_lead_agent_prompt_skill_routing.py backend\tests\test_submarine_subagents.py -q`

Expected: at least one assertion should fail before the prompt and skills are updated.

- [ ] **Step 2: Rewrite the submarine prompt section**

Update `backend/packages/harness/deerflow/agents/lead_agent/prompt.py` so the submarine section says:

- the primary agent owns user negotiation
- structured planning snapshots are recommended, not universally mandatory
- geometry, solver, and reporting tools are chosen dynamically
- high-risk actions still require explicit approval and evidence

- [ ] **Step 3: Rewrite submarine skills as guidance playbooks**

Update submarine skill docs so they answer:

- when the skill is relevant
- what risks it helps manage
- what outputs it should produce
- what it should never imply

and remove any wording that hard-codes a global linear stage sequence.

- [ ] **Step 4: Run prompt and sub-agent tests**

Run: `.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_lead_agent_prompt_skill_routing.py backend\tests\test_submarine_subagents.py -q`

Expected: PASS, with prompt language still preserving guardrails and specialist-role guidance.

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/agents/lead_agent/prompt.py skills/public/submarine-orchestrator/SKILL.md skills/public/submarine-geometry-check/SKILL.md skills/public/submarine-solver-dispatch/SKILL.md skills/public/submarine-report/SKILL.md backend/tests/test_lead_agent_prompt_skill_routing.py backend/tests/test_submarine_subagents.py
git commit -m "refactor: make submarine orchestration lead-agent first"
```

## Task 2: Turn Design Brief Into Dynamic Planning Memory

**Files:**
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/design_brief.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py`
- Modify: `backend/packages/harness/deerflow/agents/thread_state.py`
- Test: `backend/tests/test_submarine_design_brief_tool.py`
- Test: `backend/tests/test_submarine_runtime_context.py`

- [ ] **Step 1: Add failing tests for dynamic planning behavior**

Add test cases proving that:

- the design brief can be updated multiple times without forcing a hard stage transition
- `current_stage` and `next_recommended_stage` are advisory only
- confirmation state and approval state remain structured

Run: `.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_submarine_design_brief_tool.py backend\tests\test_submarine_runtime_context.py -q`

Expected: FAIL on assertions that require the new semantics.

- [ ] **Step 2: Redesign design-brief payload semantics**

Update `backend/packages/harness/deerflow/domain/submarine/design_brief.py` so the payload centers on:

- task summary
- assumptions
- open questions
- requested outputs
- selected case
- execution preference
- approval state

and only emits stage hints as optional metadata.

- [ ] **Step 3: Update tool and runtime-context helpers**

Make `submarine_design_brief_tool.py` and `submarine_runtime_context.py` treat the brief as mutable planning memory. Keep explicit confirmations and approvals, but stop assuming confirmation implies a universal next step.

- [ ] **Step 4: Adjust thread-state semantics**

Review `backend/packages/harness/deerflow/agents/thread_state.py` and related runtime snapshots so stage fields no longer function as the main orchestration control plane.

- [ ] **Step 5: Run backend tests**

Run: `.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_submarine_design_brief_tool.py backend\tests\test_submarine_runtime_context.py -q`

Expected: PASS, with structured planning retained and stage coupling reduced.

- [ ] **Step 6: Commit**

```bash
git add backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py backend/packages/harness/deerflow/domain/submarine/design_brief.py backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py backend/packages/harness/deerflow/agents/thread_state.py backend/tests/test_submarine_design_brief_tool.py backend/tests/test_submarine_runtime_context.py
git commit -m "refactor: make submarine design brief a dynamic plan snapshot"
```

## Task 3: Decouple Tools From Mandatory Stage Ownership

**Files:**
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- Test: `backend/tests/test_submarine_geometry_check_tool.py`
- Test: `backend/tests/test_submarine_solver_dispatch_tool.py`
- Test: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Add failing tests for recommendation-based tool outputs**

Write tests so the tools are expected to:

- return findings, readiness, and recommendations
- preserve explicit approval boundaries
- avoid implying that another tool must always run next

Run: `.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_submarine_geometry_check_tool.py backend\tests\test_submarine_solver_dispatch_tool.py backend\tests\test_submarine_result_report_tool.py -q`

Expected: FAIL on at least the new recommendation-oriented assertions.

- [ ] **Step 2: Refactor geometry-check output contracts**

Update geometry-check outputs so they report:

- mesh findings
- scale findings
- execution-readiness
- recommended next actions

without owning the user's journey.

- [ ] **Step 3: Refactor solver-dispatch output contracts**

Update solver-dispatch outputs so they:

- require explicit execution intent
- preserve sandbox and evidence boundaries
- expose whether execution happened, not whether the workflow advanced

- [ ] **Step 4: Refactor result-report outputs**

Update result-report outputs so they remain evidence-backed and scientific-claim-aware, but do not rely on stage-sequence assumptions.

- [ ] **Step 5: Run backend tool tests**

Run: `.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_submarine_geometry_check_tool.py backend\tests\test_submarine_solver_dispatch_tool.py backend\tests\test_submarine_result_report_tool.py -q`

Expected: PASS, with dynamic orchestration preserved and hard execution/reporting guardrails intact.

- [ ] **Step 6: Commit**

```bash
git add backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py backend/packages/harness/deerflow/domain/submarine/contracts.py backend/tests/test_submarine_geometry_check_tool.py backend/tests/test_submarine_solver_dispatch_tool.py backend/tests/test_submarine_result_report_tool.py
git commit -m "refactor: decouple submarine tools from fixed stage ownership"
```

## Task 4: Reframe the Frontend Around Task, Risk, and Evidence

**Files:**
- Modify: `frontend/src/components/workspace/submarine-workbench-shell.tsx`
- Modify: `frontend/src/components/workspace/submarine-pipeline.tsx`
- Modify: `frontend/src/components/workspace/submarine-pipeline-status.ts`
- Modify: `frontend/src/components/workspace/submarine-pipeline-runs.ts`
- Modify: `frontend/src/components/workspace/submarine-confirmation-actions.ts`
- Modify: `frontend/src/components/workspace/submarine-task-intelligence-view.ts`
- Modify: `frontend/src/components/workspace/submarine-stage-cards.tsx`
- Test: `frontend/src/components/workspace/submarine-confirmation-actions.test.ts`
- Test: `frontend/src/components/workspace/submarine-pipeline-runs.test.ts`
- Test: `frontend/src/components/workspace/submarine-pipeline-status.test.ts`
- Test: `frontend/src/components/workspace/submarine-task-intelligence-view.test.ts`
- Verify: frontend ESLint + typecheck

- [ ] **Step 1: Add failing frontend tests for lead-agent-first phrasing**

Update tests so they expect:

- plan/assumption/evidence wording instead of rigid stage wording
- confirmation actions to reinforce plan approval rather than stage progression
- status summaries to describe negotiation, readiness, and evidence posture

Run:

```bash
.\node_modules\.bin\eslint.CMD . --ext .ts,.tsx
.\node_modules\.bin\tsc.CMD --noEmit
```

Expected: current lint/typecheck may still fail until the relevant files are updated.

- [ ] **Step 2: Rewrite workbench framing**

Update `submarine-workbench-shell.tsx` and `submarine-pipeline.tsx` so the UI centers on:

- current objective
- active assumptions
- open risks
- produced evidence
- available next actions

and not on a mandatory stage journey.

- [ ] **Step 3: Rewrite status and confirmation messaging**

Update `submarine-pipeline-status.ts`, `submarine-pipeline-runs.ts`, and `submarine-confirmation-actions.ts` so they preserve approvals and evidence state without forcing a stage machine into the interaction.

- [ ] **Step 4: Simplify task-intelligence and stage-card surfaces**

Update `submarine-task-intelligence-view.ts` and `submarine-stage-cards.tsx` so they support dynamic plans and selective tool use. If the stage-card file becomes too awkward, split it into smaller task/evidence/action panels during this task.

- [ ] **Step 5: Run targeted tests and frontend checks**

Run:

```bash
.\node_modules\.bin\eslint.CMD . --ext .ts,.tsx
.\node_modules\.bin\tsc.CMD --noEmit
```

Expected: PASS, with submarine workbench messaging aligned to lead-agent-first behavior.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/workspace/submarine-workbench-shell.tsx frontend/src/components/workspace/submarine-pipeline.tsx frontend/src/components/workspace/submarine-pipeline-status.ts frontend/src/components/workspace/submarine-pipeline-runs.ts frontend/src/components/workspace/submarine-confirmation-actions.ts frontend/src/components/workspace/submarine-task-intelligence-view.ts frontend/src/components/workspace/submarine-stage-cards.tsx frontend/src/components/workspace/submarine-confirmation-actions.test.ts frontend/src/components/workspace/submarine-pipeline-runs.test.ts frontend/src/components/workspace/submarine-pipeline-status.test.ts frontend/src/components/workspace/submarine-task-intelligence-view.test.ts
git commit -m "refactor: reframe submarine workbench around dynamic plans"
```

## Task 5: Preserve Safety, Sandbox, and Scientific Guardrails

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/library.py`
- Modify: `domain/submarine/cases/index.json`
- Modify: `README.md`
- Modify: `docker/openfoam-sandbox/README.md`
- Test: `backend/tests/test_submarine_domain_assets.py`
- Test: `backend/tests/test_submarine_geometry_check_tool.py`
- Test: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Add failing tests for hard guardrails**

Add test coverage showing that even in a lead-agent-first system:

- invalid geometry still blocks execution
- placeholder-only cases do not masquerade as benchmark-backed confidence
- solver execution remains sandbox-gated

Run: `.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_submarine_domain_assets.py backend\tests\test_submarine_geometry_check_tool.py backend\tests\test_submarine_solver_dispatch_tool.py -q`

Expected: FAIL until evidence and gate semantics are updated.

- [ ] **Step 2: Strengthen geometry and evidence gates**

Update geometry integrity and case provenance semantics so orchestration can be flexible while technical and scientific boundaries remain hard.

- [ ] **Step 3: Update docs to match the new model**

Revise `README.md` and `docker/openfoam-sandbox/README.md` so they describe:

- lead-agent-first orchestration
- sandbox as the execution hard boundary
- skills as guidance modules
- artifacts as reviewable evidence

- [ ] **Step 4: Run backend tests**

Run: `.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_submarine_domain_assets.py backend\tests\test_submarine_geometry_check_tool.py backend\tests\test_submarine_solver_dispatch_tool.py -q`

Expected: PASS, with flexibility increased but safety and scientific trust not weakened.

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/geometry_check.py backend/packages/harness/deerflow/domain/submarine/library.py domain/submarine/cases/index.json README.md docker/openfoam-sandbox/README.md backend/tests/test_submarine_domain_assets.py backend/tests/test_submarine_geometry_check_tool.py backend/tests/test_submarine_solver_dispatch_tool.py
git commit -m "feat: preserve safety and evidence in vibe cfd orchestration"
```

## Self-Review

### Spec Coverage

This plan covers:

- lead-agent-first orchestration
- skill guidance instead of workflow ownership
- dynamic planning memory
- tool contract decoupling
- UI reframing
- sandbox and evidence guardrails

### Placeholder Scan

No `TBD` or `TODO` placeholders remain. Each task lists target files, intended behavior, test commands, and expected results.

### Type and Boundary Consistency

The plan consistently treats:

- prompts and skills as guidance
- tools as deterministic actions
- runtime state as planning/evidence memory
- sandbox/artifacts as hard boundaries

## Recommended Execution Order

Implement Tasks 1 through 5 in sequence. Do not start UI reframing before prompt/skill and backend contract semantics are aligned, otherwise the frontend will chase moving semantics twice.
