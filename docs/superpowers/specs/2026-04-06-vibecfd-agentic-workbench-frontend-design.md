# VibeCFD Agentic Workbench Frontend Design

**Date:** 2026-04-06

**Status:** Drafted from front-end restructuring discussion and approved direction

## Goal

Redesign the VibeCFD front end so it feels closer to vibecoding than to a fixed CFD pipeline, while still making the full workflow transparent and controllable.

The new front end must let the user:

- watch the main agent negotiate, plan, delegate, execute, and report in one continuous workspace
- interrupt the flow at any time and renegotiate with the main agent
- inspect the full process without drowning in always-on stage cards
- clearly see plan generation, plan confirmation, sub-agent delegation, skill usage, tool calls, solver execution, postprocess work, evidence quality, and final reporting
- use both `submarine` and `skill-studio` through one coherent workbench language

The redesign should preserve the current color palette and general product identity, but replace the current page structure, information hierarchy, and module layout.

## Problem Statement

The current front end has moved some language toward lead-agent-first orchestration, but the product still feels structurally stage-first.

Current issues:

- the `submarine` workbench still relies too heavily on stage cards and stage progression as the main mental model
- the top-level summary improved, but deeper views still revert to a rigid pipeline feel
- the user can see many artifacts, but not the agentic story connecting plan, delegation, skills, tools, execution, and report
- the chat rail is still treated as a separate surface rather than the user's control path into the live process
- `skill-studio` has strong visual flavor but behaves more like a concept dashboard than a true agentic workbench
- `submarine` and `skill-studio` do not yet feel like two expressions of the same system

The redesign must solve this without hiding process detail or weakening operational transparency.

## Design Principles

### 1. Agentic, Not Stage-First

The primary user experience should be:

`goal negotiation -> live plan evolution -> delegated work -> evidence-backed execution -> report and iteration`

not:

`stage 1 -> stage 2 -> stage 3 -> stage 4`

Stages may still exist internally and visually as secondary structure, but they should no longer dominate the main screen.

### 2. One Workspace, Two Domains

`submarine` and `skill-studio` should feel like the same workbench system operating on different objects:

- `submarine` operates on a simulation thread
- `skill-studio` operates on a skill asset lifecycle thread

The shell, layout rules, summary language, control affordances, and secondary layers should be shared.

### 3. Show The Whole Process Without Showing Everything At Once

The interface must preserve full process visibility, but the central area should only show the most relevant layer for the current thread state.

The full workflow stays available through secondary layers, drawers, and drill-down surfaces.

### 4. Negotiation Is A First-Class UI Primitive

The user must always feel able to interrupt the system, question a decision, revise the plan, or redirect execution.

This means the chat surface is not a secondary utility. It is a persistent negotiation rail that can expand into a full control surface when needed.

### 5. Evidence And Control Over Ornament

The redesign should stay visually confident and polished, but its value must come from clarity of control, evidence traceability, and process legibility rather than decorative dashboards.

## Shared Product Model

The front end should treat every workbench thread as an `agentic session` with:

- a current objective
- a current live state
- a current decision boundary
- a current process narrative
- a lineage and provenance state
- a set of evidence and artifacts
- a set of operator actions
- a revision and publishing state when applicable

This becomes the shared product model behind both `submarine` and `skill-studio`.

## Shared Shell

Both workbenches should use the same three-zone shell:

### Left: Workspace Navigation

Purpose:

- switch product surfaces
- switch active threads
- jump to recent work

Rules:

- lightweight and non-competing
- no dense operational data here
- supports quick context switching only

### Center: Adaptive Main Stage

Purpose:

- show the most relevant current work surface for the thread

Rules:

- exactly one primary stage at a time
- no "all stages expanded" layout
- should change based on session state, not on a fixed tab order alone

### Right: Negotiation Rail

Purpose:

- keep the user connected to the main agent's active reasoning and control surface

Rules:

- narrow by default
- shows latest question, pending approvals, interrupt entry points, and quick actions
- expands into full conversation mode when the user engages
- remains present in both `submarine` and `skill-studio`

## Information Hierarchy

To keep the interface simple without losing capability, all front-end content should be organized into four layers.

### Layer 1: Primary Stage

The main adaptive center panel.

This answers:

- what is happening now
- what matters now
- what can the user do now

### Layer 2: Negotiation Layer

The right rail and expanded conversation view.

This answers:

- what is the main agent asking
- what approvals or changes are pending
- how can the user interrupt or redirect

### Layer 3: Process Layers

Expandable surfaces for:

- live narrative timeline
- dependency map
- sub-agent assignments
- skill usage
- tool calls
- execution flow
- postprocess flow

This answers:

- how did the system get here
- what ran
- in what order or dependency pattern

### Layer 4: Evidence Layers

Expandable surfaces for:

- artifacts
- logs
- figures
- metrics
- reports
- scientific gates
- validation evidence
- provenance manifests
- reproducibility summaries
- environment parity assessments
- study and compare outputs
- dry-run and publish-gate evidence
- revision history

This answers:

