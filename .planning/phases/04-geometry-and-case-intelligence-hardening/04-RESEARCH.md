# Phase 4: Geometry and Case Intelligence Hardening - Research

**Researched:** 2026-04-02
**Domain:** Geometry preflight, case provenance, and researcher-approved calculation-plan gating over the existing DeerFlow submarine runtime
**Confidence:** MEDIUM

<user_constraints>
## User Constraints

- `GEO-01`: geometry preflight must detect STL integrity, unit/scale anomalies, and reference-length or reference-area assumptions before solve.
- `GEO-02`: case-library entries must use real references and explicit acceptance profiles rather than placeholder sources.
- `GEO-03`: non-research-ready geometries or ambiguous setups must be downgraded or blocked with clear justification.
- Final authority for ambiguous geometry and case assumptions belongs to the human researcher, not the agent.
- The system should generate a calculation-plan draft with suggested values or ranges, source, confidence, applicability conditions, and explicit missing-evidence disclosure where applicable.
- Real computation must not start until the draft is researcher-confirmed.
- Researcher confirmation stays separate from post-compute scientific claim level. It authorizes execution, but it does not automatically raise `allowed_claim_level`.
- Severe ambiguities can interrupt early, but the default experience should be a consolidated draft review instead of many mandatory prompts.

</user_constraints>

<research_summary>
## Summary

Phase 4 does not need a brand-new workflow. The codebase already contains the core pieces required to harden the STL-first path:

- `geometry_check.py` already parses STL inputs, computes triangle count and bounds, infers a geometry family, estimates length, ranks candidate cases, and writes geometry-check artifacts.
- `submarine_design_brief_tool.py`, `submarine_runtime_context.py`, and `contracts.py` already persist `confirmation_status`, `review_status`, `open_questions`, `selected_case_id`, `execution_plan`, and other draft-vs-confirmed runtime fields.
- `library.py`, `models.py`, and `domain/submarine/cases/index.json` already provide structured case entries with `reference_sources` and `acceptance_profile`.
- `submarine-stage-cards.tsx` and `submarine-runtime-panel.tsx` already surface review state, selected case, runtime timeline, and confirmation-oriented UI language in the submarine cockpit.

The gap is that these pieces are still disconnected from a research-grade pre-compute decision loop:

1. Geometry preflight is descriptive, not trustworthy. It records triangle count, bounds, and a guessed normalized length, but it does not emit structured anomaly severity, unit ambiguity, reference-value confidence, or "safe to continue" gating.
2. `solver_dispatch_case.py` still derives `reference_length_m` and `reference_area_m2` directly from `estimated_length_m` and the bounding box, so a weak geometry guess can silently flow into the OpenFOAM case scaffold.
3. Case ranking in `library.py` is lexical and family-based only. It does not expose reference strength, applicability conditions, or placeholder disclosure even though the case schema already contains raw reference lists.
4. Case-library coverage is uneven. `domain/submarine/cases/index.json` still contains multiple `https://example.com/...` placeholder sources for pressure, wake, Type 209, and free-surface entries. Only the SUBOFF baseline currently looks close to a benchmark-backed path.
5. There is no explicit calculation-plan artifact that records AI suggestions, researcher edits, final approval, and whether a severe uncertainty was escalated early.

Phase 4 should therefore harden the existing path in three layers:

- `04-01` establishes structured geometry integrity, scale, and reference-value findings.
- `04-02` hardens case-library provenance and acceptance-profile quality while keeping weak references visible with explicit disclosure.
- `04-03` turns geometry and case findings into a researcher-approved calculation-plan gate that blocks solver execution until confirmed.

</research_summary>

<existing_capabilities>
## Existing Capabilities We Can Reuse

### Geometry preflight already has real parsing and artifact output

- `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
  - parses binary and ASCII STL,
  - computes bounding-box extents,
  - derives `estimated_length_m`,
  - ranks candidate cases,
  - writes `geometry-check.json`, `.md`, and `.html`.
- `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py`
  - persists preflight output into `submarine_runtime`,
  - reconstructs thread-bound geometry paths,
  - already respects existing user-confirmation blocks from the design brief.

### Runtime state already knows draft vs confirmed

- `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
  - stores `confirmation_status`,
  - stores `open_questions`,
  - stores `selected_case_id`,
  - writes a draft/confirmed runtime snapshot before geometry preflight or solver dispatch.
