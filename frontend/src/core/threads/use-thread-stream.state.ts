import type { Message } from "@langchain/langgraph-sdk";

import type { FileInMessage } from "../messages/utils";

import type { AgentThread } from "./types";
import { resolveThreadDisplayTitle, type ThreadWorkbenchKind } from "./utils.ts";

const DEFAULT_UNTITLED_TITLE = "Untitled";

export function deriveThreadStreamBinding({
  previousThreadId,
  requestedThreadId,
}: {
  previousThreadId?: string | null;
  requestedThreadId?: string | null;
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

export function shouldPromoteStartedThreadRoute({
  pendingThreadId,
  activeThreadId,
  isLoading,
  persistedMessageCount,
  visibleMessageCount,
}: {
  pendingThreadId?: string | null;
  activeThreadId?: string | null;
  isLoading: boolean;
  persistedMessageCount: number;
  visibleMessageCount: number;
}) {
  return (
    pendingThreadId != null &&
    pendingThreadId.length > 0 &&
    activeThreadId === pendingThreadId &&
    (visibleMessageCount > 0 || (!isLoading && persistedMessageCount > 0))
  );
}

export function deriveThreadsAfterWorkbenchStart({
  threads,
  threadId,
  workbenchKind,
  updatedAt,
  provisionalTitle,
  initialMessages,
}: {
  threads: AgentThread[];
  threadId: string;
  workbenchKind: Exclude<ThreadWorkbenchKind, "chat">;
  updatedAt: string;
  provisionalTitle?: string | null;
  initialMessages?: Message[] | null;
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
      title: thread?.values?.title ?? provisionalTitle ?? "Untitled",
      messages: thread?.values?.messages ?? initialMessages ?? [],
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

export function deriveThreadsAfterSearchRefresh({
  previousThreads,
  incomingThreads,
}: {
  previousThreads: AgentThread[];
  incomingThreads: AgentThread[];
}) {
  const previousThreadsById = new Map(
    previousThreads.map((thread) => [thread.thread_id, thread] as const),
  );

  return incomingThreads.map((incomingThread) => {
    const previousThread = previousThreadsById.get(incomingThread.thread_id);
    if (!previousThread) {
      return incomingThread;
    }

    const incomingDisplayTitle = resolveThreadDisplayTitle(
      incomingThread.values?.title,
      DEFAULT_UNTITLED_TITLE,
      incomingThread.values?.messages,
    );
    const previousDisplayTitle = resolveThreadDisplayTitle(
      previousThread.values?.title,
      DEFAULT_UNTITLED_TITLE,
      previousThread.values?.messages,
    );

    const shouldPreserveReadablePreview =
      incomingDisplayTitle === DEFAULT_UNTITLED_TITLE &&
      previousDisplayTitle !== DEFAULT_UNTITLED_TITLE;

    if (
      !shouldPreserveReadablePreview &&
      incomingThread.values?.workspace_kind === previousThread.values?.workspace_kind
    ) {
      return incomingThread;
    }

    return {
      ...incomingThread,
      values: {
        ...(incomingThread.values ?? {}),
        workspace_kind:
          incomingThread.values?.workspace_kind ??
          previousThread.values?.workspace_kind,
        title: shouldPreserveReadablePreview
          ? previousDisplayTitle
          : incomingThread.values?.title,
        messages:
          shouldPreserveReadablePreview &&
          (incomingThread.values?.messages?.length ?? 0) === 0
            ? previousThread.values?.messages
            : incomingThread.values?.messages,
      },
    };
  });
}
