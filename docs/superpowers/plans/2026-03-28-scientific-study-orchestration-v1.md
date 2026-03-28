# Scientific Study Orchestration v1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic scientific study planning, variant orchestration, and verification artifact aggregation for the baseline submarine CFD path so the platform can generate research evidence instead of only asking for it.

**Architecture:** Add explicit scientific-study domain contracts plus a focused study-orchestration helper module that derives case-aware study definitions and variants from the selected baseline case. Extend solver dispatch to emit `study-plan.json`, `study-manifest.json`, per-variant result paths, and aggregated `verification-*.json` artifacts, then tighten reporting and workbench summaries to consume only structured study evidence while keeping the user-facing intent layer open-ended.

**Tech Stack:** Python, Pydantic, DeerFlow submarine domain modules, pytest, TypeScript, Node test runner, existing submarine runtime-panel utilities

---

## File Structure

- Create: `backend/packages/harness/deerflow/domain/submarine/studies.py`
  - Deterministic study definitions, variant derivation rules, manifest builders, and aggregation helpers.
- Modify: `backend/packages/harness/deerflow/domain/submarine/models.py`
  - Add typed scientific-study models that can be serialized into artifacts and reused by reporting/UI.
- Modify: `backend/packages/harness/deerflow/domain/submarine/verification.py`
  - Consume aggregated verification study payloads strictly and remove the permissive fallback that treats any matching artifact path as passed evidence.
- Modify: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
  - Materialize study plans/manifests, derive stable study directories, and aggregate per-study verification outputs.
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - Surface structured study-manifest and verification-artifact summaries in final reports.
- Modify: `backend/tests/test_submarine_domain_assets.py`
  - Cover study definitions/variant planning at the domain layer.
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`
  - Cover artifact emission for study plans/manifests and aggregated verification outputs.
- Modify: `backend/tests/test_submarine_result_report_tool.py`
  - Cover strict study-evidence handling and final-report study summaries.
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - Parse study-manifest and verification-study payloads into concise workbench summaries.
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - Render minimal study-status visibility without turning the UI into a rigid experiment wizard.
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - Cover workbench summaries for study manifests and verification outcomes.
- Modify: `docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - Record the new study-orchestration boundary and remaining research gaps after v1.

## Chunk 1: Domain Contracts And Planner

### Task 1: Add typed scientific-study models

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/models.py`
- Test: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Add assertions that the selected case exposes typed scientific-study definitions and deterministic variant labels for:
- `mesh_independence`
- `domain_sensitivity`
- `time_step_sensitivity`

Use a focused assertion block similar to:

```python
assert [item.study_type for item in definitions] == [
    "mesh_independence",
    "domain_sensitivity",
    "time_step_sensitivity",
]
assert [variant.variant_id for variant in mesh_definition.variants] == [
    "coarse",
    "baseline",
    "fine",
]
assert mesh_definition.monitored_quantity == "Cd"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k scientific_study`
Expected: FAIL because the study-definition helpers and models do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add Pydantic models for:

```python
class SubmarineScientificStudyVariant(BaseModel):
    study_type: Literal["mesh_independence", "domain_sensitivity", "time_step_sensitivity"]
    variant_id: str
    variant_label: str
    parameter_overrides: dict[str, float | int | str]
    rationale: str

class SubmarineScientificStudyDefinition(BaseModel):
    study_type: Literal["mesh_independence", "domain_sensitivity", "time_step_sensitivity"]
    summary_label: str
    monitored_quantity: str
    pass_fail_tolerance: float
    variants: list[SubmarineScientificStudyVariant] = Field(default_factory=list)

class SubmarineScientificStudyManifest(BaseModel):
    selected_case_id: str
    baseline_configuration_snapshot: dict[str, object] = Field(default_factory=dict)
    study_definitions: list[SubmarineScientificStudyDefinition] = Field(default_factory=list)
    artifact_virtual_paths: list[str] = Field(default_factory=list)
    study_execution_status: str = "planned"

class SubmarineScientificStudyResult(BaseModel):
    study_type: str
    monitored_quantity: str
    baseline_value: float | None = None
    compared_values: list[dict[str, object]] = Field(default_factory=list)
    relative_spread: float | None = None
    status: Literal["passed", "blocked", "missing_evidence"]
    summary_zh: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k scientific_study`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/models.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add submarine scientific study models"
```

