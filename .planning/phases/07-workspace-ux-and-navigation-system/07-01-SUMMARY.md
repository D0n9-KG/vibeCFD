---
phase: 07-workspace-ux-and-navigation-system
plan: 01
subsystem: ui
tags: [workspace, navigation, sidebar, layout, responsive]
requires:
  - phase: 06-03
    provides: submarine cockpit runtime/report truth that phase 7 must preserve while reshaping the shell
provides:
  - Shared workspace surface registry with fixed top-level entries and active-path helpers
  - Fixed activity bar plus one contextual sidebar shell for workspace surfaces
  - Stable shared pane ids and shell guardrail tests for later workspace rebuilds
affects: [phase-07-workspace-ux-and-navigation-system, workspace-shell, submarine, skill-studio, chats, agents]
tech-stack:
  added: []
  patterns:
    - "Drive workspace shell state from one shared surface registry instead of duplicating route labels and hrefs in multiple components."
    - "Reserve the fixed activity bar for global surface switching and keep contextual objects/actions in a single adjacent sidebar column."
key-files:
  created:
    - .planning/phases/07-workspace-ux-and-navigation-system/07-01-SUMMARY.md
    - frontend/src/components/workspace/workspace-activity-bar.tsx
    - frontend/src/components/workspace/workspace-surface-config.ts
    - frontend/src/components/workspace/workspace-surface-config.test.ts
  modified:
    - frontend/src/app/workspace/page.tsx
    - frontend/src/components/workspace/workspace-header.tsx
    - frontend/src/components/workspace/workspace-nav-chat-list.tsx
    - frontend/src/components/workspace/workspace-nav-menu.tsx
    - frontend/src/components/workspace/workspace-resizable-ids.ts
    - frontend/src/components/workspace/workspace-resizable-ids.test.ts
    - frontend/src/components/workspace/workspace-sidebar-shell.ts
    - frontend/src/components/workspace/workspace-sidebar-shell.test.ts
    - frontend/src/components/workspace/workspace-sidebar.tsx
key-decisions:
  - "Use `WORKSPACE_SURFACES` as the shared source of truth for workspace labels, hrefs, and active-path matching."
  - "Let the activity bar own surface switching and settings, while the adjacent contextual sidebar focuses on surface-specific quick links and recent work threads."
  - "Export shared pane ids before the workbench rebuild so later plans can reuse stable persistence boundaries instead of inventing page-local handles."
patterns-established:
  - "Workspace shell routing should derive the active surface through `matchWorkspaceSurface()` instead of pathname checks spread across multiple components."
  - "Shared shell chrome belongs in `workspace-sidebar-shell.ts`, while resize persistence ids belong in `workspace-resizable-ids.ts`."
requirements-completed: [UX-01, UX-03]
duration: "~12 min for shared IA, shell composition, and pane guardrails"
completed: 2026-04-03
---

# Phase 7 Plan 01: Extract the Shared Workspace IA, Activity Bar, and Shell Primitives Summary

**Shared workspace surface registry, fixed activity bar, and contextual sidebar primitives now define one route-aware shell for submarine, skill studio, chats, and agents.**

## Performance

- **Duration:** ~12 min for shared IA, shell composition, and pane guardrails
- **Started:** 2026-04-03T15:39:00+08:00
- **Completed:** 2026-04-03T15:51:21+08:00
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments

- Added `WORKSPACE_SURFACES` plus route-matching helpers so workspace labels, hrefs, and mock-aware Skill Studio routing come from one registry.
- Built `WorkspaceActivityBar` and rewired the shared sidebar into `activity bar + contextual sidebar`, with compact-mode support and settings access preserved in the bottom rail.
- Locked shared pane ids and shell guardrails with node tests before submarine, skill-studio, chat, and agent pages start rebuilding against the new shell.

## Verification

- `cd frontend && node --test src/components/workspace/workspace-surface-config.test.ts`
  - Result: passed
- `cd frontend && node --test src/components/workspace/workspace-sidebar-shell.test.ts src/components/workspace/workspace-resizable-ids.test.ts`
  - Result: passed
- `cd frontend && corepack pnpm typecheck`
  - Result: passed

## Task Commits

Each task was committed atomically:

1. **Task 1: Create the route-aware workspace surface registry and fixed activity bar** - `1a7dd22` (feat)
2. **Task 2: Turn the left side into one contextual sidebar beside the activity bar** - `41aebfc` (feat)
3. **Task 3: Lock pane identifiers, persistence boundaries, and shell helper tests** - `362a12e` (test)

**Plan metadata:** Pending plan-closeout commit

## Files Created/Modified

- `frontend/src/components/workspace/workspace-surface-config.ts` - defines the shared workspace registry, default hrefs, and active-path helpers.
- `frontend/src/components/workspace/workspace-activity-bar.tsx` - renders the fixed surface switcher and bottom settings affordance for desktop and compact modes.
- `frontend/src/components/workspace/workspace-sidebar.tsx` - composes the shared sidebar as one activity bar plus one contextual sidebar column.
- `frontend/src/components/workspace/workspace-header.tsx` - reframes the contextual header around the active surface and compact activity-bar presentation.
- `frontend/src/components/workspace/workspace-nav-chat-list.tsx` - converts the old split nav into surface-aware quick links and recent work-thread context.
- `frontend/src/components/workspace/workspace-nav-menu.tsx` - supports an icon-only settings trigger inside the activity bar.
- `frontend/src/components/workspace/workspace-sidebar-shell.ts` - exports explicit activity-bar/context-sidebar chrome tokens for later plans.
- `frontend/src/components/workspace/workspace-resizable-ids.ts` - adds shared shell pane ids for activity bar, context sidebar, main pane, and chat rail.

## Decisions Made

- One surface registry now drives both route resolution and shell labelling so later pages do not reintroduce drift by hardcoding their own top-level entries.
- The workspace settings trigger now belongs to the activity bar, which keeps the contextual sidebar focused on surface-specific objects and actions.
- Shared shell pane ids shipped before any workbench-specific layout rebuild so desktop/laptop persistence can stay stable across waves 2 and 3.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

- Wave 2 can rebuild submarine and skill-studio pages against a stable shared shell instead of inventing their own surface registry, sidebar layout, or pane ids.
- The remaining Phase 7 work should reuse the new activity-bar/context-sidebar contract and avoid reintroducing top-level nav duplication.

---
*Phase: 07-workspace-ux-and-navigation-system*
*Completed: 2026-04-03*