- what proof exists
- what result quality exists
- what outputs were generated
- whether the outputs are trustworthy enough to reuse, publish, compare, or claim against

## Shared Component System

The redesign should establish a shared component grammar before page-specific work.

### Core Shell Components

- `WorkbenchShell`
- `ThreadHeader`
- `AdaptiveMainStage`
- `NegotiationRail`
- `SecondaryLayerHost`

### Session Components

- `SessionSummaryBar`
- `DecisionCard`
- `ActionQueueCard`
- `InterruptActionBar`
- `ThreadStateBadge`

### Process Components

- `NarrativeStream`
- `ProcessLayerDrawer`
- `DependencyMapPanel`
- `AgentDispatchPanel`
- `SkillUsagePanel`
- `ToolCallPanel`

### Evidence Components

- `ArtifactPanel`
- `EvidencePanel`
- `MetricPanel`
- `ReportPanel`
- `ValidationGatePanel`
- `ProvenancePanel`
- `ReproducibilityPanel`
- `StudyComparePanel`
- `TestingEvidencePanel`

### Asset Components

- `AssetBoard`
- `RevisionTimeline`
- `BindingsPanel`
- `PublishDecisionPanel`
- `LifecycleStatePanel`
- `AssistantModePicker`

The same components should be reused across `submarine` and `skill-studio` wherever semantics match.

## Submarine Workbench Design

The `submarine` workbench should stop behaving like a cockpit with permanent stage cards and instead become an adaptive simulation session workspace.

### Submarine State A: Plan / Negotiate

Used when the thread is still forming or revising the task.

The primary stage should show:

- current objective
- current plan snapshot
- assumptions
- open questions
- requested outputs
- proposed sub-agents
- proposed skills and tools
- approval readiness

The negotiation rail should show:

- latest question from the main agent
- pending approvals
- interrupt and revise entry points
- quick actions like `confirm plan`, `revise assumptions`, `request more evidence`

### Submarine State B: Execute / Orchestrate

Used when the thread is actively coordinating geometry review, dispatch, execution, verification, or postprocess work.

The primary stage should show:

- live session narrative
- current active task
- what sub-agent is running
- what skill is in use
- what tool was called
- what execution step is active
- what can be interrupted or rerun

The process layers should expose:

- sub-agent assignment tree
- skill usage history
- tool call history
- execution dependency map
- solver and postprocess chain

### Submarine State C: Results / Postprocess / Report

Used when outputs, evidence, and reporting dominate the thread.

The primary stage should show:

- latest result summary
- current conclusion strength
- scientific claim boundary
- delivery decision status
- remediation status and recommended next owner
- evidence quality summary
- provenance and reproducibility status
- generated figures and metrics
- postprocess methods used
- study, compare, and variant status
- final report status
- next recommended follow-up

The negotiation rail should support:

- request stronger claims
- request additional postprocess
- revise report framing
- choose a delivery decision
- trigger remediation or manual handoff
- trigger rerun, compare study, or extension study
- create a follow-up branch from the current result state

### Submarine Secondary Layers

The following must remain available but not permanently occupy the center:

- full live timeline
- sub-agent allocation history
- skill usage chain
- tool invocation log
- solver execution log
- postprocess method details
- artifact browser
- report browser
- evidence and verification details
- provenance manifest and environment parity view
- reproducibility and recovery guidance
- experiment board for baseline, variants, and compare outputs
- remediation handoff, follow-up history, and operator action log

## Skill Studio Workbench Design

The `skill-studio` workbench should stop acting like a concept dashboard and become an adaptive skill-asset lifecycle workspace.

### Skill Studio State A: Define Skill

The primary stage should show:

- problem being solved
- creator or assistant selection before thread start
- target use case
- trigger conditions
- workflow steps
- required tools
- examples
- anti-patterns
- open drafting issues

Once the thread starts, the chosen creator or assistant mode should remain visible as session provenance and become locked unless the user intentionally starts a new thread.

### Skill Studio State B: Evaluate / Verify

The primary stage should show:

- structure checks
- completeness checks
- rule quality checks
- scenario-level test matrix
- dry-run readiness and handoff evidence
- blockers and warnings
- suggested fixes

This should use the same `NarrativeStream` pattern as submarine execution, but the narrative is about evaluation and hardening rather than solver execution.

This stage must not collapse testing into a single readiness badge. The user should be able to inspect scenario status, blocking reasons, expected outcomes, and dry-run related publish blockers from the main workbench.

### Skill Studio State C: Connect / Publish

The primary stage should show:

- lifecycle state
- enabled state
- active revision
- published revision
- rollback target
- version note
- explicit bindings
- current revision context
- related skills
- publish readiness
- rollback readiness
- unresolved risks

Secondary layers should expose:

- revision history
- binding map
- relationship graph
- dry-run evidence
- publish artifacts
- rollback options

The publish surface should make the relationship between `enabled`, `active revision`, `published revision`, and `rollback target` explicit so the user can tell what is live now, what is only saved, what is currently published, and what will be restored if rollback is triggered.

## Functional Coverage Matrix

The redesign must explicitly surface every major capability the back end already supports or is expected to support.

