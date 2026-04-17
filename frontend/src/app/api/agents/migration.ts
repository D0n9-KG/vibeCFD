import type { Agent } from "@/core/agents/types";

function normalizeAgentName(name: string) {
  return name.trim().toLowerCase();
}

export function markLegacyAgent(agent: Agent): Agent {
  return {
    ...agent,
    kind: agent.kind ?? "custom",
    is_builtin: false,
    is_editable: true,
    is_deletable: true,
    inventory_source: "legacy-local",
  };
}

export function mergeCanonicalAgentsWithLegacyAgents(
  canonicalAgents: Agent[],
  legacyCustomAgents: Agent[],
): Agent[] {
  const merged: Agent[] = canonicalAgents.map((agent) => ({
    ...agent,
    inventory_source: agent.inventory_source ?? "backend",
  }));
  const seen = new Set(merged.map((agent) => normalizeAgentName(agent.name)));

  for (const legacyAgent of legacyCustomAgents) {
    const normalizedName = normalizeAgentName(legacyAgent.name);
    if (seen.has(normalizedName)) {
      continue;
    }
    merged.push(markLegacyAgent(legacyAgent));
    seen.add(normalizedName);
  }

  return merged.sort((left, right) => left.name.localeCompare(right.name));
}
