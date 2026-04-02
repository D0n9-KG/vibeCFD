# Phase 5: Experiment Ops and Reproducibility - Research

**Researched:** 2026-04-02
**Domain:** Reproducible run provenance, baseline-versus-variant experiment operations, and environment-parity enforcement over the existing DeerFlow submarine runtime
**Confidence:** MEDIUM

<user_constraints>
## User Constraints

- `OPS-01`: every run must record reproducible provenance for geometry, case template, solver settings, runtime environment, and outputs.
- `OPS-02`: baseline-versus-variant studies must be traceable as first-class experiment artifacts.
- `OPS-03`: runtime configuration must stay consistent across local dev, Docker Compose, and deployed environments.
- Every run should emit one authoritative provenance manifest instead of forcing downstream tools to reconstruct rerunability from multiple files.
- The experiment layer must support user-added custom variants inside the same experiment, not only the pre-defined mesh/domain/time-step variants.
- Phase 5 should keep UI changes minimal and stay inside the existing cockpit/report surfaces; a larger frontend rebuild is explicitly deferred.
- Environment drift should not block execution by default, but it must downgrade reproducibility status and be surfaced explicitly.

</user_constraints>

<research_summary>
## Summary

Phase 5 does not need a brand-new experiment system. The repository already contains most of the evidence-layer building blocks:

- typed study and experiment contracts in `models.py`,
- deterministic study planning in `studies.py`,
- run-record and compare-summary builders in `experiments.py`,
- linkage assessment in `experiment_linkage.py`,
- experiment and compare summaries in `reporting_summaries.py`,
- research-evidence provenance scoring in `evidence.py`,
- compact experiment rendering in the submarine runtime panel.

The real gap is not missing concepts, but missing productization around three weak seams:

1. **No single rerun entrypoint exists yet.**
   The system writes `openfoam-request.json`, `solver-results.json`, `study-manifest.json`, `experiment-manifest.json`, and `run-compare-summary.json`, but another tool or researcher still has to infer which one is the canonical provenance record.

2. **The experiment model is still optimized for deterministic scientific-study variants only.**
   `studies.py` and `experiment_linkage.py` assume the planned variants come from the built-in mesh/domain/time-step workflows. That works for Phase 3 evidence, but it does not yet support the user's requested "same experiment, but with manual/custom variants" workflow cleanly.

3. **Environment parity is discussed in docs and compose files, but not captured as run-level evidence.**
   Local, dev-compose, and deployed runtime paths already differ in mount strategy, env variable names, and container wiring. Today the reporting layer can say whether experiment/study artifacts are traceable, but it cannot yet say whether the run was executed under a parity-matched environment.

The most effective decomposition is therefore:

- `05-01`: create a unified provenance manifest and persist run-level reproducibility metadata;
- `05-02`: extend the experiment layer so baseline, deterministic study variants, and user-defined variants share one explicit registry and compare contract;
- `05-03`: introduce environment fingerprinting, parity evaluation, drift reporting, and operator recovery guidance across local/dev-compose/deployment paths.

</research_summary>

<existing_capabilities>
## Existing Capabilities We Can Reuse

### Experiment and compare contracts already exist

- `backend/packages/harness/deerflow/domain/submarine/models.py`
  - already defines `SubmarineExperimentManifest`,
  - `SubmarineExperimentRunRecord`,
  - `SubmarineRunComparison`,
  - `SubmarineRunCompareSummary`,
  - and `SubmarineResearchEvidenceSummary`.
- `backend/packages/harness/deerflow/domain/submarine/experiments.py`
  - already derives deterministic `experiment_id` and `run_id`,
  - builds run records,
  - extracts metric snapshots,
  - and creates compare summaries.
- `backend/packages/harness/deerflow/domain/submarine/experiment_linkage.py`
  - already audits whether expected study variants have run records and compare coverage.

### Solver dispatch already emits a substantial evidence chain

- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
  - already writes `openfoam-request.json`,
  - `solver-results.json`,
  - `study-plan.json`,
  - `study-manifest.json`,
  - `experiment-manifest.json`,
  - `run-record.json`,
  - `run-compare-summary.json`,
  - and the standard artifact bundle.
- `backend/packages/harness/deerflow/domain/submarine/artifact_store.py`
  - already centralizes canonical artifact path resolution, so Phase 5 can add a provenance entrypoint without inventing a separate storage pattern.

### Reporting and cockpit surfaces already consume structured experiment data

