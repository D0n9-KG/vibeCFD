# Unified Research Evidence Chain Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a unified research evidence summary for submarine CFD runs so the repository can distinguish operational delivery, numerical verification, external validation, and provenance-backed research readiness.

**Architecture:** Keep the existing evidence blocks (`acceptance_assessment`, `scientific_verification_assessment`, `scientific_study_summary`, `experiment_summary`, `output_delivery_plan`) as source evidence and add one aggregate layer on top. Implement the aggregation in a focused `evidence.py` helper module, emit `research-evidence-summary.json` from reporting, and expose a compact workbench summary without adding any workflow wizard.

**Tech Stack:** Python, Pydantic, DeerFlow submarine domain modules, pytest, TypeScript, Node test runner, existing submarine runtime-panel utilities

---

## File Structure

- Create: `backend/packages/harness/deerflow/domain/submarine/evidence.py`
  - Normalize verification, validation, provenance, and aggregate readiness.
- Modify: `backend/packages/harness/deerflow/domain/submarine/models.py`
  - Add research-evidence summary models and status literals.
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - Build `research_evidence_summary`, emit `research-evidence-summary.json`, and render a compact report section.
- Modify: `backend/tests/test_submarine_domain_assets.py`
  - Cover evidence aggregation semantics and model shapes.
- Modify: `backend/tests/test_submarine_result_report_tool.py`
  - Cover report integration, readiness semantics, and evidence artifact emission.
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - Parse `research_evidence_summary` into a stable UI-facing structure.
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - Cover readiness/dimension labels and evidence gap parsing.
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - Render a compact research-evidence section in the health panel.
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - Record the new unified evidence-chain boundary and remaining gaps.

## Chunk 1: Domain Evidence Semantics

### Task 1: Add typed research-evidence models

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/models.py`
- Test: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Add focused model-shape coverage for:

- verification dimension status
- validation dimension status
- provenance dimension status
- aggregate research readiness summary

Target shape:

```python
summary = SubmarineResearchEvidenceSummary(
    readiness_status="verified_but_not_validated",
    verification_status="passed",
    validation_status="missing_validation_reference",
    provenance_status="traceable",
    confidence="medium",
    blocking_issues=[],
    evidence_gaps=["No applicable benchmark target was available for this run."],
    passed_evidence=["Scientific verification requirements passed."],
    benchmark_highlights=[],
    provenance_highlights=["Experiment manifest and compare summary are available."],
    artifact_virtual_paths=["/mnt/user-data/outputs/submarine/reports/demo/research-evidence-summary.json"],
)
assert summary.readiness_status == "verified_but_not_validated"
assert summary.validation_status == "missing_validation_reference"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k research_evidence_model`
Expected: FAIL because the research-evidence models do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add typed status literals and a new model in `models.py`, for example:

```python
SubmarineResearchReadinessStatus = Literal[
    "blocked",
    "insufficient_evidence",
    "verified_but_not_validated",
    "validated_with_gaps",
    "research_ready",
]

SubmarineResearchVerificationStatus = Literal[
    "passed",
    "needs_more_verification",
    "blocked",
]

SubmarineResearchValidationStatus = Literal[
    "validated",
    "missing_validation_reference",
    "validation_failed",
    "blocked",
]

SubmarineResearchProvenanceStatus = Literal["traceable", "partial", "missing"]

class SubmarineResearchEvidenceSummary(BaseModel):
    readiness_status: SubmarineResearchReadinessStatus
    verification_status: SubmarineResearchVerificationStatus
    validation_status: SubmarineResearchValidationStatus
    provenance_status: SubmarineResearchProvenanceStatus
    confidence: Literal["high", "medium", "low"] = "medium"
    blocking_issues: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    passed_evidence: list[str] = Field(default_factory=list)
    benchmark_highlights: list[str] = Field(default_factory=list)
    provenance_highlights: list[str] = Field(default_factory=list)
    artifact_virtual_paths: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k research_evidence_model`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/models.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add submarine research evidence models"
```

### Task 2: Add evidence aggregation helpers

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/evidence.py`
- Modify: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Add evidence-semantic coverage for the four key cases:

1. verification passed + no validation reference -> `verified_but_not_validated`
2. verification passed + validated benchmark + traceable provenance -> `research_ready`
3. validation failed -> non-ready status
4. validation passed + provenance partial -> `validated_with_gaps`

Suggested shape:

```python
summary = build_research_evidence_summary(
    acceptance_profile=None,
    acceptance_assessment={...},
    scientific_verification_assessment={"status": "research_ready", ...},
    scientific_study_summary={"study_execution_status": "completed", ...},
    experiment_summary={"experiment_status": "completed", ...},
    output_delivery_plan=[...],
    artifact_virtual_paths=[...],
)
assert summary["readiness_status"] == "verified_but_not_validated"
assert summary["validation_status"] == "missing_validation_reference"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k research_evidence_semantics`
Expected: FAIL because the evidence helper module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `evidence.py` with focused helpers:

```python
def build_verification_status(...): ...
def build_validation_status(...): ...
def build_provenance_status(...): ...
def build_research_evidence_summary(...): ...
```

Keep v1 semantics intentionally compact:

- verification status comes primarily from `scientific_verification_assessment.status`
- validation status comes from benchmark comparisons and whether an acceptance profile actually defines benchmark targets
- provenance status comes from experiment/study/output evidence entrypoints and delivered artifacts
- aggregate readiness uses the conservative rule:
  - no validation reference -> at most `verified_but_not_validated`

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k "research_evidence_model or research_evidence_semantics"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/evidence.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add submarine research evidence aggregation"
```

## Chunk 2: Reporting Integration

### Task 3: Add research-evidence summary to final reports

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing test**

