import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./page.tsx", import.meta.url), "utf8");

void test("legacy new-chat routes now forward directly into the submarine workbench", () => {
  assert.match(source, /\/workspace\/submarine\/new/);
  assert.match(source, /mock=true/);
  assert.doesNotMatch(source, /ChatBox/);
});
