# Supervisor Scientific State Machine Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit supervisor scientific gate so submarine CFD runs can continue generating artifacts while stage promotion and allowed claim levels become evidence-driven and traceable.

**Architecture:** Keep the existing generic review contract but add a separate scientific gate derived from `research_evidence_summary`. Implement the gate in a focused `supervision.py` helper, extend runtime and execution-plan contracts with scientific-gate visibility, emit `supervisor-scientific-gate.json` from reporting, and expose the gate in the workbench.

**Tech Stack:** Python, Pydantic, DeerFlow submarine domain modules, pytest, TypeScript, Node test runner, existing submarine runtime-panel utilities

---

## File Structure

- Create: `backend/packages/harness/deerflow/domain/submarine/supervision.py`
  - scientific gate builder and remediation-stage mapping
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
  - add scientific gate contract types and extend runtime snapshot / review contract
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - build and emit `scientific_supervisor_gate`, derive review state from it, and write `supervisor-scientific-gate.json`
- Modify: `backend/tests/test_submarine_domain_assets.py`
  - cover supervisor scientific gate semantics
- Modify: `backend/tests/test_submarine_result_report_tool.py`
  - cover gate artifact emission, claim-limited behavior, blocked remediation, and runtime review mapping
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - parse scientific supervisor gate summaries
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - cover gate labels, claim-level labels, and remediation stage display
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - render a compact scientific gate section
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - record the new gate behavior and remaining gaps

## Chunk 1: Domain And Runtime Contracts

### Task 1: Add scientific supervisor gate models to contracts

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- Test: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Add contract coverage for:

- `SubmarineScientificSupervisorGate`
- allowed claim levels
- gate statuses

Target shape:

```python
gate = SubmarineScientificSupervisorGate(
    gate_status="claim_limited",
    allowed_claim_level="verified_but_not_validated",
    source_readiness_status="verified_but_not_validated",
    recommended_stage="supervisor-review",
    remediation_stage="solver-dispatch",
    advisory_notes=["External validation is still missing."],
)
assert gate.gate_status == "claim_limited"
assert gate.allowed_claim_level == "verified_but_not_validated"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k scientific_supervisor_gate_model`
Expected: FAIL because the scientific gate contract does not exist yet.

- [ ] **Step 3: Write minimal implementation**

In `contracts.py`, add:

```python
SubmarineScientificGateStatus = Literal["ready_for_claim", "claim_limited", "blocked"]
SubmarineScientificClaimLevel = Literal[
    "delivery_only",
    "verified_but_not_validated",
    "validated_with_gaps",
    "research_ready",
]

class SubmarineScientificSupervisorGate(BaseModel):
    gate_status: SubmarineScientificGateStatus
    allowed_claim_level: SubmarineScientificClaimLevel
    source_readiness_status: str
    recommended_stage: str
    remediation_stage: str | None = None
    blocking_reasons: list[str] = Field(default_factory=list)
    advisory_notes: list[str] = Field(default_factory=list)
    artifact_virtual_paths: list[str] = Field(default_factory=list)
```

Also extend:

- `SupervisorReviewContract`
- `SubmarineRuntimeSnapshot`

with optional scientific-gate fields:

- `scientific_gate_status`
- `allowed_claim_level`
- `scientific_gate_virtual_path`

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k scientific_supervisor_gate_model`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/contracts.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add submarine scientific supervisor gate contracts"
```

### Task 2: Extend the execution plan with `supervisor-review`

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- Modify: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Add focused execution-plan coverage that expects:

- `supervisor-review` exists as a structured execution-plan item
- after confirmation it is initially `pending`

Suggested shape:

```python
plan = build_execution_plan(confirmation_status="confirmed")
assert plan[-1]["role_id"] == "supervisor-review"
assert plan[-1]["status"] == "pending"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k supervisor_review_execution_plan`
Expected: FAIL because the execution plan currently stops at `result-reporting`.

- [ ] **Step 3: Write minimal implementation**

In `contracts.py`:

- add `supervisor-review` to `_EXECUTION_PLAN_TEMPLATE`
- update default statuses for both `draft` and `confirmed` plans

Do not add a new runtime stage enum yet unless a test requires it.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k supervisor_review_execution_plan`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/contracts.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add supervisor review to submarine execution plan"
```

## Chunk 2: Scientific Gate Semantics

### Task 3: Add supervisor scientific gate builder

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/supervision.py`
- Modify: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Add helper-semantic coverage for:

1. `research_ready` -> `ready_for_claim`
2. `verified_but_not_validated` -> `claim_limited`
3. `validated_with_gaps` -> `claim_limited`
4. `blocked` -> `blocked`

Suggested shape:

```python
gate = build_scientific_supervisor_gate(
    research_evidence_summary={"readiness_status": "verified_but_not_validated", ...}
)
assert gate["gate_status"] == "claim_limited"
assert gate["allowed_claim_level"] == "verified_but_not_validated"
assert gate["recommended_stage"] == "supervisor-review"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k scientific_supervisor_gate_semantics`
Expected: FAIL because the supervision helper module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `supervision.py` with:

```python
def build_scientific_supervisor_gate(*, research_evidence_summary, artifact_virtual_paths=None) -> dict: ...
```

Keep v1 semantics compact:

- `research_ready` -> `ready_for_claim`
- `verified_but_not_validated` -> `claim_limited`
- `validated_with_gaps` -> `claim_limited`
- `blocked` / `insufficient_evidence` -> `blocked`

Recommended remediation mapping:

- blocked verification / validation -> `solver-dispatch`
- gaps-driven limitation -> `result-reporting` or `solver-dispatch` only as advisory

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k "scientific_supervisor_gate_model or scientific_supervisor_gate_semantics or supervisor_review_execution_plan"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/supervision.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add submarine scientific supervisor gate builder"
```

## Chunk 3: Reporting Integration

### Task 4: Emit scientific supervisor gate from final reporting

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing test**

Add reporting coverage for a claim-limited case:

- `scientific_supervisor_gate.gate_status == "claim_limited"`
- `allowed_claim_level == "verified_but_not_validated"`
- `review_status == "ready_for_supervisor"`
- `next_recommended_stage == "supervisor-review"`

Suggested assertions:

```python
gate = final_payload["scientific_supervisor_gate"]
assert gate["gate_status"] == "claim_limited"
assert gate["allowed_claim_level"] == "verified_but_not_validated"
assert final_payload["review_status"] == "ready_for_supervisor"
assert final_payload["next_recommended_stage"] == "supervisor-review"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k claim_limited_gate`
Expected: FAIL because final reporting does not emit the gate yet.

- [ ] **Step 3: Write minimal implementation**

In `reporting.py`:

- build `scientific_supervisor_gate` from `research_evidence_summary`
- add it to `final-report.json`
- derive generic review fields from it:
  - blocked -> `review_status = "blocked"`
  - otherwise -> `review_status = "ready_for_supervisor"`
  - blocked -> remediation stage
  - otherwise -> `supervisor-review`

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k claim_limited_gate`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/reporting.py backend/tests/test_submarine_result_report_tool.py
git commit -m "feat: add scientific supervisor gate to reports"
```

### Task 5: Emit gate artifact and blocked remediation behavior

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing test**

Extend reporting coverage for:

1. `research_ready` -> `ready_for_claim`
2. blocked research evidence -> `gate_status == "blocked"`
3. `supervisor-scientific-gate.json` exists and is linked

Suggested assertions:

```python
assert gate["gate_status"] == "ready_for_claim"
assert gate["allowed_claim_level"] == "research_ready"

blocked_gate = blocked_payload["scientific_supervisor_gate"]
assert blocked_gate["gate_status"] == "blocked"
assert blocked_gate["recommended_stage"] in {"solver-dispatch", "result-reporting"}
assert any(path.endswith("/supervisor-scientific-gate.json") for path in final_payload["artifact_virtual_paths"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k "ready_for_claim_gate or blocked_scientific_gate or scientific_gate_artifact"`
Expected: FAIL because the artifact emission and blocked mapping are incomplete.

