import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

void test("workspace header uses product-facing chrome copy without keeping the retired chat search action", async () => {
  const source = await readFile(
    new URL("./workspace-header.tsx", import.meta.url),
    "utf8",
  );

  assert.doesNotMatch(source, /Engineering Research Workspace/);
  assert.doesNotMatch(source, /DeerFlow Runtime/);
  assert.match(source, /当前界面/);
  assert.doesNotMatch(source, /搜索历史线程/);
});
