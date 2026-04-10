import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const pageSource = await readFile(new URL("./page.tsx", import.meta.url), "utf8");

void test("mounts the shared skill studio thread route for the explicit new entry", () => {
  assert.match(pageSource, /SkillStudioThreadRoute/);
  assert.match(pageSource, /routeThreadId="new"/);
});
