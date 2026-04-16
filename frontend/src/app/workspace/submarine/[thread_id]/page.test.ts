import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const pageSource = await readFile(new URL("./page.tsx", import.meta.url), "utf8");
const threadRouteSource = await readFile(
  new URL(
    "../../../../components/workspace/submarine-workbench/thread-route.tsx",
    import.meta.url,
  ),
  "utf8",
);

void test("cuts the submarine route over to the shared thread route", () => {
  assert.match(pageSource, /SubmarineThreadRoute/);
  assert.doesNotMatch(pageSource, /SubmarineAgenticWorkbench/);
  assert.match(threadRouteSource, /SubmarineAgenticWorkbench/);
  assert.doesNotMatch(threadRouteSource, /SubmarineWorkbenchShell/);
  assert.doesNotMatch(threadRouteSource, /getSubmarineWorkbenchLayout/);
});

void test("keeps the right-side negotiation rail mounted for submarine sessions", () => {
  assert.match(threadRouteSource, /showChatRail/);
  assert.match(threadRouteSource, /onToggleChatRail/);
});

void test("submarine route can auto-reveal the negotiation rail when runtime confirmation is blocking progress", () => {
  assert.match(threadRouteSource, /getSubmarineNegotiationAttentionKey/);
  assert.match(threadRouteSource, /autoNegotiationAttentionKey/);
  assert.match(
    threadRouteSource,
    /setAgenticWorkbenchMobileNegotiationRailVisible\(model, true\)/,
  );
});

void test("submarine route no longer imports the legacy pipeline chat rail", () => {
  assert.doesNotMatch(threadRouteSource, /SubmarinePipelineChatRail/);
});

void test("submarine route uses a fixed viewport shell instead of scrolling the whole page", () => {
  assert.match(threadRouteSource, /flex size-full min-h-0 flex-col overflow-hidden/);
  assert.match(threadRouteSource, /<main className="min-h-0 flex-1 overflow-hidden">/);
  assert.doesNotMatch(
    threadRouteSource,
    /<main className="[^"]*overflow-y-auto[^"]*">/,
  );
});

void test("submarine route offers recovery actions when a restarted runtime loses the backing thread", () => {
  assert.match(threadRouteSource, /WorkspaceStatePanel/);
  assert.match(threadRouteSource, /isMissingThreadError/);
  assert.match(threadRouteSource, /label:\s*"[^"]+"/);
  assert.match(threadRouteSource, /workspace\/submarine\/new/);
});

void test("submarine route derives the negotiation input status from the latest run status so interrupted runs can accept a fresh visible message", () => {
  assert.match(threadRouteSource, /deriveThreadInputStatus/);
  assert.match(threadRouteSource, /latestRunStatus/);
});

void test("submarine thread route promotes fresh threads onto a concrete route instead of staying on slash-new", () => {
  assert.match(threadRouteSource, /deriveThreadChatRouteState/);
  assert.match(threadRouteSource, /deriveStartedThreadChatState/);
  assert.match(threadRouteSource, /shouldPromoteStartedThreadRoute/);
  assert.match(threadRouteSource, /router\.replace/);
  assert.doesNotMatch(threadRouteSource, /useThreadChat/);
});
