# OpenFOAM Official Case Seed Import Design

## Goal

Add a user-visible input path that lets a researcher import the minimal executable seed files for an official OpenFOAM tutorial case, describe or modify the remaining run conditions in the chat box, and then drive the full VibeCFD chain from the frontend: case assembly, execution, result collection, file presentation, and Chinese report generation.

This slice is not an "official-case demo button". It is a real product test path that should behave like ordinary user work:

1. import seed files from a real official tutorial
2. describe desired setup in chat
3. let the main agent interpret and complete the case
4. run inside the same sandbox boundary as normal work
5. verify that process, outputs, and report are visible in the frontend

## Validated Current State

- The current submarine-oriented execution chain is strongly STL-first.
  - `submarine_geometry_check`
  - `submarine_design_brief`
  - `submarine_solver_dispatch`
  all assume or strongly prefer an uploaded `.stl` geometry path.
- The current runtime can execute modern steady incompressible OpenFOAM cases in the sandbox.
  - The generated project scaffold now uses `foamRun / incompressibleFluid`.
  - The local sandbox image contains official OpenFOAM 13 tutorials.
- The current `openfoam-reference` skill is reference-only and intentionally does not provide an execution entrypoint.
- Official tutorial validation already proved:
  - `cavity` can complete in the sandbox
  - `pitzDaily` enters real `foamRun` iterations but is heavier and may need longer runtime windows

## User Problem To Solve

Today, a user who wants to test the system with a real OpenFOAM tutorial cannot do so through the product in a natural way.

The user should be able to say, through the normal frontend workbench:

- "I uploaded the official cavity seed files. Run with the official defaults and show me the result report."
- "I uploaded the pitzDaily seed files. Keep the official geometry, but change the run end time and give me a Chinese summary."

The system should not require the user to upload an STL when the tutorial itself is blockMesh-driven.

## Design Principles

- Real user path, not hidden demo logic.
- Preserve the same sandbox execution boundary and artifact model as the main product.
- Import the smallest truthful case seed, then let the agent synthesize the rest.
- Keep official OpenFOAM defaults reproducible and auditable.
- Separate "official case source files" from "generated VibeCFD runtime case".

## Pinned Official Source Baseline

For this slice, "official defaults" must not mean "whatever OpenFOAM happens to ship later".

The authoritative baseline is:

- OpenFOAM 13 tutorial tree
- pinned to the exact upstream commit already used in the repo-local validation artifacts:
  - `441953dfbb4270dd54e14672e194e4a4a478afc4`

Every synthesized or reconstructed file for `cavity` and `pitzDaily` must record provenance in a dedicated manifest that includes:

- official source commit
- official tutorial-relative source path
- whether the assembled file was:
  - copied directly from imported seed
  - copied from pinned official source
  - synthesized from pinned official defaults
  - overridden from user chat instructions
  - adapted for project runtime compatibility

Without this manifest, the run must not be described as an "official-default reconstruction".

## Prior Art / Reuse Decision

Reuse and extend the current VibeCFD execution path rather than creating a parallel demo executor.

- Reuse:
  - current frontend chat input and thread/workbench surfaces
  - current sandbox execution boundary
  - current file/artifact presentation model
  - current reporting pipeline
- Adapt:
  - input resolution so a thread may be seeded by OpenFOAM case files instead of STL only
  - design brief / dispatch runtime contracts so "official case seed" is first-class
- Do not build:
  - a special hard-coded cavity/pitzDaily frontend wizard
  - a disconnected tutorial runner with separate logs and report rules

## Chosen Input Model

Introduce a second high-level input family beside STL geometry:

1. `geometry_seed`
2. `openfoam_case_seed`

### `openfoam_case_seed`

This means the user uploads the minimum official files needed to reconstruct or truthfully derive a runnable case.

The first supported official seeds are:

#### `cavity`

Required seed file set:

- `system/blockMeshDict`

Optional imported seed files if the user wants to preserve the official defaults directly instead of restating them in chat:

- `0/U`
- `0/p`
- `constant/physicalProperties`
- `system/controlDict`
- `system/fvSchemes`
- `system/fvSolution`

Recommended product test mode for this slice:

- require `system/blockMeshDict`
- allow the agent to synthesize the rest from official defaults when omitted

Execution profile for this case:

