# Phase 7: Workspace UX and Navigation System - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 rebuilds the shared workspace information architecture and page shells across the existing frontend so the product feels like one coherent workbench instead of several adjacent tools.

The phase covers the shared workspace entry model, left-side navigation, page shell primitives, desktop and laptop responsive behavior, and the core page layouts for submarine, skill studio, chat, and agent surfaces. It must keep the operator-facing submarine cockpit and skill workbench truthful and readable while preserving existing routing, providers, streaming hooks, and artifact-backed workflows.

This phase does not productize the full skill lifecycle, change backend runtime semantics, or attempt a broad architecture decomposition beyond what is necessary to land the new workspace shell and page-level UX contracts.

</domain>

<decisions>
## Implementation Decisions

### Shared workspace IA
- **D-01:** The workspace must use one top-level model: `Activity Bar + contextual sidebar + main work area + optional chat rail`.
- **D-02:** The top-level entries are fixed for this phase: `仿真`, `Skill Studio`, `对话`, `智能体`.
- **D-03:** The left-side functional navigation and the conversation-management sidebar must not exist as separate, competing sidebars. Their responsibilities must be merged into one contextual left column per surface.

### Page density and hierarchy
- **D-04:** The UI should show the full process truth, but the default viewport must remain clean and calm. Do not stack every module into one page.
- **D-05:** If a surface contains too many responsibilities, split it into navigable subpages or tabs rather than forcing one long mixed screen.
- **D-06:** Explanatory copy around obvious controls is unnecessary noise. Avoid descriptive text for things like the chat input itself unless the copy explains domain-specific state or constraints.

### Submarine workbench
- **D-07:** The submarine cockpit remains the primary operator surface. Chat supports it, but does not replace it.
- **D-08:** Users must be able to monitor runtime progress from the workbench in real time. The default overview should expose a compact live monitor summary, and a dedicated runtime view should carry the full process trace.
- **D-09:** Scientific/runtime truth must stay visible in-workbench, including current stage, gate state, evidence context, artifacts, and report surfaces.
- **D-10:** Submarine content should separate into `总览`, `运行时`, `产物`, and `报告` rather than keeping every artifact, stage, and report block in one canvas.

### Skill Studio
- **D-11:** Skill Studio should separate `总览`, `构建`, `校验`, `测试`, `发布`, and `图谱` so the workbench stays readable without hiding lifecycle steps.
- **D-12:** The `图谱` page is a real skill graph, not a placeholder block list or generic relationship panel.
- **D-13:** The graph should default to one-hop context, allow two-hop expansion on demand, preserve a focus node, and expose typed relation filters plus a detail panel.

### Chat, agents, and shared quality
- **D-14:** Chat and agent surfaces must adopt the same shell language as submarine and skill studio instead of feeling like unrelated mini-apps.
- **D-15:** Chinese-first copy, spacing, loading states, empty states, and focus behavior should feel deliberate and consistent across all redesigned workspace surfaces.
- **D-16:** Desktop and laptop widths are both first-class. Narrower layouts should degrade into drawers, sheets, or stacked panels, not simply lose monitoring, graph, or artifact access.

### the agent's Discretion
- Exact component decomposition, helper naming, and visual token extraction as long as the approved shell model and information hierarchy are preserved.
- Exact graph rendering technique as long as it remains a real graph view with focus, filtering, and detail inspection.
- Exact tab implementations as long as the phase-approved page boundaries stay intact and the runtime/chat/data truths remain visible.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and phase anchors
- `.planning/PROJECT.md` - current milestone promise, brownfield constraints, and the product value that the redesign must preserve.
- `.planning/ROADMAP.md` - Phase 7 goal, UX requirement mapping, and the intended 3-plan split.
- `.planning/REQUIREMENTS.md` - `UX-01`, `UX-02`, `UX-03`, and `UX-04` define the success boundary for this phase.
- `.planning/STATE.md` - current handoff state before planning.

### Approved Phase 7 design assets
- `.planning/phases/07-workspace-ux-and-navigation-system/07-UI-SPEC.md` - locked visual and interaction contract for Phase 7.
- `.planning/phases/07-workspace-ux-and-navigation-system/07-wireframes.html` - low-fidelity but approved page shells and state layouts.

### Prior design and implementation context
- `docs/archive/superpowers/specs/2026-03-30-vibecfd-frontend-redesign-design.md` - pre-existing redesign direction that already established the activity-bar and workbench-shell direction.
- `.planning/phases/06-research-delivery-workbench/06-CONTEXT.md` - carry-forward decision that submarine truth must stay cockpit-visible and should not collapse into generic chat.

