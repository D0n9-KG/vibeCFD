# VibeCFD Iterative Execution Core Session Status

**Status:** in_progress

**Plan:** `docs/superpowers/plans/2026-04-14-vibecfd-iterative-execution-core.md`

**Primary Spec / Brief:** `docs/superpowers/specs/2026-04-14-vibecfd-iterative-execution-core-design.md`

**Prior Art Survey:** `docs/superpowers/prior-art/2026-04-14-vibecfd-iterative-execution-core-survey.md`

**Context Summary:** `docs/superpowers/context-summaries/2026-04-14-vibecfd-iterative-execution-core-summary.md`

**Research Overlay:** disabled

**Research Mainline:** none

**Decision Log:** record durable decisions in this file

**Research Findings:** none

**Last Updated:** 2026-04-15 Asia/Shanghai

**Current Focus:** final cleanup and broad verification on the already-landed iterative-core slice: forced-reload browser checks now re-validate the published Skill Studio thread plus the two recovered submarine threads, and this pass exists to retire the last browser-visible wording leaks before returning to the deeper rerun/output-expansion mainline.

**Next Recommended Step:** The specific browser-visible copy leaks on `9fed37bf-6329-4216-8e32-a2d5ef8b877e`, `01fec432-dead-4cb3-8c2d-09896f4fe832`, and `31075618-e16f-4067-9945-1a8e778458fc` are now retired for this slice. Resume the broader iterative-CFD mainline by proving either a clean output-expansion request or a genuinely improved rerun-oriented follow-up on the submarine side.

