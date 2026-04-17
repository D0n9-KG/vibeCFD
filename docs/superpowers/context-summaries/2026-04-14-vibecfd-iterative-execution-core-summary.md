# VibeCFD Iterative Execution Core Context Summary

**Status:** in_progress - the confirmation gate and refresh-only remediation follow-up remain browser-proven on the submarine side, and a final cleanup pass now retires the last browser-visible wording leaks on the three saved verification threads: published Skill Studio thread `9fed37bf-6329-4216-8e32-a2d5ef8b877e` no longer shows the raw current skill slug or `.skill` archive name in history, thread `01fec432-dead-4cb3-8c2d-09896f4fe832` no longer shows mixed `scientific remediation / follow-up` wording, and thread `31075618-e16f-4067-9945-1a8e778458fc` remains clean after a forced reload. The main remaining uncertainty is now back where it belongs: the unproven output-expansion / rerun-improvement path on the submarine side.

**Related Plan:** `docs/superpowers/plans/2026-04-14-vibecfd-iterative-execution-core.md`

**Related Session Status:** `docs/superpowers/session-status/2026-04-14-vibecfd-iterative-execution-core-status.md`

**Research Overlay:** disabled

**Research Mainline:** none

## Canonical Snapshot
- Goal / Mainline: make the product behave like a `vibeCFD` collaborative execution partner for real CFD work, not a one-shot wrapper and not a scientific decision oracle
- Chosen direction: iterative execution core first
- Latest Verified State:
  - backend contract truth still carries iterative fields (`contract_revision`, `revision_summary`, `capability_gaps`, `unresolved_decisions`, `evidence_expectations`, `variant_policy`, `output_delivery_plan`) through design brief, geometry preflight, solver dispatch, reporting, follow-up, and runtime merge
  - public submarine skills and the lead-agent workflow prompt explicitly encode the confirmation rule that matters in practice:
    - if a user confirmation resolves all execution blockers, refresh `submarine_design_brief` with `confirmation_status="confirmed"` before `submarine_solver_dispatch`
    - if blockers remain, keep `confirmation_status="draft"`, keep only unresolved `open_questions`, explain the blockers, and stop before solver dispatch
  - the real refresh-only follow-up bug is fixed in `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`:
    - resolve task intent from the latest substantive `HumanMessage` instead of stale `handoff.tool_args.task_description` when possible
    - strip `<uploaded_files> ... </uploaded_files>` wrappers before turning the latest user message into the revised task contract
    - recognize explicit "do not rerun solver" phrasing in either Chinese or English
    - honor explicit no-rerun refresh even when the design brief is already in sync
    - prefer short but substantive latest-user follow-up instructions without relying on a length heuristic
  - the browser-proven thread `417cec01-4d6a-41f0-bce8-56773d64d7e8` now demonstrates:
    - upload + text intake from `/workspace/submarine/new`
    - reference confirmation through the visible frontend chat
    - refreshed design brief before execution
    - visible execution action sending a traced message
    - `submarine_solver_dispatch` execution and solver / study artifacts
    - `submarine_result_report` execution and final report artifacts
    - scientific gate blocking with visible evidence instead of silent over-claiming
    - remediation-handoff artifacts and a visible follow-up action that reaches `submarine_scientific_followup`
    - refresh-only run `019d8b37-20e7-7a80-a020-8a3762f393f2` updates the design brief and final report without rerunning solver
    - a post-run page reload now shows contract `r4`, clean task text without `<uploaded_files>`, and visible follow-up outcome `result_report_refreshed`
    - artifact timestamps prove the no-rerun behavior: `openfoam-request.json` stayed at `2026-04-14 16:16:40`, while `cfd-design-brief.json` and `final-report.json` advanced to `2026-04-14 16:59:26` and `2026-04-14 16:59:58`
  - `frontend check` is green and the focused backend prompt / skill suites are green after the confirmation-flow wording change and follow-up fix
  - the focused follow-up / design-brief / report suite is currently green at `67 passed`
  - the recovered thread `31075618-e16f-4067-9945-1a8e778458fc` now also proves the frontend truth-alignment guard:
    - contract snapshot shows `r5` with `待处理决策 0 项`
    - the negotiation rail no longer renders the stale `3 项待确认事项`
    - the center evidence badge now renders `阶段: 结果整理中` from `final-report.json` instead of the stale runtime stage
    - the operator board now reports user-facing labels such as `当前判断: 受环境阻塞`, `后续安排: 派发后已刷新报告`, `修正状态: 需要人工跟进`, `执行工具: 人工处理`, and `待人工确认: 补充验证参考`
    - direct page-text checks after reload confirm `blocked_by_setup`, `manual_followup_required`, `dispatch_refreshed_report`, `Attach validation reference`, `submarine_solver_dispatch`, and `spawn_agent` are absent from the rendered page body
    - the main canvas now reports `运行: 已阻塞` instead of `运行: blocked`, the revision summary now shows `已更新结构化 CFD 设计简报。`, and the structured context note now says `结果整理阶段` instead of raw `result-reporting`
    - focused frontend regressions for these language-hardening slices are green, `corepack pnpm --dir frontend check` is green, and reviewer re-checks found no remaining issues in the touched files
- Current Method / Constraints:
  - adapt the existing DeerFlow submarine architecture instead of inventing a second workflow engine
  - keep the product anchored to `vibeCFD`
  - preserve runtime snapshot authority; chat history explains but does not replace the structured contract

