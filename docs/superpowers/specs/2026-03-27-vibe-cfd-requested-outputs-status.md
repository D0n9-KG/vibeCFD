# 2026-03-27 Vibe CFD Requested Outputs Status

## 1. Purpose

This note records the current repository status after wiring user-requested outputs into the DeerFlow submarine CFD mainline.

The goal of this round was not to add a new demo shell. It was to make the system explicitly track:

- what the user asked to see
- what the current repository actually supports
- what the current run truly delivered

## 2. What Was Implemented

### 2.1 Output Contract Layer

Added a dedicated output-contract layer in:

- `backend/packages/harness/deerflow/domain/submarine/output_contract.py`

This layer now:

- normalizes free-form `expected_outputs` into structured `requested_outputs`
- assigns stable `output_id`
- marks each item with `support_level`
- can attach a structured `postprocess_spec` for supported figure-oriented outputs
- derives `output_delivery_plan` from stage, solver metrics, acceptance assessment, and generated artifacts

### 2.2 Runtime Contract Extension

Extended DeerFlow submarine runtime contracts in:

- `backend/packages/harness/deerflow/domain/submarine/contracts.py`

New runtime-carried fields:

- `requested_outputs`
- `output_delivery_plan`

This means requested outputs are now part of the real DeerFlow thread runtime state, not just brief prose.

### 2.3 Design Brief Propagation

Updated:

- `backend/packages/harness/deerflow/domain/submarine/design_brief.py`
- `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`

Current behavior:

- `expected_outputs` are normalized into `requested_outputs`
- `cfd-design-brief.json` now contains `requested_outputs`
- `submarine_runtime` now persists `requested_outputs`

### 2.4 Geometry and Solver Dispatch Propagation

Updated:

- `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py`
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`

Current behavior:

- geometry preflight preserves `requested_outputs`
- `openfoam-request.json` now contains `requested_outputs`
- solver dispatch now emits an `output_delivery_plan`
- solver dispatch now also lets `requested_outputs` influence the generated `controlDict`
- supported outputs can now carry structured `postprocess_spec` through design brief, runtime state, and dispatch payload
- requested postprocess outputs can now export stable artifacts when matching OpenFOAM postProcessing files exist
- supported outputs appear as `planned` or `delivered`
- unsupported output requests appear as `not_yet_supported`

### 2.5 Final Report Propagation

Updated:

- `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`

Current behavior:

- `final-report.json` now contains `requested_outputs`
- `final-report.json` now contains `output_delivery_plan`
- result reporting maps outputs to:
  - `delivered`
  - `pending`
  - `not_available_for_this_run`
  - `not_yet_supported`

### 2.6 Workbench Display

Updated:

- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- `frontend/src/components/workspace/submarine-runtime-panel.tsx`

Current behavior:

- design brief summary exposes structured `requestedOutputs`
- acceptance summary exposes `outputDelivery`
- the submarine workbench now shows:
  - requested outputs
  - support status
  - delivery status

## 3. Currently Supported Output Types

These output types are already wired into the current repository contract and can be marked as planned or delivered:

- `drag_coefficient`
- `force_breakdown`
- `mesh_quality_summary`
- `residual_history`
- `benchmark_comparison`
- `chinese_report`
- `surface_pressure_contour`
- `wake_velocity_slice`

For these two figure-oriented outputs, the repository now also supports a first structured postprocess contract:

- `surface_pressure_contour`
  - default field: `p`
  - default selector: hull patch
- `wake_velocity_slice`
  - default field: `U`
  - default selector: plane at `x/Lref = 1.25`
  - selector can now be overridden by runtime `postprocess_spec`

## 4. Requested But Not Yet Automatically Exported

These output types are still preserved explicitly, but the repository does not yet auto-export their artifacts:

- `streamlines`

This remains an important product behavior rule: unsupported requests are not silently lost.

## 4.1 Stable Artifact Names for Requested Postprocess Exports

The current repository now exports stable artifact names for the first two figure-oriented output types:

- `surface_pressure_contour`
  - `surface-pressure.csv`
  - `surface-pressure.md`
- `wake_velocity_slice`
  - `wake-velocity-slice.csv`
  - `wake-velocity-slice.md`

These artifacts are generated during solver dispatch when:

- the user has requested the output type
- the OpenFOAM run produces the matching raw `postProcessing` files

The workbench now classifies these files as `results` artifacts instead of leaving them in the fallback bucket.

## 4.2 Requested Outputs Now Influence Case Scaffold Generation

The repository now pushes the requested-output contract one step earlier into the OpenFOAM case scaffold:

- requesting `surface_pressure_contour` adds a `surfacePressure` function object to `system/controlDict`
- requesting `wake_velocity_slice` adds a `wakeVelocitySlice` function object to `system/controlDict`
- custom `wake_velocity_slice.postprocess_spec` can now override the slice location and normal direction
- unsupported requests such as `streamlines` still do not create new function objects

This is still intentionally limited:

- the repository is not yet dynamically synthesizing arbitrary postprocess graphs
- it is wiring only the first two supported figure-oriented outputs
- rendered figures are still a later gap

## 5. Verification

### 5.1 Focused TDD Checks

Backend:

- `uv run pytest tests/test_submarine_design_brief_tool.py -q -k requested_outputs`
- `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k requested_outputs`
- `uv run pytest tests/test_submarine_result_report_tool.py::test_submarine_result_report_tracks_requested_output_delivery -q`
- `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k postprocess`
- `uv run pytest tests/test_submarine_result_report_tool.py -q -k postprocess`
- `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k function_objects`
- `uv run pytest tests/test_submarine_design_brief_tool.py -q -k postprocess_spec`
- result: `6 passed`

Frontend:

- `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
- result: `12 passed`