**Read This Order On Resume:**
1. This session status file
2. `docs/superpowers/context-summaries/2026-04-14-vibecfd-iterative-execution-core-summary.md`
3. `docs/superpowers/specs/2026-04-14-vibecfd-iterative-execution-core-design.md`
4. `docs/superpowers/plans/2026-04-14-vibecfd-iterative-execution-core.md`
5. `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
6. `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
7. `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
8. `skills/public/submarine-orchestrator/SKILL.md`
9. `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx`
10. `frontend/src/components/workspace/submarine-workbench/submarine-operator-board.tsx`

## Progress Snapshot
- Completed Tasks:
  - external prior-art survey for research-workflow and iterative-CFD patterns
  - deep evaluation of the current product against real researcher task shapes
  - design direction selection: iterative execution core first, not frontend-first polish and not generic workflow-engine drift
  - durable artifact initialization for survey/spec/plan/status/summary
  - backend iterative contract / lineage milestone is landed in the working tree, including `contract_revision`, `lineage_reason`, `requested_output_ids`, and `output_delivery_plan`
  - frontend contract-surfacing milestone is landed: design-brief fallback, contract snapshot, capability gaps, delivery items, and minimal experiment-lineage context are visible in the workbench
  - public submarine skills and the lead-agent prompt now speak the iterative-core vocabulary without introducing a second workflow system
  - confirmation orchestration guidance is explicit: when user confirmation unlocks execution, the agent refreshes `submarine_design_brief` with `confirmation_status="confirmed"` before `submarine_solver_dispatch`
  - the confirmation-flow wording is covered by regression tests in `backend/tests/test_submarine_subagents.py`
  - fresh browser validation proves combined STL + text intake from `/workspace/submarine/new`
  - fresh browser validation proves the visible chain from reference confirmation to refreshed design brief, solver dispatch, solver artifacts, final report, scientific gate, and remediation handoff artifacts
  - the real refresh-only follow-up bug is fixed in `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
  - focused regression coverage for the follow-up / design-brief / report slice is green:
    - `uv run --project backend pytest backend/tests/test_submarine_scientific_followup_tool.py backend/tests/test_submarine_design_brief_tool.py backend/tests/test_submarine_result_report_tool.py -v`
    - result: `67 passed`
  - a fresh browser reload after refresh-only run `019d8b37-20e7-7a80-a020-8a3762f393f2` now shows the real frontend aligned with backend truth: contract `r4`, clean user task text without `<uploaded_files>`, and visible follow-up outcome `result_report_refreshed`
  - reviewer-followup fixes are now landed:
    - common English `do not rerun` / `don't rerun` phrasing is recognized
    - upload-only `<uploaded_files>` turns are ignored instead of overwriting task intent
    - explicit no-rerun refresh can skip solver dispatch even when the structured contract is already in sync
    - short but substantive latest-user follow-up messages now override stale handoff text without relying on a length heuristic
  - GPT-5.4 first-turn submarine routing is now browser-proven on a fresh thread after the prompt hardening in `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`: fresh thread `d773e0e7-4cef-4278-b865-3ee812a190ae` entered `submarine_geometry_check` immediately instead of stopping at `write_todos`
  - the apparent front-end text-drop symptom during validation was narrowed to automation method mismatch rather than a user-facing product defect: keyboard-style input reached the real `runs/stream` request body intact, while browser automation `fill()` did not reliably populate this custom prompt control
  - visible main-canvas next-step buttons are now re-enabled correctly after successful runs:
    - fixed in `frontend/src/core/threads/use-thread-stream.state.ts`
    - covered by a new regression in `frontend/src/core/threads/use-thread-stream.state.test.ts`
    - focused frontend verification is green at `24 passed`
  - incomplete solver reruns are now classified more honestly:
    - `Time = 0s ... End` without residual progression is no longer treated as a completed solver run
    - fixed in `backend/packages/harness/deerflow/domain/submarine/solver_dispatch_results.py`
    - covered by a new regression in `backend/tests/test_submarine_solver_dispatch_tool.py`
    - focused backend verification is green at `98 passed` across solver-dispatch, result-report, and scientific-followup suites
  - the false frontend confirmation/state mismatch on recovered thread `31075618-e16f-4067-9945-1a8e778458fc` is now fixed:
    - `frontend/src/components/workspace/submarine-workbench/submarine-session-model.ts` now suppresses stale confirmation-gate copy when the confirmed design brief and final report show no pending decisions
    - `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.model.ts` now prefers `final-report.json`'s `source_runtime_stage` when stale runtime stage metadata would otherwise regress the visible badge
    - the real page no longer shows `当前有 3 项待确认事项` while the contract snapshot says `待处理决策 0 项`
    - the center evidence badge on the same page now shows `阶段: 结果整理中` instead of the stale `阶段: 几何预检`
    - focused frontend regression coverage for this slice is green at `30 passed`, and `corepack pnpm --dir frontend check` is green
  - the recovered-thread operator-board raw-language leak is now fixed:
    - `frontend/src/components/workspace/submarine-workbench/submarine-detail-model.ts` now derives delivery-decision, remediation-handoff, and scientific-follow-up labels from the existing runtime-panel summary builders instead of exposing raw enums
    - the same detail model now localizes tool ids and common remediation action titles through the shared workspace display layer, and slug-like unknown fallbacks degrade to generic user-facing labels instead of leaking internal ids
    - `frontend/src/core/i18n/workspace-display.ts` now maps `submarine_solver_dispatch`, `submarine_result_report`, `submarine_scientific_followup`, `spawn_agent`, and common remediation action titles into user-facing wording
    - focused frontend regression coverage for the localized-operator-board slice is green at `26 passed`, `corepack pnpm --dir frontend check` is green, the recovered-thread page text no longer contains `blocked_by_setup` / `manual_followup_required` / `dispatch_refreshed_report` / `Attach validation reference` / `submarine_solver_dispatch` / `spawn_agent`, and a reviewer re-check reported no remaining issues in the touched files
  - the recovered-thread main-canvas language hardening slice is now fixed:
    - `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.model.ts` now localizes runtime status badges so the center evidence card shows `运行: 已阻塞` instead of `运行: blocked`
    - the same model now localizes the known English contract revision sentence before it reaches either the operator board or the main canvas (`已更新结构化 CFD 设计简报。`)
    - mapped stage ids in structured slice notes now surface as user-facing text such as `结果整理阶段`, and unknown multi-separator slug-like tokens degrade to `相关研究项` while legitimate technical hyphenated terms like `k-epsilon` remain intact
    - focused frontend regression coverage for the research-canvas hardening slice is green at `17 passed`, `corepack pnpm --dir frontend check` is green, and a reviewer re-check reported the narrowed sanitization was ready to land
- In Progress:
  - Task 7 real browser-visible iterative-scenario validation
  - proving a rerun-oriented scientific follow-up scenario end-to-end on the fixed stack
  - deciding whether remediation should keep preferring `execute-scientific-studies` when the immediate blocker is missing baseline residual evidence
