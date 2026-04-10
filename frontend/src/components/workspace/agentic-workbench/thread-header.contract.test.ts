import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./thread-header.tsx", import.meta.url), "utf8");

void test("thread header drops the redundant strip label", () => {
  assert.doesNotMatch(source, /浠诲姟鎸囨尌鏉?/);
  assert.doesNotMatch(source, /Agentic Thread/);
  assert.match(source, /statusLabel/);
});