### 5.2 Broader Regression

Backend:

- `uv run pytest tests/test_submarine_design_brief_tool.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py -q`
- result: `26 passed`
- `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q`
- result: `14 passed`

Submarine domain regression:

- `uv run pytest tests -q -k submarine`
- result: `43 passed, 730 deselected, 1 warning`

Frontend type check:

- `cd frontend && node_modules/.bin/tsc.cmd --noEmit`
- result: passed

Warning note:

- the remaining warning is the existing `datetime.utcnow()` deprecation in `backend/packages/harness/deerflow/agents/memory/updater.py`
- it is unrelated to this requested-outputs work

## 6. What This Means for the Product

After this round, the repository has moved from:

- natural-language expected outputs only

to:

- structured requested-output contracts carried through DeerFlow runtime, dispatch artifacts, final report, and workbench

That is a meaningful product step toward real `vibe CFD`, because the system can now distinguish:

- what the user wants
- what the current repo supports
- what this run actually delivered

## 7. Remaining Gaps

This direction is still incomplete in three important ways:

### 7.1 Missing Figure-Native Rendering

The repository now exports stable CSV and Markdown artifacts for pressure and wake outputs, but it still does not automatically generate:

- rendered pressure contour figures
- rendered wake slice figures
- streamline artifacts

### 7.2 Requested Outputs Still Do Not Fully Configure the Raw OpenFOAM Postprocess Chain

The system now adds the first supported function objects to `controlDict`, but it still does not dynamically synthesize a broader postprocess graph from the requested-output contract.

### 7.2.1 Current Flexibility Boundary

The current repository can now do a limited but real form of parameterized postprocessing:

- the supervisor can keep `requested_outputs` as the intent contract
- supported outputs can carry `postprocess_spec`
- deterministic runtime code in `backend/packages/harness/deerflow/domain/submarine/postprocess.py` interprets that spec

This is enough to support bounded flexibility such as custom wake-slice positions, but not yet enough for arbitrary user-defined figure pipelines.

### 7.3 Workbench Still Shows Status Better Than Figures

The workbench now shows the requested-output state clearly, but it still lacks:

- figure cards
- thumbnail previews
- slice definition metadata
- plot provenance for scientific review

## 8. Best Next Step Inside This Repository

The highest-value next repository step is:

1. make `requested_outputs` drive postprocess export selection
2. extend the artifact contract from CSV/Markdown exports to image and chart outputs
3. surface those artifacts as first-class workbench deliverables

That would turn the current output-contract layer from a planning-and-reporting feature into a true user-driven CFD delivery pipeline.

## 9. 2026-03-27 Addendum: PNG Figure Artifacts

This session continued the same DeerFlow mainline and pushed the requested-output pipeline one step further:

- `surface_pressure_contour` now exports:
  - `surface-pressure.csv`
  - `surface-pressure.png`
  - `surface-pressure.md`
- `wake_velocity_slice` now exports:
  - `wake-velocity-slice.csv`
  - `wake-velocity-slice.png`
  - `wake-velocity-slice.md`

### 9.1 Implementation Notes

- The image rendering stays inside deterministic DeerFlow domain code rather than being delegated to a free-form subagent.
- Rendering lives in:
  - `backend/packages/harness/deerflow/domain/submarine/postprocess.py`
- The implementation intentionally uses `Pillow`, not `matplotlib`, because the current `uv` test environment already has `Pillow` available while `matplotlib` is not installed there.
- The rendered PNGs are deterministic scatter-style preview figures generated from exported OpenFOAM CSV samples.

