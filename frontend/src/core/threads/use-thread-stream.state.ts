import type { Message } from "@langchain/langgraph-sdk";

import type { FileInMessage } from "../messages/utils";

import type { AgentThread } from "./types";
import type { ThreadWorkbenchKind } from "./utils";

export function deriveThreadStreamBinding({
  previousThreadId,
  requestedThreadId,
}: {
  previousThreadId?: string | null | undefined;
  requestedThreadId?: string | null | undefined;
}) {
  const streamThreadId = requestedThreadId ?? null;

  return {
    // useStream only reads reconnectOnMount on the initial mount, so new-thread
    // routes must opt in immediately to preserve resumable run metadata.
    reconnectOnMount: true,
    shouldResetStarted: (previousThreadId ?? null) !== streamThreadId,
    streamThreadId,
  };
}

export function deriveThreadStreamSendState({
  requestedThreadId,
  isNewThread = false,
}: {
  requestedThreadId: string;
  isNewThread?: boolean;
}) {
  const shouldCreateThreadBeforeSubmit = isNewThread;

  return {
    shouldCreateThreadBeforeSubmit,
    shouldSignalStartBeforeSubmit:
      !shouldCreateThreadBeforeSubmit && requestedThreadId.length > 0,
    shouldSignalStartAfterSubmitStart: shouldCreateThreadBeforeSubmit,
    shouldUseReboundThreadAfterCreate: shouldCreateThreadBeforeSubmit,
  };
}

export function deriveOptimisticMessagesAfterUpload({
  optimisticMessages,
  uploadedFiles,
}: {
  optimisticMessages: Message[];
  uploadedFiles: FileInMessage[];
}) {
  const [firstMessage, ...remainingMessages] = optimisticMessages;
  if (!firstMessage || firstMessage.type !== "human") {
    return optimisticMessages;
  }

  const nextHumanMessage: Message = {
    ...firstMessage,
    additional_kwargs: {
      ...firstMessage.additional_kwargs,
      files: uploadedFiles,
    },
  };

  return [
    nextHumanMessage,
    ...remainingMessages.filter(
      (message) => message.additional_kwargs?.element !== "task",
    ),
  ];
}

export function deriveThreadsAfterWorkbenchStart({
  threads,
  threadId,
  workbenchKind,
  updatedAt,
}: {
  threads: AgentThread[];
  threadId: string;
  workbenchKind: Exclude<ThreadWorkbenchKind, "chat">;
  updatedAt: string;
}) {
  const normalizeThread = (thread?: AgentThread): AgentThread => ({
    thread_id: thread?.thread_id ?? threadId,
    created_at: thread?.created_at ?? updatedAt,
    updated_at: updatedAt,
    status: thread?.status ?? "busy",
    metadata: thread?.metadata ?? {},
    interrupts: thread?.interrupts ?? {},
    config: thread?.config,
    error: thread?.error,
    values: {
      title: thread?.values?.title ?? "Untitled",
      messages: thread?.values?.messages ?? [],
      artifacts: thread?.values?.artifacts ?? [],
      ...thread?.values,
      workspace_kind: workbenchKind,
    },
  });

  const existingIndex = threads.findIndex(
    (thread) => thread.thread_id === threadId,
  );
  if (existingIndex < 0) {
    return [normalizeThread(), ...threads];
  }

  return threads.map((thread) =>
    thread.thread_id === threadId ? normalizeThread(thread) : thread,
  );
}
