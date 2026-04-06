import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./index.tsx", import.meta.url), "utf8");
const canvasSource = await readFile(
  new URL("./skill-studio-lifecycle-canvas.tsx", import.meta.url),
  "utf8",
);

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

void test("skill studio folds lifecycle overview and index into the main canvas", () => {
  assert.doesNotMatch(source, /const nav = \(/);
  assert.doesNotMatch(source, /nav=\{nav\}/);
  assert.doesNotMatch(source, /function NavMetric/);
  assert.match(canvasSource, /技能总览/);
  assert.match(canvasSource, /生命周期索引/);
  assert.match(canvasSource, /当前焦点/);
});

void test("skill studio canvas localizes publish gate statuses", () => {
  assert.match(canvasSource, /已通过/);
  assert.match(canvasSource, /已阻塞/);
});
