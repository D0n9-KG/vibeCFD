import assert from "node:assert/strict";
import test from "node:test";

const { WORKBENCH_COPY } = await import(
  new URL("./workbench-copy.ts", import.meta.url).href,
);

void test("shared workbench copy is Chinese and chat-first", () => {
  assert.equal(WORKBENCH_COPY.common.negotiationRailTitle, "协商区");
  assert.equal(
    WORKBENCH_COPY.common.negotiationHint,
    "可随时在协商区输入修改意见，主智能体会停止当前推进并重新协商。",
  );
  assert.equal("submarine" in WORKBENCH_COPY, false);
  assert.equal(WORKBENCH_COPY.skillStudio.modules.lifecycle, "版本与回退");
});
