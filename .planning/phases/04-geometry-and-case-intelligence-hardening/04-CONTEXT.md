# Phase 4: Geometry and Case Intelligence Hardening - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Improve geometry trust, scale assumptions, and case knowledge before solver execution so researchers receive defensible setup recommendations and a reviewable calculation plan.

This phase hardens the existing STL-first submarine workflow by:
- detecting geometry integrity, unit/scale, and reference-value risks before solver dispatch;
- upgrading case-library provenance and acceptance-profile quality; and
- turning geometry/case assumptions into a researcher-reviewable calculation-plan draft rather than silent AI decisions.

This phase does not add CAD-first intake, new CFD domains, or a new claim-level taxonomy.

</domain>

<decisions>
## Implementation Decisions

### Researcher authority and plan approval
- **D-01:** The system should generate a calculation-plan draft for geometry and case assumptions instead of autonomously deciding ambiguous inputs.
- **D-02:** Real computation cannot start until the draft is researcher-confirmed.
- **D-03:** The researcher must be able to approve directly, modify the draft and then approve, or send it back for revision.

### Dynamic clarification strategy
- **D-04:** The lead agent should decide dynamically whether to interrupt for clarification based on the completeness of the initial user input, evidence quality, and risk severity rather than a fixed mandatory checklist.
- **D-05:** Severe uncertainties that materially affect geometry family, unit/scale interpretation, reference values, or case applicability must be confirmed before solver dispatch continues.
- **D-06:** Lower-risk or well-supported assumptions should stay inside the draft for consolidated review instead of triggering unnecessary interruptions.

### Case and reference presentation
- **D-07:** When a recommended case has real references, the draft must show the suggested value or range together with source, confidence, and applicability conditions.
- **D-08:** Recommended case/profile choices are advisory inputs for the researcher, not automatic selections.
- **D-09:** The approved plan must clearly record which values came from the researcher, which were AI suggestions, and which were edited by the researcher before approval.

### Weak references and uncertainty disclosure
- **D-10:** Weak-reference or placeholder-backed cases may still appear as suggestions, but only with explicit disclosure of missing evidence and uncertainty.
- **D-11:** Phase 4 should not introduce an additional trust-tier or engineering-only status ladder; weak references and estimated values should be handled through clear disclosure plus researcher confirmation records.
- **D-12:** The product should prefer a simple approval model with plan items marked as pending researcher confirmation or researcher confirmed, rather than a broad new taxonomy of trust states.
- **D-13:** Existing scientific claim levels (`delivery_only`, `verified_but_not_validated`, `validated_with_gaps`, `research_ready`) should remain in place for post-compute evidence and report gating, but they must not be reused to describe pre-compute geometry/case approval state.
- **D-14:** Researcher confirmation means the calculation plan is approved for execution; it must not be treated as automatic evidence that raises the post-compute scientific claim level.

### The Agent's Discretion
- Exact heuristics and thresholds for deciding whether an uncertainty is severe enough to require immediate clarification
- Exact UI layout and wording for the calculation-plan draft and approval actions
- Exact metadata shape for storing proposal provenance and researcher edits, as long as the final approved plan preserves who supplied or confirmed each critical assumption

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and roadmap anchors
- `.planning/PROJECT.md` - product purpose, scientific-integrity constraints, and submarine-only milestone boundary
- `.planning/REQUIREMENTS.md` - `GEO-01`, `GEO-02`, and `GEO-03` define the Phase 4 scope
- `.planning/ROADMAP.md` - Phase 4 goal, success criteria, and plan split (`04-01` to `04-03`)
- `.planning/STATE.md` - current blockers and the handoff from completed Phase 3 work

### Prior phase decisions that still apply
- `.planning/phases/01-end-to-end-workbench-bootstrap/01-CONTEXT.md` - the submarine cockpit remains the real operator path
- `.planning/phases/02-runtime-solver-productization/02-CONTEXT.md` - thread-bound geometry and persisted runtime state remain the source of truth
- `.planning/phases/03-scientific-verification-gates/03-CONTEXT.md` - missing or mismatched scientific evidence must stay explicit and visible

