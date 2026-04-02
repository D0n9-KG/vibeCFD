---
phase: 06
slug: research-delivery-workbench
status: ready_for_planning
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-01
updated: 2026-04-03
---

# Phase 06 - Validation Strategy

## Validation Goal

Prove that Phase 6 finishes the researcher-facing delivery loop without losing scientific honesty or provenance traceability.

The validation target is not only "a report exists", but:

- the final report is readable in Chinese and led by conclusions rather than raw dumps,
- supervisor review exposes truthful next-step choices without collapsing into a button-heavy approval shell,
- follow-up actions stay bounded and auditable,
- conclusions, evidence groups, and provenance anchors remain navigable from the same cockpit contract.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` + Node test runner + TypeScript typecheck |
| **Config file** | `backend/pyproject.toml`, `frontend/package.json`, `frontend/tsconfig.json` |
| **Quick run command** | `cd backend && uv run pytest tests/test_submarine_result_report_tool.py tests/test_submarine_scientific_followup_tool.py && cd ../frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-status.test.ts && corepack pnpm typecheck` |
| **Full suite command** | `cd backend && uv run pytest tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_artifact_store.py tests/test_thread_state_reducers.py tests/test_submarine_result_report_tool.py tests/test_submarine_scientific_followup_tool.py tests/test_submarine_domain_assets.py tests/test_submarine_experiment_linkage_contracts.py && cd ../frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-runtime-panel.trends.test.ts src/components/workspace/submarine-pipeline-runs.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-pipeline-shell.test.ts && corepack pnpm typecheck` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every reporting contract change:** Run `cd backend && uv run pytest tests/test_submarine_result_report_tool.py`
- **After every follow-up/tool contract change:** Run `cd backend && uv run pytest tests/test_submarine_scientific_followup_tool.py tests/test_submarine_result_report_tool.py`
- **After every cockpit rendering change:** Run `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-status.test.ts`
- **After every plan:** Re-run the quick command
- **Before phase verification:** Re-run the full suite command
- **Max feedback latency:** 120 seconds

---

## Validation Dimensions

### Dimension 1: Chinese Research Delivery Packaging

Must validate:

- final reports lead with conclusion summary and Chinese delivery highlights
- each conclusion includes claim level, confidence, evidence gaps, and linked artifacts
- exports and cockpit rendering stay on one shared report schema

### Dimension 2: Supervisor Decision Truthfulness

Must validate:

- decision status is explicit and separate from `scientific_gate_status`
- ready, evidence-gap, and blocked states surface the right next-step options
- the final choice remains chat-driven rather than hidden behind direct cockpit buttons

### Dimension 3: Bounded Follow-Up Lineage

Must validate:

- follow-up history records kind, decision summary, trigger ids, and refreshed provenance/report anchors
- `task_complete` records closure without dispatching a rerun
- rerun-driven follow-up records one refreshed evidence anchor without recursive auto-looping

### Dimension 4: Artifact Navigation

Must validate:

- conclusions and evidence groups expose the paths needed to inspect the underlying artifacts
- latest report path and latest provenance-manifest path are visible together in the cockpit
- remediation and follow-up summaries keep the operator on one readable decision path

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | RPT-01 | backend report contract | `cd backend && uv run pytest tests/test_submarine_result_report_tool.py` | `backend/tests/test_submarine_result_report_tool.py` | pending |
| 06-01-02 | 01 | 1 | RPT-01 | frontend report summaries | `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts && corepack pnpm typecheck` | `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts` | pending |
| 06-02-01 | 02 | 2 | RPT-02 | backend decision synthesis | `cd backend && uv run pytest tests/test_submarine_result_report_tool.py` | `backend/tests/test_submarine_result_report_tool.py` | pending |
| 06-02-02 | 02 | 2 | RPT-02 | frontend cockpit/pipeline copy | `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-pipeline-status.test.ts && corepack pnpm typecheck` | `frontend/src/components/workspace/submarine-pipeline-status.test.ts` | pending |
| 06-03-01 | 03 | 3 | RPT-02 | backend follow-up lineage | `cd backend && uv run pytest tests/test_submarine_scientific_followup_tool.py tests/test_submarine_result_report_tool.py` | `backend/tests/test_submarine_scientific_followup_tool.py` | pending |
| 06-03-02 | 03 | 3 | RPT-02 | frontend latest-follow-up summary | `cd frontend && node --test src/components/workspace/submarine-runtime-panel.utils.test.ts && corepack pnpm typecheck` | `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts` | pending |

---

## Wave 0 Requirements

Existing reporting, runtime-panel, and follow-up infrastructure already covered the execution skeleton for this phase.

No new top-level page, service, or orchestration runtime was required before execution began.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Chinese report sections remain readable to a researcher | RPT-01 | Requires human judgment on summary density and ordering | Open the final report payload/export and confirm the reader sees conclusion, highlights, evidence, and next steps in that order |
| Decision surfaces stay lightweight and truth-preserving | RPT-02 | Requires reviewing wording and interaction flow, not only payload shape | Open the supervisor review surface and confirm it shows next-step choices while directing the final confirmation back to chat |
| Latest evidence anchor remains navigable after follow-up | RPT-02 | Requires visual inspection of linked report/provenance paths | Trigger one follow-up path, then confirm the runtime panel shows the latest report path and provenance-manifest path together |

---

## Evidence To Capture Before Phase Sign-Off

- one final-report payload with populated `report_overview`, `conclusion_sections`, and `evidence_index`
- one cockpit rendering that shows delivery-decision summary state
- one `scientific-followup-history.json` artifact containing follow-up kind, decision summary, trigger ids, and refreshed provenance anchor
- one runtime summary that shows latest report path plus latest provenance-manifest path together

---

## Exit Criteria

Phase 6 is not ready for execution sign-off until all of the following are true:

- `RPT-01` is backed by a conclusion-first Chinese final-report contract shared by exports and cockpit rendering
- `RPT-02` is backed by truthful supervisor decision surfaces plus bounded follow-up lineage
- follow-up never auto-loops beyond one explicit user-confirmed step
- conclusions, evidence groups, and provenance anchors remain inspectable from the workbench
- `nyquist_compliant: true` remains valid because every task maps to deterministic automated checks or explicit manual verification
