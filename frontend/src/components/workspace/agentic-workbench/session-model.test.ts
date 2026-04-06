import assert from "node:assert/strict";
import test from "node:test";

const {
  createAgenticWorkbenchSessionModel,
  toggleAgenticWorkbenchChatOpen,
} = await import(new URL("./session-model.ts", import.meta.url).href);

void test("defaults chat open state from new-thread mode", () => {
  const forNewThread = createAgenticWorkbenchSessionModel({
    isNewThread: true,
  });
  const forExistingThread = createAgenticWorkbenchSessionModel({
    isNewThread: false,
  });

  assert.equal(forNewThread.chatOpen, true);
  assert.equal(forExistingThread.chatOpen, false);
  assert.equal(forNewThread.desktopNegotiationRailPersistent, true);
  assert.equal(forExistingThread.desktopNegotiationRailPersistent, true);
});

void test("allows chat-open overrides and supports deterministic toggles", () => {
  const model = createAgenticWorkbenchSessionModel({
    isNewThread: false,
    chatOpenOverride: true,
  });
  const toggled = toggleAgenticWorkbenchChatOpen(model);

  assert.equal(model.chatOpen, true);
  assert.equal(toggled.chatOpen, false);
  assert.equal(toggled.isNewThread, model.isNewThread);
  assert.equal(toggled.desktopNegotiationRailPersistent, true);
});
