import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

void test("workspace header uses product-facing chrome copy instead of raw runtime branding", async () => {
  const source = await readFile(new URL("./workspace-header.tsx", import.meta.url), "utf8");

  assert.doesNotMatch(source, /Engineering Research Workspace/);
  assert.doesNotMatch(source, /DeerFlow Runtime/);
  assert.match(source, /统一工作台/);
  assert.match(source, /当前界面/);
});
