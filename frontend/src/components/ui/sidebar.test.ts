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

void test("sidebar menu skeleton uses a hydration-safe fixed width instead of deriving width from useId", () => {
  assert.doesNotMatch(
    sidebarSource,
    /function SidebarMenuSkeleton[\s\S]*?React\.useId\(\)/,
  );
  assert.match(
    sidebarSource,
    /"--skeleton-width":\s*"68%"/,
  );
});
