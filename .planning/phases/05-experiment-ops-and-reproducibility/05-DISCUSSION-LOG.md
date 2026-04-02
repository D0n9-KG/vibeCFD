# Phase 5: Experiment Ops and Reproducibility - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md; this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 05-experiment-ops-and-reproducibility
**Areas discussed:** Provenance package, Variant scope and control, Workbench scope, Environment consistency policy

---

## Provenance package

| Option | Description | Selected |
|--------|-------------|----------|
| A | Add a single authoritative provenance manifest per run that captures geometry identity, case/template, solver settings, approval snapshot, environment fingerprint, and canonical artifact entrypoints. | Yes |
| B | Keep relying on multiple separate artifacts and let reporting/frontend reconstruct provenance as needed. | |
| C | Other | |

**User's choice:** A
**Notes:** The user wants one clear rerun/audit entrypoint rather than making downstream tooling infer provenance from multiple files.

---

## Variant scope and control

| Option | Description | Selected |
|--------|-------------|----------|
| A | Phase 5 only productizes the current deterministic scientific-study variants. | |
| B | Allow researchers to add manual/custom variants inside the same experiment while preserving baseline linkage and compare lineage. | Yes |
| C | Other | |

**User's choice:** B
**Notes:** The current deterministic scientific-study path should remain valid, but the experiment layer must also support user-authored variants.

---

## Workbench scope

| Option | Description | Selected |
|--------|-------------|----------|
| A | Keep experiment/provenance visibility inside the current runtime panel and reporting surfaces with minimal productization. | |
| B | Build a more explicit experiment-ops view/panel as part of Phase 5. | |
| C | Other | Yes |

**User's choice:** Other
**Notes:** The user said the current frontend effect/quality feels weak and wants a separate future frontend rebuild. For Phase 5, that means avoid a full UI overhaul now and keep any required reproducibility UI changes minimal.

---

## Environment consistency policy

| Option | Description | Selected |
|--------|-------------|----------|
| A | Drift only produces a warning and does not affect reproducibility status. | |
| B | Drift does not block execution, but it downgrades reproducibility status and must be surfaced explicitly. | Yes |
| C | Drift blocks execution. | |
| D | Other | |

**User's choice:** B
**Notes:** The user wanted clarification on what environment consistency means and then chose the middle path: keep execution moving, but do not overstate reproducibility when runtime conditions drift.

---

## the agent's Discretion

- Exact provenance-manifest field schema and file location.
- Exact custom-variant authoring UX inside the existing cockpit.
- Exact reproducibility-status wording and badge taxonomy.
- Exact compact UI placement for experiment/provenance summaries before the later standalone frontend rebuild.

## Deferred Ideas

- Full submarine cockpit/frontend redesign as a separate future phase or workstream.
- Dedicated experiment-ops pages or richer compare dashboards after the reproducibility contract is stable.
