# 07-02 Summary

## Outcome

Rebuilt the submarine and skill-studio thread surfaces around explicit workspace shells while preserving their existing thread bootstrap, runtime truth, artifact loading, and publish wiring. Submarine now separates `鎬昏 / 杩愯鏃禶 / 浜х墿 / 鎶ュ憡`, and Skill Studio now separates `鎬昏 / 鏋勫缓 / 鏍￠獙 / 娴嬭瘯 / 鍙戝竷 / 鍥捐氨` with a focused graph page and node inspector.

## Key Changes

- Added `SubmarineWorkbenchShell` and `SkillStudioWorkbenchShell` to own page-level view selection, laptop toggles, and shared shell framing.
- Updated submarine and skill-studio layout helpers to encode the approved contextual-column and chat-rail ranges.
- Exported the submarine chat rail and added a center-only pipeline mode so the runtime cockpit can sit inside the new shell without losing stop/send behavior.
- Reworked `SkillStudioWorkbenchPanel` into view-driven lifecycle sections and added a filtered graph workbench model with focused-node inspection.

## Verification

- `cd frontend && node --test src/app/workspace/submarine/submarine-workbench-layout.test.ts src/components/workspace/submarine-pipeline-shell.test.ts src/components/workspace/submarine-pipeline-runs.test.ts`
- `cd frontend && node --test src/app/workspace/skill-studio/skill-studio-workbench-layout.test.ts src/components/workspace/skill-graph.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts`
- `cd frontend && corepack pnpm typecheck`

## Follow-Up

Manual browser validation for the redesigned submarine and skill-studio threads is still pending and will be covered alongside the cross-surface polish pass in 07-03.
