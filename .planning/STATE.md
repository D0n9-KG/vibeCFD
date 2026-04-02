---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 05
current_phase_name: experiment ops and reproducibility
current_plan: Not started
status: planning
stopped_at: Phase 5 context gathered
last_updated: "2026-04-02T07:57:53.489Z"
last_activity: 2026-04-02
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 12
  completed_plans: 12
  percent: 67
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-04-02)

**Core value:** A researcher can go from natural-language CFD intent to reproducible, evidence-backed submarine results without manually building and operating OpenFOAM cases.
**Current focus:** Phase 5 - Experiment Ops and Reproducibility

## Current Position

**Current Phase:** 05
**Current Phase Name:** experiment ops and reproducibility
**Total Phases:** 6
**Current Plan:** Not started
**Total Plans in Phase:** 3
**Status:** Ready to plan
**Progress:** [####--] 67%
**Last Activity:** 2026-04-02
**Last Activity Description:** Phase 4 complete, transitioned to Phase 05

Phase: 5 of 6 (Experiment Ops and Reproducibility)
Plan: Not started
Status: Ready to plan
Last activity: 2026-04-02

## Performance Metrics

**Velocity:**

- Total plans completed: 12
- Average duration: ~64 min
- Total execution time: ~12.7 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3 | ~60 min | ~20 min |
| 2 | 3 | ~2.7 hours | ~54 min |
| 3 | 3 | ~4.7 hours | ~94 min |
| 4 | 3 | ~4.5 hours | ~90 min |

**Recent Trend:**

- Last 5 plans: 03-02, 03-03, 04-01, 04-02, 04-03
- Trend: Positive

## Decisions Made

| Phase | Summary | Rationale |
|-------|---------|-----------|
| 1 | Phase 1 had to fix the dedicated submarine workbench path instead of redirecting users to generic chat as a workaround. | The product promise is a dedicated research cockpit, so the real user entry path must work natively. |
| 1 | Research usability is defined by evidence-backed claim levels, not merely by producing artifacts or running OpenFOAM. | The audit showed that runtime success alone can still yield scientifically unusable outputs. |
| 2 | DeerFlow remains the only acceptable researcher-facing runtime path for submarine CFD execution. | Splitting execution into ad-hoc shell flows would break traceability, runtime recovery, and cockpit visibility. |
| 2 | `runtime_status` is the authoritative workbench-level runtime truth, while `current_stage` and `stage_status` stay responsible for per-stage detail. | This keeps refresh-safe recovery logic deterministic and prevents the frontend from reconstructing runtime truth from stage order alone. |
| 3 | The actual researcher-facing workbench must consume scientific summaries from the active pipeline stage cards, not only from reusable helper panels. | Browser validation showed the mounted UI path had diverged from the helper panel path. |
| 3 | Benchmark references that do not match the current run condition must remain visible as explicit `not_applicable` evidence and claim-limiting advice. | Missing or mismatched references are scientifically meaningful and should not disappear from the claim narrative. |
| 4 | Geometry trust must be a structured contract that gates solver inputs, not a prose-only preflight note. | Raw STL heuristics were too easy to over-trust without explicit findings and confirmation state. |
| 4 | Researcher approval is a pre-compute execution gate and must stay separate from post-compute scientific claim labels. | Approval authorizes execution only; it should not masquerade as validation or claim readiness. |

## Pending Todos

- Investigate `useThreads()` callers that still trigger `POST /threads/search` on some `/workspace/chats/[thread_id]?mock=true` loads.
- Capture or generate a live non-mock SCI-03 thread with a benchmark-matched or cited validation condition, so browser validation can move from deterministic mock data to a fresh runtime artifact set.

## Blockers

- Phase 5 is not planned yet, so experiment provenance, baseline-vs-variant reproducibility, and environment consistency are still roadmap debt rather than active implementation.

## Session

**Last Date:** 2026-04-02T07:57:53.486Z
**Stopped At:** Phase 5 context gathered
**Resume File:** .planning/phases/05-experiment-ops-and-reproducibility/05-CONTEXT.md
