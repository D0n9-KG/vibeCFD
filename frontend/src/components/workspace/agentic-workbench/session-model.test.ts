import assert from "node:assert/strict";
import test from "node:test";

const {
  createAgenticWorkbenchSessionModel,
  selectAgenticWorkbenchPrimaryStage,
  updateAgenticWorkbenchNegotiationState,
  toggleAgenticWorkbenchChatOpen,
} = await import(new URL("./session-model.ts", import.meta.url).href);

void test("builds shared session foundation with surface, stage, and trust-critical layer", () => {
  const forNewThread = createAgenticWorkbenchSessionModel({
    surface: "submarine",
    isNewThread: true,
  });
  const forExistingThread = createAgenticWorkbenchSessionModel({
    surface: "skill-studio",
    isNewThread: false,
  });

  assert.equal(forNewThread.surface, "submarine");
  assert.equal(forExistingThread.surface, "skill-studio");
  assert.equal(forNewThread.primaryStage, "workspace");
  assert.equal(forExistingThread.primaryStage, "workspace");
  assert.equal(forNewThread.chatOpen, true);
  assert.equal(forExistingThread.chatOpen, false);
  assert.equal(forNewThread.desktopNegotiationRailPersistent, true);
  assert.equal(forExistingThread.desktopNegotiationRailPersistent, true);
  assert.equal(forNewThread.negotiation.pendingApprovals, 0);
  assert.equal(forNewThread.negotiation.interruptionVisible, false);
  assert.equal(forNewThread.secondaryLayers.trustCriticalLayerId, "trust-critical");
  assert.deepEqual(forNewThread.secondaryLayers.available, ["trust-critical"]);
});

void test("supports stage selection groundwork and deterministic chat toggles", () => {
  const model = createAgenticWorkbenchSessionModel({
    surface: "submarine",
    isNewThread: false,
    chatOpenOverride: true,
  });
  const staged = selectAgenticWorkbenchPrimaryStage(model, "review");
  const toggled = toggleAgenticWorkbenchChatOpen(model);

  assert.equal(staged.primaryStage, "review");
  assert.equal(model.chatOpen, true);
  assert.equal(toggled.chatOpen, false);
  assert.equal(toggled.isNewThread, model.isNewThread);
  assert.equal(toggled.surface, model.surface);
  assert.equal(toggled.desktopNegotiationRailPersistent, true);
});

void test("tracks negotiation state with pending approvals and interruption visibility", () => {
  const model = createAgenticWorkbenchSessionModel({
    surface: "skill-studio",
    isNewThread: false,
  });
  const withNegotiation = updateAgenticWorkbenchNegotiationState(model, {
    pendingApprovals: 3,
    interruptionVisible: true,
  });

  assert.equal(model.negotiation.pendingApprovals, 0);
  assert.equal(model.negotiation.interruptionVisible, false);
  assert.equal(withNegotiation.negotiation.pendingApprovals, 3);
  assert.equal(withNegotiation.negotiation.interruptionVisible, true);
});
