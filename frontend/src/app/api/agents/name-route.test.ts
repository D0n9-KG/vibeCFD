import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const routeSource = await readFile(
  new URL("./[name]/route.ts", import.meta.url),
  "utf8",
);

void test("named agent route falls back to legacy local agents when canonical backend misses them", () => {
  assert.match(routeSource, /proxyAgentsRequest/);
  assert.match(routeSource, /getLegacyCustomAgent/);
  assert.match(routeSource, /updateLegacyCustomAgent/);
  assert.match(routeSource, /deleteLegacyCustomAgent/);
  assert.match(routeSource, /markLegacyAgent/);
});
