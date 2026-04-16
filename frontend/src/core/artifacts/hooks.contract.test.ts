import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./hooks.ts", import.meta.url), "utf8");

void test("useArtifactContent includes thread message progress in its query key so same-path artifacts refresh after new turns", () => {
  assert.match(source, /queryKey:\s*\["artifact", filepath, threadId, isMock, thread\.messages\.length\]/);
});