### 9.2 Contract Changes

- The default `postprocess_spec.formats` for:
  - `surface_pressure_contour`
  - `wake_velocity_slice`
- are now:
  - `["csv", "png", "report"]`

This means that when the user asks for those outputs and the run produces matching postprocess CSV files, the repository now attempts to deliver both archive-friendly data and demo-friendly figures.

### 9.3 Workbench Changes

The submarine workbench now recognizes:

- `surface-pressure.png`
- `wake-velocity-slice.png`

as `results` artifacts rather than dropping them into the fallback `other` bucket.

The metadata labels were also extended so these PNG outputs show up with stable, human-readable names in the DeerFlow-style workbench UI.

### 9.4 Updated Remaining Gap

The repository no longer lacks all figure-native rendering. It now has a first deterministic figure layer for:

- surface pressure previews
- wake velocity slice previews

The remaining figure-related gaps are now narrower:

- no streamline figure export yet
- no richer plot cards or inline image previews in the workbench panel yet
- no provenance panel for slice parameters in the UI yet
- no higher-fidelity contour interpolation or publication-grade plotting templates yet

### 9.5 Verification

Focused verification:

- `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k requested_postprocess_artifacts`
- result: `1 passed`
- `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
- result: `12 passed`

Broader verification:

- `uv run pytest tests/test_submarine_design_brief_tool.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py -q`
- result: `26 passed`
- `uv run pytest tests -q -k submarine`
- result: `43 passed, 730 deselected, 1 warning`
- `cd frontend && node_modules/.bin/tsc.cmd --noEmit`
- result: passed

## 19. 2026-03-29 Addendum: Scientific Remediation Handoff v1

This session continued the scientific remediation track and turned remediation plans into an explicit next-tool handoff contract.

### 19.1 What Changed

The repository now adds a report-stage handoff layer on top of the existing scientific remediation plan:

- `backend/packages/harness/deerflow/domain/submarine/handoff.py` maps remediation actions into concrete next-step handoffs
- `backend/packages/harness/deerflow/domain/submarine/reporting.py` now emits:
  - `scientific_remediation_handoff` in `final-report.json`
  - `scientific-remediation-handoff.json` as a dedicated artifact
  - a refreshed `supervisor_handoff_virtual_path` that points at the report-stage handoff artifact
- `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py` now persists that refreshed handoff pointer back into runtime state

### 19.2 Handoff Semantics

The new handoff contract makes the repository explicit about what should happen next:

- `ready_for_auto_followup`
  - a follow-up tool call can be prepared automatically
- `manual_followup_required`
  - the next step still depends on human-supplied evidence or judgment
- `not_needed`
  - no remediation handoff is needed for the current run

In v1, the most important mapping is:

- `execute-scientific-studies`
  - suggests `submarine_solver_dispatch`
  - carries forward geometry, case selection, task metadata, and scientific-study execution arguments

Manual validation-reference gaps remain manual instead of being disguised as auto-executable.

### 19.3 Workbench Changes

The submarine runtime panel now surfaces the remediation handoff contract next to the remediation plan:

- handoff status
- recommended action id
- suggested tool name
- suggested tool arguments
- manual follow-up actions
- handoff artifact links

The workbench also now classifies `scientific-remediation-handoff.json` as a report artifact with a stable human-readable label.

### 19.4 Why This Matters

This is an important step toward research-usable `vibe CFD` because the repository no longer stops at saying "the evidence is incomplete."

It now also says:

- whether the next step is executable by contract
- which DeerFlow tool should run next
- which arguments should be carried into that next run
- which evidence gaps still require manual intervention

That keeps the product open-ended while making the supervisor layer materially more actionable.

### 19.5 Remaining Gap

This stage still does not auto-run expensive follow-up studies:

- the handoff is advisory and machine-readable
- there is still no autonomous rerun policy layer
- no loop yet re-enters solver dispatch automatically after report generation

That boundary is intentional so the repository does not collapse into a rigid workflow shell.

### 19.6 Verification

Backend verification:

- `uv run pytest tests/test_submarine_domain_assets.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py -q`
- result: `54 passed`

Focused frontend verification:

- `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
- result: `28 passed`

Frontend type/lint verification:

- `corepack pnpm exec tsc --noEmit`
- result: passed
- `corepack pnpm exec eslint src/components/workspace/submarine-runtime-panel.tsx src/components/workspace/submarine-runtime-panel.utils.ts src/components/workspace/submarine-runtime-panel.utils.test.ts`
- result: passed

## 17. 2026-03-28 Addendum: Experiment Compare Workbench v1

This session continued the research-evidence workbench and turned existing compare artifacts into a real runtime-panel review surface.

