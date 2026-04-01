# Scientific Remediation Planner v1 Design

## 1. Goal

Turn the existing scientific gate from a passive status signal into a structured remediation plan that tells the system and the reviewer what evidence is missing, which stage should address it, and which actions can be executed automatically versus which still need human input.

This slice must keep the product open-ended:

- the user still asks for flexible CFD outcomes in natural language
- the system still decides which outputs and studies matter
- artifact production still continues

What changes is that blocked or claim-limited runs should no longer stop at "not ready." They should produce an explicit next-action plan.

## 2. Why This Is The Right Next Slice

The repository already has:

- scientific verification requirements
- study orchestration
- experiment registry and run compare
- unified research evidence summaries
- scientific supervisor gating
- compare workbench cards

The remaining gap is operational.

Today the system can say:

- this run is `blocked`
- this run is `verified_but_not_validated`
- this run is `validated_with_gaps`

But it still does not emit a usable remediation contract that answers:

- what exactly should happen next
- which stage owns that work
- whether the step is auto-executable or human-required
- which evidence gap each action is meant to close

Without that layer, the repository is evidence-aware but not yet self-steering.

## 3. Product Principle

This slice should add planning, not a rigid workflow shell.

That means:

1. the user does not need to enter a remediation wizard
2. if enough evidence already exists, the plan should stay quiet
3. if evidence is missing, the repository should emit structured next actions
4. the first version should plan actions before it tries to auto-execute them

## 4. Approaches Considered

### 4.1 Option A: Encode remediation hints only in `advisory_notes`

Pros:

- minimal changes

Cons:

- too vague for automation
- not traceable
- difficult to render cleanly in the workbench

### 4.2 Option B: Add a structured remediation-plan summary and artifact

Pros:

- clear machine-readable contract
- can power both workbench and future auto-execution
- keeps action semantics in the evidence layer

Cons:

- requires one more report object and artifact

### 4.3 Option C: Jump directly to automatic remediation execution

Pros:

- more autonomous end state

Cons:

- too risky before the remediation contract is explicit
- easy to make the system feel like a rigid workflow engine

### Recommendation

Choose Option B.

This gives the system a real remediation brain without prematurely forcing it into a full workflow executor.

## 5. Scope

### In Scope

- new structured `scientific_remediation_summary` in final reporting
- new `scientific-remediation-plan.json` artifact
- deterministic remediation actions derived from:
  - `scientific_supervisor_gate`
  - `research_evidence_summary`
  - `scientific_verification_assessment`
  - `scientific_study_summary`
- workbench rendering of remediation actions and ownership
- action classification into:
  - `auto_executable`
  - `manual_required`
  - `not_needed`

### Out Of Scope

- automatic execution of remediation actions
- new supervisor agent loops that re-run stages on their own
- external benchmark acquisition from remote sources
- multi-session remediation history

## 6. Proposed Contract

Add a new report block:

- `scientific_remediation_summary`

Suggested shape:

- `plan_status`
  - `not_needed`
  - `recommended`
  - `blocked`
- `target_claim_level`
- `current_claim_level`
- `recommended_stage`
- `artifact_virtual_paths`
- `actions`

Each action should include:

- `action_id`
- `title`
- `summary`
- `owner_stage`
- `priority`
- `execution_mode`
  - `auto_executable`
  - `manual_required`
- `status`
  - `pending`
  - `not_needed`
- `evidence_gap`
- `required_artifacts`

## 7. Remediation Semantics

### 7.1 Missing Scientific Study Evidence

If the scientific verification layer reports missing study evidence, emit actions such as:

- rerun with scientific studies enabled
- regenerate specific verification artifacts for missing study families

Owner stage:

- `solver-dispatch`

Execution mode:

- `auto_executable`

### 7.2 Missing Validation Reference

If readiness is `verified_but_not_validated` because no validation reference exists, emit an action such as:

- attach or configure a benchmark / validation reference for the selected case

Owner stage:

- `supervisor-review`

Execution mode:

- `manual_required`

### 7.3 Provenance Or Reporting Gaps

If readiness is limited by missing provenance or figure/report linkage, emit actions such as:

- regenerate result report with evidence artifacts linked
- regenerate figure delivery manifests if required

Owner stage:

- `result-reporting`

Execution mode:

- `auto_executable`

### 7.4 Research Ready

If the gate is `ready_for_claim`, emit:

- `plan_status = "not_needed"`
- zero pending actions

## 8. Workbench Design

The existing runtime panel should render a compact remediation block near the scientific gate and research evidence sections.

It should show:

- remediation plan status
- current vs target claim level
- recommended stage
- action cards with:
  - title
  - owner stage
  - execution mode
  - evidence gap
  - artifact requirements

This should stay compact and review-oriented, not a wizard.

## 9. Files

### Backend

- Create: `backend/packages/harness/deerflow/domain/submarine/remediation.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_domain_assets.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

### Frontend

- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`

### Docs

- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

## 10. Testing Strategy

### Backend

- add planner helper tests for:
  - missing study evidence
  - missing validation reference
  - research-ready no-op plan
- add result-report coverage for:
  - `scientific_remediation_summary`
  - `scientific-remediation-plan.json`

### Frontend

- add utility parsing tests for remediation summary
- run typecheck and focused eslint

## 11. Success Criteria

This stage is successful when:

- final reports include a structured remediation summary
- blocked or claim-limited runs explain what should happen next
- the workbench exposes actionable remediation cards
- the repository is more self-steering without becoming a forced workflow shell

## 12. Remaining Gap After This Stage

Even after this slice, the repository will still not:

- execute auto-remediation actions by itself
- maintain a multi-run remediation history
- resolve missing validation references automatically
- provide a full audit graph for every action transition
