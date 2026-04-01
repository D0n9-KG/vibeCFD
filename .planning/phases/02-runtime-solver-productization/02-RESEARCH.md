# Phase 2: Runtime Solver Productization - Research

**Researched:** 2026-04-01
**Domain:** DeerFlow submarine runtime handoff, sandbox-backed OpenFOAM execution, canonical CFD artifacts, cockpit rehydration
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Keep DeerFlow as the only researcher-facing runtime path; do not add shell-only or out-of-band execution as a workaround.
- Treat thread-bound geometry as the execution source of truth once the study is confirmed.
- Use `deer-flow-openfoam-sandbox:latest` as the local runtime baseline for validation.
- Persist a canonical runtime artifact set so the cockpit can inspect or resume without depending on container internals.
- Make the submarine workbench show running, blocked, failed, and completed runtime states from persisted data.
- Keep scientific claim gating, case-library trust expansion, and final delivery/report UX out of Phase 2.

### The Agent's Discretion
- Exact helper boundaries between middleware, runtime-context helpers, and tool entrypoints
- Whether directory creation is eager globally or guarded per tool call
- The minimum runtime fields the frontend needs beyond `artifact_virtual_paths`
- How much runtime detail should be shown directly in stage cards versus linked as artifacts

### Deferred Ideas (Out of Scope)
- Scientific evidence enforcement and benchmark-backed claim gating
- Broader geometry trust and case-library hardening
- Provenance-heavy experiment UX across environments
- Final Chinese report packaging and supervisor delivery flow
</user_constraints>

<research_summary>
## Summary

Phase 2 is not starting from zero. The current runtime already has most of the heavy machinery needed for research-facing CFD execution:

- `submarine_solver_dispatch_tool.py` already resolves runtime context, writes a `submarine_runtime` snapshot, and can call `run_solver_dispatch(...)`.
- `solver_dispatch.py` already scaffolds OpenFOAM cases, launches the sandbox execution path, writes `openfoam-request.json`, `dispatch-summary.md`, `openfoam-run.log`, `solver-results.json`, `solver-results.md`, and postprocess exports.
- `solver_dispatch_results.py` already parses residual history, force coefficients, forces, mesh summary, and reference values.
- The frontend cockpit already merges `thread.values.artifacts` with `submarine_runtime.artifact_virtual_paths` and can rehydrate design brief, geometry check, solver results, and final report artifacts.

The biggest remaining gap is not "can OpenFOAM run in Docker?" It can. The strongest local evidence is the 2026-04-01 browser-driven thread `6f46da20-a540-4adb-8b1d-d65c33d9f6c1`, where `logs/langgraph.manual.out.log` shows:

- thread-specific `workspace/uploads/outputs` mounts were added
- container `deer-flow-sandbox-21d5b6e2` started from `deer-flow-openfoam-sandbox:latest`
- the runtime reached `POST http://localhost:8080/v1/shell/exec`

The productization gap is continuity:

1. The operator confirms execution in the submarine cockpit.
2. The runtime should inherit the bound STL and continue.
3. Instead, the flow can still fall back to a clarification asking for an STL upload or absolute path.

The code-level evidence points to a concrete fragility at the thread-boundary layer:

- `ThreadDataMiddleware` defaults to `lazy_init=True`, which computes `workspace/uploads/outputs` paths but does not create those directories in `before_agent()`.
- `submarine_design_brief_tool.py` and `submarine_solver_dispatch_tool.py` both resolve geometry from thread paths and may iterate `uploads_dir`.
- The 2026-04-01 log shows `submarine_design_brief_tool.py` hit `FileNotFoundError` while iterating the thread uploads directory for the same thread later used for sandbox-backed dispatch.

That means Phase 2 should be executed as three contracts, in order:

1. **Input continuity contract:** a confirmed thread always has a recoverable runtime geometry path and ready thread directories.
2. **Canonical artifact contract:** the same request/log/solver/postprocess artifacts are persisted into both thread artifacts and `submarine_runtime`.
3. **Rehydration contract:** refresh/re-entry derives truthful running or blocked state from persisted runtime plus artifacts, not from optimistic UI assumptions.

**Primary recommendation:** implement Phase 2 as a narrow runtime-hardening phase with three plans:

- `02-01`: make thread directories and geometry handoff deterministic from design brief through solver dispatch
- `02-02`: normalize canonical artifact persistence and surface solver metrics/log pointers through runtime/UI contracts
- `02-03`: make the cockpit runtime-aware on refresh, resume, and recovery instead of relying on stage order alone
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library / Module | Version | Purpose | Why Standard Here |
|------------------|---------|---------|-------------------|
| DeerFlow runtime graph | repo current | Researcher-facing orchestration path | The product promise depends on this being the real operator path |
| Local container sandbox provider | repo current | Docker-backed tool execution | Already launches `deer-flow-openfoam-sandbox:latest` successfully |
| OpenFOAM sandbox image | `deer-flow-openfoam-sandbox:latest` | Actual CFD execution baseline | This is the image proven to start from the live workbench path |
| Pydantic contracts | repo current | Runtime snapshot, execution plan, output delivery normalization | The frontend already assumes structured payloads from these contracts |
| Next.js + React 19 cockpit | repo current | Workbench runtime inspection and recovery UI | Existing submarine pipeline already consumes runtime and artifacts |

