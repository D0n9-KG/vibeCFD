import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(
  new URL("./submarine-operator-board.tsx", import.meta.url),
  "utf8",
);

void test("submarine operator board uses research-language labels instead of workflow-era chrome", () => {
  assert.doesNotMatch(source, /流程事件/);
  assert.doesNotMatch(source, /人工动作/);
  assert.doesNotMatch(source, /修正动作/);
  assert.match(source, /研究判断与后续安排/);
  assert.match(source, /当前判断/);
  assert.match(source, /修正事项/);
  assert.match(source, /研究记录/);
  assert.match(source, /待人工确认/);
});
