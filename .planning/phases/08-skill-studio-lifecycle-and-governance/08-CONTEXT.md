# Phase 8: Skill Studio Lifecycle and Governance - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 turns Skill Studio from a draft-and-publish workbench into a governed full-lifecycle product for Vibe CFD skills.

The phase covers expert co-creation, package completeness, publish/install-enable flow, post-publish management, relationship-graph visibility, and version plus rollback governance for project-local DeerFlow skills. It also needs to clarify when a skill is simply globally enabled versus when it is explicitly bound to a specialized execution step or subagent.

This phase does not reopen the shared workspace shell architecture from Phase 7, expand into marketplace or org-wide governance, or take on deployment-isolation work that belongs to later phases.

</domain>

<decisions>
## Implementation Decisions

### Lifecycle surface model
- **D-01:** Treat the current post-Phase-7 Skill Studio redesign as the UI baseline for Phase 8 rather than reopening workspace-shell decisions.
- **D-02:** Keep the outer lifecycle narrative centered on `Create / Evaluate / Connect`, while preserving the focused lifecycle work surfaces underneath for build, evaluation, test, publish, and graph work.
- **D-03:** The graph must remain an explicit first-class view because it is the clearest way to show relationships between skills.

### Publish and application flow
- **D-04:** Publish is mandatory first-class lifecycle behavior, not just a readiness summary. Users must still have a real way to apply a completed skill to the project.
- **D-05:** Expert confirmation remains the gate before final publish and enable.
- **D-06:** Publishing should continue to mean installing the generated `.skill` package into the project-local DeerFlow custom-skill setup and enabling it for project use when approved.
- **D-07:** Published skills must remain discoverable and callable in later threads through the normal enabled-skill loading path.

### Skill routing and step binding
- **D-08:** Phase 8 must make skill application explicit: the product should show whether a skill is only globally enabled or is also bound to a specific execution step or subagent.
- **D-09:** The system should support both application modes: agent auto-discovery from the enabled skill pool and explicit per-step or per-subagent binding for specialized or high-risk workflow steps.
- **D-10:** The existing `target_skills` execution-plan contract is the right anchor for the new "configure this skill to a specific step" capability.

### Version and governance model
- **D-11:** Version history should be centered on the skill asset, not on an individual chat thread.
- **D-12:** Threads remain creation and review workspaces; published revisions, version notes, rollback targets, and active status belong to the skill record.
- **D-13:** Phase 8 should extend beyond today's overwrite-only publish behavior into visible revision history and rollback targets.

### Graph and governance presentation
- **D-14:** The graph should carry relationship and impact context as part of governance, but it should not replace publish, revision, or rollback controls.
- **D-15:** Revision history, rollback, and enable or disable management should live inside the existing lifecycle product instead of forcing a separate parallel governance app.

### the agent's Discretion
- Exact naming between `图谱`, `连接`, or combined labels, as long as the graph stays explicit and easy to find.
- Exact visual placement of revision history, version notes, publish badges, and enablement status inside the current lifecycle workbench.
- Exact UI control pattern for per-step binding, as long as users can inspect and edit skill-to-step assignment clearly.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and phase anchors
- `.planning/PROJECT.md` - milestone promise, project-local skill-lifecycle goals, and DeerFlow alignment constraints.
- `.planning/ROADMAP.md` - Phase 8 goal, success criteria, and plan split for lifecycle, publish, and governance work.
- `.planning/REQUIREMENTS.md` - `SKILL-01` through `SKILL-05` define the acceptance boundary for this phase.
- `.planning/STATE.md` - current handoff state and phase sequencing after Phase 7.
- `.planning/research/v1.1-deerflow-alignment.md` - DeerFlow-native skill, publish, and enablement expectations that this phase should match.

### Carry-forward UX and design context
- `.planning/phases/07-workspace-ux-and-navigation-system/07-CONTEXT.md` - carry-forward decision that Skill Studio already has approved lifecycle subviews and a real graph page.
- `.planning/phases/07-workspace-ux-and-navigation-system/07-UI-SPEC.md` - locked workspace and Skill Studio UI contract from Phase 7.
- `frontend/src/components/workspace/skill-studio-dashboard.tsx` - current post-Phase-7 dashboard baseline and `Create / Evaluate / Connect` outer narrative.
- `frontend/src/components/workspace/skill-studio-workbench-shell.tsx` - current lifecycle shell, graph filter surface, and focused view structure.
- `frontend/src/components/workspace/skill-studio-workbench-panel.tsx` - current artifact-backed build, evaluation, test, publish, and graph workbench behavior.
- `frontend/src/app/workspace/skill-studio/[thread_id]/page.tsx` - current thread page, chat rail, and workbench embedding behavior.

