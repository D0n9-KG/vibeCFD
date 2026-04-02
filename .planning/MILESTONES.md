# Milestones

## v1.0 MVP (Shipped: 2026-04-03)

**Phases completed:** 6 phases, 18 plans, 52 tasks

**Audit:** `tech_debt` (non-blocking follow-up only)

**Key accomplishments:**

- Validated LangGraph bootstrap URLs and serialized the first submarine submit so `/workspace/submarine/new` creates a real thread before upload and stream submission
- Created submarine threads now keep the uploaded STL, first prompt, and workbench identity across route replacement and refresh, with a dedicated rehydration state during reload
- Bootstrap failures now render actionable submarine-cockpit guidance with regression tests, and Windows GBK clarification interrupts no longer collapse into `ask_clarification` tool errors
- Geometry continuity is now stable across fresh submit, thread persistence, and clarification follow-up turns; the remaining Phase 2 work is turning that stable bound geometry into canonical runtime evidence and solver-visible cockpit outputs.
- Canonical runtime evidence now survives dispatch, thread persistence, mock validation, and cockpit rendering through explicit request, log, and results pointers plus delivery-state-aware artifact views.
- Refresh-safe submarine runtime truth now survives backend persistence and frontend re-entry, with explicit blocked, failed, and completed semantics instead of stage-order guesswork.
- SCI-01 stability evidence is now explicit, persisted, and visible across solver dispatch, final reporting, and the submarine cockpit instead of being reconstructed late from raw metrics.
- SCI-02 sensitivity-study workflows are now explicit, claim-limiting, and visible on the real submarine workbench instead of being latent backend artifacts or unused UI contract data.
- Benchmark-backed claim gating is now explicit, citation-aware, and visible in both the final report payload and the real submarine workbench review surfaces.
- Geometry preflight now emits explicit trust artifacts and solver-dispatch respects them instead of turning raw STL heuristics directly into solver reference values.
- The submarine case library now exposes provenance and acceptance-profile honesty directly in ranked-case and final-report payloads instead of hiding weak references behind lexical ranking alone.
- Researchers now get an explicit calculation-plan review gate: ambiguous geometry or case assumptions stay reviewable, clarifiable, and execution-blocking without masquerading as scientific claim-level outcomes.
- Every submarine solver-dispatch run now emits one canonical provenance manifest, and the same manifest pointer survives runtime merges, result reporting, and research-evidence grading.
- One experiment registry now carries baseline, scientific-study variants, and declared custom variants through linkage checks, reporting, and cockpit lineage views.
- Every submarine run now carries an explicit runtime parity verdict, reproducibility downgrade guidance, and aligned runtime-profile vocabulary from backend config through the cockpit.
- Conclusion-first Chinese final-report packaging now ships as one shared backend and frontend contract with inline evidence cues and a provenance-anchored artifact index.
- Supervisor review now emits a structured chat-driven decision contract that surfaces next-step options in the cockpit without collapsing into an approve or rerun control panel.
- Scientific follow-up history now records why the user continued or stopped, which conclusion or evidence gaps triggered that choice, and which refreshed report and provenance pair became the latest evidence anchor.

**Follow-up debt:**

- Capture a fresh live non-mock SCI-03 thread so benchmark claim gating is proven against current runtime artifacts.
- Capture a live non-mock research-delivery thread for the Phase 6 delivery loop.
- Investigate residual `POST /threads/search` calls on some mock workspace loads.

---
