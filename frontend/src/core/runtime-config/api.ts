import { getBackendBaseURL } from "@/core/config";

export interface RuntimeConfigLeadAgentSummary {
  default_model: string | null;
  config_source: string;
  is_overridden: boolean;
}

export interface RuntimeConfigModelSummary {
  name: string;
  display_name?: string | null;
  description?: string | null;
  provider_key: string;
  provider_label: string;
  is_available: boolean;
  availability_reason?: string | null;
  supports_thinking: boolean;
  supports_reasoning_effort: boolean;
}

export interface RuntimeConfigProviderSummary {
  provider_key: string;
  label: string;
  model_names: string[];
  is_available: boolean;
  availability_reason?: string | null;
}

export interface RuntimeConfigStageRoleSummary {
  role_id: string;
  subagent_name: string;
  display_title: string;
  model_mode: "inherit" | "explicit";
  effective_model?: string | null;
  config_source: string;
  timeout_seconds: number;
}

export interface RuntimeConfigProvenanceSummary {
  config_path?: string | null;
  extensions_config_path?: string | null;
  runtime_overrides_path?: string | null;
  langgraph_url?: string | null;
}

export interface RuntimeConfigSummary {
  lead_agent: RuntimeConfigLeadAgentSummary;
  models: RuntimeConfigModelSummary[];
  providers: RuntimeConfigProviderSummary[];
  stage_roles: RuntimeConfigStageRoleSummary[];
  provenance: RuntimeConfigProvenanceSummary;
}

export interface RuntimeModelSummary {
  name: string;
  display_name?: string | null;
  description?: string | null;
  provider_key: "openai" | "openai-compatible" | "anthropic";
  provider_label: string;
  model: string;
  base_url?: string | null;
  has_api_key: boolean;
  supports_thinking: boolean;
  supports_reasoning_effort: boolean;
  supports_vision: boolean;
  is_available: boolean;
  availability_reason?: string | null;
  source: "config" | "runtime";
  is_editable: boolean;
}

export interface RuntimeConfigLeadAgentUpdateRequest {
  default_model: string | null;
}

export interface RuntimeConfigStageRoleUpdateRequest {
  role_id: string;
  model_mode: "inherit" | "explicit";
  model_name: string | null;
}

export interface RuntimeConfigUpdateRequest {
  lead_agent: RuntimeConfigLeadAgentUpdateRequest;
  stage_roles: RuntimeConfigStageRoleUpdateRequest[];
}

export interface RuntimeModelCreateRequest {
  name: string;
  display_name: string | null;
  description: string | null;
  provider_key: "openai" | "openai-compatible" | "anthropic";
  model: string;
  base_url: string | null;
  api_key: string | null;
  supports_thinking: boolean;
  supports_reasoning_effort: boolean;
  supports_vision: boolean;
}

export interface RuntimeModelUpdateRequest {
  display_name: string | null;
  description: string | null;
  provider_key: "openai" | "openai-compatible" | "anthropic";
  model: string;
  base_url: string | null;
  api_key: string | null;
  clear_api_key: boolean;
  supports_thinking: boolean;
  supports_reasoning_effort: boolean;
  supports_vision: boolean;
}

async function readJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage =
      errorData.detail ?? `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json() as Promise<T>;
}

export async function loadRuntimeConfig(): Promise<RuntimeConfigSummary> {
  const response = await fetch(`${getBackendBaseURL()}/api/runtime-config`);
  return readJsonResponse<RuntimeConfigSummary>(response);
}

export async function saveRuntimeConfig(
  request: RuntimeConfigUpdateRequest,
): Promise<RuntimeConfigSummary> {
  const response = await fetch(`${getBackendBaseURL()}/api/runtime-config`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  return readJsonResponse<RuntimeConfigSummary>(response);
}

export async function loadRuntimeModels(): Promise<RuntimeModelSummary[]> {
  const response = await fetch(`${getBackendBaseURL()}/api/runtime-models`);
  const payload = await readJsonResponse<{ models: RuntimeModelSummary[] }>(
    response,
  );
  return payload.models;
}

export async function createRuntimeModel(
  request: RuntimeModelCreateRequest,
): Promise<RuntimeModelSummary> {
  const response = await fetch(`${getBackendBaseURL()}/api/runtime-models`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  return readJsonResponse<RuntimeModelSummary>(response);
}

export async function updateRuntimeModel(
  modelName: string,
  request: RuntimeModelUpdateRequest,
): Promise<RuntimeModelSummary> {
  const response = await fetch(
    `${getBackendBaseURL()}/api/runtime-models/${encodeURIComponent(modelName)}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    },
  );

  return readJsonResponse<RuntimeModelSummary>(response);
}

export async function deleteRuntimeModel(modelName: string): Promise<void> {
  const response = await fetch(
    `${getBackendBaseURL()}/api/runtime-models/${encodeURIComponent(modelName)}`,
    {
      method: "DELETE",
    },
  );

  await readJsonResponse(response);
}
