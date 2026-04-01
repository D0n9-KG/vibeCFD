# Experiment Compare Workbench v1 Design

## 1. Goal

Turn the existing experiment registry and run-compare artifacts into a real compare workbench for research review, without collapsing the project into a rigid workflow shell.

The user-facing experience should stay open-ended:

- the user can still ask for flexible CFD outcomes in natural language
- the system can still choose which outputs, studies, and reports matter for the task

But once experiment data exists, the repository should become much clearer about:

- what the baseline run is
- which study variants were compared
- what the metric deltas are
- which artifacts anchor each comparison

## 2. Why This Is The Right Next Slice

The repository already has:

- scientific study orchestration
- experiment manifests
- run records
- run-compare summary artifacts
- research evidence summaries
- supervisor scientific gates
- figure manifests and figure-delivery summaries

What it still lacks is a usable research comparison surface.

Today, compare data exists, but it is still too compressed:

- final reporting only exposes compact compare notes
- the workbench only shows experiment status at a summary level
- there is no strong bridge from `run-compare-summary.json` to human-readable review

That means a real study can execute, but the user still cannot quickly inspect baseline-versus-variant evidence from the workbench itself.

## 3. Product Principle

This stage must preserve the same layering rule used so far:

- user intent stays flexible
- execution and evidence stay structured

So this stage must not force the user to enter a compare workflow explicitly.

Instead:

1. if an experiment and compare artifacts exist, reporting should emit a structured compare summary
2. if that compare summary exists, the workbench should surface it
3. if compare data does not exist, the UI should stay quiet rather than inventing fake compare state

## 4. Recommended Approach

### Approach A: UI-Only Compare View

Parse `run-compare-summary.json` directly in the frontend and build a compare panel there.

Pros:

- faster
- minimal backend change

Cons:

- pushes research semantics into UI code
- duplicates backend artifact-loading logic
- makes final reports weaker than the workbench

### Approach B: Backend Compare Summary + Thin Workbench

Extend result reporting so it emits a structured `experiment_compare_summary` into `final-report.json`, then let the workbench render that summary.

Pros:

- compare semantics stay in the evidence layer
- final report and workbench share the same compare contract
- easier to test and extend later

Cons:

- requires backend and frontend changes

### Approach C: Full Compare Dashboard

Build a separate compare page with side-by-side figures, filters, and metric charts now.

Pros:

- richer final UX

Cons:

- too large for this slice
- high UI complexity before the compare contract is stable
- higher risk of turning this into a workflow shell instead of a reusable research layer

### Recommendation

Choose Approach B.

This is the right v1 because it strengthens the evidence layer first, keeps the UI compact, and creates a stable contract for later multi-run figure dashboards.

## 5. Scope

### In Scope

- new structured `experiment_compare_summary` in final reporting
- compare entries that expand `run-compare-summary.json` into UI-ready records
- baseline/candidate artifact entrypoints for each compare item
- workbench parsing of the new compare summary
- workbench rendering of compact compare cards inside the existing runtime panel

### Out Of Scope

- a separate compare page or dashboard route
- interactive plotting or metric charts
- automatic side-by-side image diffing
- full multi-experiment browsing
- publication-grade compare figures

## 6. Backend Design

### 6.1 Reporting Contract

`reporting.py` should load:

- `experiment-manifest.json`
- `run-compare-summary.json`

and emit a new `experiment_compare_summary` block into `final-report.json`.

That block should include:

- `experiment_id`
- `baseline_run_id`
- `compare_count`
- `compare_virtual_path`
- `artifact_virtual_paths`
- `comparisons`

Each comparison entry should include:

- `candidate_run_id`
- `study_type`
- `variant_id`
- `compare_status`
- `notes`
- `metric_deltas`
- `baseline_solver_results_virtual_path`
- `candidate_solver_results_virtual_path`
- `baseline_run_record_virtual_path`
- `candidate_run_record_virtual_path`

### 6.2 Artifact Resolution

The reporting layer should derive compare entrypoints by matching:

- baseline run record from `experiment-manifest.json`
- candidate run records from `experiment-manifest.json`
- compare entries from `run-compare-summary.json`

It should not require the frontend to reconstruct this join.

### 6.3 Markdown / HTML Output

Final report Markdown / HTML should gain a compact compare section that exposes:

- compare artifact path
- baseline run id
- one line per candidate comparison with status and metric deltas

This keeps compare evidence visible in the final report instead of only the workbench.

## 7. Frontend Design

### 7.1 Utility Contract

`submarine-runtime-panel.utils.ts` should parse `experiment_compare_summary` into a stable front-end summary type.

That type should expose:

- compare path
- baseline run id
- compare count
- per-comparison status label
- compact metric delta lines
- baseline/candidate artifact entrypoints

### 7.2 Workbench Rendering

The existing runtime panel should render compare data inside the current health/evidence area, not as a new app shell.

Each compare item should show:

- baseline vs candidate run identifiers
- study type / variant
- compare status
- key metric delta lines such as `Cd`, `Fx`, `mesh_cells`, `final_time_seconds`
- quick links to baseline and candidate artifacts

### 7.3 UX Constraint

The compare surface should stay compact and legible:

- cards over tables
- explicit labels over hidden hover-only detail
- no side-by-side images yet

## 8. Files

### Backend

- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

### Frontend

- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`

### Docs

- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

## 9. Testing Strategy

### Backend

- add report tests for `experiment_compare_summary`
- verify compare entries contain resolved baseline/candidate artifact entrypoints
- verify Markdown / HTML includes compare lines

### Frontend

- add utility tests for compare summary parsing
- add utility tests for metric delta labels
- run typecheck and focused eslint

## 10. Success Criteria

This stage is successful when:

- final reports include a structured `experiment_compare_summary`
- the workbench shows real compare entries rather than only compact experiment notes
- baseline and variant artifacts are directly reachable from compare UI
- the result still feels like an open-ended `vibe CFD` workbench, not a forced compare wizard

## 11. Remaining Gap After This Stage

Even after this stage, the repository will still not have:

- side-by-side multi-run figure panels
- compare-specific publication-grade layouts
- cross-experiment search and filtering
- full audit-graph provenance

Those should come after the compare contract is proven stable in reporting and the current workbench.
