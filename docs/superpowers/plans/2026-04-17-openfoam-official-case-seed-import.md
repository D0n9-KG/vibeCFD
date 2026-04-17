# OpenFOAM Official Case Seed Import Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then choose the execution skill that fits the work: use superpowers:subagent-driven-development when delegation benefits outweigh the round-trip, or superpowers:executing-plans when the work is better kept local. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the plan controls below, especially reuse, continuity, artifact lifecycle, validation/review cadence, and any research-overlay constraints.

**Goal:** Add an official OpenFOAM case-seed input path that lets users upload minimal tutorial seed files, describe remaining conditions in the normal chat box, and run `cavity` / `pitzDaily` through the real frontend VibeCFD flow with visible process, files, and report outputs.

**Architecture:** Extend the existing STL-first runtime into a parallel `openfoam_case_seed` path instead of creating a demo executor. Backend work will add seed classification, official-case runtime metadata, case assembly, and case-specific dispatch profiles; frontend work will surface the new runtime truth through the existing workbench and file/report views.

**Tech Stack:** Python backend runtime/contracts/tools, OpenFOAM 13 sandbox, existing DeerFlow thread runtime state, React/Next frontend workbench, Node/unit tests, pytest, browser-driven product verification

**Prior Art Survey:** none needed - this is engineering execution against the approved spec, which already pins the exact OpenFOAM 13 tutorial baseline and upstream source commit

**Reuse Strategy:** adapt existing project

**Artifact Scope:** task-local

**Artifact Epoch:** openfoam-official-case-seed-import

**Supersedes:** none

**Session Status File:** `docs/superpowers/session-status/2026-04-17-openfoam-official-case-seed-import-status.md`

**Context Summary:** none

**Primary Context Files:** `docs/superpowers/specs/2026-04-17-openfoam-official-case-seed-import-design.md`; `backend/packages/harness/deerflow/domain/submarine/contracts.py`; `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py`; `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`; `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`; `backend/packages/harness/deerflow/domain/submarine/reporting.py`; `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`; `frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts`; `frontend/src/components/workspace/chats/chat-box.artifacts.ts`

**Artifact Lifecycle:** Keep the spec, this plan, and the companion session status file. Keep minimal official-case seed fixtures only if they are the smallest files needed for deterministic automated tests; delete any full tutorial copies, downloaded zip bundles, ad-hoc exported cases, and temporary sandbox dumps after product verification. Replace STL-only assumptions in the affected runtime/reporting paths instead of leaving duplicate official-case branches beside them.

**Workspace Strategy:** current workspace

**Validation Strategy:** mixed

**Review Cadence:** each milestone

**Checkpoint Strategy:** user-directed checkpoints

**Research Overlay:** disabled

**Research Mainline:** none

**Evaluation Rubric:** none

**Non-Negotiables:** none

**Forbidden Regressions:** none

**Method Fidelity Checks:** none

**Scale Gate:** none

**Freeze Gate:** none

**Decision Log:** none - record durable decisions in session status and linked findings docs

**Research Findings:** none

**Uncertainty Hotspots:** exact chat-to-tool routing for official seeds in the current lead-agent flow; how much frontend wording/model logic assumes every run has `geometry_virtual_path`; whether repo-kept fixtures are necessary or whether runtime download/copy is enough for deterministic tests

**Replan Triggers:** if official-case routing cannot be added without breaking the existing STL path; if the current reporting contract cannot represent official-case provenance without a larger schema split; if frontend thread/workbench assumptions about geometry prove too widespread for this slice

---

### Task 1: Add Official Case Seed Runtime Contracts

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/official_case_seed_models.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- Modify: `backend/packages/harness/deerflow/agents/thread_state.py`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`
- Test: `backend/tests/test_openfoam_case_seed_contracts.py`

- [x] **Step 1: Write the failing backend contract tests for the new official-case fields**

```python
def test_runtime_snapshot_accepts_official_case_seed_metadata() -> None:
    snapshot = build_runtime_snapshot(
        current_stage="solver-dispatch",
        task_summary="Run official cavity seed",
        task_type="official_openfoam_case",
        geometry_virtual_path="",
        geometry_family=None,
        next_recommended_stage="solver-dispatch",
        report_virtual_path="/mnt/user-data/outputs/submarine/reports/cavity/final-report.md",
        input_source_type="openfoam_case_seed",
        official_case_id="cavity",
        official_case_seed_virtual_paths=["/mnt/user-data/uploads/cavity/system/blockMeshDict"],
        official_case_profile={"source_commit": "441953dfbb4270dd54e14672e194e4a4a478afc4"},
    )
    assert snapshot.input_source_type == "openfoam_case_seed"
    assert snapshot.official_case_id == "cavity"
