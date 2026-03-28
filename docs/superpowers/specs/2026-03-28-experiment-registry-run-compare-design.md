# Experiment Registry And Run Compare Design

## 1. Purpose

This document defines the next implementation slice after `Scientific Study Orchestration v1`.

The purpose of this slice is to make the current submarine CFD workflow capable of recording a controlled experiment boundary and summarizing run-to-run differences without collapsing the product into a rigid workflow shell.

The scope is intentionally narrow:

- add a lightweight experiment registry for the current solver-dispatch path
- record baseline and scientific-study runs as explicit experiment members
- generate stable compare artifacts from structured solver outputs
- expose a minimal experiment summary in reporting and the workbench

This slice does not attempt to build the final research experiment manager.

## 2. Problem Statement

The repository can now do something important:

- plan scientific studies
- optionally execute study variants
- aggregate `verification-*.json` evidence

But it still lacks an explicit experiment layer.

Today, the system can tell whether a mesh/domain/time-step study passed or failed, yet it still cannot answer some equally important research questions with stable artifacts:

- which runs belong to the same controlled experiment?
- which run is the baseline anchor?
- what changed between baseline and each variant?
- how should the current workbench summarize those differences without scanning arbitrary files?

Without an experiment registry, the platform still relies too heavily on implicit file layout and ad hoc artifact discovery. That is enough for a single slice, but not enough for a research-usable evidence chain.

## 3. Core Design Principle

The system must remain agentic at the user-intent layer and structured at the evidence layer.

This means:

- users should still be able to say "compare the study runs" or "is this experiment stable?" in natural language
- the system should not force users through a dedicated experiment wizard
- once execution begins, the experiment boundary, run roles, and compare outputs must become explicit and reproducible

In practice, this slice continues the same architecture rule:

1. free-form request stays open
2. structured contract resolves intent into selected case and execution mode
3. controlled execution records experiment membership and compare evidence
4. evidence delivery surfaces only structured experiment summaries

## 4. Goals

- Add a lightweight experiment registry for the current solver-dispatch output tree.
- Record baseline and study-variant runs as explicit experiment members.
- Emit stable compare artifacts that describe baseline-versus-variant differences.
- Keep compare scope limited to the current experiment rather than arbitrary global history.
- Surface experiment and compare summaries in the final report and current workbench.

## 5. Non-Goals

- No global multi-project experiment database in this slice.
- No arbitrary selection of any two historical runs across all threads.
- No full compare dashboard or large side-by-side UI.
- No publication-grade comparison figure generation yet.
- No supervisor state-machine overhaul in this slice.

## 6. Scope Boundary

This slice covers the current solver-dispatch execution tree for one experiment rooted in one dispatch directory:

- one selected case
- one baseline run
- zero or more scientific-study variant runs generated from that baseline

The output of this slice should be enough to answer:

- what experiment is this?
- what runs does it contain?
- what role does each run play?
- what differs between baseline and each variant?

It should not yet attempt to unify experiments across unrelated dispatch roots or threads.

## 7. Current System Baseline

The repository already has:

- typed scientific-study contracts in `backend/packages/harness/deerflow/domain/submarine/models.py`
- deterministic study planning and aggregation in `backend/packages/harness/deerflow/domain/submarine/studies.py`
- optional study variant execution in `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- scientific verification summaries in `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- workbench rendering for study summaries in `frontend/src/components/workspace/submarine-runtime-panel.tsx`

What is still missing is a dedicated layer for:

- experiment identity
- run identity
- compare summaries
- stable linkage between raw solver results and higher-level experiment reasoning

## 8. Proposed Architecture

### 8.1 Domain Contracts

The submarine domain should gain explicit experiment contracts.

Recommended additions:

- `SubmarineExperimentRunRole`
  - `baseline`
  - `scientific_study_variant`

- `SubmarineExperimentRunRecord`
  - `run_id`
  - `experiment_id`
  - `study_type` or `None`
  - `variant_id`
  - `run_role`
  - `solver_results_virtual_path`
  - `run_record_virtual_path`
  - selected metric snapshot
  - execution status

