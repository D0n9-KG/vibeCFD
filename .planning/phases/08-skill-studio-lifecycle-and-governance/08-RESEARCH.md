# Phase 8: Skill Studio Lifecycle and Governance - Research

**Researched:** 2026-04-04
**Domain:** DeerFlow-aligned skill lifecycle, publish governance, and post-publish routing
**Confidence:** HIGH

<user_constraints>
## User Constraints (from ROADMAP.md / REQUIREMENTS.md / approved discussion)

- `SKILL-01`: Users must be able to co-create a Vibe CFD skill inside a dedicated workbench that follows DeerFlow skill conventions.
- `SKILL-02`: Generated outputs must stay package-complete and installable without manual patching.
- `SKILL-03`: After expert sign-off, publish must install and auto-configure the skill into the project's DeerFlow setup.
- `SKILL-04`: Users must be able to inspect draft versus published revisions, version notes, and rollback targets.
- `SKILL-05`: Published custom skills must remain discoverable to the main agent in later threads and visible in management plus relationship views.
- The user explicitly locked the current post-Phase-7 Skill Studio redesign as the frontend baseline for Phase 8.
- The user explicitly locked graph as a first-class view and explicitly rejected removing publish.
- The user explicitly wants both skill-application modes to exist: default enabled-pool discovery and explicit binding to a specific step or subagent.
- The user explicitly wants revision history centered on the skill asset rather than on an individual thread.

</user_constraints>

<research_summary>
## Summary

Phase 8 is not a greenfield phase. The repo already has four major ingredients:

- a draft-generation pipeline that writes `SKILL.md`, metadata, validation, test-matrix, publish-readiness, and `.skill` archive artifacts,
- a publish route that installs `.skill` archives into `skills/custom/<skill-name>` and toggles enablement in `extensions_config.json`,
- a skill graph API that builds relationship and focus views from local skills,
- and a runtime contract that already supports explicit `target_skills` narrowing for delegated work.

The real gap is that these ingredients are still separate slices rather than one governed lifecycle product.

Key findings:

- Skill Studio draft truth is still thread-scoped. `run_skill_studio()` writes artifacts under `/submarine/skill-studio/<skill-slug>/...` and mirrors a lightweight summary into `thread.values.submarine_skill_studio`, but that thread-state contract has no asset id, revision list, version note, active revision, rollback target, or binding metadata.
- Publish is operational but shallow. `/api/skills/publish` installs the generated archive into `skills/custom`, optionally overwrites an existing skill, and flips enablement through `extensions_config.json`, but it does not create any durable lifecycle record beyond the installed files plus enable flag.
- Skill discovery already supports the exact dual mode the user asked for. `load_skills(enabled_only=True)` makes enabled skills broadly available to agents, while `task_tool` already validates and injects explicit `target_skills` for narrower delegated work.
- The graph is already useful for routing and relationship explanation, but it is not yet a governance graph. `relationships.py` computes `similar_to`, `compose_with`, and `depend_on` edges plus focused-node context, but it knows nothing about publish status, revision count, rollback eligibility, or configured bindings.
- The frontend already exposes the right lifecycle shell. The dashboard and workbench surface `Create / Evaluate / Connect`, publish-readiness gates, publish buttons, and a dedicated graph page. The missing layer is not a new shell; it is a management model that can show published lifecycle state alongside the current thread draft.

Planning implication:

- `08-01` should normalize a stable skill lifecycle contract and stop relying on ad hoc thread/artifact inference alone.
- `08-02` should productize publish, auto-configuration, and explicit step binding without breaking existing DeerFlow enablement behavior.
- `08-03` should extend that lifecycle contract into real revision history, rollback, and governance-aware graph or discoverability views.

</research_summary>

<standard_stack>
## Standard Stack