- Reopened / Invalidated:
  - the earlier mouse-submit regression is not reproduced on the latest clean frontend/backend stack and should not be treated as an active product bug without fresh evidence
  - the assumption that "if plan iteration works, the rest of the workflow families are automatically stable" remains invalidated
  - the product is explicitly `vibeCFD` as a collaborative execution partner, not a scientific decision oracle
  - the temporary concern that the frontend was still stale after the refresh-only run is invalidated by the post-run reload: the visible page now reflects `r4` and the cleaned task text

## Execution / Review Trace
- Latest Implementation Mode: local implementation in the active `main` workspace
- Latest Review Mode: reviewer subagents re-checked both the operator-board and the research-canvas language-hardening slices after each fallback tightening and reported no remaining issues in the touched files
- Latest Delegation Note: reviewer passes were used first to catch the raw-fallback leak path in `submarine-detail-model.ts`, then to tighten the research-canvas sanitization so it still hides internal slugs without swallowing legitimate technical hyphenated terms

## Research Overlay Check
- Research Mainline Status: not applicable
- Non-Negotiables Status: not applicable
- Forbidden Regression Check:
  - do not drift into a generic workflow engine
  - do not paper over orchestration weakness with prompt-only behavior unless the prompt change is paired with durable validation and the structured state remains authoritative
  - do not let message history remain the only source of task truth
- Method Fidelity Check:
  - authoritative task state still comes from the structured runtime / artifact contract, not only chat history
  - `output_delivery_plan` remains authoritative from design brief through reporting
  - visible frontend state must keep reflecting the same contract and runtime truth as backend artifacts
  - confirmation turns that unlock execution must refresh the design brief before solver dispatch
  - refresh-only follow-up now also derives revised task intent from the latest substantive user message when present, instead of trusting stale handoff text
- Scale Gate Status: not applicable
- Decision Log Updates:
  - the earlier mouse-submit suspicion is retired as an active blocker unless fresh evidence reappears on the latest stack
  - the real blocker before this slice was confirmation orchestration: the user could confirm pending assumptions, but the agent sometimes skipped the design-brief refresh and hit solver dispatch too early
  - fresh thread `417cec01-4d6a-41f0-bce8-56773d64d7e8` proves the visible chain through upload, confirmation, solver dispatch, reporting, scientific gate, and remediation handoff
  - the later refresh-only follow-up blocker was not the rerun/no-rerun branch itself; it was stale task-text resolution inside `submarine_scientific_followup`, which previously trusted `handoff.tool_args.task_description` even when the latest user message carried the authoritative intent
  - `submarine_scientific_followup` now resolves the active task description from the latest substantive user message when available, strips `<uploaded_files> ... </uploaded_files>` wrappers, and treats explicit "do not rerun solver" wording as an explicit refresh-only contract revision
  - the follow-up tool no longer requires a design-brief delta before honoring an explicit no-rerun refresh request; if the contract is already in sync, it can still refresh the report without falling through to solver dispatch
  - the latest-user task-intent rule is now direct rather than length-based: non-empty, non-generic latest user instructions override stale handoff text once upload-only wrappers and trivial acknowledgements are excluded
  - refresh-only run `019d8b37-20e7-7a80-a020-8a3762f393f2` proves the visible thread can refresh design brief + final report without rerunning solver, and a subsequent browser reload proves the frontend reflects that state
  - the GPT-5.4 first-turn routing issue is retired as an active blocker after fresh-thread validation on `d773e0e7-4cef-4278-b865-3ee812a190ae`
  - visible next-step buttons must not stay disabled once the latest run is already `success`; the older `deriveThreadInputStatus()` logic caused that false streaming lock and is now fixed
  - solver completion detection must not treat `Time = 0s ... End` without residual progression as a completed rerun; the older parser did, and that bug is now fixed
  - after deploying the stricter solver-result classification, thread `d773e0e7-4cef-4278-b865-3ee812a190ae` now surfaces the rerun truthfully as contract `r3`, runtime `failed`, and `scientific-followup-0001` with `outcome_status: dispatch_failed` instead of a false-complete state
  - thread `31075618-e16f-4067-9945-1a8e778458fc` still carries stale confirmation/stage flags under `thread.values.submarine_runtime`, but the frontend now resolves the visible truth from the confirmed design brief and final report when those later artifacts prove there are no pending decisions
  - the visible workbench now suppresses false negotiation copy on that recovered thread and prefers `final-report.json`'s `source_runtime_stage` for the center badge, which brings the user-visible state back in line with the contract snapshot and final report
