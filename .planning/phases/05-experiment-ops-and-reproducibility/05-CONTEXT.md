# Phase 5: Experiment Ops and Reproducibility - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Give researchers a reproducible submarine-study system with clear run provenance, explicit baseline-versus-variant linkage, and visible environment consistency across local, Docker Compose, and deployed runtime paths.

Phase 5 productizes the experiment/evidence layer that already exists in partial form. It should make every run rerunnable, every experiment traceable, and every environment drift visible without turning the submarine cockpit into a rigid workflow shell or bundling a full frontend redesign into this phase.

</domain>

<decisions>
## Implementation Decisions

### Provenance package
- **D-01:** Every run should emit a single authoritative provenance manifest as the reproducibility entrypoint for reruns and audits.
- **D-02:** The provenance manifest should capture geometry identity, selected case/template, solver settings, requested outputs, approval snapshot, environment fingerprint, and canonical artifact entrypoints instead of forcing downstream consumers to reconstruct provenance from scattered files.
- **D-03:** Existing solver-dispatch, study, compare, and reporting artifacts remain part of the evidence chain, but the new provenance manifest becomes the one-file index that links them together.

### Variant scope and experiment structure
- **D-04:** Phase 5 should support user-added custom variants inside the same experiment rather than limiting the experiment layer to the pre-defined scientific-study variants only.
- **D-05:** Custom variants must still be recorded as first-class experiment members with explicit linkage to the baseline run and with the same compare/provenance lineage as deterministic study variants.
- **D-06:** The existing mesh/domain/time-step study orchestration remains the default standard path; custom variants extend the experiment model rather than replacing the current scientific-study flow.

### Workbench scope for this phase
- **D-07:** Phase 5 should keep provenance and experiment visibility inside the existing runtime panel and reporting surfaces with only the minimal productization needed for reproducibility workflows.
- **D-08:** A full frontend page overhaul is intentionally out of scope for Phase 5 and should be handled as a separate future phase or workstream.

### Environment consistency policy
- **D-09:** Environment drift across local, Docker Compose, and deployed runtime paths should not block execution by default.
- **D-10:** Environment drift must downgrade reproducibility status and be surfaced explicitly; a drifted run must not be presented as strictly reproducible.
- **D-11:** Phase 5 should record per-run environment fingerprints and parity assessments so reports and the cockpit can explain why a run is fully reproducible versus only partially reproducible.

### the agent's Discretion
- Exact field schema and file naming for the provenance manifest, as long as it remains the single rerun/audit entrypoint.
- Exact custom-variant authoring flow, so long as baseline linkage and compare lineage stay explicit.
- Exact reproducibility-status labels and wording, so long as drift clearly downgrades the result without hiding the issue.
- Exact placement of compact provenance and experiment summaries inside the current cockpit surfaces.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and phase anchors
- `.planning/PROJECT.md` - core product promise, runtime constraints, and the Phase 5 bottleneck statement around reproducibility.
- `.planning/REQUIREMENTS.md` - `OPS-01`, `OPS-02`, and `OPS-03` define the concrete phase scope.
- `.planning/ROADMAP.md` - Phase 5 goal, success criteria, and plan split (`05-01` to `05-03`).
- `.planning/STATE.md` - current project position and the handoff from completed Phase 4 work.

### Prior phase decisions that still constrain Phase 5
- `.planning/phases/02-runtime-solver-productization/02-CONTEXT.md` - thread-bound geometry, persisted runtime state, and artifact paths remain the runtime truth model.
- `.planning/phases/04-geometry-and-case-intelligence-hardening/04-CONTEXT.md` - researcher approval remains explicit and separate from post-compute scientific claim labels.

### Experiment and scientific-study design references
- `docs/archive/superpowers/specs/2026-03-28-scientific-study-orchestration-v1-design.md` - deterministic study-manifest and variant-orchestration design that Phase 5 must extend rather than replace.
- `docs/archive/superpowers/specs/2026-03-28-experiment-registry-run-compare-design.md` - intended experiment registry, run-record, and baseline-versus-variant compare contract.
- `docs/archive/superpowers/specs/2026-03-28-experiment-compare-workbench-v1-design.md` - current guidance for compact compare visibility in reporting and the workbench.
- `docs/archive/superpowers/specs/2026-03-28-unified-research-evidence-chain-design.md` - provenance and research-evidence-chain expectations that Phase 5 should complete.

