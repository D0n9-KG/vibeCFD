import type { ExecutionAttempt, RunEvent, RunSummary, TaskType } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8010";

export interface TaskFormInput {
  taskDescription: string;
  taskType: TaskType;
  geometryFamilyHint: string;
  operatingNotes: string;
  geometryFile?: File | null;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function submitTask(payload: TaskFormInput): Promise<RunSummary> {
  const formData = new FormData();
  formData.append("task_description", payload.taskDescription);
  formData.append("task_type", payload.taskType);
  formData.append("geometry_family_hint", payload.geometryFamilyHint);
  formData.append("operating_notes", payload.operatingNotes);
  if (payload.geometryFile) {
    formData.append("geometry_file", payload.geometryFile);
  }

  const response = await fetch(`${API_BASE}/api/tasks`, {
    method: "POST",
    body: formData
  });
  return parseResponse<RunSummary>(response);
}

export async function getRun(runId: string): Promise<RunSummary> {
  const response = await fetch(`${API_BASE}/api/runs/${runId}`);
  return parseResponse<RunSummary>(response);
}

export async function listRuns(): Promise<RunSummary[]> {
  const response = await fetch(`${API_BASE}/api/runs`);
  return parseResponse<RunSummary[]>(response);
}

export async function listRunEvents(runId: string): Promise<RunEvent[]> {
  const response = await fetch(`${API_BASE}/api/runs/${runId}/events`);
  return parseResponse<RunEvent[]>(response);
}

export async function listRunAttempts(runId: string): Promise<ExecutionAttempt[]> {
  const response = await fetch(`${API_BASE}/api/runs/${runId}/attempts`);
  return parseResponse<ExecutionAttempt[]>(response);
}

export async function confirmRun(runId: string, reviewerNotes: string): Promise<RunSummary> {
  const response = await fetch(`${API_BASE}/api/runs/${runId}/confirm`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      confirmed: true,
      reviewer_notes: reviewerNotes
    })
  });
  return parseResponse<RunSummary>(response);
}

export async function cancelRun(runId: string, reason: string): Promise<RunSummary> {
  const response = await fetch(`${API_BASE}/api/runs/${runId}/cancel`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ reason })
  });
  return parseResponse<RunSummary>(response);
}

export async function retryRun(runId: string): Promise<RunSummary> {
  const response = await fetch(`${API_BASE}/api/runs/${runId}/retry`, {
    method: "POST"
  });
  return parseResponse<RunSummary>(response);
}
