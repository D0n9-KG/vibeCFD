# Workspace Management Center Design

## Goal

Create a single user-facing management center for VibeCFD that makes runtime configuration, agent/skill management, and thread/history lifecycle explicit, editable, and auditable. The center must replace today's fragmented management surfaces with one coherent control plane while preserving quick actions in the existing workbenches.

## Validated Current State

- Agent management is split across two sources of truth.
  - The workspace UI currently uses the frontend-local `frontend/src/app/api/agents/store.ts` store backed by `.deerflow-ui/agents.json`.
  - The backend already exposes a richer `/api/agents` router backed by DeerFlow's `.deer-flow/agents/` structure.
- Skill management already has usable backend primitives (`/api/skills`, `/api/skills/lifecycle`, `/api/skills/graph`) and strong Skill Studio internals, but there is no general user-facing catalog that answers:
  - what skills exist,
  - which ones are enabled,
  - which roles or agents they bind to,
  - what files each skill contains,
  - and how to preview those files.
- Thread deletion is partly implemented but operationally fragmented.
  - The frontend delete mutation currently calls both LangGraph thread deletion and backend local directory cleanup.
  - The backend local cleanup removes the entire DeerFlow thread directory (`workspace`, `uploads`, `outputs`) through `Paths.delete_thread_dir`.
  - The main workbench sidebars do not expose those management actions consistently, so users cannot trust that cleanup is happening from where they work.
- Runtime configuration is partially exposed at the per-thread input level (`model_name`, reasoning depth, thread context), but the user still lacks a single explicit control plane for:
  - lead-agent defaults,
  - stage/subagent model overrides,
  - external vibecoding provider selection,
  - runtime availability / credential health,
  - and server-safe deployment configuration.

## User Problems To Solve

1. The user cannot confidently move the system from a local workstation to a server because the active model/provider/tool chain is not centrally visible or configurable.
2. The user cannot see the full skill inventory or understand what is bound to which agent/role without digging through partial surfaces.
3. The user cannot manage recent work threads from the surfaces where those threads are actually used.
4. Deleting a thread must mean deleting all associated persisted state and files, not just hiding a record from a list.
5. Historical local files may already be accumulating; the product needs a way to audit and clean orphaned thread storage.

## Design Principles

- One management center, not many half-admin pages.
- Canonical backend state, thin frontend adapters.
- User-visible provenance for runtime configuration and bindings.
- Destructive actions must be explicit, previewable, idempotent, and auditable.
- Keep surface-local convenience actions, but back them with the same canonical APIs as the management center.

## Chosen Information Architecture

Add a new top-level workspace surface:

- `/workspace/control-center`

This surface becomes the canonical management hub and is organized into four tabs:

1. `Runtime Config`
2. `Agents`
3. `Skills`
4. `Threads & History`

Existing workbench sidebars and cards keep lightweight quick actions, but those actions call the same control-center APIs rather than bespoke local logic.

## Tab 1: Runtime Config

### Purpose

Let the user inspect and manage the models, provider routes, and external vibecoding tool assignments that drive the main agent and stage-specific subagents.

### What Must Be Visible

- Lead-agent default model and reasoning policy
- Stage role -> active model override
  - `task-intelligence`
  - `geometry-preflight`
  - `solver-dispatch`
  - `scientific-study`
  - `experiment-compare`
  - `scientific-verification`
  - `result-reporting`
  - `scientific-followup`
- External vibecoding / provider profiles
  - Codex-backed provider availability
  - Claude Code provider availability
  - OpenAI API provider availability
  - any configured alternate fallback chain
- Config source provenance
  - env / config file / default / agent override
- Credential health without leaking secrets
  - `configured`
  - `missing`
  - `unavailable on this server`

### What Must Be Editable In V1

- Default lead model
- Stage role model overrides
- Whether a stage inherits the default or pins an override
- External provider selection / preferred route per supported task family
- Optional tool-group assignment for managed stage roles where the product already supports tool groups

### Explicit V1 Non-Goal

Do not expose raw secret values in the browser in this first pass. The UI configures model/provider selection and shows credential health, but secrets remain server-side and masked.

## Tab 2: Agents

### Purpose

Let the user manage both built-in and custom agents from one place and understand what each agent is configured to do.

### Key Changes

- Stop treating the frontend-local `.deerflow-ui/agents.json` store as the primary source of truth.
- Make backend-managed agent state canonical.
- Surface both built-in and custom agents in the same list.
- Show:
  - display name
  - description
  - model override
  - tool groups
  - role / usage notes
  - assigned or explicitly linked skills (when applicable)
- Support:
  - create custom agent
  - edit custom agent
  - delete custom agent
  - remove or change agent-level bindings

### Migration Requirement

The current frontend-local custom-agent store cannot simply be dropped. The first backend-backed release must include a migration path so existing custom agents are not lost.