### Supporting
| Library / Module | Purpose | When to Use |
|------------------|---------|-------------|
| `thread_data_middleware.py` | Thread-scoped workspace/uploads/outputs paths | Any fix involving missing runtime directories |
| `uploads_middleware.py` | Uploaded STL metadata injected into message/state context | Any fix involving attachment-to-runtime continuity |
| `submarine_runtime_context.py` | Recovery of confirmation state, execution preference, and design brief data | Any fix bridging design brief, geometry check, and solver dispatch |
| `solver_dispatch_results.py` | Residual/force parsing and solver result summarization | Any fix involving canonical solver metrics |
| `submarine-pipeline.tsx` and `submarine-stage-cards.tsx` | Runtime/artifact rehydration and stage-card truth | Any fix involving refresh, blocked state, or runtime inspection |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hardening DeerFlow runtime continuity | Ask the user to re-enter the STL path after confirmation | Rejected because it breaks the thread-bound execution promise |
| Persisting canonical thread outputs | Reading metrics directly from the sandbox/container workspace only | Rejected because refresh, downloads, and recovery would be brittle |
| Runtime-aware cockpit status | Inferring stage completion from stage order only | Rejected because blocked and failed runs become indistinguishable |
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Thread-Bound Geometry Recovery
**What:** Resolve the authoritative STL from thread state before any runtime tool asks the user for more input.
**Preferred precedence:**
1. Explicit tool argument when valid
2. Persisted `submarine_runtime.geometry_virtual_path`
3. Persisted design-brief `geometry_virtual_path`
4. Current `uploaded_files` state (`/mnt/user-data/uploads/*.stl`)
5. Latest actual STL under the thread uploads directory

**Why it matters:** This lets a confirmed operator action cross the planning-to-execution boundary without manual path re-entry.

### Pattern 2: Canonical Runtime Artifact Set
**What:** Every real solver-dispatch run should persist the same minimal evidence package:
- `openfoam-request.json`
- `dispatch-summary.md`
- `dispatch-summary.html`
- `openfoam-run.log` when execution was attempted
- `solver-results.json`
- `solver-results.md`
- `supervisor-handoff.json`
- supported requested postprocess exports

**Why it matters:** The cockpit, later scientific gates, and any download/report layer all depend on a stable artifact contract.

### Pattern 3: Dual-Channel Rehydration
**What:** Treat `submarine_runtime` as primary execution truth and artifacts as corroborating detail.
**Why it matters:** Runtime truth should survive partial artifact loading, while artifacts should survive partial state loss.
**Implementation rule:** If the two channels disagree, Phase 2 should fix the producer contract rather than adding a third UI-only cache.

### Pattern 4: Recoverable Runtime Failure Instead of Generic Clarification
**What:** Missing geometry binding, missing thread directories, or absent solver artifacts should become explicit runtime-blocked state with recovery guidance.
**Why it matters:** Researchers need inspectable failure, not a vague chat loop that hides the real runtime break.

### Anti-Patterns to Avoid
- Letting submarine tools call `uploads_dir.iterdir()` without first ensuring the directory exists
- Treating `uploaded_files` as chat-only metadata instead of a valid runtime recovery source
- Writing runtime artifacts to thread outputs but forgetting to mirror them into `submarine_runtime.artifact_virtual_paths`
- Showing a solver stage as "done" only because `current_stage` moved forward once
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Runtime state persistence | A new UI-only runtime store | `SubmarineRuntimeSnapshot` + `merge_submarine_runtime()` | Existing reducers already merge execution plans and timelines |
| Output delivery bookkeeping | Ad hoc per-output UI heuristics | `output_contract.py` and `SubmarineOutputDeliveryItem` | Output support/delivery semantics already exist |
| Artifact resolution | Raw host path joins in the frontend | `artifact_store.py` virtual-path model | Thread outputs are already virtual-path based |
| Solver metric parsing | New regexes in UI code | `solver_dispatch_results.py` | Backend already parses residuals, forces, and coefficients deterministically |

**Key insight:** Phase 2 should tighten existing contracts and fallback rules, not replace the runtime architecture.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Lazy thread-data paths without real directories
**What goes wrong:** A submarine tool receives valid `thread_data.uploads_path` but the directory does not exist yet, so path iteration raises `FileNotFoundError`.
**Why it happens:** `ThreadDataMiddleware` currently defaults to lazy initialization and only computes paths.
**How to avoid:** Ensure thread directories exist before tool execution or guard all directory scans with existence checks plus fallback to `uploaded_files`.