### Submarine Coverage

- plan generation: primary stage in `Plan / Negotiate`
- plan confirmation: decision cards plus negotiation rail approvals
- sub-agent task allocation: process layer agent dispatch panel
- skill usage: process layer skill usage panel and event chips in narrative stream
- actual calculation flow: execution narrative + tool call layer + execution panel
- geometry review: either as plan evidence or execution narrative event with expandable findings
- solver dispatch: execution narrative event + control actions + execution details
- postprocess methods: result stage method section plus expandable process layer
- postprocess results: evidence layer figures, metrics, and derived outputs
- calculation results: result board metric section
- evidence quality and claim limits: validation gate panel
- provenance, reproducibility, and environment parity: dedicated evidence panels, not a generic metadata foldout
- scientific delivery decision and remediation handoff: result-stage decision card plus operator action surfaces
- scientific follow-up and extension history: follow-up board with lineage to current run
- multi-run studies, custom variants, and compare outputs: experiment board with baseline, candidate, lineage, and compare summaries
- final report: report panel and report status in result stage
- artifacts and logs: evidence layer artifact browser
- user interruption: always available through negotiation rail
- rerun or redirection: interrupt action bar and decision cards

### Skill Studio Coverage

- skill definition: definition board primary stage
- creator or assistant selection: visible in thread setup and persisted thread header
- workflow structure: definition board plus process layer
- examples and anti-patterns: definition board
- validation and readiness: evaluation primary stage
- scenario-level tests and dry-run evidence: evaluation stage plus testing evidence panel
- draft quality warnings: evaluation primary stage
- revisions: asset board plus revision timeline
- bindings: asset board plus bindings panel with explicit binding state
- related skills: process/evidence layer graph panel
- publish decision: publish decision panel
- publish state model: enabled state, active revision, published revision, rollback target, and version notes
- rollback: asset board controls and revision timeline
- user interruption: always available through negotiation rail

No backend capability that matters to user trust or control should exist only in hidden JSON without a corresponding front-end surface.

## Visual Language

The redesign should preserve the current palette direction and product identity.

Keep:

- existing color family and tonal direction
- overall VibeCFD visual brand recognition
- current warm and technical balance

Change:

- page structure
- spatial hierarchy
- component composition
- density management
- visual emphasis rules

The new visuals should feel:

- sharper and more intentional
- less dashboard-like for the sake of dashboards
- more like an intelligent control room for a live agentic system

## Interaction Rules

### Rule 1: One Primary Question Per Main Stage

At any moment, the center should answer one dominant question only.

Examples:

- "What do I still need to confirm?"
- "What is running right now?"
- "How strong are the current conclusions?"

### Rule 2: Interruptibility Must Be Obvious

The user should never have to hunt for how to stop, revise, redirect, or renegotiate.

### Rule 3: Full Process Visibility Must Be Recoverable

Even if not all process detail is visible at once, the user must be able to reconstruct:

- who did what
- what skills were used
- what tools were called
- what execution actually happened
- what outputs came out of that work

### Rule 4: Chat Should Control, Not Distract

The negotiation rail should always feel available, but should not dominate the primary stage unless the user intentionally expands it.

### Rule 5: Trust-Critical States Must Stay Named

Provenance, reproducibility, study comparison, publish gates, rollback state, and dry-run evidence must remain first-class named surfaces. They should not be flattened into generic badges, hidden accordions, or unlabeled JSON viewers.

## Routing Direction

The surface routing can stay roughly compatible with current paths, but the page semantics should change.

Recommended direction:

- `/workspace/submarine/new`
  - starts in `Plan / Negotiate`
- `/workspace/submarine/[thread_id]`
  - adaptive workbench, not a stage cockpit
- `/workspace/skill-studio/new`
  - starts in `Define Skill`
- `/workspace/skill-studio/[thread_id]`
  - adaptive lifecycle workbench, not a concept landing page

## Migration Strategy

### Phase 1: Shared Shell And Right Rail

- introduce common workbench shell
- unify thread header and negotiation rail
- preserve current colors

### Phase 2: Replace Stage-First Center Panels

- remove current permanent stage card dominance
- introduce adaptive main stage containers
- move stage detail into process layers

### Phase 3: Process Transparency Layers

- add narrative stream
- add sub-agent, skill, tool, and execution layers
- add unified evidence layers with dedicated provenance, reproducibility, and testing surfaces

### Phase 4: Result And Asset Boards

- replace current result and skill summary surfaces with dedicated asset boards
- add experiment/compare boards and scientific remediation surfaces
- unify report, evidence, lifecycle, revision, and publish-state panels

## Recommendation

The front end should adopt:

`a shared agentic workbench shell with an adaptive main stage, a persistent right-side negotiation rail, and expandable process/evidence layers`

For user experience, this should behave like:

- vibecoding when the agent is actively thinking, negotiating, and executing
- a research caseboard when the user is reviewing evidence and conclusions
- a control room when the user interrupts, redirects, approves, or reruns work

This design is the best fit for VibeCFD because it preserves transparency and control without forcing the user to live inside a stage machine.
