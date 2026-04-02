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
  scientificVerificationStatus?: string | null;
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

const SCIENTIFIC_VERIFICATION_STATUS_LABELS: Record<string, string> = {
  research_ready: "SCI-01 已通过",
  needs_more_verification: "SCI-01 仍需补证",
  blocked: "SCI-01 已阻塞",
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
  scientificVerificationStatus,
}: {
  hasFinalReport: boolean;
  runtimeSummary?: string | null;
  runtimeTaskSummary?: string | null;
  scientificGateStatus?: string | null;
  allowedClaimLevel?: string | null;
  scientificVerificationStatus?: string | null;
}): SubmarinePipelineStatus | null {
  const gateLabel =
    SCIENTIFIC_GATE_STATUS_LABELS[scientificGateStatus ?? ""] ??
    scientificGateStatus ??
    null;
  const claimLabel =
    SCIENTIFIC_CLAIM_LEVEL_LABELS[allowedClaimLevel ?? ""] ??
    allowedClaimLevel ??
    null;
  const verificationLabel =
    SCIENTIFIC_VERIFICATION_STATUS_LABELS[scientificVerificationStatus ?? ""] ??
    scientificVerificationStatus ??
    null;

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
        title: "Scientific Gate Blocked",
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
      outputStatus: hasFinalReport ? "结果报告已生成，可支持更强科研声明" : "求解已完成，具备更强科研声明条件",
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
        title: "Scientific Verification Blocked",
        message: verificationLabel ?? "SCI-01 已阻塞",
        guidance: "优先检查 stability evidence、残差阈值和力系数尾段稳定性结论。",
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
        `${verificationLabel ?? "SCI-01 仍需补证"}，建议先查看 stability evidence 与验证要求。`,
      errorBanner: null,
    };
  }

  if (scientificVerificationStatus === "research_ready") {
    return {
      tone: "ready",
      agentLabel: "CFD runtime 已完成",
      runLabel: "SCI-01 已通过",
      outputStatus: hasFinalReport ? "结果报告已生成，SCI-01 已通过" : "求解已完成，SCI-01 已通过",
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
    ? "Immediate researcher clarification is required before any real computation can begin."
    : pendingCount > 0
      ? `${pendingCount} calculation-plan item(s) are still waiting for researcher confirmation before solver dispatch.`
      : "The calculation plan is ready for researcher confirmation before solver dispatch.";
  const detail =
    runtimeSummary ?? runtimeTaskSummary ?? designBriefSummary ?? null;

  return {
    tone: "ready",
    agentLabel: "Research plan ready",
    runLabel: needsImmediateClarification
      ? "Needs clarification"
      : "Awaiting confirmation",
    outputStatus: needsImmediateClarification
      ? "Immediate clarification required"
      : "Pending researcher confirmation",
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
  scientificVerificationStatus,
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
  if (normalizedRuntimeStatus === "blocked" || normalizedRuntimeStatus === "failed") {
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
      scientificVerificationStatus,
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
        ? "已形成 design brief"
        : "等待用户输入任务",
    summaryText:
      runtimeSummary ??
      designBriefSummary ??
      runtimeTaskSummary ??
      DEFAULT_SUMMARY,
    errorBanner: null,
  };
}
