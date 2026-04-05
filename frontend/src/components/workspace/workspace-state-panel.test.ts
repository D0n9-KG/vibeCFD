import assert from "node:assert/strict";
import test from "node:test";

const { WORKSPACE_STATE_IDS, getWorkspaceStateCopy } = await import(
  new URL("./workspace-state-panel.state.ts", import.meta.url).href
);
const { enUS } = await import(
  new URL("../../core/i18n/locales/en-US.ts", import.meta.url).href
);
const { zhCN } = await import(
  new URL("../../core/i18n/locales/zh-CN.ts", import.meta.url).href
);

void test("shared workspace states expose the four locked state ids", () => {
  assert.deepEqual(WORKSPACE_STATE_IDS, [
    "first-run",
    "permissions-error",
    "data-interrupted",
    "update-failed",
  ]);
});

void test("shared workspace state copy stays locale-backed for every state", () => {
  const english = getWorkspaceStateCopy(enUS.workspaceStates, "update-failed");
  const chinese = getWorkspaceStateCopy(zhCN.workspaceStates, "data-interrupted");

  assert.ok(english.label.length > 0);
  assert.ok(english.title.length > 0);
  assert.ok(english.message.length > 0);
  assert.ok(chinese.label.length > 0);
  assert.ok(chinese.title.length > 0);
  assert.ok(chinese.message.length > 0);
});
