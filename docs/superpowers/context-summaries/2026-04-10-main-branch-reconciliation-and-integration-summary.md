# Main Branch Reconciliation And Integration Context Summary

**Status:** active

**Related Plan:** `docs/superpowers/plans/2026-04-10-main-branch-reconciliation-and-integration.md`

**Related Session Status:** `docs/superpowers/session-status/2026-04-10-main-branch-reconciliation-and-integration-status.md`

## Canonical Snapshot
- Goal / Mainline: land a verified `main` that keeps the current branch's Skill Studio/runtime contract, preserves only the `main` submarine semantics that still matter, and retires the temporary worktree after push
- Current Verified State:
  - the merge is resolved in `.worktrees/main-integration` and still uncommitted
  - lead-agent-first / judgment-first submarine wording is preserved
  - same-origin `runtime-base-url` defaults are preserved while explicit browser overrides still win
  - the frontend auth/proxy slice and backend startup-dir-safe config slice from the previously verified runtime-security work were ported into the worktree
  - backend full suite is green at `929 passed, 1 skipped, 10 warnings`
  - frontend full Node contract suite is green at `295 passed`, with `tsc`, `eslint`, and `git diff --check` also clean
  - the final reviewer pass cleared the integrated diff with no Critical or Important issues
- Key Constraint: the dirty primary workspace remains untouched; its local `config.yaml` and `extensions_config.json` were only referenced as environment inputs for backend verification

## Keep / Retire Decisions
- Keep: `0050c2d` runtime-default hardening intent for submarine subagents
- Keep intent and reapply: `cb68630` lead-agent-first / judgment-first submarine orchestration semantics
- Drop as superseded: old dynamic-plan frontend/workbench shell path, stale stage-ownership metadata, and retired `recommended_actions` expectations in backend tests
- Port from verified dirty primary-workspace runtime slice because the merge needed it:
  - `frontend/src/app/api/threads/_auth.ts`
  - `frontend/src/app/api/threads/_auth.policy.ts`
  - `frontend/src/app/api/_backend.ts`
  - `frontend/src/env.js`
  - backend config/path/skills/thread-data startup-dir-safe files and tests

## Next Step
- Commit the merge on `main`
- Push `origin main`
- Remove `.worktrees/main-integration`
- Refresh the artifacts one last time with the published commit and cleanup state
