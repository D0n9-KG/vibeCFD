# VibeCFD Runtime Flow Security First Pass Session Status

**Status:** active

**Plan:** `docs/superpowers/plans/2026-04-08-vibecfd-runtime-flow-security-first-pass.md`

**Primary Spec / Brief:** `none`

**Prior Art Survey:** `none`

**Last Updated:** 2026-04-08 21:28 Asia/Shanghai

**Current Focus:** Hold the repo at a verified checkpoint after extending the first-pass runtime/url/progress/security fixes with cleaner progress previews, thread-title sanitation, thread-level upload quotas, and an earlier route-promotion rule for newly created threads.

**Next Recommended Step:** Prioritize the thread route-promotion timing issue in `submarine/new`, then decide whether the following pass should focus on gateway-side auth / deployment hardening or deeper CFD-specific artifact generation and geometry-state UX.

**Read This Order On Resume:**
1. This session status file
2. The linked implementation plan
3. `docs/superpowers/session-status/2026-04-08-vibecfd-superpowers-alignment-and-workbench-cleanup-status.md`
4. `docs/superpowers/session-status/2026-04-08-vibecfd-legacy-workspace-retirement-status.md`
5. Git status and recent relevant commits

## Progress Snapshot
- Completed Tasks:
  - Task 1 - Runtime Surface And Backend URL Alignment
  - Task 2 - Main-Workspace Runtime Cleanup And Verification
  - Task 3 - Submarine Pre-Artifact Progress Visibility
  - Task 4 - Skill Studio Pre-Artifact Progress Visibility
  - Task 5 - Frontend Session Guards For Thread File APIs
  - Task 6 - Upload Size And Type Guardrails
  - Task 7 - Integrated Verification On The Main Workspace
  - Follow-up - Progress Preview Sanitization And Thread Title Cleanup
  - Follow-up - Thread-Level Upload Quota Guardrails
- In Progress: none
- Reopened / Invalidated: none

## Execution / Review Trace
- Latest Implementation Mode: local execution
- Latest Review Mode: review pending
- Latest Delegation Note: user asked to start fixing immediately after runtime cleanup, so this pass is proceeding inline from the main workspace

## Artifact Hygiene / Retirement
- Keep / Promote: this plan and session status file, any new regression tests that lock in runtime/url/progress/security behavior
- Archive / Delete / Replace Next: replace stale runtime assumptions that depend on frontend-local thread filesystem routes during standalone local frontend execution

## Latest Verified State
- Main workspace runtime is now a single stack: frontend `127.0.0.1:3000`, LangGraph `127.0.0.1:2024`, gateway `0.0.0.0:8001`
- `runtime-base-url` now sends standalone local browser traffic directly to `http://localhost:8001` and `http://localhost:2024`, while keeping reverse-proxied `localhost:2026` on same-origin routing
- Browser verification on `http://127.0.0.1:3000/workspace/submarine/new` showed uploads posting to `http://localhost:8001/api/threads/{thread_id}/uploads` and runs streaming from `http://localhost:2024/threads/{thread_id}/runs/stream`
- Browser verification on `http://127.0.0.1:3000/workspace/skill-studio/new` showed lifecycle data loading from `http://localhost:8001/api/skills/lifecycle` instead of the old same-origin 404 path
- Submarine and Skill Studio both surface inline Live Progress cards before structured artifacts exist, so the main canvas no longer looks stalled during upload/agent startup windows
- Live progress previews now strip `<uploaded_files>` scaffolding and `/mnt/user-data/uploads/...` transport paths instead of exposing raw upload protocol text to users
- Existing polluted thread titles such as truncated `<uploaded_files> ...` fall back to safe display labels (`未命名`, `潜艇 CFD 会话`), and newly created Skill Studio threads now display the user intent text instead of raw upload scaffolding
- Frontend thread-scoped file routes now require a session and return `401 {"detail":"Unauthorized"}` when called directly without authentication
- Frontend-local upload storage now rejects files above 25 MB and blocked executable/script extensions; backend upload router enforces the same first-pass policy
- Frontend-local upload storage and the backend upload router now also enforce per-thread quotas of 20 files and 200 MB total payload
- Backend `TitleMiddleware` now strips uploaded-file scaffolding before prompt construction and fallback-title generation, so future thread titles are no longer seeded from raw upload protocol text

## Unverified Hypotheses / Next Checks
- Gateway-wide auth and authorization are still open; this pass only protected the frontend thread file edge routes
- The new progress cards improve visibility, but they still stop at generic pre-artifact summaries; a later pass should feed geometry-specific state (bound STL, detected hull scale, recommended regime) into the main canvas earlier
- Server deployment still needs broader quota / concurrency / rate-limit planning beyond the per-file size and blocked-extension checks added here

## Open Questions / Risks
- The main workspace runtime is stable in the current session, but the historical duplicate-process issue suggests startup orchestration should eventually be scripted so developers do not drift back into split runtime states
- Frontend session guards are now in place, but any feature that still depends on frontend thread-file routes in an unauthenticated local environment would need an explicit auth story
- Browser QA shows the system still often sits in a pre-artifact state for a while; the UX is now understandable, but deeper agent/runtime instrumentation may still be needed for CFD users who expect immediate geometry-specific feedback
- Fresh `submarine/new` submissions now promote to `/workspace/submarine/{thread_id}` once the created thread is rebound and visible messages exist, even before persisted-message counts catch up. The remaining issue is title freshness, not route promotion.

## Relevant Findings / Notes
- Focused verification completed successfully:
  - `node --test frontend/src/core/config/runtime-base-url.test.ts`
  - `node --test frontend/src/app/api/threads/thread-route-auth.test.ts frontend/src/app/api/threads/uploads-storage.test.ts`
  - `node --test frontend/src/core/messages/utils.progress-preview.test.ts`
  - `node --test frontend/src/core/threads/utils.test.ts`
  - `node --test frontend/src/components/workspace/submarine-workbench/index.contract.test.ts`
  - `node --test frontend/src/components/workspace/skill-studio-workbench/index.contract.test.ts`
  - `corepack pnpm exec eslint ...` on all changed frontend files
  - `corepack pnpm exec tsc --noEmit`
  - `uv run pytest tests/test_title_generation.py`
  - `uv run pytest tests/test_uploads_router.py`
  - `uv run pytest tests/test_submarine_subagents.py`
- The `node --test` invocation for `frontend/src/app/workspace/submarine/[thread_id]/page.test.ts` did not execute tests under the PowerShell path syntax used in-session; the file itself was not changed in this pass
- Browser regression after the title cleanup showed:
  - existing polluted Submarine threads no longer leak raw upload protocol text into the heading or recent-thread list
  - newly created Skill Studio threads now show the user’s intent sentence as the visible thread title
  - after adjusting `shouldPromoteStartedThreadRoute(...)` to use the rebound thread id plus visible message count, fresh Submarine submissions now cut over to `/workspace/submarine/{thread_id}` instead of lingering on `/new`
  - newly created Submarine threads still often display `未命名` / `潜艇 CFD 会话` during the pre-artifact window, so title generation freshness remains open even though the route timing is improved
