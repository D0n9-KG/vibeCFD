# Mainline End-To-End Bring-Up And Hardening Context Summary

**Status:** active

**Related Plan:** `docs/superpowers/plans/2026-04-11-mainline-end-to-end-bringup-and-hardening.md`

**Related Session Status:** `docs/superpowers/session-status/2026-04-11-mainline-end-to-end-bringup-and-hardening-status.md`

## Canonical Snapshot
- Goal / Mainline: prove the newly merged `main` branch is not only test-green but locally runnable across the critical frontend/backend/runtime chain
- Current Verified State:
  - `main` was published at `c302c81`
  - the old `main-integration` worktree has been retired
  - the clean `codex/main-bringup` worktree is now carrying the post-merge bring-up fixes and verification evidence
  - Skill Studio end-to-end bring-up is working in the browser from `/workspace/skill-studio/new`, including a fresh post-review thread `a6b38162-d3f6-46ba-8816-458ed84394b6` that auto-promoted and produced `ready_for_review` artifacts
  - `/workspace/agents` and `/workspace/submarine/new` are live and reachable in the running local stack
  - backend built-in Skill Creator agents now match the frontend tool-group contract
  - backend alternate-model empty-response recovery now ignores hidden-only and invalid-tool-only alternate payloads
  - backend full suite (with explicit config env), frontend lint/typecheck, frontend thread-stream tests, and frontend production build (with explicit auth env) have all passed on the latest diff
- Key Constraint: do not modify or clean the dirty primary workspace in place; use explicit env vars or untracked local runtime inputs instead

## Known Inputs
- Primary local runtime config source currently lives outside the clean worktree:
  - `C:\Users\D0n9\Desktop\颠覆性大赛\config.yaml`
  - `C:\Users\D0n9\Desktop\颠覆性大赛\extensions_config.json`
- Current startup references live in:
  - `Makefile`
  - `scripts/serve.sh`
  - `scripts/start-daemon.sh`
- Frontend production build additionally requires:
  - `BETTER_AUTH_SECRET`
- Better Auth will still warn during build if:
  - `BETTER_AUTH_BASE_URL` is not set

## Next Step
- Create one clean commit on `codex/main-bringup`
- Push the validated branch state to `origin`