- `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py`
  - already blocks later tools when `review_status == "needs_user_confirmation"` or `next_recommended_stage == "user-confirmation"`.
- `backend/packages/harness/deerflow/domain/submarine/contracts.py`
  - already separates runtime review state from post-compute `scientific_gate_status` and `allowed_claim_level`.

### Case-library structure already exists

- `backend/packages/harness/deerflow/domain/submarine/models.py`
  - already defines `ReferenceSource`, `SubmarineCase`, `SubmarineCaseAcceptanceProfile`, and `SubmarineBenchmarkTarget`.
- `backend/packages/harness/deerflow/domain/submarine/library.py`
  - already normalizes the case library and returns ranked `SubmarineCaseMatch` objects.
- `backend/tests/test_submarine_domain_assets.py`
  - already asserts that the SUBOFF baseline exposes an acceptance profile and benchmark target.

### Frontend surfaces for confirmation already exist

- `frontend/src/components/workspace/submarine-stage-cards.tsx`
  - already renders geometry-preflight, solver-dispatch, and supervisor-review stages,
  - already treats `needs_user_confirmation` as a first-class review state.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - already shows review status, selected case, execution outline, and runtime summary,
  - already keeps scientific gate and claim-level explanation separate.
- `frontend/src/components/workspace/submarine-confirmation-actions.ts`
  - already gives the workbench a place to express confirmation-related actions instead of falling back to generic chat-only semantics.

</existing_capabilities>

<code_level_findings>
## Code-Level Findings That Matter For Planning

### Finding 1: Geometry normalization is heuristic and currently one-way

`geometry_check.py` currently normalizes length with a very narrow heuristic:

- if the raw max dimension is `>= 100` and much larger than the family default, divide by `1000`;
- otherwise trust the raw number as meters;
- then write that result into `GeometryInspection.estimated_length_m`.

What is missing:

- no structured "why this unit guess was chosen" payload,
- no severity field for suspicious scale mismatch,
- no explicit anomaly rows for empty meshes, zero-size bounds, or family-length mismatch,
- no distinction between "strongly supported reference value" and "best available guess".

### Finding 2: Geometry preflight always points downstream toward solver dispatch

`run_geometry_check()` currently builds a supervisor review contract with:

- `review_status="ready_for_supervisor"`
- `next_recommended_stage="solver-dispatch"`

That means the artifact path is hard-coded toward continuation, even when the geometry estimate is only heuristic. Existing tests in `backend/tests/test_submarine_geometry_check_tool.py` assert this current behavior directly.

### Finding 3: Solver dispatch still trusts geometry estimates too early

`solver_dispatch_case.py` currently:

- computes `reference_length_m` directly from `geometry.estimated_length_m`,
- computes `reference_area_m2` from the normalized bounding box,
- uses those values for `forceCoeffs`, domain sizing, and case scaffold generation.

This is the exact propagation path Phase 4 must harden. If geometry preflight remains heuristic-only, solver dispatch turns a weak guess into a CFD input without a researcher approval checkpoint.

### Finding 4: Case ranking ignores provenance quality

`library.py` scores cases using:

- task-type equality,
- geometry-family match,
- token overlap,
- input-suffix match.

It does not currently score or expose:

- whether references are benchmark-grade vs tutorial-grade,
- whether URLs are placeholders,
- whether the case acceptance profile actually contains benchmark targets,
- whether a case should be surfaced as "advisory only".

### Finding 5: Placeholder provenance is a real, current product problem

`domain/submarine/cases/index.json` still contains placeholder URLs for multiple cases, including:

- `suboff-pressure`
- `joubert-wake`
- `joubert-template`
- `type209`
- `type209-openfoam`
- `free-surface`
- `joubert-drag-pressure`

This means Phase 4 must not assume every case can become benchmark-backed immediately. Some entries will need either real source replacement or explicit weak-evidence disclosure.

### Finding 6: The draft-vs-confirmed contract already exists, but not for geometry/case plan items

The existing brief/runtime contract already supports:

- `confirmation_status` (`draft` vs `confirmed`),
- `open_questions`,
- `review_status`,
- `selected_case_id`,
- `simulation_requirements`.

What is missing is a structured calculation-plan draft that can carry:

- per-item suggested value or range,
- source label and URL,
- applicability conditions,
- confidence or uncertainty note,
- whether the item came from user input, AI suggestion, or researcher edit,
- whether the item requires immediate clarification.

</code_level_findings>

