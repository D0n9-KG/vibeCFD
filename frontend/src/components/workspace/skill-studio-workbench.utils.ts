import {
  DEFAULT_SKILL_STUDIO_AGENT,
  labelOfSkillStudioAgentName,
  normalizeSkillStudioAgentLabel,
} from "./skill-studio-agent-options.ts";

export type SkillStudioArtifactGroup = {
  id: "package" | "validation" | "testing" | "publish" | "other";
  label: string;
  count: number;
  paths: string[];
};

export type SkillStudioStatusValue =
  | "ready_for_review"
  | "needs_revision"
  | "draft_only"
  | "ready_for_dry_run"
  | "draft_ready"
  | "published"
  | "rollback_available"
  | "blocked"
  | "passed"
  | "failed"
  | "pending"
  | (string & {});

export type SkillStudioReadinessInput = {
  errorCount: number;
  warningCount: number;
  validationStatus?: SkillStudioStatusValue | null;
  testStatus?: SkillStudioStatusValue | null;
  publishStatus?: SkillStudioStatusValue | null;
};

export type SkillStudioReadinessSummary = {
  progress: number;
  blockingCount: number;
  warningCount: number;
  validationLabel: string;
  testLabel: string;
  publishLabel: string;
};

export type SkillStudioAssistantIdentityInput = {
  draftAssistantMode?: string | null;
  draftAssistantLabel?: string | null;
  packageAssistantMode?: string | null;
  packageAssistantLabel?: string | null;
  stateAssistantMode?: string | null;
  stateAssistantLabel?: string | null;
};

export type SkillStudioAssistantIdentity = {
  assistantMode: string;
  assistantLabel: string;
};

export const SKILL_STUDIO_BINDING_ROLE_IDS = [
  "task-intelligence",
  "geometry-preflight",
  "solver-dispatch",
  "scientific-study",
  "experiment-compare",
  "scientific-verification",
  "result-reporting",
  "scientific-followup",
] as const;

export type SkillStudioBindingRoleId =
  (typeof SKILL_STUDIO_BINDING_ROLE_IDS)[number];

const BINDING_ROLE_LABELS: Record<string, string> = {
  "task-intelligence": "任务理解",
  "geometry-preflight": "几何预检",
  "solver-dispatch": "求解派发",
  "scientific-study": "科学研究",
  "experiment-compare": "实验对比",
  "scientific-verification": "科学验证",
  "result-reporting": "结果整理",
  "scientific-followup": "后续研究",
};

export function labelOfSkillStudioBindingRoleId(roleId: string) {
  return BINDING_ROLE_LABELS[roleId] ?? roleId;
}

export type SkillStudioLifecycleBindingTarget = {
  role_id: string;
  mode: string;
  target_skills: string[];
};

export type SkillStudioLifecycleRevision = {
  revision_id: string;
  published_at: string;
  archive_path: string;
  published_path: string;
  version_note: string;
  binding_targets: SkillStudioLifecycleBindingTarget[];
  enabled: boolean;
  source_thread_id?: string | null;
};

export type SkillStudioLifecycleSummary = {
  skill_name: string;
  enabled: boolean;
  binding_targets: SkillStudioLifecycleBindingTarget[];
  revision_count: number;
  binding_count: number;
  active_revision_id?: string | null;
  published_revision_id?: string | null;
  rollback_target_id?: string | null;
  draft_status: SkillStudioStatusValue;
  published_path?: string | null;
  last_published_at?: string | null;
  version_note?: string | null;
};

export type SkillStudioPublishPanelModel = {
  enabled: boolean;
  versionNote: string;
  bindingTargets: SkillStudioLifecycleBindingTarget[];
  explicitBindingRoleIds: string[];
  hasExplicitBindings: boolean;
  revisionCount: number;
  bindingCount: number;
  activeRevisionId: string | null;
  publishedRevisionId: string | null;
  rollbackTargetId: string | null;
  draftStatus: SkillStudioStatusValue;
  publishedPath: string | null;
  lastPublishedAt: string | null;
};

const STATUS_LABELS: Record<string, string> = {
  ready_for_review: "寰呭闃?",
  needs_revision: "闇€淇",
  draft_only: "浠呮湁鑽夌",
  ready_for_dry_run: "鍙瘯杩愯",
  draft_ready: "\u8349\u7a3f\u5c31\u7eea",
  published: "\u5df2\u53d1\u5e03",
  rollback_available: "\u53ef\u56de\u6eda",
  blocked: "宸查樆濉?",
  passed: "宸查€氳繃",
  failed: "鏈€氳繃",
  pending: "寰呭鐞?",
};

