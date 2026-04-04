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