### Backend contracts and artifact flow
- `backend/packages/harness/deerflow/domain/submarine/models.py` - typed experiment, compare, provenance-status, and study contracts.
- `backend/packages/harness/deerflow/domain/submarine/studies.py` - deterministic scientific-study manifest generation and workflow status rules.
- `backend/packages/harness/deerflow/domain/submarine/experiments.py` - experiment ids, run ids, run records, metric snapshots, and compare-summary builders.
- `backend/packages/harness/deerflow/domain/submarine/experiment_linkage.py` - consistency checks between study manifests, experiment manifests, and compare coverage.
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` - current artifact emission path for study plans, experiment manifests, baseline run records, and compare summaries.
- `backend/packages/harness/deerflow/domain/submarine/artifact_store.py` - canonical artifact virtual-path strategy and loader helpers.
- `backend/packages/harness/deerflow/domain/submarine/reporting.py` - final report assembly that should consume the new provenance entrypoint and parity status.
- `backend/packages/harness/deerflow/domain/submarine/evidence.py` - current provenance-status and research-evidence summary logic that Phase 5 should tighten.
- `backend/packages/harness/deerflow/agents/thread_state.py` - persisted `submarine_runtime` merge semantics and artifact-path persistence.
- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - execution-plan/runtime snapshot contract that already includes scientific-study and experiment-compare stages.

### Environment consistency and runtime-path references
- `config.yaml` - active sandbox/runtime configuration used by the current local system.
- `docker/docker-compose-dev.yaml` - development runtime path and environment wiring.
- `docker/docker-compose.yaml` - production/deployed runtime path and environment wiring.
- `docker/openfoam-sandbox/README.md` - canonical OpenFOAM sandbox image build and verification instructions.
- `backend/packages/harness/deerflow/config/sandbox_config.py` - sandbox configuration model and mount/environment contract.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/packages/harness/deerflow/domain/submarine/experiments.py`: already provides deterministic experiment ids, run ids, run records, metric snapshots, and compare-summary builders.
- `backend/packages/harness/deerflow/domain/submarine/studies.py`: already models the baseline scientific-study path for mesh/domain/time-step variants.
- `backend/packages/harness/deerflow/domain/submarine/experiment_linkage.py`: already detects missing run records, missing compare entries, and broken experiment coverage.
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`: already emits `study-manifest.json`, `experiment-manifest.json`, `run-record.json`, and `run-compare-summary.json`.
- `backend/packages/harness/deerflow/domain/submarine/reporting.py` plus `reporting_summaries.py`: already pull experiment/study information into final-report payloads and research-evidence summaries.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts` and `frontend/src/components/workspace/submarine-runtime-panel.tsx`: already parse and render compact scientific-study and experiment-compare summaries in the cockpit.

### Established Patterns
- The system favors flexible user intent with structured evidence artifacts behind the scenes; Phase 5 should extend that pattern instead of introducing a rigid experiment wizard.
- Artifact identity is virtual-path based (`/mnt/user-data/outputs/...`) rather than raw host-path based.
- Reporting and workbench surfaces are expected to consume stable structured summaries rather than reconstructing semantics from arbitrary files in the frontend.
- `submarine_runtime` plus canonical artifacts remain the persisted truth across refresh and re-entry.

### Integration Points
- Solver dispatch is the natural place to emit the new unified provenance manifest and environment fingerprint for every run.
- Reporting/evidence assembly is the natural place to convert parity findings into reproducibility status and user-facing guidance.
- `submarine_runtime` should expose enough provenance pointers/status for the cockpit to summarize experiment health without a new page architecture.
- Custom variants need to plug into the existing experiment manifest, compare summary, and evidence chain instead of forming a separate side system.

</code_context>

<specifics>
## Specific Ideas

- The user wants a single provenance entrypoint instead of forcing future tooling to infer rerunability from scattered artifacts.
- The user explicitly wants manual/custom variants to be possible within the same experiment, not only the deterministic mesh/domain/time-step set.
- The user is unhappy with the current frontend quality and wants a later dedicated frontend rebuild, but does not want that redesign to absorb Phase 5.
- The user prefers scientific honesty over hard blocking: environment drift should be visible and should downgrade reproducibility, but it should not stop execution by default.

</specifics>

<deferred>
## Deferred Ideas

- Full submarine cockpit/frontend redesign should be handled as a dedicated future phase or workstream, not bundled into Phase 5.
- A larger experiment-ops surface or dedicated compare dashboard remains future work after the reproducibility contracts are stable.
- Global multi-experiment browsing and cross-thread experiment management remain out of scope for this phase.

</deferred>

---

*Phase: 05-experiment-ops-and-reproducibility*
*Context gathered: 2026-04-02*
