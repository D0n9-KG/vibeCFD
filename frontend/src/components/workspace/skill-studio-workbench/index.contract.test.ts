import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./index.tsx", import.meta.url), "utf8");

void test("mounts skill studio on shared agentic workbench primitives", () => {
  assert.match(source, /WorkbenchShell/);
  assert.match(source, /NegotiationRail/);
  assert.match(source, /ThreadHeader/);
  assert.match(source, /SecondaryLayerHost/);
});
