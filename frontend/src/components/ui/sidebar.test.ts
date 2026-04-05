import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const sidebarSource = await readFile(new URL("./sidebar.tsx", import.meta.url), "utf8");

void test("desktop sidebar root forwards caller styles so the reserved gap matches the fixed rail width", () => {
  assert.match(
    sidebarSource,
    /data-slot="sidebar"[\s\S]*?style=\{style\}[\s\S]*?<div[\s\S]*?data-slot="sidebar-gap"/,
  );
});