<gaps>
## Product Gaps That Still Block Research-Usable Behavior

### Gap 1: No structured geometry-trust contract

The current geometry artifact is readable, but it is not machine-actionable enough to decide whether the agent may continue, must interrupt, or should prepare a draft for later approval.

### Gap 2: No provenance-aware candidate-case contract

Recommended cases currently surface title, score, rationale, and expected outputs, but not the provenance details a researcher actually needs before accepting a case as the template for a real study.

### Gap 3: No pre-compute calculation-plan artifact

The product still lacks a first-class artifact that says:

- what the agent inferred,
- what evidence supports each inference,
- which values are only suggestions,
- what the researcher changed,
- which items are still pending confirmation.

### Gap 4: Solver gating is not aligned with researcher authority

The code already knows how to block for user confirmation in general, but the geometry/case path still lacks a dedicated "researcher-approved calculation plan" gate before `execute_now` can continue.

### Gap 5: Pre-compute review state and post-compute claim level can be conflated accidentally

The frontend and runtime already render both review status and scientific gate status. Without a dedicated calculation-plan contract, it is too easy for implementation work to reuse claim-level language for pre-compute approval, which the user explicitly rejected.

</gaps>

<recommended_decomposition>
## Recommended Plan Decomposition

### 04-01: Geometry inspection hardening

Scope:

- add structured geometry findings for integrity, scale, and reference-value suggestions;
- carry those findings into solver-dispatch gating inputs;
- stop treating `estimated_length_m` as an unqualified green light.

Why first:

- it closes the most dangerous silent-propagation path,
- it defines the geometry evidence that later case and approval logic must consume.

### 04-02: Case reference and acceptance-profile hardening

Scope:

- replace or explicitly disclose placeholder references,
- enrich case metadata with applicability conditions and evidence-gap notes,
- make case-ranking outputs provenance-aware.

Why second:

- geometry hardening defines the input facts,
- case hardening defines the library evidence that should be shown in the draft,
- both are needed before the final approval loop is productized.

### 04-03: Calculation-plan draft, blocking, and approval flow

Scope:

- introduce a calculation-plan draft contract,
- implement dynamic early clarification vs consolidated review,
- block solver execution until the researcher confirms the plan,
- keep this pre-compute approval state separate from post-compute claim levels.

Why third:

- it should consume the geometry findings from `04-01`,
- it should consume the provenance-aware case metadata from `04-02`,
- it is where the user's locked product semantics become real runtime behavior.

</recommended_decomposition>

<architecture_guidance>
## Architecture Guidance

### Backend ownership

- `geometry_check.py`
  - should own raw STL-derived findings and suggested geometry reference values,
  - should not own final approval authority.
- `solver_dispatch_case.py`
  - should consume approved reference values or explicitly marked low-risk defaults,
  - should no longer silently treat every normalized estimate as trusted input.
- `library.py`, `models.py`, and `domain/submarine/cases/index.json`
  - should own provenance metadata, applicability conditions, and placeholder disclosure.
- `submarine_design_brief_tool.py`, `submarine_runtime_context.py`, and `contracts.py`
  - should persist the calculation-plan draft and final researcher-confirmed decisions.

### Frontend ownership

- `submarine-stage-cards.tsx`
  - should show top-line "ready / needs confirmation / blocked" state for geometry and plan approval.
- `submarine-runtime-panel.tsx`
  - should be the detailed inspection surface for calculation-plan items, references, applicability, and researcher edits.
- `submarine-pipeline-status.ts`
  - should continue to describe post-compute scientific gate status only, not pre-compute plan approval.

### Recommended artifact layering

Prefer a layered pre-compute contract:

1. design brief
   - user objective, known inputs, open questions
2. geometry-check artifact
   - structured geometry findings and geometry reference suggestions
3. case-provenance artifact or payload
   - candidate case evidence, applicability, acceptance-profile summary
4. calculation-plan draft
   - merged geometry and case assumptions awaiting researcher approval
5. approved runtime snapshot
   - the exact values solver dispatch is allowed to consume

This keeps pre-compute approval separate from:

6. post-compute scientific evidence
7. final `scientific_gate_status`
8. final `allowed_claim_level`

</architecture_guidance>

<validation_architecture>
## Validation Architecture

### Automated backend validation

- `backend/tests/test_submarine_geometry_check_tool.py`
  - add coverage for geometry anomaly detection, reference-value suggestions, and clarification-required branches.
