import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const pageSource = await readFile(new URL("./page.tsx", import.meta.url), "utf8");

void test("hands the skill studio index route off to the new thread entry flow", () => {
  assert.match(pageSource, /redirect\(["'`]\/workspace\/skill-studio\/new["'`]\)/);
  assert.doesNotMatch(pageSource, /SkillStudioDashboard/);
});
