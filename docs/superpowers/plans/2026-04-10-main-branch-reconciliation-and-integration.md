# Main Branch Reconciliation And Integration Implementation Plan

**Goal:** Reconcile `main`-only behavior with `codex/competition-agent-executor`, keep only still-needed `main` semantics, merge the current branch into `main` inside an isolated worktree, and leave `main` verified, pushed, and the temporary worktree removed.

**Reuse Strategy:** adapt existing project

**Session Status File:** `docs/superpowers/session-status/2026-04-10-main-branch-reconciliation-and-integration-status.md`

**Context Summary:** `docs/superpowers/context-summaries/2026-04-10-main-branch-reconciliation-and-integration-summary.md`

**Workspace Strategy:** dedicated worktree

**Validation Strategy:** mixed

**Review Cadence:** each milestone

**Artifact Lifecycle:** Keep this plan/status/context-summary chain with the final merge. Remove `.worktrees/main-integration` after push. Do not touch unrelated dirty files in the primary workspace.

## Task 1: Establish The Isolated Main Worktree And Baseline
- [x] Verify `.worktrees` ignore safety and remote visibility limits
- [x] Create `.worktrees/main-integration` on `main`
- [x] Record baseline verification and pre-existing frontend layout failures

## Task 2: Decide Which Main-Only Behavior Survives
- [x] Review `main`-only commits and build keep/drop matrix
- [x] Preserve `0050c2d` runtime-default hardening intent
- [x] Preserve `cb68630` judgment-first / lead-agent-first submarine orchestration intent
- [x] Drop stale dynamic-plan frontend and superseded stage-ownership metadata
- [x] Run reviewer checkpoint on the keep/drop matrix

## Task 3: Merge The Current Branch Into Main And Resolve Conflicts
- [x] Start the merge in `.worktrees/main-integration`
- [x] Resolve backend/frontend conflicts according to the keep/drop matrix
- [x] Keep hybrid `runtime-base-url` behavior
- [x] Restore verified auth/proxy hardening from the runtime-security slice
- [x] Restore verified startup-dir-safe backend config/path/skills/thread-data behavior needed by the merged runtime
- [x] Sync stale backend tests to the merged semantics

## Task 4: Run The Integrated Verification Slice And Reviewer Pass
- [x] Run targeted backend verification in the worktree
- [x] Run targeted frontend verification in the worktree
- [x] Run `tsc`, targeted `eslint`, and `git diff --check`
- [x] Run final reviewer-subagent pass on the integrated diff
- [x] Refresh status/context-summary with final reviewer result and publication state

## Task 5: Push Main And Retire The Temporary Worktree
- [ ] Stage and commit the verified merge on `main`
- [ ] Push `main` to `origin`
- [ ] Remove `.worktrees/main-integration`
- [ ] Refresh the durable artifacts with the pushed commit and cleanup result