```

- [x] **Step 2: Run the new backend contract test to confirm the starting state fails**

Run: `uv run --project backend pytest backend/tests/test_openfoam_case_seed_contracts.py -q`
Expected: FAIL because the current runtime snapshot / state models do not yet support official-case seed metadata

- [x] **Step 3: Add the shared Python runtime fields and thread-state support**

```python
class SubmarineRuntimeSnapshot(BaseModel):
    input_source_type: Literal["geometry_seed", "openfoam_case_seed"] = "geometry_seed"
    official_case_id: str | None = None
    official_case_seed_virtual_paths: list[str] = Field(default_factory=list)
    assembled_case_virtual_paths: list[str] = Field(default_factory=list)
    official_case_profile: dict[str, Any] | None = None
```

- [x] **Step 4: Mirror the new runtime fields into the frontend contract payload types**

```ts
export type SubmarineRuntimeSnapshotPayload = {
  input_source_type?: "geometry_seed" | "openfoam_case_seed" | string | null;
  official_case_id?: string | null;
  official_case_seed_virtual_paths?: string[] | null;
  assembled_case_virtual_paths?: string[] | null;
  official_case_profile?: Record<string, unknown> | null;
  // existing fields...
};
```

- [x] **Step 5: Re-run the backend contract test and the frontend typecheck**

Run: `uv run --project backend pytest backend/tests/test_openfoam_case_seed_contracts.py -q`
Expected: PASS

Run: `corepack pnpm exec tsc --noEmit`
Expected: PASS with the updated payload types

### Task 2: Build Seed Classification, Ambiguity Resolution, And Pinned Fixtures

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/official_case_seed_resolver.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_runtime_context.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
- Create: `backend/tests/fixtures/openfoam_case_seeds/cavity/system/blockMeshDict`
- Create: `backend/tests/fixtures/openfoam_case_seeds/pitzDaily/pitzDaily.blockMeshDict`
- Test: `backend/tests/test_openfoam_case_seed_resolver.py`
- Test: `backend/tests/test_submarine_runtime_context.py`

- [x] **Step 1: Write failing tests for valid seeds, mixed uploads, and partial imports**

```python
def test_resolve_official_case_seed_detects_cavity_blockmesh_only(tmp_path: Path) -> None:
    uploads = tmp_path / "uploads"
    (uploads / "system").mkdir(parents=True)
    (uploads / "system" / "blockMeshDict").write_text("FoamFile{}", encoding="utf-8")
    result = resolve_official_case_seed(uploads)
    assert result.case_id == "cavity"

def test_resolve_input_source_requires_user_choice_when_stl_and_case_seed_coexist(...) -> None:
    result = resolve_runtime_input_source(...)
    assert result.status == "ambiguous"
    assert "official OpenFOAM case reconstruction" in result.user_message
```

- [x] **Step 2: Run the resolver/context tests to confirm they fail first**

Run: `uv run --project backend pytest backend/tests/test_openfoam_case_seed_resolver.py backend/tests/test_submarine_runtime_context.py -q`
Expected: FAIL because no official-case resolver or mixed-source precedence exists yet

- [x] **Step 3: Implement the resolver with deterministic precedence and minimum-valid tree rules**

```python
def resolve_runtime_input_source(...) -> RuntimeInputResolution:
    if explicit_case_seed_intent and valid_case_seed:
        return RuntimeInputResolution(kind="openfoam_case_seed", ...)
    if valid_case_seed and valid_stl:
        return RuntimeInputResolution(kind="ambiguous", ...)
    if valid_case_seed:
        return RuntimeInputResolution(kind="openfoam_case_seed", ...)
    if valid_stl:
        return RuntimeInputResolution(kind="geometry_seed", ...)
    return RuntimeInputResolution(kind="missing", ...)
