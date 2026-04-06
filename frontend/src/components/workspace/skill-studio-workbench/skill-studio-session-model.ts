import { WORKBENCH_COPY } from "../agentic-workbench/workbench-copy.ts";
import {
  DEFAULT_SKILL_STUDIO_AGENT,
  labelOfSkillStudioAgentName,
} from "../skill-studio-agent-options.ts";

export const SKILL_STUDIO_MODULE_ORDER = [
  "intent",
  "draft",
  "evaluation",
  "release-prep",
  "lifecycle",
  "graph",
] as const;

export type SkillStudioModuleId = (typeof SKILL_STUDIO_MODULE_ORDER)[number];

export type SkillStudioLifecycleModule = {
  id: SkillStudioModuleId;
  title: string;
  status: string;
  summary: string;
  expanded: boolean;
};

export type SkillStudioSessionModel = {
  activeModuleId: SkillStudioModuleId;
  modules: readonly SkillStudioLifecycleModule[];
  assistant: {
    mode: string;
    label: string;
    locked: boolean;
  };
  summary: {
    hasDraftArtifact: boolean;
    validationStatus: string;
    testStatus: string;
    publishStatus: string;
    graphRelationshipCount: number;
  };
  negotiation: {
    pendingApprovalCount: number;
    interruptionVisible: boolean;
    question: string | null;
  };
};

export type BuildSkillStudioSessionModelInput = {
  isNewThread: boolean;
  persistedAssistantMode: string | null;
  hasDraftArtifact: boolean;
  validationStatus: string | null;
  testStatus: string | null;
  publishStatus: string | null;
  errorCount: number;
  warningCount: number;
  blockingCount: number;
  graphRelationshipCount: number;
};

const LIFECYCLE_READY_STATUSES = new Set([
  "draft_ready",
  "published",
  "ready_for_review",
  "rollback_available",
]);

function normalizeStatus(value: string | null | undefined, fallback = "draft_only") {
  const normalized = value?.trim();
  return normalized && normalized.length > 0 ? normalized : fallback;
}

function hasBlockingNegotiation(input: BuildSkillStudioSessionModelInput) {
  return (
    input.blockingCount > 0 ||
    input.errorCount > 0 ||
    normalizeStatus(input.validationStatus) === "needs_revision" ||
    normalizeStatus(input.testStatus) === "failed" ||
    normalizeStatus(input.publishStatus) === "blocked"
  );
}

function resolveActiveModuleId(
  input: BuildSkillStudioSessionModelInput,
  blocking: boolean,
): SkillStudioModuleId {
  if (input.isNewThread || !input.hasDraftArtifact) {
    return "intent";
  }

  if (blocking) {
    return "evaluation";
  }

  if (LIFECYCLE_READY_STATUSES.has(normalizeStatus(input.publishStatus))) {
    return "lifecycle";
  }

  if (
    normalizeStatus(input.validationStatus) !== "draft_only" ||
    normalizeStatus(input.testStatus) !== "draft_only"
  ) {
    return "release-prep";
  }

  return "draft";
}

function buildNegotiationQuestion(
  input: BuildSkillStudioSessionModelInput,
  blocking: boolean,
) {
  if (!blocking) {
    return null;
  }

  if (input.errorCount > 0 || normalizeStatus(input.validationStatus) === "needs_revision") {
    return "仍有验证问题待修正，先在协商区补齐证据与规则。";
  }

  if (normalizeStatus(input.testStatus) === "failed") {
    return "场景测试尚未通过，先处理阻塞用例。";
  }

  if (normalizeStatus(input.publishStatus) === "blocked") {
    return "发布准备仍被阻塞，先补齐缺失门禁。";
  }

  return "当前技能生命周期仍有阻塞项，先在协商区确认修订方案。";
}

