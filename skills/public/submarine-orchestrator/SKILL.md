---
name: submarine-orchestrator
description: Coordinate the submarine CFD workflow across case search, geometry preflight, solver dispatch, and reporting roles. Use when a task spans multiple stages and needs DeerFlow-native role boundaries.
---

# Submarine Orchestrator

Read `references/subagent-roles.md` when a submarine task spans more than one stage.

## Intent

This skill does not restore the legacy executor. It defines how the DeerFlow-native workflow should be decomposed inside DeerFlow itself:

- case search and task understanding
- geometry check and preprocessing
- solver dispatch
- result reporting

Use it to keep the system specialized for submarine CFD instead of generic chat.

## Required orchestration path

When the task is a real submarine CFD workflow, prefer the specialized DeerFlow subagents instead of generic delegation:

- `submarine-task-intelligence`
- `submarine-geometry-preflight`
- `submarine-solver-dispatch`
- `submarine-result-reporting`

Use the built-in tools in this order when appropriate:

1. `submarine_design_brief`
2. `submarine_geometry_check`
3. `submarine_solver_dispatch`
4. artifact-driven Chinese reporting

## V1 geometry boundary

- v1 direct solver execution is `STL-only`
- Treat clean `.stl` as the only geometry format that can proceed into solver dispatch
- Treat non-`STL` uploads as unsupported for the v1 runtime and hand back a clear STL-only requirement instead of fabricating a solver run

## Runtime rules

- Treat DeerFlow `thread / upload / artifact` as the canonical run container.
- Treat structured JSON outputs as the canonical machine-readable state for Supervisor review.
- Preserve and pass through these review fields whenever available:
  - `review_status`
  - `next_recommended_stage`
  - `report_virtual_path`
  - `artifact_virtual_paths`
- When the user is still discussing goals,工况、交付物或约束，先更新 `submarine_design_brief`，不要把关键方案只留在聊天记录里。
- Only move from `submarine_design_brief` to `submarine_geometry_check` after the current task understanding is clear enough to form a first executable plan.
- If the task only reaches geometry preflight, stop there cleanly and hand off for Supervisor review instead of fabricating solver results.
- If solver dispatch has executed, hand the run to `submarine-result-reporting` rather than answering from raw logs alone.