- Research Findings Updates: none

## Artifact Hygiene / Retirement
- Keep / Promote:
  - `docs/superpowers/prior-art/2026-04-14-vibecfd-iterative-execution-core-survey.md`
  - `docs/superpowers/specs/2026-04-14-vibecfd-iterative-execution-core-design.md`
  - `docs/superpowers/plans/2026-04-14-vibecfd-iterative-execution-core.md`
  - this status file and its context summary
- Archive / Delete / Replace Next:
  - replace any scratch browser-debug notes with updates to the durable status / summary pair
  - avoid keeping stale "mouse-submit bug" notes as live blockers now that fresh evidence points elsewhere

## Latest Verified State
- Active workspace: `C:\Users\D0n9\Desktop\颠覆性大赛`
- Active branch: `main`
- Working tree is intentionally dirty with the iterative-core slice, follow-up fix, and durable-artifact refresh
- Verified this session:
  - `uv run --project backend pytest backend/tests/test_submarine_design_brief_tool.py backend/tests/test_submarine_geometry_check_tool.py backend/tests/test_thread_state_submarine_runtime_merge.py -v`
  - `uv run --project backend pytest backend/tests/test_submarine_solver_dispatch_tool.py backend/tests/test_submarine_experiment_linkage_contracts.py -v`
  - `uv run --project backend pytest backend/tests/test_submarine_result_report_tool.py backend/tests/test_submarine_scientific_followup_tool.py -v`
  - `uv run --project backend pytest backend/tests/test_submarine_scientific_followup_tool.py backend/tests/test_submarine_design_brief_tool.py backend/tests/test_submarine_result_report_tool.py -v`
  - `uv run --project backend pytest backend/tests/test_skill_relationships.py backend/tests/test_submarine_skills_presence.py backend/tests/test_submarine_subagents.py backend/tests/test_lead_agent_prompt_skill_routing.py -v`
  - `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/components/workspace/submarine-workbench/index.contract.test.ts" "src/components/workspace/submarine-workbench/submarine-contract-snapshot.contract.test.ts" "src/components/workspace/submarine-workbench/submarine-visible-actions.test.ts" "src/components/workspace/submarine-workbench/submarine-detail-model.test.ts" "src/components/workspace/submarine-workbench/submarine-session-model.test.ts" "src/components/workspace/submarine-workbench/submarine-research-canvas.model.test.ts" "src/components/workspace/submarine-workbench/submarine-secondary-layers.model.test.ts" "src/components/workspace/submarine-workbench/submarine-operator-board.contract.test.ts" "src/app/workspace/submarine/[thread_id]/page.test.ts"`
  - `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/components/workspace/submarine-workbench/submarine-session-model.test.ts" "src/components/workspace/submarine-workbench/submarine-research-canvas.model.test.ts"`
  - `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/core/i18n/workspace-display.test.ts" "src/components/workspace/submarine-workbench/submarine-detail-model.test.ts" "src/components/workspace/submarine-workbench/submarine-operator-board.contract.test.ts" "src/components/workspace/submarine-workbench/submarine-secondary-layers.model.test.ts"`
  - `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/components/workspace/submarine-workbench/submarine-research-canvas.model.test.ts"`
  - `corepack pnpm --dir frontend check`
  - `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/core/i18n/workspace-display.recovered-copy.test.ts" "src/core/i18n/workspace-display.artifact-filenames.test.ts" "src/core/i18n/workspace-display.skill-studio-files.test.ts" "src/components/workspace/skill-studio-workbench.utils.test.ts" "src/components/workspace/skill-studio-workbench/index.contract.test.ts" "src/components/workspace/artifacts/skill-install.contract.test.ts" "src/components/workspace/submarine-runtime-panel.utils.test.ts"`
  - `uv run --project backend pytest backend/tests/test_submarine_design_brief_tool.py backend/tests/test_submarine_geometry_check_tool.py backend/tests/test_submarine_solver_dispatch_tool.py backend/tests/test_submarine_result_report_tool.py backend/tests/test_submarine_scientific_followup_tool.py backend/tests/test_submarine_subagents.py backend/tests/test_lead_agent_prompt_skill_routing.py -q`
  - backend `8001` listener was explicitly restarted onto the latest local code before the fresh browser validation below
