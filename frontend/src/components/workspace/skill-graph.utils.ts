type SkillGraphRelationshipCounts = Record<string, number>;

export type SkillGraphOverview = {
  skillCount: number;
  enabledCount: number;
  publicCount: number;
  customCount: number;
  edgeCount: number;
  topRelationships: Array<{
    type: string;
    label: string;
    count: number;
  }>;
};

export type FocusedSkillGraphItem = {
  skillName: string;
  category: string;
  enabled: boolean;
  description: string;
  relationshipLabels: string[];
  strongestScore: number;
  reasons: string[];
};

function formatRelationshipLabel(value: string) {
  switch (value) {
    case "similar_to":
      return "Similar to";
    case "compose_with":
      return "Compose with";
    case "depend_on":
      return "Depends on";
    default:
      return value
        .split("_")
        .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`)
        .join(" ");
  }
}

export function buildSkillGraphOverview(graph?: {
  summary?: {
    skill_count?: number;
    enabled_skill_count?: number;
    public_skill_count?: number;
    custom_skill_count?: number;
    edge_count?: number;
    relationship_counts?: SkillGraphRelationshipCounts;
  };
} | null): SkillGraphOverview {
  const relationshipCounts = graph?.summary?.relationship_counts ?? {};
  const topRelationships = Object.entries(relationshipCounts)
    .map(([type, count]) => ({
      type,
      label: formatRelationshipLabel(type),
      count,
    }))
    .sort((left, right) => right.count - left.count || left.label.localeCompare(right.label))
    .slice(0, 3);

  return {
    skillCount: graph?.summary?.skill_count ?? 0,
    enabledCount: graph?.summary?.enabled_skill_count ?? 0,
    publicCount: graph?.summary?.public_skill_count ?? 0,
    customCount: graph?.summary?.custom_skill_count ?? 0,
    edgeCount: graph?.summary?.edge_count ?? 0,
    topRelationships,
  };
}

export function buildFocusedSkillGraphItems(graph?: {
  focus?: {
    related_skills?: Array<{
      skill_name: string;
      category: string;
      enabled: boolean;
      description: string;
      relationship_types: string[];
      strongest_score: number;
      reasons: string[];
    }>;
  } | null;
} | null): FocusedSkillGraphItem[] {
  const relatedSkills = graph?.focus?.related_skills ?? [];
  return [...relatedSkills]
    .sort(
      (left, right) =>
        right.strongest_score - left.strongest_score ||
        left.skill_name.localeCompare(right.skill_name),
    )
    .map((item) => ({
      skillName: item.skill_name,
      category: item.category,
      enabled: item.enabled,
      description: item.description,
      relationshipLabels: [...item.relationship_types]
        .map(formatRelationshipLabel)
        .sort((left, right) => left.localeCompare(right)),
      strongestScore: item.strongest_score,
      reasons: item.reasons,
    }));
}
