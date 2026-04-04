import type { Agent } from "./types";

const BUILTIN_AGENT_DISPLAY_NAMES: Readonly<Record<string, string>> = {
  "codex-skill-creator": "Codex 技能创建器",
  "claude-code-skill-creator": "Claude Code 技能创建器",
};

const TOOL_GROUP_LABELS: Readonly<Record<string, string>> = {
  workspace: "工作区",
  skills: "技能",
  tools: "工具",
  memory: "记忆",
};

const MODEL_LABELS: Readonly<Record<string, string>> = {
  "gpt-5.4": "GPT-5.4",
  "claude-sonnet-4-6": "Claude Sonnet 4.6",
};

type AgentIdentity = Pick<Agent, "name" | "display_name">;

export function getAgentDisplayName(
  agent?: AgentIdentity | null,
  fallbackName?: string | null,
) {
  const displayName = agent?.display_name?.trim();
  if (displayName) {
    return displayName;
  }

  const resolvedName = agent?.name ?? fallbackName ?? "";
  return BUILTIN_AGENT_DISPLAY_NAMES[resolvedName] ?? resolvedName;
}

export function getAgentToolGroupLabel(group: string) {
  return TOOL_GROUP_LABELS[group] ?? group;
}

export function getAgentModelLabel(model?: string | null) {
  if (!model) {
    return "";
  }

  return MODEL_LABELS[model] ?? model;
}
