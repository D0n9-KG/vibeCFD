import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(
  new URL("./command-palette.tsx", import.meta.url),
  "utf8",
);

void test("command palette routes users into submarine work and thread management instead of the retired chats surface", () => {
  assert.match(source, /\/workspace\/submarine\/new/);
  assert.match(source, /\/workspace\/control-center\?tab=threads/);
  assert.doesNotMatch(source, /\/workspace\/chats/);
});
