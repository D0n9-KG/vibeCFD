import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const moduleDir = path.dirname(fileURLToPath(import.meta.url));
const threadPath = path.resolve(
  moduleDir,
  "../../../../public/demo/threads/submarine-skill-studio-demo/thread.json",
);
const publishReadinessPath = path.resolve(
  moduleDir,
  "../../../../public/demo/threads/submarine-skill-studio-demo/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/publish-readiness.json",
);

void test("skill studio demo assets keep user-facing mock copy in Chinese", async () => {
  const threadSource = await readFile(threadPath, "utf8");
  const publishReadinessSource = await readFile(publishReadinessPath, "utf8");

  assert.doesNotMatch(threadSource, /Submarine Skill Studio Demo/);
  assert.doesNotMatch(threadSource, /We need a reusable skill/);
  assert.doesNotMatch(threadSource, /I drafted the/);
  assert.doesNotMatch(publishReadinessSource, /Skill structure is valid/);
  assert.doesNotMatch(publishReadinessSource, /Dry-run handoff is ready/);
  assert.doesNotMatch(publishReadinessSource, /UI metadata has been generated/);
});
