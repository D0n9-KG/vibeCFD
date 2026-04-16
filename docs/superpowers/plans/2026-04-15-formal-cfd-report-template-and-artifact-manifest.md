# Formal CFD Report Template And Artifact Manifest Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then choose the execution skill that fits the work: use superpowers:subagent-driven-development when delegation benefits outweigh the round-trip, or superpowers:executing-plans when the work is better kept local. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the plan controls below, especially reuse, continuity, artifact lifecycle, validation/review cadence, and any research-overlay constraints.

**Goal:** Upgrade the submarine `final-report` artifacts into a formal CFD technical report with a concise appendix: key result / deliverable files remain itemized with virtual and absolute paths, while OpenFOAM intermediate files are summarized by their workspace locations instead of being exhaustively listed one-by-one.

**Architecture:** Keep the current submarine result-report pipeline and extend it in two places: `reporting.py` will assemble a richer report payload with a compact `artifact_manifest` plus a `workspace_storage_summary`, and `reporting_render.py` will render that payload into a formal technical-report structure for markdown and HTML. No frontend contract rename is required; the existing `final-report.{json,md,html}` filenames stay authoritative.

**Tech Stack:** Python 3.12, DeerFlow submarine domain contracts, JSON/Markdown/HTML report rendering, pytest

**Prior Art Survey:** `docs/superpowers/prior-art/2026-04-15-formal-cfd-report-template-survey.md`

**Reuse Strategy:** adapt existing project

**Session Status File:** `docs/superpowers/session-status/2026-04-15-formal-cfd-report-template-and-artifact-manifest-status.md`

**Context Summary:** none

**Primary Context Files:** `docs/superpowers/prior-art/2026-04-15-formal-cfd-report-template-survey.md`; `backend/packages/harness/deerflow/domain/submarine/reporting.py`; `backend/packages/harness/deerflow/domain/submarine/reporting_render.py`; `backend/packages/harness/deerflow/domain/submarine/artifact_store.py`; `backend/tests/test_submarine_result_report_tool.py`

**Artifact Lifecycle:** Keep the prior-art survey, this plan, and the companion status file. Keep new payload fields, renderer logic, and regression tests if they land. Delete no-longer-needed scratch report dumps or ad-hoc inspection scripts; do not create alternate report filenames or a second parallel report pipeline.

**Workspace Strategy:** current workspace

**Validation Strategy:** strict tdd

**Review Cadence:** each milestone

**Checkpoint Strategy:** user-directed checkpoints

**Research Overlay:** disabled

**Research Mainline:** none

**Non-Negotiables:** none

**Forbidden Regressions:** downgrading the report back into a pure workflow summary; omitting artifact provenance once a formal report exists; hiding OpenFOAM workspace paths behind only virtual `/mnt/...` references when the host absolute path is known; reverting to an exhaustive workspace-file dump after the user explicitly chose a concise appendix

**Method Fidelity Checks:** the final report must include formal CFD-report sections, a compact key-file inventory with descriptions and both virtual / absolute paths when resolvable, plus a directory-level summary that tells the user where OpenFOAM intermediate files, postProcessing outputs, and study workspaces live

**Scale Gate:** none

**Decision Log:** none - record durable decisions in the session status file

**Research Findings:** none

**Uncertainty Hotspots:** how much of the current payload already exposes enough information to describe file purpose without new schema churn; whether artifact grouping should be rendered directly from `artifact_virtual_paths` or from a new normalized manifest structure

**Replan Triggers:** if adding absolute workspace paths requires changing thread runtime contracts beyond reporting-only scope; if report rendering starts depending on frontend-only assumptions; if the manifest cannot cleanly classify outputs and workspace files from current runtime/artifact data

---

### Task 1: Add Failing Tests For Formal Report Structure And File Appendix

**Files:**
- Modify: `backend/tests/test_submarine_result_report_tool.py`
- Test: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Add a failing test for formal technical-report sections in markdown and HTML**

```python
assert "## 计算目标与工况" in markdown
assert "## 几何、网格与计算设置" in markdown
assert "## 结果、验证与结论边界" in markdown
assert "## 文件清单与路径索引" in markdown
assert "<h2>计算目标与工况</h2>" in html
```

- [ ] **Step 2: Run it to verify RED**