- `SubmarineExperimentManifest`
  - `experiment_id`
  - `selected_case_id`
  - `task_type`
  - `baseline_run_id`
  - run membership list
  - artifact paths
  - experiment status

- `SubmarineRunComparison`
  - `baseline_run_id`
  - `candidate_run_id`
  - metric deltas
  - compare status
  - compare notes

- `SubmarineRunCompareSummary`
  - `experiment_id`
  - baseline summary
  - per-run comparisons
  - grouped study comparisons
  - artifact entrypoints

These models should stay in the existing submarine domain layer, not in generic runtime state files.

### 8.2 New Helper Module

This slice should add a focused helper module, recommended path:

- `backend/packages/harness/deerflow/domain/submarine/experiments.py`

Responsibilities:

- deterministic experiment id derivation
- run record construction
- compare summary construction
- metric extraction for compare-ready payloads

This keeps `solver_dispatch.py` from becoming an even larger mixed-responsibility file.

### 8.3 Artifact Strategy

The experiment layer should emit a small, stable artifact set:

- `experiment-manifest.json`
- `run-compare-summary.json`
- root baseline `run-record.json`
- per-variant `run-record.json`

Recommended locations:

- root baseline:
  - `run-record.json`
- root experiment:
  - `experiment-manifest.json`
  - `run-compare-summary.json`
- study variants:
  - `studies/<study>/<variant>/run-record.json`

The existing artifacts remain unchanged and continue to matter:

- `solver-results.json`
- `study-manifest.json`
- `verification-*.json`

The new registry artifacts do not replace raw results. They describe relationships between runs.

### 8.4 Experiment Identity

Experiment identity should be deterministic within the current dispatch root.

For v1, `experiment_id` can be derived from:

- dispatch run directory
- selected case id
- task type

The important property is not global uniqueness across all time. The important property is that all artifacts inside one dispatch root agree on the same experiment identity.

### 8.5 Run Identity

Each run should have a stable `run_id`.

Examples:

- `baseline`
- `mesh_independence:coarse`
- `mesh_independence:fine`
- `domain_sensitivity:compact`
- `time_step_sensitivity:fine`

This id should be used consistently in:

- `run-record.json`
- `experiment-manifest.json`
- `run-compare-summary.json`

### 8.6 Compare Semantics

Compare v1 should remain intentionally small and numeric.

For each non-baseline run, compare against baseline using:

- `Cd`
- `Fx` (x-component of total force)
- `final_time_seconds`
- `mesh_summary.cells`

If a metric is missing, the compare record should preserve that fact explicitly instead of pretending a clean comparison exists.

The compare layer should not make research-readiness decisions by itself. That remains the job of:

- study verification artifacts
- acceptance assessment
- later validation/provenance slices

The compare layer answers a narrower question:

- what changed between baseline and the variant?

### 8.7 Grouped Study Compare Summary

The root `run-compare-summary.json` should provide two views:

1. per-run comparisons
   - each non-baseline run versus baseline

2. grouped study comparisons
   - mesh study summary
   - domain study summary
   - time-step study summary

The grouped summary is meant for the workbench and report.
The per-run summary is meant for deeper inspection and future compare UI work.

### 8.8 Reporting Integration

The final report should gain an `experiment_summary` block.

It should include:

- `experiment_id`
- experiment status
- baseline run id
- run count
- compare artifact paths
- compact per-study compare notes

This summary should be separate from:

- `scientific_study_summary`
- `scientific_verification_assessment`

Those blocks answer different questions.

### 8.9 Workbench Integration

Workbench scope remains intentionally minimal.

The current runtime panel should surface:

- experiment id
- run count
- baseline run id
- compact study compare rows
- links to `experiment-manifest.json` and `run-compare-summary.json`

It should not yet include:

- arbitrary run pickers
- large compare tables
- chart-heavy side-by-side analysis

## 9. User Interaction Model

This slice must not turn the product into a workflow gate.