- `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - already synthesizes final report payloads from artifacts, study summaries, experiment summaries, and evidence summaries.
- `backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py`
  - already joins `experiment-manifest.json` and `run-compare-summary.json` into UI-ready summary blocks.
- `backend/packages/harness/deerflow/domain/submarine/evidence.py`
  - already computes provenance status as `traceable`, `partial`, or `missing`.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - already parses scientific-study, experiment-summary, and experiment-compare payloads into workbench view models.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - already renders compact experiment and compare sections without needing a new route.

### Runtime persistence model is already compatible with Phase 5

- `backend/packages/harness/deerflow/agents/thread_state.py`
  - already preserves `artifact_virtual_paths`, `execution_plan`, `activity_timeline`, and other runtime snapshot fields across concurrent graph updates.
- `backend/packages/harness/deerflow/domain/submarine/contracts.py`
  - already models `scientific-study` and `experiment-compare` as explicit execution-plan stages.

</existing_capabilities>

<code_level_findings>
## Code-Level Findings That Matter For Planning

### Finding 1: provenance is currently inferred, not declared

`solver_dispatch.py` already writes many of the right artifacts, but there is no single `provenance-manifest.json` or equivalent canonical record tying together:

- geometry identity,
- selected case/template,
- simulation requirements,
- requested outputs,
- approval state,
- environment fingerprint,
- experiment/study manifest entrypoints,
- and report entrypoints.

This is the biggest blocker for `OPS-01`.

### Finding 2: provenance scoring currently ignores environment parity

`evidence.py` computes provenance status using the presence and completeness of:

- final report entrypoints,
- experiment manifest and compare summary,
- study manifest,
- delivered outputs,
- core verification artifacts.

That is useful, but it does not yet incorporate:

- runtime environment fingerprint,
- parity match / drift level,
- config provenance,
- or compose-vs-deployment divergence.

Today a run can look "traceable" even if it was produced under a drifted environment with no explicit parity evidence.

### Finding 3: experiment linkage is strict for planned scientific-study variants, but custom variants are not first-class yet

`experiment_linkage.py` derives expected variant ids from `study-manifest.json` and then flags:

- missing run records,
- missing compare entries,
- orphan compare entries,
- additional run ids not present in the planned study manifest.

This is excellent for deterministic scientific-study workflows, but if we add user-authored custom variants, those extra run ids will currently look like anomalies rather than supported experiment members. Phase 5 must expand the contract so "custom but valid" does not get treated as "unplanned and suspicious."

### Finding 4: the cockpit can already show experiment summaries, but not a dedicated reproducibility contract

The frontend already understands:

- experiment id,
- baseline run id,
- compare counts,
- linkage issues,
- planned/completed/blocked variant coverage,
- compare artifact entrypoints.

What it does not yet receive is a compact provenance summary that answers:

- which file is the canonical rerun entrypoint,
- whether the environment matched a supported parity profile,
- why this run is fully reproducible versus only partially reproducible,
- and what the operator should do when drift exists.

### Finding 5: local/dev/deployed runtime paths are intentionally similar but not actually normalized

`docker/docker-compose-dev.yaml` and `docker/docker-compose.yaml` both wire the same product, but they differ in important ways:

- dev uses bind-mounted source trees and `DEER_FLOW_ROOT`,
- production uses mounted config paths and `DEER_FLOW_HOME`,
- dev and prod mount different paths for backend/frontend assets and logs,
- both rely on Docker socket plus `host.docker.internal`, but with slightly different environment setups,
- the sandbox image contract is documented in `docker/openfoam-sandbox/README.md`, not yet captured per run.

Phase 5 therefore should not promise "all environments are identical." It should promise:

- the system knows what environment it actually ran under,
- it can compare that against supported parity targets,
- and it can downgrade reproducibility honestly when drift exists.

### Finding 6: the Phase 5 seams already sit in a small set of crowded, reusable modules

Phase 4 is now committed cleanly, and the remaining reproducibility work still concentrates in a predictable set of modules:

- `models.py`,
- `artifact_store.py`,
- `experiments.py`,
- `experiment_linkage.py`,
- `solver_dispatch.py`,
- `evidence.py`,
- `reporting.py`,
- `reporting_summaries.py`,
- `submarine-runtime-panel.*`,
- related backend/frontend tests.

That suggests the plan should avoid broad new subsystem creation and instead tighten these existing hotspots with explicit contracts, tests, and parity rules.

</code_level_findings>

<gaps>
## Product Gaps That Still Block Research-Usable Behavior

### Gap 1: No single provenance entrypoint for reruns

The product still makes a human or downstream tool inspect multiple artifacts to answer "what exactly was run and how do I rerun it?"

### Gap 2: No first-class support for custom experiment variants

The experiment layer is mature enough for deterministic built-in study variants, but not yet for user-defined/manual variants inside the same experiment boundary.

### Gap 3: No run-level environment fingerprint and parity decision

There is no canonical artifact or report field that says whether the run used:

- a known local path,
- dev compose path,
- deployment path,
- or a drifted/partially known environment.

### Gap 4: Failure recovery guidance is not tied to reproducibility drift

The runtime can already surface blocked/failed status, but it does not yet tell the operator whether the remedy is:

- regenerate provenance,
- fix manifest coverage,
- re-run under a parity-matched environment,
- or accept downgraded reproducibility.

### Gap 5: minimal cockpit visibility still lacks a reproducibility-specific summary

The workbench can show experiment and compare summaries, but not yet a crisp reproducibility block with:

- provenance-manifest path,
- parity status,
- drift reasons,
- rerun prerequisites,
- and recovery guidance.

</gaps>

<recommended_decomposition>
## Recommended Plan Decomposition

### 05-01: Persist full run provenance and reproducibility metadata

Scope:

- introduce a unified provenance manifest artifact,
- capture geometry/case/settings/outputs/approval/environment entrypoints in one place,
- persist runtime pointers to the provenance manifest,
- add tests proving the manifest is complete enough for rerunability.

Why first:

- it creates the canonical contract that both experiment ops and environment parity must build on,
- it satisfies the user's strongest decision: one authoritative provenance entrypoint.

### 05-02: Productize experiment manifests, custom variants, and comparison summaries

Scope:

- support user-authored/custom variants inside the experiment registry,
- update linkage logic to distinguish valid custom variants from broken coverage,
- preserve baseline-versus-variant compare summaries as first-class artifacts,
- surface complete experiment coverage through reporting and the existing cockpit.

Why second:

- the experiment layer already exists, but it needs contract widening rather than reinvention,
- custom variants should plug into the same provenance and compare chain created in `05-01`.

### 05-03: Align runtime configuration and environment parity with recovery guidance

Scope:

- fingerprint supported runtime environments,
- compare actual run environment against known parity profiles,
- downgrade reproducibility when drift exists,
- expose operator-facing recovery guidance in report/runtime surfaces,
- align docs and config references across local/dev-compose/production paths.

Why third:

- the parity decision should attach to the provenance manifest created in `05-01`,
- the experiment layer in `05-02` should already be stable before parity logic decides whether the resulting evidence chain is fully reproducible.

</recommended_decomposition>

<architecture_guidance>
## Architecture Guidance

### Backend ownership

- `solver_dispatch.py`
  - should remain the primary writer for per-run provenance and experiment artifacts,
  - but should delegate formatting and path helpers to focused domain helpers where possible.
- `models.py`
  - should own typed provenance contracts and any explicit parity status enums.
- `artifact_store.py`
  - should own canonical virtual-path helpers for the new provenance artifact.
- `experiment_linkage.py`
  - should evolve from "planned deterministic study completeness" into "experiment membership integrity," including supported custom variants.
- `evidence.py` and `reporting.py`
  - should consume parity status and provenance-manifest entrypoints instead of inferring reproducibility from artifact presence alone.

### Frontend ownership

- `submarine-runtime-panel.contract.ts`
  - should add explicit payload types for provenance summary and parity status.
- `submarine-runtime-panel.utils.ts`
  - should format provenance/parity summaries into compact cockpit sections.
- `submarine-runtime-panel.tsx`
  - should render the minimal reproducibility surface inside the existing panel, not a new page.

### Environment-parity modeling

Treat parity as a supported-profile comparison, not a naive byte-for-byte match.

Recommended normalized statuses:

- `matched`
- `drifted_but_runnable`
- `unknown`
- `blocked`

Recommended semantics:

- `matched`: known supported profile; reproducibility may stay full if other evidence is complete.
- `drifted_but_runnable`: execution allowed, but reproducibility is downgraded.
- `unknown`: insufficient environment evidence was recorded; reproducibility cannot be claimed strictly.
- `blocked`: environment is unsupported for the requested run or known to violate a hard requirement.

</architecture_guidance>

<validation_architecture>
## Validation Architecture

### Automated backend validation

- `backend/tests/test_submarine_solver_dispatch_tool.py`
  - verify a solver-dispatch run writes a provenance manifest with geometry, case, settings, outputs, approval, and environment fields.
- `backend/tests/test_thread_state_reducers.py`
  - verify runtime snapshot merging preserves provenance-manifest paths and reproducibility-related runtime fields.
- `backend/tests/test_submarine_experiment_linkage_contracts.py`
  - verify custom variants can belong to the same experiment without being misclassified as broken linkage.
- `backend/tests/test_submarine_result_report_tool.py`
  - verify final report payloads expose provenance summary, parity status, and recovery guidance.

### Automated frontend validation

- `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - verify provenance/parity summaries and experiment coverage formatting.
- `frontend/src/components/workspace/submarine-pipeline-runs.test.ts`
  - verify run collections keep baseline and variant linkage readable in the cockpit.
