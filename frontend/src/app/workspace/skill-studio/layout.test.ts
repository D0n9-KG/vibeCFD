import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./layout.tsx", import.meta.url), "utf8");

void test("wraps skill studio routes in the providers required by new and persisted threads", () => {
  assert.match(source, /SubtasksProvider/);
  assert.match(source, /ArtifactsProvider/);
  assert.match(source, /PromptInputProvider/);
});
