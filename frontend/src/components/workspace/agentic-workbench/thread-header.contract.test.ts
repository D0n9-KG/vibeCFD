import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./thread-header.tsx", import.meta.url), "utf8");

void test("thread header uses chinese command-strip copy", () => {
  assert.match(source, /任务指挥条/);
  assert.doesNotMatch(source, /Agentic Thread/);
});
