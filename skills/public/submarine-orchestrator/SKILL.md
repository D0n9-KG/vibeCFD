---
name: submarine-orchestrator
description: Guide the primary agent when a submarine CFD task may need case search, geometry checks, solver dispatch, reporting, or specialist sub-agents. Use when the task spans multiple concerns and the primary agent needs DeerFlow-native judgment and role boundaries.
---

# Submarine Orchestrator

Read `references/subagent-roles.md` when a submarine task spans more than one stage.

## Intent

This skill does not restore the legacy executor. It helps the primary agent decide how a submarine CFD task should be decomposed inside DeerFlow itself:

- case search and task understanding
- geometry check and preprocessing
- solver dispatch
- result reporting

Use it to keep the system specialized for submarine CFD instead of generic chat while still letting the primary agent control the order of work.

## Guidance For The Primary Agent

When the primary agent should coordinate a real submarine CFD workflow, prefer the specialized DeerFlow subagents instead of generic delegation if the work is worth decomposing:

- `submarine-task-intelligence`
- `submarine-geometry-preflight`
- `submarine-solver-dispatch`
- `submarine-result-reporting`

Use the built-in tools selectively:

- `submarine_design_brief` when the negotiated plan needs to be checkpointed
- `submarine_geometry_check` when geometry quality or scale is uncertain
- `submarine_solver_dispatch` when execution is justified and approved
- artifact-driven Chinese reporting when evidence already exists

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
- When the user is still discussing goals、工况、交付物或约束，优先更新 `submarine_design_brief`，不要把关键方案只留在聊天记录里。
- Let the primary agent decide whether the next best move is more clarification, geometry inspection, case retrieval, execution planning, or reporting.
- If the task only reaches geometry preflight, stop there cleanly and return artifact-backed conclusions instead of fabricating solver results.
- If solver dispatch has executed, hand the run to `submarine-result-reporting` rather than answering from raw logs alone.
- Keep the orchestration judgment-first: this skill should guide what to do next, not force one global tool order for every task.
