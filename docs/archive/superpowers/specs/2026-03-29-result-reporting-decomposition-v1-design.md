# Result Reporting Decomposition v1 Design

## 1. Goal

Break `backend/packages/harness/deerflow/domain/submarine/reporting.py` into focused modules so the result-reporting layer stops behaving like a single accumulating god file.

This stage is about architecture, not product behavior. It should preserve the current report contract while making future scientific-report evolution safer.

## 2. Why This Is The Right Next Slice

After the frontend final-report schema cleanup, the largest immediate maintainability risk is now backend-side result reporting.

Current state:

- `reporting.py` is 2428 lines
- `_build_acceptance_assessment` alone is about 350 lines
- `run_result_report` is about 230 lines
- markdown and HTML rendering live in the same file as:
  - artifact loading
  - benchmark evaluation
  - experiment/study summary building
  - scientific remediation summary assembly
  - final artifact writing

That means every new scientific-report capability now increases pressure on the same file, even when the change belongs to only one concern.

For a truly research-usable `vibe CFD`, result reporting is not a side concern. It is one of the core evidence surfaces. That makes clarity and change safety here especially important.

## 3. Design Options

### Option A: Keep Patching The Existing File

Pros:

- no immediate file movement

Cons:

- preserves the main architecture hotspot untouched
- increases merge risk and regression risk every time a new report field lands
- makes future research evidence growth harder to reason about

### Option B: Full Rewrite Of Result Reporting In One Big Jump

Pros:

- could produce a cleaner end state quickly

Cons:

- too much surface area for one stage
- mixes structural refactor with high regression risk
- harder to verify incrementally

### Option C: Phased Extraction By Responsibility

Pros:

- preserves behavior while shrinking the hotspot
- lets tests lock existing report behavior before and after extraction
- creates clean boundaries for later work

Cons:

- requires a few small modules instead of one file

## 4. Recommendation

Implement Option C.

Use this v1 stage to turn `reporting.py` into an orchestration entrypoint plus artifact writer, while extracting the largest responsibility clusters into dedicated modules.

## 5. Proposed Module Boundaries

### Acceptance And Benchmark Evaluation

- Create: `backend/packages/harness/deerflow/domain/submarine/reporting_acceptance.py`

Move:

- `_has_required_artifact`
- `_resolve_benchmark_observed_value`
- `_evaluate_benchmark_target`
- `_build_acceptance_assessment`

This module owns scientific acceptance / benchmark gate logic only.

### Report Summary Builders

- Create: `backend/packages/harness/deerflow/domain/submarine/reporting_summaries.py`

Move:

- case / artifact loading helpers needed only for reporting summaries
- `_build_scientific_study_summary`
- `_build_experiment_summary`
- `_build_experiment_compare_summary`
- `_build_figure_delivery_summary`
- selected-case resolution helpers if still needed here

This module should build structured payload blocks, not render them.

### Markdown / HTML Rendering

- Create: `backend/packages/harness/deerflow/domain/submarine/reporting_render.py`

Move:

- markdown section renderers
- HTML section renderers
- shared render-format helpers such as postprocess summary formatting
- top-level `_render_markdown` / `_render_html`
- delivery-readiness renderers

This module should render already-built payload blocks, not decide scientific status.

### Remaining `reporting.py`

Keep in `reporting.py`:

- public `run_result_report(...)`
- minimal artifact-path helpers if still central
- final payload assembly orchestration
- final file writes

The end state should make `run_result_report(...)` read like a report assembly pipeline rather than a mixed bag of all reporting internals.

## 6. Product Boundary

This stage should not:

- add new report fields
- change report artifact names
- change gate semantics
- change markdown / HTML section ordering on purpose

This stage should:

- preserve current payload and artifact behavior
- shrink `reporting.py`
- make future science/report changes land in the correct module

## 7. Success Criteria

This stage is successful when:

- `reporting.py` is materially smaller and primarily orchestration-focused
- acceptance logic lives outside the entrypoint file
- summary-building logic lives outside the entrypoint file
- markdown / HTML rendering lives outside the entrypoint file
- existing report tests still pass unchanged

## 8. Why This Matters For Research Readiness

The remaining product gaps to true research usability are still mostly:

- stronger benchmark/reference coverage
- expert-reviewed CFD skill content
- production/HPC execution
- richer supervisor/workbench control loops
- publication-grade comparison and provenance UX

But architecture is now the main force multiplier risk. If the reporting layer remains monolithic while those capabilities keep landing, the repo will become harder to evolve safely than the science gaps themselves.

This decomposition stage is therefore not a detour from research readiness. It is what keeps the evidence/reporting core healthy enough to carry the remaining science-facing work.
