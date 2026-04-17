import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const workspaceNavChatListSource = await readFile(
  new URL("./workspace-nav-chat-list.tsx", import.meta.url),
  "utf8",
);

void test("workspace nav reserves recent-thread space while threads are still loading", () => {
  assert.match(
    workspaceNavChatListSource,
    /const \{ data: threads = \[], isLoading \} = useThreads\(\);/,
  );
  assert.match(
    workspaceNavChatListSource,
    /\{\(isLoading \|\| recentThreads\.length > 0\) && \(/,
  );
  assert.match(
    workspaceNavChatListSource,
    /<SidebarMenuSkeleton showIcon \/>/,
  );
});

void test("agents internal routes link back to the control-center agents tab instead of a duplicate gallery", () => {
  assert.match(
    workspaceNavChatListSource,
    /\/workspace\/control-center\?tab=agents/,
  );
});