- preserve the official legacy stack for validation
- solver path: `blockMesh` -> `icoFoam`
- do not silently modernize `cavity` into `foamRun / incompressibleFluid` for this slice
- if user asks for a modernized equivalent, that is a different experiment and must be labeled as such in provenance and reporting

#### `pitzDaily`

Required seed file set:

- official blockMesh seed equivalent to `tutorials/resources/blockMesh/pitzDaily`

Optional imported seed files:

- `0/U`
- `0/p`
- `0/k`
- `0/T`
- `0/nut`
- `0/alphat`
- `0/muTilda`
- `constant/physicalProperties`
- `constant/momentumTransport`
- `system/controlDict`
- `system/functions`
- `system/fvConstraints`
- `system/fvSchemes`
- `system/fvSolution`

Recommended product test mode for this slice:

- require the official `pitzDaily` blockMesh seed
- allow the agent to synthesize or preserve the remaining files based on user instructions and default-mode selection

Execution profile for this case:

- preserve the official modern tutorial stack for validation
- solver path: `blockMesh -dict <official pitzDaily seed>` -> `foamRun`
- maintain the official tutorial's modern control structure rather than projecting submarine-runtime conventions onto it

## Import Precedence And Ambiguity Rules

The resolver must use deterministic precedence rules because the existing product is STL-first.

### Source-family precedence

1. explicit user intent in chat
2. valid `openfoam_case_seed` file set
3. valid STL geometry upload

If the thread contains both a valid case seed and a valid STL, the system must not guess. It must ask the user whether the run should be:

- official OpenFOAM case reconstruction
- STL-based submarine workflow

### Minimum-valid imports

`cavity` is valid only when:

- `system/blockMeshDict` is present

`pitzDaily` is valid only when:

- the official `pitzDaily` blockMesh seed is present

### Partial imports

If the upload contains a recognizable but incomplete official seed set, the system must:

- classify the candidate case tentatively
- explain exactly which required seed file is missing
- stop before assembly or execution

It must not fall back silently to the STL path or a generic submarine path.

## User Experience

### Upload

The existing attachment flow remains the entrypoint.

The system should accept uploaded OpenFOAM seed files and store them in the same thread-local upload area as normal files.

### Chat

The user provides the remaining instructions in ordinary chat, for example:

- "Use the official cavity defaults and generate the full run report."
- "Use pitzDaily official defaults, but set a longer end time and export key flow-field outputs."

### Agent Interpretation

The main agent should detect that:

- the thread contains OpenFOAM seed files rather than STL geometry
- the task is an official OpenFOAM case reconstruction / execution request
- the correct execution path is case-seed assembly, not submarine geometry preflight

### Execution

The system should:

1. classify the imported seed set
2. bind an `official_case_id`
3. assemble a runnable case directory under the thread workspace
4. run the case inside the sandbox
5. expose logs, results, and report through the existing frontend

## Architecture Changes

### 1. New Runtime Source Type

Extend the runtime/design-brief contract with:

- `input_source_type`: `geometry_seed` | `openfoam_case_seed`
- `official_case_id`: nullable string
- `official_case_seed_virtual_paths`: list of imported seed files
- `official_case_profile`: summary of what was preserved from imports versus synthesized by the agent

### 2. New Case-Seed Resolution Path

Add a dedicated resolver for OpenFOAM seed files.

Responsibilities:

- inspect uploaded files
- recognize supported official seeds
- validate minimum required files
- reject ambiguous or incomplete imports with a clear user-facing explanation
- preserve deterministic source-family precedence when STL and case seeds coexist

This resolver should not be mixed into the STL suffix gate. It should be a parallel input path.

### 3. New Official-Case Assembly Layer

Add a case assembly unit that can build a runnable case from:

- imported seed files
- official default assumptions
- user chat instructions

Responsibilities:

- copy preserved seed files into the assembled workspace case
- synthesize missing files when allowed
- record provenance for each assembled file
- stamp whether each file came from:
  - imported official seed
  - official default reconstruction
  - user-requested override
  - project compatibility synthesis

### 4. Dispatch Generalization

Generalize solver dispatch so it can run:

- STL-derived submarine cases
- official-case-seed cases

without pretending the latter are submarine geometry flows.

The official-case path should bypass submarine geometry inspection when no STL is involved.

The dispatch layer must select execution behavior from a case-specific execution profile, not from one generalized "official case" branch.

