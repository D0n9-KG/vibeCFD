import assert from "node:assert/strict";
import test from "node:test";

const { getSubmarineWorkbenchLayout } = await import(
  new URL("./submarine-workbench-layout.ts", import.meta.url).href
);

void test("uses a persistent desktop split layout when the chat rail is open", () => {
  const layout = getSubmarineWorkbenchLayout({ chatOpen: true });

  assert.match(layout.shellClassName, /w-full/);
  assert.match(layout.shellClassName, /grid-cols-1/);
  assert.match(layout.shellClassName, /xl:h-\[calc\(100vh-5\.5rem\)\]/);
  assert.match(layout.shellClassName, /xl:overflow-hidden/);
  assert.match(
    layout.shellClassName,
    /xl:grid-cols-\[minmax\(0,1fr\)_minmax\(360px,420px\)\]/,
  );
  assert.match(layout.workbenchPaneClassName, /xl:min-h-0/);
  assert.match(layout.workbenchPaneClassName, /xl:overflow-y-auto/);
  assert.doesNotMatch(layout.chatRailClassName, /absolute/);
  assert.match(layout.chatRailClassName, /xl:block/);
  assert.match(layout.chatRailClassName, /xl:h-full/);
  assert.match(layout.chatRailInnerClassName, /xl:sticky/);
  assert.match(layout.chatRailInnerClassName, /xl:h-full/);
  assert.doesNotMatch(layout.chatRailInnerClassName, /shadow-2xl/);
});

void test("collapses back to a single-column layout when the chat rail is hidden", () => {
  const layout = getSubmarineWorkbenchLayout({ chatOpen: false });

  assert.match(layout.shellClassName, /grid-cols-1/);
  assert.doesNotMatch(
    layout.shellClassName,
    /xl:grid-cols-\[minmax\(0,1fr\)_minmax\(360px,420px\)\]/,
  );
  assert.match(layout.chatRailClassName, /hidden/);
});
