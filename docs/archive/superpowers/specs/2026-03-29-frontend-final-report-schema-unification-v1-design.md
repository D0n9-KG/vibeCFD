# Frontend Final Report Schema Unification v1 Design

## 1. Goal

Create one shared frontend contract module for the submarine workbench's parsed report payloads so `submarine-runtime-panel.tsx` and `submarine-runtime-panel.utils.ts` stop carrying duplicated final-report schema definitions.

The stage is intentionally narrow:

- remove duplicated payload typing
- keep runtime behavior and UI unchanged
- reduce future report-field regression risk before larger backend cleanup

## 2. Why This Is The Right Next Slice

The project is already deep enough into scientific execution, evidence, remediation, and follow-up layers that the main short-term engineering risk is no longer "missing one more feature tile." It is contract drift.

The most recent `scientific_followup_summary` regression came from exactly that drift:

- the page component had its own local `FinalReportPayload`
- the summary builders in `submarine-runtime-panel.utils.ts` accepted separate anonymous payload shapes
- a backend payload field changed, but the frontend had no single typed place to absorb that change

If we keep layering more research-facing report fields onto that pattern, the workbench will become brittle long before the repo reaches true research readiness.

## 3. Design Options

### Option A: Keep Local Types And Patch Missing Fields As Regressions Appear

Pros:

- smallest immediate diff

Cons:

- preserves the exact failure mode that already happened
- guarantees more drift as report payloads grow
- makes later backend decomposition harder because frontend contracts stay implicit

### Option B: Extract One Shared Parsed-Payload Contract Module

Pros:

- one source of truth for parsed report payload types
- lets the page component depend on contract types without importing view-model helpers
- keeps summary/view-model code in `utils` while separating raw payload contracts cleanly

Cons:

- small migration cost across component and utils imports

### Option C: Jump Straight To Runtime Schema Validation With Zod Or Similar

Pros:

- strongest eventual contract boundary

Cons:

- too large for the current cleanup slice
- mixes architectural hygiene with new runtime behavior and validation semantics

## 4. Recommendation

Implement Option B now.

Create a dedicated contract module under the existing submarine workbench component area and move the shared parsed-payload types there, including:

- design-brief payload
- acceptance / verification assessment payload fragments
- solver / dispatch / geometry payloads
- final-report payload and its nested scientific summary blocks

Then:

- `submarine-runtime-panel.tsx` should parse artifacts using those shared types
- `submarine-runtime-panel.utils.ts` should accept those same shared types in builder signatures
- summary/view-model output types should remain in `utils`

This gives the repo a clean contract/view-model split without changing product behavior.

## 5. Proposed File Boundaries

### New Shared Contract Module

- Create: `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`
  - raw parsed artifact payload contracts used by both the page and utils

This file should contain only parsed-contract types, not rendering helpers, labels, or summary builders.

### Existing View-Model Utility Module

- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - keep summary builders and derived UI models
  - import shared payload contracts instead of defining them inline or via anonymous structural signatures

### Existing Page Component

- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - import shared payload contracts from the new contract module
  - delete the local duplicated `FinalReportPayload` and related raw payload types that belong in the shared contract file

## 6. Product Boundary

This stage should not:

- change any rendered section ordering
- add new data fields to the UI
- add new backend fields
- introduce runtime validation failures for previously accepted payloads

This stage should only:

- centralize raw frontend payload contracts
- remove duplicated schema definitions
- make future report evolution safer

## 7. Success Criteria

This stage is successful when:

- the submarine workbench parses final-report payloads from one shared type source
- `submarine-runtime-panel.utils.ts` no longer declares ad-hoc final-report payload fragments for its builder inputs
- the page component no longer carries a separate local `FinalReportPayload`
- existing frontend tests and TypeScript checks still pass with no UI behavior changes

## 8. Why This Matters For Research Readiness

This cleanup does not directly add new CFD science capability. But it is still part of making the repo genuinely research-usable.

A research-facing `vibe CFD` system must survive repeated growth in:

- benchmark evidence fields
- remediation contracts
- follow-up history
- experiment compare metadata
- provenance and publication summaries

Without a clean frontend contract boundary, every new research layer increases the chance that the workbench silently drifts away from the backend evidence model. This slice reduces that risk before the next larger decomposition stages.
