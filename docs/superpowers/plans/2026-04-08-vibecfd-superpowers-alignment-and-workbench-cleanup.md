# VibeCFD Superpowers Alignment And Workbench Cleanup Implementation Plan

> **For agentic workers:** If you are starting from a fresh session, use superpowers:resuming-work first. Then use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Respect the `Prior Art Survey`, `Reuse Strategy`, `Session Status File`, `Primary Context Files`, `Artifact Lifecycle`, `Workspace Strategy`, `Validation Strategy`, `Review Cadence`, `Checkpoint Strategy`, `Uncertainty Hotspots`, and `Replan Triggers` fields below while executing.

**Goal:** Align the active VibeCFD branch with current superpowers guidance by converting submarine orchestration back to guidance-first language, removing remaining stage-first frontend entrypoint dependencies, and leaving behind a resumable handoff.

**Architecture:** Adapt the existing lead-agent-first/backend workbench implementation instead of rewriting it. Keep the current Chinese workbench foundation, tighten only the backend prompt/skill wording and the `submarine` route wiring that still leaks legacy pipeline pieces, then verify the focused regression surface end-to-end.

**Tech Stack:** Python 3.12 + pytest/uv workspace, DeerFlow harness prompts and skills, Next.js 16, React 19, TypeScript, Node 24 `node:test`

**Prior Art Survey:** none needed - local alignment and cleanup task inside the existing repo

**Reuse Strategy:** adapt existing project

**Session Status File:** `docs/superpowers/session-status/2026-04-08-vibecfd-superpowers-alignment-and-workbench-cleanup-status.md`

**Primary Context Files:**
- `README.md`
- `docs/superpowers/specs/2026-04-05-vibecfd-lead-agent-first-design.md`
- `docs/superpowers/specs/2026-04-06-vibecfd-agentic-workbench-frontend-design.md`

**Artifact Lifecycle:** Keep this plan and its companion status file as the active handoff for this cleanup. Keep the 2026-04-05 and 2026-04-06 design specs as durable context. Superseded older plan files may be deleted once newer 2026-04-08 plans/status files cover the active execution path. Replace legacy `submarine` route usage of `SubmarinePipelineChatRail` with a workbench-local negotiation surface if the route cleanup lands. Delete stale barrel exports or dead stage-first entrypoint references only when targeted verification proves nothing still imports them.

**Workspace Strategy:** branch in current workspace

**Validation Strategy:** strict tdd

**Review Cadence:** each milestone

**Checkpoint Strategy:** user-directed checkpoints

**Uncertainty Hotspots:** The `submarine` route may still depend on helper types or props hidden inside the old pipeline chat rail; removing that dependency may expose a second cleanup seam. Backend prompt wording changes may need to preserve current safety guarantees while dropping mandatory-flow phrasing.

**Replan Triggers:** Pause and revise the plan if route cleanup requires a broader `submarine-pipeline` component breakup than this task assumes, if prompt wording changes invalidate existing runtime/safety tests beyond the targeted guidance-first failures, or if unrelated dirty-worktree edits appear in the touched frontend/backend files.

---

## File Structure Map

- Modify: `backend/tests/test_submarine_subagents.py`
  Keep the new regression assertions that define the desired guidance-first behavior.
- Modify: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
  Reword submarine workflow instructions so they preserve safety gates without sounding like a fixed mandatory stage protocol.
- Modify: `skills/public/submarine-orchestrator/SKILL.md`
  Reframe orchestration guidance around primary-agent judgment instead of fixed tool order.
- Modify: `frontend/src/app/workspace/submarine/[thread_id]/page.test.ts`
  Add a route-level guard that fails while the thread page still imports the legacy pipeline chat rail.
- Modify: `frontend/src/app/workspace/submarine/[thread_id]/page.tsx`
  Swap the old pipeline chat rail dependency for a route-local negotiation surface built on the new workbench primitives.
- Modify: `frontend/src/components/workspace/agentic-workbench/index.ts`
  Stop exporting stale stage-first helpers once route-level imports no longer need them.

## Task 1: Lock The Guidance-First Backend Contract

**Files:**
- Modify: `backend/tests/test_submarine_subagents.py`
- Modify: `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- Modify: `skills/public/submarine-orchestrator/SKILL.md`

- [x] **Step 1: Keep the failing regressions focused on guidance-first wording**

```python
def test_submarine_workflow_prompt_section_is_guidance_first_not_stage_mandatory():
    section = prompt_module.get_submarine_workflow_prompt_section()

    assert "primary agent" in section.lower()
    assert "recommended" in section.lower()
    assert "follow this protocol strictly" not in section.lower()
    assert "always capture or refresh the structured plan" not in section.lower()
```

```python
def test_submarine_orchestrator_skill_guides_judgment_without_fixed_tool_order():
    content = skill_path.read_text(encoding="utf-8")

    assert "when the primary agent should" in content.lower()
    assert "use the built-in tools in this order" not in content.lower()
    assert "required orchestration path" not in content.lower()
```

- [x] **Step 2: Run the backend regression file to confirm the starting failure**

Run: `uv run pytest tests/test_submarine_subagents.py`
Expected: FAIL in exactly the two guidance-first assertions above.

- [x] **Step 3: Reword the lead-agent submarine workflow section without weakening safety gates**

```python
return """<submarine_workflow_protocol>
For submarine CFD requests involving uploaded geometry, OpenFOAM execution, resistance/wake/pressure analysis, or research-grade result delivery, the primary agent should treat the following sequence as the recommended DeerFlow-native path:

1. Start by capturing or refreshing `submarine_design_brief` so the current objective, operating conditions, requested outputs, verification expectations, constraints, and open questions are explicit.
2. Present the brief-backed calculation plan to the user instead of answering submarine CFD requests from generic reasoning alone.
3. If operating conditions, deliverables, comparison targets, or verification requirements are still unresolved, call `ask_clarification` and stop there.
4. Continue to `submarine_geometry_check` and `submarine_solver_dispatch` only after the user has explicitly confirmed the current plan.
5. Keep execution aligned with the confirmed brief instead of inventing a different path mid-run.
6. Use `submarine_result_report` only after preflight or solver artifacts exist and the report can be grounded in DeerFlow evidence.
</submarine_workflow_protocol>"""
```

- [x] **Step 4: Reword the public orchestrator skill around judgment and delegation choices**

```md
## Guidance For The Primary Agent

