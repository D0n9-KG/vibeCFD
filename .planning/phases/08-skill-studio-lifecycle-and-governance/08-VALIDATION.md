---
phase: 08
slug: skill-studio-lifecycle-and-governance
status: ready_for_planning
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-04
updated: 2026-04-04
---

# Phase 08 - Validation Strategy

## Validation Goal

Prove that Phase 8 turns Skill Studio from a thread-scoped draft generator into a governed skill lifecycle product without breaking DeerFlow-compatible publish and discovery behavior.

The validation target is not only "a skill can still be published", but:

- draft generation and thread state now point at a stable lifecycle contract instead of only loose artifact paths,
- publish still installs and enables DeerFlow skills while also persisting lifecycle and binding metadata,
- explicit step bindings remain compatible with the existing `target_skills` runtime contract,
- revision history, rollback targets, and graph discoverability become visible and auditable after publish.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` + Node test runner + TypeScript typecheck |
| **Config file** | `backend/pyproject.toml`, `frontend/package.json`, `frontend/tsconfig.json` |
| **Quick run command** | `cd backend && uv run pytest tests/test_submarine_skill_studio_tool.py tests/test_skills_publish_router.py tests/test_skills_graph_router.py tests/test_skill_relationships.py tests/test_lead_agent_prompt_skill_routing.py && cd ../frontend && node --test src/components/workspace/skill-graph.utils.test.ts src/components/workspace/skill-studio-dashboard.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts && corepack pnpm typecheck` |
| **Full suite command** | `cd backend && uv run pytest tests/test_submarine_skill_studio_tool.py tests/test_skills_publish_router.py tests/test_skills_graph_router.py tests/test_skills_loader.py tests/test_skills_router.py tests/test_skill_relationships.py tests/test_lead_agent_prompt_skill_routing.py tests/test_skill_lifecycle_store.py && cd ../frontend && node --test src/components/workspace/skill-graph.utils.test.ts src/components/workspace/skill-studio-agent-options.test.ts src/components/workspace/skill-studio-dashboard.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts && corepack pnpm typecheck` |
| **Estimated runtime** | ~150 seconds |

---

## Sampling Rate

- **After every lifecycle-schema change:** Run `cd backend && uv run pytest tests/test_submarine_skill_studio_tool.py tests/test_skill_lifecycle_store.py`
- **After every publish or router change:** Run `cd backend && uv run pytest tests/test_skills_publish_router.py tests/test_skills_graph_router.py tests/test_lead_agent_prompt_skill_routing.py`
- **After every dashboard or workbench helper change:** Run `cd frontend && node --test src/components/workspace/skill-studio-dashboard.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts src/components/workspace/skill-graph.utils.test.ts && corepack pnpm typecheck`
- **After every plan:** Re-run the quick command
- **Before phase verification:** Re-run the full suite command
- **Max feedback latency:** 150 seconds

---

## Validation Dimensions

### Dimension 1: Draft Lifecycle Contract

Must validate:

- skill studio draft generation emits a stable lifecycle payload in addition to existing package artifacts
- `submarine_skill_studio` mirrors the lifecycle fields needed by the frontend
- dashboard and workbench helpers stop depending only on artifact-path inference

### Dimension 2: Publish and Auto-Configuration

Must validate:

- publish still installs the generated `.skill` archive into `skills/custom/<skill-name>`
- publish still writes enablement into `extensions_config.json`
- publish also persists lifecycle metadata that survives beyond the current thread

### Dimension 3: Explicit Binding and Discoverability

Must validate:

- configured bindings round-trip through backend APIs and frontend controls
- the lead agent can see project-level binding guidance and use exact role ids with `target_skills`
- enabled-pool discovery still works when no explicit binding is configured

### Dimension 4: Revision and Governance Visibility

Must validate:

- each publish appends revision metadata instead of collapsing to overwrite-only state
- rollback restores a prior published revision and updates active lifecycle metadata
- dashboard, publish, and graph surfaces show revision, binding, and discoverability state without losing existing relationship context

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | SKILL-01, SKILL-02 | backend lifecycle contract | `cd backend && uv run pytest tests/test_skill_lifecycle_store.py` | `backend/tests/test_skill_lifecycle_store.py` | pending |
| 08-01-02 | 01 | 1 | SKILL-01, SKILL-02 | draft artifact generation | `cd backend && uv run pytest tests/test_submarine_skill_studio_tool.py tests/test_skill_lifecycle_store.py` | `backend/tests/test_submarine_skill_studio_tool.py` | pending |
| 08-01-03 | 01 | 1 | SKILL-01, SKILL-02 | frontend lifecycle helpers | `cd frontend && node --test src/components/workspace/skill-studio-dashboard.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts && corepack pnpm typecheck` | `frontend/src/components/workspace/skill-studio-dashboard.utils.test.ts` | pending |
| 08-02-01 | 02 | 2 | SKILL-03 | publish and management API | `cd backend && uv run pytest tests/test_skills_publish_router.py tests/test_skills_router.py tests/test_skill_lifecycle_store.py` | `backend/tests/test_skills_publish_router.py` | pending |
| 08-02-02 | 02 | 2 | SKILL-03, SKILL-05 | binding prompt and routing guidance | `cd backend && uv run pytest tests/test_lead_agent_prompt_skill_routing.py tests/test_skills_router.py` | `backend/tests/test_lead_agent_prompt_skill_routing.py` | pending |
| 08-02-03 | 02 | 2 | SKILL-03, SKILL-05 | publish-management frontend flow | `cd frontend && node --test src/components/workspace/skill-studio-dashboard.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts && corepack pnpm typecheck` | `frontend/src/components/workspace/skill-studio-workbench.utils.test.ts` | pending |
| 08-03-01 | 03 | 3 | SKILL-04 | backend revision and rollback flow | `cd backend && uv run pytest tests/test_skills_publish_router.py tests/test_skill_lifecycle_store.py` | `backend/tests/test_skill_lifecycle_store.py` | pending |
| 08-03-02 | 03 | 3 | SKILL-04, SKILL-05 | graph governance metadata | `cd backend && uv run pytest tests/test_skills_graph_router.py tests/test_skill_relationships.py` | `backend/tests/test_skills_graph_router.py` | pending |
| 08-03-03 | 03 | 3 | SKILL-04, SKILL-05 | frontend revision and discoverability views | `cd frontend && node --test src/components/workspace/skill-graph.utils.test.ts src/components/workspace/skill-studio-dashboard.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts && corepack pnpm typecheck` | `frontend/src/components/workspace/skill-graph.utils.test.ts` | pending |

---

## Wave 0 Requirements

Existing backend and frontend test infrastructure already covers this phase:

- `uv run pytest` is already used for backend router and domain-contract tests
- `node:test` is already used for skill-studio and graph helper coverage
- `corepack pnpm typecheck` already exists as the frontend integration gate

Wave 0 only needs phase-specific test files to be added where the new lifecycle registry and governance helpers are introduced.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Publish confirmation makes it obvious whether the skill was only enabled globally or also bound to a specific step | SKILL-03, SKILL-05 | Requires judging UI wording and hierarchy | Open the publish surface, publish a skill with one explicit binding, and confirm the panel separately shows global enablement plus bound execution roles |
| Revision history and rollback stay understandable inside the existing lifecycle product | SKILL-04 | Requires evaluating ordering, labels, and control clarity | Open a skill with at least two revisions and confirm the active revision, rollback target, version note, and rollback action are all visible without leaving Skill Studio |
| Graph inspector adds governance context without hiding relationship reasoning | SKILL-05 | Requires visual judgment on density and explanation quality | Open the graph focus view and confirm the node inspector shows relationship reasons plus lifecycle badges such as enabled state, binding count, and revision count together |
| Draft versus published state remains easy to compare after a new publish | SKILL-04 | Requires seeing both thread draft and published asset context together | Generate a new draft from an existing skill, then confirm the workbench clearly shows which values come from the draft and which come from the active published revision |

---

## Evidence To Capture Before Phase Sign-Off

- one sample `skills/custom/.skill-studio-registry.json` file showing publish metadata, enable state, and at least one explicit binding
- one publish response payload showing lifecycle metadata after install and enable
- one screenshot of the Skill Studio publish surface with revision history and step-binding state visible
- one screenshot of the graph inspector showing relationship reasons plus governance badges
- one rollback response or workbench state capture showing `active_revision_id` changed after rollback

---

## Exit Criteria

Phase 8 is not ready for execution sign-off until all of the following are true:

- `SKILL-01` is backed by a dedicated workbench that still co-creates DeerFlow-compatible skills but now points at a stable lifecycle contract
- `SKILL-02` is backed by package-complete artifacts plus lifecycle metadata that do not require manual patching
- `SKILL-03` is backed by publish, install, enable, and project-level management behavior without manual filesystem surgery
- `SKILL-04` is backed by visible revisions, version notes, active revision tracking, and rollback targets
- `SKILL-05` is backed by enabled-pool discoverability plus explicit binding visibility inside management and graph views
- `nyquist_compliant: true` remains valid because every task maps to deterministic automated checks or explicit manual verification