function resolveModuleStatus({
  id,
  activeModuleId,
  input,
  blocking,
}: {
  id: SkillStudioModuleId;
  activeModuleId: SkillStudioModuleId;
  input: BuildSkillStudioSessionModelInput;
  blocking: boolean;
}) {
  if (id === activeModuleId) {
    return "当前焦点";
  }

  switch (id) {
    case "intent":
      return input.hasDraftArtifact ? "已明确" : "待明确";
    case "draft":
      return input.hasDraftArtifact ? "已生成" : "待生成";
    case "evaluation":
      return blocking ? "待修正" : input.hasDraftArtifact ? "已检查" : "待验证";
    case "release-prep":
      return input.hasDraftArtifact ? "待发布" : "待准备";
    case "lifecycle":
      return LIFECYCLE_READY_STATUSES.has(normalizeStatus(input.publishStatus))
        ? "已建立"
        : "待建立";
    case "graph":
      return input.graphRelationshipCount > 0 ? "已建立" : "待建立";
  }
}

function resolveModuleSummary({
  id,
  input,
  blocking,
}: {
  id: SkillStudioModuleId;
  input: BuildSkillStudioSessionModelInput;
  blocking: boolean;
}) {
  switch (id) {
    case "intent":
      return "先明确技能目标、触发条件、适用边界和成功标准。";
    case "draft":
      return input.hasDraftArtifact
        ? "技能草案、规则和输入输出约束已经生成。"
        : "等待主智能体产出第一版技能草案。";
    case "evaluation":
      return blocking
        ? `当前有 ${input.blockingCount} 项阻塞，需先修正验证或测试问题。`
        : "验证、试跑与结构检查结果会在这里集中展示。";
    case "release-prep":
      return "在发布前确认门禁状态、版本说明、包产物与挂载目标。";
    case "lifecycle":
      return "这里汇总启用状态、活动版本、已发布版本和回退目标。";
    case "graph":
      return input.graphRelationshipCount > 0
        ? `已建立 ${input.graphRelationshipCount} 条技能关系，可查看上下游与高影响连接。`
        : "关系网络会在技能纳入图谱后出现。";
  }
}

export function buildSkillStudioSessionModel(
  input: BuildSkillStudioSessionModelInput,
): SkillStudioSessionModel {
  const assistantMode = input.persistedAssistantMode ?? DEFAULT_SKILL_STUDIO_AGENT;
  const blocking = hasBlockingNegotiation(input);
  const activeModuleId = resolveActiveModuleId(input, blocking);

  return {
    activeModuleId,
    modules: SKILL_STUDIO_MODULE_ORDER.map((id) => ({
      id,
      title:
        {
          intent: WORKBENCH_COPY.skillStudio.modules.intent,
          draft: WORKBENCH_COPY.skillStudio.modules.draft,
          evaluation: WORKBENCH_COPY.skillStudio.modules.evaluation,
          "release-prep": WORKBENCH_COPY.skillStudio.modules.releasePrep,
          lifecycle: WORKBENCH_COPY.skillStudio.modules.lifecycle,
          graph: WORKBENCH_COPY.skillStudio.modules.graph,
        }[id] ?? id,
      status: resolveModuleStatus({
        id,
        activeModuleId,
        input,
        blocking,
      }),
      summary: resolveModuleSummary({
        id,
        input,
        blocking,
      }),
      expanded: id === activeModuleId,
    })),
    assistant: {
      mode: assistantMode,
      label: labelOfSkillStudioAgentName(assistantMode),
      locked: !input.isNewThread || Boolean(input.persistedAssistantMode),
    },
    summary: {
      hasDraftArtifact: input.hasDraftArtifact,
      validationStatus: normalizeStatus(input.validationStatus),
      testStatus: normalizeStatus(input.testStatus),
      publishStatus: normalizeStatus(input.publishStatus),
      graphRelationshipCount: input.graphRelationshipCount,
    },
    negotiation: {
      pendingApprovalCount: input.blockingCount,
      interruptionVisible: blocking,
      question: buildNegotiationQuestion(input, blocking),
    },
  };
}
