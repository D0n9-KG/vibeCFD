import assert from "node:assert/strict";
import test from "node:test";

const { getAgenticWorkbenchLayout } = await import(
  new URL("./agentic-workbench-layout.ts", import.meta.url).href,
);

void test("builds a persistent desktop split from surface metadata", () => {
  const layout = getAgenticWorkbenchLayout({
    surface: "submarine",
    mobileNegotiationRailVisible: true,
  });

  assert.match(layout.shellClassName, /w-full/);
  assert.match(layout.shellClassName, /grid-cols-1/);
  assert.match(layout.shellClassName, /xl:h-\[calc\(100vh-5\.5rem\)\]/);
  assert.match(layout.shellClassName, /xl:overflow-hidden/);
  assert.match(
    layout.shellClassName,
    /xl:grid-cols-\[minmax\(0,1fr\)_minmax\(320px,420px\)\]/,
  );
  assert.match(
    layout.workbenchPaneClassName,
    /xl:grid-cols-\[minmax\(240px,280px\)_minmax\(400px,1fr\)\]/,
  );
  assert.match(layout.workbenchPaneClassName, /xl:min-h-0/);
  assert.match(layout.workbenchPaneClassName, /xl:overflow-hidden/);
  assert.match(layout.workbenchPaneClassName, /xl:pr-1/);
  assert.doesNotMatch(layout.chatRailClassName, /hidden/);
  assert.match(layout.chatRailClassName, /xl:block/);
  assert.match(layout.chatRailClassName, /xl:h-full/);
  assert.match(layout.chatRailInnerClassName, /xl:h-full/);
});

void test("keeps desktop negotiation rail mounted when mobile chat is hidden", () => {
  const layout = getAgenticWorkbenchLayout({
    surface: "skill-studio",
    mobileNegotiationRailVisible: false,
  });

  assert.match(
    layout.shellClassName,
    /xl:grid-cols-\[minmax\(0,1fr\)_minmax\(340px,460px\)\]/,
  );
  assert.match(layout.chatRailClassName, /hidden/);
  assert.match(layout.chatRailClassName, /xl:block/);
  assert.match(layout.workbenchPaneClassName, /xl:pr-2/);
});
