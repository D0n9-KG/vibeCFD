import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const uploadRouteSource = await readFile(
  new URL("./[thread_id]/uploads/route.ts", import.meta.url),
  "utf8",
);
const uploadListRouteSource = await readFile(
  new URL("./[thread_id]/uploads/list/route.ts", import.meta.url),
  "utf8",
);
const uploadDeleteRouteSource = await readFile(
  new URL("./[thread_id]/uploads/[filename]/route.ts", import.meta.url),
  "utf8",
);
const artifactRouteSource = await readFile(
  new URL("./[thread_id]/artifacts/[[...artifact_path]]/route.ts", import.meta.url),
  "utf8",
);
const recoveryRouteSource = await readFile(
  new URL("./[thread_id]/recover/route.ts", import.meta.url),
  "utf8",
);
const authHelperSource = await readFile(new URL("./_auth.ts", import.meta.url), "utf8");

void test("thread-scoped file routes require a session before touching thread files", () => {
  assert.match(authHelperSource, /getSession/);
  assert.match(authHelperSource, /Unauthorized/);
  assert.match(authHelperSource, /401/);

  for (const source of [
    uploadRouteSource,
    uploadListRouteSource,
    uploadDeleteRouteSource,
    artifactRouteSource,
    recoveryRouteSource,
  ]) {
    assert.match(source, /requireThreadRouteSession/);
  }
});
