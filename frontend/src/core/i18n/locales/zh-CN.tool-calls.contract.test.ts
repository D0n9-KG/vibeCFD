import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./zh-CN.ts", import.meta.url), "utf8");

void test("zh-CN tool call collapse copy refers to process records instead of steps", () => {
  assert.doesNotMatch(source, /查看其他 \$\{count\} 个步骤/);
  assert.doesNotMatch(source, /隐藏步骤/);
  assert.match(source, /查看其他 \$\{count\} 条过程记录/);
  assert.match(source, /隐藏过程记录/);
});