- Browser-proven latest threads:
  - thread `31075618-e16f-4067-9945-1a8e778458fc` now proves the recovered-page truth-alignment slice:
    - contract snapshot shows `r5` and `待处理决策 0 项`
    - the negotiation rail is no longer rendered with a false `3 项待确认事项`
    - the center research card now reports `当前进度: 运行已阻塞`
    - the center evidence badge now reports `阶段: 结果整理中`
    - the operator board now reports `当前判断: 受环境阻塞`, `后续安排: 派发后已刷新报告`, `修正状态: 需要人工跟进`, `执行工具: 人工处理`, `后续执行: 求解派发`, and `待人工确认: 1（补充验证参考）`
    - direct page-text checks after reload confirm `blocked_by_setup`, `manual_followup_required`, `dispatch_refreshed_report`, `Attach validation reference`, `submarine_solver_dispatch`, and `spawn_agent` are absent from the rendered page body
    - the main canvas now reports `运行: 已阻塞` instead of `运行: blocked`, and the contract / main-canvas revision summary now shows `已更新结构化 CFD 设计简报。`
    - the structured context note shown under `切片上下文` now says `结果整理阶段` rather than surfacing raw `result-reporting` in that card
  - thread `417cec01-4d6a-41f0-bce8-56773d64d7e8` still proves the refresh-only follow-up path from the real frontend
  - thread `d773e0e7-4cef-4278-b865-3ee812a190ae` now proves the broader GPT-5.4 mainline:
    - fresh first turn routes directly into geometry preflight
    - typed confirmation updates the design brief and delivery plan
    - visible execution action triggers solver dispatch
    - visible report action triggers final-report and scientific-gate generation
    - visible remediation action reaches `submarine_scientific_followup`
    - after the solver-result parser fix is deployed, the page now surfaces the rerun truthfully as `failed` with all three outputs unavailable for that rerun instead of silently over-claiming completion
- Confirmed product gap:
  - the remaining unproven gap is no longer first-turn routing, confirmation gating, refresh-only follow-up, or visible CTA re-entry; it is whether rerun-oriented follow-up can complete a genuinely improved rerun instead of ending in a correctly classified but still incomplete solver execution

## Unverified Hypotheses / Next Checks
- the output-expansion scenario may already work with the current contract vocabulary because the runtime now preserves `requested_outputs` and `output_delivery_plan` across stages
- the same remediation handoff machinery still needs better recommendation fidelity: the current handoff can choose `execute-scientific-studies` even when the immediate blocker is missing baseline residual evidence

## Open Questions / Risks
- full browser-visible Task 7 flows may still expose orchestration gaps even though confirmation gating and refresh-only follow-up are now proven
- the specific browser-visible wording leaks previously seen on `9fed37bf-6329-4216-8e32-a2d5ef8b877e`, `01fec432-dead-4cb3-8c2d-09896f4fe832`, and `31075618-e16f-4067-9945-1a8e778458fc` are retired after forced reload checks, but broader surface-area coverage on other older threads is still lighter than the core CFD-flow evidence
- the scientific gate currently blocks the baseline because `max_final_residual` exceeds threshold; that is correct behavior, but the deeper auto-remediation loop is not yet fully proven
- a real output-expansion scenario may still reveal downstream execution or post-process gaps despite the stronger contract-state rendering
- repeated rerun-oriented follow-up lineage may still need broader schema pressure testing than the now-proven refresh-only path
- the rerun toolchain can now classify incomplete solver logs more honestly, but the underlying remediation strategy can still fail to produce the intended improved baseline evidence
- backend runtime merge semantics can still leave stale confirmation/stage metadata in `thread.values.submarine_runtime`; the frontend now guards against that in the recovered-page view, but the backend single-source-truth path is not yet fully hardened

## Relevant Findings / Notes
- External STL fixture for browser-visible testing: `C:\Users\D0n9\Desktop\suboff_solid.stl`
- Earlier strong report thread: `d84b80ef-ed26-4fa9-b1a8-a55a2745df91`
- Earlier strong report location:
  - `backend/.deer-flow/threads/d84b80ef-ed26-4fa9-b1a8-a55a2745df91/user-data/outputs/submarine/reports/suboff_solid/`
- Fresh confirmation / dispatch / report validation thread:
  - `417cec01-4d6a-41f0-bce8-56773d64d7e8`
