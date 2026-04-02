# Phase 6: Research Delivery Workbench - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 06-research-delivery-workbench
**Areas discussed:** report package shape, supervisor decision surface, evidence traceability, follow-up loop

---

## Report Package Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Delivery-summary | Lead with an executive-style delivery summary and move technical evidence later. | |
| Evidence-indexed technical report | Lead with evidence structure and make the report primarily a technical audit trail. | |
| Hybrid Chinese report | Conclusion-first Chinese report with readable summary plus evidence-backed detail. | x |

**User's choice:** Hybrid Chinese report.
**Notes:** Follow-up clarifications locked the report into a conclusion-first structure with a two-layer summary. Layer 1 should show the current conclusion, allowed claim level, review/supervisor status, reproducibility status, and recommended next step. Layer 2 should show key metrics and representative figures. The main body should be organized by conclusion, and the report should end with a full evidence index.

---

## Supervisor Decision Surface

| Option | Description | Selected |
|--------|-------------|----------|
| Status-summary only | Show gate status and notes, but keep actions elsewhere. | |
| Action-first review panel | Put approve/block/rerun/extend actions directly in a dedicated workbench panel. | |
| Heavy workflow review flow | Add a stronger staged review/approval flow. | |

**User's choice:** None of the original panel-heavy options as the final direction.
**Notes:** The user clarified that the project should not focus on a separate approval surface. Instead, the system should output a conclusion package with sources, confidence, claim level, and gaps, and then the main agent should continue in chat to ask whether the task is complete, whether more evidence is needed, or whether setup/parameter issues should be corrected. The workbench should remain a lightweight visibility surface rather than a button-heavy approval tool.

---

## Evidence Traceability

| Option | Description | Selected |
|--------|-------------|----------|
| Inline-only | Put all sources directly next to each conclusion with no separate index. | |
| Index-only | Keep the main narrative short and move traceability to a shared evidence index. | |
| Inline summary + full index | Include short source/confidence notes next to each conclusion and keep a full evidence index at the end. | x |

**User's choice:** Inline summary plus a full index.
**Notes:** The user wants each conclusion to state its sources and confidence directly, but does not want the whole report to turn into a raw artifact dump. A complete artifact/evidence index should still exist at the end for audit and deep review.

---

## Follow-Up Loop

| Option | Description | Selected |
|--------|-------------|----------|
| Advice only | Suggest next steps in prose but do not structure follow-up state. | |
| Chat-driven plus structured history | Let the main agent drive follow-up in chat and persist the resulting decision lineage as structured follow-up history. | x |
| Autonomous loop | Automatically keep rerunning and refreshing until evidence is sufficient. | |

**User's choice:** Chat-driven follow-up with structured history.
**Notes:** The follow-up loop should capture why the work is continuing and whether the next step is more evidence, parameter/setup correction, study extension, or task completion. It should preserve lineage between the prior report and any rerun/refreshed artifacts, but remain bounded and user-confirmed rather than autonomous.

---

## the agent's Discretion

- Exact report section labels and UI microcopy.
- Exact formatting of inline source tags and the end-of-report evidence index.
- Exact field names for stored follow-up history, as long as decision reason and lineage stay explicit.

## Deferred Ideas

- Standalone approval dashboard with direct approve/block/rerun/extend controls.
- Full frontend redesign for the submarine cockpit.
- Autonomous repeated rerun loops without user confirmation.
