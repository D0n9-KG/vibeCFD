# VibeCFD Stabilization Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the current DeerFlow-based VibeCFD project from a promising demo baseline to a research-safer, reproducible, and maintainable STL-first submarine CFD workbench.

**Architecture:** Keep DeerFlow as the only runtime and harden the submarine domain layer instead of adding a parallel execution stack. Stabilize the frontend workbench first, then raise scientific trust gates in geometry, case ranking, and reporting, and finally reduce oversized modules by extracting shared helpers and smaller domain units.

**Tech Stack:** Python 3.12, FastAPI, LangGraph/DeerFlow harness, Next.js 16, React 19, TypeScript, OpenFOAM sandbox, pytest, ESLint, TypeScript compiler

---

## Scope Split Recommendation

This roadmap covers three independent subsystems and should not be implemented as one giant branch:

1. Frontend/workbench stabilization
2. Scientific trust and CFD workflow hardening
3. Runtime architecture and onboarding/productization

If execution starts, split this roadmap into separate plans per subsystem after Task 1 completes.

### Task 1: Stop-Ship Frontend Stabilization

**Files:**
- Modify: `frontend/src/components/workspace/skill-studio-workbench-panel.tsx`
- Modify: `frontend/src/components/workspace/submarine-stage-cards.tsx`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- Modify: `frontend/src/components/workspace/submarine-task-intelligence-view.ts`
- Modify: `frontend/src/app/api/models/config-models.ts`
- Modify: `frontend/src/app/api/agents/store.ts`
- Modify: `frontend/src/app/workspace/chats/[thread_id]/page.tsx`
- Modify: `frontend/src/app/workspace/agents/[agent_name]/chats/[thread_id]/page.tsx`
- Modify: `frontend/src/components/workspace/messages/message-list.tsx`
- Test: `frontend` ESLint + typecheck

- [ ] Fix hook-order violations in `frontend/src/components/workspace/skill-studio-workbench-panel.tsx` by moving all hooks above the early return and converting post-return derived values into safe unconditional hooks or plain expressions.
- [ ] Fix floating-promise violations in `frontend/src/components/workspace/submarine-stage-cards.tsx` by explicitly awaiting, chaining, or `void`-marking all async confirm/modify actions.
- [ ] Fix remaining import-order, nullish-coalescing, and no-base-to-string errors reported by ESLint in the current frontend workspace.
- [ ] Run `.\node_modules\.bin\eslint.CMD . --ext .ts,.tsx` from `frontend` and confirm zero errors.
- [ ] Run `.\node_modules\.bin\tsc.CMD --noEmit` from `frontend` and confirm the UI still typechecks.
- [ ] Commit with `git commit -m "fix: stabilize submarine and skill studio workbenches"`.

**Exit Criteria:**
- Frontend lint is green.
- Frontend typecheck is green.
- Skill Studio and submarine workbench are no longer blocked by React hook correctness issues.

### Task 2: Raise Geometry Preflight From Demo Check To CFD Gate

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/models.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- Modify: `backend/tests/test_submarine_geometry_check_tool.py`
- Create: `backend/tests/fixtures/submarine/`
- Create: `backend/tests/test_submarine_geometry_gate_contracts.py`

- [ ] Extend geometry inspection to compute mesh-level integrity checks that matter for CFD entry gates: watertightness, non-manifold edges, duplicate triangles, degenerate triangles, and empty/zero-area regions.
- [ ] Separate "unit inference" from "geometry integrity" so a mesh can be geometrically valid but still blocked pending explicit scale confirmation.
- [ ] Replace the current single severe mm-to-m heuristic with a structured scale inference contract that records inference reason, confidence, and whether execution is allowed.
- [ ] Add fixture coverage for a healthy STL, a clearly broken STL, and the SUBOFF-like millimeter-scale case used in local review.
- [ ] Update the tool message and runtime snapshot so the user can see exactly why the geometry is blocked, advisory, or execution-ready.
- [ ] Run `.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_submarine_geometry_check_tool.py backend\tests\test_submarine_geometry_gate_contracts.py -q`.
- [ ] Commit with `git commit -m "feat: harden submarine geometry trust gate"`.

**Exit Criteria:**
- Geometry preflight can fail closed on invalid mesh integrity.
- "Watertight STL" is enforced in code instead of only promised in docs.
- Runtime state clearly distinguishes mesh validity, scale validity, and user-confirmation needs.

### Task 3: Demote Placeholder Cases And Promote Evidence-Aware Ranking

**Files:**
- Modify: `domain/submarine/cases/index.json`
- Modify: `domain/submarine/skills/index.json`
- Modify: `backend/packages/harness/deerflow/domain/submarine/library.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/models.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_domain_assets.py`
- Modify: `backend/tests/test_submarine_geometry_check_tool.py`
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] Add an explicit evidence tier to cases, for example `validated_benchmark`, `curated_reference`, and `advisory_placeholder`.
- [ ] Update ranking so placeholder-only cases can still appear as templates but cannot silently outrank validated benchmarks when a validated benchmark exists.
- [ ] Update geometry-check and solver-dispatch summaries to surface evidence gaps in plain language whenever the chosen case is advisory.
- [ ] Prevent reporting and supervisor handoff from implying research-grade confidence when the selected case lacks benchmark-grade provenance.
- [ ] Add or curate at least one more non-placeholder benchmark-backed path beyond bare-hull SUBOFF resistance.
- [ ] Run `.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_submarine_domain_assets.py backend\tests\test_submarine_geometry_check_tool.py backend\tests\test_submarine_solver_dispatch_tool.py -q`.
- [ ] Commit with `git commit -m "feat: add evidence-aware submarine case ranking"`.

