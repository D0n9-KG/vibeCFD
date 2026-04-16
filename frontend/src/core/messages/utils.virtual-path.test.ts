import assert from "node:assert/strict";
import test from "node:test";

const utils = await import(new URL("./utils.ts", import.meta.url).href);

void test("normalizeMessageDisplayText strips raw virtual paths from human copy even without extra workflow markers", () => {
  const normalized = utils.normalizeMessageDisplayText({
    type: "human",
    content: "请检查 `/mnt/user-data/uploads/suboff_solid.stl` 是否就是这次要用的几何文件。",
  });

  assert.doesNotMatch(normalized, /\/mnt\/user-data/i);
  assert.match(normalized, /suboff_solid\.stl/);
});
