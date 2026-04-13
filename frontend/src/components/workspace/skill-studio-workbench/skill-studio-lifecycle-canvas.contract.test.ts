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

void test("skill studio defaults the secondary drawer to testing while dry-run evidence is still missing", () => {
  assert.match(source, /detail\.evaluate\.dryRun\.status !== "passed"/);
  assert.match(source, /detail\.evaluate\.scenarioMatrix\.scenarioCount > 0/);
});

void test("skill studio exposes explicit controls to switch between secondary drawers", () => {
  assert.match(source, /drawerLayers\.map\(\(layer\) =>/);
  assert.match(source, /setActiveDrawerId\(layer\.id\)/);
});

void test("skill studio gives the version note textarea a stable id and name", () => {
  assert.match(source, /id="skill-version-note"/);
  assert.match(source, /name="version_note"/);
});

void test("skill studio disables lifecycle save until a draft or lifecycle record is available", () => {
  assert.match(source, /canSaveLifecycle: boolean/);
  assert.match(source, /disabled=\{busy \|\| isMock \|\| !canSaveLifecycle\}/);
});

void test("skill studio keeps the chosen secondary drawer while detail refreshes inside the same module", () => {
  assert.match(source, /previousModuleIdRef/);
  assert.match(source, /if \(previousModuleIdRef\.current === session\.activeModuleId\)/);
  assert.match(source, /previousModuleIdRef\.current = session\.activeModuleId/);
});
