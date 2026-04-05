# VibeCFD Lead-Agent-First Design

**Date:** 2026-04-05

**Status:** Drafted from design discussion and approved direction

## Goal

Reposition the current DeerFlow-based submarine CFD system from a stage-driven workflow product into a true Vibe CFD system:

- `Codex` or `Claude Code` is the user-facing primary agent
- the primary agent negotiates goals, constraints, deliverables, and execution strategy with the user
- submarine skills guide the primary agent with domain knowledge, heuristics, and guardrails
- deterministic tools and sandboxed execution perform high-risk actions safely
- sub-agents handle bounded specialist tasks under the primary agent's direction

This should feel closer to vibe coding than to a rigid pipeline runner.

## What Must Change

The current implementation still behaves as:

`chat -> design brief -> user confirmation -> geometry preflight -> solver dispatch -> reporting`

That interaction is useful for control, but it makes the system feel like a fixed workflow. The target interaction should instead be:

`user goal -> primary agent negotiation -> dynamic plan -> selective skill/tool/sub-agent use -> sandboxed execution -> artifact-backed delivery`

The primary agent should decide when to:

- keep asking questions
- write or update a structured plan snapshot
- inspect geometry
- search cases or references
- dispatch solver preparation
- run commands inside the sandbox
- generate delivery artifacts
- stop and ask for approval

The system should no longer assume a mandatory linear stage order for every task.

## Non-Goals

This redesign does not aim to:

- remove DeerFlow runtime primitives
- remove thread-local workspace, uploads, outputs, or artifacts
- let the primary agent execute unsafe commands directly on the host
- discard scientific trust gates for CFD execution and claims
- bring back the legacy prototype executor

## Design Principles

### 1. Primary-Agent-First

`Codex` or `Claude Code` remains the single conversational owner of the task.

The primary agent is responsible for:

- understanding the user's real goal
- negotiating scope and success criteria
- deciding which domain skills are relevant
- deciding whether a specialist sub-agent is worth spawning
- deciding when the task has enough information to move from planning to execution
- synthesizing final outputs for the user

The user should feel they are collaborating with one capable research engineer, not driving a menu of workflow stages.

### 2. Skills Guide, Tools Execute

Skills should be used to shape the primary agent's judgment, not to dictate a universal stage order.

Skills should answer questions like:

- what checks matter before running submarine CFD
- what evidence is needed before making stronger scientific claims
- what kinds of requested outputs are currently supported
- when geometry issues require clarification
- how to decompose a task into specialist sub-agents

Tools should stay deterministic and bounded. Examples:

- `submarine_geometry_check`
- `submarine_solver_dispatch`
- `submarine_result_report`
- future postprocess or verification tools

The primary agent decides whether to call a tool. The tool should not try to become the planner.

### 3. Structured Memory, Not Structured Workflow

Structured artifacts are still valuable, but they should represent the current shared understanding of the task rather than a fixed pipeline state machine.

The structured layer should capture:

- current task summary
- confirmed vs unconfirmed assumptions
- bound geometry
- selected reference case, if any
- execution preference
- requested deliverables
- scientific trust posture
- produced artifacts
- execution evidence

This state should support dynamic replanning, branching, and revisiting earlier assumptions.

### 4. Hard Guardrails Only For High-Risk Actions

The system should avoid hard-coding sequence, but it should still harden high-risk actions:

- actual solver execution
- file-system and command execution
- publication or export of artifacts
- scientific-claim escalation

These boundaries should be enforced through tools, sandboxing, explicit artifact generation, and structured evidence contracts rather than only through prompt wording.

### 5. DeerFlow-Native Deployment Safety

The redesign should remain compatible with DeerFlow's runtime model so it can run safely on a server later.

That means retaining:

- per-thread user-data roots
- artifact-backed evidence
- sandbox-wrapped execution
- sub-agent delegation through DeerFlow-native mechanisms
- prompt + skill injection instead of app-specific orchestration engines

## Target Architecture

### Layer 1: Primary Agent

This is the conversational control plane.

Responsibilities:

- talk to the user
- clarify ambiguous requirements
- build and revise the current plan
- decide whether more information is needed
- choose skills and sub-agents
- choose when to invoke tools
- decide when the user must explicitly approve high-risk actions

This layer should no longer be forced by prompt text into a single mandatory stage order.

### Layer 2: Domain Skills

This is the strategic guidance layer.

Responsibilities:

- define domain-specific best practices
- define warning signs
- define preferred decomposition patterns
- define claim/evidence expectations
- define when certain tools are recommended or disallowed

This layer should become less like a workflow script and more like a submarine-CFD operating handbook for the primary agent.

### Layer 3: Specialist Sub-Agents

This is the bounded analysis/execution layer.

Responsibilities:

- geometry specialist: inspect geometry issues and summarize findings
- case/reference specialist: search benchmark candidates or related studies
- solver specialist: prepare or execute solver tasks in the sandbox
- reporting specialist: synthesize evidence-backed outputs

