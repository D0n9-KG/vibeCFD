---
phase: 08-skill-studio-lifecycle-and-governance
plan: 02
subsystem: publish-management
tags: [skill-studio, publish, lifecycle, bindings, workbench, deerflow]
requires:
  - phase: 08-01
    provides: lifecycle registry contract, lifecycle thread-state mirrors, skill-lifecycle.json draft artifacts
provides:
  - publish and lifecycle management APIs for project-local DeerFlow skills
  - lead-agent prompt guidance for explicit project-level role bindings
  - Skill Studio publish-surface controls for enablement, version notes, and binding targets
affects:
  - phase-08-03 revision history and rollback flows
  - later-thread lead-agent routing for specialized submarine roles
  - dashboard and workbench lifecycle helper consumers
tech-stack:
  added: []
  patterns:
    - registry-backed publish management
    - explicit role-to-skill binding persistence
    - lifecycle-aware workbench mutation invalidation
key-files:
  modified:
    - backend/app/gateway/routers/skills.py
    - backend/packages/harness/deerflow/domain/submarine/skill_lifecycle.py
    - backend/packages/harness/deerflow/agents/lead_agent/prompt.py
    - backend/tests/test_skill_lifecycle_store.py
    - backend/tests/test_skills_publish_router.py
    - backend/tests/test_skills_router.py
    - backend/tests/test_lead_agent_prompt_skill_routing.py
    - frontend/src/core/skills/api.ts
    - frontend/src/core/skills/hooks.ts
    - frontend/src/components/workspace/skill-studio-dashboard.utils.ts
    - frontend/src/components/workspace/skill-studio-dashboard.utils.test.ts
    - frontend/src/components/workspace/skill-studio-workbench-panel.tsx
    - frontend/src/components/workspace/skill-studio-workbench.utils.ts
    - frontend/src/components/workspace/skill-studio-workbench.utils.test.ts
key-decisions:
  - "Keep enablement compatible with DeerFlow's existing extensions_config.json path, but persist richer lifecycle metadata in the registry."
  - "Treat explicit role bindings as a governed layer on top of the normal enabled skill pool rather than a replacement for default discoverability."
patterns-established:
  - "Lifecycle API pattern: publish, list, detail, and update all normalize through one shared lifecycle merge path."
  - "Workbench governance pattern: publish surface edits enablement, version notes, and binding targets inline instead of sending users to a separate admin page."
requirements-completed: [SKILL-03]
requirements-progress:
  - SKILL-05 remains open for revision history, rollback visibility, and graph/dashboard governance surfacing in 08-03.
duration: 35 min
completed: 2026-04-04
---

# Phase 8 Plan 02: Add Publish, Auto-Configure, and Management Flows for Project-Local DeerFlow Skills Summary

**Lifecycle-aware publish and management APIs, prompt-side explicit binding guidance, and an inline Skill Studio governance surface**

## Performance

- **Duration:** 35 min
- **Started:** 2026-04-04T20:56:00+08:00
- **Completed:** 2026-04-04T21:31:29+08:00
- **Tasks:** 3
- **Files modified:** 14

## Accomplishments

- Extended `/api/skills/publish` so publish persists `version_note`, `binding_targets`, publish timestamps, and project-level enabled state into the lifecycle registry without breaking the existing install-and-enable path.
- Added lifecycle management routes for list, detail, and update flows so the frontend can inspect and edit project-local skill governance state without re-publishing.
- Injected project-level explicit role bindings into the lead-agent prompt through a new `<project_skill_bindings>` block, preserving graph-assisted `target_skills` routing while making curated bindings visible in later threads.
- Added lifecycle client hooks plus publish-panel controls for enablement, version notes, and explicit role bindings directly inside the current Skill Studio publish surface.

## Verification

- `cd backend && uv run pytest tests/test_skills_publish_router.py tests/test_skills_router.py tests/test_skill_lifecycle_store.py tests/test_lead_agent_prompt_skill_routing.py`
- `cd frontend && node --test src/components/workspace/skill-studio-dashboard.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts`
- `cd frontend && corepack pnpm typecheck`

## Files Created/Modified

- `backend/app/gateway/routers/skills.py` - Added lifecycle summary/detail/update APIs and publish-time registry persistence.
- `backend/packages/harness/deerflow/domain/submarine/skill_lifecycle.py` - Added lifecycle record loading, timestamp helpers, and shared merge logic for publish/update flows.
- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py` - Added project-level explicit binding guidance for later subagent routing.
- `backend/tests/test_skill_lifecycle_store.py` - Covers lifecycle merge behavior for binding and publish metadata.
- `backend/tests/test_skills_publish_router.py` - Covers publish-time lifecycle persistence and overwrite metadata updates.
- `backend/tests/test_skills_router.py` - Covers lifecycle list/detail/update round trips.
- `backend/tests/test_lead_agent_prompt_skill_routing.py` - Covers the new `<project_skill_bindings>` prompt section.
- `frontend/src/core/skills/api.ts` - Added lifecycle query/update clients and extended publish payloads with management fields.
- `frontend/src/core/skills/hooks.ts` - Added lifecycle queries, lifecycle updates, and query invalidation for publish-management flows.
- `frontend/src/components/workspace/skill-studio-dashboard.utils.ts` - Lets dashboard entries prefer lifecycle summaries when available.
- `frontend/src/components/workspace/skill-studio-dashboard.utils.test.ts` - Covers lifecycle-summary precedence for explicit bindings.
- `frontend/src/components/workspace/skill-studio-workbench.utils.ts` - Added publish-panel lifecycle view-model helpers and canonical role-binding builders.
- `frontend/src/components/workspace/skill-studio-workbench.utils.test.ts` - Covers binding helpers and publish-panel defaults without explicit bindings.
- `frontend/src/components/workspace/skill-studio-workbench-panel.tsx` - Added inline governance controls for enablement, version notes, binding targets, and lifecycle saves.

## Decisions Made

- Keep the publish surface inside the existing Skill Studio workbench rather than branching into a separate governance screen.
- Use the exact submarine role ids (`task-intelligence`, `geometry-preflight`, `solver-dispatch`, `scientific-study`, `experiment-compare`, `scientific-verification`, `result-reporting`, `scientific-followup`) as the binding vocabulary end-to-end.

## Deviations from Plan

None. The implementation matched the planned publish-management scope and left rollback/history work for 08-03.

## Issues Encountered

- `skills/{skill_name}` routing would have shadowed the new lifecycle detail endpoints, so the new lifecycle routes had to be defined ahead of the generic skill detail route.
- Router tests needed an explicit temp-root `load_skills()` patch because lifecycle listing depends on the router's imported skill loader, not just the publish helper path patch.

## User Setup Required

None.

## Next Phase Readiness

- Plan 08-03 can now append real revisions and implement rollback on top of an already-stable lifecycle API and workbench management surface.
- The frontend already exposes active revision placeholders, published path metadata, and explicit binding controls, so 08-03 can focus on history, rollback, and governance visibility rather than first-time publish UX.

---
*Phase: 08-skill-studio-lifecycle-and-governance*
*Completed: 2026-04-04*
