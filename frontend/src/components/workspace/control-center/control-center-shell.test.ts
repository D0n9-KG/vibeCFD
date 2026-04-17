import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(
  new URL("./control-center-shell.tsx", import.meta.url),
  "utf8",
);

void test("control center shell exposes the four management tabs and delegates to the real management surfaces", () => {
  assert.match(source, /TabsList/);
  assert.match(source, /value:\s*"runtime-config"/);
  assert.match(source, /value:\s*"agents"/);
  assert.match(source, /value:\s*"skills"/);
  assert.match(source, /value:\s*"threads"/);
  assert.match(source, /管理中心/);
  assert.match(source, /运行配置/);
  assert.match(source, /智能体与子代理/);
  assert.match(source, /技能资产/);
  assert.match(source, /线程与历史/);
  assert.match(source, /renderTabContent/);
  assert.match(source, /<RuntimeConfigTab \/>/);
  assert.match(source, /<AgentsTab \/>/);
  assert.match(source, /<SkillsTab \/>/);
  assert.match(source, /<ThreadsTab \/>/);
});
