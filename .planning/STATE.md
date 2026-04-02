---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 06
current_phase_name: research delivery workbench
current_plan: Not started
status: planning
stopped_at: Phase 6 context gathered
last_updated: "2026-04-02T13:47:19.039Z"
last_activity: 2026-04-02
progress:
  total_phases: 6
  completed_phases: 5
  total_plans: 15
  completed_plans: 15
  percent: 83
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-04-02)

**Core value:** A researcher can go from natural-language CFD intent to reproducible, evidence-backed submarine results without manually building and operating OpenFOAM cases.
**Current focus:** Phase 06 - research-delivery-workbench

## Current Position

**Current Phase:** 06
**Current Phase Name:** research delivery workbench
**Total Phases:** 6
**Current Plan:** Not started
**Total Plans in Phase:** 3
**Status:** Ready to plan
**Progress:** [#####-] 83%
**Last Activity:** 2026-04-02
**Last Activity Description:** Phase 05 complete, transitioned to Phase 06

Phase: 06 (research-delivery-workbench) - READY TO PLAN
Plan: Not started
Status: Ready to plan Phase 06
Last activity: 2026-04-02 -- Phase 05 complete, transitioned to Phase 06

## Performance Metrics

**Velocity:**

- Total plans completed: 14
- Total plans completed: 15
- Average duration: ~62 min
- Total execution time: ~15.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3 | ~60 min | ~20 min |
| 2 | 3 | ~2.7 hours | ~54 min |
| 3 | 3 | ~4.7 hours | ~94 min |
| 4 | 3 | ~4.5 hours | ~90 min |
| 5 | 3 | ~2.9 hours | ~58 min |

**Recent Trend:**

- Last 5 plans: 04-02, 04-03, 05-01, 05-02, 05-03
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
| 5 | Every solver-dispatch run needs one canonical provenance manifest that survives reducer merges and final reporting. | Researchers need a single rerun and audit entrypoint instead of reconstructing provenance from scattered artifacts. |
| 5 | Custom variants belong in the same experiment manifest and compare chain as baseline and deterministic study variants. | Splitting user-authored variants into side channels would make linkage, reporting, and cockpit lineage inconsistent. |
| 5 | Runtime parity must downgrade reproducibility separately from scientific truth so drift stays operator-honest without corrupting evidence claims. | Environment mismatch affects rerun confidence, not whether benchmark or verification evidence was scientifically observed. |

## Pending Todos

- Investigate `useThreads()` callers that still trigger `POST /threads/search` on some `/workspace/chats/[thread_id]?mock=true` loads.
- Capture or generate a live non-mock SCI-03 thread with a benchmark-matched or cited validation condition, so browser validation can move from deterministic mock data to a fresh runtime artifact set.

## Blockers

- No blocking implementation issues are open for Phase 05. Non-blocking follow-up: `.planning/phases/05-experiment-ops-and-reproducibility/05-UAT.md` still contains pending test placeholders flagged during phase closeout.

## Session

**Last Date:** 2026-04-02T13:47:19.036Z
**Stopped At:** Phase 6 context gathered
**Resume File:** .planning/phases/06-research-delivery-workbench/06-CONTEXT.md