```

- [x] **Step 4: Wire design-brief input resolution to use the new case-seed resolver before STL fallback**

```python
resolved_input = resolve_runtime_input_source(
    thread_id=thread_id,
    uploads_dir=uploads_dir,
    explicit_geometry_path=geometry_path,
    existing_runtime=existing_runtime,
    existing_brief=existing_payload,
    uploaded_files=(runtime.state or {}).get("uploaded_files"),
    task_description=task_description,
)
```

- [x] **Step 5: Re-run the resolver/context tests**

Run: `uv run --project backend pytest backend/tests/test_openfoam_case_seed_resolver.py backend/tests/test_submarine_runtime_context.py -q`
Expected: PASS with coverage for `cavity`, `pitzDaily`, mixed-upload ambiguity, and partial-import rejection

- [x] **Step 6: Add the smallest pinned official seed fixtures used by automated tests and frontend product validation**

```text
backend/tests/fixtures/openfoam_case_seeds/cavity/system/blockMeshDict
backend/tests/fixtures/openfoam_case_seeds/pitzDaily/pitzDaily.blockMeshDict
```

Rule:

```text
- Copy each fixture from the pinned OpenFOAM 13 upstream source commit `441953dfbb4270dd54e14672e194e4a4a478afc4`.
- Do not keep full tutorial bundles in-repo.
- Use these same minimal files for frontend upload validation when possible.
```

### Task 3: Generalize Design Brief, Dispatch, And Reporting For Official Cases

**Files:**
- Create: `backend/packages/harness/deerflow/domain/submarine/official_case_profiles.py`
- Create: `backend/packages/harness/deerflow/domain/submarine/official_case_assembly.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/provenance.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting.py`
- Modify: `backend/packages/harness/deerflow/domain/submarine/reporting_render.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`
- Test: `backend/tests/test_submarine_design_brief_tool.py`
- Test: `backend/tests/test_official_case_assembly.py`
- Test: `backend/tests/test_official_case_provenance.py`
- Test: `backend/tests/test_submarine_solver_dispatch_tool.py`
- Test: `backend/tests/test_submarine_result_report_tool.py`

- [x] **Step 1: Write failing assembly and reporting tests for `cavity` and `pitzDaily` execution profiles**

```python
def test_assemble_cavity_case_preserves_legacy_execution_profile(...) -> None:
    assembled = assemble_official_case(...)
    assert assembled.execution_profile.case_id == "cavity"
    assert assembled.execution_profile.command_chain == ["blockMesh", "icoFoam"]

def test_assemble_pitzdaily_case_preserves_modern_execution_profile(...) -> None:
    assembled = assemble_official_case(...)
    assert assembled.execution_profile.case_id == "pitzDaily"
    assert assembled.execution_profile.command_chain[0].startswith("blockMesh -dict")
    assert assembled.execution_profile.command_chain[1] == "foamRun"

def test_official_case_provenance_manifest_records_per_file_source(...) -> None:
    manifest = build_official_case_provenance_manifest(...)
    entry = manifest["files"]["system/controlDict"]
    assert entry["source_commit"] == "441953dfbb4270dd54e14672e194e4a4a478afc4"
    assert entry["source_kind"] in {
        "imported_seed",
        "pinned_official_source",
        "synthesized_from_official_default",
        "user_override",
        "project_compatibility_adaptation",
    }
```

- [x] **Step 2: Run the targeted backend tests and capture the expected failures**

Run: `uv run --project backend pytest backend/tests/test_official_case_assembly.py backend/tests/test_submarine_solver_dispatch_tool.py backend/tests/test_submarine_result_report_tool.py -q`
Expected: FAIL because dispatch/reporting still assume STL geometry and have no official-case execution profile support

Run: `uv run --project backend pytest backend/tests/test_official_case_provenance.py -q`
Expected: FAIL because the existing provenance manifest does not yet capture per-file official-case sources

- [x] **Step 3: Implement official-case profile and assembly modules with pinned-source provenance**

```python
OFFICIAL_CASE_PROFILES = {
    "cavity": OfficialCaseProfile(
        case_id="cavity",
        source_commit="441953dfbb4270dd54e14672e194e4a4a478afc4",
        command_chain=["blockMesh", "icoFoam"],
    ),
    "pitzDaily": OfficialCaseProfile(
        case_id="pitzDaily",
        source_commit="441953dfbb4270dd54e14672e194e4a4a478afc4",
        command_chain=["blockMesh -dict {seed_path}", "foamRun"],
    ),
}
```

- [x] **Step 4: Expand the provenance manifest schema and writer so official-case runs record per-file source commit, source path, and classification**

```python
manifest["files"][relative_path] = {
    "source_commit": profile.source_commit,
    "source_path": official_source_path,
    "source_kind": source_kind,
    "imported_virtual_path": imported_virtual_path,
}
```

- [x] **Step 5: Generalize design-brief and solver dispatch to branch on `input_source_type`**

```python
if resolved_input.kind == "openfoam_case_seed":
    payload = run_official_case_dispatch(...)
