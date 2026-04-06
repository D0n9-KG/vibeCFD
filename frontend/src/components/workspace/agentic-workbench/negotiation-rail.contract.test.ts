import assert from "node:assert/strict";
import test from "node:test";

const moduleUrl = new URL("./negotiation-rail.contract.ts", import.meta.url)
  .href;

void test("negotiation rail slot contract preserves shared slot order", async () => {
  const { NEGOTIATION_RAIL_SLOT_ORDER, getNegotiationRailRenderedSlotOrder } =
    await import(moduleUrl);

  assert.deepEqual(NEGOTIATION_RAIL_SLOT_ORDER, [
    "title",
    "question",
    "actions",
    "body",
    "footer",
  ]);
  assert.deepEqual(getNegotiationRailRenderedSlotOrder({ hasFooter: false }), [
    "title",
    "question",
    "actions",
    "body",
  ]);
  assert.deepEqual(getNegotiationRailRenderedSlotOrder({ hasFooter: true }), [
    "title",
    "question",
    "actions",
    "body",
    "footer",
  ]);
});
