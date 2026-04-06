import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const moduleUrl = new URL("./workbench-shell.contract.ts", import.meta.url).href;
const moduleDir = path.dirname(fileURLToPath(import.meta.url));

void test("declares named shell zones for nav, main stage, and negotiation rail only", async () => {
  const { WORKBENCH_SHELL_ZONE_ORDER, getWorkbenchShellZoneClassNames } =
    await import(moduleUrl);
  const classes = getWorkbenchShellZoneClassNames();

  assert.deepEqual(WORKBENCH_SHELL_ZONE_ORDER, ["nav", "main", "negotiation"]);
  assert.ok(classes.root.includes("grid"));
  assert.ok(classes.nav.includes("agentic-workbench-zone-nav"));
  assert.ok(classes.main.includes("agentic-workbench-zone-main"));
  assert.ok(classes.negotiation.includes("agentic-workbench-zone-negotiation"));
});

void test("keeps shell contract stage-agnostic instead of stage-tab driven", async () => {
  const source = await readFile(
    path.join(moduleDir, "workbench-shell.tsx"),
    "utf-8",
  );

  assert.match(source, /data-workbench-zone="nav"/);
  assert.match(source, /data-workbench-zone="main"/);
  assert.match(source, /data-workbench-zone="negotiation"/);
  assert.doesNotMatch(source, /data-workbench-zone="secondary"/);
  assert.doesNotMatch(source, /@radix-ui\/react-tabs/);
  assert.doesNotMatch(source, /\bstageTabs\b/i);
  assert.doesNotMatch(source, /\bstage-tab\b/i);
});

void test("stage 2 barrel exposes shell primitives but not stage 1 session model", async () => {
  const source = await readFile(path.join(moduleDir, "index.ts"), "utf-8");

  assert.match(source, /export \* from "\.\/workbench-shell"/);
  assert.match(source, /export \* from "\.\/negotiation-rail"/);
  assert.match(source, /export \* from "\.\/secondary-layer-host"/);
  assert.doesNotMatch(source, /export \* from "\.\/session-model"/);
});
