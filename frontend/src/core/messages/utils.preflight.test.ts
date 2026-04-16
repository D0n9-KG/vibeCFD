import assert from "node:assert/strict";
import test from "node:test";

const utils = await import(new URL("./utils.ts", import.meta.url).href);

void test("normalizeMessageDisplayText localizes standalone preflight approval wording in human-visible history", () => {
  const normalized = utils.normalizeMessageDisplayText({
    type: "human",
    content: "你下一步如果要继续，可以直接回复： “批准进入 preflight” 或 “批准开始执行”",
  });

  assert.doesNotMatch(normalized, /\bpreflight\b/i);
  assert.match(normalized, /预检/);
});
