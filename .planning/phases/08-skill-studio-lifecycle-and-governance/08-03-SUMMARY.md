---
phase: 08-skill-studio-lifecycle-and-governance
plan: 03
subsystem: revision-history-and-governance-views
tags: [skill-studio, lifecycle, rollback, revisions, governance, graph, dashboard, deerflow]
requires:
  - phase: 08-01
    provides: lifecycle registry contract, lifecycle thread-state mirrors, skill-lifecycle.json draft artifacts
  - phase: 08-02
    provides: publish-management APIs, explicit role bindings, inline workbench governance controls
provides:
  - persisted published revision archives and rollback against real skill snapshots
  - lifecycle and graph governance metadata for revision/binding/discoverability visibility
  - dashboard and workbench revision history plus rollback actions for project-local skills
affects:
  - Phase 08 closure for SKILL-04 and SKILL-05
  - later-thread discoverability and governed skill reuse
  - future Phase 09 deployment hardening around project-local skill assets
tech-stack:
  added: []
  patterns:
    - snapshot-backed custom skill rollback
    - governance metadata enrichment without relationship-semantic regression
    - lifecycle-detail-driven publish/workbench rendering
key-files:
  modified:
    - backend/app/gateway/routers/skills.py
    - backend/packages/harness/deerflow/domain/submarine/skill_lifecycle.py
    - backend/packages/harness/deerflow/skills/relationships.py
    - backend/tests/test_skill_lifecycle_store.py
    - backend/tests/test_skills_publish_router.py
    - backend/tests/test_skills_graph_router.py
    - backend/tests/test_skill_relationships.py
    - frontend/src/core/skills/api.ts
    - frontend/src/core/skills/hooks.ts
    - frontend/src/components/workspace/skill-graph.utils.ts
    - frontend/src/components/workspace/skill-graph.utils.test.ts
    - frontend/src/components/workspace/skill-studio-dashboard.tsx
    - frontend/src/components/workspace/skill-studio-dashboard.utils.ts
    - frontend/src/components/workspace/skill-studio-dashboard.utils.test.ts
    - frontend/src/components/workspace/skill-studio-workbench-panel.tsx
    - frontend/src/components/workspace/skill-studio-workbench.utils.ts
    - frontend/src/components/workspace/skill-studio-workbench.utils.test.ts
key-decisions:
  - "Treat revision history as a skill-asset concern by snapshotting `.skill` archives under `skills/custom/<skill-name>/.revisions/`."
  - "Enrich graph and lifecycle views with governance metadata while preserving the existing relationship edges, scores, and reasons."
patterns-established:
  - "Rollback pattern: restore a saved archive, preserve `.revisions` across overwrites, then reapply the saved revision metadata and enable flag."
  - "Governance-view pattern: dashboard, workbench, and graph inspector consume the same lifecycle-backed revision, binding, and publish metadata."
requirements-completed: [SKILL-04, SKILL-05]
requirements-progress: []
duration: 41 min
completed: 2026-04-04
---

# Phase 8 Plan 03: Add Revision History, Rollback, and Post-Publish Discoverability Plus Governance Views Summary

**Real revision archives, rollback against saved snapshots, governance-enriched APIs, and frontend visibility for revision/binding state**

## Performance

- **Duration:** 41 min
- **Started:** 2026-04-04T21:31:29+08:00
- **Completed:** 2026-04-04T22:12:04+08:00
- **Tasks:** 3
- **Files modified:** 17

## Accomplishments

- Persisted every publish as a real revision archive under `skills/custom/<skill-name>/.revisions/<revision_id>.skill`, with lifecycle records now tracking active revision ids, rollback targets, version notes, bindings, and publish metadata per revision.
- Added `POST /api/skills/{skill_name}/rollback` so rollback restores an actual saved snapshot into the project-local DeerFlow custom skill directory instead of only mutating lifecycle labels.
- Enriched lifecycle and graph APIs with governance fields such as `revision_count`, `binding_count`, `active_revision_id`, `rollback_target_id`, and `last_published_at` while keeping graph relationship semantics untouched.
- Updated the Skill Studio dashboard, publish workbench, and graph helpers so users can inspect revision history, rollback targets, binding counts, and post-publish governance state directly in the current product surfaces.

