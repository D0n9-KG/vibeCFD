---
name: submarine-geometry-check
description: Inspect uploaded `.stl` submarine geometry for the STL-only v1 runtime, emit DeerFlow artifacts, and return a Chinese preflight summary. Use when a user uploads submarine geometry and wants readiness checks, scale estimates, family mapping, or a visible artifact-backed result.
---

# Submarine Geometry Check

This skill is the first hard gate in the submarine CFD workflow.

## Workflow

1. Read `references/geometry-check-contract.md`.
2. Call the `submarine_geometry_check` tool.
3. Prefer the uploaded `/mnt/user-data/uploads/...` path if the user already attached a geometry file.
4. Pass the task description and task type so the tool can rank cases as part of the result.
5. After the tool returns, summarize the result in Chinese and point the user to the generated artifacts.

## Rules

- Enforce the STL-only v1 boundary and treat `.stl` as the only supported runtime geometry input
- If the upload is not STL, return a clear STL-only requirement instead of inventing a conversion or solver path
- Treat the generated artifacts as the primary deliverable, not the chat reply
- Keep the result traceable to the current DeerFlow thread