Run: `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py -k formal_report_sections -q`
Expected: FAIL because the current renderer still emits the old stage-summary structure

- [ ] **Step 3: Add a failing test for file-manifest entries that include file role, virtual path, and absolute path**

```python
assert any(item["virtual_path"].endswith("/final-report.json") for item in payload["artifact_manifest"])
assert any(item["absolute_path"].endswith("final-report.json") for item in payload["artifact_manifest"])
assert any(item["location_kind"] == "workspace_case" for item in payload["artifact_manifest"])
```

- [ ] **Step 4: Run it to verify RED**

Run: `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py -k artifact_manifest_absolute_paths -q`
Expected: FAIL because the payload does not yet expose a formal artifact manifest

### Task 2: Build A Formal Artifact Manifest In The Reporting Payload

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/artifact_store.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Test: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Add path-resolution helpers for both `/mnt/user-data/outputs/...` and `/mnt/user-data/workspace/...`**

```python
def resolve_workspace_artifact(outputs_dir: Path, virtual_path: str) -> Path | None:
    ...
```

- [ ] **Step 2: Build a normalized manifest entry shape in reporting**

```python
{
    "label": "...",
    "description": "...",
    "filename": "...",
    "file_type": "...",
    "location_kind": "report_output" | "solver_output" | "workspace_case" | "workspace_postprocess" | "study_workspace_case",
    "stage": "...",
    "virtual_path": "...",
    "absolute_path": "...",
    "is_final_deliverable": True | False,
}
```

- [ ] **Step 3: Populate the manifest from current payload state plus workspace case roots**

```python
artifact_manifest = build_report_artifact_manifest(
    outputs_dir=outputs_dir,
    source_artifact_virtual_paths=snapshot.artifact_virtual_paths,
    final_artifact_virtual_paths=new_artifacts,
    workspace_case_dir_virtual_path=snapshot.workspace_case_dir_virtual_path,
    run_script_virtual_path=snapshot.run_script_virtual_path,
)
```

- [ ] **Step 4: Run the targeted manifest tests**

Run: `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py -k artifact_manifest -q`
Expected: PASS

### Task 3: Rebuild Markdown And HTML Into A Formal CFD Report

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting_render.py`
- Test: `backend/tests/test_submarine_result_report_tool.py`

- [ ] **Step 1: Replace the current stage-summary layout with formal technical-report sections**

```python
sections = [
    "计算目标与工况",
    "几何、网格与计算设置",
    "结果、验证与结论边界",
    "可复现性与追溯",
    "文件清单与路径索引",
    "建议下一步",
]
```

- [ ] **Step 2: Render the new artifact appendix with description plus both path forms**

```python
- 文件：`final-report.json`
- 用途：最终结构化报告 JSON
- 类型：report_output
- 虚拟路径：`/mnt/...`
- 绝对路径：`C:\\...`
```

- [ ] **Step 3: Keep all current scientific gate / evidence information, but place it under formal report headings**

```python
overview = payload["report_overview"]
solver_metrics = payload["solver_metrics"]
acceptance = payload["acceptance_assessment"]
```

- [ ] **Step 4: Run the focused render suite**

Run: `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py -k "formal_report_sections or decomposition_render or artifact_manifest" -q`
Expected: PASS

### Task 4: Verify Against Real SUBOFF Outputs And Refresh Handoff

**Files:**
- Modify: `docs/superpowers/session-status/2026-04-15-formal-cfd-report-template-and-artifact-manifest-status.md`

- [ ] **Step 1: Run the broader result-report suite**

Run: `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py -q`
Expected: PASS

- [ ] **Step 2: Inspect a real generated report using thread `01fec432-dead-4cb3-8c2d-09896f4fe832` and confirm that outputs plus workspace/OpenFOAM case files appear in the appendix**

Run: `Get-Content -Raw backend/.deer-flow/threads/01fec432-dead-4cb3-8c2d-09896f4fe832/user-data/outputs/submarine/reports/suboff_solid/final-report.md`
Expected: markdown now includes formal sections and file manifest lines with absolute paths

- [ ] **Step 3: Refresh the status file with the verified outcome and any remaining report-quality gaps**

```markdown
- verified whether the new report is now suitable as a formal CFD technical report
- note any remaining gaps such as missing figures, weak physical discussion, or missing benchmark context
```
