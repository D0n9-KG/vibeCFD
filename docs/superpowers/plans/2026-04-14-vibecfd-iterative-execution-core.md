# VibeCFD Iterative Execution Core Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then choose the execution skill that fits the work: use superpowers:subagent-driven-development when delegation benefits outweigh the round-trip, or superpowers:executing-plans when the work is better kept local. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the plan controls below, especially reuse, continuity, artifact lifecycle, validation/review cadence, and any research-overlay constraints.

**Goal:** Turn the current submarine workflow into a true `vibeCFD` iterative execution core that can negotiate, revise, branch, and complete complex CFD tasks with durable lineage and explicit output-delivery contracts.

**Architecture:** Keep the current DeerFlow submarine architecture, but strengthen the contract and orchestration spine instead of adding a second workflow system. Evolve the existing design brief, runtime state, output contract, experiment manifests, and follow-up flow into a stable iterative-task model, then surface the minimum necessary UI for users to understand and steer it.

**Tech Stack:** FastAPI gateway, DeerFlow/LangGraph runtime, Python domain contracts, built-in submarine tools and subagents, Next.js 16 frontend, TypeScript workbench contracts, OpenFOAM execution and post-processing

**Prior Art Survey:** `docs/superpowers/prior-art/2026-04-14-vibecfd-iterative-execution-core-survey.md`

**Reuse Strategy:** adapt existing project

**Session Status File:** `docs/superpowers/session-status/2026-04-14-vibecfd-iterative-execution-core-status.md`

**Context Summary:** `docs/superpowers/context-summaries/2026-04-14-vibecfd-iterative-execution-core-summary.md`

**Primary Context Files:** `docs/superpowers/specs/2026-04-14-vibecfd-iterative-execution-core-design.md`; `docs/superpowers/prior-art/2026-04-14-vibecfd-iterative-execution-core-survey.md`; `docs/superpowers/plans/2026-04-14-vibecfd-iterative-execution-core.md`; `docs/superpowers/session-status/2026-04-14-vibecfd-iterative-execution-core-status.md`; `docs/superpowers/context-summaries/2026-04-14-vibecfd-iterative-execution-core-summary.md`; `backend/packages/harness/deerflow/domain/submarine/contracts.py`; `backend/packages/harness/deerflow/domain/submarine/models.py`; `backend/packages/harness/deerflow/domain/submarine/experiments.py`; `backend/packages/harness/deerflow/domain/submarine/design_brief.py`; `backend/packages/harness/deerflow/domain/submarine/output_contract.py`; `backend/packages/harness/deerflow/domain/submarine/runtime_plan.py`; `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`; `backend/packages/harness/deerflow/domain/submarine/followup.py`; `backend/packages/harness/deerflow/domain/submarine/remediation.py`; `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`; `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`; `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`; `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`; `backend/packages/harness/deerflow/agents/thread_state.py`; `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`; `backend/packages/harness/deerflow/skills/relationships.py`; `backend/tests/test_skill_relationships.py`; `backend/tests/test_submarine_skills_presence.py`; `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`; `frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts`; `frontend/src/components/workspace/submarine-workbench/submarine-detail-model.ts`; `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.model.ts`; `frontend/src/components/workspace/submarine-workbench/index.tsx`; `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx`

**Artifact Lifecycle:** Keep the prior-art survey, design spec, plan, session status file, and context summary as the active continuity chain for this long-running architecture slice. Keep durable contract tests, domain models, and runtime state changes that strengthen iterative execution. Keep new skills only if they become actual runtime accelerators; delete throwaway experiments, scratch prompts, and one-off prototype helpers that are superseded by stable domain contracts. Replace any legacy “message-history-only” orchestration assumptions with explicit contract/state fields rather than retaining both as co-equal primary paths.

**Workspace Strategy:** current workspace

**Validation Strategy:** mixed

**Review Cadence:** each milestone

**Checkpoint Strategy:** milestone commits

**Research Overlay:** disabled

**Research Mainline:** none

**Non-Negotiables:** none

**Forbidden Regressions:** turning the product into a generic workflow engine; solving iteration problems only with prompt text instead of durable contract/state changes; hiding unsupported outputs behind vague generic prose; losing lineage between baseline, variants, and follow-up runs

**Method Fidelity Checks:** the authoritative task state must come from structured runtime contracts, not only chat history; each requested output must have an explicit support and delivery state; the `output_delivery_plan` must become authoritative from the design-brief stage onward instead of appearing only at reporting time; variant and follow-up execution must preserve parentage; visible frontend state must reflect the same contract and runtime truth as the backend artifacts

