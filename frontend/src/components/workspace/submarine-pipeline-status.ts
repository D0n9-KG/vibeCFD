import { localizeWorkspaceDisplayText } from "../../core/i18n/workspace-display.ts";
import { getThreadErrorMessage } from "../../core/threads/error.ts";

export type SubmarinePipelineTone = "ready" | "streaming" | "error";
export type SubmarinePipelineRuntimeStatus =
  | "ready"
  | "running"
  | "blocked"
  | "failed"
  | "completed";

export type SubmarinePipelineStatus = {
  tone: SubmarinePipelineTone;
  agentLabel: string;
  runLabel: string;
  outputStatus: string;
  summaryText: string;
  errorBanner: {
    title: string;
    message: string;
    guidance: string;
  } | null;
};

export type SubmarinePipelineStatusInput = {
  threadError: unknown;
  threadIsLoading: boolean;
  isNewThread: boolean;
  hasMessages: boolean;
  hasDesignBrief: boolean;
  hasFinalReport: boolean;
  designBriefSummary?: string | null;
  runtimeTaskSummary?: string | null;
  runtimeStatus?: string | null;
  runtimeSummary?: string | null;
  recoveryGuidance?: string | null;
  blockerDetail?: string | null;
  reviewStatus?: string | null;
  nextRecommendedStage?: string | null;
  requiresImmediateConfirmation?: boolean | null;
  pendingCalculationPlanCount?: number | null;
  scientificGateStatus?: string | null;
  allowedClaimLevel?: string | null;
  decisionStatus?: string | null;
  scientificVerificationStatus?: string | null;
  environmentParityStatus?: string | null;
  reproducibilityStatus?: string | null;
  environmentProfileLabel?: string | null;
};

const DEFAULT_SUMMARY =
  "在右侧聊天中说明研究目标、工况、对比对象和交付件，工作台会把它整理成可确认的 CFD brief，并继续推进几何预检、求解、结果整理与复核。";

const DEFAULT_ERROR_GUIDANCE =
  "当前研究状态未能推进，可以在当前潜艇工作台中补充条件或调整配置后直接重试。";

const HYDRATION_SUMMARY =
  "正在从已创建的潜艇仿真线程恢复消息、附件与研究产物，请稍候。";

const DEFAULT_BLOCKED_GUIDANCE =
  "先处理阻塞说明，再从当前线程继续恢复，不需要重新新建线程。";

const DEFAULT_FAILED_GUIDANCE =
  "优先检查求解日志与结果产物，修正命令、网格或边界条件后再重试。";

const SCIENTIFIC_GATE_STATUS_LABELS: Record<string, string> = {
  ready_for_claim: "可支持更强科研声明",
  claim_limited: "科研声明受限",
  blocked: "科学门禁阻塞",
};

const SCIENTIFIC_CLAIM_LEVEL_LABELS: Record<string, string> = {
  delivery_only: "仅交付原始结果",
  verified_but_not_validated: "已验证但未外部校核",
  validated_with_gaps: "已校核但仍有缺口",
  research_ready: "可用于科研结论",
};

const DELIVERY_DECISION_STATUS_LABELS: Record<string, string> = {
  ready_for_user_decision: "等待聊天确认",
  needs_more_evidence: "需要更多证据",
  blocked_by_setup: "受环境阻塞",
};

const SCIENTIFIC_VERIFICATION_STATUS_LABELS: Record<string, string> = {
  research_ready: "SCI-01 已通过",
  needs_more_verification: "SCI-01 仍需补证",
  blocked: "SCI-01 已阻塞",
};

const RUNTIME_PARITY_STATUS_LABELS: Record<string, string> = {
  matched: "环境一致",
  drifted_but_runnable: "环境漂移但仍可运行",
  unknown: "环境画像未知",
  blocked: "运行环境一致性受阻",
};

function normalizeRuntimeStatus(
  value?: string | null,
): SubmarinePipelineRuntimeStatus | null {
  switch (value) {
    case "ready":
    case "running":
    case "blocked":
    case "failed":
    case "completed":
      return value;
    default:
      return null;
  }
}

