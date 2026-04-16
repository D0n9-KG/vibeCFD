import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(
  new URL("./submarine-research-canvas.tsx", import.meta.url),
  "utf8",
);

void test("contract snapshot avoids inventing baseline defaults when revision data is still missing", () => {
  assert.match(source, /data-submarine-contract-snapshot="submarine"/);
  assert.doesNotMatch(source, /revisionLabel \?\? "r1"/);
  assert.doesNotMatch(source, /iterationModeLabel \?\? "基线"/);
});

void test("contract snapshot renders concrete capability gaps and delivery items", () => {
  assert.match(source, /capabilityGapLabels/);
  assert.match(source, /deliveryItems/);
});
