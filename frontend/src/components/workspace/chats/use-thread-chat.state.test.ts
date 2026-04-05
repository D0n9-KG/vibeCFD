import assert from "node:assert/strict";
import test from "node:test";

import {
  deriveStartedThreadChatState,
  deriveThreadChatRouteState,
} from "./use-thread-chat.state.ts";

void test("deriveThreadChatRouteState creates a fresh thread id for new routes", () => {
  let calls = 0;
  const state = deriveThreadChatRouteState("new", () => {
    calls += 1;
    return "generated-thread-id";
  });

  assert.deepEqual(state, {
    isNewThread: true,
    threadId: "generated-thread-id",
  });
  assert.equal(calls, 1);
});

void test("deriveThreadChatRouteState reuses the route thread id for existing threads", () => {
  let calls = 0;
  const state = deriveThreadChatRouteState("thread-123", () => {
    calls += 1;
    return "generated-thread-id";
  });

  assert.deepEqual(state, {
    isNewThread: false,
    threadId: "thread-123",
  });
  assert.equal(calls, 0);
});

void test("deriveStartedThreadChatState locks the local thread state to the created thread id", () => {
  assert.deepEqual(
    deriveStartedThreadChatState("created-thread-id"),
    {
      isNewThread: false,
      threadId: "created-thread-id",
    },
  );
});
