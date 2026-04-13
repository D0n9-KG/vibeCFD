import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./index.tsx", import.meta.url), "utf8");
const canvasSource = await readFile(
  new URL("./submarine-research-canvas.tsx", import.meta.url),
  "utf8",
);
const ribbonSource = await readFile(
  new URL("./submarine-research-slice-ribbon.tsx", import.meta.url),
  "utf8",
);
const cardSource = await readFile(
  new URL("./submarine-research-slice-card.tsx", import.meta.url),
  "utf8",
);
const historyBannerSource = await readFile(
  new URL("./submarine-research-slice-history-banner.tsx", import.meta.url),
  "utf8",
);
const visibleActionsSource = await readFile(
  new URL("./submarine-visible-actions.ts", import.meta.url),
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
  assert.match(source, /buildSubmarineNegotiationPanelModel\(session\.negotiation\)/);
  assert.doesNotMatch(source, /question=\{null\}/);
  assert.match(source, /question=\{railPrompt\}/);
  assert.match(source, /railPanel\.ctaLabel/);
  assert.match(source, /onClick=\{onOpenChat\}/);
});

void test("submarine workbench renders a research ribbon and slice card instead of a flow-based center surface", () => {
  assert.doesNotMatch(source, /const nav = \(/);
  assert.doesNotMatch(source, /nav=\{nav\}/);
  assert.match(canvasSource, /SubmarineResearchSliceRibbon/);
  assert.match(canvasSource, /SubmarineResearchSliceCard/);
  assert.match(canvasSource, /SubmarineResearchSliceHistoryBanner/);
  assert.doesNotMatch(canvasSource, /WorkbenchFlow/);
  assert.doesNotMatch(canvasSource, /FlowIndexChip/);
});

void test("submarine workbench exposes live progress before structured artifacts arrive", () => {
  assert.match(source, /buildProgressPreviewFromMessage/);
  assert.match(source, /resolveThreadDisplayTitle\(thread\.values\.title,/);
  assert.match(source, /latestAssistantPreview/);
  assert.match(source, /latestUserPreview/);
  assert.match(canvasSource, /data-live-progress="submarine"/);
});

void test("submarine workbench adds visible action buttons that send execution and report requests through chat history", () => {
  assert.match(source, /buildSubmarineVisibleActions/);
  assert.match(source, /onSubmitVisibleAction/);
  assert.match(canvasSource, /data-submarine-visible-actions="submarine"/);
  assert.match(canvasSource, /data-submarine-visible-action=/);
  assert.match(visibleActionsSource, /开始实际求解执行/);
  assert.match(visibleActionsSource, /生成最终结果报告/);
});

void test("submarine workbench exposes a visible runtime skill snapshot for binding proof", () => {
  assert.match(source, /skill_runtime_snapshot/);
  assert.match(source, /skillRuntimeSnapshot/);
  assert.match(canvasSource, /data-submarine-runtime-snapshot="submarine"/);
  assert.match(canvasSource, /data-submarine-runtime-binding=/);
  assert.match(canvasSource, /resolved_binding_targets/);
});

void test("submarine center surface no longer renders raw DeerFlow stage ids as visible evidence badges", () => {
  assert.doesNotMatch(canvasSource, /阶段: \$\{runtime\.current_stage\}/);
  assert.match(canvasSource, /buildSliceEvidenceBadgesModel/);
});

void test("submarine workbench scrolls the center canvas instead of the whole page", () => {
  assert.match(
    source,
    /<section data-workbench-surface="submarine" className="h-full min-h-0">/,
  );
  assert.match(source, /className="min-h-0 flex-1 overflow-y-auto pr-1"/);
  assert.match(
    source,
    /id="submarine-chat-rail"[\s\S]*className="flex h-full min-h-0 flex-col overflow-hidden"/,
  );
});

void test("submarine workbench forwards mobile chat-rail visibility into the shared shell", () => {
  assert.match(source, /showChatRail\?: boolean/);
  assert.match(source, /mobileNegotiationRailVisible=\{showChatRail\}/);
});

void test("submarine research ribbon keeps slice nodes stacked on narrow screens before widening out", () => {
  assert.match(ribbonSource, /className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3"/);
  assert.match(ribbonSource, /className=\{\[\s*"w-full rounded-\[22px\]/);
});

void test("submarine research surface uses motion-safe transitions with reduced-motion fallbacks", () => {
  assert.match(
    canvasSource,
    /motion-safe:transition-\[opacity,transform\][\s\S]*motion-reduce:transition-none/,
  );
  assert.match(
    ribbonSource,
    /motion-safe:transition-\[transform,box-shadow,border-color,background-color\][\s\S]*motion-reduce:transition-none/,
  );
  assert.match(
    cardSource,
    /motion-safe:transition-\[transform,box-shadow,border-color,opacity\][\s\S]*motion-reduce:transition-none/,
  );
  assert.match(
    historyBannerSource,
    /motion-safe:transition-\[transform,opacity,box-shadow\][\s\S]*motion-reduce:transition-none/,
  );
});