Sub-agents should not own the user relationship. They should return bounded results to the primary agent.

### Layer 4: Deterministic Tools

This is the precise action layer.

Responsibilities:

- generate structured geometry findings
- generate execution payloads and case scaffolds
- generate reports and evidence packages
- update machine-readable artifacts

Tool inputs and outputs should stay explicit and reviewable.

### Layer 5: Sandbox + Artifact Boundary

This is the hard safety and reproducibility layer.

Responsibilities:

- execute risky commands safely
- isolate per-thread files
- record machine-readable outputs
- preserve reviewable evidence for later verification

This layer should remain strict even if the planning layer becomes more flexible.

## Target Interaction Model

### Before

The current system assumes a mostly linear path:

1. capture brief
2. wait for confirmation
3. run preflight
4. dispatch solver
5. report

### After

The target system should support more organic task patterns such as:

- "Here is an STL. First tell me whether it is usable, and suggest what we can study."
- "I want drag and surface pressure at 5 m/s. If the setup looks safe, go ahead."
- "Compare two candidate operating conditions and tell me which one is more worth simulating first."
- "Don't solve yet. Just tell me what inputs and assumptions are still risky."
- "Generate a result package I can review with my advisor."

The primary agent should be able to:

- stop at planning
- stop at geometry review
- run partial execution
- revisit assumptions after new user input
- branch into different output requests

without fighting a stage machine.

## State Model Redesign

The current `submarine_runtime` should evolve from a stage registry into a task session ledger.

It should keep:

- `task_summary`
- `goal_status`
- `execution_preference`
- `approval_state`
- `geometry_binding`
- `assumptions`
- `open_questions`
- `selected_case`
- `requested_outputs`
- `scientific_guardrails`
- `execution_evidence`
- `artifact_virtual_paths`
- `activity_timeline`

It should de-emphasize:

- `current_stage`
- `next_recommended_stage`

These can still exist for UI hints, but they should not be the primary source of truth for system behavior.

## Tool Contract Changes

### `submarine_design_brief`

This tool should no longer act like a compulsory stage gate.

It should become:

- a structured planning-memory tool
- callable whenever the primary agent wants to checkpoint current understanding
- able to update confirmed and unconfirmed assumptions without implying a fixed next stage

### `submarine_geometry_check`

This should remain a hard technical gate for geometry quality, but it should not imply that solver dispatch must immediately follow.

It should return:

- mesh integrity findings
- scale findings
- readiness assessment
- recommended next actions

without owning the whole workflow.

### `submarine_solver_dispatch`

This should remain the execution-prep or execution tool.

It should only run when:

- the primary agent decides execution is appropriate
- required inputs are present
- guardrails allow it

It should not assume that the prior user interaction exactly matched a fixed stage protocol.

### `submarine_result_report`

This should remain evidence-backed and artifact-backed.

It should produce:

- structured result summary
- evidence quality summary
- delivery package
- explicit scientific-claim boundary

## Skill Redesign

### Current Problem

The current `submarine-orchestrator` and prompt section prescribe a fixed order.

### Target Shape

The orchestration skill should instead say:

- when a structured plan snapshot is useful
- when geometry inspection is recommended
- when execution is unsafe
- when to stop and ask the user
- when reporting can or cannot make stronger scientific statements
- which specialist sub-agent is best for the current subtask

In other words, skills should encode `judgment`, not `workflow`.

## UI Redesign Direction

The frontend should stop presenting the system as if users are manually walking a fixed pipeline.

The workbench should instead emphasize:

- current negotiated objective
- active assumptions and open risks
- produced evidence and outputs
- execution readiness
- user approvals that are still needed
- available next actions chosen by the primary agent

The UI can still visualize artifacts by category such as planning, geometry, execution, and reporting, but those categories should help review, not dictate behavior.

## Safety Model

To remain server-safe and DeerFlow-native:

- sandbox stays mandatory for risky execution
- artifact outputs stay mandatory for reviewable evidence
- direct host execution remains disallowed
- high-risk transitions should remain explicit in tool calls
- scientific claim levels should remain structured, not free-form

This gives the primary agent flexibility without weakening operational safety.

## Migration Strategy

### Phase 1

Loosen prompt and skill language first:

- remove mandatory linear workflow phrasing
- retain guidance and safety language
- keep current tools intact

### Phase 2

Refactor structured state:

- make plan snapshots more dynamic
- demote `current_stage` to UI hinting
- center state around assumptions, approvals, evidence, and outputs

### Phase 3

Refactor frontend:

- reduce stage-first framing
- promote task-first and evidence-first views
- present suggested next actions without implying mandatory order

### Phase 4

Strengthen hard guardrails:

- geometry integrity
- execution approval
- sandbox enforcement
- claim boundary enforcement

## Recommendation

The project should adopt:

`lead-agent-first orchestration with skill-guided judgment and sandbox-enforced execution`

This keeps the spirit of DeerFlow, preserves server deployability, and aligns with the intended Vibe CFD experience better than continuing to refine a fixed submarine workflow.
