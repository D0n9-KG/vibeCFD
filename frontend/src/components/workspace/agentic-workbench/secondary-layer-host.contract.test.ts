import assert from "node:assert/strict";
import test from "node:test";

const moduleUrl = new URL("./secondary-layer-host.contract.ts", import.meta.url)
  .href;

void test(
  "secondary layer selection falls back only when no active layer is requested",
  async () => {
    const { selectSecondaryLayer } = await import(moduleUrl);
    const layers = [
      { id: "trust", label: "Trust", content: "Layer A" },
      { id: "audit", label: "Audit", content: "Layer B" },
    ];

    const selection = selectSecondaryLayer({ layers });

    assert.equal(selection.kind, "active");
    if (selection.kind === "active") {
      assert.equal(selection.layer.id, "trust");
    }
  },
);

void test(
  "secondary layer selection reports missing when an explicit layer id is invalid",
  async () => {
    const { selectSecondaryLayer } = await import(moduleUrl);
    const layers = [{ id: "trust", label: "Trust", content: "Layer A" }];

    const selection = selectSecondaryLayer({
      layers,
      activeLayerId: "missing-layer",
    });

    assert.deepEqual(selection, {
      kind: "missing",
      activeLayerId: "missing-layer",
    });
  },
);

void test("secondary layer selection reports empty when no layers exist", async () => {
  const { selectSecondaryLayer } = await import(moduleUrl);

  const selection = selectSecondaryLayer({
    layers: [],
  });

  assert.deepEqual(selection, { kind: "empty" });
});

void test("secondary layer copy is chinese drawer language", async () => {
  const {
    DEFAULT_SECONDARY_LAYER_EMPTY_STATE,
    DEFAULT_SECONDARY_LAYER_MISSING_STATE,
  } = await import(moduleUrl);

  assert.match(DEFAULT_SECONDARY_LAYER_EMPTY_STATE, /详情/);
  assert.match(DEFAULT_SECONDARY_LAYER_MISSING_STATE, /详情/);
  assert.doesNotMatch(DEFAULT_SECONDARY_LAYER_EMPTY_STATE, /secondary/i);
});
