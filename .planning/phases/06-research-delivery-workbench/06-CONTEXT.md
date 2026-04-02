# Phase 6: Research Delivery Workbench - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete the researcher-facing delivery loop inside the existing submarine workbench by producing Chinese final reports, surfacing lightweight delivery/review status, and keeping follow-up decisions traceable without turning the cockpit into a separate approval workflow product.

Phase 6 should make the system honest and reviewable about what the current run can claim, what evidence supports that claim, what is still missing, and what the next study step should be. It should not attempt to manage how researchers use the result after delivery, and it should not absorb a full frontend redesign.

</domain>

<decisions>
## Implementation Decisions

### Report package shape
- **D-01:** The final report should use a hybrid Chinese delivery format rather than a pure executive summary or a pure evidence dump.
- **D-02:** The report homepage should be conclusion-first and use a two-layer summary: first the current conclusion, allowed claim level, supervisor/review status, reproducibility status, and recommended next step; then the key metrics and representative figures.
- **D-03:** The main body should be organized by conclusion, not by raw subsystem or artifact type.

### Evidence traceability
- **D-04:** Each major conclusion should carry short inline source references, confidence/claim wording, and any missing-evidence note directly in the conclusion block.
- **D-05:** The report should end with a complete evidence/artifact index so readers can trace every conclusion back to detailed artifacts without forcing the main narrative to become an appendix-first document.
- **D-06:** Provenance remains the canonical rerun/audit entrypoint, and report traceability should link back to that entrypoint rather than creating a second competing lineage model.

### Delivery and review interaction model
- **D-07:** Phase 6 should not build a heavyweight approve/block/rerun/extend control panel or a standalone approval workflow.
- **D-08:** The system should first output a structured conclusion package with sources, claim level, confidence, and evidence gaps; the main agent should then continue in chat to ask the user whether the task is complete, whether more evidence is needed, whether setup/parameter issues must be corrected, or whether the study should be extended.
- **D-09:** The workbench should stay lightweight in this phase: show report status, artifact links, scientific gate context, and follow-up references, but leave the actual decision conversation to the main agent.

### Follow-up and rerun loop
- **D-10:** Follow-up should be chat-driven but recorded as structured history rather than staying as unstructured conversation only.
- **D-11:** Each structured follow-up record should capture why work is continuing, whether the next action is evidence supplementation, setup/parameter correction, study extension, or task completion, and which conclusions/evidence gaps triggered that choice.
- **D-12:** Follow-up records must preserve lineage between the prior report and any new run/report artifacts so the research trail stays auditable across reruns.
- **D-13:** The follow-up loop should stay bounded and user-confirmed; the system may recommend next actions, but it should not autonomously recurse through repeated rerun cycles.

### the agent's Discretion
- Exact report section titles, visual grouping, and microcopy as long as the conclusion-first hybrid structure remains intact.
- Exact artifact-link formatting and evidence-index presentation as long as each conclusion remains traceable.
- Exact follow-up field names and storage details as long as the decision reason and rerun lineage remain explicit.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and phase anchors
- `.planning/PROJECT.md` - product promise, architectural constraints, and the remaining Phase 6 delivery bottleneck.
- `.planning/REQUIREMENTS.md` - `RPT-01` and `RPT-02` define the required Chinese report delivery and review/follow-up behavior.
- `.planning/ROADMAP.md` - Phase 6 goal, success criteria, and the intended split across report packaging, supervisor review, and guided reruns.
- `.planning/STATE.md` - current project handoff into Phase 6.

### Prior phase decisions that still constrain Phase 6
- `.planning/phases/03-scientific-verification-gates/03-CONTEXT.md` - evidence quality and claim gating remain upstream truth for any delivery wording.
- `.planning/phases/04-geometry-and-case-intelligence-hardening/04-CONTEXT.md` - pre-compute approval must remain distinct from post-compute claim language.
- `.planning/phases/05-experiment-ops-and-reproducibility/05-CONTEXT.md` - provenance manifest and cockpit-first delivery constraints carry directly into the final report and follow-up design.

