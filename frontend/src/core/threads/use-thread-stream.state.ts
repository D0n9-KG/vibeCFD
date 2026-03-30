export function deriveThreadStreamBinding({
  previousThreadId,
  requestedThreadId,
}: {
  previousThreadId?: string | null | undefined;
  requestedThreadId?: string | null | undefined;
}) {
  const streamThreadId = requestedThreadId ?? null;

  return {
    reconnectOnMount: streamThreadId !== null,
    shouldResetStarted: (previousThreadId ?? null) !== streamThreadId,
    streamThreadId,
  };
}

export function deriveThreadStreamSendState({
  activeThreadId,
  requestedThreadId,
}: {
  activeThreadId?: string | null | undefined;
  requestedThreadId: string;
}) {
  return {
    shouldSignalStartBeforeSubmit:
      (activeThreadId ?? null) === requestedThreadId,
  };
}