**Exit Criteria:**
- Placeholder templates are visible but clearly marked advisory.
- Ranking no longer overstates scientific confidence.
- Supervisor handoff reflects provenance quality, not just workflow completeness.

### Task 4: Refactor Runtime Hotspots Before More Features Land

**Files:**
- Create: `backend/packages/harness/deerflow/tools/builtins/submarine_paths.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
- Split: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- Create: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_execution.py`
- Create: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_artifacts.py`
- Create: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_summary.py`
- Split: `frontend/src/components/workspace/submarine-stage-cards.tsx`
- Create: `frontend/src/components/workspace/submarine-stage-cards/`
- Split: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Create: `frontend/src/components/workspace/submarine-runtime-panel/`
- Test: targeted backend + frontend regression commands

- [ ] Extract shared thread-path and virtual-path resolution helpers so geometry and solver tools stop duplicating the same filesystem logic.
- [ ] Split `solver_dispatch.py` by responsibility: payload building, execution/scaffold writing, artifact assembly, and summary generation.
- [ ] Split oversized submarine frontend files by stage/view responsibility so future iteration does not keep accumulating into 1k+ line files.
- [ ] Keep behavior stable while refactoring by adding or preserving targeted regression tests first.
- [ ] Run targeted backend submarine tests and frontend lint/typecheck after each extraction slice.
- [ ] Commit with `git commit -m "refactor: split submarine runtime hotspots"`.

**Exit Criteria:**
- No single submarine runtime file continues growing as the default integration point.
- Shared path logic lives in one place.
- Submarine UI files become reviewable and safer to change.

### Task 5: Add A Real Windows-Friendly SUBOFF Smoke Workflow

**Files:**
- Modify: `README.md`
- Modify: `domain/submarine/README.md`
- Modify: `docker/openfoam-sandbox/README.md`
- Modify: `backend/README.md`
- Modify: `backend/CLAUDE.md`
- Create: `scripts/suboff-smoke.ps1`
- Create: `scripts/suboff-smoke.py`
- Create: `docs/superpowers/plans/` follow-up execution plans if needed

- [ ] Document the exact happy path for a Windows user starting from `suboff_solid.stl`: config, upload, geometry check, dispatch planning, optional sandbox execution, and result reporting.
- [ ] Add a scriptable smoke flow that exercises the current STL-first path without requiring users to manually stitch together thread paths and internal artifacts.
- [ ] Explicitly document the difference between `plan_only` and `execute_now`, and the difference between local CLI mode and Docker sandbox mode.
- [ ] Update docs that currently drift from code, including middleware counts and current runtime boundaries.
- [ ] Run the smoke flow end-to-end against `suboff_solid.stl` and record the artifacts it is expected to produce.
- [ ] Commit with `git commit -m "docs: add windows-friendly suboff smoke workflow"`.

**Exit Criteria:**
- A new contributor can run a known STL sample without reverse-engineering the runtime.
- Docs match the actual code paths and current middleware/runtime structure.
- Windows is treated as a first-class dev path rather than an implied Bash-compatible environment.

### Task 6: Upgrade Skill Studio From Draft Generator To Governance Tool

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/skill_studio.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_skill_studio_tool.py`
- Modify: `backend/app/gateway/routers/skills.py`
- Modify: `frontend/src/components/workspace/skill-studio-workbench-panel.tsx`
- Modify: `frontend/src/core/skills/hooks.ts`
- Modify: `backend/tests/test_submarine_skill_studio_tool.py`
- Create: `backend/tests/test_skill_studio_publish_flow.py`

- [ ] Strengthen skill validation so it checks for domain-specific quality, not only skeleton completeness.
- [ ] Make publish/readiness statuses reflect real installability, rollback readiness, and binding state instead of only local artifact presence.
- [ ] Add end-to-end publish-flow tests covering draft generation, archive install, lifecycle update, and rollback.
- [ ] Surface clearer UI messaging for "draft exists", "installed into project", "enabled", and "bound to roles", because those are currently easy to conflate.
- [ ] Run `.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_submarine_skill_studio_tool.py backend\tests\test_skill_studio_publish_flow.py -q`.
- [ ] Commit with `git commit -m "feat: harden skill studio governance flow"`.

**Exit Criteria:**
- Skill Studio becomes a trustworthy publishing/governance surface.
- Draft, published, enabled, and bound states are distinct in both backend state and frontend UI.

## Release Sequence

1. Task 1 first. Do not add new CFD features while the workbench is lint-red.
2. Task 2 second. This is the minimum scientific trust upgrade.
3. Task 3 third. This prevents overstated confidence in case selection and reporting.
4. Task 4 fourth. Refactor only after the behavior and gates are clarified.
5. Task 5 fifth. This makes the project reproducible for new users and demos.
6. Task 6 sixth. Governance should sit on top of a stable runtime and stable UI.

## Success Definition

The project should only be described as "research-ready v1" when all of the following are true:

- Frontend lint and typecheck are green in the default workspace.
- Geometry preflight enforces actual CFD integrity gates.
- Placeholder-only cases are clearly advisory and cannot masquerade as validated benchmarks.
- `suboff_solid.stl` has a documented, repeatable smoke path from upload to reviewable artifacts.
- Submarine runtime and workbench files are small enough to evolve without constant regression risk.
- Skill Studio can publish and govern skills with state transitions that match reality.
