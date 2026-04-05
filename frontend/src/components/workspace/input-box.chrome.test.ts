import assert from "node:assert/strict";
import test from "node:test";

const { getInputBoxChromeState, getResolvedMode } = await import(
  new URL("./input-box.chrome.ts", import.meta.url).href
);

void test("resolved mode falls back to pro when thinking-capable models have no saved mode yet", () => {
  assert.equal(getResolvedMode(undefined, true), "pro");
});

void test("resolved mode collapses to flash when the selected model cannot think", () => {
  assert.equal(getResolvedMode("ultra", false), "flash");
});

void test("input box keeps chrome non-interactive until the client has mounted", () => {
  const chrome = getInputBoxChromeState({
    mounted: false,
    mode: "ultra",
    supportsThinking: true,
    supportsReasoningEffort: true,
  });

  assert.equal(chrome.interactive, false);
  assert.equal(chrome.resolvedMode, "ultra");
  assert.equal(chrome.showReasoningEffort, true);
});

void test("reasoning effort control stays hidden for flash mode even after mount", () => {
  const chrome = getInputBoxChromeState({
    mounted: true,
    mode: "flash",
    supportsThinking: true,
    supportsReasoningEffort: true,
  });

  assert.equal(chrome.interactive, true);
  assert.equal(chrome.showReasoningEffort, false);
});
