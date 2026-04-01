# Phase 2: Runtime Solver Productization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `02-CONTEXT.md`; this log preserves the alternatives considered and the auto-selected defaults.

**Date:** 2026-04-01
**Phase:** 02-runtime-solver-productization
**Areas discussed:** Runtime path, geometry handoff, runtime artifacts, workbench recovery, phase boundary

---

## Runtime Path

| Option | Description | Selected |
|--------|-------------|----------|
| Keep DeerFlow as the only runtime path | Reuse the existing graph, tool, sandbox, and thread-state model so execution stays traceable in the workbench | x |
| Add shell-only bypass execution | Faster short term, but researchers would lose runtime traceability and cockpit state | |
| Mix manual CLI and DeerFlow runtime | Lets execution happen outside the intended operator path and weakens recovery semantics | |

**User's choice:** Auto-selected the recommended option: keep DeerFlow as the sole runtime path.
**Notes:** Project constraints and Phase 1 already established that the dedicated submarine cockpit must remain the real operator path.

---

## Geometry Handoff

| Option | Description | Selected |
|--------|-------------|----------|
| Treat thread-bound uploads/runtime state as the execution source of truth | A confirmed run should inherit the already bound STL and continue without manual path re-entry | x |
| Ask the operator to retype the geometry path before execution | Operationally fragile and easy to break after refresh or approval loops | |
| Infer the path from prompt text only | Too brittle for research execution and not compatible with attachment-driven flow | |

**User's choice:** Auto-selected the recommended option: runtime should consume the thread-bound geometry directly.
**Notes:** A 2026-04-01 sandbox-backed test still asked for an STL path after approval, so this remains a concrete runtime hardening target.

---

## Runtime Artifacts

| Option | Description | Selected |
|--------|-------------|----------|
| Persist a canonical artifact set | Save request payload, dispatch summary, execution log, solver metrics, and supported postprocess exports into thread outputs | x |
| Persist only a summary report | Too little detail for inspect/resume/recovery and later scientific gates | |
| Leave outputs only inside the container/workspace | Not acceptable for refresh, download, or reproducible workbench behavior | |

**User's choice:** Auto-selected the recommended option: persist the full canonical runtime artifact set.
**Notes:** Existing backend code already has most of these artifact writers; Phase 2 must make them reliable and workbench-visible.

---

## Workbench Recovery

| Option | Description | Selected |
|--------|-------------|----------|
| Persist runtime truth in `submarine_runtime` plus artifacts | Lets the cockpit show running/blocked/failed/completed state and survive refresh | x |
| Rely on browser-console diagnostics and ad-hoc logs | Unacceptable for researcher-facing runtime operations | |
| Reconstruct state from artifacts alone | Loses in-flight progress and makes recovery semantics too weak | |

**User's choice:** Auto-selected the recommended option: `submarine_runtime` is the primary runtime truth, with artifacts as supporting detail.
**Notes:** Frontend stage cards already read both channels; Phase 2 needs to make them agree and stay recoverable.

---

## Phase Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Stop Phase 2 at runtime productization | Capture executable evidence inputs now, then let later phases decide scientific readiness and delivery gates | x |
| Fold scientific claim gates into Phase 2 | Too broad and would dilute runtime hardening work | |
| Defer resume/recovery until later phases | Would leave the runtime productization incomplete for actual operator use | |

**User's choice:** Auto-selected the recommended option: keep Phase 2 focused on runtime productization and hand off scientific gating to later phases.
**Notes:** This preserves the roadmap order: runtime first, scientific evidence gates second, delivery/reproducibility later.

---

## the agent's Discretion

- Streaming partial solver-log excerpts versus linking to full persisted log files
- Exact state-transition timing between tool completion and UI card refresh
- Badge wording and UX copy for recoverable runtime failures
- Test partitioning across tool, graph, and browser layers

## Deferred Ideas

- Scientific claim-level blocking and verification evidence policy
- Case-library source hardening and geometry trust expansion
- Experiment ops, provenance, and cross-environment reproducibility
- Final report/supervisor delivery loop