### 17.1 What Changed

The repository now promotes compare evidence into two connected layers:

- final report payloads expose a structured `experiment_compare_summary`
- the submarine runtime panel renders compact compare cards from that summary

The new summary bridges:

- the experiment baseline run id
- compare-count and compare-artifact entrypoints
- per-candidate compare status
- resolved baseline and candidate solver-result / run-record artifact paths
- compact metric-delta lines derived from structured `metric_deltas`

This means the workbench no longer depends on raw `compare_notes` alone to explain study comparisons.

### 17.2 Why This Matters

For research-facing `vibe CFD`, the existence of a compare artifact is not enough. A human reviewer needs to see:

- what was compared
- whether the comparison was complete or blocked
- which metrics moved
- which artifacts anchor the baseline and candidate evidence

This slice keeps the user experience open-ended while making the evidence layer much more inspectable.

### 17.3 Current Limitation

This is still a compact workbench compare surface, not a full compare lab:

- there is still no dedicated multi-experiment compare page
- figures are not yet rendered side-by-side by baseline and variant
- there are no interactive compare charts or filters
- compare provenance still stops at artifact entrypoints rather than a deeper audit graph

### 17.4 Verification

Focused verification:

- `cd frontend && node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
- result: `25 passed`
- `cd frontend && corepack pnpm exec tsc --noEmit`
- result: passed
- `cd frontend && corepack pnpm exec eslint src/components/workspace/submarine-runtime-panel.tsx src/components/workspace/submarine-runtime-panel.utils.ts src/components/workspace/submarine-runtime-panel.utils.test.ts`
- result: passed

Broader verification:

- `uv run pytest tests/test_submarine_domain_assets.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py -q`
- result: `52 passed`

## 18. 2026-03-28 Addendum: Scientific Remediation Planner v1

This session continued the scientific gate work and added a first structured remediation layer.

### 18.1 What Changed

The repository now emits a deterministic `scientific_remediation_summary` and a companion artifact:

- `scientific-remediation-plan.json`

The remediation layer translates research evidence and scientific gate outcomes into explicit next actions.

Current action families include:

- execute missing scientific verification studies
- attach a validation reference when the run is verified but not externally validated
- regenerate result-report packaging when provenance linkage is still limiting the claim level

The runtime workbench now renders remediation cards so a reviewer can see:

- current claim level
- target claim level
- recommended owner stage
- whether an action is auto-executable or manual-required
- which evidence gap the action is closing

### 18.2 Why This Matters

Before this slice, the repository could explain why a run was blocked or claim-limited, but it still stopped at diagnosis.

Now it also produces a machine-readable answer to:

- what should happen next
- who should do it
- whether the repository can do it itself later

This is an important step from "evidence-aware" toward "self-steering" research workflow behavior.

### 18.3 Current Limitation

This is still a remediation planner, not a remediation executor:

- auto-executable actions are described, but not yet launched automatically
- there is no remediation history across multiple follow-up runs
- missing validation references still need human or case-library input
- provenance remains summary-oriented rather than a full action audit graph

### 18.4 Verification

Focused verification:

- `uv run pytest tests/test_submarine_domain_assets.py -q -k scientific_remediation_plan`
- result: `1 passed`
- `uv run pytest tests/test_submarine_result_report_tool.py -q -k verified_but_not_validated`
- result: `1 passed`
- `cd frontend && node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
- result: `26 passed`
- `cd frontend && corepack pnpm exec tsc --noEmit`
- result: passed
- `cd frontend && corepack pnpm exec eslint src/components/workspace/submarine-runtime-panel.tsx src/components/workspace/submarine-runtime-panel.utils.ts src/components/workspace/submarine-runtime-panel.utils.test.ts`
- result: passed

Broader verification:

- `uv run pytest tests/test_submarine_domain_assets.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py -q`
- result: `53 passed`

## 15. 2026-03-28 Addendum: Figure Delivery Summary

This session continued the same requested-output mainline and upgraded the supported figure outputs from loose PNG previews to manifest-backed delivery records.

### 15.1 What Changed

The deterministic postprocess layer now emits a structured `figure-manifest.json` alongside supported figure exports such as:

- `surface_pressure_contour`
- `wake_velocity_slice`

Each figure entry now records:

- stable `figure_id`
- human-readable `title`
- publication-oriented `caption`
- `render_status`
- `selector_summary`
- `field`
- figure-specific `artifact_virtual_paths`
- `source_csv_virtual_path`

The final report now loads that manifest and emits a compact `figure_delivery_summary` that includes:

- manifest path
- figure count
- per-figure caption and selector provenance
- figure-specific artifact entrypoints

