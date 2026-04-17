import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./page.tsx", import.meta.url), "utf8");

void test("legacy chat thread routes are reduced to a redirect shim instead of rendering the retired chat workspace", () => {
  assert.match(source, /resolveLegacyChatThreadHref/);
  assert.match(source, /router\.replace\(/);
  assert.match(source, /WorkspaceStatePanel/);
  assert.doesNotMatch(source, /<ChatBox/);
  assert.doesNotMatch(source, /<MessageList/);
});
