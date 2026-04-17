import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./agents-tab.tsx", import.meta.url), "utf8");

void test("agents tab combines canonical agents with runtime stage-role summaries and binding metadata", () => {
  assert.match(source, /useAgents/);
  assert.match(source, /useRuntimeConfig/);
  assert.match(source, /useSkillLifecycleSummaries/);
  assert.match(source, /useCreateAgent/);
  assert.match(source, /useUpdateAgent/);
  assert.match(source, /useDeleteAgent/);
  assert.match(source, /buildStageRoleSkillSummaries/);
  assert.match(source, /inventory_source/);
  assert.match(source, /执行子代理/);
  assert.match(source, /关联技能/);
  assert.match(source, /Dialog/);
  assert.match(source, /Input/);
  assert.match(source, /搜索智能体/);
  assert.match(source, /filterAgents/);
  assert.match(source, /filterStageRoleSkillSummaries/);
  assert.match(source, /getAgentDisplayName/);
  assert.match(source, /WorkspaceStatePanel/);
});