### Report and evidence delivery design
- `docs/archive/superpowers/specs/2026-03-28-unified-research-evidence-chain-design.md` - defines the evidence-chain direction that final reporting should preserve.
- `docs/archive/superpowers/specs/2026-03-29-frontend-final-report-schema-unification-v1-design.md` - explains the shared frontend report contract boundary and why report-field drift is a key risk.
- `docs/archive/superpowers/specs/2026-03-28-publication-grade-figure-delivery-design.md` - defines figure-delivery expectations, manifest-driven reporting, and why figures must be treated as research artifacts rather than previews.

### Supervisor and follow-up design
- `docs/archive/superpowers/specs/2026-03-28-supervisor-scientific-state-machine-design.md` - current scientific gate semantics, recommended stage mapping, and the distinction between generic review state and scientific claim gating.
- `docs/archive/superpowers/specs/2026-03-29-scientific-followup-report-refresh-v1-design.md` - bounded rerun-plus-report-refresh behavior for follow-up orchestration.

### Current implementation contracts
- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - runtime snapshot, supervisor review contract, scientific gate types, and stage template.
- `backend/packages/harness/deerflow/domain/submarine/reporting.py` - current final report assembly, scientific gate emission, remediation handoff, and report artifact writing.
- `backend/packages/harness/deerflow/domain/submarine/followup.py` - scientific follow-up history and summary contract.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts` - shared parsed payload contracts consumed by the workbench.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx` - current cockpit rendering surface for reports, scientific gate state, and follow-up summaries.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/packages/harness/deerflow/domain/submarine/reporting.py`: already builds `final-report.json`, `final-report.md`, `final-report.html`, the scientific gate artifact, remediation handoff, and summary payloads for the current report stage.
- `backend/packages/harness/deerflow/domain/submarine/followup.py`: already supports a structured scientific follow-up history artifact and a latest-follow-up summary model.
- `backend/packages/harness/deerflow/domain/submarine/contracts.py`: already defines `review_status`, `allowed_claim_level`, and `scientific_supervisor_gate`, so Phase 6 can refine the user-facing interaction model without inventing a new runtime truth contract.
- `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`: already centralizes parsed final-report and runtime payload contracts for the cockpit.
- `frontend/src/components/workspace/submarine-runtime-panel.tsx`: already renders scientific gate, remediation, and follow-up summaries inside the existing workbench, which makes a lightweight Phase 6 extension viable.

### Established Patterns
- Report delivery uses structured artifacts plus Markdown/HTML renderings rather than frontend-only composition.
- Artifact identity stays virtual-path based, and traceability should continue to point through artifact paths and provenance manifests instead of host-local paths.
- The cockpit is the existing home for delivery visibility, but major operator decisions can still remain chat-driven rather than hardcoded into button-heavy workflow shells.
- Follow-up and remediation are already modeled as artifact-backed summaries, so Phase 6 should extend those structures rather than replacing them with free-text-only history.

### Integration Points
- `reporting.py` is the natural place to enforce the conclusion-first Chinese report shape, inline source/confidence summaries, and the end-of-report evidence index.
- `submarine-runtime-panel.tsx` is the natural place to keep lightweight review/delivery visibility and follow-up lineage links without adding a separate approval app.
- `followup.py` and the scientific follow-up tool chain are the natural place to persist chat-driven next-step decisions and rerun/report lineage across iterations.

</code_context>

<specifics>
## Specific Ideas

- The user does not want Phase 6 to manage downstream business use of results; the system should instead state what can currently be claimed, with sources and confidence, and stop there.
- After the system outputs the conclusion package, the main agent should continue in chat to ask whether the task can end, whether more evidence/cases are needed, whether parameter/setup errors must be corrected, or whether the study should be extended.
- The report should feel like a researcher-facing deliverable, not a workflow wizard: readable first, but still traceable down to artifacts and provenance.

</specifics>

<deferred>
## Deferred Ideas

- A standalone approval dashboard or button-heavy supervisor workflow is out of scope for Phase 6.
- A full frontend redesign remains separate future work and should not be bundled into this delivery phase.
- Autonomous multi-step rerun loops remain out of scope; Phase 6 keeps user-confirmed bounded follow-up only.

</deferred>

---

*Phase: 06-research-delivery-workbench*
*Context gathered: 2026-04-02*