**Scale Gate:** none

**Decision Log:** none - record durable decisions in session status and plan updates

**Research Findings:** none

**Uncertainty Hotspots:** how far current `requested_outputs` and `custom_variants` plumbing already reaches in runtime execution; whether variant/follow-up lineage can be extended inside existing manifests without broad schema churn; whether the lead-agent prompting needs a light touch or a larger contract-first rewrite; how much minimal frontend exposure is needed before the system becomes steerable enough for real iterative work

**Replan Triggers:** the existing contract/state model cannot carry iteration lineage without breaking current flows; output-delivery support states cannot be made authoritative without a broader schema migration; follow-up orchestration needs a new execution backbone instead of the current DeerFlow chain; user-visible runtime steering requires a much larger frontend redesign than expected

---

### Task 1: Add Contract-Level Tests For Iterative Task State

**Files:**
- Modify: `backend/tests/test_submarine_design_brief_tool.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`
- Modify: `backend/tests/test_submarine_scientific_followup_tool.py`
- Test: `backend/tests/test_submarine_design_brief_tool.py`
- Test: `backend/tests/test_submarine_result_report_tool.py`
- Test: `backend/tests/test_submarine_scientific_followup_tool.py`

- [x] **Step 1: Add a failing design-brief test for explicit requested-output support states and an initial delivery plan**

```python
def test_submarine_design_brief_marks_requested_outputs_with_support_states(...):
    payload = ...
    assert payload["requested_outputs"][0]["support_level"] == "supported"
    assert payload["requested_outputs"][1]["support_level"] == "not_yet_supported"
    assert any(
        item["output_id"] == "wake_velocity_slice"
        and item["delivery_status"] in {"planned", "not_yet_supported"}
        for item in payload["output_delivery_plan"]
    )
```

- [x] **Step 2: Run it to verify the starting gap**

Run: `uv run --project backend pytest backend/tests/test_submarine_design_brief_tool.py -k requested_outputs_support_states -v`
Expected: FAIL if the current payload or rendering does not preserve the intended iterative-delivery contract strongly enough from the design-brief stage onward

- [x] **Step 3: Add a failing result-report test for output-delivery states surviving into reporting**

```python
def test_submarine_result_report_preserves_output_delivery_plan(...):
    report_payload = ...
    assert any(item["output_id"] == "wake_velocity_slice" for item in report_payload["output_delivery_plan"])
```

- [x] **Step 4: Run it to verify RED**

Run: `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py -k output_delivery_plan -v`
Expected: FAIL if reporting currently drops or weakens the delivery plan

- [x] **Step 5: Add a failing follow-up test for explicit lineage across remediation iterations**

```python
def test_submarine_scientific_followup_records_parent_lineage(...):
    history_payload = ...
    assert history_payload["entries"][0]["baseline_reference_run_id"] == "baseline"
```

- [x] **Step 6: Run it to verify RED**

Run: `uv run --project backend pytest backend/tests/test_submarine_scientific_followup_tool.py -k parent_lineage -v`
Expected: FAIL if follow-up history is not explicit enough for iteration lineage

### Task 2: Strengthen The Iterative Task Contract In Domain Models And Runtime Producers

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/models.py`
- Modify: `backend/packages/harness/deerflow/agents/thread_state.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
- Test: `backend/tests/test_submarine_design_brief_tool.py`

- [x] **Step 1: Extend the contract models with explicit iteration and negotiation fields that map to persisted snapshot data**

```python
class SubmarineIterationContext(BaseModel):
    contract_revision: int = 1
    iteration_mode: Literal["baseline", "revise_baseline", "derive_variant", "followup"] = "baseline"
    revision_summary: str | None = None
    evidence_expectations: list[dict[str, object]] = Field(default_factory=list)
    variant_policy: dict[str, object] = Field(default_factory=dict)
```

- [x] **Step 2: Add runtime-state slots for the new contract information**

```python
class SubmarineRuntimeState(TypedDict):
    ...
    contract_revision: NotRequired[int]
    iteration_mode: NotRequired[str]
    revision_summary: NotRequired[str | None]
    unresolved_decisions: NotRequired[list[dict] | None]
    capability_gaps: NotRequired[list[dict] | None]
    evidence_expectations: NotRequired[list[dict] | None]
    variant_policy: NotRequired[dict[str, object] | None]
```

