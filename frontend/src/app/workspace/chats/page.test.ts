import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./page.tsx", import.meta.url), "utf8");

void test("workspace chats landing now redirects into control-center thread management instead of rendering a standalone chats surface", () => {
  assert.match(source, /redirect\(\s*"\/workspace\/control-center\?tab=threads"/);
  assert.doesNotMatch(source, /WorkspaceSurfacePage/);
});
