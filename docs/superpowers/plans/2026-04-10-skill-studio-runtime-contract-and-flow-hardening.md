# Skill Studio Runtime Contract And Flow Hardening Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then choose the execution skill that fits the work: use superpowers:subagent-driven-development when delegation benefits outweigh the round-trip, or superpowers:executing-plans when the work is better kept local. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the plan controls below, especially reuse, continuity, artifact lifecycle, validation/review cadence, and any research-overlay constraints.

**Goal:** Make the Skill Studio mainline reliably complete the chain `draft -> dry-run evidence -> publish gate -> runtime refresh -> future-thread visibility` without a repo-wide cleanup.

**Architecture:** Reuse the current DeerFlow Skill Studio, gateway, and lead-agent stack. Persist explicit dry-run evidence beside draft artifacts, make backend publish read that evidence from the packaged archive, add a monotonic lifecycle `runtime_revision`, and bind new-thread skill visibility to a persisted `skill_runtime_snapshot` instead of the current process-local cache alone.

**Tech Stack:** FastAPI gateway, Pydantic models, LangChain/LangGraph agent middleware, pytest, Next.js App Router, React Query, Node test runner.

**Prior Art Survey:** none needed - local DeerFlow/VibeCFD contract hardening task

**Reuse Strategy:** adapt existing project

**Session Status File:** `docs/superpowers/session-status/2026-04-10-skill-studio-runtime-contract-and-flow-hardening-status.md`

**Context Summary:** `docs/superpowers/context-summaries/2026-04-10-skill-studio-runtime-contract-and-flow-hardening-summary.md`

**Primary Context Files:** `docs/superpowers/specs/2026-04-10-skill-studio-runtime-contract-and-flow-hardening-design.md`, `docs/superpowers/session-status/2026-04-08-vibecfd-runtime-flow-security-first-pass-status.md`, `docs/superpowers/session-status/2026-04-08-vibecfd-superpowers-alignment-and-workbench-cleanup-status.md`, `docs/superpowers/session-status/2026-04-08-vibecfd-legacy-workspace-retirement-status.md`, `backend/packages/harness/deerflow/domain/submarine/skill_studio.py`, `backend/packages/harness/deerflow/domain/submarine/skill_lifecycle.py`, `backend/app/gateway/routers/skills.py`, `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`, `backend/packages/harness/deerflow/agents/lead_agent/agent.py`, `backend/packages/harness/deerflow/agents/thread_state.py`, `frontend/src/components/workspace/skill-studio-workbench/index.tsx`, `frontend/src/components/workspace/skill-studio-workbench/skill-studio-lifecycle-canvas.tsx`, `frontend/src/components/workspace/skill-studio-workbench/skill-studio-testing-evidence.tsx`, `frontend/src/core/skills/api.ts`, `frontend/src/core/skills/hooks.ts`

**Artifact Lifecycle:** Keep this plan, the companion session status file, the context summary, the approved design spec, and new focused regression tests for dry-run evidence, publish gating, runtime revision invalidation, and thread snapshot boundaries. Replace the implicit "ready_for_dry_run means publishable" contract with explicit `dry-run-evidence.json` artifacts and backend publish enforcement. Replace cache-only future-skill visibility with `runtime_revision` plus persisted `skill_runtime_snapshot`. Keep `legacy/current-prototype/` as reference-only material; do not open a broad cleanup pass. Do not keep scratch scripts or one-off archive inspection helpers after the tests cover the same behavior.

**Workspace Strategy:** current workspace

**Validation Strategy:** mixed

**Review Cadence:** each milestone

**Checkpoint Strategy:** user-directed checkpoints

**Research Overlay:** disabled

**Research Mainline:** none

**Non-Negotiables:** none

**Forbidden Regressions:** none

**Method Fidelity Checks:** none

**Scale Gate:** none

**Decision Log:** none - record durable decisions in session status and linked findings docs

**Research Findings:** none

