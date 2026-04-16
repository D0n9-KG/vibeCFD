# Formal CFD Report Template Prior Art Survey

**Question:** How should VibeCFD upgrade the current submarine `final-report` artifact from a workflow-stage summary into a formal CFD technical report that still preserves full artifact traceability, including result files, OpenFOAM workspace files, and absolute host paths?

**Constraints:** Must fit the existing DeerFlow submarine reporting pipeline; must preserve machine-readable JSON plus markdown/html outputs; must include both user-facing technical narrative and exhaustive file provenance; must work for local-thread storage under `backend/.deer-flow/threads/<thread-id>/user-data/{outputs,workspace}`.

## Candidate References
- NASA NPARC Alliance CFD Validation Archive documentation guidance: emphasizes documenting geometry, grid, boundary conditions, numerical method, convergence, validation context, and archived supporting files. Source: https://www.grc.nasa.gov/WWW/wind/valid/document.html
- ASME V&V 20 framing for CFD verification and validation: formal separation of numerical verification, validation evidence, uncertainty / applicability limits, and conclusion boundaries. Source family: ASME V&V 20 standard materials and references to the standard.

## Reuse Options
- Reuse dependency: not suitable. This is not primarily a third-party rendering problem; it is a domain-specific report-composition problem built on our own payloads.
- Adapt existing project: suitable. Extend the existing `deerflow.domain.submarine.reporting` and `reporting_render` pipeline instead of introducing a second report stack.
- Fork and modify: not suitable. No external report generator offers the required combination of CFD-domain structure, provenance-aware payloads, and local absolute-path appendices.
- Reference only: suitable for report shape. NASA / ASME patterns are useful as structural guidance for sections and evidence boundaries.
- Build from scratch: not suitable. Replacing the current reporting pipeline would risk regressions and duplicate logic already present in `final-report.json`.

## Recommended Strategy
- Adapt existing project, using NASA / ASME reporting expectations as reference-only structure guidance.

## Why This Wins
- The current payload already contains most of the needed technical content: solver metrics, mesh summary, scientific verification, reproducibility, output delivery, and artifact paths.
- The gap is presentation and appendix completeness, not missing raw data.
- Upgrading the current renderer keeps frontend compatibility with `final-report.{json,md,html}` while producing a much more formal artifact for human users.

## Why Not The Others
- Reuse dependency: would still require heavy custom payload shaping and path/provenance logic.
- Fork and modify: no obvious external project is closer than our existing domain pipeline.
- Build from scratch: unnecessary churn; we already have tested report generation and should evolve it.

## Sources
- NASA NPARC CFD validation documentation guidance: https://www.grc.nasa.gov/WWW/wind/valid/document.html
- ASME V&V 20 standard family references for CFD verification / validation structure
