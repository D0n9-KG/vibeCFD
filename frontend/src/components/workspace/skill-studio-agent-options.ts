import type { Agent } from "@/core/agents";

export type SkillStudioAgentOption = {
  name: string;
  label: string;
  description: string;
};

export const DEFAULT_SKILL_STUDIO_AGENT = "codex-skill-creator";

const LEGACY_SKILL_STUDIO_AGENT_LABELS: Record<string, string> = {
  "Codex · Skill Creator": "Codex 技能创建器",
  "Codex Skill Creator": "Codex 技能创建器",
  "Claude Code · Skill Creator": "Claude Code 技能创建器",
  "Claude Code Skill Creator": "Claude Code 技能创建器",
};

function isSkillStudioAgent(agent: Agent) {
  return agent.name.endsWith("skill-creator");
}

function priorityOfSkillStudioAgent(name: string) {
  switch (name) {
    case "codex-skill-creator":
      return 0;
    case "claude-code-skill-creator":
      return 1;
    default:
      return 10;
  }
}

export function labelOfSkillStudioAgentName(name: string) {
  switch (name) {
    case "codex-skill-creator":
      return "Codex 技能创建器";
    case "claude-code-skill-creator":
      return "Claude Code 技能创建器";
    default:
      return name
        .split("-")
        .filter(Boolean)
        .map((part) => part[0]?.toUpperCase() + part.slice(1))
        .join(" ");
  }
}

function inferSkillStudioAgentNameFromLabel(label: string) {
  if (/claude code/i.test(label)) {
    return "claude-code-skill-creator";
  }
  if (/codex/i.test(label)) {
    return "codex-skill-creator";
  }
  return null;
}

export function normalizeSkillStudioAgentLabel(
  label?: string | null,
  assistantMode?: string | null,
) {
  const trimmedLabel = label?.trim() ?? "";
  if (trimmedLabel.length === 0) {
    return labelOfSkillStudioAgentName(
      assistantMode ?? DEFAULT_SKILL_STUDIO_AGENT,
    );
  }

  if (LEGACY_SKILL_STUDIO_AGENT_LABELS[trimmedLabel]) {
    return LEGACY_SKILL_STUDIO_AGENT_LABELS[trimmedLabel];
  }

  if (/skill creator/i.test(trimmedLabel)) {
    const inferredMode = inferSkillStudioAgentNameFromLabel(trimmedLabel);
    if (inferredMode) {
      return labelOfSkillStudioAgentName(inferredMode);
    }
  }

  return trimmedLabel;
}

export function buildSkillStudioAgentOptions(
  agents: Agent[],
): SkillStudioAgentOption[] {
  return agents
    .filter(isSkillStudioAgent)
    .sort((left, right) => {
      const priorityDifference =
        priorityOfSkillStudioAgent(left.name) -
        priorityOfSkillStudioAgent(right.name);
      if (priorityDifference !== 0) {
        return priorityDifference;
      }
      return left.name.localeCompare(right.name);
    })
    .map((agent) => {
      const displayName = agent.display_name?.trim() ?? "";
      return {
        name: agent.name,
        label:
          displayName.length > 0
            ? normalizeSkillStudioAgentLabel(displayName, agent.name)
            : labelOfSkillStudioAgentName(agent.name),
        description: agent.description,
      };
    });
}

export function resolveSkillStudioAgentSelection({
  selectedAgentName,
  persistedAssistantMode,
  options,
}: {
  selectedAgentName: string | null;
  persistedAssistantMode: string | null;
  options: SkillStudioAgentOption[];
}) {
  const optionNames = new Set(options.map((option) => option.name));
  if (persistedAssistantMode && optionNames.has(persistedAssistantMode)) {
    return persistedAssistantMode;
  }
  if (selectedAgentName && optionNames.has(selectedAgentName)) {
    return selectedAgentName;
  }
  if (optionNames.has(DEFAULT_SKILL_STUDIO_AGENT)) {
    return DEFAULT_SKILL_STUDIO_AGENT;
  }
  return options[0]?.name ?? DEFAULT_SKILL_STUDIO_AGENT;
}
