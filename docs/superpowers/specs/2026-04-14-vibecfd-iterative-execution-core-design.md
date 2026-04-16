# VibeCFD Iterative Execution Core Design

## Goal

Evolve the current submarine workflow into a true `vibeCFD` core: a system that can negotiate complex CFD work with researchers, keep an explicit task contract, replan when goals change, coordinate multiple specialist agents, execute variants and follow-ups, and return stable, traceable outputs.

The target is not “an agent that decides science for the user.” The target is “a collaborative CFD execution partner that helps researchers get complex work done reliably.”

## Product Definition

### What We Are Building

We are building a collaborative CFD execution system that supports:

- iterative task negotiation
- structured calculation planning
- explicit output requests and delivery tracking
- experiment lineage across baseline runs, variants, and follow-ups
- multi-agent role handoffs
- reproducible artifact chains

### What We Are Not Building

- Not a generic workflow engine for arbitrary domains
- Not a scientific-decision oracle that substitutes for researcher judgment
- Not a pure prompt/skill shell with weak state
- Not an optimization platform-first product

## Current Leverage In The Codebase

The current project already has the beginnings of the right architecture:

- `SubmarineRuntimeRequest` already carries `task_summary`, `simulation_requirements`, `requested_outputs`, `calculation_plan`, and `custom_variants`
- `design_brief.py` already emits `requested_outputs`, `open_questions`, `execution_outline`, and stage hints
- `output_contract.py` already normalizes supported vs unsupported requested outputs
- `solver_dispatch.py` already writes `study-manifest.json`, `experiment-manifest.json`, `run-record.json`, and `run-compare-summary.json`
- runtime state already supports `execution_plan`, `runtime_status`, and `skill_runtime_snapshot`
- there are already domain subagent roles for:
  - `task-intelligence`
  - `geometry-preflight`
  - `scientific-study`
  - `experiment-compare`
  - `scientific-verification`
  - `result-reporting`
  - `scientific-followup`

This means the right move is not a rewrite. The right move is to strengthen the existing contract and orchestration spine.

## Approach Comparison

### Approach A: Prompt And Skill First

Use more skills and smarter prompts so the system better interprets complex research asks.

Pros:
- fastest visible improvement
- low implementation cost

Cons:
- fragile under long-running iteration
- weak reproducibility and lineage
- state still leaks across message history instead of being explicit

### Approach B: Iterative Execution Core First

Strengthen the underlying task contract, replanning model, experiment lineage, and multi-agent role boundaries, then let prompts and skills accelerate a stable core.

Pros:
- matches the actual `vibeCFD` product goal
- improves stability, extensibility, and visible UX together
- turns future skills into durable accelerators instead of fragile glue

Cons:
- more architectural work before flashy surface changes

### Approach C: Generic Workflow Engine First

Abstract everything into a generalized DAG/workflow system and then layer submarine CFD on top.

Pros:
- theoretically broad

Cons:
- product drift
- higher complexity
- lower domain fit right now

## Chosen Approach

**Approach B: Iterative Execution Core First**

We should treat the current submarine workflow as the seed of a domain-specific iterative execution engine for CFD. The core work is to make changing research intent, branching variants, and follow-up remediation first-class and durable.

## Core Design

### 1. Research Task Contract

The system needs a stronger “task contract” than the current design brief.

Today, the design brief captures many useful fields, but it does not yet fully behave like a living research task agreement. We need it to explicitly represent:

- research objective
- current scenario / case template
- confirmed inputs
- unresolved decisions
- required outputs
- unsupported outputs
- evidence expectations
- variant policy
- replanning rationale

This contract should be the authoritative handoff object between negotiation and execution, rather than treating message history as the real source of truth.

#### Concrete Schema Direction

This should not stay conceptual. The authoritative persisted contract should be an explicit extension of the existing DeerFlow-native snapshot model and must be carried by the same backend-to-frontend path that already transports submarine runtime truth.

The first-pass schema should add contract-specific fields such as:

- `contract_revision`
- `revision_summary`
- `unresolved_decisions`
- `capability_gaps`
- `evidence_expectations`
- `variant_policy`

These fields should be produced first in `design_brief.py`, persisted through `build_runtime_snapshot(...)` in `contracts.py`, carried by downstream tools such as result reporting and scientific follow-up, and then consumed by the existing frontend model builders rather than only by raw page wrappers.

The design intent is:

- message history remains explanatory
- runtime snapshot remains authoritative
- frontend models derive visible state from the authoritative snapshot

### 2. Iteration Loop As A First-Class Primitive

The central product behavior should be:

`negotiate -> clarify -> confirm -> execute -> inspect -> revise -> branch or follow up -> re-execute`

That loop already exists informally. We need to make it structurally explicit.

The system must support at least these iteration modes:

- revise the same baseline with changed simulation settings
- append new requested outputs to an existing run family
- derive structured variants from a baseline
- follow a remediation handoff into another execution cycle
- reopen a completed or blocked thread with new research goals

### 3. Experiment Graph Rather Than Flat Run History

Current manifests already hint at this. We should formalize it into an experiment graph model:

- **Baseline node**
- **Variant nodes**
- **Follow-up nodes**
- **Derived output nodes**
- **Comparison nodes**

Each node should preserve:

- parentage
- why it was created
- what changed
- which outputs it is expected to produce
- whether it satisfied its purpose

This gives us a real “researcher collaboration memory” rather than just a long thread transcript.

#### Canonical Lineage Vocabulary

We should not invent a second lineage language if the current code already has one.

The canonical run-lineage fields should continue to be:

- `run_role`
- `variant_origin`
- `baseline_reference_run_id`
- `compare_target_run_id`

The correct first-step enhancement is to extend the existing experiment and run-record schema with missing iteration metadata, such as:

- `contract_revision`
- `lineage_reason`
- `requested_output_ids`
- optional follow-up provenance notes

The experiment graph therefore becomes a stronger interpretation layer over the existing `experiment-manifest.json`, `study-manifest.json`, `run-record.json`, and `run-compare-summary.json` artifacts, not a second competing graph store.

### 4. Capability Negotiation Before Execution

When a researcher asks for outputs like wake slices, pressure maps, wall friction, or benchmark comparisons, the system should not defer that understanding until reporting. It should negotiate early:

- supported now
- can be delivered after specific post-processing
- needs more geometry / setup / reference data
- not yet supported

This negotiation should feed:

- the design brief
- the execution plan
- the output delivery plan

### 5. Clear Agent Boundaries

The current role breakdown is close, but we should harden the boundaries:

- **Supervisor / lead agent**
  - owns user negotiation
  - owns contract revisions
  - decides when replanning is needed
- **Task-intelligence**
  - case matching
  - workflow path recommendation
- **Geometry-preflight**
  - geometry readiness and scale risk
- **Solver-dispatch**
  - execution package generation and run launch
- **Scientific-study**
  - variant planning and execution graph expansion
- **Experiment-compare**
  - baseline vs variant relationship tracking
- **Result-reporting**
  - delivery-oriented packaging
- **Scientific-followup**
  - remediation continuity and re-entry into execution

The key change is that contract revision and iteration policy should stay with the supervisor layer, while specialist roles act against explicit, durable contracts.

### 6. Skill Strategy

Skills should accelerate stable workflows, not replace them.

We should use skills for bounded, reusable domain accelerators such as:

- benchmark planning
- requested-output normalization
- variant proposal generation
- post-processing recipe selection
- experiment summary drafting

We should not use skills as the only place where core orchestration logic lives.

We also should not assume that creating a new skill automatically makes it routable. New runtime-facing skills should only be introduced after they have a clear invocation path through existing stage owners or explicit routing logic. Until then, the safer path is to strengthen the current stage-aligned skills and role prompts.

## Stability Requirements

For this design to qualify as `vibeCFD`, the following must be true:

- changing task goals must update the task contract, not just append chat text
- derived variants must preserve lineage to the baseline
- each important output request must have an explicit support and delivery status
- blocked states must explain whether the block is due to setup, missing reference, unsupported output, failed execution, or unresolved researcher confirmation
- follow-up execution must preserve parentage and purpose
- the visible frontend must always be able to explain what the system thinks it is doing now

## Implementation Implications

### Backend

Primary focus:

- strengthen runtime contracts and design brief payloads
- upgrade output negotiation
- formalize experiment graph lineage
- extend follow-up and variant orchestration
- add stable contract-level tests

### Skills

Introduce focused, explicit skills only where they increase reuse:

- benchmark-planning skill
- variant-planning skill
- postprocess-packaging skill

### Frontend

Frontend is not the first implementation target, but it must eventually expose:

- current task contract
- unresolved decisions
- requested outputs and support status
- experiment graph / variant lineage
- follow-up reasoning and next-step clarity

## Milestones

### Milestone 1

Make the task contract iteration-ready:

- richer requested-output and unresolved-decision handling
- contract revision semantics
- stronger runtime state propagation

### Milestone 2

Make variant and follow-up lineage explicit:

- baseline/variant/follow-up relationships
- experiment graph metadata
- deterministic re-entry paths

### Milestone 3

Make output delivery negotiation real:

- supported vs unsupported vs pending outputs
- better post-processing planning
- delivery plan tied to artifacts

### Milestone 4

Turn common iteration patterns into reusable skills and planner helpers.

## Acceptance Criteria

We should consider this design successful when a researcher can:

1. describe a complex CFD goal in natural language
2. see the system turn it into a structured, revisable task contract
3. request changes after the first plan without losing continuity
4. branch variants or follow-ups from a baseline
5. ask for specific outputs and immediately see what is supported, missing, or pending
6. complete several iterations while preserving artifact lineage and traceability

## Prior Art / Reuse Decision

We will **adapt the existing DeerFlow project** and use external systems as **reference-only patterns**:

- signac for research data-space and job lineage ideas
- Dakota for deterministic study-shape ideas
- OpenFOAM function objects for runtime and post-process output generation
- ASME / ITTC for evidence and credibility framing

We will not import a new workflow stack as the product core.