The submarine workbench result cards now surface that same structured evidence directly next to the preview area:

- figure render status
- caption text
- selector provenance
- manifest-backed artifact links

### 15.2 Why This Matters

This closes an important honesty gap in the requested-output pipeline. The repository no longer treats a PNG as self-explanatory; it now keeps the visual artifact tied to:

- what figure it is
- what was sampled
- how it was selected
- which stable artifacts back the image

That makes the figure layer more suitable for supervisor review and for later publication-grade upgrades without turning the user-facing flow into a rigid report wizard.

### 15.3 Remaining Gap

This is still `Publication-Grade Figure Delivery v1`, not the final scientific figure system:

- preview rendering is still deterministic and lightweight rather than publication-polished
- there is still no side-by-side multi-run figure compare workspace
- streamline and other richer figure families are still unsupported
- figure styling is more provenance-rich now, but not yet journal-grade

### 15.4 Verification

Focused verification:

- `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k requested_postprocess_artifacts`
- result: `1 passed`
- `uv run pytest tests/test_submarine_result_report_tool.py -q -k postprocess_exports_delivered`
- result: `1 passed`
- `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
- result: `24 passed`

## 15. 2026-03-28 Addendum: Unified Research Evidence Chain

This session connected the existing experiment, verification, benchmark, and delivery summaries into one explicit research-facing evidence layer.

### 15.1 What Changed

The repository now emits a structured `research_evidence_summary` that sits above:

- `acceptance_assessment`
- `scientific_verification_assessment`
- `scientific_study_summary`
- `experiment_summary`
- `output_delivery_plan`

This new layer does not replace those blocks. It interprets them together and answers the more important research question:

- what can this run legitimately claim right now?

### 15.2 Conservative Readiness Rule

The top-level semantics are now intentionally stricter:

- without an external validation reference, the highest default readiness is `verified_but_not_validated`

That means the repository now explicitly distinguishes:

- numerical verification strength
- external validation support
- provenance traceability

The system no longer treats strong numerical verification alone as enough for generic `research_ready`.

### 15.3 New Artifact And Reporting Layer

`backend/packages/harness/deerflow/domain/submarine/reporting.py` now emits:

- `research-evidence-summary.json`
- `research_evidence_summary` inside `final-report.json`

The new summary normalizes three dimensions:

- `verification_status`
- `validation_status`
- `provenance_status`

and aggregates them into a top-level readiness status:

- `blocked`
- `insufficient_evidence`
- `verified_but_not_validated`
- `validated_with_gaps`
- `research_ready`

### 15.4 Provenance Semantics

This session also tightened one important nuance in the provenance layer.

`traceable` provenance no longer depends on user-requested output cards alone. A run can now be considered traceable when the core research evidence trail is present via:

- solver results
- scientific verification artifacts
- study manifest
- experiment manifest
- compare summary
- report entrypoints

This matters because research evidence should not be downgraded merely because the user did not request extra presentation-oriented output artifacts.

### 15.5 Workbench Changes

The submarine workbench now surfaces a compact research evidence section that shows:

- research readiness
- verification status
- validation status
- provenance status
- confidence
- passed evidence
- evidence gaps
- benchmark highlights
- provenance highlights
- evidence artifact entrypoints

This keeps the UI agentic and compact while making the evidence semantics much harder to misuse.

### 15.6 Remaining Gap

This is a major evidence-layer step, but it is still not the final research platform:

- supervisor transitions are still softer than a dedicated scientific state machine
- provenance is still summary-based rather than a full audit graph
- validation still depends on case-local benchmark targets rather than a broader validation registry
- publication-grade figures and compare views are still a later slice

## 16. 2026-03-28 Addendum: Supervisor Scientific State Machine

This session tightened the supervisor transition semantics so the repository now distinguishes between:

- generating artifacts
- promoting a run to a stronger scientific claim level

The important rule is that artifact generation remains open and agentic, but stage promotion is now evidence-gated.

### 16.1 What Changed

The submarine domain now has an explicit scientific supervisor gate contract in:

- `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- `backend/packages/harness/deerflow/domain/submarine/supervision.py`

The new gate exposes:

- `gate_status`
- `allowed_claim_level`
- `source_readiness_status`
- `recommended_stage`
- `remediation_stage`
- `blocking_reasons`
- `advisory_notes`
- `artifact_virtual_paths`

The execution plan also now includes an explicit `supervisor-review` step instead of treating supervisor sign-off as an implicit afterthought.

### 16.2 Gate Semantics

The first deterministic supervisor-gate semantics are now:

- `research_ready` -> `ready_for_claim`
- `verified_but_not_validated` -> `claim_limited`
- `validated_with_gaps` -> `claim_limited`
- `blocked` / `insufficient_evidence` -> `blocked`

