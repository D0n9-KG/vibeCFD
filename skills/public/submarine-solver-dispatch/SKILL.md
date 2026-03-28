---
name: submarine-solver-dispatch
description: Prepare or execute a controlled OpenFOAM dispatch inside DeerFlow sandbox, emit artifact-backed runtime payloads, and hand the run back to Supervisor cleanly. Use when geometry preflight is complete and the workflow needs a traceable solver dispatch plan or a bounded first execution.
---

# Submarine Solver Dispatch

Use this skill after geometry preflight has already established that the uploaded submarine geometry can enter the CFD workflow.

## Workflow

1. Read `references/solver-dispatch-contract.md`.
2. Call the `submarine_solver_dispatch` tool.
3. Prefer the current DeerFlow thread upload path for the geometry input.
4. Only set `execute_now=true` when the task is already confirmed and the runtime has a valid sandbox command to run.
5. Return a Chinese summary that points back to the generated artifacts instead of repeating raw command details.

## Rules

- Treat the dispatch JSON and summary artifacts as the canonical execution handoff.
- Keep the real OpenFOAM case scaffold in DeerFlow `workspace`, and keep presentation/report artifacts in DeerFlow `outputs`.
- Preserve the runtime review fields and `submarine_runtime` stage snapshot when the tool returns them.
- Preserve `workspace_case_dir_virtual_path`, `run_script_virtual_path`, and `supervisor_handoff_virtual_path` when they are available.
- If execution is not yet confirmed, stop at a planned dispatch and hand the run back for Supervisor review.
- If execution has already happened, hand off toward result reporting instead of answering from logs alone.