- **Backend domain:** `backend/packages/harness/deerflow/domain/submarine/skill_studio.py`, `thread_state.py`, and a new lifecycle helper/store module are the right anchors.
- **Backend APIs:** `backend/app/gateway/routers/skills.py` already owns publish, enable, install, and graph routes and should remain the gateway surface.
- **Runtime routing:** `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`, `backend/packages/harness/deerflow/tools/builtins/task_tool.py`, and `backend/packages/harness/deerflow/domain/submarine/contracts.py`.
- **Persistence today:** thread-scoped artifact files under `/submarine/skill-studio/...`, installed skill files under `skills/custom/<skill-name>`, and enablement flags in `extensions_config.json`.
- **Frontend surfaces:** `skill-studio-dashboard.tsx`, `skill-studio-workbench-shell.tsx`, `skill-studio-workbench-panel.tsx`, `skill-graph.utils.ts`, `skill-studio-dashboard.utils.ts`, and `skill-studio-workbench.utils.ts`.
- **Verification:** backend `pytest` coverage for skill studio, publish, graph, loader, and routing; frontend `node:test` coverage for skill graph and skill-studio helpers; `corepack pnpm typecheck` as the integration gate.

</standard_stack>

<implementation_notes>
## Implementation Notes

### Existing lifecycle truth and the missing asset model

- `run_skill_studio()` already generates a complete draft workspace: `skill-draft.json`, `skill-package.json`, `SKILL.md`, `agents/openai.yaml`, `references/domain-rules.md`, `test-matrix.*`, `validation-report.*`, `publish-readiness.*`, and the installable `.skill` archive.
- `SubmarineSkillStudioState` in `thread_state.py` is still draft-oriented. It only stores fields such as `skill_name`, `validation_status`, `test_status`, `publish_status`, `package_archive_virtual_path`, and artifact pointers.
- Recommended planning anchor: keep thread state as the active draft workspace, but add a separate persisted skill lifecycle record keyed by `skill_name` or `skill_asset_id`. That record should become the home for published metadata, bindings, revision history, and rollback targets.

### Publish path and configuration implications

- `_install_skill_archive()` validates the archive, extracts it, and copies the resolved skill directory into `skills/custom/<skill-name>`.
- `_set_skill_enabled()` writes only one bit of management truth today: `skills.<skill_name>.enabled` inside `extensions_config.json`.
- `ExtensionsConfig` intentionally stays simple and backward-compatible. It does not currently define fields for version notes, revision lists, or step-binding rules.
- Recommended planning anchor: preserve `extensions_config.json` as the compatibility layer for enablement, but store richer lifecycle metadata in a separate project-local registry or sidecar metadata file instead of overloading `ExtensionsConfig`.

### Routing and explicit step binding implications

- `get_skills_prompt_section()` injects all enabled skills into the lead-agent prompt, and `task_tool` injects either the full enabled pool or an explicitly narrowed subset into delegated subagents.
- `_resolve_target_skills()` already validates explicit lists against the enabled pool, which is exactly the guardrail the user needs for configured bindings.
- `_SUBMARINE_SUBAGENT_ROUTING` already exposes concrete role ids and stages such as `geometry-preflight`, `solver-dispatch`, `scientific-verification`, and `result-reporting`.
- Recommended planning anchor: Phase 8 should persist bindings against those exact role ids and feed them back into the lead-agent routing prompt and/or execution-plan defaults, rather than inventing a second binding vocabulary.

### Graph implications

- `/api/skills/graph` returns summary counts, node metadata, relationships, and a focused related-skills list.
- `relationships.py` infers stage labels and relationships from token overlap plus explicit references inside `SKILL.md`. This is already useful for routing and impact context.
- The graph model currently carries `enabled`, `relationship_types`, `strongest_score`, and `reasons`, but it does not carry lifecycle metadata such as `revision_count`, `active_revision_id`, `rollback_target_id`, or configured `binding_count`.
- Recommended planning anchor: extend the graph response with lifecycle metadata from the new registry while keeping the existing relationship heuristics intact.

### Frontend implications

- The dashboard already frames Skill Studio as `Create / Evaluate / Connect` and surfaces graph overview metrics, focused related skills, and recent workbench entries.
- The workbench already shows publish gates and real publish actions (`发布并启用`, `覆盖发布`) plus a graph workbench and node inspector.
- Current frontend state derivation still depends heavily on thread search results, `submarine_skill_studio`, and artifact scanning. There is no dedicated query for published lifecycle records or project-level bindings.
- Recommended planning anchor: add a lifecycle management query model for published skills, then surface revision, enablement, and binding controls inside the current publish and graph surfaces rather than introducing a separate governance app.