else:
    payload = run_solver_dispatch(...)
```

- [x] **Step 6: Expose assembled-case file listings and provenance-manifest paths through runtime/report payloads**

```python
payload["assembled_case_virtual_paths"] = assembled_case_virtual_paths
payload["provenance_manifest_virtual_path"] = provenance_manifest_virtual_path
```

- [x] **Step 7: Update reporting so official-case runs describe source commit, imported seeds, execution profile, and completion state without forcing a geometry-upload story**

```python
if snapshot.input_source_type == "openfoam_case_seed":
    payload["official_case_id"] = snapshot.official_case_id
    payload["official_case_seed_virtual_paths"] = snapshot.official_case_seed_virtual_paths
    payload["assembled_case_virtual_paths"] = snapshot.assembled_case_virtual_paths
    payload["official_case_profile"] = snapshot.official_case_profile
```

- [x] **Step 8: Re-run the targeted backend tests**

Run: `uv run --project backend pytest backend/tests/test_official_case_assembly.py backend/tests/test_official_case_provenance.py backend/tests/test_submarine_solver_dispatch_tool.py backend/tests/test_submarine_result_report_tool.py -q`
Expected: PASS with explicit coverage for case-specific solver stacks and official-case provenance

### Task 4: Surface Official Case Runtime Truth In The Frontend

**Files:**
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts`
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.model.ts`
- Modify: `frontend/src/components/workspace/submarine-workbench/submarine-visible-actions.ts`
- Modify: `frontend/src/components/workspace/chats/chat-box.artifacts.ts`
- Modify: `frontend/src/core/threads/utils.ts`
- Modify: `frontend/src/components/workspace/submarine-runtime-panel.contract.ts`
- Test: `frontend/src/components/workspace/submarine-workbench/submarine-session-model.test.ts`
- Test: `frontend/src/components/workspace/submarine-workbench/submarine-visible-actions.test.ts`
- Test: `frontend/src/components/workspace/chats/chat-box.artifacts.test.ts`

- [ ] **Step 1: Write failing frontend tests for official-case labeling, file grouping, and non-geometry runtime summaries**

```ts
void test("buildSubmarineSessionModel shows official case metadata without geometry path", () => {
  const model = buildSubmarineSessionModel({
    runtime: {
      input_source_type: "openfoam_case_seed",
      official_case_id: "cavity",
      official_case_seed_virtual_paths: ["/mnt/user-data/uploads/cavity/system/blockMeshDict"],
      geometry_virtual_path: null,
    },
    designBrief: null,
    finalReport: null,
  });
  assert.match(model.summaryText, /cavity/);
});
```

- [ ] **Step 2: Run the targeted frontend tests to confirm the current STL-centric assumptions fail**

Run: `node --test "src/components/workspace/submarine-workbench/submarine-session-model.test.ts" "src/components/workspace/submarine-workbench/submarine-visible-actions.test.ts" "src/components/workspace/chats/chat-box.artifacts.test.ts"`
Expected: FAIL because the current models and artifact view still assume geometry-centric runs

- [ ] **Step 3: Update session-model and visible-action builders to describe official-case seeds and completion states correctly**

```ts
const runBasis =
  runtime?.input_source_type === "openfoam_case_seed"
    ? runtime?.official_case_id ?? "official-case"
    : runtime?.geometry_virtual_path ?? designBrief?.geometry_virtual_path ?? "submarine-run";
