# Experiment Registry And Run Compare Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight experiment registry and run-compare layer for the submarine solver-dispatch workflow so baseline and study-variant runs become explicit experiment members with stable compare artifacts.

**Architecture:** Add typed experiment and compare contracts plus a focused `experiments.py` helper module that derives deterministic experiment ids, run records, and compare summaries from existing solver results. Extend solver dispatch to emit `experiment-manifest.json`, `run-record.json`, and `run-compare-summary.json`, then tighten reporting and workbench summaries to consume those structured experiment artifacts without introducing a rigid compare wizard.

**Tech Stack:** Python, Pydantic, DeerFlow submarine domain modules, pytest, TypeScript, Node test runner, existing submarine runtime-panel utilities

---

## File Structure

- Create: `backend/packages/harness/deerflow/domain/submarine/experiments.py`
  - Deterministic experiment ids, run ids, run-record builders, metric extractors, and compare-summary helpers.
- Modify: `backend/packages/harness/deerflow/domain/submarine/models.py`
  - Add typed experiment, run-record, and compare-summary models.
- Modify: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
  - Emit baseline and variant run records, experiment manifest, and run-compare summary artifacts.
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - Load experiment artifacts and expose a compact `experiment_summary` block in final reports.
- Modify: `backend/tests/test_submarine_domain_assets.py`
  - Cover deterministic experiment id and compare-summary contracts.
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`
  - Cover experiment artifact emission for baseline-only and study-enabled executions.
- Modify: `backend/tests/test_submarine_result_report_tool.py`
  - Cover final-report experiment summaries.
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
  - Parse `experiment_summary` into a stable workbench summary.
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
  - Render a small experiment summary section.
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`
  - Cover experiment summary parsing and labeling.
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`
  - Record the new experiment-registry boundary and remaining compare gaps.

## Chunk 1: Domain Experiment Contracts

### Task 1: Add typed experiment and compare models

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/models.py`
- Test: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Add focused assertions that the domain can represent:

- a baseline run record
- a scientific-study variant run record
- a root experiment manifest
- a compare summary entry

Use a shape like:

```python
record = SubmarineExperimentRunRecord(
    run_id="mesh_independence:coarse",
    experiment_id="darpa-suboff-bare-hull-resistance-study-execution-demo",
    run_role="scientific_study_variant",
    study_type="mesh_independence",
    variant_id="coarse",
    solver_results_virtual_path="/mnt/user-data/outputs/submarine/solver-dispatch/demo/studies/mesh-independence/coarse/solver-results.json",
    run_record_virtual_path="/mnt/user-data/outputs/submarine/solver-dispatch/demo/studies/mesh-independence/coarse/run-record.json",
    execution_status="completed",
)
assert record.run_id == "mesh_independence:coarse"
assert record.study_type == "mesh_independence"
assert record.run_role == "scientific_study_variant"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k experiment_record`
Expected: FAIL because the experiment contracts do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add Pydantic models for:

```python
SubmarineExperimentRunRole = Literal["baseline", "scientific_study_variant"]

class SubmarineExperimentRunRecord(BaseModel):
    run_id: str
    experiment_id: str
    run_role: SubmarineExperimentRunRole
    study_type: SubmarineScientificStudyType | None = None
    variant_id: str | None = None
    solver_results_virtual_path: str
    run_record_virtual_path: str
    execution_status: Literal["planned", "completed", "blocked"]
    metric_snapshot: dict[str, object] = Field(default_factory=dict)

class SubmarineExperimentManifest(BaseModel):
    experiment_id: str
    selected_case_id: str | None = None
    task_type: str
    baseline_run_id: str
    run_records: list[SubmarineExperimentRunRecord] = Field(default_factory=list)
    artifact_virtual_paths: list[str] = Field(default_factory=list)
    experiment_status: Literal["planned", "completed", "blocked"] = "planned"

class SubmarineRunComparison(BaseModel):
    baseline_run_id: str
    candidate_run_id: str
    study_type: SubmarineScientificStudyType | None = None
    variant_id: str | None = None
    compare_status: Literal["completed", "missing_metrics", "blocked"]
    metric_deltas: dict[str, object] = Field(default_factory=dict)
    notes: str | None = None

class SubmarineRunCompareSummary(BaseModel):
    experiment_id: str
    baseline_run_id: str
    comparisons: list[SubmarineRunComparison] = Field(default_factory=list)
    artifact_virtual_paths: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k experiment_record`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/models.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add submarine experiment registry models"