function getBootstrapGuidance(message: string): string {
  if (message.includes("LangGraph")) {
    return "当前研究状态未能推进。请在潜艇工作台中直接重试；如果仍失败，请检查 LangGraph URL 配置后再提交。";
  }

  if (message.includes("流线程")) {
    return "当前研究状态未能推进。请在潜艇工作台中直接重试；如果仍失败，请刷新当前线程页面后再次提交。";
  }

  return DEFAULT_ERROR_GUIDANCE;
}

function buildRuntimeErrorStatus({
  runtimeStatus,
  runtimeSummary,
  recoveryGuidance,
  blockerDetail,
}: {
  runtimeStatus: "blocked" | "failed";
  runtimeSummary?: string | null;
  recoveryGuidance?: string | null;
  blockerDetail?: string | null;
}): SubmarinePipelineStatus {
  const isBlocked = runtimeStatus === "blocked";
  const title = isBlocked ? "CFD runtime 已阻塞" : "CFD runtime 已失败";
  const message =
    blockerDetail ??
    runtimeSummary ??
    (isBlocked
      ? "当前线程缺少继续恢复所需的关键运行证据。"
      : "当前求解链路出现失败标记。");
  const guidance =
    recoveryGuidance ??
    (isBlocked ? DEFAULT_BLOCKED_GUIDANCE : DEFAULT_FAILED_GUIDANCE);

  return {
    tone: "error",
    agentLabel: isBlocked ? "CFD runtime 受阻" : "CFD runtime 失败",
    runLabel: isBlocked ? "受阻" : "失败",
    outputStatus: isBlocked ? "等待恢复" : "执行失败",
    summaryText: runtimeSummary ?? guidance,
    errorBanner: {
      title,
      message,
      guidance,
    },
  };
}