### Pitfall 2: Geometry continuity split between artifacts and transient message metadata
**What goes wrong:** The model knows an STL was uploaded, but the runtime tools cannot recover a stable geometry path once the conversation advances.
**Why it happens:** `uploaded_files`, design-brief artifacts, and runtime state are not treated as one continuity contract.
**How to avoid:** Centralize geometry recovery in `submarine_runtime_context.py` and reuse it across design brief, geometry check, and solver dispatch.

### Pitfall 3: Runtime artifacts written, but not surfaced
**What goes wrong:** `solver-results.json` or `openfoam-run.log` exists under thread outputs, but the cockpit never discovers it after refresh.
**Why it happens:** `thread.values.artifacts` and `submarine_runtime.artifact_virtual_paths` drift apart.
**How to avoid:** Build one canonical artifact list in the backend and write it to both channels every dispatch.

### Pitfall 4: Stage cards only understand ordered progress
**What goes wrong:** A blocked solver run can still render like a normal active or completed pipeline because stage state is derived from stage ordering rather than runtime status.
**Why it happens:** `StageCardState` currently only supports `done`, `active`, and `pending`.
**How to avoid:** Extend stage-card/runtime-view logic to represent blocked runtime truth explicitly.
</common_pitfalls>

<validation_architecture>
## Validation Architecture

Phase 2 needs all three layers below before it should be marked complete:

- **Backend contract tests:** `test_thread_data_middleware.py`, `test_submarine_design_brief_tool.py`, `test_submarine_runtime_context.py`, `test_submarine_solver_dispatch_tool.py`, `test_submarine_artifact_store.py`, `test_thread_state_reducers.py`
- **Frontend runtime-state tests:** `submarine-pipeline-runs.test.ts`, `submarine-pipeline-status.test.ts`, `submarine-runtime-panel.utils.test.ts`, `submarine-runtime-panel.trends.test.ts`, `submarine-pipeline-layout.test.ts`
- **Browser proof:** Chrome DevTools MCP using `C:\Users\D0n9\Desktop\suboff_solid.stl`, confirming that:
  1. a confirmed study reaches sandbox-backed dispatch without asking for a new STL path
  2. the solver stage surfaces log/metric/artifact pointers
  3. refreshing the thread preserves truthful runtime state

The browser check is mandatory because the key Phase 2 failure mode is a continuity issue across upload, confirmation, tool execution, and refresh.
</validation_architecture>

<open_questions>
## Open Questions

1. **Should thread directory creation become globally eager, or only guaranteed before submarine tools run?**
   - What we know: lazy path computation can surface missing-directory failures.
   - Recommended default: create thread directories in `ThreadDataMiddleware.before_agent()` so every runtime path is safe by construction.

2. **Should blocked runtime state be encoded as `stage_status`, a new `runtime_status`, or both?**
   - What we know: the current frontend stage-card API cannot represent blocked explicitly.
   - Recommended default: keep `stage_status` for per-stage detail and add one explicit runtime-level status for cockpit truth.

3. **How much runtime detail should the cockpit show inline versus linking as artifacts?**
   - What we know: logs, solver metrics, and output delivery are already persisted or derivable.
   - Recommended default: show summary badges and latest event inline, keep full logs/downloads as artifact links.
</open_questions>

<sources>
## Sources

### Primary (High confidence)
- `backend/packages/harness/deerflow/agents/middlewares/thread_data_middleware.py`
- `backend/packages/harness/deerflow/agents/middlewares/uploads_middleware.py`
- `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
- `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py`
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_results.py`
- `backend/packages/harness/deerflow/domain/submarine/output_contract.py`
- `backend/packages/harness/deerflow/domain/submarine/artifact_store.py`
- `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- `frontend/src/components/workspace/submarine-pipeline.tsx`
- `frontend/src/components/workspace/submarine-stage-cards.tsx`
- `frontend/src/components/workspace/submarine-stage-card.tsx`
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`
- `logs/langgraph.manual.out.log`

### Secondary (High confidence)
- `.planning/STATE.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/phases/02-runtime-solver-productization/02-CONTEXT.md`
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: DeerFlow submarine runtime continuity and sandbox execution
- Ecosystem: Docker-backed OpenFOAM runtime, Pydantic contracts, Next.js workbench rehydration
- Patterns: thread-bound geometry recovery, canonical artifact persistence, runtime-aware cockpit status
- Pitfalls: lazy thread directories, geometry handoff breaks, artifact channel drift, stage-order-only UI logic

**Confidence breakdown:**
- Sandbox execution path exists: HIGH
- Geometry/runtime continuity gap exists: HIGH
- Artifact persistence base is already implemented: HIGH
- Best implementation shape: HIGH
- Remaining uncertainty: MEDIUM around the minimum extra runtime fields the frontend needs for blocked/recovery UX

**Research date:** 2026-04-01
**Valid until:** 2026-05-01
</metadata>

---

*Phase: 02-runtime-solver-productization*
*Research completed: 2026-04-01*
*Ready for planning: yes*