- [ ] **Step 3: Write minimal implementation**

In `reporting.py`:

- add `supervisor-scientific-gate.json` to report artifacts
- write the JSON artifact
- include the gate artifact path in:
  - `scientific_supervisor_gate`
  - `artifact_virtual_paths`
- render a compact Markdown / HTML section for the gate

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k "claim_limited_gate or ready_for_claim_gate or blocked_scientific_gate or scientific_gate_artifact"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/reporting.py backend/tests/test_submarine_result_report_tool.py
git commit -m "feat: emit submarine scientific gate artifacts"
```

## Chunk 4: Workbench Visibility

### Task 6: Parse the scientific supervisor gate in workbench utilities

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`

- [ ] **Step 1: Write the failing test**

Add utility coverage for:

- gate status label
- allowed claim level label
- recommended stage
- remediation stage
- blocking reasons
- advisory notes

Suggested shape:

```ts
const summary = buildSubmarineScientificGateSummary({
  scientific_supervisor_gate: {
    gate_status: "claim_limited",
    allowed_claim_level: "verified_but_not_validated",
    recommended_stage: "supervisor-review",
    remediation_stage: "solver-dispatch",
    advisory_notes: ["External validation is still missing."],
  },
});
assert.equal(summary?.gateStatusLabel, "Claim Limited");
assert.equal(summary?.allowedClaimLevelLabel, "Verified But Not Validated");
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL because the workbench utilities do not yet parse the scientific gate.

- [ ] **Step 3: Write minimal implementation**

Add:

- a `SubmarineScientificGateSummary` UI type
- label maps for gate status and claim level
- `buildSubmarineScientificGateSummary(...)`
- artifact copy metadata for `supervisor-scientific-gate.json`

- [ ] **Step 4: Run test to verify it passes**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.utils.ts frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
git commit -m "feat: parse submarine scientific supervisor gates"
```

### Task 7: Render a compact scientific gate section in the runtime panel

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`

- [ ] **Step 1: Write the failing test**

Use the utility test as the main red-green gate, then treat TypeScript / lint as the UI wiring verification for this slice.

- [ ] **Step 2: Run verification to confirm the current UI is incomplete**

Run: `corepack pnpm exec tsc --noEmit`
Expected: the new scientific-gate payload field is not yet wired.

- [ ] **Step 3: Write minimal implementation**

In `submarine-runtime-panel.tsx`:

- extend `FinalReportPayload` with `scientific_supervisor_gate`
- compute a memoized gate summary
- render:
  - gate status
  - allowed claim level
  - recommended stage
  - remediation stage
  - blocking reasons
  - advisory notes
  - gate artifact path

Keep the section compact and colocated with the health / evidence area.

- [ ] **Step 4: Run verification to verify it passes**

Run: `corepack pnpm exec tsc --noEmit`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.tsx
git commit -m "feat: surface submarine scientific gates in workbench"
```

## Chunk 5: Docs And Regression Verification

### Task 8: Update status docs and run focused verification

**Files:**
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Update docs**

Document:

- the new scientific gate contract
- the new `supervisor-scientific-gate.json` artifact
- the difference between claim-limited and blocked behavior
- how runtime review fields are now derived from scientific gate semantics

- [ ] **Step 2: Run focused backend verification**

Run: `uv run pytest tests/test_submarine_domain_assets.py tests/test_submarine_result_report_tool.py -q`
Expected: PASS

- [ ] **Step 3: Run focused frontend verification**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 4: Run TypeScript verification**

Run: `corepack pnpm exec tsc --noEmit`
Expected: PASS

- [ ] **Step 5: Run focused lint verification**

Run: `corepack pnpm exec eslint src/components/workspace/submarine-runtime-panel.tsx src/components/workspace/submarine-runtime-panel.utils.ts src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md
git commit -m "docs: record supervisor scientific gate status"
```
