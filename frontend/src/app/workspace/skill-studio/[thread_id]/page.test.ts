import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const pageSource = await readFile(new URL("./page.tsx", import.meta.url), "utf8");

void test("cuts the skill studio thread route over to the new domain workbench", () => {
  assert.match(pageSource, /SkillStudioThreadRoute/);
  assert.doesNotMatch(pageSource, /SkillStudioWorkbenchShell/);
  assert.doesNotMatch(pageSource, /getSkillStudioWorkbenchLayout/);
});
