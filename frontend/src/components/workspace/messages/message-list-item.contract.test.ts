import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./message-list-item.tsx", import.meta.url), "utf8");

void test("message list item uses a chinese fallback label for empty task bubbles", () => {
  assert.doesNotMatch(source, /Task status/);
  assert.match(source, /任务状态/);
});
