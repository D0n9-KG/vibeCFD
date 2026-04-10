import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./api.ts", import.meta.url), "utf8");

void test("recordDryRunEvidence does not hardcode empty message_ids defaults", () => {
  assert.match(source, /recordDryRunEvidence/);
  assert.doesNotMatch(source, /message_ids:\s*\[\]/);
});
