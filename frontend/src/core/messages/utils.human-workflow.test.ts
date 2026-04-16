import assert from "node:assert/strict";
import test from "node:test";

const utils = await import(new URL("./utils.ts", import.meta.url).href);

void test("normalizeMessageDisplayText localizes human workflow copy with internal paths and execution modes", () => {
  const normalized = utils.normalizeMessageDisplayText({
    type: "human",
    content:
      "我已检测到你上传了潜艇几何文件 /mnt/user-data/uploads/suboff_solid.stl，请确认这一步是保持 plan-only，还是进入 preflight_then_execute。",
  });

  assert.doesNotMatch(
    normalized,
    /\/mnt\/user-data|plan-only|preflight_then_execute/i,
  );
  assert.match(normalized, /suboff_solid\.stl/);
});
