---
name: submarine-solver-dispatch
description: Prepare or execute a controlled OpenFOAM dispatch inside DeerFlow sandbox, emit artifact-backed runtime payloads, and hand the run back to the primary agent cleanly. Use when execution is justified, inputs are ready, and the task needs a traceable solver dispatch plan or a bounded first execution.
---

# Submarine Solver Dispatch

Use this skill when the primary agent has enough evidence to justify execution planning or bounded execution. Geometry preflight may be one input, but it is not the only way execution can become ready.

## Workflow

1. Read `references/solver-dispatch-contract.md`.
2. Confirm that the user goal, key inputs, and execution approval are clear enough.
3. Call the `submarine_solver_dispatch` tool only when execution planning or execution itself is warranted.
4. Prefer the current DeerFlow thread upload path for the geometry input.
5. Only set `execute_now=true` when the task is approved and the runtime has a valid sandbox command to run.
6. Return a Chinese summary that points back to the generated artifacts instead of repeating raw command details.

## Rules

- Treat the dispatch JSON and summary artifacts as the canonical execution handoff.
- Keep the real OpenFOAM case scaffold in DeerFlow `workspace`, and keep presentation/report artifacts in DeerFlow `outputs`.
- Preserve the runtime review fields and `submarine_runtime` stage snapshot when the tool returns them.
- Preserve `workspace_case_dir_virtual_path`, `run_script_virtual_path`, and `supervisor_handoff_virtual_path` when they are available.
- If execution is not yet confirmed, stop at a planned dispatch and hand the run back for user-facing review.
- If execution has already happened, hand off toward result reporting instead of answering from logs alone.
- Treat this skill as a high-risk action boundary, not as a mandatory stage in every submarine conversation.