function buildCompletedScientificStatus({
  hasFinalReport,
  runtimeSummary,
  runtimeTaskSummary,
  scientificGateStatus,
  allowedClaimLevel,
  decisionStatus,
  scientificVerificationStatus,
  environmentParityStatus,
  reproducibilityStatus,
  environmentProfileLabel,
}: {
  hasFinalReport: boolean;
  runtimeSummary?: string | null;
  runtimeTaskSummary?: string | null;
  scientificGateStatus?: string | null;
  allowedClaimLevel?: string | null;
  decisionStatus?: string | null;
  scientificVerificationStatus?: string | null;
  environmentParityStatus?: string | null;
  reproducibilityStatus?: string | null;
  environmentProfileLabel?: string | null;
}): SubmarinePipelineStatus | null {
  const gateLabel =
    SCIENTIFIC_GATE_STATUS_LABELS[scientificGateStatus ?? ""] ??
    scientificGateStatus ??
    null;
  const claimLabel =
    SCIENTIFIC_CLAIM_LEVEL_LABELS[allowedClaimLevel ?? ""] ??
    allowedClaimLevel ??
    null;
  const decisionLabel =
    DELIVERY_DECISION_STATUS_LABELS[decisionStatus ?? ""] ??
    decisionStatus ??
    null;
  const verificationLabel =
    SCIENTIFIC_VERIFICATION_STATUS_LABELS[scientificVerificationStatus ?? ""] ??
    scientificVerificationStatus ??
    null;
  const parityState = reproducibilityStatus ?? environmentParityStatus ?? null;
  const parityLabel =
    RUNTIME_PARITY_STATUS_LABELS[parityState ?? ""] ?? parityState ?? null;
  const profileLabel = environmentProfileLabel ?? "当前运行环境";

  if (parityState === "blocked") {
    return {
      tone: "error",
      agentLabel: "CFD runtime 已完成",
      runLabel: "运行环境一致性受阻",
      outputStatus: "结果已完成，但可复现运行环境被阻塞",
      summaryText:
        runtimeSummary ??
        `${profileLabel} 当前处于${parityLabel ?? "运行环境一致性受阻"}状态。在恢复必要的运行前提之前，不应将本次结果视为可复现实验。`,
      errorBanner: {
        title: "运行环境一致性受阻",
        message: parityLabel ?? "运行环境一致性受阻",
        guidance:
          "请先恢复所需的运行画像、挂载配置和 Docker Socket 访问，再把这次运行作为可复现实验依据。",
      },
    };
  }

  if (parityState === "drifted_but_runnable" || parityState === "unknown") {
    return {
      tone: "ready",
      agentLabel: "CFD runtime 已完成",
        runLabel: parityLabel ?? "复现性受限",
      outputStatus:
        parityState === "drifted_but_runnable"
          ? "结果已完成，但运行环境与复现配置发生漂移"
          : "结果已完成，但当前运行环境配置无法确认",
      summaryText:
        runtimeSummary ??
        `${profileLabel} 当前处于${parityLabel ?? "复现性受限"}状态。科学证据已保留，但在恢复运行环境一致性前，复现性仍受限制。`,
      errorBanner: null,
    };
  }

  if (decisionStatus === "blocked_by_setup") {
    return {
      tone: "error",
      agentLabel: "CFD runtime 已完成",
        runLabel: decisionLabel ?? "受环境阻塞",
      outputStatus: "请在聊天中确认下一步。",
      summaryText:
        runtimeSummary ??
        `请在聊天中确认下一步。当前科研闸门：${gateLabel ?? "已阻塞"}；允许结论级别：${claimLabel ?? "仅可交付"}。`,
      errorBanner: {
          title: "需要聊天确认",
          message: gateLabel ?? "科研闸门已阻塞",
          guidance:
            "请在主聊天里决定是修复环境、校正输入，还是先补回缺失的证据链，再刷新报告。",
      },
    };
  }

  if (decisionStatus === "needs_more_evidence") {
    return {
      tone: "ready",
      agentLabel: "CFD runtime 已完成",
        runLabel: decisionLabel ?? "需要更多证据",
      outputStatus: "请在聊天中确认下一步。",
      summaryText:
        runtimeSummary ??
        `请在聊天中确认下一步。当前科研闸门：${gateLabel ?? "结论受限"}；允许结论级别：${claimLabel ?? "待判定"}。`,
      errorBanner: null,
    };
  }

  if (decisionStatus === "ready_for_user_decision") {
    return {
      tone: "ready",
      agentLabel: "CFD runtime 已完成",
        runLabel: decisionLabel ?? "等待聊天确认",
      outputStatus: "请在聊天中确认下一步。",
      summaryText:
        runtimeSummary ??
        `请在聊天中确认下一步。当前科研闸门：${gateLabel ?? "可声明"}；允许结论级别：${claimLabel ?? "可用于科研结论"}。`,
      errorBanner: null,
    };
  }

  if (scientificGateStatus === "blocked") {
    const summary =
      runtimeSummary ??
      `求解已完成，但科学门禁当前判定为阻塞。允许声明级别：${claimLabel ?? "待补证"}`;
    return {
      tone: "error",
      agentLabel: "CFD runtime 已完成",
      runLabel: "科学受阻",
      outputStatus: "结果已完成，但科研声明已阻塞",
      summaryText: summary,
      errorBanner: {
        title: "科研门禁已阻塞",
        message: gateLabel ?? "科学门禁阻塞",
        guidance: claimLabel
          ? `当前仅允许 ${claimLabel}，补齐验证证据后再刷新报告。`
          : DEFAULT_BLOCKED_GUIDANCE,
      },
    };
  }

  if (scientificGateStatus === "claim_limited") {
    return {
      tone: "ready",
      agentLabel: "CFD runtime 已完成",
      runLabel: "声明受限",
      outputStatus: "结果已完成，但科研声明仍受限",
      summaryText:
        runtimeSummary ??
        `当前科学门禁状态：${gateLabel ?? "声明受限"}。允许声明级别：${claimLabel ?? "待确认"}`,
      errorBanner: null,
    };
  }

  if (scientificGateStatus === "ready_for_claim") {
    return {
      tone: "ready",
        agentLabel: "CFD runtime 已完成",
        runLabel: "科研就绪",
      outputStatus: hasFinalReport
        ? "结果报告已生成，可支持更强科研声明"
        : "求解已完成，具备更强科研声明条件",
      summaryText:
        runtimeSummary ??
        `当前科学门禁状态：${gateLabel ?? "可支持更强科研声明"}。允许声明级别：${claimLabel ?? "可用于科研结论"}`,
      errorBanner: null,
    };
  }

  if (scientificVerificationStatus === "blocked") {
    return {
      tone: "error",
      agentLabel: "CFD runtime 已完成",
      runLabel: "SCI-01 受阻",
      outputStatus: "求解已完成，但科学验证已阻塞",
      summaryText:
        runtimeSummary ??
        `${verificationLabel ?? "SCI-01 已阻塞"}，需要回到验证链路补齐证据后再推进报告。`,
      errorBanner: {
        title: "科研校验已阻塞",
        message: verificationLabel ?? "SCI-01 已阻塞",
        guidance: "优先检查稳定性证据、残差阈值和力系数尾段稳定性结论。",
      },
    };
  }

  if (scientificVerificationStatus === "needs_more_verification") {
    return {
      tone: "ready",
      agentLabel: "CFD runtime 已完成",
      runLabel: "待补科学证据",
      outputStatus: "求解已完成，仍需补齐科学验证",
      summaryText:
        runtimeSummary ??
        `${verificationLabel ?? "SCI-01 仍需补证"}，建议先查看稳定性证据与验证要求。`,
      errorBanner: null,
    };
  }

  if (scientificVerificationStatus === "research_ready") {
    return {
      tone: "ready",
      agentLabel: "CFD runtime 已完成",
      runLabel: "SCI-01 已通过",
      outputStatus: hasFinalReport
        ? "结果报告已生成，SCI-01 已通过"
        : "求解已完成，SCI-01 已通过",
      summaryText:
        runtimeSummary ??
        verificationLabel ??
        runtimeTaskSummary ??
        DEFAULT_SUMMARY,
      errorBanner: null,
    };
  }

  return null;
}

