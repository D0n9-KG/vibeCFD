import assert from "node:assert/strict";
import test from "node:test";

import {
  deriveThreadStreamBinding,
  deriveThreadStreamSendState,
} from "./use-thread-stream.state.ts";

test("deriveThreadStreamBinding disables reconnect when the route has no thread id", () => {
  assert.deepEqual(
    deriveThreadStreamBinding({
      previousThreadId: "old-thread",
      requestedThreadId: undefined,
    }),
    {
      reconnectOnMount: false,
      shouldResetStarted: true,
      streamThreadId: null,
    },
  );
});

test("deriveThreadStreamBinding tracks explicit thread switches", () => {
  assert.deepEqual(
    deriveThreadStreamBinding({
      previousThreadId: "old-thread",
      requestedThreadId: "new-thread",
    }),
    {
      reconnectOnMount: true,
      shouldResetStarted: true,
      streamThreadId: "new-thread",
    },
  );
});

test("deriveThreadStreamBinding keeps reconnect enabled for the same thread", () => {
  assert.deepEqual(
    deriveThreadStreamBinding({
      previousThreadId: "same-thread",
      requestedThreadId: "same-thread",
    }),
    {
      reconnectOnMount: true,
      shouldResetStarted: false,
      streamThreadId: "same-thread",
    },
  );
});

test("deriveThreadStreamSendState waits for thread creation before signaling start on new routes", () => {
  assert.deepEqual(
    deriveThreadStreamSendState({
      activeThreadId: null,
      requestedThreadId: "generated-thread-id",
    }),
    {
      shouldSignalStartBeforeSubmit: false,
    },
  );
});

test("deriveThreadStreamSendState eagerly signals start for existing threads", () => {
  assert.deepEqual(
    deriveThreadStreamSendState({
      activeThreadId: "existing-thread-id",
      requestedThreadId: "existing-thread-id",
    }),
    {
      shouldSignalStartBeforeSubmit: true,
    },
  );
});
