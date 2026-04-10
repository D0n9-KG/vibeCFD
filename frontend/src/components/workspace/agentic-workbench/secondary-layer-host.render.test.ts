import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./secondary-layer-host.tsx", import.meta.url), "utf8");

void test("secondary layer host does not add a duplicate drawer heading above already titled content", () => {
  assert.doesNotMatch(source, /详情抽屉/);
  assert.doesNotMatch(source, /selection\.layer\.label/);
});