### Task 2: Add deterministic study-planning helpers

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/studies.py`
- Modify: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Add coverage that `darpa_suboff_bare_hull_resistance` produces a stable study plan from baseline simulation requirements, including explicit override coefficients:

```python
manifest = build_scientific_study_manifest(
    selected_case=case,
    simulation_requirements={"delta_t_seconds": 1.0, "end_time_seconds": 200.0},
)
assert manifest.study_execution_status == "planned"
assert manifest.study_definitions[0].variants[0].parameter_overrides["mesh_scale_factor"] == 0.75
assert manifest.study_definitions[1].variants[2].parameter_overrides["domain_extent_multiplier"] == 1.20
assert manifest.study_definitions[2].variants[0].parameter_overrides["delta_t_multiplier"] == 2.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k study_manifest`
Expected: FAIL because `build_scientific_study_manifest` is undefined.

- [ ] **Step 3: Write minimal implementation**

Implement focused planner helpers in `studies.py`:

```python
def build_effective_scientific_study_definitions(*, selected_case, simulation_requirements) -> list[SubmarineScientificStudyDefinition]:
    ...

def build_scientific_study_manifest(*, selected_case, simulation_requirements, baseline_configuration_snapshot) -> SubmarineScientificStudyManifest:
    ...
```

Rules for v1:
- mesh variants: `0.75x`, `1.00x`, `1.25x`
- domain variants: `0.85x`, `1.00x`, `1.20x`
- deltaT variants: `2.0x`, `1.0x`, `0.5x`
- monitored quantity for the resistance baseline path: `Cd`
- pass/fail tolerance should default to the case benchmark tolerance when available, otherwise a conservative fallback such as `0.02`

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k "scientific_study or study_manifest"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/studies.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add deterministic submarine study planner"
```

## Chunk 2: Solver Dispatch Study Artifacts

### Task 3: Emit `study-plan.json` and `study-manifest.json` during dispatch planning

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Write the failing test**

Extend the planned-dispatch test so it expects:
- `study-plan.json`
- `study-manifest.json`
- artifact paths for all three studies
- stable study directory names under `studies/`

Example assertions:

```python
assert any(path.endswith("/study-plan.json") for path in artifacts)
assert any(path.endswith("/study-manifest.json") for path in artifacts)
assert payload["study_manifest"]["study_execution_status"] == "planned"
assert payload["study_manifest"]["study_definitions"][0]["study_type"] == "mesh_independence"
assert payload["study_manifest"]["study_definitions"][0]["variants"][0]["variant_id"] == "coarse"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k study_plan`
Expected: FAIL because dispatch artifacts do not include study-plan or study-manifest payloads.

- [ ] **Step 3: Write minimal implementation**

In `solver_dispatch.py`:
- build a study manifest after the baseline case and simulation requirements are resolved
- serialize a compact `study-plan.json` for humans plus `study-manifest.json` for structured consumers
- place per-variant artifact targets under:
  - `studies/mesh-independence/<variant>/`
  - `studies/domain-sensitivity/<variant>/`
  - `studies/time-step-sensitivity/<variant>/`
- attach those artifact paths to the dispatch payload so reporting/UI can discover them without guessing

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k study_plan`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py backend/tests/test_submarine_solver_dispatch_tool.py
git commit -m "feat: emit submarine study plan artifacts"
```

### Task 4: Aggregate executed study variants into `verification-*.json`

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/studies.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Write the failing test**

Add an execution-path test using the fake sandbox that expects:
- one baseline result
- per-study variant result paths recorded in the manifest
- aggregated verification artifacts written at the dispatch root

Target shape:

```python
verification_payload = json.loads(
    (solver_results_dir / "verification-mesh-independence.json").read_text(encoding="utf-8")
)
assert verification_payload["study_type"] == "mesh_independence"
assert verification_payload["status"] == "passed"
assert verification_payload["compared_values"][0]["variant_id"] == "coarse"
assert verification_payload["relative_spread"] is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k verification_mesh`
Expected: FAIL because no study-aggregation artifacts are produced.