Recommended behavior:

- Detect legacy `.deerflow-ui/agents.json`
- Import legacy custom agents into the backend-managed DeerFlow agent store when needed
- Mark migration status in the UI

## Tab 3: Skills

### Purpose

Make skills fully legible to the user outside Skill Studio.

### Required Views

- Skill catalog list
  - name
  - description
  - category (`public` / `custom`)
  - enabled state
  - lifecycle status
  - revision count
  - binding count
- Binding map
  - skill -> bound roles / agents
  - role / agent -> active skills
- File preview
  - tree of installed skill files
  - preview of selected file contents
  - support installed custom skills and packaged/archive-backed skill assets where relevant

### Required Actions

- enable / disable
- inspect lifecycle state
- inspect graph relationships
- inspect bindings
- preview files
- remove custom skill where safe
- rollback published revision where supported

### Backend Gap To Close

The current backend returns skill metadata and graph/lifecycle information, but not a unified safe file tree + file content preview API for installed skills. That must be added.

## Tab 4: Threads & History

### Purpose

Give users one place to manage all persisted work threads and reclaim storage safely.

### Required Inventory

- Unified list of:
  - chat threads
  - submarine workbench threads
  - skill studio threads
- Filters by workspace kind / title / status / last updated
- Storage summary
  - uploads count / size
  - outputs count / size
  - workspace count / size
  - total local footprint

### Required Actions

- rename
- export
- hard delete
- inspect thread kind / title / last updated
- clean orphaned local thread directories

## Hard Delete Semantics

Thread deletion must become a single backend-orchestrated cascade operation. The frontend should no longer manually coordinate multiple independent deletion calls as the primary strategy.

### A hard delete must remove:

- LangGraph thread state / checkpoints for the target thread
- DeerFlow local thread directory:
  - `workspace`
  - `uploads`
  - `outputs`
  - any remaining thread-local persisted metadata below `.deer-flow/threads/{thread_id}`

### Required UX

- Preview dialog before confirm
- Explicit impact summary, for example:
  - thread state count
  - upload file count
  - output artifact count
  - workspace file count
  - total bytes to remove
- Clear final status:
  - full success
  - partial success with retry guidance

### Failure Policy

Deletion must be idempotent and return stage-by-stage results. If one subsystem was already removed and another still exists, the user should see which cleanup stage remains instead of a vague failure.

## Orphan Cleanup

Because storage may already have accumulated, the management center must also expose an orphan cleanup view.

An orphaned local thread directory is one that exists under `.deer-flow/threads/` but no longer has a corresponding live LangGraph thread state.

The UI must let the user:

- inspect orphaned thread directories
- see their disk footprint
- delete one orphan
- bulk delete all confirmed orphans

## Chosen Backend Architecture

### Canonical state

- Backend gateway becomes canonical for management operations.
- Frontend route handlers become proxies or compatibility shims rather than authoritative stores.

### New or expanded backend capabilities

- Runtime configuration read/write summary endpoints
- Canonical agent inventory endpoints that include built-ins and custom agents
- Safe skill file tree + file content preview endpoints
- Thread deletion preview + cascade-delete endpoints
- Orphan thread storage audit endpoints

## Chosen Frontend Architecture

- Add a dedicated management-center route with four tabs.
- Reuse existing card/list primitives where possible.
- Reuse existing skill lifecycle / graph UI concepts from Skill Studio instead of rebuilding that logic from scratch.
- Add per-surface overflow actions in:
  - recent work thread sidebars
  - agent cards / lists
  - skill list rows / cards

## Security / Safety Constraints

- Never expose secret material in file preview or runtime config summaries.
- Skill file preview must be path-safe and restricted to known skill roots / archives.
- Hard delete must require explicit confirmation.
- Bulk orphan cleanup must show a count and size preview before execution.

## Validation Strategy

- Backend API tests for:
  - runtime config summary/update
  - skill file preview safety
  - cascade delete preview/results
  - orphan audit detection
  - legacy custom-agent migration
- Frontend tests for:
  - tab routing
  - list rendering
  - preview interactions
  - delete confirmation and result handling
- End-to-end verification:
  - create/edit/delete custom agent
  - inspect skill + preview `SKILL.md`
  - inspect skill bindings
  - rename/export/delete thread from management center
  - delete thread from a workbench-local quick action
  - verify local files are actually removed

## Non-Goals For This Slice

- Full browser-side secret entry / credential vault management
- A complete RBAC / multi-user permission system
- Replacing Skill Studio itself
- Replacing per-thread workbench flows with management-center flows

## Implementation Recommendation

Implement this as one coherent product slice, but decompose execution into backend-first milestones:

1. Canonical management APIs
2. Management center shell
3. Runtime + agent configuration
4. Skill catalog + preview + binding map
5. Thread/history audit + hard delete + orphan cleanup
6. Surface-local quick actions and final integration
