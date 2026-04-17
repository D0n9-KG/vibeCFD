import { useQuery } from "@tanstack/react-query";

import { loadOrphanThreadAudit, loadThreadDeletePreview } from "./api";

export function useThreadDeletePreview({
  threadId,
  enabled = true,
}: {
  threadId?: string | null;
  enabled?: boolean;
}) {
  return useQuery({
    queryKey: ["threads", "delete-preview", threadId ?? "__missing__"],
    queryFn: () => loadThreadDeletePreview(threadId!),
    enabled: enabled && Boolean(threadId),
  });
}

export function useOrphanThreadAudit({ enabled = true }: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: ["threads", "orphans"],
    queryFn: loadOrphanThreadAudit,
    enabled,
  });
}