This means the system can now say:

- the run is ready for a strong research claim
- the run is numerically credible but only for a limited claim
- the run is blocked from scientific promotion and needs remediation

without collapsing all of those cases into the old generic review shell.

### 16.3 New Artifact And Reporting Layer

`backend/packages/harness/deerflow/domain/submarine/reporting.py` now emits:

- `supervisor-scientific-gate.json`
- `scientific_supervisor_gate` inside `final-report.json`

The final report also now carries:

- `scientific_gate_virtual_path`

and the result-report tool maps runtime review state from the gate instead of hard-coding it:

- `gate_status == blocked` -> `review_status = blocked`
- otherwise -> `review_status = ready_for_supervisor`
- `next_recommended_stage` now follows the gate's `recommended_stage`

This makes the supervisor-facing state traceable instead of being a loose convention.

### 16.4 Claim-Limited vs Blocked

The repository now makes an important scientific distinction:

- `claim_limited` means the run can still move to supervisor review, but only with a constrained claim level such as `verified_but_not_validated`
- `blocked` means the run can still keep its artifacts, but promotion is stopped until the recommended remediation stage is revisited

This preserves the `vibe CFD` openness of the system while still enforcing hard scientific guardrails where they matter.

### 16.5 Workbench Changes

The submarine workbench now surfaces a dedicated scientific supervisor gate section that shows:

- gate status
- allowed claim level
- source readiness
- recommended stage
- remediation stage
- blocking reasons
- advisory notes
- gate artifact entrypoints

The top-level supervisor review tile also now reflects the scientific gate, so the user can see at a glance whether the current run is:

- ready for claim
- claim limited
- blocked

### 16.6 Remaining Gap

This is the first real scientific state machine, but it is still only the current stage gate:

- the supervisor does not yet drive a richer multi-step remediation loop
- compare views are still compact rather than a dedicated research dashboard
- provenance is still summary-oriented rather than a full audit graph
- publication-grade figures are still a later slice

## 14. 2026-03-28 Addendum: Experiment Registry And Run Compare v1

This session extended the scientific-study work into a lightweight experiment registry so baseline and variant runs are now explicit members of a shared compareable experiment, instead of a loose collection of artifacts.

### 14.1 What Changed

The submarine domain now has typed contracts for:

- experiment manifests
- baseline and scientific-study variant run records
- run-compare entries
- root compare summaries

The new helper layer derives deterministic identifiers for:

- `experiment_id`
- baseline `run_id`
- per-study variant `run_id`

That makes experiment evidence stable enough to reference in reporting and the workbench without hard-coding one-off directory names.

### 14.2 Solver-Dispatch Changes

`backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` now emits:

- root `experiment-manifest.json`
- root `run-record.json` for the baseline execution
- root `run-compare-summary.json`
- per-variant `run-record.json` files under `studies/<study>/<variant>/`

For baseline-only runs, the compare summary is intentionally minimal and honest:

- `baseline_run_id` is always explicit
- `comparisons` is empty when no non-baseline runs executed
- the experiment manifest still records the baseline run as the first experiment member

For study-enabled execution, the compare summary now aggregates the currently executed non-baseline variants and records compact deltas for:

- `Cd`
- `Fx`
- `final_time_seconds`
- `mesh_cells`

Blocked or incomplete study runs are no longer silently dropped from compare bookkeeping; they surface as compare entries with non-success status.

### 14.3 Reporting And Workbench Changes

The final report now adds an `experiment_summary` block that includes:

- `experiment_id`
- `experiment_status`
- `baseline_run_id`
- `run_count`
- manifest and compare artifact entrypoints
- compact compare notes

The submarine workbench now surfaces that experiment summary in the runtime health panel so users can see:

- which experiment the current run belongs to
- whether the registry is only planned, completed, or blocked
- how many runs are already attached
- where the compare summary lives
- which variant comparisons currently exist

This keeps the top-level UX open-ended while tightening the execution and evidence layers underneath.

### 14.4 Remaining Gap

This is still intentionally a v1 experiment layer, not a full research experiment platform:

- there is still no dedicated side-by-side compare workspace
- compare semantics are still compact and metric-oriented, not figure-native
- validation targets and provenance are not yet unified into the same experiment evidence chain
- supervisor transitions are still softer than a dedicated scientific state machine
- publication-grade compare figures remain a later slice

## 11. 2026-03-28 Addendum: Structured Requested-Result Cards

This session continued the same DeerFlow-native requested-output pipeline and upgraded the submarine workbench from text-only requested-output summaries to structured result cards.