## Verification

- `cd backend && uv run pytest tests/test_skill_lifecycle_store.py tests/test_skills_publish_router.py`
- `cd backend && uv run pytest tests/test_skills_graph_router.py tests/test_skill_relationships.py`
- `cd frontend && node --test src/components/workspace/skill-graph.utils.test.ts src/components/workspace/skill-studio-dashboard.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts`
- `cd frontend && corepack pnpm typecheck`

## Files Created/Modified

- `backend/app/gateway/routers/skills.py` - Added rollback API, revision archive persistence, lifecycle detail responses, and governance-enriched lifecycle summaries.
- `backend/packages/harness/deerflow/domain/submarine/skill_lifecycle.py` - Added revision path/id helpers, active-revision syncing helpers, and guarded merge behavior for publish versus management updates.
- `backend/packages/harness/deerflow/skills/relationships.py` - Merged lifecycle governance metadata into graph nodes and focused related-skill items without changing relationship analysis logic.
- `backend/tests/test_skill_lifecycle_store.py` - Covers revision ids, hidden revision archive paths, and rollback-target state across publishes.
- `backend/tests/test_skills_publish_router.py` - Covers double-publish revision history, preserved `.revisions`, and rollback restoring the first published snapshot.
- `backend/tests/test_skills_graph_router.py` - Covers governance metadata exposure through graph summary and focus responses.
- `backend/tests/test_skill_relationships.py` - Covers lifecycle governance metadata on relationship-analysis dataclasses.
- `frontend/src/core/skills/api.ts` - Added rollback client support and extended lifecycle/graph response types with revision and governance fields.
- `frontend/src/core/skills/hooks.ts` - Added rollback mutation plus lifecycle/graph invalidation after rollback.
- `frontend/src/components/workspace/skill-graph.utils.ts` - Added raw skill ids and governance metadata to focused items and graph workbench nodes.
- `frontend/src/components/workspace/skill-graph.utils.test.ts` - Covers governance metadata retention and raw-id graph node behavior.
- `frontend/src/components/workspace/skill-studio-dashboard.tsx` - Surfaces lifecycle governance metrics and uses lifecycle-backed skill ids for focused graph lookups.
- `frontend/src/components/workspace/skill-studio-dashboard.utils.ts` - Extends dashboard entries with revision counts, rollback targets, binding counts, and publish timestamps.
- `frontend/src/components/workspace/skill-studio-dashboard.utils.test.ts` - Covers lifecycle-backed dashboard governance fields.
- `frontend/src/components/workspace/skill-studio-workbench-panel.tsx` - Adds lifecycle detail loading, revision history rendering, rollback actions, and governance metrics in the graph inspector.
- `frontend/src/components/workspace/skill-studio-workbench.utils.ts` - Extends publish-panel view models with revision and rollback metadata.
- `frontend/src/components/workspace/skill-studio-workbench.utils.test.ts` - Covers publish-panel revision counts, binding counts, and rollback targets.

## Decisions Made

- Preserve revision archives during overwrite publishes by copying `.revisions` out of the target skill before replacement and restoring it afterward.
- Keep graph and dashboard discoverability grounded in the same lifecycle registry data used by the workbench rather than introducing a second governance store.

## Deviations from Plan

None. The shipped work matches the planned revision-storage, rollback, API-enrichment, and frontend-governance scope.

## Issues Encountered

- Importing lifecycle helpers directly into the relationship analyzer created a circular import with the skill loader, so the lifecycle imports were made lazy inside the analysis path.
- Custom skill lookup for rollback was still relying on the general app-config skill search path, so it was tightened to use the project-local DeerFlow skills root explicitly.

## User Setup Required

None.

## Next Phase Readiness

- Phase 8 is now complete: custom skills can be created, published, versioned, rolled back, and inspected through lifecycle plus graph surfaces.
- The next milestone step is Phase 09 planning and execution for runtime isolation and deployment hardening.

---
*Phase: 08-skill-studio-lifecycle-and-governance*
*Completed: 2026-04-04*
