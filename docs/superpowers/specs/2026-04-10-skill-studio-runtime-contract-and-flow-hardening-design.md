# Skill Studio Runtime Contract And Flow Hardening Design

**Date:** 2026-04-10

## Goal

Stabilize the active DeerFlow-based VibeCFD mainline without doing a repo-wide cleanup first. The immediate objective is to turn the current partial Skill Studio lifecycle into a reliable production chain:

`draft -> test evidence -> publish gate -> runtime refresh -> new thread visibility`

This design keeps the current Submarine and Skill Studio workbench direction, preserves the same-origin runtime/auth hardening that is already in progress, and focuses the next optimization pass on the narrow set of changes that unblock long-term delivery.

## Current State

The repository is not in a full legacy-collapse state. The active mainline is already relatively clear:

- `frontend/` contains the active workbench shell plus the Submarine and Skill Studio surfaces.
- `backend/` contains the DeerFlow runtime, gateway, prompt assembly, and built-in tools.
- `skills/` contains the active public skill pool.
- `domain/submarine/` contains retained submarine-domain reference assets.
- `legacy/current-prototype/` is already isolated as reference-only material rather than the active execution path.

Recent cleanup passes have already retired the stage-first workspace surfaces and hardened the standalone runtime/auth/proxy path. Current uncommitted changes are not random drift; they are concentrated in one active slice around runtime/auth/skills loading hardening.

The real remaining issue is not repository sprawl. It is that the final operational contract between Skill Studio, publish, runtime refresh, and thread visibility is still incomplete.

## Problem Statement

The project currently has a real Skill Studio lifecycle model, a real publish endpoint, revision history, rollback support, and explicit bindings. However, the main chain is still incomplete in four ways:

1. `test_status` currently represents readiness for a dry run more than proof that a dry run passed.
2. The gateway publish path does not yet enforce publish-readiness as a hard backend gate.
3. Gateway and LangGraph runtime still behave like separate caches/processes without an explicit publish-to-runtime invalidation contract.
4. There is no explicit thread-level skill snapshot contract to guarantee:
   - newly published skills become visible without restart
   - only future new threads receive the new skill set
   - already-running threads keep their existing skill snapshot

As a result, the project feels "messy" in practice because several layers are compensating for the missing system contract at once.

## Non-Negotiables

- Do not start with a broad repo-wide cleanup.
- Keep the current DeerFlow-based mainline rather than reviving legacy runtime or legacy workspace surfaces.
- Treat Submarine and Skill Studio as linked systems, not separate tracks.
- Skill Studio output must become usable by agent runtime without service restart.
- Newly published skills should affect later new threads, not already-running threads.
- Publish must be blocked until testing requirements pass.
- Existing runtime/auth hardening around same-origin proxying and thread-route policy must not regress.

## Prior Art / Reuse Decision

Reuse strategy: adapt the current DeerFlow-based architecture already present in this repository.

No new external prior-art survey is required for this design pass because the work is a local stabilization and contract-definition task on top of an already chosen stack. The design deliberately avoids introducing a new orchestration framework, new registry service, or new deployment model.

## Design Overview

### 1. Limit Cleanup To Mainline-Clarity Work

The next cleanup pass should be narrow and only remove ambiguity that directly interferes with the main chain.

Allowed cleanup:

- clarify which docs are active vs retired
- reduce duplicated entry assumptions around runtime base URL / auth policy / skill request URL handling
- mark legacy/reference-only directories and old plans as non-mainline where needed
- keep the current uncommitted runtime/auth/skills slice together instead of partially cherry-picking it

Disallowed cleanup:

- broad file-by-file beautification
- deleting old reference material just because it looks unused
- refactoring unrelated frontend modules or domain assets before the runtime contract is stable

This keeps cleanup in service of delivery rather than turning it into a separate project.

### 2. Define The Skill Lifecycle Contract Explicitly

Skill Studio should stop treating "dry-run ready" and "test passed" as effectively equivalent.

For the first hardening pass, the current serialized status fields stay compatible with the existing repo instead of being renamed wholesale.

Compatibility rule:

- `validation_status` keeps the current validation-facing values such as `draft_only` and `needs_revision`
- `test_status` keeps the current preparation-facing values such as `ready_for_dry_run` and `blocked`
- `publish_status` keeps the current publish-readiness values such as `ready_for_review` and `blocked`
- lifecycle history fields such as `published` and `rollback_available` continue to live in lifecycle record state rather than replacing the publish-readiness field

