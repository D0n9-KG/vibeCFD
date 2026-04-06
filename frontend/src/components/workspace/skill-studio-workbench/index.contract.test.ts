import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./index.tsx", import.meta.url), "utf8");

void test("skill studio mounts lifecycle canvas instead of legacy stage panes", () => {
  assert.match(source, /SkillStudioLifecycleCanvas/);
  assert.doesNotMatch(source, /SkillStudioDefineStage/);
  assert.doesNotMatch(source, /SkillStudioEvaluateStage/);
  assert.doesNotMatch(source, /SkillStudioPublishStage/);
  assert.doesNotMatch(source, /SkillStudioGraphStage/);
  assert.doesNotMatch(source, /InterruptActionBar/);
});

void test("skill studio source no longer hardcodes english stage-first chrome", () => {
  assert.doesNotMatch(source, /\bDefine\b/);
  assert.doesNotMatch(source, /\bEvaluate\b/);
  assert.doesNotMatch(source, /\bPublish\b/);
  assert.doesNotMatch(source, /\bAssistant Rail\b/);
  assert.doesNotMatch(source, /Show rail|Hide rail/);
});
