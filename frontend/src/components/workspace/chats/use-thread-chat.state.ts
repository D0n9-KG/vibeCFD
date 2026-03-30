export function deriveThreadChatRouteState(
  routeThreadId: string,
  createThreadId: () => string,
) {
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
