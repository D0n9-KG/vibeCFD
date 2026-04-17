import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const routeSource = await readFile(new URL("./route.ts", import.meta.url), "utf8");

void test("agents list route proxies canonical backend data and merges legacy custom agents", () => {
  assert.match(routeSource, /proxyAgentsRequest/);
  assert.match(routeSource, /listLegacyCustomAgents/);
  assert.match(routeSource, /mergeCanonicalAgentsWithLegacyAgents/);
});