### Current backend skill lifecycle and publish mechanics
- `backend/packages/harness/deerflow/domain/submarine/skill_studio.py` - generated Skill Studio artifacts, `.skill` archive assembly, readiness payloads, and current state contract.
- `backend/app/gateway/routers/skills.py` - install and publish endpoints plus `extensions_config.json` enablement behavior.
- `backend/packages/harness/deerflow/skills/loader.py` - enabled-skill discovery across `skills/public` and `skills/custom`.
- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py` - enabled skill injection into agent prompts and graph-assisted routing guidance.
- `backend/packages/harness/deerflow/tools/builtins/task_tool.py` - explicit `target_skills` narrowing for specialized delegated work.
- `backend/packages/harness/deerflow/domain/submarine/contracts.py` - execution-plan contract that already includes `target_skills`.

### Behavioral anchors and current expectations
- `backend/tests/test_submarine_skill_studio_tool.py` - expected generated artifacts, statuses, and publish-ready package output from Skill Studio.
- `backend/tests/test_skills_publish_router.py` - expected install, enable, and overwrite publish behavior.
- `backend/tests/test_skill_relationships.py` - expected local skill-graph relationship semantics and focused-node behavior.
- `backend/tests/test_lead_agent_prompt_skill_routing.py` - expected lead-agent routing guidance for explicit `target_skills`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/packages/harness/deerflow/domain/submarine/skill_studio.py` already generates `skill-draft`, `skill-package`, `SKILL.md`, validation, test-matrix, publish-readiness, and `.skill` archive artifacts, so Phase 8 does not start from zero.
- `backend/app/gateway/routers/skills.py` already supports install, publish, overwrite, and enablement by writing `extensions_config.json`.
- `backend/packages/harness/deerflow/skills/loader.py` plus `backend/packages/harness/deerflow/agents/lead_agent/prompt.py` already make enabled skills visible to agents in later runs.
- `backend/packages/harness/deerflow/tools/builtins/task_tool.py` and `backend/packages/harness/deerflow/domain/submarine/contracts.py` already provide a concrete `target_skills` contract for step-specific or subagent-specific skill routing.
- `frontend/src/components/workspace/skill-studio-dashboard.tsx`, `frontend/src/components/workspace/skill-studio-workbench-shell.tsx`, and `frontend/src/components/workspace/skill-studio-workbench-panel.tsx` already provide the lifecycle UI home for additional governance features.
- Existing skill-graph helpers and `/api/skills/graph` already provide a relationship model that Phase 8 can extend rather than replace.

### Established Patterns
- Skill Studio state is persisted in `thread.values.submarine_skill_studio` and mirrored into artifact-backed JSON or Markdown outputs under `/submarine/skill-studio/...`.
- Publishing currently means "install into custom skills + optionally enable", with overwrite support but without a first-class revision history model.
- Agents currently discover skills from the enabled skill pool by default; explicit narrowing only happens when `target_skills` is passed.
- The current frontend has already shifted from a crowded shell to a lighter lifecycle narrative; governance additions should preserve that tighter focus instead of re-expanding the page into one mixed canvas.

### Integration Points
- `extensions_config.json` and `skills/custom/*` are the concrete project-local application path after publish.
- `target_skills` in the execution plan is the natural integration point for "bind this skill to a specific step" behavior.
- `/api/skills/graph` and current graph helpers are the natural home for post-publish relationship and impact inspection.
- The Skill Studio dashboard and thread workbench are the current product surfaces where revision history, rollback, publish state, and binding controls should surface.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly said the graph should stay because it best shows relationships between skills.
- The user explicitly said publish cannot disappear because the product needs a real path for how a completed skill gets applied.
- The user wants a concrete capability to configure a skill to a specific step, not just a passive publish result.
- The user explicitly asked the phase to clarify whether skills are auto-discovered by agents or preconfigured ahead of execution.
- After Phase 7 completed, the user further refined frontend page design; the current `Create / Evaluate / Connect` framing and lighter overview should be treated as the new frontend baseline for Phase 8 work.

</specifics>

<deferred>
## Deferred Ideas

- Marketplace-style or public skill distribution remains out of scope; this phase is project-local governance only.
- Organization-wide RBAC or multi-tenant publishing remains out of scope for this milestone.
- Deployment isolation and sandbox-hardening work still belongs to Phase 9.
- Broad architecture decomposition beyond what is needed for lifecycle governance still belongs to Phase 10.

</deferred>

---

*Phase: 08-skill-studio-lifecycle-and-governance*
*Context gathered: 2026-04-04*