- [ ] **Step 3: Write minimal implementation**

Add helpers that:
- map each study variant to a stable subdirectory
- collect per-variant `solver-results.json`
- extract the monitored quantity from each result payload
- compute relative spread versus the baseline variant
- write:
  - `verification-mesh-independence.json`
  - `verification-domain-sensitivity.json`
  - `verification-time-step-sensitivity.json`

Keep v1 simple:
- compare only the monitored quantity recorded in `latest_force_coefficients`
- if any required variant result is missing or lacks the monitored quantity, mark the study as `missing_evidence`
- never mark a study as `passed` based on artifact-path presence alone

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k "study_plan or verification_mesh"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/studies.py backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py backend/tests/test_submarine_solver_dispatch_tool.py
git commit -m "feat: aggregate submarine verification study artifacts"
```

## Chunk 3: Reporting And Scientific Verification Gates

### Task 5: Tighten study-evidence assessment and surface manifest context in final reports

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/verification.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing test**

Add report-tool coverage for two cases:
- a valid parsed verification artifact should drive requirement status
- a matching artifact path with invalid or missing JSON should remain `missing_evidence`, not `passed`

Example assertions:

```python
assert payload["scientific_verification_assessment"]["requirements"][2]["status"] == "passed"
assert payload["scientific_verification_assessment"]["requirements"][3]["status"] == "missing_evidence"
assert "study-manifest.json" in payload["scientific_study_summary"]["artifact_virtual_paths"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k scientific_study`
Expected: FAIL because reporting does not yet expose structured study summaries and `verification.py` still has permissive fallback behavior.

- [ ] **Step 3: Write minimal implementation**

Update `verification.py` to:
- require parseable JSON payloads for `artifact_presence` scientific-study requirements
- prefer the aggregated study result `status`, `summary_zh`, and `relative_spread`
- downgrade unreadable or incomplete study artifacts to `missing_evidence`

Update `reporting.py` to:
- load `study-manifest.json` when present
- include a compact `scientific_study_summary` block in `final-report.json`
- render the same block in Markdown/HTML with:
  - study type
  - execution status
  - artifact links
  - verification status

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k scientific_study`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/verification.py backend/packages/harness/deerflow/domain/submarine/reporting.py backend/tests/test_submarine_result_report_tool.py
git commit -m "feat: tighten submarine study evidence assessment"
```

## Chunk 4: Workbench Visibility And Regression Verification

### Task 6: Add minimal workbench summaries for study manifests and verification results

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`

- [ ] **Step 1: Write the failing test**

Add utility coverage that:
- parses `scientific_study_summary`
- surfaces a small list of study statuses and artifact links
- keeps the UI summary read-only and evidence-focused

Suggested assertion shape:

```ts
assert.equal(summary.statusLabel, "Planned");
assert.equal(summary.studies[0]?.studyType, "mesh_independence");
assert.equal(summary.studies[0]?.verificationStatus, "passed");
assert.equal(summary.artifactPaths[0], "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json");
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL because the workbench utilities do not summarize scientific-study manifests yet.

- [ ] **Step 3: Write minimal implementation**

Add:
- a `SubmarineScientificStudySummary` type
- a summary builder that consumes `final-report.json` and `study-manifest.json`
- a small runtime-panel section that lists:
  - study type
  - execution status
  - verification status
  - artifact entrypoints

Do not add:
- compare dashboards
- editable matrices
- wizard-like step gating

- [ ] **Step 4: Run test to verify it passes**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.utils.ts frontend/src/components/workspace/submarine-runtime-panel.tsx frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
git commit -m "feat: surface submarine study summaries in workbench"
```

### Task 7: Update status docs and run focused regression verification

**Files:**
- Modify: `docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Update docs**

Document:
- what v1 now auto-generates
- which studies are deterministic in v1
- what still remains for later phases (`experiment registry`, `run compare`, `supervisor scientific state machine`)

- [ ] **Step 2: Run focused backend verification**

Run: `uv run pytest tests/test_submarine_domain_assets.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py -q`
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
git add docs/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md
git commit -m "docs: record scientific study orchestration status"
```