The intended behavior is:

- quick one-off user requests can still execute baseline-only runs
- if no study execution happens, the experiment registry still records the baseline run cleanly
- if study execution is enabled, experiment membership and compare summaries are generated automatically

That means the experiment registry is not a user-facing ceremony. It is a back-end evidence layer that activates behind current natural-language workflows.

## 10. Data Flow

The intended v1 flow is:

1. Solver-dispatch resolves selected case and simulation requirements.
2. Baseline run executes and writes `solver-results.json`.
3. Baseline `run-record.json` is emitted.
4. If scientific studies execute, each variant writes:
   - `solver-results.json`
   - `run-record.json`
5. The experiment helper builds:
   - `experiment-manifest.json`
   - `run-compare-summary.json`
6. Reporting consumes the experiment summary.
7. The workbench shows the experiment summary and compare artifact links.

## 11. File and Module Strategy

Recommended implementation targets:

- Create `backend/packages/harness/deerflow/domain/submarine/experiments.py`
  - experiment id helpers
  - run record builders
  - compare summary builders

- Modify `backend/packages/harness/deerflow/domain/submarine/models.py`
  - add experiment and compare models

- Modify `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
  - emit run records
  - emit experiment manifest
  - emit run compare summary

- Modify `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - load and summarize experiment artifacts in final reports

- Modify `backend/tests/test_submarine_domain_assets.py`
  - cover deterministic experiment and compare contracts

- Modify `backend/tests/test_submarine_solver_dispatch_tool.py`
  - cover experiment artifact emission and compare summary behavior

- Modify `backend/tests/test_submarine_result_report_tool.py`
  - cover final report experiment summary

- Modify `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - add experiment summary parser

- Modify `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - render minimal experiment summary section

- Modify `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - cover experiment summary parsing

## 12. Testing Strategy

This slice should be built test-first.

Minimum coverage:

1. Domain tests
   - deterministic experiment ids
   - deterministic run ids
   - compare payload shape from baseline + variants

2. Solver-dispatch tests
   - baseline-only execution emits baseline run record and experiment manifest
   - study execution emits variant run records and run compare summary

3. Reporting tests
   - final report includes experiment summary when registry artifacts exist

4. Frontend utility tests
   - experiment summary is parsed into stable UI-facing data
   - compare labels remain readable when statuses are missing or blocked

## 13. Risks

### 13.1 Registry Drift

Risk:

The new registry becomes a second source of truth that drifts away from solver results.

Mitigation:

- run records should be derived from already-written solver results
- compare summaries should use run records and solver metrics, not hand-maintained state

### 13.2 Overbuilt Compare Layer

Risk:

This slice turns into a complex comparison platform and stalls.

Mitigation:

- compare only a small metric set in v1
- keep scope to the current experiment root
- keep UI summary intentionally compact

### 13.3 Workflow Creep

Risk:

Users are forced into explicit experiment setup even for simple requests.

Mitigation:

- baseline-only runs remain valid
- experiment registry activates automatically
- no front-end wizard or mandatory experiment ceremony is introduced

### 13.4 Misleading Scientific Confidence

Risk:

Users confuse compare summaries with scientific validation.

Mitigation:

- keep experiment summary separate from scientific verification summary
- describe compare outputs as observed deltas, not proof of research readiness

## 14. Success Criteria

This slice is successful when:

- a baseline-only run emits explicit experiment and run identity artifacts
- a study-enabled run emits variant run records and a stable compare summary
- the final report exposes an `experiment_summary`
- the workbench can point to experiment manifest and compare artifacts
- the product still behaves like an agentic CFD assistant, not a rigid compare workflow

## 15. Out Of Scope But Next

After this slice, the next recommended order remains:

1. Unified validation, benchmark, and provenance evidence chain
2. Supervisor scientific state machine
3. Publication-grade figure and delivery layer

At that point, the platform should have:

- explicit study evidence
- explicit experiment identity
- explicit compare artifacts

which is the right foundation for broader research usability.
