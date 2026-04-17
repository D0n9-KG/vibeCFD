import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./input-box.tsx", import.meta.url), "utf8");

void test("input box falls back to the canonical runtime-config default model before using the first configured model", () => {
  assert.match(source, /useRuntimeConfig/);
  assert.match(source, /runtimeConfig\?\.lead_agent\.default_model/);
});