Add result-report coverage for the conservative semantic rule:

- a run with passed numerical verification but no benchmark targets should produce:
  - `verification_status == "passed"`
  - `validation_status == "missing_validation_reference"`
  - `readiness_status == "verified_but_not_validated"`

Suggested assertions:

```python
research = final_payload["research_evidence_summary"]
assert research["verification_status"] == "passed"
assert research["validation_status"] == "missing_validation_reference"
assert research["readiness_status"] == "verified_but_not_validated"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k verified_but_not_validated`
Expected: FAIL because final reporting does not expose unified research evidence yet.

- [ ] **Step 3: Write minimal implementation**

Update `reporting.py` to:

- import the new `build_research_evidence_summary(...)`
- build `research_evidence_summary` after acceptance / scientific verification / experiment summaries are available
- add it to `final-report.json`
- render a compact Markdown / HTML section with:
  - readiness
  - verification status
  - validation status
  - provenance status
  - evidence gaps
  - passed evidence

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k verified_but_not_validated`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/reporting.py backend/tests/test_submarine_result_report_tool.py
git commit -m "feat: add research evidence summary to reports"
```

### Task 4: Emit dedicated research-evidence artifact and cover validated/failed cases

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing test**

Extend reporting coverage so the final-report tool also verifies:

1. benchmark-validated + traceable provenance -> `research_ready`
2. validation failure -> non-ready outcome
3. `research-evidence-summary.json` is written and linked

Target assertions:

```python
research = final_payload["research_evidence_summary"]
assert research["readiness_status"] == "research_ready"
assert any(path.endswith("/research-evidence-summary.json") for path in final_payload["artifact_virtual_paths"])

failed = blocked_payload["research_evidence_summary"]
assert failed["validation_status"] == "validation_failed"
assert failed["readiness_status"] in {"blocked", "insufficient_evidence", "validated_with_gaps"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k "research_ready or validation_failed or research_evidence_artifact"`
Expected: FAIL because dedicated artifact emission and full readiness mapping do not exist yet.

- [ ] **Step 3: Write minimal implementation**

In `reporting.py`:

- add `research-evidence-summary.json` to the report artifact set
- write the aggregate JSON artifact
- include the artifact path in the summary payload and final artifact list
- tighten validation-status mapping:
  - benchmark target exists and passes -> `validated`
  - benchmark target exists and fails -> `validation_failed`
  - no benchmark target exists -> `missing_validation_reference`

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k "verified_but_not_validated or research_ready or validation_failed or research_evidence_artifact"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/reporting.py backend/tests/test_submarine_result_report_tool.py
git commit -m "feat: emit submarine research evidence artifacts"
```

## Chunk 3: Workbench Visibility

### Task 5: Parse research-evidence summary in workbench utilities

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`

- [ ] **Step 1: Write the failing test**

Add utility coverage that parses:

- top-level readiness
- verification / validation / provenance labels
- evidence gaps
- passed evidence
- artifact entrypoints

Suggested shape:

```ts
const summary = buildSubmarineResearchEvidenceSummary({
  research_evidence_summary: {
    readiness_status: "verified_but_not_validated",
    verification_status: "passed",
    validation_status: "missing_validation_reference",
    provenance_status: "traceable",
    confidence: "medium",
    evidence_gaps: ["No applicable benchmark target was available for this run."],
    passed_evidence: ["Scientific verification requirements passed."],
    artifact_virtual_paths: [
      "/mnt/user-data/outputs/submarine/reports/demo/research-evidence-summary.json",
    ],
  },
});
assert.equal(summary?.readinessLabel, "Verified But Not Validated");
assert.equal(summary?.validationStatusLabel, "Missing Validation Reference");
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL because the workbench utilities do not yet parse research evidence summaries.

- [ ] **Step 3: Write minimal implementation**

Add:

- a `SubmarineResearchEvidenceSummary` UI type
- label maps for readiness and dimension statuses
- `buildSubmarineResearchEvidenceSummary(...)`
- artifact copy metadata for `research-evidence-summary.json`

- [ ] **Step 4: Run test to verify it passes**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.utils.ts frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
git commit -m "feat: parse submarine research evidence summaries"
```

### Task 6: Render compact research-evidence section in the runtime panel

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`

- [ ] **Step 1: Write the failing test**

If a dedicated component test is not available, extend the util test coverage first and then use TypeScript / lint as the verification gate for the UI wiring. The UI should show:

- readiness
- verification status
- validation status
- provenance status
- evidence gaps
- passed evidence

- [ ] **Step 2: Run verification to confirm the current UI is incomplete**

Run: `corepack pnpm exec tsc --noEmit`
Expected: either type errors after adding the new final-report payload field, or no visible UI support for research evidence yet.

- [ ] **Step 3: Write minimal implementation**

In `submarine-runtime-panel.tsx`:

- extend `FinalReportPayload` with `research_evidence_summary`
- compute `const researchEvidenceSummary = useMemo(...)`
- add a compact section in the health panel

Do not add:

- a workflow wizard
- a dedicated validation page
- a large compare dashboard

- [ ] **Step 4: Run verification to verify it passes**

Run: `corepack pnpm exec tsc --noEmit`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.tsx frontend/src/components/workspace/submarine-runtime-panel.utils.ts
git commit -m "feat: surface submarine research evidence in workbench"
```

## Chunk 4: Docs And Regression Verification

### Task 7: Update status docs and run focused verification

**Files:**
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Update docs**

Document:

- the new `research_evidence_summary`
- the conservative readiness rule
- the new `research-evidence-summary.json` artifact
- what remains for later slices (`supervisor scientific state machine`, richer provenance, publication-grade figures)

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
git commit -m "docs: record unified research evidence status"
```
