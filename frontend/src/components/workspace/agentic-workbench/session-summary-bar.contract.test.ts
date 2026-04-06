import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(
  new URL("./session-summary-bar.tsx", import.meta.url),
  "utf8",
);

void test("session summary bar uses chinese approval and negotiation labels", () => {
  assert.match(source, /待确认事项/);
  assert.match(source, /协商区/);
  assert.doesNotMatch(source, /Pending approvals/);
  assert.doesNotMatch(source, /Interruption visible/);
});
