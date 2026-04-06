import assert from "node:assert/strict";
import test from "node:test";

const {
  createAgenticWorkbenchSessionModel,
  setAgenticWorkbenchMobileNegotiationRailVisible,
  selectAgenticWorkbenchPrimaryStage,
  updateAgenticWorkbenchNegotiationState,
  toggleAgenticWorkbenchMobileNegotiationRailVisible,
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
  assert.equal(forNewThread.mobileNegotiationRailVisible, true);
  assert.equal(forExistingThread.mobileNegotiationRailVisible, false);
  assert.equal(forNewThread.desktopNegotiationRailPersistent, true);
  assert.equal(forExistingThread.desktopNegotiationRailPersistent, true);
  assert.equal(forNewThread.negotiation.pendingApprovals, 0);
  assert.equal(forNewThread.negotiation.interruptionVisible, false);
  assert.equal(forNewThread.secondaryLayers.trustCriticalLayerId, "trust-critical");
  assert.deepEqual(forNewThread.secondaryLayers.available, ["trust-critical"]);
});

void test("supports stage selection groundwork and deterministic rail toggles", () => {
  const model = createAgenticWorkbenchSessionModel({
    surface: "submarine",
    isNewThread: false,
    mobileNegotiationRailVisibleOverride: true,
  });
  const staged = selectAgenticWorkbenchPrimaryStage(model, "review");
  const toggled = toggleAgenticWorkbenchMobileNegotiationRailVisible(model);

  assert.equal(staged.primaryStage, "review");
  assert.equal(model.mobileNegotiationRailVisible, true);
  assert.equal(toggled.mobileNegotiationRailVisible, false);
  assert.equal(toggled.isNewThread, model.isNewThread);
  assert.equal(toggled.surface, model.surface);
  assert.equal(toggled.desktopNegotiationRailPersistent, true);
});

void test("supports explicit mobile negotiation-rail visibility updates", () => {
  const model = createAgenticWorkbenchSessionModel({
    surface: "skill-studio",
    isNewThread: true,
  });
  const updated = setAgenticWorkbenchMobileNegotiationRailVisible(model, false);

  assert.equal(model.mobileNegotiationRailVisible, true);
  assert.equal(updated.mobileNegotiationRailVisible, false);
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
