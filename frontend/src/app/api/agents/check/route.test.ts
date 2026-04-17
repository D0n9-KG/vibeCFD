import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const routeSource = await readFile(new URL("./route.ts", import.meta.url), "utf8");

void test("agent name check route combines canonical backend availability with legacy local collisions", () => {
  assert.match(routeSource, /proxyAgentsRequest/);
  assert.match(routeSource, /hasLegacyCustomAgent/);
  assert.match(routeSource, /available:\s*backendPayload\.available && !hasLegacyConflict/);
});
