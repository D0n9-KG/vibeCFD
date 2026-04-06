import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./submarine-pipeline.tsx", import.meta.url), "utf8");

void test("submarine chat rail keeps the message list clear of a larger pinned composer", () => {
  assert.match(source, /paddingBottom=\{160\}/);
  assert.match(source, /textareaClassName="min-h-28"/);
});
