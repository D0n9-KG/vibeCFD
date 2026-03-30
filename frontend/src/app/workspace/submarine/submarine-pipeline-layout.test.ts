import assert from "node:assert/strict";
import test from "node:test";

const {
  getPipelineLayoutConfig,
  PIPELINE_SIDEBAR_MIN_PCT,
  PIPELINE_SIDEBAR_DEFAULT_PCT,
  PIPELINE_SIDEBAR_MAX_PCT,
  PIPELINE_CHAT_MIN_PCT,
  PIPELINE_CHAT_DEFAULT_PCT,
  PIPELINE_CHAT_MAX_PCT,
  PIPELINE_STORAGE_KEY_SIDEBAR,
  PIPELINE_STORAGE_KEY_CHAT,
} = await import(
  new URL("./submarine-pipeline-layout.ts", import.meta.url).href
);

void test("getPipelineLayoutConfig returns complete config", () => {
  const config = getPipelineLayoutConfig();
  assert.equal(config.sidebarDefaultPct, PIPELINE_SIDEBAR_DEFAULT_PCT);
  assert.equal(config.sidebarMinPct, PIPELINE_SIDEBAR_MIN_PCT);
  assert.equal(config.sidebarMaxPct, PIPELINE_SIDEBAR_MAX_PCT);
  assert.equal(config.chatDefaultPct, PIPELINE_CHAT_DEFAULT_PCT);
  assert.equal(config.chatMinPct, PIPELINE_CHAT_MIN_PCT);
  assert.equal(config.chatMaxPct, PIPELINE_CHAT_MAX_PCT);
  assert.equal(config.sidebarStorageKey, PIPELINE_STORAGE_KEY_SIDEBAR);
  assert.equal(config.chatStorageKey, PIPELINE_STORAGE_KEY_CHAT);
});

void test("sidebar default is within min-max range", () => {
  assert.ok(PIPELINE_SIDEBAR_DEFAULT_PCT > PIPELINE_SIDEBAR_MIN_PCT);
  assert.ok(PIPELINE_SIDEBAR_DEFAULT_PCT < PIPELINE_SIDEBAR_MAX_PCT);
});

void test("chat default is within min-max range", () => {
  assert.ok(PIPELINE_CHAT_DEFAULT_PCT > PIPELINE_CHAT_MIN_PCT);
  assert.ok(PIPELINE_CHAT_DEFAULT_PCT < PIPELINE_CHAT_MAX_PCT);
});

void test("storage keys are distinct strings", () => {
  assert.notEqual(PIPELINE_STORAGE_KEY_SIDEBAR, PIPELINE_STORAGE_KEY_CHAT);
  assert.equal(typeof PIPELINE_STORAGE_KEY_SIDEBAR, "string");
  assert.equal(typeof PIPELINE_STORAGE_KEY_CHAT, "string");
});
