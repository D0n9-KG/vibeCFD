export interface Agent {
  name: string;
  description: string;
  display_name?: string | null;
  model: string | null;
  tool_groups: string[] | null;
  soul?: string | null;
  kind?: "builtin" | "custom";
  is_builtin?: boolean;
  is_editable?: boolean;
  is_deletable?: boolean;
  source_path?: string | null;
  inventory_source?: "backend" | "legacy-local";
}

export interface AgentLegacyStoreSummary {
  exists: boolean;
  path: string | null;
  agent_count: number;
}

export interface AgentInventoryResponse {
  agents: Agent[];
  legacy_store?: AgentLegacyStoreSummary;
}

export interface CreateAgentRequest {
  name: string;
  description?: string;
  display_name?: string | null;
  model?: string | null;
  tool_groups?: string[] | null;
  soul?: string;
}

export interface UpdateAgentRequest {
  description?: string | null;
  display_name?: string | null;
  model?: string | null;
  tool_groups?: string[] | null;
  soul?: string | null;
}