- [x] **Step 3: Wire the new fields through actual runtime producers instead of only types**

```python
runtime_snapshot = build_runtime_snapshot(
    ...,
    contract_revision=payload.get("contract_revision", snapshot.contract_revision),
    iteration_mode=payload.get("iteration_mode", snapshot.iteration_mode),
    unresolved_decisions=payload.get("unresolved_decisions", snapshot.unresolved_decisions),
    capability_gaps=payload.get("capability_gaps", snapshot.capability_gaps),
    evidence_expectations=payload.get("evidence_expectations", snapshot.evidence_expectations),
    variant_policy=payload.get("variant_policy", snapshot.variant_policy),
)
```

- [x] **Step 4: Update merge behavior so iterative state survives later stage updates**

```python
if "unresolved_decisions" in prior or "unresolved_decisions" in item_dict:
    combined["unresolved_decisions"] = _merge_unique_dict_list(...)
if "capability_gaps" in prior or "capability_gaps" in item_dict:
    combined["capability_gaps"] = _merge_unique_dict_list(...)
if "evidence_expectations" in prior or "evidence_expectations" in item_dict:
    combined["evidence_expectations"] = _merge_unique_dict_list(...)
if "variant_policy" in prior or "variant_policy" in item_dict:
    combined["variant_policy"] = {
        **(prior.get("variant_policy") or {}),
        **(item_dict.get("variant_policy") or {}),
    }
if "contract_revision" in prior or "contract_revision" in item_dict:
    combined["contract_revision"] = max(
        int(prior.get("contract_revision") or 1),
        int(item_dict.get("contract_revision") or 1),
    )
if "output_delivery_plan" in prior or "output_delivery_plan" in item_dict:
    combined["output_delivery_plan"] = _merge_keyed_dict_list(
        ...,
        id_key="output_id",
        status_key="delivery_status",
        status_order=_OUTPUT_DELIVERY_STATUS_ORDER,
    )
```

- [x] **Step 5: Run the focused contract suite**

Run: `uv run --project backend pytest backend/tests/test_submarine_design_brief_tool.py -v`
Expected: PASS with the new iterative contract fields serialized and stable

### Task 3: Make Design Briefs Behave Like Revisable Research Task Contracts

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/design_brief.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/output_contract.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
- Modify: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- Test: `backend/tests/test_submarine_design_brief_tool.py`

- [ ] **Step 1: Preserve the existing requested-output normalization and close the real semantic gap: unresolved decisions, capability gaps, and the initial output-delivery plan must become durable contract state**

```python
requested_outputs = resolve_requested_outputs(expected_outputs)
capability_gaps = [
    item for item in requested_outputs
    if item["support_level"] != "supported"
]
output_delivery_plan = build_output_delivery_plan(
    requested_outputs,
    stage="task-intelligence",
)
```

- [ ] **Step 2: Generate unresolved decisions instead of leaving complex asks implicit**

```python
open_questions = [
    *open_questions,
    *[
        f"请确认输出“{item['requested_label']}”是否接受当前支持边界。"
        for item in capability_gaps
        if item.get("requested_label")
    ],
]
```

- [ ] **Step 3: Add contract revision and iteration context into the persisted design-brief payload**

```python
payload["contract_revision"] = previous_revision + 1
payload["iteration_mode"] = inferred_iteration_mode
payload["revision_summary"] = revision_summary
payload["capability_gaps"] = capability_gaps
payload["unresolved_decisions"] = unresolved_decisions
payload["evidence_expectations"] = [
    {
        "expectation_id": item["requirement_id"],
        "kind": item["check_type"],
        "label": item["label"],
    }
    for item in scientific_verification_requirements
]
payload["variant_policy"] = {
    "default_compare_target_run_id": "baseline",
    "allow_custom_variants": True,
    "custom_variant_count": len(existing_custom_variants or []),
}
payload["output_delivery_plan"] = output_delivery_plan
```

- [ ] **Step 4: Teach the lead-agent prompt to treat material task changes as contract revisions, not just extra chat context**

```text
When the user changes outputs, scope, benchmark target, variant strategy, or execution intent, update the structured submarine design brief before launching downstream tools.
```

- [ ] **Step 5: Run the design-brief suite**

Run: `uv run --project backend pytest backend/tests/test_submarine_design_brief_tool.py -v`
Expected: PASS with explicit capability and unresolved-decision behavior

