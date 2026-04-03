# Phase 7: Workspace UX and Navigation System - Research

**Researched:** 2026-04-03
**Domain:** Shared workspace IA, page-shell primitives, responsive workbench layouts
**Confidence:** MEDIUM-HIGH

<user_constraints>
## User Constraints (from ROADMAP.md / REQUIREMENTS.md / approved discussion)

- `UX-01`: one coherent IA across chat, submarine, skill studio, and agents.
- `UX-02`: key submarine and skill tasks must remain operable on desktop and laptop without losing primary actions, status context, or artifacts.
- `UX-03`: shared page shells, navigation, and feedback states must replace page-by-page drift.
- `UX-04`: Chinese copy, spacing, readability, loading states, and focus states must feel intentional.
- The user rejected duplicated left-side rails and explicitly wants a merged contextual sidebar.
- The user explicitly asked for complete process visibility with a cleaner, less crowded default viewport.
- The user explicitly approved a real-time runtime monitor inside the workbench and a true graph-style `Skill 图谱`.

</user_constraints>

<research_summary>
## Summary

Phase 7 can be executed as a frontend-shell phase without backend contract changes because the necessary state already exists in the current frontend runtime and skill data hooks. The real work is reorganizing how those truths are presented and navigated.

Key findings:

- The root workspace shell already exists in `frontend/src/app/workspace/layout.tsx` and should remain the mount point. Replacing it would create avoidable risk around providers, command palette behavior, and query lifetime.
- The current left rail is incomplete and conceptually split. `workspace-nav-chat-list.tsx` only exposes submarine, skill studio, and chats, while conversation history is handled separately inside `workspace-sidebar.tsx`. This is exactly the duplication the user called out.
- The current submarine and skill-studio shells already have responsive helper modules, but the actual surface implementations still bury too much responsibility inside large workbench components. The best Phase 7 move is to extract shared shell primitives and page-level subviews, not to re-platform the data layer.
- Real-time monitoring data is already available from `thread.values.submarine_runtime`, artifact virtual paths, and timeline/activity payloads. The approved overview/runtime split can be implemented by reorganizing existing truth, not inventing a new API.
- Skill graph data is already available through `useSkillGraph()` plus `skill-graph.utils.ts`. The graph page can be productized by adding focus, filter, and inspector presentation around the existing data contract.
- Existing tests already cover layout helpers and pure utilities via `node:test`; this is enough infrastructure to validate new shell helpers, pane ids, graph-filter behavior, and compact-state logic while using manual visual review for final polish.

</research_summary>

<standard_stack>
## Standard Stack

- **Framework:** Next.js 16 App Router + React 19 + TypeScript 5.8
- **Styling:** Tailwind CSS v4 + shadcn/ui + existing workspace chrome helpers
- **Panels:** `react-resizable-panels` for desktop splits and persisted pane sizes
- **Data:** `useThreadStream`, `useThreads`, `useArtifactContent`, `useSkillGraph`, and TanStack Query
- **Graph helpers:** existing `skill-graph.utils.ts`, optionally paired with current frontend graph dependencies where useful
- **Verification:** `node --test` for helper contracts and `corepack pnpm typecheck` for integration-level safety

</standard_stack>

<implementation_notes>
## Implementation Notes

### Shared shell direction
- Keep `SidebarProvider` as the outer shell.
- Introduce a route-aware workspace surface registry so the same shared shell can know which top-level surface is active.
- Treat the activity bar as fixed navigation and the adjacent sidebar as contextual content only.

### Submarine direction
- Keep thread bootstrap, notifications, and artifact drawer ownership in the route page.
- Move page chrome and subview framing out of `SubmarinePipeline`.
- Reuse existing runtime stage cards, artifact access, and report rendering logic within the new `总览 / 运行时 / 产物 / 报告` structure.

### Skill Studio direction
- Keep current thread stream, agent selection, and artifact-backed readiness data flow.
- Convert the giant panel into a shell plus view-specific sections.
- Build the `图谱` page around focused-node graph interactions rather than a single all-in-one dashboard.

### Chat and agent direction
- Re-skin existing chat and agent entry points into the shared shell instead of inventing new data flows.
- Keep the current agent creation bootstrap flow, but place it inside the same workspace language and responsive rules as the other surfaces.

</implementation_notes>

<validation_architecture>
## Validation Architecture

Phase 7 needs validation along four dimensions:

- **Shared-shell contract validation:** confirm one registry drives top-level navigation, pane ids, and contextual-sidebar behavior.
- **Responsive layout validation:** confirm desktop split, laptop degradation, and chat-rail behavior remain deterministic through pure helper tests.
- **Surface-behavior validation:** confirm submarine monitoring summaries, skill graph filters/focus, and chat/agent shell states are present in the right page subviews.
- **Polish validation:** confirm Chinese copy cleanup, focus-visible styling, loading/empty/error states, and keyboard navigation through manual inspection plus targeted helper tests.

Recommended validation shape:

- Extend node tests around shell tokens, pane ids, responsive helper outputs, graph-filter helpers, and compact-state mappers.
- Keep `corepack pnpm typecheck` as the fast global correctness gate for the frontend.
- Use manual visual review for desktop and laptop widths, keyboard focus order, runtime monitoring visibility, and graph-page degradation rules.

</validation_architecture>

<sources>
## Sources

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/phases/07-workspace-ux-and-navigation-system/07-UI-SPEC.md`
- `.planning/phases/07-workspace-ux-and-navigation-system/07-wireframes.html`
- `docs/archive/superpowers/specs/2026-03-30-vibecfd-frontend-redesign-design.md`
- `frontend/src/app/workspace/layout.tsx`
- `frontend/src/components/workspace/workspace-sidebar.tsx`
- `frontend/src/components/workspace/workspace-nav-chat-list.tsx`
- `frontend/src/components/workspace/workspace-sidebar-shell.ts`
- `frontend/src/components/workspace/submarine-pipeline.tsx`
- `frontend/src/components/workspace/skill-studio-workbench-panel.tsx`
- `frontend/src/app/workspace/submarine/submarine-workbench-layout.ts`
- `frontend/src/app/workspace/skill-studio/skill-studio-workbench-layout.ts`
- `frontend/src/app/workspace/chats/chat-layout.ts`

</sources>

<metadata>
## Metadata

**Research date:** 2026-04-03
**Valid until:** Phase 7 execution materially changes the shell structure
**Status:** complete for planning

</metadata>

---

*Phase: 07-workspace-ux-and-navigation-system*
*Research completed: 2026-04-03*
