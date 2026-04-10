import assert from "node:assert/strict";
import test from "node:test";

const {
  createAgenticWorkbenchSessionModel,
  setAgenticWorkbenchMobileNegotiationRailVisible,
  toggleAgenticWorkbenchMobileNegotiationRailVisible,
} = await import(new URL("./session-model.ts", import.meta.url).href);

void test("builds shared session foundation with only shared chat visibility and pending approvals", () => {
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
  assert.equal(forNewThread.mobileNegotiationRailVisible, true);
  assert.equal(forExistingThread.mobileNegotiationRailVisible, false);
  assert.equal(forNewThread.pendingApprovals, 0);
  assert.equal(forExistingThread.pendingApprovals, 0);
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

void test("toggles mobile negotiation visibility without mutating surface metadata", () => {
  const model = createAgenticWorkbenchSessionModel({
    surface: "submarine",
    isNewThread: false,
  });
  const toggled = toggleAgenticWorkbenchMobileNegotiationRailVisible(model);

  assert.equal(model.mobileNegotiationRailVisible, false);
  assert.equal(toggled.mobileNegotiationRailVisible, true);
  assert.equal(toggled.surface, model.surface);
  assert.equal(toggled.isNewThread, model.isNewThread);
});