### Task 4: Formalize Experiment Graph Lineage By Extending The Existing Experiment Schema

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/models.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/experiments.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/followup.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/remediation.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
- Test: `backend/tests/test_submarine_experiment_linkage_contracts.py`
- Test: `backend/tests/test_submarine_scientific_followup_tool.py`

- [ ] **Step 1: Reuse the existing lineage vocabulary and extend it with missing iteration metadata**

```python
class SubmarineExperimentRunRecord(BaseModel):
    ...
    contract_revision: int | None = None
    lineage_reason: str | None = None
    requested_output_ids: list[str] = Field(default_factory=list)
```

- [ ] **Step 2: Ensure custom variants and scientific-study variants are represented with the same lineage model**

```python
experiment_manifest["run_records"].append(
    _build_variant_run_record(
        ...,
        baseline_reference_run_id="baseline",
        compare_target_run_id="baseline",
        contract_revision=contract_revision,
        lineage_reason=revision_summary,
    )
)
```

- [ ] **Step 3: Persist follow-up lineage using the same canonical run identifiers instead of a second parent vocabulary**

```python
history_entry["source_run_id"] = source_run_id
history_entry["baseline_reference_run_id"] = baseline_reference_run_id
history_entry["compare_target_run_id"] = compare_target_run_id
history_entry["derived_run_ids"] = refreshed_run_ids
```

- [ ] **Step 4: Run the linkage suite**

Run: `uv run --project backend pytest backend/tests/test_submarine_experiment_linkage_contracts.py backend/tests/test_submarine_scientific_followup_tool.py -v`
Expected: PASS with explicit lineage and no regression in current manifest behavior

### Task 5: Align Existing Submarine Skills With The Iterative-Core Vocabulary

**Files:**
- Modify: `skills/public/submarine-orchestrator/SKILL.md`
- Modify: `skills/public/submarine-report/SKILL.md`
- Modify: `skills/public/submarine-solver-dispatch/SKILL.md`
- Modify: `backend/packages/harness/deerflow/skills/relationships.py`
- Modify: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- Test: `backend/tests/test_skill_relationships.py`
- Test: `backend/tests/test_submarine_skills_presence.py`

- [x] **Step 1: Update the existing submarine public skills so they speak the new contract and lineage vocabulary**

```md
Explain contract revision, requested-output support states, baseline/variant lineage, and follow-up continuity using the existing submarine skill set.
```

- [x] **Step 2: Align skill-relationship analysis with the stronger iterative vocabulary without assuming new runtime routing**

```python
assert "submarine-orchestrator" in names
assert "submarine-report" in names
```

- [x] **Step 3: Tighten lead-agent prompt references to the existing stage/skill set instead of inventing unroutable planner roles**

```text
Use the existing submarine stage roles and their attached skills when revising contracts, planning variants, and packaging outputs.
```

- [x] **Step 4: Run the relevant skill suites**

Run: `uv run --project backend pytest backend/tests/test_skill_relationships.py backend/tests/test_submarine_skills_presence.py -v`
Expected: PASS with the existing skill set still discoverable and semantically aligned

### Task 6: Surface The Iterative Contract And Output Plan In The Frontend

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts`
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-detail-model.ts`
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.model.ts`
- Modify: `frontend/src/components/workspace/submarine-workbench/index.tsx`
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx`
- Test: `frontend/src/components/workspace/submarine-workbench/index.contract.test.ts`
- Test: `frontend/src/components/workspace/submarine-workbench/submarine-visible-actions.test.ts`
- Test: `frontend/src/app/workspace/submarine/[thread_id]/page.test.ts`

- [x] **Step 1: Extend frontend contracts to include contract revision, iteration mode, capability gaps, unresolved decisions, and output delivery plan**

```ts
export type SubmarineRuntimeSnapshotPayload = {
  ...
  contract_revision?: number | null
  iteration_mode?: string | null
  revision_summary?: string | null
  capability_gaps?: Array<Record<string, unknown>> | null
  unresolved_decisions?: Array<Record<string, unknown>> | null
  evidence_expectations?: Array<Record<string, unknown>> | null
  variant_policy?: Record<string, unknown> | null
  output_delivery_plan?: Array<Record<string, unknown>> | null
}
```

- [x] **Step 2: Render the task-contract and output-delivery truth in the workbench**

```tsx
<section>
  <h3>任务合同</h3>
  <p>合同修订：{runtime.contract_revision ?? designBrief?.contract_revision ?? "1"}</p>
  <p>迭代模式：{runtime.iteration_mode ?? "baseline"}</p>
</section>
```

