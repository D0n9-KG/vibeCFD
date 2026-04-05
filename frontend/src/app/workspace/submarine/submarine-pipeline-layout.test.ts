import assert from "node:assert/strict";
import test from "node:test";

const {
  getPipelineLayoutConfig,
  getPipelineDefaultLayout,
  getPipelineStoredLayout,
  PIPELINE_DEFAULT_VIEWPORT_WIDTH_PX,
  PIPELINE_WORKSPACE_SIDEBAR_WIDTH_PX,
  PIPELINE_SIDEBAR_MIN_PX,
  PIPELINE_SIDEBAR_DEFAULT_PX,
  PIPELINE_SIDEBAR_MAX_PX,
  PIPELINE_CHAT_MIN_PX,
  PIPELINE_CHAT_DEFAULT_PX,
  PIPELINE_CHAT_MAX_PX,
  PIPELINE_STORAGE_KEY_SIDEBAR,
  PIPELINE_STORAGE_KEY_CHAT,
  resolveStoredPanelPct,
} = await import(
  new URL("./submarine-pipeline-layout.ts", import.meta.url).href
);

void test("getPipelineLayoutConfig returns complete config", () => {
  const config = getPipelineLayoutConfig();
  assert.equal(config.sidebarDefaultSize, `${PIPELINE_SIDEBAR_DEFAULT_PX}px`);
  assert.equal(config.sidebarMinSize, `${PIPELINE_SIDEBAR_MIN_PX}px`);
  assert.equal(config.sidebarMaxSize, `${PIPELINE_SIDEBAR_MAX_PX}px`);
  assert.equal(config.chatDefaultSize, `${PIPELINE_CHAT_DEFAULT_PX}px`);
  assert.equal(config.chatMinSize, `${PIPELINE_CHAT_MIN_PX}px`);
  assert.equal(config.chatMaxSize, `${PIPELINE_CHAT_MAX_PX}px`);
  assert.equal(config.sidebarStorageKey, PIPELINE_STORAGE_KEY_SIDEBAR);
  assert.equal(config.chatStorageKey, PIPELINE_STORAGE_KEY_CHAT);
  assert.match(config.sidebarDefaultSize, /^\d+px$/);
  assert.match(config.chatDefaultSize, /^\d+px$/);
});

void test("sidebar pixel defaults stay within min-max range", () => {
  assert.ok(PIPELINE_SIDEBAR_DEFAULT_PX > PIPELINE_SIDEBAR_MIN_PX);
  assert.ok(PIPELINE_SIDEBAR_DEFAULT_PX < PIPELINE_SIDEBAR_MAX_PX);
});

void test("chat pixel defaults stay within min-max range", () => {
  assert.ok(PIPELINE_CHAT_DEFAULT_PX > PIPELINE_CHAT_MIN_PX);
  assert.ok(PIPELINE_CHAT_DEFAULT_PX < PIPELINE_CHAT_MAX_PX);
});

void test("storage keys are distinct strings", () => {
  assert.notEqual(PIPELINE_STORAGE_KEY_SIDEBAR, PIPELINE_STORAGE_KEY_CHAT);
  assert.equal(typeof PIPELINE_STORAGE_KEY_SIDEBAR, "string");
  assert.equal(typeof PIPELINE_STORAGE_KEY_CHAT, "string");
});

void test("viewport-aware percentages still clamp stored layouts", () => {
  const config = getPipelineLayoutConfig(2048);
  assert.ok(config.sidebarMinPct > 0);
  assert.ok(config.sidebarMaxPct < 100);
  assert.ok(config.chatMinPct > 0);
  assert.ok(config.chatMaxPct < 100);
  assert.ok(config.sidebarMinPct < config.sidebarDefaultPct);
  assert.ok(config.sidebarDefaultPct < config.sidebarMaxPct);
  assert.ok(config.chatMinPct < config.chatDefaultPct);
  assert.ok(config.chatDefaultPct < config.chatMaxPct);
});

void test("layout config uses workspace width instead of raw viewport width", () => {
  const config = getPipelineLayoutConfig(PIPELINE_DEFAULT_VIEWPORT_WIDTH_PX);
  const estimatedWorkbenchWidth =
    PIPELINE_DEFAULT_VIEWPORT_WIDTH_PX - PIPELINE_WORKSPACE_SIDEBAR_WIDTH_PX;
  const expectedSidebarDefaultPct =
    (PIPELINE_SIDEBAR_DEFAULT_PX / estimatedWorkbenchWidth) * 100;
  const expectedChatDefaultPct =
    (PIPELINE_CHAT_DEFAULT_PX / estimatedWorkbenchWidth) * 100;

  assert.equal(
    Number(config.sidebarDefaultPct.toFixed(2)),
    Number(expectedSidebarDefaultPct.toFixed(2)),
  );
  assert.equal(
    Number(config.chatDefaultPct.toFixed(2)),
    Number(expectedChatDefaultPct.toFixed(2)),
  );
});

void test("resolveStoredPanelPct clamps persisted sizes back into configured range", () => {
  const config = getPipelineLayoutConfig();

  assert.equal(
    resolveStoredPanelPct("1.039", {
      fallbackPct: config.sidebarDefaultPct,
      minPct: config.sidebarMinPct,
      maxPct: config.sidebarMaxPct,
    }),
    config.sidebarMinPct,
  );

  assert.equal(
    resolveStoredPanelPct("101", {
      fallbackPct: config.chatDefaultPct,
      minPct: config.chatMinPct,
      maxPct: config.chatMaxPct,
    }),
    config.chatMaxPct,
  );

  assert.equal(
    resolveStoredPanelPct(null, {
      fallbackPct: config.chatDefaultPct,
      minPct: config.chatMinPct,
      maxPct: config.chatMaxPct,
    }),
    config.chatDefaultPct,
  );
});

void test("default pipeline layout uses stable server-safe percentages", () => {
  const layout = getPipelineDefaultLayout();
  const config = getPipelineLayoutConfig();

  assert.equal(layout["submarine-pipeline-sidebar"], config.sidebarDefaultPct);
  assert.equal(layout["submarine-pipeline-chat"], config.chatDefaultPct);
  assert.equal(
    Number(
      (
        layout["submarine-pipeline-sidebar"] +
        layout["submarine-pipeline-center"] +
        layout["submarine-pipeline-chat"]
      ).toFixed(2),
    ),
    100,
  );
});

void test("stored pipeline layout resolves persisted values against the live viewport", () => {
  const layout = getPipelineStoredLayout({
    viewportWidth: 2048,
    sidebarRaw: "14",
    chatRaw: "40",
  });
  const config = getPipelineLayoutConfig(2048);

  assert.equal(layout["submarine-pipeline-sidebar"], 14);
  assert.equal(layout["submarine-pipeline-chat"], config.chatMaxPct);
  assert.equal(
    Number(layout["submarine-pipeline-center"].toFixed(2)),
    Number((100 - 14 - config.chatMaxPct).toFixed(2)),
  );
});

void test("stored pipeline layout falls back to defaults when persistence is absent", () => {
  assert.deepEqual(
    getPipelineStoredLayout({
      viewportWidth: 1600,
      sidebarRaw: null,
      chatRaw: undefined,
    }),
    getPipelineDefaultLayout(1600),
  );
});