### 11.1 What Changed

The front-end utility layer now builds `result cards` by combining three already-existing sources:

- requested outputs from the design brief
- output delivery status from the final report
- exported artifact paths from the run

This logic lives in:

- `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`

The new helper:

- `buildSubmarineResultCards(...)`

produces a stable card model that includes:

- `outputId`
- output label / requested label
- support level
- delivery status
- provenance summary
- delivery detail
- preview artifact path
- attached artifact list

The submarine workbench now renders these cards inside the existing `Artifacts` panel rather than creating a parallel UI shell. The rendering lives in:

- `frontend/src/components/workspace/submarine-runtime-panel.tsx`

### 11.2 Current Behavior

For supported postprocess outputs such as:

- `surface_pressure_contour`
- `wake_velocity_slice`

the workbench can now show:

- a preview image when a PNG artifact exists
- the structured `postprocess_spec` summary
- the delivery status badge
- the attached artifacts that belong to that requested output

For non-image outputs such as:

- `drag_coefficient`
- `benchmark_comparison`

the same card model still works, but the preview area falls back to a placeholder while the artifact list still links to the matching JSON / report artifacts.

This is important because it moves the project closer to a real `vibe CFD` workbench:

- the user can ask for specific outputs
- DeerFlow records them in a structured contract
- the run produces artifacts
- the workbench now groups those artifacts back into output-oriented cards

### 11.3 Remaining Gap

This is a meaningful UI step, but it is not the final research-grade result browser yet. The remaining gaps are now more specific:

- no streamline result card yet
- no side-by-side compare between runs
- no richer field-specific legends or scale bars in preview cards
- no inline structured table for `postprocess_spec`
- no publication-grade figure layout

### 11.4 Verification

Focused verification:

- `node --experimental-strip-types --test frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
- result: `14 passed`

Frontend verification:

- `cd frontend && node_modules/.bin/tsc.cmd --noEmit`
- result: passed

## 12. 2026-03-28 Addendum: Scientific Verification Contract

This session pushed the repository one step closer to research-facing `vibe CFD` by adding a first deterministic scientific verification layer.

### 12.1 What Changed

The repository now distinguishes between:

- delivery readiness
- scientific verification readiness

This is important because a run can already be traceable and deliverable while still lacking the evidence expected for research-grade conclusions.

The new scientific verification contract now appears in three places:

- submarine design brief
- final report
- submarine workbench

### 12.2 Backend Contract

The backend now derives an effective verification checklist from the case acceptance profile and task type. The first default requirement set includes:

- final residual threshold
- force coefficient tail stability
- mesh independence study
- domain sensitivity study
- time-step sensitivity study

This logic lives in:

- `backend/packages/harness/deerflow/domain/submarine/verification.py`

The typed model layer was extended in:

- `backend/packages/harness/deerflow/domain/submarine/models.py`

The design brief now emits `scientific_verification_requirements`, so the supervisor and the workbench can see the research-facing checklist before execution starts.

The final report now emits `scientific_verification_assessment`, which evaluates:

- what passed in the current run
- what is blocked by poor numerical behavior
- what evidence is still missing

### 12.3 Current Behavior

For a case such as `darpa_suboff_bare_hull_resistance`, the repository can now honestly report:

- residual threshold passed
- force-coefficient tail stability passed
- mesh independence evidence missing
- domain sensitivity evidence missing
- time-step sensitivity evidence missing

The overall scientific verification status therefore becomes:

- `needs_more_verification`

instead of pretending that a single successful baseline run is already research-ready.

### 12.4 Workbench Changes

The submarine workbench now shows:

- scientific verification requirements in the design brief panel
- scientific verification status, confidence, missing evidence, blockers, and requirement-by-requirement status in the health panel

This keeps the DeerFlow workbench style intact while making the research gap visible to the user.

### 12.5 Remaining Gap

This new layer is still the first step, not the final research workflow:

- there is no run-to-run compare UI yet
- mesh/domain/time-step studies are tracked as required evidence, but the repository still lacks a full experiment manager to generate and compare those studies
- streamlines and richer publication-grade figure outputs are still missing
- supervisor state transitions are still weaker than a dedicated scientific workflow state machine

### 12.6 Verification

Focused backend verification:

- `uv run pytest tests/test_submarine_domain_assets.py tests/test_submarine_design_brief_tool.py tests/test_submarine_result_report_tool.py -q`
- result: `21 passed`

Broader backend verification:

- `uv run pytest tests -q -k submarine`
- result: `46 passed, 730 deselected, 1 warning`

Focused frontend verification:

- `node --experimental-strip-types --test frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
- result: `16 passed`

Frontend type verification:

