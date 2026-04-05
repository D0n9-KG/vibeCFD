import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const workspaceContainerSource = await readFile(
  new URL("./workspace-container.tsx", import.meta.url),
  "utf8",
);

void test("surface cards opt out of flex shrinking so overview headers stay fully visible", () => {
  assert.match(
    workspaceContainerSource,
    /"shrink-0 rounded-\[28px\] border border-stone-200\/80 bg-white\/92 p-5 shadow-\[0_18px_44px_rgba\(15,23,42,0\.06\)\]"/,
  );
});
