import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const pageSource = await readFile(new URL("./page.tsx", import.meta.url), "utf8");

void test("cuts the submarine route over to the new domain workbench", () => {
  assert.match(pageSource, /SubmarineAgenticWorkbench/);
  assert.doesNotMatch(pageSource, /SubmarineWorkbenchShell/);
  assert.doesNotMatch(pageSource, /getSubmarineWorkbenchLayout/);
});

void test("keeps the right-side negotiation rail mounted for submarine sessions", () => {
  assert.match(pageSource, /showChatRail/);
  assert.match(pageSource, /onToggleChatRail/);
});

void test("submarine route no longer imports the legacy pipeline chat rail", () => {
  assert.doesNotMatch(pageSource, /SubmarinePipelineChatRail/);
});

void test("submarine route uses a fixed viewport shell instead of scrolling the whole page", () => {
  assert.match(pageSource, /flex size-full min-h-0 flex-col overflow-hidden/);
  assert.match(pageSource, /<main className="min-h-0 flex-1 overflow-hidden">/);
  assert.doesNotMatch(
    pageSource,
    /<main className="[^"]*overflow-y-auto[^"]*">/,
  );
});
