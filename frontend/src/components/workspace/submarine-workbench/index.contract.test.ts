import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./index.tsx", import.meta.url), "utf8");
const canvasSource = await readFile(
  new URL("./submarine-research-canvas.tsx", import.meta.url),
  "utf8",
);

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

void test("submarine workbench removes the extra summary bar and verbose chat helper copy", () => {
  assert.doesNotMatch(source, /SessionSummaryBar/);
  assert.match(source, /px-1 text-sm font-semibold text-slate-900/);
  assert.match(source, /协商区/);
  assert.doesNotMatch(source, /negotiationQuestion/);
});

void test("submarine workbench folds overview and flow index back into the main canvas", () => {
  assert.doesNotMatch(source, /const nav = \(/);
  assert.doesNotMatch(source, /nav=\{nav\}/);
  assert.doesNotMatch(source, /function NavMetric/);
  assert.match(canvasSource, /FlowIndexChip/);
  assert.doesNotMatch(canvasSource, /FlowIndexCard/);
  assert.doesNotMatch(canvasSource, /overflow-x-auto/);
  assert.doesNotMatch(canvasSource, /min-w-\[150px\]/);
  assert.doesNotMatch(canvasSource, /DrawerShortcut/);
});

void test("submarine workbench scrolls the center canvas instead of the whole page", () => {
  assert.match(
    source,
    /<section data-workbench-surface="submarine" className="h-full min-h-0">/,
  );
  assert.match(source, /className="min-h-0 flex-1 overflow-y-auto pr-1"/);
  assert.match(
    source,
    /id="submarine-chat-rail" className="min-h-0 flex-1 overflow-hidden"/,
  );
});
