import fs from "node:fs/promises";
import path from "node:path";

import type {
  Agent,
  CreateAgentRequest,
  UpdateAgentRequest,
} from "@/core/agents/types";

const BUILTIN_AGENTS: Agent[] = [
  {
    name: "codex-skill-creator",
    description: "Built-in skill creation agent.",
    display_name: "Codex Skill Creator",
    model: "gpt-5.4",
    tool_groups: ["workspace", "skills"],
    soul: null,
  },
  {
    name: "claude-code-skill-creator",
    description: "Built-in Claude Code skill creation agent.",
    display_name: "Claude Code Skill Creator",
    model: "claude-sonnet-4-6",
    tool_groups: ["workspace", "skills"],
    soul: null,
  },
];

const STORE_DIR = path.join(process.cwd(), ".deerflow-ui");
const STORE_PATH = path.join(STORE_DIR, "agents.json");

function normalizeAgentName(name: string) {
  return name.trim().toLowerCase();
}

function validateAgentName(name: string) {
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name);
}

async function ensureStoreDir() {
  await fs.mkdir(STORE_DIR, { recursive: true });
}

async function readCustomAgents(): Promise<Agent[]> {
  try {
    const content = await fs.readFile(STORE_PATH, "utf8");
    const parsed = JSON.parse(content) as Agent[];
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return [];
    }
    throw error;
  }
}

async function writeCustomAgents(agents: Agent[]) {
  await ensureStoreDir();
  await fs.writeFile(STORE_PATH, JSON.stringify(agents, null, 2), "utf8");
}

function sortAgents(agents: Agent[]) {
  return [...agents].sort((a, b) => a.name.localeCompare(b.name));
}

export async function listStoredAgents(): Promise<Agent[]> {
  const customAgents = await readCustomAgents();
  return sortAgents([...BUILTIN_AGENTS, ...customAgents]);
}

export async function getStoredAgent(name: string): Promise<Agent | null> {
  const normalizedName = normalizeAgentName(name);
  const agents = await listStoredAgents();
  return (
    agents.find((agent) => normalizeAgentName(agent.name) === normalizedName) ??
    null
  );
}

export async function isAgentNameAvailable(name: string) {
  const normalizedName = normalizeAgentName(name);
  if (!normalizedName || !validateAgentName(normalizedName)) {
    return false;
  }

  const agent = await getStoredAgent(normalizedName);
  return agent === null;
}

export async function createStoredAgent(
  request: CreateAgentRequest,
): Promise<Agent> {
  const normalizedName = normalizeAgentName(request.name);
  if (!validateAgentName(normalizedName)) {
    throw new Error("Agent name must use lowercase letters, numbers, and hyphens only.");
  }

  if (!(await isAgentNameAvailable(normalizedName))) {
    throw new Error(`Agent '${normalizedName}' already exists.`);
  }

  const customAgents = await readCustomAgents();
  const agent: Agent = {
    name: normalizedName,
    description: request.description?.trim() || "Custom workspace agent.",
    display_name: request.display_name?.trim() || normalizedName,
    model: request.model?.trim() || null,
    tool_groups: request.tool_groups ?? null,
    soul: request.soul?.trim() || null,
  };

  customAgents.push(agent);
  await writeCustomAgents(sortAgents(customAgents));
  return agent;
}

export async function updateStoredAgent(
  name: string,
  request: UpdateAgentRequest,
): Promise<Agent> {
  const normalizedName = normalizeAgentName(name);
  if (BUILTIN_AGENTS.some((agent) => agent.name === normalizedName)) {
    throw new Error("Built-in agents cannot be edited from the workspace UI.");
  }

  const customAgents = await readCustomAgents();
  const index = customAgents.findIndex(
    (agent) => normalizeAgentName(agent.name) === normalizedName,
  );
  if (index === -1) {
    throw new Error(`Agent '${normalizedName}' not found.`);
  }

  const current = customAgents[index];
  if (!current) {
    throw new Error(`Agent '${normalizedName}' not found.`);
  }

  const updated: Agent = {
    ...current,
    description: request.description?.trim() ?? current.description,
    display_name: request.display_name?.trim() ?? current.display_name,
    model: request.model?.trim() ?? current.model,
    tool_groups: request.tool_groups ?? current.tool_groups,
    soul: request.soul?.trim() ?? current.soul,
  };

  customAgents[index] = updated;
  await writeCustomAgents(sortAgents(customAgents));
  return updated;
}

export async function deleteStoredAgent(name: string) {
  const normalizedName = normalizeAgentName(name);
  if (BUILTIN_AGENTS.some((agent) => agent.name === normalizedName)) {
    throw new Error("Built-in agents cannot be deleted from the workspace UI.");
  }

  const customAgents = await readCustomAgents();
  const nextAgents = customAgents.filter(
    (agent) => normalizeAgentName(agent.name) !== normalizedName,
  );
  if (nextAgents.length === customAgents.length) {
    throw new Error(`Agent '${normalizedName}' not found.`);
  }

  await writeCustomAgents(sortAgents(nextAgents));
}
