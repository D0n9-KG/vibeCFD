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

void test("skill studio keeps the rail focused on chat instead of selector chrome", () => {
  assert.doesNotMatch(source, /negotiationQuestion/);
  assert.match(source, /px-1 text-sm font-semibold text-slate-900/);
  assert.match(source, /协商区/);
  assert.match(source, /SelectTrigger className="w-\[220px\] bg-white\/90"/);
  assert.match(source, /paddingBottom=\{192\}/);
  assert.match(source, /textareaClassName="min-h-36"/);
});

void test("skill studio folds lifecycle overview and index into the main canvas", () => {
  assert.doesNotMatch(source, /const nav = \(/);
  assert.doesNotMatch(source, /nav=\{nav\}/);
  assert.doesNotMatch(source, /function NavMetric/);
  assert.match(canvasSource, /FlowIndexChip/);
  assert.doesNotMatch(canvasSource, /FlowIndexCard/);
  assert.doesNotMatch(canvasSource, /overflow-x-auto/);
  assert.doesNotMatch(canvasSource, /min-w-\[150px\]/);
  assert.doesNotMatch(canvasSource, /onOpenNegotiation/);
});

void test("skill studio canvas localizes publish gate statuses", () => {
  assert.match(canvasSource, /已通过/);
  assert.match(canvasSource, /已阻塞/);
  assert.match(canvasSource, /待处理/);
});

void test("skill studio shows live progress while waiting for the first artifact", () => {
  assert.match(source, /buildProgressPreviewFromMessage/);
  assert.match(source, /resolveThreadDisplayTitle\(\s*thread\.values\.title,/);
  assert.match(source, /latestVisiblePreview/);
  assert.match(canvasSource, /data-live-progress="skill-studio"/);
});

void test("skill studio scrolls the center canvas while keeping a larger fixed composer in the rail", () => {
  assert.match(source, /className="min-h-0 flex-1 overflow-y-auto pr-1"/);
  assert.match(source, /id="skill-studio-chat-rail" className="min-h-0 flex-1 overflow-hidden"/);
  assert.match(source, /className="border-t border-slate-200\/80 p-2.5"/);
});

void test("skill studio records dry-run evidence with traceable message ids", () => {
  assert.match(source, /const dryRunEvidenceMessageIds = useMemo/);
  assert.match(source, /message_ids: dryRunEvidenceMessageIds/);
});

void test("skill studio surfaces a recovery panel when the backing thread has expired", () => {
  assert.match(source, /WorkspaceStatePanel/);
  assert.match(source, /isMissingThreadError/);
  assert.match(source, /新建技能线程/);
  assert.match(source, /workspace\/skill-studio\/new/);
});