## Read Next If Needed
- `docs/superpowers/session-status/2026-04-14-vibecfd-iterative-execution-core-status.md`
- `docs/superpowers/specs/2026-04-14-vibecfd-iterative-execution-core-design.md`
- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
- `backend/packages/harness/deerflow/tools/builtins/submarine_scientific_followup_tool.py`
- `skills/public/submarine-orchestrator/SKILL.md`
- `frontend/src/components/workspace/submarine-workbench/submarine-research-canvas.tsx`
- `frontend/src/components/workspace/submarine-workbench/submarine-operator-board.tsx`

## Active Artifacts
- Keep Active:
  - `docs/superpowers/prior-art/2026-04-14-vibecfd-iterative-execution-core-survey.md`
  - `docs/superpowers/specs/2026-04-14-vibecfd-iterative-execution-core-design.md`
  - `docs/superpowers/plans/2026-04-14-vibecfd-iterative-execution-core.md`
  - `docs/superpowers/session-status/2026-04-14-vibecfd-iterative-execution-core-status.md`
  - this summary file
- Superseded Or Archived:
  - the older "mouse-submit bug" narrative is historical only; the latest clean validation does not support keeping it as the active blocker

## Retirement Queue
- stale scratch notes about the earlier submit suspicion
- temporary browser-debug notes once the output-expansion scenario and any rerun-oriented follow-up checks are durably recorded

## Open Risks
- the specific browser-visible wording leaks on the three saved verification threads are retired, but broader coverage across older or less-representative threads is still lighter than the mainline CFD execution evidence
- the scientific gate correctly blocks the current baseline because residual evidence is weak; the refresh-only remediation path is proven, but the rerun-oriented path still has lighter evidence
- output-expansion after first execution is still unproven in a fresh real thread
- repeated rerun-oriented follow-up lineage may still reveal schema pressure in the current manifest model
- the interrupted explicit-variant run from this session is not trustworthy evidence because the backend was restarted while it was in flight and the run was later rolled back
- `thread.values.submarine_runtime` can still retain stale confirmation/stage metadata under the hood after later artifacts land; the frontend now guards against that in the recovered-page view, but the backend single-source-truth path is not yet fully hardened

## 2026-04-15 Frontend Hardening Update
- The recovered real-thread UI hardening now covers a fourth browser-proven slice on thread `01fec432-dead-4cb3-8c2d-09896f4fe832`:
  - the main workbench header no longer stays on the generic upload title inside the thread view; it falls back to the current submarine objective
  - raw `/mnt/user-data/...` upload paths in user-facing history collapse to filenames
  - `plan-only` and `preflight_then_execute` no longer surface as raw internal execution modes in the visible thread history
  - the visible remediation CTA summary now localizes the previously mixed English rerun guidance and study ids
  - the remediation action title `Execute scientific verification studies` now renders as user-facing Chinese text
- Reviewer re-check notes for this slice:
  - a proactive reviewer flagged two remaining risks (path-only human copy leakage and generic upload titles with upload-only message scaffolding)
  - both were converted into explicit regressions and now pass on the current frontend stack
- Remaining UI hardening gap after this slice is narrower and more peripheral:
  - the recent-thread sidebar can still show a generic localized upload title when list payloads lack runtime/message context
  - the file drawer still exposes raw artifact filenames rather than user-facing labels
- the recent-thread sidebar entry for the recovered real thread now also avoids the generic upload title and renders `suboff_solid CFD ??` when list payloads only provide submarine artifact paths

## 2026-04-15 Skill Studio Publish/Install Update
- Published Skill Studio thread `9fed37bf-6329-4216-8e32-a2d5ef8b877e` now proves the previously unresolved install UX slice:
  - the packaged `.skill` archive renders as `已安装` and is disabled in both visible artifact entry points
  - frontend install handling now normalizes the backend's `409 Skill '...' already exists` response into an already-installed no-op state
  - pre-render installed-state lookup comes from `GET /api/skills`, so reload lands directly in the correct state instead of waiting for a failed click
- The same thread also proves a follow-on copy-hardening slice:
  - binding target cards now show `显式挂载` and `当前技能`
  - visible header/history copy now rewrites `deliver / review / rerun`, `final report`, `scientific verification`, `SKILL.md`, and `validation-report.json`
- Reload handling for the same page is also tighter now:
  - the no-data-yet hydration window no longer drops the user into a misleading `未命名技能` empty draft shell; the frontend now shows a dedicated `正在恢复技能线程` placeholder during that gap
- Reviewer subagent `Tesla` re-checked the install-state slice and reported no findings; residual risk is limited to dependence on the current backend `already exists` detail string and the `.skill` filename convention.
- Residual observation: keep watching reload-heavy behavior in case future query/cache changes regress the new hydration placeholder back into an empty draft shell.

## 2026-04-15 Final Cleanup And Broad Verification
- Final forced-reload browser validation now proves:
  - Skill Studio thread `9fed37bf-6329-4216-8e32-a2d5ef8b877e` renders `已创建技能 当前技能` and `最终打包文件 当前技能安装包` instead of the raw slug / archive filename
  - the same Skill Studio history now keeps `remediation handoff` fully localized as `修正交接说明` instead of regressing into mixed `修正事项 handoff`
  - submarine thread `01fec432-dead-4cb3-8c2d-09896f4fe832` no longer leaks `scientific remediation / follow-up`
  - recovered thread `31075618-e16f-4067-9945-1a8e778458fc` remains free of earlier raw internal status ids after another hard reload
- Final verification in this pass:
  - `corepack pnpm --dir frontend check`
  - focused frontend localization / Skill Studio / artifact / submarine utility suites: `99 passed`
  - backend iterative mainline suite: `159 passed`
- Cleanup in this pass:
  - removed scratch export `tmp-thread-01fec432-history.json`
