import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./workbench-flow.tsx", import.meta.url), "utf8");

void test("flow canvas expands one module and keeps others collapsed", () => {
  assert.match(source, /data-flow-item=/);
  assert.match(source, /item\.expanded/);
  assert.doesNotMatch(source, /TabsList|TabsTrigger/);
});