What changes is the publish gate input, not the whole public vocabulary.

The lifecycle should therefore be interpreted as:

- `draft_only`: structured draft not yet validated
- `needs_revision`: validation failed
- `ready_for_dry_run`: structure and scenario prep are acceptable, but no passing dry run has been recorded
- `dry_run_evidence.status = not_recorded | failed | passed`: explicit dry-run result recorded as structured evidence
- `ready_for_review`: all existing publish-readiness gates passed, but backend publish is still blocked until dry-run evidence says `passed`
- `published`: skill archive installed and recorded into lifecycle history
- `rollback_available`: published with at least one prior revision available

For the first hardening pass, dry-run pass/fail does not need a full general-purpose evaluation platform. It only needs one explicit, auditable evidence artifact produced from the Skill Studio thread and stored alongside the existing draft outputs.

The first-pass artifact should be a structured payload such as `dry-run-evidence.json` that records:

- `status`
- `recorded_at`
- `recorded_by`
- `thread_id`
- `scenario_id`
- `message_ids` or equivalent traceable conversation references
- optional reviewer note / version note

The writer for this artifact should be the Skill Studio flow itself after a reviewed dry run, not the publish endpoint.

Placement contract:

- `dry-run-evidence.json` is written into the Skill Studio draft directory beside the existing draft outputs
- the `.skill` packaging step must include `dry-run-evidence.json` so the archive is self-contained
- the backend publish gate reads `dry-run-evidence.json` from the extracted archive contents, not by reaching back into thread-local draft artifacts
- after a successful publish, lifecycle history may copy summary fields from the evidence artifact, but the archive copy is the gate-time source of truth

### 3. Enforce Publish In The Backend, Not Just In The UI

The backend publish route must become the source of truth.

Required backend behavior:

- load lifecycle payload and publish-readiness artifacts from the archive being published
- reject publish if required evidence is missing
- reject publish if validation failed
- reject publish if `dry_run_evidence.status` is not `passed`
- reject publish if publish gates are not all passing
- only append revision history after the gate succeeds

The frontend should still disable the publish action when the draft is not publishable, but that is only a convenience layer. The hard rule belongs in the gateway.

### 4. Introduce A Runtime Refresh Contract

Publishing a skill should not require a full service restart, but it also should not rely on accidental cache invalidation.

The first-pass contract should be:

- publish writes the new lifecycle registry state and installed skill files
- the lifecycle registry keeps `version` as a schema version only and adds a separate monotonic `runtime_revision`
- gateway-side mutations are the sole owner of incrementing `runtime_revision`
- the increment applies to publish, rollback, enable/disable changes, and binding changes
- LangGraph-side skill loading checks `runtime_revision` when constructing skill availability for a thread entry point
- if the version changed, the process-local enabled-skills snapshot is refreshed before composing the next new-thread prompt context

The runtime snapshot source state should explicitly include:

- lifecycle registry `runtime_revision`
- lifecycle registry mtime
- `extensions_config.json` mtime
- relevant skill file mtimes under the active skills root

This design deliberately reuses the current file-backed registry plus process-local cache model instead of introducing an event bus. The goal is to make ownership and invalidation deterministic within the architecture that already exists.

### 5. Make Thread-Level Skill Snapshots Explicit

The project should define skill visibility at thread creation time, not as an implicit side effect of whatever the current process cache contains mid-run.

Required behavior:

- the snapshot source of truth lives in LangGraph thread state, not in thread-data middleware and not only in filesystem convention
- add a dedicated `skill_runtime_snapshot` structure to persisted thread state
- a thread receives a snapshot when it first enters actual lead-agent execution that can use skills
- that snapshot includes the enabled skill pool plus any applicable explicit binding outcomes
- later skill publishes do not mutate the snapshot of an already-running thread
- later new threads receive the latest snapshot derived from the newest registry/config state

The first-pass `skill_runtime_snapshot` should include:

- `runtime_revision`
- `captured_at`
- `enabled_skill_names`
- `binding_targets_applied`
- `source_registry_path` or equivalent source marker

Thread-data middleware should remain responsible only for filesystem directories. Snapshot capture should happen in the runtime path that already assembles available skills and prompt context, then persist through the existing LangGraph checkpointer.

This contract matches the desired operational rule:

`publish affects future threads, not already-running threads`

It also reduces debugging ambiguity, because "what skills did this thread have?" becomes inspectable state rather than a guess.