- `cd frontend && node_modules/.bin/tsc.cmd --noEmit`
- result: passed

Warning note:

- the remaining warning is still the pre-existing `datetime.utcnow()` deprecation in `backend/packages/harness/deerflow/agents/memory/updater.py`

Warning note:

- the remaining warning is still the existing `datetime.utcnow()` deprecation in `backend/packages/harness/deerflow/agents/memory/updater.py`
- it is unrelated to this PNG artifact work

## 13. 2026-03-28 Addendum: Scientific Study Orchestration v1

This session moved the repository beyond "scientific verification is required" and into a first deterministic study-orchestration layer that now supports both honest planning artifacts and optional real variant execution.

### 13.1 What Changed

The submarine domain now has typed scientific-study contracts for:

- study definitions
- study variants
- study manifests
- study results

The first deterministic planner generates three study families for supported resistance baselines:

- `mesh_independence`
- `domain_sensitivity`
- `time_step_sensitivity`

### 13.2 Solver-Dispatch Changes

`backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py` now emits:

- `study-plan.json`
- `study-manifest.json`
- planned per-variant artifact paths under `studies/<study>/<variant>/solver-results.json`

When a baseline run is executed without extra study execution, the repository emits structured verification-study artifacts such as:

- `verification-mesh-independence.json`
- `verification-domain-sensitivity.json`
- `verification-time-step-sensitivity.json`

In this v1 slice, those verification artifacts are intentionally honest:

- they record the baseline value when available
- they mark the study as `missing_evidence` when only the baseline run has been executed
- they do not pretend that a matched artifact path is enough to claim research readiness

When `execute_scientific_studies=true`, solver dispatch now also materializes and executes the planned non-baseline variants for:

- `mesh_independence`
- `domain_sensitivity`
- `time_step_sensitivity`

That execution path writes real per-variant `solver-results.json` payloads under `studies/<study>/<variant>/`, copies the baseline result into each study's `baseline` slot, and regenerates the root `verification-*.json` artifacts from measured `latest_force_coefficients`.

### 13.3 Reporting And Workbench Changes

The final report now adds `scientific_study_summary`, which links:

- the discovered `study-manifest.json`
- study execution status
- per-study verification status derived from the scientific verification assessment

The workbench now surfaces that study summary in the runtime health panel so users can inspect:

- whether studies are only planned or already materialized
- whether study execution finished cleanly or is blocked
- which study families are still missing evidence
- which artifact entrypoints anchor the current evidence trail

### 13.4 Remaining Gap

This is still not the full research experiment manager:

- variant case execution is available, but not yet a full run-to-run compare system
- domain and mesh variants still need deeper physical parameterization and stricter provenance
- supervisor gating is still softer than a dedicated scientific state machine
- publication-grade figure generation is still a later slice

## 10. 2026-03-27 Addendum: Postprocess Provenance Summaries

This session continued the same requested-output pipeline and added a first provenance layer for supported postprocess outputs.

### 10.1 What Changed

The repository now turns structured `postprocess_spec` into human-readable summaries in two places:

- final report Markdown / HTML requested-output sections
- submarine workbench requested-output and output-delivery summaries

For example, the system can now surface summaries such as:

- `field=p; selector=patch[hull]; time=latest; formats=csv,png,report`
- `field=U; selector=plane[x/Lref=1.25; normal=(1, 0, 0)]; time=latest; formats=csv,png,report`

This means the user can see not only that a wake slice or surface-pressure artifact exists, but also the configuration that was used to generate it.

### 10.2 Why This Matters

This is an important step for research-facing `vibe CFD`, because image artifacts alone are not enough. A scientific workflow also needs basic provenance:

- what field was sampled
- what selector was used
- where the slice was placed
- what output formats were requested

The current implementation is still lightweight, but it already makes the requested-output contract more reviewable and less chat-like.

### 10.3 Current Limitation

The repository now shows postprocess provenance summaries, but it still does not yet provide:

- a dedicated workbench provenance card
- richer UI rendering of slice metadata as structured chips or tables
- per-figure captions that embed provenance directly next to image thumbnails
- stronger publication-grade provenance formatting

### 10.4 Verification

Focused verification:

- `uv run pytest tests/test_submarine_result_report_tool.py -q -k postprocess_exports_delivered`
- result: `1 passed`
- `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
- result: `12 passed`

Broader verification:

- `uv run pytest tests/test_submarine_design_brief_tool.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py -q`
- result: `26 passed`
- `uv run pytest tests -q -k submarine`
- result: `43 passed, 730 deselected, 1 warning`
- `cd frontend && node_modules/.bin/tsc.cmd --noEmit`
- result: passed
