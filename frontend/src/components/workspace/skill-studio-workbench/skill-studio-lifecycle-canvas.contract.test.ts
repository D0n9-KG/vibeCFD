import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(
  new URL("./skill-studio-lifecycle-canvas.tsx", import.meta.url),
  "utf8",
);

void test("skill studio disables publish actions when the surface is mock-only", () => {
  assert.match(source, /disabled=\{busy \|\| isMock \|\| !canPublish\}/);
  assert.match(source, /disabled=\{busy \|\| isMock \|\| !canRollback\}/);
});

void test("skill studio wires dry-run evidence actions into the testing drawer", () => {
  assert.match(source, /onRecordDryRunPassed/);
  assert.match(source, /onRecordDryRunFailed/);
  assert.match(source, /<SkillStudioTestingEvidence[\s\S]*onRecordDryRunPassed=/);
});