```

- [ ] **Step 4: Update artifact grouping so imported seeds, assembled case files, and generated report artifacts are visually separable**

```ts
return [
  ...asArtifactList(values.submarine_runtime?.official_case_seed_virtual_paths, "seed"),
  ...asArtifactList(values.submarine_runtime?.assembled_case_virtual_paths, "assembled-case"),
  ...asArtifactList(values.submarine_runtime?.artifact_virtual_paths, "result"),
];
```

The frontend model for this step must preserve three explicit classes:

```ts
type ArtifactClass = "seed" | "assembled-case" | "result";
```

- [ ] **Step 5: Re-run the targeted frontend tests and lint/typecheck**

Run: `node --test "src/components/workspace/submarine-workbench/submarine-session-model.test.ts" "src/components/workspace/submarine-workbench/submarine-visible-actions.test.ts" "src/components/workspace/chats/chat-box.artifacts.test.ts"`
Expected: PASS

Run: `corepack pnpm exec eslint src/components/workspace/submarine-workbench/submarine-session-model.ts src/components/workspace/submarine-workbench/submarine-session-model.test.ts src/components/workspace/submarine-workbench/submarine-visible-actions.ts src/components/workspace/submarine-workbench/submarine-visible-actions.test.ts src/components/workspace/chats/chat-box.artifacts.ts src/components/workspace/chats/chat-box.artifacts.test.ts src/core/threads/utils.ts`
Expected: PASS

Run: `corepack pnpm exec tsc --noEmit`
Expected: PASS

### Task 5: Validate The Real Frontend Product Flow With Official Seeds

**Type:** Exploratory

**Files:**
- Notes: `docs/superpowers/session-status/2026-04-17-openfoam-official-case-seed-import-status.md`
- Create: `backend/tests/fixtures/openfoam_case_seeds/cavity/system/blockMeshDict`
- Create: `backend/tests/fixtures/openfoam_case_seeds/pitzDaily/pitzDaily.blockMeshDict`
- Test: `backend/tests/test_openfoam_case_seed_contracts.py`
- Test: `backend/tests/test_openfoam_case_seed_resolver.py`
- Test: `backend/tests/test_official_case_assembly.py`
- Test: `backend/tests/test_official_case_provenance.py`
- Test: `backend/tests/test_submarine_solver_dispatch_tool.py`
- Test: `backend/tests/test_submarine_result_report_tool.py`

**Goal:** Prove the feature through the real frontend user path, not only through backend scaffolding.

**Collect Evidence:**
- `cavity` can be uploaded as a seed and run from the frontend chat path with visible files and a truthful report
- `pitzDaily` can be uploaded as a seed and driven from the frontend chat path with correct heavy-case status labeling
- the generated reports distinguish imported official seeds from synthesized/overridden files

**Stop and Replan If:**
- the frontend cannot route the upload + chat path into the official-case branch without manual backend intervention
- the `pitzDaily` runtime truth cannot be represented without misleading the user about completion state

**Checkpoint If:**
- both official-case product tests have complete evidence captured in runtime artifacts and the session status file

- [ ] **Step 1: Run the full targeted backend/frontend automated verification suite**

Run: `uv run --project backend pytest backend/tests/test_openfoam_case_seed_contracts.py backend/tests/test_openfoam_case_seed_resolver.py backend/tests/test_official_case_assembly.py backend/tests/test_official_case_provenance.py backend/tests/test_submarine_solver_dispatch_tool.py backend/tests/test_submarine_result_report_tool.py -q`
Expected: PASS

Run: `node --test "src/components/workspace/submarine-workbench/submarine-session-model.test.ts" "src/components/workspace/submarine-workbench/submarine-visible-actions.test.ts" "src/components/workspace/chats/chat-box.artifacts.test.ts"`
Expected: PASS

- [ ] **Step 2: Prepare the exact upload source files used for the frontend product flow**

Procedure:

```text
1. Use the pinned minimal fixtures created in Task 2 as the upload source of truth.
2. If a manual browser upload requires copies outside the repo, copy only those minimal fixture files into a temporary user-visible folder.
3. Do not use full tutorial bundles or hand-edited case folders for product validation.
```

- [ ] **Step 3: Execute the real frontend `cavity` product flow**

Procedure:

```text
1. Upload the minimal `cavity` seed file through the normal attachment flow.
2. In chat, request an official-default run.
3. Let the main agent assemble and run the case.
4. Capture screenshots / artifacts showing process, files, and report.
```

- [ ] **Step 4: Execute the real frontend `pitzDaily` product flow**

Procedure:

```text
1. Upload the minimal `pitzDaily` seed file through the normal attachment flow.
2. In chat, request an official-default run.
3. Let the main agent assemble and run the case.
4. Verify the UI/report labels the result as `completed` or `partial-but-valid-product-flow` truthfully.
```

- [ ] **Step 5: Record the final verified state and any remaining edge risks in the companion session status file**

Run: `git status --short`
Expected: the tracked slice files are identifiable and any temporary downloaded tutorial bundles are either removed or explicitly retained as minimal fixtures only