function buildPrecomputeApprovalStatus({
  designBriefSummary,
  runtimeTaskSummary,
  runtimeSummary,
  reviewStatus,
  nextRecommendedStage,
  requiresImmediateConfirmation,
  pendingCalculationPlanCount,
}: {
  designBriefSummary?: string | null;
  runtimeTaskSummary?: string | null;
  runtimeSummary?: string | null;
  reviewStatus?: string | null;
  nextRecommendedStage?: string | null;
  requiresImmediateConfirmation?: boolean | null;
  pendingCalculationPlanCount?: number | null;
}): SubmarinePipelineStatus | null {
  const pendingCount = Math.max(0, pendingCalculationPlanCount ?? 0);
  const needsImmediateClarification =
    Boolean(requiresImmediateConfirmation) ||
    nextRecommendedStage === "user-confirmation";
  const needsResearcherConfirmation =
    needsImmediateClarification ||
    reviewStatus === "needs_user_confirmation" ||
    pendingCount > 0;

  if (!needsResearcherConfirmation) {
    return null;
  }

  const baseSummary = needsImmediateClarification
    ? "在开始任何真实计算前，还需要研究人员立即补充确认。"
    : pendingCount > 0
      ? `仍有 ${pendingCount} 条计算计划项等待研究人员确认，然后才能进入求解派发。`
      : "计算计划已经整理完成，等待研究人员确认后进入求解派发。";
  const detail = localizeWorkspaceDisplayText(
    runtimeSummary ?? runtimeTaskSummary ?? designBriefSummary ?? null,
  );

  return {
    tone: "ready",
    agentLabel: "研究计划已就绪",
    runLabel: needsImmediateClarification
      ? "需要补充确认"
      : "等待确认",
    outputStatus: needsImmediateClarification
      ? "需要立即补充确认"
      : "等待研究人员确认",
    summaryText: detail ? `${baseSummary} ${detail}` : baseSummary,
    errorBanner: null,
  };
}

