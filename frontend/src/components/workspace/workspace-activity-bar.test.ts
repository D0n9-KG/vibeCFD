import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(
  new URL("./workspace-activity-bar.tsx", import.meta.url),
  "utf8",
);

void test("workspace activity bar renders only primary workspace surfaces", () => {
  assert.match(source, /PRIMARY_WORKSPACE_SURFACES/);
  assert.doesNotMatch(source, /\{\s*WORKSPACE_SURFACES\.map/);
});