- Fresh validation findings:
  - recovered-thread UI truth alignment now holds on `31075618-e16f-4067-9945-1a8e778458fc`: no false pending-confirmation rail, and the center evidence badge uses `result-reporting`
  - upload + text mouse submission works on the latest clean frontend/backend stack
  - after explicit reference confirmation, the latest guidance refreshes the design brief before execution
  - visible execution action triggers `submarine_solver_dispatch`
  - the baseline run reaches reporting, but scientific delivery is correctly blocked because `Final residual threshold: observed 0.072008 exceeds limit 0.001000`
  - refresh-only follow-up run `019d8b37-20e7-7a80-a020-8a3762f393f2` updates the design brief and final report while leaving the original solver request untouched
  - the reloaded frontend now reflects that refresh-only outcome with contract `r4`, cleaned task text, and no visible `<uploaded_files>` pollution
  - an explicit variant follow-up run `019d8b50-356d-7ef2-8b03-03bac662abf8` was launched from the real frontend, then intentionally interrupted and rolled back after a backend restart during this session; it should not be treated as product evidence
  - latest follow-up history file:
    - `backend/.deer-flow/threads/417cec01-4d6a-41f0-bce8-56773d64d7e8/user-data/outputs/submarine/reports/suboff_solid/scientific-followup-history.json`
  - current key artifact roots for the fresh thread:
    - `backend/.deer-flow/threads/417cec01-4d6a-41f0-bce8-56773d64d7e8/user-data/outputs/submarine/design-brief/suboff_solid/`
    - `backend/.deer-flow/threads/417cec01-4d6a-41f0-bce8-56773d64d7e8/user-data/outputs/submarine/solver-dispatch/suboff_solid/`
    - `backend/.deer-flow/threads/417cec01-4d6a-41f0-bce8-56773d64d7e8/user-data/outputs/submarine/reports/suboff_solid/`

## 2026-04-15 Frontend Hardening Update
- Real-thread browser validation on `01fec432-dead-4cb3-8c2d-09896f4fe832` now confirms the main workbench header no longer stays on the generic upload title inside the thread view; it falls back to the current submarine objective (`DARPA SUBOFF ...`) instead.
- The same page now localizes the previously visible raw workflow copy in user-facing chat/history for the confirmed-path slice:
  - raw `/mnt/user-data/...` upload paths collapse to filenames such as `suboff_solid.stl`
  - `plan-only` now renders as a user-facing Chinese label
  - `preflight_then_execute` now renders as a user-facing Chinese label
  - the visible remediation CTA summary no longer shows `Run the planned ... verification artifacts ... domain_sensitivity, time_step_sensitivity`
  - remediation titles such as `Execute scientific verification studies` now render as user-facing Chinese text
- Focused frontend verification added in this slice:
  - `frontend/src/core/i18n/workspace-display.recovered-copy.test.ts`
  - `frontend/src/core/messages/utils.human-workflow.test.ts`
  - `frontend/src/core/messages/utils.virtual-path.test.ts`
  - `frontend/src/core/threads/utils.generic-title.test.ts`
  - `frontend/src/core/threads/utils.contextual-title.test.ts`
  - `frontend/src/components/workspace/submarine-workbench/submarine-visible-actions.recovered-copy.test.ts`
- Reviewer follow-up from subagent `Noether` raised two Important concerns (path-only human copy leakage and generic upload titles with upload-only message scaffolding). Both concerns were pressure-tested with new regressions; the current implementation passes those tests and the concerns are no longer treated as open blockers for this slice.
- Remaining user-visible cleanup gap after this slice:
  - the recent-thread sidebar list can still show a generic localized upload label (`STL ????`) when the thread list payload lacks enough runtime/message context to derive a better title
  - the file drawer still surfaces raw artifact filenames such as `study-manifest.json`, `solver-results.json`, and `scientific-remediation-handoff.json`
- after the later contextual-title hardening, the recent-thread sidebar entry for `01fec432-dead-4cb3-8c2d-09896f4fe832` now also avoids the generic upload title and renders `suboff_solid CFD ??` instead

## 2026-04-15 Skill Studio Publish/Install Update
- Real-browser validation on published Skill Studio thread `9fed37bf-6329-4216-8e32-a2d5ef8b877e` now proves the install UX no longer dead-ends in `409 already exists` from the user perspective:
  - the packaged `.skill` artifact now renders as `已安装` and is disabled both in the visible chat artifact list and in the file drawer list
  - the frontend now treats the backend's `409 Skill '...' already exists` install response as an already-installed no-op state instead of surfacing it as a failure toast
  - the artifact install controls pre-compute installed state from `GET /api/skills`, so the published thread reloads directly into the correct `已安装` state without requiring a failed click first
