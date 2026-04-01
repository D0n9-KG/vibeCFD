# Phase 2: Runtime Solver Productization - Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Turn a confirmed submarine study from a planning artifact into a controllable DeerFlow runtime flow: recover the bound geometry from thread context, launch OpenFOAM inside the configured sandbox, capture canonical runtime outputs, and let the submarine workbench inspect or resume the job from persisted state. This phase hardens runtime execution and evidence capture; it does not yet decide research claim level, benchmark authority, or broad case-library trust.

</domain>

<decisions>
## Implementation Decisions

### Runtime path and execution boundary
- **D-01:** DeerFlow remains the sole researcher-facing runtime path for submarine CFD; Phase 2 should harden the existing graph/tool/sandbox flow instead of adding shell-only or out-of-band execution shortcuts.
- **D-02:** Thread-bound geometry is the source of truth for runtime execution. Once a study is confirmed, the operator should not have to manually retype an STL absolute path just to cross from planning into execution.
- **D-03:** `deer-flow-openfoam-sandbox:latest` is the Phase 2 local execution baseline. Validation should happen against the same Docker-backed path the workbench actually uses.
- **D-04:** Approval to execute must translate into workbench-visible runtime transitions (`task-intelligence` -> `geometry-preflight` -> `solver-dispatch`) rather than generic-chat detours or hidden backend-only state changes.

### Artifact contract and thread outputs
- **D-05:** Phase 2 canonical runtime artifacts are the OpenFOAM request payload, dispatch summary, execution log, `solver-results.json`, `solver-results.md`, and supported requested postprocess exports.
- **D-06:** `solver-results.json` must persist at least solver completion status, final time, mesh summary, residual summary/history, latest force coefficients, latest forces, reference values, and simulation requirements.
- **D-07:** Requested outputs must stay explicit through a delivery contract. Unsupported outputs should surface as `not_yet_supported` or `needs_clarification`, not disappear silently.
- **D-08:** Runtime artifact paths must be written to both thread-level artifacts and `submarine_runtime.artifact_virtual_paths` so refresh/re-entry does not depend on a single storage channel.

### Workbench visibility and recovery
- **D-09:** The submarine cockpit should treat persisted `submarine_runtime` as the primary execution truth, with artifacts as corroborating detail for charts, cards, and downloads.
- **D-10:** Running, blocked, failed, and completed solver states all require operator-visible status plus enough persisted detail to retry, resume, or inspect after refresh.
- **D-11:** If sandbox startup succeeds but geometry binding or runtime context is missing, the workbench must surface a concrete recoverable runtime error instead of looping back into vague clarification.
- **D-12:** Refresh/resume support is in scope first for a single baseline submarine run. Broader experiment operations and reproducibility UX stay in later phases.

### Phase boundary protection
- **D-13:** Scientific claim-level gating, sensitivity-study completeness, and benchmark-backed acceptance remain downstream concerns. Phase 2 only ensures the runtime captures the evidence inputs those later gates need.
- **D-14:** Phase 2 validation should focus on SUBOFF/STL-backed baseline runs before trying to generalize across weaker case-library entries.

### the agent's Discretion
- Exact split between event-by-event timeline updates and final snapshot writes
- Whether to stream partial log excerpts into runtime timeline or only persist file links
- Workbench wording for `running`, `blocked`, `recoverable`, and `completed` runtime states
- Regression-test split between tool-level, graph-level, and browser-level coverage

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and phase anchors
- `.planning/PROJECT.md` - core value, runtime constraints, and brownfield expectations for research-usable submarine CFD
- `.planning/REQUIREMENTS.md` - `EXEC-01`, `EXEC-02`, and `EXEC-03` define the concrete runtime scope for this phase
- `.planning/ROADMAP.md` - Phase 2 goal, success criteria, and plan split (`02-01` to `02-03`)
- `.planning/STATE.md` - current project position and unresolved blockers entering Phase 2
- `.planning/phases/01-end-to-end-workbench-bootstrap/01-CONTEXT.md` - prior decision that the submarine cockpit, not generic chat, must remain the real operator path

### Runtime state and contracts
- `backend/packages/harness/deerflow/agents/thread_state.py` - shared `submarine_runtime` state shape, merge semantics, artifact/timeline persistence
- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - runtime request/snapshot/event/output contracts and execution-plan template
- `backend/packages/harness/deerflow/domain/submarine/runtime_plan.py` - mapping from runtime/report signals back into execution-plan status
- `backend/packages/harness/deerflow/domain/submarine/handoff.py` - remediation and follow-up handoff contract expectations
- `backend/packages/harness/deerflow/domain/submarine/artifact_store.py` - `/mnt/user-data/outputs/...` virtual-path resolution and artifact loading rules
- `backend/packages/harness/deerflow/domain/submarine/output_contract.py` - requested-output normalization and delivery-state contract
- `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py` - confirmation-status, execution-preference, and design-brief recovery across tool boundaries