- `frontend/src/components/workspace/submarine-pipeline-status.test.ts`
  - verify reproducibility downgrade language is distinct from scientific claim-level language.

### Manual validation

Use one baseline run and at least one custom variant to confirm:

1. the cockpit exposes a single provenance entrypoint;
2. baseline, built-in scientific-study variants, and custom variants all appear under one experiment boundary;
3. a local run under a parity-matched profile can be marked fully reproducible when other evidence is complete;
4. a drifted compose/deployment run remains executable but is visibly downgraded and accompanied by recovery guidance.

</validation_architecture>

<risks>
## Key Risks

- `solver_dispatch.py` is already a crowded orchestration file. Phase 5 should avoid embedding all new logic inline without helper extraction.
- Custom variants can accidentally undermine experiment-linkage checks if the registry contract is widened carelessly.
- Environment parity can become too strict and block ordinary development work if the plan confuses "known drift" with "unsafe to run."
- Reporting and cockpit wording can accidentally conflate reproducibility downgrade with scientific claim downgrade if parity and claim-level summaries are mixed.
- The main Phase 5 modules are already crowded and highly connected, so executors must read current file state carefully and avoid shallow inline changes that create more drift.

</risks>

<canonical_refs>
## Canonical References

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/phases/05-experiment-ops-and-reproducibility/05-CONTEXT.md`
- `.planning/phases/05-experiment-ops-and-reproducibility/05-UAT.md`
- `.planning/phases/05-experiment-ops-and-reproducibility/05-VERIFICATION.md`
- `docs/archive/superpowers/specs/2026-03-28-scientific-study-orchestration-v1-design.md`
- `docs/archive/superpowers/specs/2026-03-28-experiment-registry-run-compare-design.md`
- `docs/archive/superpowers/specs/2026-03-28-experiment-compare-workbench-v1-design.md`
- `docs/archive/superpowers/specs/2026-03-28-unified-research-evidence-chain-design.md`
- `backend/packages/harness/deerflow/domain/submarine/models.py`
- `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- `backend/packages/harness/deerflow/domain/submarine/artifact_store.py`
- `backend/packages/harness/deerflow/domain/submarine/experiments.py`
- `backend/packages/harness/deerflow/domain/submarine/experiment_linkage.py`
- `backend/packages/harness/deerflow/domain/submarine/studies.py`
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- `backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py`
- `backend/packages/harness/deerflow/domain/submarine/evidence.py`
- `backend/packages/harness/deerflow/agents/thread_state.py`
- `backend/tests/test_submarine_solver_dispatch_tool.py`
- `backend/tests/test_submarine_experiment_linkage_contracts.py`
- `backend/tests/test_submarine_result_report_tool.py`
- `backend/tests/test_thread_state_reducers.py`
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`
- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- `frontend/src/components/workspace/submarine-pipeline-runs.ts`
- `frontend/src/components/workspace/submarine-pipeline-status.ts`
- `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
- `docker/docker-compose-dev.yaml`
- `docker/docker-compose.yaml`
- `docker/openfoam-sandbox/README.md`
- `config.yaml`
- `.env.example`

</canonical_refs>

<deferred>
## Deferred Ideas

- A full submarine cockpit redesign remains a separate future phase or workstream.
- A dedicated experiment manager page or cross-thread compare dashboard remains future work after the reproducibility contract is stable.
- Global multi-project experiment registries remain out of scope for this phase.
- Strict execution blocking on every drift condition is deferred; Phase 5 should prefer transparent downgrade plus recovery guidance.

</deferred>

---

*Phase: 05-experiment-ops-and-reproducibility*
*Research refreshed: 2026-04-02*
