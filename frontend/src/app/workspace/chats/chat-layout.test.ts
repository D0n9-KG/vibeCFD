import assert from "node:assert/strict";
import test from "node:test";

const { getChatPageLayout } = await import(
  new URL("./chat-layout.ts", import.meta.url).href
);

void test("reserves bottom safe area when the submarine runtime panel is shown", () => {
  const layout = getChatPageLayout({
    hasRuntimeWorkbench: true,
    isNewThread: false,
    supportPanelOpen: true,
  });

  assert.match(layout.contentClassName, /\bpb-40\b/);
  assert.match(layout.messageListClassName, /\bpt-10\b/);
  assert.match(
    layout.shellClassName,
    /2xl:grid-cols-\[minmax\(0,1fr\)_minmax\(320px,360px\)\]/,
  );
  assert.match(layout.supportPanelClassName, /2xl:block/);
});

void test("keeps the centered composer treatment for a new thread", () => {
  const layout = getChatPageLayout({
    hasRuntimeWorkbench: false,
    isNewThread: true,
    supportPanelOpen: false,
  });

  assert.match(layout.inputShellClassName, /-translate-y-\[calc\(50vh-96px\)\]/);
  assert.match(layout.messageListClassName, /\bpt-6\b/);
  assert.match(layout.supportPanelClassName, /\bhidden\b/);
});

void test("exposes an explicit focus-visible toggle treatment for compact layouts", () => {
  const layout = getChatPageLayout({
    hasRuntimeWorkbench: false,
    isNewThread: false,
    supportPanelOpen: true,
  });

  assert.match(layout.supportToggleClassName, /focus-visible/);
  assert.match(layout.supportPanelInnerClassName, /min-h-\[420px\]/);
});
