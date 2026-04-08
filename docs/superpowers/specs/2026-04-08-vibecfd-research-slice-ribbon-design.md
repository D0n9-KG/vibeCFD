# VibeCFD Research Slice Ribbon Design

## Goal

Replace the current stage-like submarine workbench with a more flexible `VibeCFD` surface that feels closer to `vibecoding` than a fixed workflow runner.

The new surface should:

- treat the session as an evolving sequence of meaningful research slices, not a mandatory stage checklist
- let the lead agent cut new slices automatically when the research state meaningfully changes
- let the user inspect earlier slices in detail without mutating the current active slice
- preserve the current shallow, scientific, light-color visual language instead of drifting into a dark "AI product" style

## Product Direction

### Core Mental Model

A submarine CFD thread is not a linear workflow.

It is a chain of `research slices`.

Each slice represents a meaningful shift in the session, such as:

- a concrete geometry becoming the active object
- a boundary-condition framing becoming stable enough to inspect
- a computation plan becoming actionable
- a result or postprocessing artifact changing the meaning of the session
- a report-worthy conclusion being formed

The user should feel like they are navigating research states, not advancing through a wizard.

### Main Layout

Keep the overall three-part shell, but change the center surface model:

- **Top:** `Research Ribbon`
- **Center:** `Current Slice Card`
- **Right:** existing general conversation / negotiation rail

The conversation rail remains a standard chat/negotiation surface. It does not become a slice-specific special mode in the first release.

## Research Ribbon

### Behavior

The top ribbon is a compact, expandable history strip of research slices.

Default state:

- shows the current active slice
- shows adjacent previous/next slices where available
- collapses the rest of history

Expanded state:

- reveals the full slice history
- may show branch markers later, but branch visualization is not required in the first release

### Ribbon Node Semantics

Ribbon nodes are not workflow steps.

Each node represents a slice with:

- short title
- compact status
- lightweight evidence or state badge

Examples:

- `任务建立`
- `SUBOFF 几何预检`
- `工况草案`
- `网格与域设置判断`
- `首轮计算结果`
- `后处理与交付判断`

## Slice Lifecycle

### Auto-Creation Strategy

The lead agent should be the primary source of slice creation.

Users may manually create or branch from slices later, but the default flow is:

- the agent works
- the session meaning changes
- a new slice is cut

### First-Release Slice Triggers

Use a hybrid semantic trigger model, not a static phase table.

A new slice may be created when one of the following becomes true:

- the active geometry object changes or becomes concrete for the first time
- the active research objective materially changes
- the lead agent produces a new structured brief or artifact with new meaning
- the session crosses into a clearly different execution context
  - example: from geometry/intent framing into actual simulation planning
- a result or report artifact changes the current scientific claim surface

The trigger system should bias toward meaningful state transitions, not frequent micro-splitting.

## Current Slice Card

### Purpose

The center panel is the main research card for the currently viewed slice.

It should answer:

- what this slice is about
- why this slice exists
- what evidence currently supports it
- what the lead agent currently believes
- what comes next

### First-Release Contents

Each slice card should be able to show:

- slice title
- current objective / why-this-slice summary
- key evidence summary
- current lead-agent interpretation
- key artifacts for this slice
- recommended next slice or next action

This replaces the current rigid eight-module `proposal / execution / report` center structure.

## Historical Inspection

### Viewing a Historical Slice

Clicking a historical slice does **not** change the current active slice.

It opens a `historical inspection mode`.

### Historical Inspection Rules

When the user clicks a past slice:

- the center card changes to that slice's content
- the actual live session remains on the current active slice
- a visible but restrained banner appears above the card, such as:
  - `正在查看历史切片：SUBOFF 几何预检`
- the user gets a clear action:
  - `返回当前研究`

This is inspection, not rollback.

### Continue From Here

From a historical slice, the user may later choose:

- `从此切片继续研究`

This should create a new forward continuation or branch-like slice path.

It must not destructively overwrite the current live state.

This can be deferred until after the first inspection release if needed, but the design should leave room for it.

## Conversation Rail

The conversation rail should remain simple in the first release.

Do **not**:

- make it slice-specific by default
- add separate chat modes for each slice
- overload it with timeline semantics

Instead:

- keep the rail as the general negotiation / conversation area
- let the innovation live in the ribbon + center-card model

This keeps the UX lighter and avoids creating two competing navigation systems.

## Visual Direction

### Visual Language

Keep the current project's light, scientific, instrument-like palette.

Avoid:

- dark "AI dashboard" aesthetics
- neon/cyber styling
- heavy futuristic chrome

Aim for:

- precise
- light
- editorial-scientific
- slightly elevated, but not theatrical

### Motion Direction

Motion should be polished but restrained.

Recommended motion behaviors:

- slice focus change: horizontal slide with subtle depth shift
- historical inspection: card settles into a slightly recessed state with a clear viewing banner
- return to current: layered restore animation
- newly created slice: gentle push-in / emergence from the ribbon

Avoid flashy motion that makes the interface feel like a consumer entertainment product.

## Implementation Impact

### What Must Change

The current submarine workbench still encodes a fixed module order and renders it as a structured flow.

This design requires replacing that model in at least:

- `frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts`
- `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx`

### New Direction

Instead of:

- `SUBMARINE_RESEARCH_MODULE_ORDER`
- fixed module IDs
- module summaries/statuses tied to a hidden workflow table

the center surface should move toward:

- `research slices`
- slice metadata
- viewed-slice state vs active-slice state
- semantic slice summaries derived from runtime/artifacts/messages

## Reuse / Prior Art Decision

This design is intentionally based on:

- Figma's version history / branching mental model
- v0's version and fork mental model
- LangGraph checkpoint and time-travel capabilities
- W&B / MLflow's experiment comparison and lineage thinking

Reference survey:

- [prior-art survey](/C:/Users/D0n9/Desktop/颠覆性大赛/docs/superpowers/prior-art/2026-04-08-vibecfd-timeline-workbench-survey.md)

Chosen strategy:

- reference these patterns
- implement a local VibeCFD-native slice UI on top of the current stack

## First Release Scope

### In Scope

- top research ribbon
- current slice card
- historical inspection mode
- current vs viewed slice distinction
- replacement of the rigid center workflow model
- preservation of the existing conversation rail

### Out of Scope

- destructive rollback of thread state
- full branch graph UI
- full compare mode between arbitrary slices
- conversation rail specialization per slice
- complete artifact lineage explorer as the main surface

## Success Criteria

The redesign is successful when:

- the submarine workspace no longer reads as a fixed workflow
- the user can understand the current research state from one slice card
- the user can inspect earlier slices without losing their place
- the system still feels controllable and scientific, not chaotic
- the UI feels more like an AI-native research surface than a stage runner