- [x] **Step 3: Update the actual frontend model builders so the new runtime fields are consumed, summarized, and surfaced**

```ts
const contractRevision = runtime?.contract_revision ?? designBrief?.contract_revision ?? null
const capabilityGaps = runtime?.capability_gaps ?? designBrief?.capability_gaps ?? []
const outputDeliveryPlan = runtime?.output_delivery_plan ?? designBrief?.output_delivery_plan ?? []
```

- [x] **Step 4: Add a minimal experiment-lineage summary so users can tell whether they are on a baseline, variant, or follow-up path**

```tsx
<ExperimentLineageBadge
  mode={runtime.iteration_mode}
  baselineRunId={detail.experimentBoard.baselineRunId}
  variantRunIds={detail.experimentBoard.variantRunIds}
/>
```

- [x] **Step 5: Run the focused frontend suite**

Run: `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/components/workspace/submarine-workbench/index.contract.test.ts" "src/components/workspace/submarine-workbench/submarine-visible-actions.test.ts" "src/app/workspace/submarine/[thread_id]/page.test.ts"`
Expected: PASS with the new iterative contract visible and typed

### Task 7: Run Real Iterative Scenarios From The Frontend And Harden Gaps

**Type:** Exploratory

**Files:**
- Modify: `docs/superpowers/session-status/2026-04-14-vibecfd-iterative-execution-core-status.md`
- Modify: `docs/superpowers/context-summaries/2026-04-14-vibecfd-iterative-execution-core-summary.md`
- Modify: implementation files above if deep testing reveals missing contract propagation or unstable iteration behaviors

**Goal:** Validate that the system now behaves like a collaborative iterative CFD tool in real browser-visible scenarios, not just in isolated unit contracts.

**Collect Evidence:**
- a same-baseline revision scenario
- a baseline-to-variant branching scenario
- a follow-up remediation scenario
- an output-expansion scenario where the user adds new requested outputs after the first execution

**Stop and Replan If:**
- contract revisions remain mostly invisible in runtime state
- lineage breaks when deriving variants or follow-ups
- output-delivery negotiation is still only cosmetic and does not affect downstream execution

**Checkpoint If:**
- at least one full thread visibly proves each iteration mode

- [ ] **Step 1: Create or reuse a baseline submarine thread from the frontend using `C:\\Users\\D0n9\\Desktop\\suboff_solid.stl`**
- [ ] **Step 2: Revise the task after initial planning and confirm the task contract updates instead of silently appending chat context**
- [ ] **Step 3: Derive at least one explicit variant and confirm lineage is visible in runtime state and artifacts**
- [x] **Step 4: Trigger a follow-up cycle and confirm parentage and refreshed outputs remain traceable**
- [ ] **Step 5: Add new requested outputs after the first run and confirm support/pending/unsupported states remain explicit**
- [ ] **Step 6: Record verified thread ids, remaining gaps, and next-hardening actions in the session status file and context summary**

### Task 8: Final Verification And Milestone Review

**Files:**
- Modify: `docs/superpowers/session-status/2026-04-14-vibecfd-iterative-execution-core-status.md`
- Modify: `docs/superpowers/context-summaries/2026-04-14-vibecfd-iterative-execution-core-summary.md`

- [ ] **Step 1: Run the backend milestone suite**

Run: `uv run --project backend pytest backend/tests/test_submarine_design_brief_tool.py backend/tests/test_submarine_experiment_linkage_contracts.py backend/tests/test_submarine_result_report_tool.py backend/tests/test_submarine_scientific_followup_tool.py backend/tests/test_cli_auth_providers.py -v`
Expected: PASS

- [ ] **Step 2: Run the frontend milestone suite**

Run: `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/components/workspace/submarine-workbench/index.contract.test.ts" "src/components/workspace/submarine-workbench/submarine-visible-actions.test.ts" "src/app/workspace/submarine/[thread_id]/page.test.ts" "src/core/threads/use-thread-stream.state.test.ts"`
Expected: PASS

- [ ] **Step 3: Run frontend typecheck**

Run: `corepack pnpm --dir frontend typecheck`
Expected: PASS

- [ ] **Step 4: Request milestone review and update the status summary honestly**

```text
Record what iterative modes are genuinely proven, what still remains weak, and whether the product now qualifies as a stronger `vibeCFD` core.
```