export function formatSkillStudioStatus(
  value?: SkillStudioStatusValue | null,
) {
  if (!value) {
    return "鏈煡";
  }
  const normalizedValue = value.trim().toLowerCase();
  if (STATUS_LABELS[normalizedValue]) {
    return STATUS_LABELS[normalizedValue];
  }
  return value
    .split("_")
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`)
    .join(" ");
}

function getArtifactGroupId(path: string): SkillStudioArtifactGroup["id"] {
  if (
    path.endsWith("/skill-draft.json") ||
    path.endsWith("/skill-lifecycle.json") ||
    path.endsWith("/skill-package.json") ||
    path.endsWith(".skill") ||
    path.endsWith("/SKILL.md") ||
    path.includes("/references/") ||
    path.endsWith("/agents/openai.yaml")
  ) {
    return "package";
  }
  if (path.includes("/validation-report.")) {
    return "validation";
  }
  if (path.includes("/test-matrix.")) {
    return "testing";
  }
  if (path.includes("/publish-readiness.")) {
    return "publish";
  }
  return "other";
}

const GROUP_LABELS: Record<SkillStudioArtifactGroup["id"], string> = {
  package: "鎶€鑳藉寘",
  validation: "鏍￠獙",
  testing: "娴嬭瘯",
  publish: "鍙戝竷",
  other: "鍏朵粬",
};

export function groupSkillStudioArtifacts(
  artifacts: string[],
): SkillStudioArtifactGroup[] {
  const buckets = new Map<SkillStudioArtifactGroup["id"], string[]>();

  for (const artifact of artifacts) {
    const id = getArtifactGroupId(artifact);
    const existing = buckets.get(id) ?? [];
    existing.push(artifact);
    buckets.set(id, existing);
  }

  const order: SkillStudioArtifactGroup["id"][] = [
    "package",
    "validation",
    "testing",
    "publish",
    "other",
  ];

  return order
    .map((id) => {
      const paths = buckets.get(id) ?? [];
      if (paths.length === 0) {
        return null;
      }
      return {
        id,
        label: GROUP_LABELS[id],
        count: paths.length,
        paths,
      };
    })
    .filter((group): group is SkillStudioArtifactGroup => group !== null);
}

function getStatusWeight(status?: SkillStudioStatusValue | null) {
  switch (status) {
    case "ready_for_review":
      return 100;
    case "ready_for_dry_run":
      return 100;
    case "published":
    case "rollback_available":
      return 100;
    case "draft_ready":
      return 60;
    case "needs_revision":
      return 45;
    case "draft_only":
      return 25;
    case "blocked":
      return 0;
    default:
      return 10;
  }
}

function getBlockingCount(statuses: Array<SkillStudioStatusValue | null | undefined>) {
  return statuses.reduce((count, status) => {
    return count + (status === "blocked" || status === "needs_revision" ? 1 : 0);
  }, 0);
}

export function buildSkillStudioReadinessSummary(
  input: SkillStudioReadinessInput,
): SkillStudioReadinessSummary {
  const baseProgress = Math.round(
    (getStatusWeight(input.validationStatus) +
      getStatusWeight(input.testStatus) +
      getStatusWeight(input.publishStatus)) /
      3,
  );
  const warningPenalty = Math.min(input.warningCount * 8, 16);
  const errorPenalty = Math.min(input.errorCount * 25, 60);

  return {
    progress: Math.max(0, baseProgress - warningPenalty - errorPenalty),
    blockingCount:
      input.errorCount +
      getBlockingCount([
        input.validationStatus,
        input.testStatus,
        input.publishStatus,
      ]),
    warningCount: input.warningCount,
    validationLabel: formatSkillStudioStatus(input.validationStatus),
    testLabel: formatSkillStudioStatus(input.testStatus),
    publishLabel: formatSkillStudioStatus(input.publishStatus),
  };
}

export function resolveSkillStudioAssistantIdentity(
  input: SkillStudioAssistantIdentityInput,
): SkillStudioAssistantIdentity {
  const assistantMode =
    input.draftAssistantMode ??
    input.packageAssistantMode ??
    input.stateAssistantMode ??
    DEFAULT_SKILL_STUDIO_AGENT;

  const assistantLabel = normalizeSkillStudioAgentLabel(
    input.draftAssistantLabel ??
      input.packageAssistantLabel ??
      input.stateAssistantLabel ??
      labelOfSkillStudioAgentName(assistantMode),
    assistantMode,
  );

  return {
    assistantMode,
    assistantLabel,
  };
}

function normalizeBindingTargets(
  bindingTargets:
    | Array<{
        role_id?: string | null;
        mode?: string | null;
        target_skills?: string[] | null;
      }>
    | null
    | undefined,
): SkillStudioLifecycleBindingTarget[] {
  if (!Array.isArray(bindingTargets)) {
    return [];
  }

  return bindingTargets
    .map((binding) => {
      const roleId =
        typeof binding?.role_id === "string" ? binding.role_id : null;
      const mode = typeof binding?.mode === "string" ? binding.mode : null;
      if (!roleId || !mode) {
        return null;
      }

      return {
        role_id: roleId,
        mode,
        target_skills: Array.isArray(binding?.target_skills)
          ? binding.target_skills.filter(
              (skill): skill is string => typeof skill === "string",
            )
          : [],
      };
    })
    .filter(
      (
        binding,
      ): binding is SkillStudioLifecycleBindingTarget => binding !== null,
    );
}

export function findSkillLifecycleSummary(
  lifecycleSummaries: SkillStudioLifecycleSummary[],
  skillName?: string | null,
): SkillStudioLifecycleSummary | null {
  if (!skillName) {
    return null;
  }
  return (
    lifecycleSummaries.find((summary) => summary.skill_name === skillName) ??
    null
  );
}

export function buildSkillStudioBindingTargets(
  skillName: string,
  explicitBindingRoleIds: string[],
): SkillStudioLifecycleBindingTarget[] {
  const explicitRoleIdSet = new Set(explicitBindingRoleIds);
  return SKILL_STUDIO_BINDING_ROLE_IDS.filter((roleId) =>
    explicitRoleIdSet.has(roleId),
  ).map((roleId) => ({
    role_id: roleId,
    mode: "explicit",
    target_skills: [skillName],
  }));
}

export function buildSkillStudioPublishPanelModel(input: {
  skillName: string;
  lifecycleSummary?: SkillStudioLifecycleSummary | null;
  stateVersionNote?: string | null;
  stateBindings?:
    | Array<{
        role_id?: string | null;
        mode?: string | null;
        target_skills?: string[] | null;
      }>
    | null;
  stateActiveRevisionId?: string | null;
  statePublishedRevisionId?: string | null;
}): SkillStudioPublishPanelModel {
  const lifecycleBindingTargets = normalizeBindingTargets(
    input.lifecycleSummary?.binding_targets,
  );
  const stateBindingTargets = normalizeBindingTargets(input.stateBindings);
  const bindingTargets =
    lifecycleBindingTargets.length > 0
      ? lifecycleBindingTargets
      : stateBindingTargets;
  const explicitBindingRoleIds = bindingTargets
    .filter((binding) => binding.mode === "explicit")
    .map((binding) => binding.role_id);

  return {
    enabled: input.lifecycleSummary?.enabled ?? true,
    versionNote:
      input.lifecycleSummary?.version_note ?? input.stateVersionNote ?? "",
    bindingTargets,
    explicitBindingRoleIds,
    hasExplicitBindings: explicitBindingRoleIds.length > 0,
    revisionCount: input.lifecycleSummary?.revision_count ?? 0,
    bindingCount:
      input.lifecycleSummary?.binding_count ?? bindingTargets.length,
    activeRevisionId:
      input.lifecycleSummary?.active_revision_id ??
      input.stateActiveRevisionId ??
      null,
    publishedRevisionId:
      input.lifecycleSummary?.published_revision_id ??
      input.statePublishedRevisionId ??
      null,
    rollbackTargetId: input.lifecycleSummary?.rollback_target_id ?? null,
    draftStatus: input.lifecycleSummary?.draft_status ?? "draft_only",
    publishedPath: input.lifecycleSummary?.published_path ?? null,
    lastPublishedAt: input.lifecycleSummary?.last_published_at ?? null,
  };
}
