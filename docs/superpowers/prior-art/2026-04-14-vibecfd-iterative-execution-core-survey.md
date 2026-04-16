# VibeCFD Iterative Execution Core Prior Art Survey

**Question:** For a `vibeCFD`-style product, how should we evolve the existing submarine workflow so it behaves like a collaborative CFD execution partner for researchers rather than a one-shot solver wrapper or a generic workflow engine?

**Constraints:**
- The product goal is `vibeCFD`, not a generic workflow platform and not a scientific decision oracle.
- We must preserve the current DeerFlow architecture, existing submarine contracts, and visible frontend interaction model.
- The system must support iterative negotiation, task replanning, multi-agent execution, repeat runs, variant management, and artifact traceability.
- We should prefer adapting the current codebase and native solver capabilities over introducing a heavy external orchestration stack.

## Candidate References

- **signac / signac-flow**: A research workflow framework centered on an indexable data space, jobs, job documents, stores, workflow operations, grouping, and cluster submission. It is strong at reproducible simulation spaces and operation orchestration, especially where many runs share a common schema. Official docs: [signac documentation](https://signac.readthedocs.io/en/latest/).
- **Dakota parameter studies**: A mature parameter-study engine emphasizing deterministic study shapes such as vector, list, centered, and multidimensional sweeps, with explicit response cataloguing and sensitivity-analysis framing. Official docs: [Dakota parameter studies](https://snl-dakota.github.io/docs/6.18.0/users/usingdakota/studytypes/parameterstudies.html).
- **OpenFOAM function objects**: Native solver-side facilities for producing additional user-requested data during runtime and post-processing, standardizing batch post-processing sequences, and reducing manual interaction. Official docs: [OpenFOAM function objects](https://www.openfoam.com/documentation/guides/latest/doc/guide-function-objects.html).
- **ASME V&V 20**: A formal verification and validation framing for CFD credibility, focused on quantified accuracy relative to specified validation variables and validation points. Official standard page: [ASME V&V 20](https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-fluid-dynamics-and-heat-transfer).
- **ITTC uncertainty-analysis procedures and benchmark repository**: Marine hydrodynamics guidance for CFD uncertainty analysis, resistance/flow validation examples, and benchmark-oriented workflow expectations. Official sources: [ITTC uncertainty analysis procedure](https://ittc.info/media/11954/75-03-02-01.pdf), [ITTC benchmark repository](https://ittc.info/benchmark-repository/).
- **OpenMDAO**: A multidisciplinary design, analysis, and optimization framework focused on high-fidelity coupling and analytic derivatives. It is informative for future high-end optimization integration, but heavier than what we need for the current `vibeCFD` core. Official site: [OpenMDAO](https://openmdao.org/).

## Reuse Options

- **Reuse dependency**
  - **Suitable:** Continue reusing OpenFOAM-native post-processing and runtime data production mechanisms, especially function-object style outputs, within our generated case configurations.
  - **Not suitable:** Bringing in signac, Dakota, or OpenMDAO as hard dependencies right now would add a second orchestration model on top of DeerFlow.

- **Adapt existing project**
  - **Suitable:** The current project already has the right seeds:
    - structured submarine runtime contracts in `backend/packages/harness/deerflow/domain/submarine/contracts.py`
    - task contracts and output negotiation in `backend/packages/harness/deerflow/domain/submarine/design_brief.py` and `output_contract.py`
    - experiment and study manifests in `solver_dispatch.py`
    - built-in subagent roles for `task-intelligence`, `scientific-study`, `experiment-compare`, `scientific-verification`, and `result-reporting`
  - This is the strongest base and should remain the primary implementation path.

- **Fork and modify**
  - **Not suitable:** No external project cleanly matches our mixed requirements of conversational planning, visible thread interaction, DeerFlow state, and CFD-domain execution.

- **Reference only**
  - **Recommended:** Borrow structural ideas from signac and Dakota, and credibility/evidence expectations from ASME / ITTC, while implementing them in DeerFlow-native contracts and manifests.

- **Build from scratch**
  - **Not suitable as a pure strategy:** A full greenfield workflow engine would ignore the strong existing domain-specific architecture already present in this repo.

## Recommended Strategy

- **Primary strategy:** `adapt existing project`
- **Secondary strategy:** `reference only`
- **Target shape:** Keep DeerFlow as the orchestration backbone, evolve the submarine runtime contract into a stronger iterative research task contract, and use the existing experiment/study manifest infrastructure as the backbone for replanning and lineage.

## Why This Wins

- The current codebase already models:
  - explicit runtime stages
  - execution outlines
  - requested outputs
  - scientific-study manifests
  - experiment manifests
  - follow-up history
  - runtime skill snapshots
- signac validates the value of a stable run/job schema and explicit metadata space, which maps well to our thread/runtime state and experiment manifests.
- Dakota validates the need for first-class parameter-study shapes and deterministic variation patterns, which we can express through custom variants and study manifests without importing Dakota itself.
- OpenFOAM function objects align directly with our need to turn “researcher requested outputs” into reliable runtime/post-process artifacts.
- ASME / ITTC confirm that research-grade tooling should treat benchmark applicability, uncertainty, and evidence boundaries as explicit workflow data rather than informal report prose.
- This path keeps us focused on `vibeCFD`: a collaborative CFD tool, not a general workflow engine.

## Why Not The Others

- **Pure prompt/skill-first approach:** Too brittle for long-running iterative CFD work; it makes the system sound smart without making run lineage, task contracts, and execution stability strong enough.
- **Generic workflow-engine-first approach:** Risks drifting away from the product identity and duplicating orchestration concerns that DeerFlow already handles.
- **Full optimization framework adoption:** Valuable later for advanced design-space exploration, but currently overkill relative to our mainline need: stable collaborative execution and iteration.

## Sources

- signac documentation: https://signac.readthedocs.io/en/latest/
- Dakota parameter studies: https://snl-dakota.github.io/docs/6.18.0/users/usingdakota/studytypes/parameterstudies.html
- OpenFOAM function objects: https://www.openfoam.com/documentation/guides/latest/doc/guide-function-objects.html
- ASME V&V 20 standard page: https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-fluid-dynamics-and-heat-transfer
- ITTC uncertainty analysis procedure: https://ittc.info/media/11954/75-03-02-01.pdf
- ITTC benchmark repository: https://ittc.info/benchmark-repository/
- OpenMDAO: https://openmdao.org/