When the primary agent should coordinate a real submarine CFD run, prefer the specialized DeerFlow subagents over generic delegation:

- `submarine-task-intelligence`
- `submarine-geometry-preflight`
- `submarine-solver-dispatch`
- `submarine-result-reporting`

The usual DeerFlow-native path is:

1. capture or refresh `submarine_design_brief`
2. run `submarine_geometry_check` when the brief is concrete enough
3. use `submarine_solver_dispatch` when execution is approved
4. hand off artifact-backed synthesis to `submarine-result-reporting`
```

- [x] **Step 5: Re-run the backend regression file**

Run: `uv run pytest tests/test_submarine_subagents.py`
Expected: PASS

## Task 2: Remove The Remaining Legacy `submarine` Route Dependency

**Files:**
- Modify: `frontend/src/app/workspace/submarine/[thread_id]/page.test.ts`
- Modify: `frontend/src/app/workspace/submarine/[thread_id]/page.tsx`
- Modify: `frontend/src/components/workspace/agentic-workbench/index.ts`

- [x] **Step 1: Add a failing route-level regression for the old chat rail import**

```ts
void test("submarine route no longer imports the legacy pipeline chat rail", () => {
  assert.doesNotMatch(pageSource, /SubmarinePipelineChatRail/);
});
```

- [x] **Step 2: Run the route test to verify the current failure**

Run:
`Push-Location -LiteralPath 'frontend/src/app/workspace/submarine/[thread_id]'; node --test page.test.ts; Pop-Location`

Expected: FAIL because `page.tsx` still imports and renders `SubmarinePipelineChatRail`.

- [x] **Step 3: Replace the route-level negotiation body with a workbench-local surface**

```tsx
function SubmarineNegotiationRailBody(...) {
  return (
    <div id="submarine-chat-rail" className="flex h-full min-h-0 flex-col overflow-hidden rounded-[24px] border border-slate-200/80 bg-white/96">
      <div className="border-b border-slate-200/70 px-4 py-3">
        <div className="text-sm font-semibold text-slate-900">主智能体协商线程</div>
        <div className="mt-1 text-xs leading-5 text-slate-500">
          在这里补充约束、追问结果、要求改方案，主画布保持研究推进视图。
        </div>
      </div>
      <div className="min-h-0 flex-1">
        <ChatRail ... />
      </div>
    </div>
  );
}
```

Keep the existing `ChatBox`, `useThreadStream`, stop handling, and context wiring intact; only remove the dependency on `@/components/workspace/submarine-pipeline`.

- [x] **Step 4: Drop stale barrel exports that should no longer be part of the active workbench surface**

```ts
export * from "./narrative-stream";
export * from "./negotiation-rail";
export * from "./secondary-layer-host";
export * from "./session-summary-bar";
export * from "./thread-header";
export * from "./workbench-copy";
export * from "./workbench-flow";
export * from "./workbench-shell";
export * from "./workbench-shell.contract";
```

- [x] **Step 5: Re-run the route-level and workbench contract tests**

Run:
`Push-Location -LiteralPath 'frontend/src/app/workspace/submarine/[thread_id]'; node --test page.test.ts; Pop-Location`

Run:
`Push-Location 'frontend/src/components/workspace/agentic-workbench'; node --test workbench-shell.contract.test.ts workbench-copy.test.ts workbench-flow.contract.test.ts; Pop-Location`

Expected: PASS

## Task 3: Verify, Reconcile Artifact Hygiene, And Update The Handoff

**Files:**
- Modify: `docs/superpowers/session-status/2026-04-08-vibecfd-superpowers-alignment-and-workbench-cleanup-status.md`

- [x] **Step 1: Run the focused full verification set for this cleanup**

Run:
`uv run pytest tests/test_submarine_subagents.py`

Run:
`Push-Location -LiteralPath 'frontend/src/app/workspace/submarine/[thread_id]'; node --test page.test.ts; Pop-Location`

Run:
`Push-Location 'frontend/src/components/workspace/agentic-workbench'; node --test workbench-shell.contract.test.ts workbench-copy.test.ts workbench-flow.contract.test.ts; Pop-Location`

Run:
`Push-Location 'frontend/src/components/workspace/submarine-workbench'; node --test index.contract.test.ts submarine-session-model.test.ts submarine-detail-model.test.ts; Pop-Location`

Expected: PASS across all commands.

- [x] **Step 2: Review stale artifacts and code paths created or superseded by this work**

Check:
- whether `frontend/src/components/workspace/agentic-workbench/interrupt-action-bar.tsx` still has any active imports
- whether `frontend/src/components/workspace/submarine-pipeline.tsx` remains in the runtime path after route cleanup
- whether the older 2026-04-06 frontend rebuild plan should remain reference-only instead of active execution guidance

Record each item in the session status file as keep, delete, or replace-next.

- [x] **Step 3: Refresh the session status handoff**

Update the companion status file with:
- completed task numbers
- current verified commands
- any still-open cleanup paths
- exact next recommended step if this work stops before broader legacy retirement
