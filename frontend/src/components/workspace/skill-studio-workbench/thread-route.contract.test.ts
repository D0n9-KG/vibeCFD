import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./thread-route.tsx", import.meta.url), "utf8");

void test("skill studio thread route wraps the workbench in a fixed viewport shell", () => {
  assert.match(source, /flex size-full min-h-0 flex-col overflow-hidden/);
  assert.match(source, /<main className="min-h-0 flex-1 overflow-hidden">/);
  assert.match(source, /max-w-\[1720px\]/);
});