export function getSubmarinePipelineStatus({
  threadError,
  threadIsLoading,
  isNewThread,
  hasMessages,
  hasDesignBrief,
  hasFinalReport,
  designBriefSummary,
  runtimeTaskSummary,
  runtimeStatus,
  runtimeSummary,
  recoveryGuidance,
  blockerDetail,
  reviewStatus,
  nextRecommendedStage,
  requiresImmediateConfirmation,
  pendingCalculationPlanCount,
  scientificGateStatus,
  allowedClaimLevel,
  decisionStatus,
  scientificVerificationStatus,
  environmentParityStatus,
  reproducibilityStatus,
  environmentProfileLabel,
}: SubmarinePipelineStatusInput): SubmarinePipelineStatus {
  if (threadError) {
    const message = getThreadErrorMessage(
      threadError,
      "主智能体调用失败，请稍后重试。",
    );
    const guidance = getBootstrapGuidance(message);

    return {
      tone: "error",
      agentLabel: "主智能体失败",
      runLabel: "失败",
      outputStatus: "主智能体失败",
      summaryText: `${guidance} 错误原因：${message}`,
      errorBanner: {
        title: "主智能体调用失败",
        message,
        guidance,
      },
    };
  }

  const isHydratingExistingThread =
    !isNewThread &&
    threadIsLoading &&
    !hasMessages &&
    !hasDesignBrief &&
    !hasFinalReport;

  if (isHydratingExistingThread) {
    return {
      tone: "streaming",
      agentLabel: "主智能体恢复中",
      runLabel: "恢复中",
      outputStatus: "正在恢复已创建的研究线程",
      summaryText: HYDRATION_SUMMARY,
      errorBanner: null,
    };
  }

  const normalizedRuntimeStatus = normalizeRuntimeStatus(runtimeStatus);
  if (
    normalizedRuntimeStatus === "blocked" ||
    normalizedRuntimeStatus === "failed"
  ) {
    return buildRuntimeErrorStatus({
      runtimeStatus: normalizedRuntimeStatus,
      runtimeSummary,
      recoveryGuidance,
      blockerDetail,
    });
  }

  if (normalizedRuntimeStatus === "running") {
    return {
      tone: "streaming",
      agentLabel: "CFD runtime 运行中",
      runLabel: "运行中",
      outputStatus: hasFinalReport ? "结果报告更新中" : "运行证据持续写入中",
      summaryText: runtimeSummary ?? runtimeTaskSummary ?? DEFAULT_SUMMARY,
      errorBanner: null,
    };
  }

  if (normalizedRuntimeStatus === "completed") {
    const scientificCompletionStatus = buildCompletedScientificStatus({
      hasFinalReport,
      runtimeSummary,
      runtimeTaskSummary,
      scientificGateStatus,
      allowedClaimLevel,
      decisionStatus,
      scientificVerificationStatus,
      environmentParityStatus,
      reproducibilityStatus,
      environmentProfileLabel,
    });
    if (scientificCompletionStatus) {
      return scientificCompletionStatus;
    }

    return {
      tone: "ready",
      agentLabel: "CFD runtime 已完成",
      runLabel: "已完成",
      outputStatus: hasFinalReport ? "结果报告已生成" : "求解已完成，待整理结果",
      summaryText: runtimeSummary ?? runtimeTaskSummary ?? DEFAULT_SUMMARY,
      errorBanner: null,
    };
  }

  const precomputeApprovalStatus = buildPrecomputeApprovalStatus({
    designBriefSummary,
    runtimeTaskSummary,
    runtimeSummary,
    reviewStatus,
    nextRecommendedStage,
    requiresImmediateConfirmation,
    pendingCalculationPlanCount,
  });
  if (precomputeApprovalStatus) {
    return precomputeApprovalStatus;
  }

  return {
    tone: threadIsLoading ? "streaming" : "ready",
    agentLabel: threadIsLoading ? "主智能体运行中" : "主智能体待命",
    runLabel: threadIsLoading ? "运行中" : "待命",
    outputStatus: hasFinalReport
      ? "结果报告已生成"
      : hasDesignBrief
        ? "已形成设计简报"
        : "等待用户输入任务",
    summaryText:
      runtimeSummary ??
      designBriefSummary ??
      runtimeTaskSummary ??
      DEFAULT_SUMMARY,
    errorBanner: null,
  };
}
