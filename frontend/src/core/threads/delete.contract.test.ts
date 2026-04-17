import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./hooks.ts", import.meta.url), "utf8");

void test("useDeleteThread delegates to the backend cascade-delete contract instead of split frontend deletion", () => {
  assert.match(
    source,
    /import\s+\{\s*deleteManagedThread\s*\}\s+from\s+"..\/thread-management\/api"/,
  );
  assert.match(source, /return deleteManagedThread\(threadId\)/);
  assert.doesNotMatch(source, /apiClient\.threads\.delete\(threadId\)/);
});
