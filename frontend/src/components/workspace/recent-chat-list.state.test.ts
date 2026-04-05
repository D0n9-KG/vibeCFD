import assert from "node:assert/strict";
import test from "node:test";

import type { AgentThread } from "../../core/threads/types";

const { classifyThreadsForSidebar } = await import(
  new URL("./recent-chat-list.state.ts", import.meta.url).href
);

function makeThread(
  threadId: string,
  values: Partial<AgentThread["values"]> = {},
): AgentThread {
  return {
    thread_id: threadId,
    created_at: "",
    updated_at: "",
    status: "idle",
    metadata: {},
    values: {
      title: threadId,
      messages: [],
      artifacts: [],
      ...values,
    },
  } as AgentThread;
}

void test("classifyThreadsForSidebar keeps persisted submarine threads out of the generic chat bucket", () => {
  const groups = classifyThreadsForSidebar([
    makeThread("new-submarine", {
      workspace_kind: "submarine",
    }),
    makeThread("new-skill", {
      workspace_kind: "skill-studio",
    }),
    makeThread("plain-chat"),
  ]);

  assert.deepEqual(
    groups.map((group) => ({
      kind: group.kind,
      threadIds: group.threads.map((thread) => thread.thread_id),
    })),
    [
      {
        kind: "submarine",
        threadIds: ["new-submarine"],
      },
      {
        kind: "skill-studio",
        threadIds: ["new-skill"],
      },
      {
        kind: "chat",
        threadIds: ["plain-chat"],
      },
    ],
  );
});
