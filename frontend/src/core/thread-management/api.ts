import { getBackendBaseURL } from "@/core/config";

export interface ThreadStorageSliceSummary {
  exists: boolean;
  file_count: number;
  total_bytes: number;
}

export interface ThreadLocalStorageSummary {
  thread_dir: string;
  exists: boolean;
  workspace: ThreadStorageSliceSummary;
  uploads: ThreadStorageSliceSummary;
  outputs: ThreadStorageSliceSummary;
  total_files: number;
  total_bytes: number;
}

export interface ThreadDeletePreviewSummary {
  thread_id: string;
  impact_summary: {
    total_files: number;
    total_bytes: number;
  };
  local_storage: ThreadLocalStorageSummary;
  langgraph_state: {
    status: string;
    can_delete: boolean;
  };
}

export interface ThreadCascadeDeleteStep {
  key: string;
  status: string;
  detail: string;
}

export interface ThreadCascadeDeleteResult {
  success: boolean;
  message: string;
  thread_id: string;
  partial_success: boolean;
  steps: ThreadCascadeDeleteStep[];
}

export interface ThreadOrphanSummary {
  thread_id: string;
  thread_dir: string;
  total_files: number;
  total_bytes: number;
  langgraph_state: {
    status: string;
    can_delete: boolean;
  };
}

export interface ThreadOrphanAuditResult {
  orphans: ThreadOrphanSummary[];
}

export async function loadThreadDeletePreview(
  threadId: string,
): Promise<ThreadDeletePreviewSummary> {
  const response = await fetch(
    `${getBackendBaseURL()}/api/threads/${encodeURIComponent(threadId)}/delete-preview`,
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage =
      errorData.detail ?? `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
}

export async function deleteManagedThread(
  threadId: string,
): Promise<ThreadCascadeDeleteResult> {
  const response = await fetch(
    `${getBackendBaseURL()}/api/threads/${encodeURIComponent(threadId)}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage =
      errorData.detail ?? `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
}

export async function loadOrphanThreadAudit(): Promise<ThreadOrphanAuditResult> {
  const response = await fetch(`${getBackendBaseURL()}/api/threads/orphans`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage =
      errorData.detail ?? `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
}