### 6. Keep Binding Configuration Controlled

Skills should not auto-attach globally just because they were published.

Binding policy for the next pass:

- publish may persist explicit binding targets
- bindings remain configuration-driven, not self-rewriting by the lead agent
- explicit bindings narrow routing for specific roles
- absence of explicit binding falls back to the normal enabled skill pool

This preserves user/operator control while still allowing Skill Studio outputs to become operational.

### 7. Add One True End-To-End Regression Chain

The current test base is strong in unit and contract coverage, but the project is still missing one proof-oriented chain that exercises the real promise of the system.

The first E2E regression should verify:

1. create or update a skill draft in Skill Studio
2. record passing dry-run evidence
3. publish successfully
4. start a new thread and observe the new skill/binding availability
5. confirm that a pre-existing thread keeps its previous snapshot
6. confirm same-origin auth/proxy behavior still works during the flow

Until this exists, the project will continue to feel "almost connected" even after local fixes.

## Phased Optimization Plan

### Phase 0: Contract Scaffold And Mainline-Clarity Cleanup

Objective: remove ambiguity only where it is a prerequisite for Phase 1 and 2, without opening a standalone cleanup branch.

Deliverables:

- short active-mainline documentation refresh
- explicit note that `legacy/current-prototype/` is reference-only
- keep the current runtime/auth/skills WIP grouped as one slice
- add the minimal schema/documentation scaffolding needed for:
  - dry-run evidence persistence
  - lifecycle registry `runtime_revision`
  - thread-state `skill_runtime_snapshot`
- no unrelated refactoring or broad hygiene work

### Phase 1: Publish Gate Hardening

Objective: make publish refusal deterministic.

Deliverables:

- backend publish gate checks
- frontend publish button aligned with gate state
- structured representation for `dry_run_evidence`
- regression tests for blocked vs allowed publish paths

### Phase 2: Runtime Refresh And Snapshot Boundary

Objective: guarantee no-restart future-thread visibility.

Deliverables:

- runtime registry/config versioning or equivalent invalidation marker
- deterministic refresh of enabled skill snapshots for new-thread entry
- thread-level persisted skill snapshot contract
- regression tests proving new-thread vs existing-thread behavior

### Phase 3: Full Chain Verification

Objective: prove the supply chain, not just the components.

Deliverables:

- one end-to-end test or scripted verification path
- documented operational checklist for local QA
- explicit failure diagnostics for publish gate, refresh, and thread snapshot mismatches

## Error Handling And Diagnostics

Failures should become legible at the exact layer that rejected the flow.

Required diagnostics:

- publish rejection messages should explain whether the failure came from validation, dry run, missing evidence, or publish gates
- runtime refresh mismatch should be observable via version/snapshot metadata
- thread state should expose enough metadata to answer:
  - which skill snapshot version was attached?
  - when was the snapshot created?
  - which explicit bindings were applied?

This prevents the current class of "it still doesn't seem connected" debugging loops.

## Testing Strategy

- unit tests for lifecycle-state transitions and publish gate rules
- gateway tests for publish rejection/acceptance and revision handling
- runtime tests for cache invalidation and new-thread snapshot construction
- frontend contract tests for publish button availability and lifecycle display
- one end-to-end verification path covering publish to runtime visibility
- one direct backend publish test that bypasses the UI and proves the gateway still rejects missing/failed dry-run evidence
- one cross-process or simulated cross-process refresh test that proves stale runtime visibility is detectable instead of silently accepted
- one new-thread vs existing-thread snapshot test that asserts the older thread keeps the older captured revision after a later publish

The system should not claim this chain is done until the end-to-end path exists and passes.

## Risks

- the exact place to persist thread-level skill snapshots may surface design tension with existing thread state/checkpoint behavior
- process-local cache refresh may still be subtle if multiple runtime entry paths build prompts differently
- the first implementation must avoid turning dry-run evidence into an overbuilt evaluation subsystem

## Out Of Scope

- broad legacy deletion beyond already isolated reference material
- redesigning the overall DeerFlow architecture
- replacing same-origin proxy/auth handling with a new security model
- building a generalized skill marketplace or autonomous self-binding system

## Recommended Next Step

Write a focused implementation plan that executes the work in this order:

1. mainline-clarity cleanup
2. backend publish gate hardening
3. runtime refresh contract
4. thread-level skill snapshot
5. end-to-end verification
