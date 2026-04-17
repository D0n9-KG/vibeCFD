import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./route.ts", import.meta.url), "utf8");

void test("runtime-config route proxies canonical backend GET and PUT operations", () => {
  assert.match(source, /proxyBackendRequest/);
  assert.match(source, /export async function GET/);
  assert.match(source, /export async function PUT/);
  assert.match(source, /"\/api\/runtime-config"/);
});
