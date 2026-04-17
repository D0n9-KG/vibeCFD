import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("./threads-tab.tsx", import.meta.url), "utf8");

void test("threads tab focuses on canonical thread management and now exposes a real open-thread path alongside rename and delete actions", () => {
  assert.match(source, /useThreads/);
  assert.match(source, /useRenameThread/);
  assert.match(source, /useThreadDeletePreview/);
  assert.match(source, /useDeleteThread/);
  assert.match(source, /isManagedWorkbenchThread/);
  assert.match(source, /pathOfThreadByState/);
  assert.match(source, /<Link/);
  assert.match(source, /打开线程/);
  assert.doesNotMatch(source, /useOrphanThreadAudit/);
  assert.doesNotMatch(source, /buildOrphanAuditSummary/);
  assert.doesNotMatch(source, /filterAndSortOrphans/);
  assert.match(source, /Dialog/);
  assert.match(source, /Input/);
  assert.match(source, /partial_success/);
  assert.match(source, /WorkspaceStatePanel/);
});