### Geometry preflight and runtime handoff
- `backend/packages/harness/deerflow/domain/submarine/geometry_check.py` - current geometry parsing, family defaults, length normalization, summary artifacts, and next-stage behavior
- `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py` - geometry-preflight tool wiring, runtime snapshot updates, and existing confirmation blocking behavior
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_case.py` - downstream use of geometry estimates to derive reference length, reference area, and case scaffold scale
- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - runtime snapshot, review contract, and existing scientific gate / claim-level fields

### Case library and provenance
- `backend/packages/harness/deerflow/domain/submarine/library.py` - current case-ranking and case-match behavior
- `backend/packages/harness/deerflow/domain/submarine/assets.py` - source-of-truth loading for submarine domain assets
- `backend/packages/harness/deerflow/domain/submarine/models.py` - typed schema for case references, acceptance profiles, and geometry results
- `domain/submarine/cases/index.json` - case definitions, current reference sources, and acceptance profiles that Phase 4 must harden

### Workbench presentation surfaces
- `frontend/src/components/workspace/submarine-stage-cards.tsx` - geometry-preflight card behavior and stage-state presentation
- `frontend/src/components/workspace/submarine-runtime-panel.tsx` - cockpit summary, geometry/case visibility, and artifact-backed runtime context
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - frontend payload contract for geometry/runtime/report data
- `frontend/src/components/workspace/submarine-pipeline-status.ts` - current user-facing scientific gate and claim-level wording; Phase 4 should avoid introducing a conflicting extra taxonomy

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `geometry_check.py` already parses STL inputs, computes bounds, estimates length, ranks candidate cases, and writes geometry-check artifacts.
- `submarine_geometry_check_tool.py` already blocks on user confirmation when required and persists geometry/runtime fields into `submarine_runtime`.
- `library.py` plus `domain/submarine/cases/index.json` already provide a structured case index with reference sources and acceptance profiles.
- `submarine-stage-cards.tsx` and `submarine-runtime-panel.tsx` already render geometry-preflight summaries and selected-case context inside the submarine cockpit.
- `solver_dispatch_case.py` already consumes estimated geometry length and reference values, so Phase 4 can tighten trust before those values propagate into actual OpenFOAM setup.

### Established Patterns
- The dedicated submarine cockpit is the operator surface; review and approval UX should stay there instead of falling back to generic chat.
- Persisted thread/runtime state plus artifacts remain the source of truth across refresh and re-entry.
- Scientific limitations are surfaced explicitly rather than hidden, so geometry and case uncertainty should follow the same disclosure pattern.
- Existing scientific gate / claim-level fields are already in use; Phase 4 should preserve those flows for post-compute reporting while keeping pre-compute approval state simple and separate.

### Integration Points
- Geometry preflight must decide when to interrupt for immediate clarification versus when to place assumptions into the draft for final review.
- The approved draft needs to feed the same runtime state that solver-dispatch and reporting already consume.
- Case-library provenance and acceptance logic need to become inspectable from the workbench and carried into the calculation-plan draft.
- Solver dispatch should be gated on researcher-confirmed plan state rather than implicit AI assumptions.
- Post-compute scientific gates should continue to evaluate evidence quality independently, even when the plan itself was explicitly researcher-confirmed.

</code_context>

<specifics>
## Specific Ideas

- The researcher wants the AI to surface uncertainty, candidate values, and supporting references, but not silently make final geometry or case decisions on their behalf.
- Severe uncertainties may justify an early interruption, but the default experience should be a consolidated draft review rather than many small confirmation prompts.
- Cases with real references should display source, confidence, and applicability conditions next to suggested values or ranges.
- Weak or placeholder references should still be visible as suggestions when useful, but the plan must explain the missing evidence rather than hide it behind a new status ladder.
- The approved plan should preserve whether a value was user-provided initially, AI-suggested, or edited by the researcher during review.

</specifics>

<deferred>
## Deferred Ideas

- Native STEP / Parasolid intake remains outside the current milestone; Phase 4 hardens the STL path only.
- Automatic geometry cleanup or repair pipelines remain later work after trust, provenance, and approval flow are stabilized.

</deferred>

---

*Phase: 04-geometry-and-case-intelligence-hardening*
*Context gathered: 2026-04-02*