**Uncertainty Hotspots:** whether the current LangChain agent wiring should capture snapshot-specific skills by overriding `ModelRequest.system_message` in middleware rather than rebuilding the whole agent graph; whether the `.skill` packaging path already preserves arbitrary JSON artifacts when rebuilt after dry-run evidence updates; whether the current frontend artifact cache invalidation is sufficient after writing updated draft artifacts from a mutation instead of a tool run.

**Replan Triggers:** if the checkpointer cannot persist a new `skill_runtime_snapshot` field cleanly; if `ModelRequest` middleware cannot safely swap the skills section without breaking existing system-prompt behavior; if the draft-evidence writer cannot rebuild the archive and publish-readiness artifacts from the existing thread outputs in a deterministic way.

---

### Task 1: Persist Dry-Run Evidence In Skill Studio Draft Outputs

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/skill_studio.py`
- Modify: `backend/packages/harness/deerflow/tools/builtins/submarine_skill_studio_tool.py`
- Modify: `backend/packages/harness/deerflow/agents/thread_state.py`
- Modify: `backend/tests/test_submarine_skill_studio_tool.py`

- [x] **Step 1: Add failing tests for the new draft artifact and state fields**

```python
assert any(path.endswith("/dry-run-evidence.json") for path in artifacts)

dry_run_evidence = json.loads(
    (draft_dir / "dry-run-evidence.json").read_text(encoding="utf-8")
)
assert dry_run_evidence["status"] == "not_recorded"
assert dry_run_evidence["thread_id"] == thread_id
assert dry_run_evidence["scenario_id"] is None

studio_state = result.update["submarine_skill_studio"]
assert studio_state["dry_run_evidence_status"] == "not_recorded"
assert studio_state["dry_run_evidence_virtual_path"].endswith(
    "/dry-run-evidence.json"
)
```

- [x] **Step 2: Run the focused Skill Studio artifact test to confirm the current gap**

Run: `uv run pytest tests/test_submarine_skill_studio_tool.py`
Expected: FAIL because `run_skill_studio()` does not currently create or surface `dry-run-evidence.json`.

- [x] **Step 3: Write the draft-evidence scaffold and include it in the packaged archive**

```python
def _build_dry_run_evidence(*, skill_slug: str, source_thread_id: str | None) -> dict:
    return {
        "skill_name": skill_slug,
        "status": "not_recorded",
        "recorded_at": None,
        "recorded_by": None,
        "thread_id": source_thread_id,
        "scenario_id": None,
        "message_ids": [],
        "reviewer_note": "",
    }
```

```python
artifact_virtual_paths = [
    ...
    _artifact_virtual_path(skill_slug, "dry-run-evidence.json"),
    ...
]

