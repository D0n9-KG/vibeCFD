# Geometry Check Contract

The `submarine_geometry_check` tool should be used for submarine geometry preflight.

Inputs:

- `geometry_path`
- `task_description`
- `task_type`
- `geometry_family_hint` (optional)

Expected outputs:

- `geometry-check.json`
- `geometry-check.md`
- `geometry-check.html`

Expected content:

- geometry format
- estimated scale / length
- geometry family mapping
- candidate benchmark or engineering cases
- suggested next-step role boundaries
- `review_status`
- `next_recommended_stage`
- `report_virtual_path`
- `artifact_virtual_paths`

All outputs must be written into `/mnt/user-data/outputs/...` and surfaced as DeerFlow artifacts.