- `backend/tests/test_submarine_runtime_context.py`
  - verify that runtime gating respects the new calculation-plan confirmation logic instead of relying only on legacy `open_questions`.
- `backend/tests/test_submarine_design_brief_tool.py`
  - verify that the calculation-plan draft and researcher edits persist in design-brief artifacts and runtime state.
- `backend/tests/test_submarine_domain_assets.py`
  - verify case provenance fields, placeholder disclosure, and benchmark-backed acceptance-profile expectations.
- `backend/tests/test_submarine_solver_dispatch_tool.py`
  - verify solver dispatch blocks or downgrades when geometry/case approval is missing or severe ambiguity remains.
- `backend/tests/test_submarine_result_report_tool.py`
  - verify pre-compute approval metadata stays separate from post-compute claim-level synthesis.

### Automated frontend validation

- `frontend/src/components/workspace/submarine-confirmation-actions.test.ts`
  - cover approve / revise / return-for-revision actions around the calculation-plan draft.
- `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - cover geometry-trust and case-provenance summaries.
- `frontend/src/components/workspace/submarine-pipeline-status.test.ts`
  - ensure claim-level language remains post-compute only.
- `frontend/src/components/workspace/submarine-pipeline-shell.test.ts`
  - verify the active cockpit path shows pending confirmation or blocked state clearly.

### Manual validation

Use the real submarine cockpit with a representative STL such as `C:/Users/D0n9/Desktop/suboff_solid.stl` and confirm:

1. a clean benchmark-like geometry yields a calculation-plan draft with references and suggested values;
2. a severe scale or ambiguity issue interrupts early before solver execution;
3. a weaker library case stays visible but is clearly marked as missing strong evidence;
4. researcher edit plus approval survives refresh and becomes the exact solver input;
5. post-compute claim level remains unchanged until scientific evidence is actually generated.

</validation_architecture>

<risks>
## Key Risks

- `models.py` and `contracts.py` are already crowded shared files. Careless edits could create parallel-plan merge pressure or ambiguous ownership.
- Some cases may not have clean public benchmark references available. The implementation must support "visible but weakly evidenced" suggestions rather than forcing false certainty.
- STL-only geometry inspection will still have hard limits. Phase 4 can harden trust and disclosure, but it cannot eliminate the need for human judgment on ambiguous source meshes.
- Existing tests currently assert the old continuation behavior (`next_recommended_stage == "solver-dispatch"` after geometry preflight). Those tests must be updated deliberately rather than treated as accidental failures.
- Historical encoding noise exists in a few submarine-domain strings. Planning should prefer targeted logic and schema edits over broad cosmetic rewrites.

</risks>

<canonical_refs>
## Canonical References

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/phases/04-geometry-and-case-intelligence-hardening/04-CONTEXT.md`
- `.planning/phases/04-geometry-and-case-intelligence-hardening/04-UAT.md`
- `.planning/phases/04-geometry-and-case-intelligence-hardening/04-VERIFICATION.md`
- `.planning/phases/03-scientific-verification-gates/03-CONTEXT.md`
- `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
- `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_case.py`
- `backend/packages/harness/deerflow/domain/submarine/library.py`
- `backend/packages/harness/deerflow/domain/submarine/models.py`
- `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
- `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py`
- `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py`
- `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
- `backend/tests/test_submarine_design_brief_tool.py`
- `backend/tests/test_submarine_domain_assets.py`
- `backend/tests/test_submarine_geometry_check_tool.py`
- `backend/tests/test_submarine_runtime_context.py`
- `backend/tests/test_submarine_solver_dispatch_tool.py`
- `backend/tests/test_submarine_result_report_tool.py`
- `frontend/src/components/workspace/submarine-confirmation-actions.ts`
- `frontend/src/components/workspace/submarine-stage-cards.tsx`
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`
- `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- `frontend/src/components/workspace/submarine-pipeline-status.ts`
- `domain/submarine/cases/index.json`

</canonical_refs>

<deferred>
## Deferred Ideas

- Native STEP or Parasolid intake remains outside the current milestone.
- Automatic geometry repair, watertight-mesh healing, and CAD cleanup pipelines remain later work.
- Fully automated literature harvesting for all submarine families remains future work after the provenance contract is stable.
- Near-free-surface and broader multiphase case hardening remain future-domain expansion work.

</deferred>

---

*Phase: 04-geometry-and-case-intelligence-hardening*
*Research refreshed: 2026-04-02*
