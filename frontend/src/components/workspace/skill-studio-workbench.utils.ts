import {
  DEFAULT_SKILL_STUDIO_AGENT,
  labelOfSkillStudioAgentName,
} from "./skill-studio-agent-options.ts";

export type SkillStudioArtifactGroup = {
  id: "package" | "validation" | "testing" | "publish" | "other";
  label: string;
  count: number;
  paths: string[];
};

export type SkillStudioReadinessInput = {
  errorCount: number;
  warningCount: number;
  validationStatus?: string | null;
  testStatus?: string | null;
  publishStatus?: string | null;
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
  ready_for_review: "待审阅",
  needs_revision: "需修订",
  draft_only: "仅有草稿",
  ready_for_dry_run: "可试运行",
  blocked: "已阻塞",
};

export function formatSkillStudioStatus(value?: string | null) {
  if (!value) {
    return "未知";
  }
  if (STATUS_LABELS[value]) {
    return STATUS_LABELS[value];
  }
  return value
    .split("_")
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`)
    .join(" ");
}

function getArtifactGroupId(path: string): SkillStudioArtifactGroup["id"] {
  if (
    path.endsWith("/skill-draft.json") ||
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
  package: "技能包",
  validation: "校验",
  testing: "测试",
  publish: "发布",
  other: "其他",
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

function getStatusWeight(status?: string | null) {
  switch (status) {
    case "ready_for_review":
      return 100;
    case "ready_for_dry_run":
      return 100;
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

function getBlockingCount(statuses: Array<string | null | undefined>) {
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
      input.errorCount + getBlockingCount([
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

  const assistantLabel =
    input.draftAssistantLabel ??
    input.packageAssistantLabel ??
    input.stateAssistantLabel ??
    labelOfSkillStudioAgentName(assistantMode);

  return {
    assistantMode,
    assistantLabel,
  };
}
