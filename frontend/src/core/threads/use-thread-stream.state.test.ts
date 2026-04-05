import assert from "node:assert/strict";
import test from "node:test";

import type { Message } from "@langchain/langgraph-sdk";

import type { AgentThread } from "./types.ts";
import {
  deriveOptimisticMessagesAfterUpload,
  deriveThreadsAfterWorkbenchStart,
  deriveThreadStreamBinding,
  deriveThreadStreamSendState,
  shouldPromoteStartedThreadRoute,
} from "./use-thread-stream.state.ts";

void test("deriveThreadStreamBinding keeps reconnect enabled for new-thread routes so active runs can rejoin after navigation", () => {
  assert.deepEqual(
    deriveThreadStreamBinding({
      previousThreadId: "old-thread",
      requestedThreadId: undefined,
    }),
    {
      reconnectOnMount: true,
      shouldResetStarted: true,
      streamThreadId: null,
    },
  );
});

void test("deriveThreadStreamBinding tracks explicit thread switches", () => {
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

void test("deriveThreadStreamBinding keeps reconnect enabled for the same thread", () => {
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

void test("deriveThreadStreamSendState flags new-thread submits to wait for the rebound stream binding", () => {
  assert.deepEqual(
    deriveThreadStreamSendState({
      requestedThreadId: "generated-thread-id",
      isNewThread: true,
    }),
    {
      shouldCreateThreadBeforeSubmit: true,
      shouldSignalStartBeforeSubmit: false,
      shouldSignalStartAfterSubmitStart: true,
      shouldUseReboundThreadAfterCreate: true,
    },
  );
});

void test("deriveThreadStreamSendState waits for thread creation before signaling start on new routes", () => {
  assert.deepEqual(
    deriveThreadStreamSendState({
      requestedThreadId: "generated-thread-id",
      isNewThread: true,
    }),
    {
      shouldCreateThreadBeforeSubmit: true,
      shouldSignalStartBeforeSubmit: false,
      shouldSignalStartAfterSubmitStart: true,
      shouldUseReboundThreadAfterCreate: true,
    },
  );
});

void test("deriveThreadStreamSendState eagerly signals start for existing threads", () => {
  assert.deepEqual(
    deriveThreadStreamSendState({
      requestedThreadId: "existing-thread-id",
      isNewThread: false,
    }),
    {
      shouldCreateThreadBeforeSubmit: false,
      shouldSignalStartBeforeSubmit: true,
      shouldSignalStartAfterSubmitStart: false,
      shouldUseReboundThreadAfterCreate: false,
    },
  );
});

void test("deriveOptimisticMessagesAfterUpload removes the stale uploading placeholder once files are uploaded", () => {
  const optimisticMessages: Message[] = [
    {
      type: "human",
      id: "opt-human",
      content: [{ type: "text", text: "Inspect the uploaded STL." }],
      additional_kwargs: {
        files: [
          {
            filename: "suboff_solid.stl",
            size: 0,
            status: "uploading",
          },
        ],
      },
    },
    {
      type: "ai",
      id: "opt-ai",
      content: "文件上传中，请稍候...",
      additional_kwargs: { element: "task" },
    },
  ];

  assert.deepEqual(
    deriveOptimisticMessagesAfterUpload({
      optimisticMessages,
      uploadedFiles: [
        {
          filename: "suboff_solid.stl",
          size: 1638084,
          path: "/mnt/user-data/uploads/suboff_solid.stl",
          status: "uploaded",
        },
      ],
    }),
    [
      {
        type: "human",
        id: "opt-human",
        content: [{ type: "text", text: "Inspect the uploaded STL." }],
        additional_kwargs: {
          files: [
            {
              filename: "suboff_solid.stl",
              size: 1638084,
              path: "/mnt/user-data/uploads/suboff_solid.stl",
              status: "uploaded",
            },
          ],
        },
      },
    ],
  );
});

void test("deriveThreadsAfterWorkbenchStart patches a created thread with a persisted workbench kind", () => {
  assert.deepEqual(
    deriveThreadsAfterWorkbenchStart({
      threads: [
        {
          thread_id: "new-submarine-thread",
          created_at: "2026-03-31T00:00:00.000Z",
          updated_at: "2026-03-31T00:00:00.000Z",
          status: "busy",
          metadata: {},
          values: null,
          interrupts: {},
        } as unknown as AgentThread,
      ],
      threadId: "new-submarine-thread",
      workbenchKind: "submarine",
      updatedAt: "2026-03-31T00:00:01.000Z",
    }),
    [
      {
        thread_id: "new-submarine-thread",
        created_at: "2026-03-31T00:00:00.000Z",
        updated_at: "2026-03-31T00:00:01.000Z",
        status: "busy",
        metadata: {},
        interrupts: {},
        config: undefined,
        error: undefined,
        values: {
          artifacts: [],
          messages: [],
          title: "Untitled",
          workspace_kind: "submarine",
        },
      },
    ],
  );
});

void test("shouldPromoteStartedThreadRoute waits until the first thread response has landed", () => {
  assert.equal(
    shouldPromoteStartedThreadRoute({
      pendingThreadId: "thread-123",
      isLoading: true,
      persistedMessageCount: 1,
    }),
    false,
  );
  assert.equal(
    shouldPromoteStartedThreadRoute({
      pendingThreadId: "thread-123",
      isLoading: false,
      persistedMessageCount: 0,
    }),
    false,
  );
  assert.equal(
    shouldPromoteStartedThreadRoute({
      pendingThreadId: "thread-123",
      isLoading: false,
      persistedMessageCount: 2,
    }),
    true,
  );
});
