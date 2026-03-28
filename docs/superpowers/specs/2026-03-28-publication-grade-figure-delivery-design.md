# Publication-Grade Figure Delivery v1 Design

## 1. Goal

Push the current submarine `vibe CFD` stack beyond preview PNGs and into a first research-facing figure delivery layer that is:

- deterministic
- provenance-rich
- reviewable in final reports
- directly consumable in the workbench

This stage is not about making the UI prettier in isolation. It is about making generated figures credible delivery artifacts inside the same evidence chain that now already covers studies, experiments, research evidence, and supervisor gating.

## 2. Why This Is The Right Next Step

The repository already has:

- requested-output contracts
- deterministic postprocess export
- PNG preview artifacts for surface pressure and wake slices
- result cards in the workbench
- scientific verification, experiment registry, unified research evidence, and supervisor gating

What it still lacks is a figure layer that can support research review rather than only demo inspection.

Right now the main gaps are:

- PNGs are deterministic previews, not richer delivery figures
- provenance is visible as loose text, not as structured per-figure metadata
- final reporting does not yet have a dedicated figure-delivery contract
- the workbench knows how to show image cards, but not how to explain figure meaning, selector provenance, or render quality

That makes `Publication-Grade Figure Delivery v1` the highest-value next slice after the scientific state machine.

## 3. Design Constraint

Keep the same architectural rule we used for the scientific workflow:

- user intent stays open-ended
- execution and evidence stay structured and deterministic

So this stage must not turn figure generation into a fixed workflow shell. The user can still ask for different outputs in flexible language. The repository should simply become much stricter and more explicit about how it renders, captions, and records the figures it generates.

## 4. Approaches Considered

### Approach A: Upgrade The Existing Deterministic Postprocess Path

Use the current DeerFlow postprocess/export layer, add a typed figure manifest, upgrade the PNG rendering and provenance summaries, then teach reporting and the workbench to consume that manifest.

Pros:

- fits the current repo structure
- keeps figures inside the deterministic evidence chain
- no new heavyweight plotting dependency is required
- minimal risk of splitting backend truth from frontend presentation

Cons:

- requires careful refactoring because `postprocess.py` is already carrying several responsibilities

### Approach B: Add A Separate Plotting Subsystem

Introduce a new plotting stack such as `matplotlib` or Plotly-style rendering and make the backend export a second, more specialized figure pipeline.

Pros:

- could eventually support richer plot families

Cons:

- new dependency and environment risk
- higher chance of bifurcating “real evidence” and “display figures”
- too large for the next focused stage

### Approach C: Frontend-Only Figure Polish

Keep backend artifacts unchanged and improve only the workbench cards and image layout.

Pros:

- fast

Cons:

- does not improve provenance
- does not strengthen figure delivery as a scientific artifact
- would mostly be cosmetic

## 5. Recommended Approach

Use **Approach A**.

This keeps the system true to the project’s core principle:

- the frontend behaves like an agentic workbench
- the backend remains the deterministic owner of scientific artifacts

## 6. Scope

### In Scope

- richer deterministic rendering for:
  - `surface_pressure_contour`
  - `wake_velocity_slice`
- a new structured `figure-manifest.json`
- figure caption and provenance metadata
- final report propagation of figure-delivery metadata
- workbench support for figure-manifest-driven cards

### Out Of Scope

- streamlines
- arbitrary user-authored figure grammars
- full compare-plot generation across experiments
- a new plotting dependency such as `matplotlib`
- publication-ready journal layout for every possible figure family

## 7. Architecture

### 7.1 Backend Figure Contract

Add a focused figure-delivery contract layer for submarine postprocess outputs.

The new contract should describe each generated figure in terms of:

- `figure_id`
- `output_id`
- `title`
- `caption`
- `render_status`
- `field`
- `selector_summary`
- `axes`
- `color_metric`
- `sample_count`
- `value_range`
- `artifact_virtual_paths`
- `source_csv_virtual_path`

At the run level, the manifest should expose:

- `run_id` or run-directory identity
- `figure_count`
- `figures`
- `artifact_virtual_paths`

This gives the repository one stable place to answer:

- what figure was generated
- what it represents
- how it was rendered
- where its provenance artifacts live

### 7.2 Backend Rendering Upgrade

The current PNGs are simple scatter previews. This stage upgrades them into more reviewable delivery figures while keeping them deterministic and dependency-light.

The renderer should add:

- clearer titles
- stable margins and plot frame
- denser axes treatment
- more explicit color legend
- better numeric range labeling
- a provenance footer or caption block embedded in the image/report pair

For `wake_velocity_slice`, the repository should surface the selector provenance explicitly:

- plane origin mode
- origin value
- normal direction

For `surface_pressure_contour`, it should surface:

- sampled field
- patch selector summary

The result does not need to be “journal perfect,” but it should no longer feel like a disposable preview.

### 7.3 Manifest-Driven Reporting

`reporting.py` should stop inferring figure meaning only from artifact suffixes.

Instead it should load `figure-manifest.json` and emit a compact `figure_delivery_summary` into `final-report.json`.

That summary should include:

- figure count
- manifest path
- figure status lines
- caption/provenance highlights
- artifact entrypoints

This keeps final reporting aligned with the new contract and makes figure delivery part of the structured evidence trail.

### 7.4 Workbench Consumption

The submarine workbench should consume the figure summary and manifest metadata rather than only the raw artifact path list.

The existing requested-result cards are the right UI anchor. They already connect:

- requested outputs
- delivery status
- attached artifacts

This stage should extend them with:

- figure caption text
- selector provenance
- field / axis / sample summaries
- manifest-backed artifact entrypoints

That preserves the current workbench shape while making the figure cards substantially more scientific.

## 8. File Strategy

### Backend

- Keep `postprocess.py` focused on discovery, export orchestration, and renderer invocation.
- Introduce a new focused module for figure metadata and manifest shaping so we do not keep bloating `postprocess.py`.
- Update `reporting.py` to load and summarize the manifest.

### Frontend

- Extend `submarine-runtime-panel.utils.ts` with figure-summary parsing.
- Extend `submarine-runtime-panel.tsx` by enriching the existing requested-result cards instead of creating a parallel figure workspace.

## 9. Data Flow

1. Requested outputs still enter through the existing structured output contract.
2. Solver dispatch still generates CSV / PNG / Markdown artifacts deterministically.
3. Figure-delivery code writes `figure-manifest.json`.
4. Result reporting loads the manifest and adds `figure_delivery_summary`.
5. Workbench utilities parse the summary.
6. Requested-result cards render figure caption and provenance from structured metadata.

## 10. Testing Strategy

### Backend

- add targeted tests for figure-manifest generation
- add rendering tests that verify caption / metadata fields rather than image pixels alone
- add report tests for `figure_delivery_summary`

### Frontend

- add utility tests for manifest parsing and figure-card provenance summaries
- use `tsc` and focused lint as the main UI wiring gates

## 11. Success Criteria

This stage is successful when:

- each supported figure artifact can be explained by a structured manifest
- final reports link figure delivery as a first-class artifact layer
- requested-result cards show figure provenance and caption details
- the output still feels like open-ended `vibe CFD`, not a hard-coded report wizard

## 12. Remaining Gap After This Stage

Even after this stage, the repository will still not be the final research platform.

Later slices will still need:

- richer compare figures across experiment variants
- more figure families such as streamlines
- deeper uncertainty or validation overlays on figures
- more advanced publication templates

But this stage closes the most important current delivery gap: turning generated figures from “nice previews” into structured scientific deliverables.
