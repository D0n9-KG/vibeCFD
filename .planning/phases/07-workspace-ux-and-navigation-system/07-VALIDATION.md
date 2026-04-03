---
phase: 07
slug: workspace-ux-and-navigation-system
status: ready_for_planning
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-03
updated: 2026-04-03
---

# Phase 07 - Validation Strategy

## Validation Goal

Prove that Phase 7 makes the workspace feel coherent and trustworthy without losing any of the runtime, artifact, or workflow truths that already exist in the product.

The validation target is not only "pages look nicer", but:

- one shared workspace shell really drives all four surfaces,
- submarine and skill workflows stay understandable on desktop and laptop widths,
- chat and agent pages stop drifting visually from the main workbench,
- Chinese copy, focus states, and feedback states become more intentional instead of more confusing.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `node:test` + TypeScript typecheck |
| **Config file** | `frontend/package.json`, `frontend/tsconfig.json` |
| **Quick run command** | `cd frontend && node --test src/components/workspace/workspace-sidebar-shell.test.ts src/components/workspace/workspace-resizable-ids.test.ts src/app/workspace/submarine/submarine-workbench-layout.test.ts src/app/workspace/skill-studio/skill-studio-workbench-layout.test.ts src/app/workspace/chats/chat-layout.test.ts src/components/workspace/submarine-pipeline-shell.test.ts src/components/workspace/submarine-pipeline-runs.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/skill-graph.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts && corepack pnpm typecheck` |
| **Full suite command** | `cd frontend && node --test src/app/workspace/chats/chat-layout.test.ts src/app/workspace/submarine/submarine-workbench-layout.test.ts src/app/workspace/skill-studio/skill-studio-workbench-layout.test.ts src/components/workspace/input-box.chrome.test.ts src/components/workspace/input-box.submit.test.ts src/components/workspace/recent-chat-list.state.test.ts src/components/workspace/skill-graph.utils.test.ts src/components/workspace/skill-studio-agent-options.test.ts src/components/workspace/skill-studio-dashboard.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts src/components/workspace/submarine-confirmation-actions.test.ts src/components/workspace/submarine-pipeline-runs.test.ts src/components/workspace/submarine-pipeline-shell.test.ts src/components/workspace/submarine-pipeline-status.test.ts src/components/workspace/submarine-runtime-panel.trends.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-task-intelligence-view.test.ts src/components/workspace/workspace-resizable-ids.test.ts src/components/workspace/workspace-sidebar-shell.test.ts && corepack pnpm typecheck` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every shared-shell or navigation task:** Run the quick command
- **After every responsive-layout task:** Re-run the quick command
- **After every plan wave:** Re-run the full suite command
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Validation Dimensions

### Dimension 1: Shared Workspace IA

Must validate:

- one route-aware surface registry drives top-level navigation across submarine, skill studio, chats, and agents
- activity bar and contextual sidebar do not duplicate responsibilities
- shared pane ids and shell tokens remain stable and testable

### Dimension 2: Submarine and Skill Workflow Readability

Must validate:

- submarine overview keeps live runtime truth visible without dumping every section into the first viewport
- runtime, artifact, report, and graph subviews exist as deliberate surface boundaries
- skill graph remains a real graph interaction with filters/focus instead of degrading into a generic list by default

### Dimension 3: Responsive and Compact Behavior

Must validate:

- desktop widths preserve the intended multi-pane shell
- laptop widths degrade to drawers/sheets or stacked layouts without losing monitor, artifact, or graph access
- chat rail behavior remains deterministic across submarine, skill studio, and chat-heavy pages

### Dimension 4: Copy, Focus, and Feedback States

Must validate:

