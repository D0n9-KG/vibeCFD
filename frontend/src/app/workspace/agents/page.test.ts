import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./page.tsx", import.meta.url), "utf8");

void test("agents landing page redirects into the control-center agents tab instead of rendering a duplicate gallery", () => {
  assert.match(source, /redirect\("\/workspace\/control-center\?tab=agents"\)/);
  assert.doesNotMatch(source, /AgentGallery/);
});