(draft_dir / "dry-run-evidence.json").write_text(
    json.dumps(dry_run_evidence, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
```

```python
package_files = [
    draft_dir / "SKILL.md",
    draft_dir / "agents" / "openai.yaml",
    draft_dir / "dry-run-evidence.json",
]
```

Thread state should expose:
- `dry_run_evidence_status`
- `dry_run_evidence_virtual_path`

- [x] **Step 4: Re-run the focused Skill Studio artifact test**

Run: `uv run pytest tests/test_submarine_skill_studio_tool.py`
Expected: PASS

- [x] **Step 5: Checkpoint according to `Checkpoint Strategy`**

Update the session status file with the new draft artifact contract and note that the artifact is present but not yet writable from the UI until Task 2 lands.

### Task 2: Add A Dedicated Dry-Run Evidence Recording Path And Backend Publish Gate

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/skill_studio.py`
- Modify: `backend/app/gateway/routers/skills.py`
- Modify: `backend/tests/test_skills_publish_router.py`
- Modify: `backend/tests/test_skills_router.py`
- Modify: `frontend/src/core/skills/api.ts`
- Modify: `frontend/src/core/skills/hooks.ts`
- Modify: `frontend/src/components/workspace/skill-studio-workbench/index.tsx`
- Modify: `frontend/src/components/workspace/skill-studio-workbench/skill-studio-detail-model.ts`
- Modify: `frontend/src/components/workspace/skill-studio-workbench/skill-studio-detail-model.test.ts`
- Modify: `frontend/src/components/workspace/skill-studio-workbench/skill-studio-lifecycle-canvas.tsx`
- Modify: `frontend/src/components/workspace/skill-studio-workbench/skill-studio-lifecycle-canvas.contract.test.ts`
- Modify: `frontend/src/components/workspace/skill-studio-workbench/skill-studio-testing-evidence.tsx`

- [x] **Step 1: Add failing backend tests that prove publish is still bypassable**

```python
blocked = client.post(
    "/api/skills/publish",
    json={
        "thread_id": "thread-1",
        "path": archive_virtual_path,
        "overwrite": False,
        "enable": True,
        "version_note": "",
        "binding_targets": [],
    },
)
assert blocked.status_code == 400
assert "dry-run evidence" in blocked.json()["detail"]
```

```python
recorded = client.post(
    "/api/skills/dry-run-evidence",
    json={
        "thread_id": "thread-1",
        "path": draft_virtual_path,
        "status": "passed",
        "scenario_id": "scenario-1",
        "message_ids": ["msg-1", "msg-2"],
        "reviewer_note": "Dry run matches the expected acceptance rubric.",
    },
)
assert recorded.status_code == 200
```

- [x] **Step 2: Add failing frontend contract coverage for the missing evidence action**

```ts
assert.match(source, /onRecordDryRunPassed/);
assert.match(source, /onRecordDryRunFailed/);
assert.match(source, /记录试跑通过|记录试跑失败/);
```

- [x] **Step 3: Run the focused backend and frontend tests to capture the starting failures**

Run: `uv run pytest tests/test_skills_publish_router.py tests/test_skills_router.py`
Expected: FAIL because publish still succeeds without a recorded dry run and no evidence-recording route exists.

Run: `node --test frontend/src/components/workspace/skill-studio-workbench/skill-studio-detail-model.test.ts frontend/src/components/workspace/skill-studio-workbench/skill-studio-lifecycle-canvas.contract.test.ts`
Expected: FAIL because the testing panel has no mutation path for recording dry-run results.

- [x] **Step 4: Implement a dedicated dry-run evidence writer that refreshes draft artifacts and the packaged archive**

```python
class SkillDryRunEvidenceRequest(BaseModel):
    thread_id: str
    path: str
    status: Literal["passed", "failed"]
    scenario_id: str | None = None
    message_ids: list[str] = Field(default_factory=list)
    reviewer_note: str = ""
```

```python
evidence_payload = {
    **existing_evidence,
    "status": request.status,
    "recorded_at": utc_timestamp(),
    "recorded_by": "skill-studio-ui",
    "scenario_id": request.scenario_id,
    "message_ids": request.message_ids,
    "reviewer_note": request.reviewer_note,
}
```

```python
if dry_run_evidence.get("status") != "passed":
    raise HTTPException(
        status_code=400,
        detail="Publish blocked: dry-run evidence is missing or has not passed.",
    )
```

Implementation notes:
- The record-evidence route should resolve the draft directory from the thread-local virtual path.
- After writing `dry-run-evidence.json`, rebuild `publish-readiness.json`, `publish-readiness.md`, and the `.skill` archive so publish reads a self-contained package.
- The publish route must read the extracted archive copy of `dry-run-evidence.json`, not the live thread directory.
- Keep `validation_status`, `test_status`, and `publish_status` compatible for existing UI paths; derive the gate result from explicit evidence instead of overloading `test_status`.

- [x] **Step 5: Add the smallest frontend mutation surface that can close the loop**

```ts
export interface RecordDryRunEvidenceRequest {
  thread_id: string;
  path: string;
  status: "passed" | "failed";
  scenario_id?: string;
  message_ids?: string[];
  reviewer_note?: string;
}
```

```ts
const recordDryRun = useCallback(async (status: "passed" | "failed") => {
  if (!draftPath) return;
  await recordDryRunEvidenceMutation.mutateAsync({
    thread_id: threadId,
    path: draftPath,
    status,
    scenario_id: detail.evaluate.scenarioMatrix.scenarios[0]?.id,
    reviewer_note: versionNote,
  });
}, [detail.evaluate.scenarioMatrix.scenarios, draftPath, recordDryRunEvidenceMutation, threadId, versionNote]);
```

The mutation should invalidate:
- `["artifact", draftPath, threadId, isMock]`
- the known `publish-readiness` artifact query key
- `["skills", "lifecycle"]`

- [x] **Step 6: Re-run the focused backend and frontend tests**

Run: `uv run pytest tests/test_skills_publish_router.py tests/test_skills_router.py`
Expected: PASS

Run: `node --test frontend/src/components/workspace/skill-studio-workbench/skill-studio-detail-model.test.ts frontend/src/components/workspace/skill-studio-workbench/skill-studio-lifecycle-canvas.contract.test.ts`
Expected: PASS

- [x] **Step 7: Checkpoint according to `Checkpoint Strategy`**

Ask the reviewer subagent to inspect the evidence-writing and publish-gate slice before continuing to runtime invalidation.

### Task 3: Make Lifecycle `runtime_revision` The Explicit Runtime Refresh Signal

**Files:**
- Modify: `backend/packages/harness/deerflow/domain/submarine/skill_lifecycle.py`
- Modify: `backend/app/gateway/routers/skills.py`
- Modify: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- Modify: `backend/tests/test_skill_lifecycle_store.py`
- Modify: `backend/tests/test_lead_agent_prompt_skill_routing.py`

- [x] **Step 1: Add failing tests for lifecycle revision ownership and prompt invalidation**

```python
registry = SkillLifecycleRegistry(runtime_revision=3, records={})
written_path = save_skill_lifecycle_registry(registry, registry_path=registry_path)
loaded_registry = load_skill_lifecycle_registry(registry_path=written_path)
assert loaded_registry.runtime_revision == 3
```

```python
before = prompt_module._get_enabled_skills_snapshot_source_state()
registry_path.write_text(
    json.dumps({"version": "1.0", "runtime_revision": 2, "records": {}}, indent=2),
    encoding="utf-8",
)
after = prompt_module._get_enabled_skills_snapshot_source_state()
assert after != before
```

- [x] **Step 2: Run the focused runtime invalidation tests**

Run: `uv run pytest tests/test_skill_lifecycle_store.py tests/test_lead_agent_prompt_skill_routing.py`
Expected: FAIL because the registry currently has no `runtime_revision` and prompt invalidation only watches file mtimes.

- [x] **Step 3: Implement the monotonic runtime revision helpers and wire them into every lifecycle mutation**

```python
class SkillLifecycleRegistry(BaseModel):
    version: str = "1.0"
    runtime_revision: int = 0
    records: dict[str, SkillLifecycleRecord] = Field(default_factory=dict)
```

```python
def bump_skill_runtime_revision(registry: SkillLifecycleRegistry) -> SkillLifecycleRegistry:
    registry.runtime_revision += 1
    return registry
```

Every mutation path in `skills.py` should call the helper exactly once after the state change succeeds:
- publish
- rollback
- lifecycle update
- generic enable/disable for custom skills

Prompt invalidation should include:

```python
registry = load_skill_lifecycle_registry()
registry_state = (
    str(get_skill_lifecycle_registry_path()),
    registry.runtime_revision,
    get_skill_lifecycle_registry_path().stat().st_mtime if get_skill_lifecycle_registry_path().exists() else None,
)

return (
    existing_extensions_config_state,
    existing_skill_file_watch_state,
    registry_state,
)
```

Do not replace the current `extensions_config.json` and skill-file mtime invalidation inputs. `runtime_revision` is an additional explicit refresh signal, not a substitute for direct filesystem-change detection.

- [x] **Step 4: Re-run the focused runtime invalidation tests**

Run: `uv run pytest tests/test_skill_lifecycle_store.py tests/test_lead_agent_prompt_skill_routing.py`
Expected: PASS

- [x] **Step 5: Checkpoint according to `Checkpoint Strategy`**

Record the exact mutation paths that now own `runtime_revision` so later sessions do not reintroduce hidden owners.

### Task 4: Persist `skill_runtime_snapshot` And Enforce The Old-Thread/New-Thread Boundary

**Files:**
- Modify: `backend/packages/harness/deerflow/agents/thread_state.py`
- Create: `backend/packages/harness/deerflow/agents/middlewares/skill_runtime_snapshot_middleware.py`
- Modify: `backend/packages/harness/deerflow/agents/lead_agent/agent.py`
- Modify: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- Modify: `backend/tests/test_thread_state_reducers.py`
- Create: `backend/tests/test_skill_runtime_snapshot_middleware.py`

- [x] **Step 1: Add failing reducer and middleware tests for snapshot persistence**

```python
result = graph.compile().invoke(
    {
        "messages": [],
        "skill_runtime_snapshot": {
            "runtime_revision": 4,
            "captured_at": "2026-04-10T08:00:00Z",
            "enabled_skill_names": ["submarine-result-acceptance"],
            "binding_targets_applied": ["scientific-verification"],
            "source_registry_path": "skills/custom/.skill-studio-registry.json",
        },
    }
)
assert result["skill_runtime_snapshot"]["runtime_revision"] == 4
```

```python
request = middleware._override_skill_snapshot(
    request_with_revision(5),
    {
        "runtime_revision": 3,
        "enabled_skill_names": ["cached-skill"],
        "binding_targets_applied": ["result-reporting"],
    },
)
assert "cached-skill" in request.system_prompt
assert "fresh-skill" not in request.system_prompt
```

- [x] **Step 2: Run the focused snapshot-boundary tests**

Run: `uv run pytest tests/test_thread_state_reducers.py tests/test_skill_runtime_snapshot_middleware.py`
Expected: FAIL because `ThreadState` has no `skill_runtime_snapshot` field and no middleware currently rewrites prompt skills from persisted state.

- [x] **Step 3: Add the persisted snapshot schema and middleware capture path**

```python
class SkillRuntimeSnapshotState(TypedDict):
    runtime_revision: int
    captured_at: str
    enabled_skill_names: list[str]
    binding_targets_applied: list[str]
    source_registry_path: str
```

```python
class SkillRuntimeSnapshotMiddleware(AgentMiddleware[ThreadState]):
    def before_model(self, state: ThreadState, runtime: Runtime) -> dict | None:
        if state.get("skill_runtime_snapshot"):
            return None
        return {"skill_runtime_snapshot": capture_skill_runtime_snapshot()}
```

```python
def wrap_model_call(self, request: ModelRequest, handler):
    snapshot = request.state.get("skill_runtime_snapshot")
    if snapshot:
        request = request.override(
            system_message=SystemMessage(
                content=apply_prompt_template(
                    ...,
                    skill_snapshot=snapshot,
                )
            )
        )
    return handler(request)
```

The snapshot capture function should:
- resolve the current `runtime_revision`
- freeze the enabled skill list for the thread
- freeze the explicit binding targets actually applied

- [x] **Step 4: Re-run the focused snapshot-boundary tests**

Run: `uv run pytest tests/test_thread_state_reducers.py tests/test_skill_runtime_snapshot_middleware.py`
Expected: PASS

- [x] **Step 5: Extend the prompt tests to prove old threads stay pinned after a later publish**

```python
snapshot = {
    "runtime_revision": 1,
    "enabled_skill_names": ["submarine-result-acceptance"],
    "binding_targets_applied": ["scientific-verification"],
    "source_registry_path": str(registry_path),
}
request = middleware._override_skill_snapshot(
    request_with_revision(2, live_skills=["newer-skill"]),
    snapshot,
)
assert "submarine-result-acceptance" in request.system_prompt
assert "newer-skill" not in request.system_prompt
```

- [x] **Step 6: Checkpoint according to `Checkpoint Strategy`**

Ask the reviewer subagent to inspect the snapshot middleware and prompt-rewrite slice before running the broader verification set.

### Task 5: Run The Proof-Oriented Verification Slice And Refresh The Durable Handoff

**Type:** Exploratory

**Files:**
- Create: `backend/tests/test_skill_studio_runtime_flow_e2e.py`
- Modify: `docs/superpowers/session-status/2026-04-10-skill-studio-runtime-contract-and-flow-hardening-status.md`
- Modify: `docs/superpowers/context-summaries/2026-04-10-skill-studio-runtime-contract-and-flow-hardening-summary.md`

**Goal:** Prove the full contract works from draft output through publish and new-thread skill visibility, then leave behind an accurate durable handoff.

**Collect Evidence:**
- publish is blocked without recorded dry-run evidence even when called directly against the backend
- recording passing evidence rebuilds the archive and allows publish
- publish/update/rollback bump `runtime_revision`
- a thread with a persisted snapshot keeps the old revision after a later publish
- the Skill Studio canvas can record evidence and then publish without manual filesystem edits

**Stop and Replan If:**
- the prompt override path cannot keep the snapshot-specific skills/bindings stable across model calls
- the evidence-recording route cannot reliably invalidate artifact content and the UI still reads stale draft files

**Checkpoint If:**
- the focused test suite is green and the durable status/context summary describe the verified chain accurately

- [x] **Step 1: Add the proof-oriented end-to-end backend harness**

```python
def test_skill_studio_runtime_flow_end_to_end(tmp_path: Path, monkeypatch) -> None:
    draft = build_skill_studio_draft(tmp_path, thread_id="thread-old")
    blocked = publish_without_dry_run(draft.archive_virtual_path)
    assert blocked.status_code == 400

    evidence = record_dry_run(
        thread_id="thread-old",
        path=draft.draft_virtual_path,
        status="passed",
        scenario_id="scenario-1",
        message_ids=["msg-1"],
    )
    assert evidence.status_code == 200

    published = publish_with_dry_run(draft.archive_virtual_path)
    assert published.status_code == 200

    old_snapshot = capture_skill_runtime_snapshot(runtime_revision=1)
    publish_new_revision(...)
    new_snapshot = capture_skill_runtime_snapshot(runtime_revision=2)

    assert old_snapshot["runtime_revision"] == 1
    assert new_snapshot["runtime_revision"] == 2
    assert old_snapshot["enabled_skill_names"] != []
```

The harness should execute the full chain in one test module:
- generate a real Skill Studio draft
- prove publish is blocked before evidence
- record passing evidence and rebuild the archive
- publish successfully
- capture one "old thread" snapshot before the next publish
- publish a second revision and capture a "new thread" snapshot
- assert the older snapshot stays pinned while the newer snapshot advances

- [x] **Step 2: Run the backend regression suite for the touched chain**

Run: `uv run pytest tests/test_submarine_skill_studio_tool.py tests/test_skills_publish_router.py tests/test_skills_router.py tests/test_skill_lifecycle_store.py tests/test_lead_agent_prompt_skill_routing.py tests/test_thread_state_reducers.py tests/test_skill_runtime_snapshot_middleware.py tests/test_skill_studio_runtime_flow_e2e.py`
Expected: PASS

- [x] **Step 3: Run the frontend regression slice for the touched Skill Studio surface**

Run: `node --test frontend/src/components/workspace/skill-studio-workbench/index.contract.test.ts frontend/src/components/workspace/skill-studio-workbench/skill-studio-detail-model.test.ts frontend/src/components/workspace/skill-studio-workbench/skill-studio-lifecycle-canvas.contract.test.ts`
Expected: PASS

- [x] **Step 4: Run lint or typecheck only if one of the touched files participates in those pipelines**

Run: `corepack pnpm --dir frontend exec tsc --noEmit`
Expected: PASS

Run: `corepack pnpm --dir frontend exec eslint src/components/workspace/skill-studio-workbench/index.tsx src/components/workspace/skill-studio-workbench/skill-studio-detail-model.ts src/components/workspace/skill-studio-workbench/skill-studio-lifecycle-canvas.tsx src/components/workspace/skill-studio-workbench/skill-studio-testing-evidence.tsx src/core/skills/api.ts src/core/skills/hooks.ts --ext .ts,.tsx`
Expected: PASS

- [x] **Step 5: Update the session status file with verified state, remaining risks, and the exact next recommendation**
- [x] **Step 6: Refresh the context summary so a new session can re-enter from the compressed map instead of rereading every artifact**
- [x] **Step 7: Decide whether the next pass should stay on this plan or invoke `superpowers:revising-plans`**
