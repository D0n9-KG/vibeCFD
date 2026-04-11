# Main Branch Reconciliation And Integration Context Summary

**Status:** active

**Related Plan:** `docs/superpowers/plans/2026-04-10-main-branch-reconciliation-and-integration.md`

**Related Session Status:** `docs/superpowers/session-status/2026-04-10-main-branch-reconciliation-and-integration-status.md`

## Canonical Snapshot
- Goal / Mainline: keep `main` as the single active workspace, preserve the integrated Skill Studio/runtime contract plus the selected submarine semantics, and publish from the primary workspace without reintroducing worktree sprawl
- Current Verified State:
  - the temporary `main-finalize` worktree is gone; the primary workspace itself is now on `main`
  - `main` and `origin/main` both point at `1ed86cb fix: harden missing thread recovery detection`
  - the working tree is clean after the follow-up `isMissingThreadError()` improvement and its regression test were committed
  - stale-thread recovery UX works on both Skill Studio and submarine pages
  - real Skill Studio and submarine flows both complete from the primary workspace and surface their generated artifacts
  - frontend targeted tests (`19`), frontend `typecheck`, frontend `lint`, frontend production `build`, and backend focused runtime tests (`41`) are green after the follow-up fix
  - reviewer follow-up reduced to one valid nested-error edge case, now covered by test
- Key Constraints:
  - keep local frontend dev runs anonymous: do not inject `BETTER_AUTH_SECRET` into `next dev`
  - the safety snapshot branch `codex/primary-workspace-snapshot-20260411` preserves the older dirty state and should not be rewritten casually before push
  - `config.yaml` and `extensions_config.json` remain local environment prerequisites for runtime verification

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
- Continue the next runtime/product slice directly from the primary workspace on `main`
- Keep local frontend dev runs free of `BETTER_AUTH_SECRET`
- Retire the safety snapshot branch later if it is no longer needed
