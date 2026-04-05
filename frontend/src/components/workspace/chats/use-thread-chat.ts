"use client";

import { useParams, usePathname, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { uuid } from "@/core/utils/uuid";

import {
  deriveStartedThreadChatState,
  deriveThreadChatRouteState,
} from "./use-thread-chat.state";

export function useThreadChat() {
  const { thread_id: threadIdFromPath } = useParams<{ thread_id: string }>();
  const pathname = usePathname();

  const searchParams = useSearchParams();
  const [threadState, setThreadState] = useState(() =>
    deriveThreadChatRouteState(threadIdFromPath, uuid),
  );

  useEffect(() => {
    setThreadState((currentState) => {
      const nextState = deriveThreadChatRouteState(threadIdFromPath, uuid);
      if (
        currentState.threadId === nextState.threadId &&
        currentState.isNewThread === nextState.isNewThread
      ) {
        return currentState;
      }
      return nextState;
    });
  }, [pathname, threadIdFromPath]);

  const isMock = searchParams.get("mock") === "true";
  return {
    isMock,
    isNewThread: threadState.isNewThread,
    markThreadStarted: (createdThreadId: string) => {
      setThreadState(deriveStartedThreadChatState(createdThreadId));
    },
    setIsNewThread: (isNewThread: boolean) => {
      setThreadState((currentState) => ({
        ...currentState,
        isNewThread,
      }));
    },
    threadId: threadState.threadId,
  };
}
