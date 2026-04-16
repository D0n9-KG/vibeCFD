import { getBackendBaseURL } from "../config";

export type ThreadStreamingRecoveryResponse = {
  recovered: boolean;
  reason: string;
  latestRunStatus: string | null;
  runId: string | null;
  latestCommandExitAt: string | null;
};

export async function recoverThreadStreamingConflict(
  threadId: string,
): Promise<ThreadStreamingRecoveryResponse> {
  const response = await fetch(
    `${getBackendBaseURL()}/api/threads/${encodeURIComponent(threadId)}/recover`,
    {
      method: "POST",
      cache: "no-store",
    },
  );

  if (!response.ok) {
    const detail =
      (await response.json().catch(() => null))?.detail ??
      "Failed to recover the current thread.";
    throw new Error(detail);
  }

  return (await response.json()) as ThreadStreamingRecoveryResponse;
}