### Current frontend shell and workspace implementation
- `frontend/src/app/workspace/layout.tsx` - current shared workspace provider and sidebar mount point.
- `frontend/src/app/workspace/page.tsx` - default workspace route entry.
- `frontend/src/components/workspace/workspace-sidebar.tsx` - current left rail composition.
- `frontend/src/components/workspace/workspace-header.tsx` - current sidebar header and quick action area.
- `frontend/src/components/workspace/workspace-nav-chat-list.tsx` - current top-level workspace navigation.
- `frontend/src/components/workspace/workspace-nav-menu.tsx` - current footer menu and settings affordance.
- `frontend/src/components/workspace/workspace-sidebar-shell.ts` - current shell tokens and sidebar chrome definitions.

### Current surface implementations that Phase 7 must reshape
- `frontend/src/components/workspace/submarine-pipeline.tsx` - current submarine cockpit monolith.
- `frontend/src/app/workspace/submarine/[thread_id]/page.tsx` - submarine route shell and header behavior.
- `frontend/src/app/workspace/submarine/submarine-workbench-layout.ts` - current submarine desktop/laptop layout helper.
- `frontend/src/components/workspace/skill-studio-workbench-panel.tsx` - current skill-studio workbench monolith.
- `frontend/src/app/workspace/skill-studio/[thread_id]/page.tsx` - skill-studio route shell and chat rail behavior.
- `frontend/src/app/workspace/skill-studio/skill-studio-workbench-layout.ts` - current skill-studio desktop/laptop layout helper.
- `frontend/src/app/workspace/chats/page.tsx` - current chat gallery page.
- `frontend/src/app/workspace/agents/page.tsx` - current agent gallery page.
- `frontend/src/app/workspace/agents/new/page.tsx` - current agent creation flow.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/app/workspace/layout.tsx` already provides the shared `SidebarProvider`, query client, command palette, and toaster shell. Phase 7 should preserve that root instead of inventing a second workspace mount.
- `frontend/src/components/workspace/workspace-sidebar-shell.ts` already centralizes workspace chrome tokens, making it the natural place to normalize shared shell styling instead of scattering classes again.
- `frontend/src/app/workspace/submarine/submarine-workbench-layout.ts`, `frontend/src/app/workspace/skill-studio/skill-studio-workbench-layout.ts`, and `frontend/src/app/workspace/chats/chat-layout.ts` already encapsulate some responsive decisions in testable helpers.
- `frontend/src/components/workspace/skill-graph.utils.ts` and `frontend/src/components/workspace/skill-studio-workbench.utils.ts` already provide graph and readiness helpers that can be reused instead of rebuilding graph semantics from scratch.

### Structural Risks
- `frontend/src/components/workspace/submarine-pipeline.tsx` is already over 1000 lines and mixes shell, layout persistence, runtime derivation, artifact loading, stage rendering, and chat rail composition.
- `frontend/src/components/workspace/skill-studio-workbench-panel.tsx` is already around 900 lines and mixes artifact fetching, readiness summaries, graph focus logic, validation/test/publish views, and shell framing.
- `frontend/src/components/workspace/workspace-nav-chat-list.tsx` currently omits the agent surface and splits the left rail into multiple conceptual groups that no longer match the approved Phase 7 IA.

### Integration Points
- Submarine and skill-studio route pages already own `useThreadStream`, thread bootstrap, notification behavior, and artifact drawer setup, so Phase 7 should preserve those responsibilities while moving presentation into shared shell primitives.
- `thread.values.submarine_runtime`, artifact virtual paths, and timeline data already provide the runtime-monitor inputs needed for the new overview/runtime split without requiring backend changes.
- `useSkillGraph()` and current skill-studio artifacts already provide the graph and lifecycle data needed for the new subpage model without changing the underlying skill package contract.

</code_context>

<specifics>
## Specific Ideas

- The approved shell should feel more like one serious research workspace and less like separate pages that happen to live under `/workspace`.
- The user explicitly wants clean screens, no duplicated sidebars, and no explanatory text around obvious chat controls.
- The user explicitly approved real-time runtime monitoring inside the workbench and a real graph-style skill map.
- The user explicitly approved using separate subpages when that is the cleaner way to keep process visibility complete without visual crowding.

</specifics>

<deferred>
## Deferred Ideas

- Full skill lifecycle governance, publish automation, and rollback management remain Phase 8 scope, even if Phase 7 introduces the page shells those workflows will later use.
- Backend runtime, reporting, or scientific contract changes are out of scope unless a tiny frontend-enabling adjustment becomes unavoidable.
- Broad architectural decomposition of oversized modules is deferred to Phase 10; Phase 7 may extract shell and page primitives, but it should not become a whole-repo refactor.

</deferred>

---

*Phase: 07-workspace-ux-and-navigation-system*
*Context gathered: 2026-04-03*