### Risks and traps to avoid

- If revision history stays thread-bound, overwrite publish will keep erasing provenance and rollback will remain undefined.
- If bindings live only in UI state, later threads will not know about them and `target_skills` will stay a hidden power-user contract instead of a governed feature.
- If graph tries to present governance without a real lifecycle source of truth, publish badges, binding counts, and rollback state will drift out of sync.
- If Phase 8 reaches into the shared workspace shell again, it will reopen Phase 7 scope instead of extending the approved baseline.

</implementation_notes>

<validation_architecture>
## Validation Architecture

Phase 8 needs validation along four dimensions:

- **Lifecycle contract validation:** confirm draft generation emits a stable skill lifecycle payload and that thread state plus lifecycle registry stay synchronized.
- **Publish and auto-configuration validation:** confirm publish still installs into `skills/custom`, still writes enablement into `extensions_config.json`, and now also writes durable lifecycle metadata.
- **Binding and discoverability validation:** confirm configured bindings round-trip through APIs, appear in lead-agent guidance, and preserve the normal enabled-pool behavior when explicit bindings are absent.
- **Revision and governance validation:** confirm publish appends revisions, rollback restores a prior published snapshot, and graph or dashboard views surface revision and binding metadata without losing existing relationship semantics.

Recommended validation shape:

- Add backend tests for lifecycle registry persistence, publish-route lifecycle writes, rollback behavior, graph governance metadata, and lead-agent binding prompts.
- Extend frontend node tests around dashboard entries, readiness helpers, and graph view-model helpers so revision counts, active revision labels, and binding badges are deterministic.
- Keep `corepack pnpm typecheck` as the fast frontend integration gate and the existing backend publish/graph tests as the compatibility guardrail.
- Reserve manual visual review for the publish-management surface, binding editor clarity, and rollback-state presentation inside the current Skill Studio workbench.

</validation_architecture>

<sources>
## Sources

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/08-skill-studio-lifecycle-and-governance/08-CONTEXT.md`
- `.planning/phases/07-workspace-ux-and-navigation-system/07-CONTEXT.md`
- `.planning/phases/07-workspace-ux-and-navigation-system/07-UI-SPEC.md`
- `.planning/research/v1.1-deerflow-alignment.md`
- `backend/packages/harness/deerflow/domain/submarine/skill_studio.py`
- `backend/packages/harness/deerflow/agents/thread_state.py`
- `backend/app/gateway/routers/skills.py`
- `backend/packages/harness/deerflow/skills/loader.py`
- `backend/packages/harness/deerflow/skills/relationships.py`
- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- `backend/packages/harness/deerflow/tools/builtins/task_tool.py`
- `backend/packages/harness/deerflow/domain/submarine/contracts.py`
- `backend/tests/test_submarine_skill_studio_tool.py`
- `backend/tests/test_skills_publish_router.py`
- `backend/tests/test_skills_graph_router.py`
- `backend/tests/test_skill_relationships.py`
- `backend/tests/test_lead_agent_prompt_skill_routing.py`
- `frontend/src/app/workspace/skill-studio/[thread_id]/page.tsx`
- `frontend/src/core/skills/api.ts`
- `frontend/src/core/skills/hooks.ts`
- `frontend/src/components/workspace/skill-studio-dashboard.tsx`
- `frontend/src/components/workspace/skill-studio-dashboard.utils.ts`
- `frontend/src/components/workspace/skill-studio-workbench-shell.tsx`
- `frontend/src/components/workspace/skill-studio-workbench-panel.tsx`
- `frontend/src/components/workspace/skill-studio-workbench.utils.ts`
- `frontend/src/components/workspace/skill-graph.utils.ts`
- `frontend/src/components/workspace/skill-graph.utils.test.ts`
- `frontend/src/components/workspace/skill-studio-dashboard.utils.test.ts`
- `frontend/src/components/workspace/skill-studio-workbench.utils.test.ts`

</sources>

<metadata>
## Metadata

**Research date:** 2026-04-04
**Valid until:** Phase 8 materially changes the skill lifecycle contract or publish surface
**Status:** complete for planning

</metadata>

---

*Phase: 08-skill-studio-lifecycle-and-governance*
*Research completed: 2026-04-04*
