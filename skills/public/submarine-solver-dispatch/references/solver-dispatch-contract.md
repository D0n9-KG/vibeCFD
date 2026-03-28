# Submarine Solver Dispatch Contract

When dispatching a submarine CFD solve inside DeerFlow:

- Treat the generated `openfoam-request.json` as the canonical machine-readable handoff.
- Treat the markdown and HTML summaries as the primary presentation artifacts for the current stage.
- Preserve these review fields whenever present:
  - `review_status`
  - `next_recommended_stage`
  - `report_virtual_path`
  - `artifact_virtual_paths`
- Preserve these runtime continuation fields whenever present:
  - `workspace_case_dir_virtual_path`
  - `run_script_virtual_path`
  - `supervisor_handoff_virtual_path`
- Preserve the `submarine_runtime` stage snapshot so later stages can continue from structured thread state.
- Keep the executable OpenFOAM case scaffold under DeerFlow `workspace`, not under a separate ad-hoc executor directory.
- If the dispatch is still planned, make it explicit that Supervisor confirmation is still required.
- If the dispatch has already executed, point the workflow toward result reporting and artifact consolidation.

Preferred output sections:

1. Dispatch summary
2. Geometry and selected case context
3. Execution status
4. Risks or missing parameters
5. Next-step recommendation
6. Review contract / artifact handoff
