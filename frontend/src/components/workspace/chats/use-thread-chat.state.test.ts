import assert from "node:assert/strict";
import test from "node:test";

import { deriveThreadChatRouteState } from "./use-thread-chat.state.ts";

test("deriveThreadChatRouteState creates a fresh thread id for new routes", () => {
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

test("deriveThreadChatRouteState reuses the route thread id for existing threads", () => {
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
