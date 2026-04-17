import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./api.ts", import.meta.url), "utf8");

void test("thread management api exposes delete preview, cascade delete, and orphan audit endpoints", () => {
  assert.match(source, /\/delete-preview/);
  assert.match(source, /\/api\/threads\/orphans/);
  assert.match(source, /\/api\/threads\/\$\{encodeURIComponent\(threadId\)\}/);
});
