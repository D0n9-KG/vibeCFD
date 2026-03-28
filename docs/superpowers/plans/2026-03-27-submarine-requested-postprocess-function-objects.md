# Submarine Requested Postprocess Function Objects Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make user-requested CFD outputs configure the OpenFOAM case scaffold so requested pressure and wake results are planned at case-generation time.

**Architecture:** Extend the existing requested-output contract into `solver_dispatch` earlier in the pipeline by generating additional `controlDict` function objects only for supported requested outputs. Keep the scope tight and compatible with the current export chain: wire `surface_pressure_contour` and `wake_velocity_slice` first, leave `streamlines` explicitly unsupported, and verify through scaffold tests rather than speculative rendering logic.

**Tech Stack:** Python, DeerFlow submarine runtime, OpenFOAM case scaffold generation, pytest.

---

### Task 1: Failing Scaffold Tests

**Files:**
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Write the failing tests**

Add focused tests that assert:
- requested `surface_pressure_contour` adds a stable `surfacePressure` function object to `system/controlDict`
- requested `wake_velocity_slice` adds a stable `wakeVelocitySlice` function object to `system/controlDict`
- unsupported outputs such as `streamlines` still do not add new function objects

- [ ] **Step 2: Run the focused tests to verify they fail**

Run:
- `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k function_objects`

Expected: FAIL because the current scaffold always writes the same static `controlDict`.

### Task 2: ControlDict Wiring

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py` (only if runtime propagation needs adjustment)

- [ ] **Step 1: Implement the minimal function-object plan**

Add:
- requested-output ID normalization for scaffold generation
- supported requested-output to function-object mapping
- `controlDict` generation that appends only the requested supported postprocess blocks

- [ ] **Step 2: Run the focused tests**

Run:
- `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k function_objects`

Expected: PASS

### Task 3: Regression and Docs

**Files:**
- Modify: `docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Run regression**

Run:
- `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q`
- `uv run pytest tests -q -k submarine`

Expected: PASS

- [ ] **Step 2: Update docs**

Record:
- the new function-object-driven behavior
- the still-open gap between raw postprocess generation and final rendered figure generation
