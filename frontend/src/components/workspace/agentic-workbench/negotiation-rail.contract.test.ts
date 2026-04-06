import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const moduleUrl = new URL("./negotiation-rail.contract.ts", import.meta.url)
  .href;
const railSource = await readFile(new URL("./negotiation-rail.tsx", import.meta.url), "utf8");

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

void test("negotiation rail clips its body slot so chat internals can scroll without moving the rail", () => {
  assert.match(railSource, /slot === "body" \? "min-h-0 flex-1 overflow-hidden" : undefined/);
});
