export type ThreadChatRouteState = {
  isNewThread: boolean;
  threadId: string;
};

export function deriveThreadChatRouteState(
  routeThreadId: string,
  createThreadId: () => string,
): ThreadChatRouteState {
  if (routeThreadId === "new") {
    return {
      isNewThread: true,
      threadId: createThreadId(),
    };
  }

  return {
    isNewThread: false,
    threadId: routeThreadId,
  };
}

export function deriveStartedThreadChatState(
  createdThreadId: string,
): ThreadChatRouteState {
  return {
    isNewThread: false,
    threadId: createdThreadId,
  };
}
