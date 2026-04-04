import type { Agent, CreateAgentRequest, UpdateAgentRequest } from "./types";

const AGENTS_API_BASE = "/api/agents";

const BUILTIN_AGENT_COPY_MAP: Record<
  string,
  {
    display_name: string;
    description: string;
  }
> = {
  "codex-skill-creator": {
    display_name: "Codex 技能创建器",
    description:
      "Codex 专属技能创建代理，负责技能工作台中的技能编写、校验、测试与发布准备。",
  },
  "claude-code-skill-creator": {
    display_name: "Claude Code 技能创建器",
    description:
      "Claude Code 专属技能创建代理，负责技能工作台中的技能编写、校验、测试与发布准备。",
  },
};

function normalizeAgent(agent: Agent): Agent {
  const builtinCopy = BUILTIN_AGENT_COPY_MAP[agent.name];
  if (!builtinCopy) {
    return agent;
  }

  return {
    ...agent,
    display_name: builtinCopy.display_name,
    description: builtinCopy.description,
  };
}

export async function listAgents(): Promise<Agent[]> {
  const res = await fetch(AGENTS_API_BASE);
  if (!res.ok) throw new Error(`Failed to load agents: ${res.statusText}`);
  const data = (await res.json()) as { agents: Agent[] };
  return data.agents.map(normalizeAgent);
}

export async function getAgent(name: string): Promise<Agent> {
  const res = await fetch(`${AGENTS_API_BASE}/${encodeURIComponent(name)}`);
  if (!res.ok) throw new Error(`Agent '${name}' not found`);
  const agent = (await res.json()) as Agent;
  return normalizeAgent(agent);
}

export async function createAgent(request: CreateAgentRequest): Promise<Agent> {
  const res = await fetch(AGENTS_API_BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(err.detail ?? `Failed to create agent: ${res.statusText}`);
  }
  return res.json() as Promise<Agent>;
}

export async function updateAgent(
  name: string,
  request: UpdateAgentRequest,
): Promise<Agent> {
  const res = await fetch(`${AGENTS_API_BASE}/${encodeURIComponent(name)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(err.detail ?? `Failed to update agent: ${res.statusText}`);
  }
  return res.json() as Promise<Agent>;
}

export async function deleteAgent(name: string): Promise<void> {
  const res = await fetch(`${AGENTS_API_BASE}/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete agent: ${res.statusText}`);
}

export async function checkAgentName(
  name: string,
): Promise<{ available: boolean; name: string }> {
  const res = await fetch(
    `${AGENTS_API_BASE}/check?name=${encodeURIComponent(name)}`,
  );
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(
      err.detail ?? `Failed to check agent name: ${res.statusText}`,
    );
  }
  return res.json() as Promise<{ available: boolean; name: string }>;
}
