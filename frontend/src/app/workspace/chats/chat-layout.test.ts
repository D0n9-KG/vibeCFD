import assert from "node:assert/strict";
import test from "node:test";

const { getChatPageLayout } = await import(
  new URL("./chat-layout.ts", import.meta.url).href
);

void test("reserves bottom safe area when the submarine runtime panel is shown", () => {
  const layout = getChatPageLayout({
    hasRuntimeWorkbench: true,
    isNewThread: false,
  });

  assert.match(layout.contentClassName, /\bpb-40\b/);
  assert.match(layout.messageListClassName, /\bpt-10\b/);
});

void test("keeps the centered composer treatment for a new thread", () => {
  const layout = getChatPageLayout({
    hasRuntimeWorkbench: false,
    isNewThread: true,
  });

  assert.match(layout.inputShellClassName, /-translate-y-\[calc\(50vh-96px\)\]/);
});
