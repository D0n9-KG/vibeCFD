---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 3
current_phase_name: Scientific Verification Gates
current_plan: 3
status: ready_to_execute
stopped_at: Phase 3 Plan 02 completed; next logical step is executing 03-03 to add benchmark comparison logic and connect it to scientific claim-level decisions
last_updated: "2026-04-01T16:56:14Z"
last_activity: 2026-04-02
progress:
  total_phases: 6
  completed_phases: 2
  total_plans: 3
  completed_plans: 2
  percent: 44
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-04-01)

**Core value:** A researcher can go from natural-language CFD intent to reproducible, evidence-backed submarine results without manually building and operating OpenFOAM cases.
**Current focus:** Phase 3 - Scientific Verification Gates

## Current Position

**Current Phase:** 3
**Current Phase Name:** Scientific Verification Gates
**Total Phases:** 6
**Current Plan:** 03
**Total Plans in Phase:** 3
**Status:** Ready to execute
**Progress:** [####--] 44%
**Last Activity:** 2026-04-02
**Last Activity Description:** Executed 03-02 to package sensitivity-study workflows, preserve experiment linkage gaps explicitly, and surface SCI-02 summaries on the active submarine workbench

Phase: 3 of 6 (Scientific Verification Gates)
Plan: 3 of 3
Status: Ready to execute
Last activity: 2026-04-02

## Performance Metrics

**Velocity:**

- Total plans completed: 8
- Average duration: ~50 min
- Total execution time: ~6.7 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3 | ~60 min | ~20 min |
| 2 | 3 | ~2.7 hours | ~54 min |
| 3 | 2 | ~3.2 hours | ~95 min |

**Recent Trend:**

- Last 5 plans: 02-01, 02-02, 02-03, 03-01, 03-02
- Trend: Positive

## Decisions Made

| Phase | Summary | Rationale |
|-------|---------|-----------|
| 1 | Phase 1 had to fix the dedicated submarine workbench path instead of redirecting users to generic chat as a workaround. | The product promise is a dedicated research cockpit, so the real user entry path must work natively. |
| 1 | Research usability is defined by evidence-backed claim levels, not merely by producing artifacts or running OpenFOAM. | The audit showed that runtime success alone can still yield scientifically unusable outputs. |
| 1 | `deer-flow-openfoam-sandbox:latest` is the current local execution baseline for submarine CFD. | This is the image that actually executed the generated OpenFOAM case successfully during validation. |
| 1 | Clarification interrupts must be safe under Windows/GBK consoles because missing-input negotiation is part of the real operator path. | A live browser run showed `ask_clarification` could otherwise fail before the user ever saw the question. |
| 2 | DeerFlow remains the only acceptable researcher-facing runtime path for submarine CFD execution. | Splitting execution into ad-hoc shell flows would break traceability, runtime recovery, and cockpit visibility. |
| 2 | Phase 2 must treat thread-bound geometry and persisted runtime state as execution truth, not ask operators to retype paths after approval. | A runtime handoff that loses geometry context is not productized, even if Docker can launch. |
| 2 | Frontend-visible STL attachments must still be reconstructed into the outgoing submit payload when prompt state drops `message.files`. | Browser validation proved backend recovery alone is insufficient if the first operator submit never uploads the geometry. |
| 2 | Canonical runtime artifacts must include request payloads, execution logs, solver metrics, and requested postprocess exports inside thread outputs. | Refresh/resume and later scientific gates both depend on a stable artifact contract. |
| 2 | Mock-mode validation must override configured LangGraph artifact URLs and use a UUID-backed demo thread when live solver-results artifacts are not stable. | The operator-facing cockpit still needs end-to-end validation even when live backend evidence is temporarily unsuitable for deterministic UI checks. |
| 2 | The submarine workbench must expose running, blocked, failed, and completed runtime states from persisted `submarine_runtime`. | Researchers need inspect/resume/recovery behavior, not console-only diagnostics. |
| 2 | `runtime_status` is now the authoritative workbench-level runtime truth, while `current_stage` and `stage_status` stay responsible for per-stage detail. | This keeps refresh-safe recovery logic deterministic and prevents the frontend from reconstructing runtime truth from stage order alone. |
| 3 | Phase 3 should productize existing scientific verification modules rather than rebuilding a second evidence pipeline beside them. | The codebase already contains verification, study, experiment-linkage, evidence, and supervisor-gate primitives; the gap is first-class workflow behavior and visibility. |
| 3 | Stability evidence must become an explicit artifact and cockpit truth as soon as a baseline solve is eligible. | SCI-01 is not satisfied if residual and force-history logic remains buried inside late report synthesis only. |
| 3 | The actual researcher-facing workbench must consume SCI-02 summaries directly from the active pipeline stage card, not only from reusable helper panels. | Browser validation showed the page in use no longer mounted `submarine-runtime-panel.tsx`, so workflow visibility had to be attached to `submarine-stage-cards.tsx`. |
| 3 | Benchmark claim decisions should build on the same stability and sensitivity evidence contracts established earlier in the phase. | Claim-level decisions are only trustworthy when benchmark validation consumes the same explicit evidence trail seen by the researcher. |
| 3 | Dispatch-time runtime state must carry both structured SCI-01 payloads and top-level gate consequences, so completed runs can still be scientifically blocked or limited after refresh. | Researchers need immediate scientific usability signals before opening the final report, and those signals must survive re-entry without frontend-only reconstruction. |

## Pending Todos

- Investigate `useThreads()` callers that still trigger `POST /threads/search` on some `/workspace/chats/[thread_id]?mock=true` loads.
- Capture or generate a live non-mock SCI-02 thread once benchmark and follow-up execution paths are ready, so browser validation can move from deterministic mock data to a fresh runtime artifact set.

## Blockers

- Phase 3 Plan 03 is still outstanding, so benchmark-backed claim hardening is not yet productized.
- Most non-SUBOFF case-library entries still rely on placeholder references and need hardening before broader research use.

## Session

**Last Date:** 2026-04-02 00:56
**Stopped At:** Phase 3 Plan 02 completed; next logical step is executing 03-03
**Resume File:** `.planning/phases/03-scientific-verification-gates/03-03-PLAN.md`