### Solver dispatch and sandbox execution
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` - case scaffold generation, sandbox execution, runtime artifact writing, and study/experiment placeholders
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_case.py` - OpenFOAM case scaffold writing, simulation defaults, and workspace virtual-path mapping
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_results.py` - solver log parsing, residual/force extraction, and result summary payloads
- `backend/packages/harness/deerflow/domain/submarine/postprocess.py` - deterministic requested-output export collection and figure-manifest generation
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py` - graph-facing tool entrypoint that updates `submarine_runtime` and thread artifacts
- `backend/packages/harness/deerflow/config/sandbox_config.py` - sandbox provider contract and mount/environment model

### Existing phase-adjacent domain producers
- `backend/packages/harness/deerflow/domain/submarine/design_brief.py` - current design-brief artifacts and confirmation state that gate runtime
- `backend/packages/harness/deerflow/domain/submarine/geometry_check.py` - geometry-preflight artifact model and current next-stage expectations

### Workbench runtime surfaces
- `frontend/src/app/workspace/submarine/[thread_id]/page.tsx` - submarine workbench shell and thread-stream lifecycle wiring
- `frontend/src/components/workspace/submarine-pipeline.tsx` - cockpit state derivation from thread values and artifact content, including sidebar/status/stage cards
- `frontend/src/components/workspace/submarine-stage-cards.tsx` - stage-card UX that must reflect persisted runtime truth
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - frontend expectations for design-brief, geometry, solver-metrics, and report payloads

### Validation evidence
- `logs/langgraph.manual.out.log` - 2026-04-01 evidence that sandbox creation, Docker launch, and shell execution reached the local OpenFOAM sandbox path during Phase 2 exploration

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `build_runtime_snapshot`, `build_execution_plan`, and `extend_runtime_timeline` already provide a structured runtime state model for the workbench.
- `run_solver_dispatch(...)` already knows how to write OpenFOAM case scaffolds, invoke sandbox execution, parse solver outputs, and emit canonical runtime artifacts.
- `collect_requested_postprocess_artifacts(...)` already turns supported requested outputs into deterministic CSV/PNG/Markdown exports plus a figure manifest.
- The submarine workbench already rehydrates design brief, geometry check, solver results, and final report artifacts into stage cards without needing a new UI architecture.

### Established Patterns
- Thread-scoped data lives under `backend/.deer-flow/threads/<thread_id>/user-data/{workspace,uploads,outputs}` and is mounted into the sandbox as `/mnt/user-data/...`.
- Artifact access is virtual-path based (`/mnt/user-data/outputs/...`) rather than raw host paths, so runtime persistence must respect that contract consistently.
- Clarification middleware already intercepts tool-driven clarification and keeps it inside the submarine cockpit rather than bouncing to generic chat.
- Frontend runtime UI currently merges two channels: `submarine_runtime` state and downloadable artifacts. Phase 2 should make those channels agree rather than adding a third source of truth.

### Integration Points
- `submarine_solver_dispatch_tool` is the key bridge from confirmed brief context into actual OpenFOAM runtime work.
- `submarine_runtime_context.py` is the chokepoint for carrying confirmation status, execution preference, and recovered design-brief data into runtime tools.
- `submarine-pipeline.tsx` is already wired to render `solver-results.json`, `final-report.json`, and `submarine_runtime` status when those artifacts exist.
- The sandbox provider is already capable of mounting thread-specific directories and launching `deer-flow-openfoam-sandbox:latest`; Phase 2 mainly needs to make upstream thread context reliable enough to use it without operator re-entry.

</code_context>

<specifics>
## Specific Ideas

- A DevTools-driven validation run on 2026-04-01 created thread `6f46da20-a540-4adb-8b1d-d65c33d9f6c1` from the provided `suboff_solid.stl` test asset and successfully advanced into a clarification about whether to execute OpenFOAM for real.
- The same run showed the Docker sandbox path is real: `logs/langgraph.manual.out.log` records container `deer-flow-sandbox-21d5b6e2` starting from `deer-flow-openfoam-sandbox:latest`, mounting the thread `workspace/uploads/outputs` directories, and reaching `POST http://localhost:8080/v1/shell/exec`.
- After the operator explicitly approved real execution, the next clarification still asked for an STL upload or absolute path. That means the approval -> runtime handoff is still brittle around geometry/context recovery, even though the sandbox itself can launch.
- During that DevTools-driven run, `backend/.deer-flow/threads/6f46da20-a540-4adb-8b1d-d65c33d9f6c1/user-data/uploads` was empty at inspection time. Treat this as a validation target for Phase 2: attachment propagation must be rechecked for both real browser/manual flow and automated browser flow, because runtime productization depends on geometry binding being trustworthy.

</specifics>

<deferred>
## Deferred Ideas

- Scientific claim-level enforcement, sensitivity-study completeness, and benchmark-backed blocking logic belong to Phase 3.
- Broader geometry trust, unit/scale hardening beyond current preflight, and case-library source quality hardening belong to Phase 4.
- Provenance-heavy experiment operations, baseline-vs-variant UX, and cross-environment reproducibility belong to Phase 5.
- Final Chinese researcher reports, supervisor decision UX, and guided rerun/report follow-up belong to Phase 6.
- HPC scheduling, CAD-first intake, and broader CFD-domain expansion remain outside the current milestone.

</deferred>

---

*Phase: 02-runtime-solver-productization*
*Context gathered: 2026-04-01*