- Chinese copy remains consistent and avoids filler around obvious controls
- loading, empty, permission-error, interruption, and update-failure states render through one shared language
- focus-visible styling and keyboard reachability exist for activity-bar buttons, graph filters, side-nav items, and chat toggles

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | UX-01 | shared navigation registry | `cd frontend && node --test src/components/workspace/workspace-sidebar-shell.test.ts src/components/workspace/workspace-resizable-ids.test.ts && corepack pnpm typecheck` | `frontend/src/components/workspace/workspace-sidebar-shell.test.ts` | pending |
| 07-01-02 | 01 | 1 | UX-03 | shell token + pane id contract | `cd frontend && node --test src/components/workspace/workspace-sidebar-shell.test.ts src/components/workspace/workspace-resizable-ids.test.ts && corepack pnpm typecheck` | `frontend/src/components/workspace/workspace-resizable-ids.test.ts` | pending |
| 07-02-01 | 02 | 2 | UX-02 | submarine shell layout | `cd frontend && node --test src/app/workspace/submarine/submarine-workbench-layout.test.ts src/components/workspace/submarine-pipeline-shell.test.ts src/components/workspace/submarine-pipeline-runs.test.ts && corepack pnpm typecheck` | `frontend/src/app/workspace/submarine/submarine-workbench-layout.test.ts` | pending |
| 07-02-02 | 02 | 2 | UX-02 | skill studio shell and graph helpers | `cd frontend && node --test src/app/workspace/skill-studio/skill-studio-workbench-layout.test.ts src/components/workspace/skill-graph.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts && corepack pnpm typecheck` | `frontend/src/components/workspace/skill-graph.utils.test.ts` | pending |
| 07-03-01 | 03 | 3 | UX-01 | chat and agent shell parity | `cd frontend && node --test src/app/workspace/chats/chat-layout.test.ts && corepack pnpm typecheck` | `frontend/src/app/workspace/chats/chat-layout.test.ts` | pending |
| 07-03-02 | 03 | 3 | UX-04 | shared state and copy polish | `cd frontend && corepack pnpm typecheck` | `frontend/src/core/i18n/locales/zh-CN.ts` | pending |
| 07-03-03 | 03 | 3 | UX-03, UX-04 | accessibility/focus state coverage | `cd frontend && corepack pnpm typecheck` | `frontend/src/components/workspace/workspace-state-panel.tsx` | 07-W0 |

---

## Wave 0 Requirements

Existing frontend infrastructure already covers the phase:

- `node:test` is already used for layout and helper contracts
- `corepack pnpm typecheck` already exists as a global frontend gate
- no new test runner or framework bootstrap is required before execution begins

Wave 0 only needs phase-specific test files to be added where the new shell helpers or shared state components are introduced.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Activity bar plus contextual sidebar feels like one shell instead of two sidebars | UX-01, UX-03 | Requires visual judgment on duplication and hierarchy | Open submarine, skill studio, chats, and agents on desktop width and confirm the left side is one coherent navigation/context system |
| Submarine overview keeps live monitoring visible without overwhelming the page | UX-02 | Requires judging information density and runtime readability | Open a thread with `submarine_runtime`, verify overview shows compact live status, then switch to runtime/report/artifact views and confirm the deeper detail moved out of the overview |
| Skill graph remains navigable on laptop width | UX-02 | Requires checking focus, minimap/detail behavior, and compact degradation | Open the graph page at laptop width, confirm filters, focus node, and detail access still work through the compact layout |
| Chinese copy and obvious controls feel cleaner | UX-04 | Requires human review of wording and noise level | Compare redesigned chat rail and workbench headers against the approved Phase 7 wireframes and confirm obvious controls are not surrounded by explanatory filler |
| Keyboard focus order across activity bar, sidebar, graph filters, and chat toggles is usable | UX-04 | Automated tests will not fully prove real focus clarity | Tab through the redesigned surfaces and confirm visible focus and predictable order |

---

## Evidence To Capture Before Phase Sign-Off

- one desktop screenshot showing the shared shell on submarine or skill studio
- one laptop-width screenshot showing the compact shell without lost monitoring or graph access
- one screenshot of the skill graph page with filters and focused-node detail visible
- one screenshot or short note confirming a shared workspace error/empty/interruption state

---

## Exit Criteria

Phase 7 is not ready for execution sign-off until all of the following are true:

- `UX-01` is satisfied through one shared workspace IA that includes the agent surface
- `UX-02` is satisfied through readable desktop and laptop workbench flows for submarine and skill studio
- `UX-03` is satisfied through shared shell primitives, pane ids, and feedback-state patterns instead of per-page drift
- `UX-04` is satisfied through cleaner Chinese copy, consistent state presentation, and visible focus behavior
- `nyquist_compliant: true` remains valid because every plan has automated coverage or explicit manual verification
