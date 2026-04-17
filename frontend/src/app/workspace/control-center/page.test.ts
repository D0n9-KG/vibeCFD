import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./page.tsx", import.meta.url), "utf8");

void test("control center page renders the dedicated management shell", () => {
  assert.match(source, /ControlCenterShell/);
});
