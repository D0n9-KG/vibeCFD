import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./hooks.ts", import.meta.url), "utf8");

void test("skill graph cache is invalidated after publish and lifecycle updates", () => {
  assert.match(
    source,
    /export function usePublishSkill\(\)[\s\S]*?queryKey: \["skills", "graph"\][\s\S]*?exact: false/,
  );
  assert.match(
    source,
    /export function useUpdateSkillLifecycle\(\)[\s\S]*?queryKey: \["skills", "graph"\][\s\S]*?exact: false/,
  );
});