Required initial profiles:

- `cavity`
  - `blockMesh`
  - `icoFoam`
- `pitzDaily`
  - `blockMesh -dict <official pitzDaily seed>`
  - `foamRun`

If the case-specific execution profile is missing, dispatch must fail closed rather than guessing a solver stack.

### 5. Reporting Generalization

Result reporting must stop assuming every run has a geometry upload.

For official-case runs, the report should show:

- official case name
- official source commit and tutorial path
- imported seed files
- preserved official defaults
- user-provided overrides from chat
- execution command and sandbox provenance
- key result files
- comparison against expected tutorial behavior where possible

## Frontend Changes

### Input Surface

Do not add a special tutorial wizard in this slice.

Keep the normal:

- file attachment button
- chat box
- thread/workbench

### File Awareness

The file panel should clearly distinguish:

- imported seed files
- assembled runtime case files
- generated result artifacts

### Thread Feedback

The workbench should surface:

- detected official case type
- whether default reconstruction is pending or complete
- whether execution is using official defaults or user overrides

## Verification Strategy

This slice is complete only if it passes product-style validation from the frontend, not just backend unit tests.

### Required Product Tests

#### Test 1: `cavity` Official Default Reconstruction

1. Upload the minimal `cavity` seed file set through the frontend
2. In chat, request an official-default run
3. Let the main agent assemble and run the case
4. Verify:
   - case classification is correct
   - runtime process is visible in the frontend
   - file panel shows seed files, assembled case, logs, and report
   - solver completes successfully
   - report describes the case truthfully as an official tutorial reconstruction

#### Test 2: `cavity` User Override

1. Upload the same seed
2. In chat, request one controlled change such as end time or lid velocity
3. Verify the override appears in the assembled case and report

#### Test 3: `pitzDaily` Official Default Reconstruction

1. Upload the minimal `pitzDaily` seed file set
2. In chat, request an official-default run
3. Verify:
   - case classification is correct
   - execution enters the real solve path
   - process and files are visible in the frontend
   - report captures heavy-case runtime reality honestly
   - provenance manifest shows pinned official source commit and per-file source classification

#### Test 4: `pitzDaily` User Override

1. Upload the same seed
2. In chat, request one controlled override such as longer end time or output emphasis
3. Verify the assembled case and report reflect the override

### Expected Result Policy

- `cavity` should be treated as the first full-pass product validation target.
- `pitzDaily` may require longer or asynchronous execution windows, but the frontend product flow itself must still work correctly.
- Do not fake success for `pitzDaily` just because the official tutorial is known-good in principle.

### Explicit Acceptance Gates

#### `cavity`

A run passes the product gate only if all of the following are true:

- the frontend upload + chat path classifies the case as `cavity`
- the assembled case preserves the `cavity` legacy execution profile
- `blockMesh` succeeds
- `icoFoam` exits successfully
- the file panel exposes imported seed, assembled case, execution log, result artifacts, and final report
- the report includes pinned-official provenance and no false "modern OF13 parity" claim

#### `pitzDaily`

A run passes the product gate only if all of the following are true:

- the frontend upload + chat path classifies the case as `pitzDaily`
- the assembled case preserves the `pitzDaily` modern execution profile
- `blockMesh` succeeds
- `foamRun` enters the real solve path
- the file panel exposes imported seed, assembled case, execution log, result artifacts, and final report
- the report includes pinned-official provenance and explicitly states whether the solve fully completed or only partially advanced within the allowed runtime window

For this slice, a `pitzDaily` run may be marked:

- `completed` when the solve exits successfully
- `partial-but-valid-product-flow` only when:
  - the runtime window was reached
  - the execution log proves the real solve path was entered
  - the report and UI label the run as incomplete rather than complete

This second status is acceptable only for validating the frontend product flow and must not be reported as full numerical completion.

## Non-Goals For This Slice

- Full generalized import of arbitrary OpenFOAM tutorial families
- Automatic support for every OpenFOAM physics family
- Replacing the existing submarine STL path
- Shipping a hard-coded official tutorial launcher as the primary UX

## Implementation Recommendation

Implement this as one coherent slice:

1. add case-seed import classification and runtime contract changes
2. add official-case assembly support
3. generalize dispatch/reporting
4. validate from the real frontend using `cavity` and `pitzDaily`