- The same Skill Studio thread now also localizes the most visible remaining binding / historical copy leaks:
  - binding target cards now show `显式挂载` and `当前技能` instead of raw `explicit` and the current skill slug
  - the thread header and visible historical summary copy now rewrite `deliver / review / rerun`, `final report`, `scientific verification`, `SKILL.md`, and `validation-report.json` into user-facing Chinese wording
- hard-reload hydration no longer falls straight into the misleading `未命名技能` empty shell:
  - `frontend/src/components/workspace/skill-studio-workbench/index.tsx` now detects the no-data-yet hydration window and shows a dedicated `正在恢复技能线程` placeholder instead of rendering the default empty draft chrome
- Focused frontend verification added / refreshed in this slice:
  - `frontend/src/core/skills/install-utils.test.ts`
  - `frontend/src/components/workspace/artifacts/skill-install.contract.test.ts`
  - `frontend/src/core/i18n/workspace-display.recovered-copy.test.ts`
  - `frontend/src/components/workspace/skill-studio-workbench.utils.test.ts`
  - `frontend/src/components/workspace/skill-studio-workbench/index.contract.test.ts`
- Verification completed in this slice:
  - `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/core/skills/install-utils.test.ts" "src/components/workspace/artifacts/skill-install.contract.test.ts"`
  - `corepack pnpm --dir frontend exec node --experimental-strip-types --test "src/core/i18n/workspace-display.recovered-copy.test.ts" "src/core/i18n/workspace-display.test.ts" "src/components/workspace/skill-studio-workbench.utils.test.ts" "src/components/workspace/skill-studio-workbench/skill-studio-detail-model.test.ts" "src/components/workspace/skill-studio-workbench/skill-studio-publish-status.test.ts" "src/components/workspace/skill-studio-workbench/index.contract.test.ts"`
  - `corepack pnpm --dir frontend check`
- Reviewer subagent `Tesla` re-checked the install-state slice and reported no findings; the only residual risk it called out is that the already-installed detection still depends on the backend keeping the same `Skill '...' already exists` detail plus the `.skill` filename convention.
- Remaining observation after reload-heavy browser checks:
  - hard reloads were previously able to flash the empty draft shell before rehydration; this slice now routes that window through a dedicated recovery placeholder, but it is still worth keeping an eye on whether future cache/query changes regress that experience

## 2026-04-15 Final Cleanup And Broad Verification
- A final forced-reload browser pass now retires the two residual frontend-only leaks that were still visible before this checkpoint:
  - Skill Studio thread `9fed37bf-6329-4216-8e32-a2d5ef8b877e` no longer shows the raw current skill slug or `.skill` archive name inside historical chat copy; the page now renders `已创建技能 当前技能` and `最终打包文件 当前技能安装包`
  - submarine thread `01fec432-dead-4cb3-8c2d-09896f4fe832` no longer shows mixed `scientific remediation / follow-up` wording; the visible page now stays fully localized on reload
- The same final browser pass also re-confirmed the older recovered thread `31075618-e16f-4067-9945-1a8e778458fc` remains free of `blocked_by_setup`, `manual_followup_required`, `dispatch_refreshed_report`, `spawn_agent`, `result-reporting`, and `Execute scientific verification studies` leakage after a fresh reload.
- Regression coverage added in this cleanup pass:
  - `frontend/src/core/i18n/workspace-display.recovered-copy.test.ts` now includes code-span coverage for the current skill slug / package filename, phrase-order coverage for `scientific remediation / follow-up`, and a direct guard against `remediation handoff` regressing into mixed `修正事项 handoff` copy
  - `frontend/src/core/i18n/workspace-display.test.ts` now also guards the shared helper against rewriting ordinary English prose that merely contains words like `explicit` or `review`
- Broad verification completed in this cleanup pass:
  - `corepack pnpm --dir frontend check`
  - focused frontend localization / Skill Studio / artifact / submarine utility suites: `99 passed`
  - backend iterative mainline suite: `159 passed`
- Artifact hygiene completed in this cleanup pass:
  - deleted scratch export `tmp-thread-01fec432-history.json`