```

### Task 2: Add experiment helper builders

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/experiments.py`
- Modify: `backend/tests/test_submarine_domain_assets.py`

- [ ] **Step 1: Write the failing test**

Add coverage for deterministic helper behavior:

- stable `experiment_id`
- stable `baseline` run id
- stable variant run id
- compact compare summary built from baseline and variant metric snapshots

Target shape:

```python
experiment_id = build_experiment_id(
    selected_case_id="darpa_suboff_bare_hull_resistance",
    run_dir_name="study-execution-demo",
    task_type="resistance",
)
assert experiment_id == "darpa-suboff-bare-hull-resistance-study-execution-demo-resistance"
assert build_experiment_run_id(study_type=None, variant_id=None) == "baseline"
assert build_experiment_run_id(study_type="mesh_independence", variant_id="coarse") == "mesh_independence:coarse"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k experiment_compare`
Expected: FAIL because the experiment helper module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Implement helpers in `experiments.py`:

```python
def build_experiment_id(*, selected_case_id: str | None, run_dir_name: str, task_type: str) -> str:
    ...

def build_experiment_run_id(*, study_type: str | None, variant_id: str | None) -> str:
    ...

def build_metric_snapshot(*, solver_results: Mapping[str, object] | None) -> dict[str, object]:
    ...

def build_run_comparison(... ) -> SubmarineRunComparison:
    ...

def build_run_compare_summary(... ) -> SubmarineRunCompareSummary:
    ...
```

Keep compare v1 intentionally small:

- `Cd`
- `Fx`
- `final_time_seconds`
- `mesh_cells`

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_domain_assets.py -q -k "experiment_record or experiment_compare"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/experiments.py backend/tests/test_submarine_domain_assets.py
git commit -m "feat: add submarine experiment compare helpers"
```

## Chunk 2: Solver Dispatch Experiment Artifacts

### Task 3: Emit baseline experiment artifacts for baseline-only runs

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Write the failing test**

Extend the baseline execution-path tests so a baseline-only run expects:

- `experiment-manifest.json`
- root `run-record.json`
- `run-compare-summary.json`

Target assertions:

```python
assert any(path.endswith("/experiment-manifest.json") for path in artifacts)
assert any(path.endswith("/run-record.json") for path in artifacts)
assert any(path.endswith("/run-compare-summary.json") for path in artifacts)
assert payload["experiment_manifest"]["baseline_run_id"] == "baseline"
assert payload["run_compare_summary"]["comparisons"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k baseline_experiment_manifest`
Expected: FAIL because solver dispatch does not emit experiment artifacts yet.

- [ ] **Step 3: Write minimal implementation**

In `solver_dispatch.py`:

- derive `experiment_id` once the selected case and run dir are known
- emit root `run-record.json` for the baseline execution
- emit root `experiment-manifest.json`
- emit root `run-compare-summary.json` with zero comparisons for baseline-only execution
- attach those artifact paths to the payload and artifact list

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k baseline_experiment_manifest`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py backend/tests/test_submarine_solver_dispatch_tool.py
git commit -m "feat: emit submarine baseline experiment artifacts"
```

### Task 4: Emit variant run records and compare summaries for study-enabled runs

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
- Modify: `backend/tests/test_submarine_solver_dispatch_tool.py`

- [ ] **Step 1: Write the failing test**

Add study-enabled execution coverage that expects:

- variant `run-record.json` files under each executed study directory
- root `run-compare-summary.json` with one comparison per non-baseline variant
- grouped compare rows for `mesh_independence`, `domain_sensitivity`, and `time_step_sensitivity`

Target shape:

```python
compare_summary = json.loads(compare_summary_path.read_text(encoding="utf-8"))
assert compare_summary["baseline_run_id"] == "baseline"
assert len(compare_summary["comparisons"]) == 6
assert compare_summary["comparisons"][0]["candidate_run_id"] == "mesh_independence:coarse"
assert compare_summary["comparisons"][0]["metric_deltas"]["Cd"]["baseline_value"] == 0.12
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k run_compare_summary`
Expected: FAIL because study-enabled execution does not write run-record and compare-summary artifacts yet.

- [ ] **Step 3: Write minimal implementation**

Extend `solver_dispatch.py` so that:

- baseline execution emits a baseline run record
- each executed study variant emits `run-record.json`
- the experiment manifest includes every run record path
- compare summary is built from baseline solver results and variant solver results
- blocked or incomplete runs become compare entries with `blocked` or `missing_metrics` semantics instead of silent omission

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_solver_dispatch_tool.py -q -k "baseline_experiment_manifest or run_compare_summary"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py backend/tests/test_submarine_solver_dispatch_tool.py
git commit -m "feat: emit submarine run compare summaries"
```

## Chunk 3: Reporting Integration

### Task 5: Surface experiment summary in final reports

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Write the failing test**

Add result-report coverage that expects:

- `experiment_summary` in `final-report.json`
- experiment id
- baseline run id
- run count
- compare artifact paths

Suggested assertions:

```python
assert payload["experiment_summary"]["experiment_id"] == "darpa-suboff-bare-hull-resistance-study-execution-demo-resistance"
assert payload["experiment_summary"]["baseline_run_id"] == "baseline"
assert payload["experiment_summary"]["run_count"] == 7
assert payload["experiment_summary"]["compare_virtual_path"].endswith("/run-compare-summary.json")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k experiment_summary`
Expected: FAIL because final reporting does not expose experiment summaries yet.

- [ ] **Step 3: Write minimal implementation**

Update `reporting.py` to:

- load `experiment-manifest.json` and `run-compare-summary.json` when present
- build a compact `experiment_summary` block for final-report JSON
- render the same block in Markdown/HTML with:
  - experiment id
  - experiment status
  - baseline run id
  - run count
  - compare artifact links

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_submarine_result_report_tool.py -q -k experiment_summary`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/packages/harness/deerflow/domain/submarine/reporting.py backend/tests/test_submarine_result_report_tool.py
git commit -m "feat: add submarine experiment summaries to reports"
```

## Chunk 4: Workbench Visibility And Regression Verification

### Task 6: Add minimal workbench summaries for experiment registry artifacts

**Files:**
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts`

- [ ] **Step 1: Write the failing test**

Add utility coverage that:

- parses `experiment_summary`
- exposes the experiment id, baseline run id, run count, compare path, and compact compare rows

Suggested assertion shape:

```ts
assert.equal(summary.experimentId, "darpa-suboff-bare-hull-resistance-study-execution-demo-resistance");
assert.equal(summary.baselineRunId, "baseline");
assert.equal(summary.runCount, 7);
assert.equal(summary.comparePath, "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json");
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: FAIL because the workbench utilities do not summarize experiment registry payloads yet.

- [ ] **Step 3: Write minimal implementation**

Add:

- a `SubmarineExperimentSummary` type
- a summary builder for `experiment_summary`
- a compact runtime-panel section showing:
  - experiment id
  - baseline run
  - run count
  - compact compare notes
  - experiment and compare artifact links

Do not add:

- a free-form run selector
- a chart-heavy compare dashboard
- a workflow wizard

- [ ] **Step 4: Run test to verify it passes**

Run: `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/submarine-runtime-panel.utils.ts frontend/src/components/workspace/submarine-runtime-panel.tsx frontend/src/components/workspace/submarine-runtime-panel.utils.test.ts
git commit -m "feat: surface submarine experiment summaries in workbench"
```

### Task 7: Update status docs and run focused regression verification

**Files:**
- Modify: `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md`

- [ ] **Step 1: Update docs**

Document:

- what experiment artifacts are now emitted
- how run compare is scoped in v1
- what still remains for later phases (`validation/provenance`, `supervisor scientific state machine`, `publication-grade compare views`)

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
git add docs/archive/superpowers/specs/2026-03-27-vibe-cfd-requested-outputs-status.md
git commit -m "docs: record experiment registry and compare status"
```
