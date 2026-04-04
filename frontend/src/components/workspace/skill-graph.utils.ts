import { localizeWorkspaceDisplayText } from "../../core/i18n/workspace-display.ts";

type SkillGraphRelationshipCounts = Record<string, number>;

export type SkillGraphWorkbenchFilter = 
  | "all"
  | "upstream"
  | "downstream"
  | "similar"
  | "high-impact";

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

export type SkillGraphWorkbenchNode = {
  id: string;
  skillName: string;
  category: string;
  enabled: boolean;
  description: string;
  relationshipLabels: string[];
  strongestScore: number;
  reasons: string[];
  isFocus: boolean;
  x: number;
  y: number;
};

export type SkillGraphWorkbenchEdge = {
  id: string;
  source: string;
  target: string;
  label: string;
  score: number;
};

export type SkillGraphWorkbenchModel = {
  focusSkillName: string | null;
  nodes: SkillGraphWorkbenchNode[];
  edges: SkillGraphWorkbenchEdge[];
};

function formatRelationshipLabel(value: string) {
  switch (value) {
    case "similar_to":
      return "能力相似";
    case "compose_with":
      return "组合使用";
    case "depend_on":
      return "依赖于";
    default:
      return value
        .split("_")
        .join(" / ");
  }
}

function filterFocusedItems(
  items: FocusedSkillGraphItem[],
  filter: SkillGraphWorkbenchFilter,
) {
  switch (filter) {
    case "upstream":
      return items.filter((item) =>
        item.relationshipLabels.some((label) => label === "依赖于"),
      );
    case "downstream":
      return items.filter(
        (item) =>
          !item.relationshipLabels.some((label) => label === "依赖于") &&
          !item.relationshipLabels.some((label) => label === "能力相似"),
      );
    case "similar":
      return items.filter((item) =>
        item.relationshipLabels.some((label) => label === "能力相似"),
      );
    case "high-impact":
      return items.filter((item) => item.strongestScore >= 0.75);
    case "all":
    default:
      return items;
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
      skillName: localizeWorkspaceDisplayText(item.skill_name),
      category: item.category,
      enabled: item.enabled,
      description: localizeWorkspaceDisplayText(item.description),
      relationshipLabels: [...item.relationship_types]
        .map(formatRelationshipLabel)
        .sort((left, right) => left.localeCompare(right)),
      strongestScore: item.strongest_score,
      reasons: (item.reasons ?? []).map((reason) =>
        localizeWorkspaceDisplayText(reason),
      ),
    }));
}

export function buildSkillGraphWorkbenchModel(
  graph?: {
    focus?: {
      skill_name?: string;
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
  } | null,
  filter: SkillGraphWorkbenchFilter = "all",
): SkillGraphWorkbenchModel {
  const focusSkillName = graph?.focus?.skill_name ?? null;
  const focusedItems = filterFocusedItems(
    buildFocusedSkillGraphItems(graph),
    filter,
  );

  if (!focusSkillName) {
    return {
      focusSkillName: null,
      nodes: [],
      edges: [],
    };
  }

  const focusNode: SkillGraphWorkbenchNode = {
    id: focusSkillName,
    skillName: localizeWorkspaceDisplayText(focusSkillName),
    category: "焦点",
    enabled: true,
    description: "来自当前技能工作台线程的焦点技能。",
    relationshipLabels: [],
    strongestScore: 1,
    reasons: ["当前工作台焦点"],
    isFocus: true,
    x: 50,
    y: 18,
  };

  const relatedNodes = focusedItems.map((item, index, allItems) => {
    const total = Math.max(allItems.length, 1);
    const x = total === 1 ? 50 : 14 + (72 / (total - 1)) * index;
    const y = 72;

      return {
        id: item.skillName,
        skillName: item.skillName,
      category: item.category,
      enabled: item.enabled,
      description: item.description,
      relationshipLabels: item.relationshipLabels,
      strongestScore: item.strongestScore,
      reasons: item.reasons,
      isFocus: false,
      x,
      y,
    } satisfies SkillGraphWorkbenchNode;
  });

  const edges = relatedNodes.map((node) => ({
    id: `${focusSkillName}-${node.skillName}`,
    source: focusSkillName,
    target: node.skillName,
    label: node.relationshipLabels.join(" / ") || "相关",
    score: node.strongestScore,
  }));

  return {
    focusSkillName,
    nodes: [focusNode, ...relatedNodes],
    edges,
  };
}
