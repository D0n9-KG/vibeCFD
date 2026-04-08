import assert from "node:assert/strict";
import { access } from "node:fs/promises";
import test from "node:test";

const retiredFiles = [
  "./agentic-workbench/interrupt-action-bar.tsx",
  "./agentic-workbench/agentic-workbench-layout.ts",
  "./submarine-pipeline.tsx",
  "./submarine-pipeline-runs.ts",
  "./submarine-pipeline-shell.ts",
  "./submarine-pipeline-sidebar.tsx",
  "./submarine-pipeline-status.ts",
  "./submarine-stage-card.tsx",
  "./submarine-stage-cards.tsx",
  "./skill-studio-dashboard.tsx",
  "./skill-studio-dashboard.utils.ts",
  "./submarine-workbench/submarine-plan-stage.tsx",
  "./submarine-workbench/submarine-execution-stage.tsx",
  "./submarine-workbench/submarine-results-stage.tsx",
  "./skill-studio-workbench/skill-studio-define-stage.tsx",
  "./skill-studio-workbench/skill-studio-evaluate-stage.tsx",
  "./skill-studio-workbench/skill-studio-publish-stage.tsx",
  "./skill-studio-workbench/skill-studio-graph-stage.tsx",
  "../../app/workspace/submarine/submarine-pipeline-layout.ts",
  "../../app/workspace/submarine/submarine-workbench-layout.ts",
  "../../app/workspace/skill-studio/skill-studio-workbench-layout.ts",
] as const;

for (const retiredFile of retiredFiles) {
  void test(`${retiredFile} has been retired`, async () => {
    await assert.rejects(access(new URL(retiredFile, import.meta.url)));
  });
}
