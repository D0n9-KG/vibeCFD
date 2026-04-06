import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./index.tsx", import.meta.url), "utf8");

void test("submarine workbench mounts the research canvas instead of stage tabs", () => {
  assert.match(source, /SubmarineResearchCanvas/);
  assert.doesNotMatch(source, /SubmarinePlanStage/);
  assert.doesNotMatch(source, /SubmarineExecutionStage/);
  assert.doesNotMatch(source, /SubmarineResultsStage/);
  assert.doesNotMatch(source, /InterruptActionBar/);
});

void test("submarine workbench source no longer hardcodes english stage-first chrome", () => {
  assert.doesNotMatch(source, /Adaptive Session Stages/);
  assert.doesNotMatch(source, /Negotiation Rail/);
  assert.doesNotMatch(source, /Revise plan/);
  assert.doesNotMatch(source, /Current stage/);
});
