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
    return {
      tone: "ready",
      agentLabel: "CFD runtime 已完成",
      runLabel: "已完成",
      outputStatus: hasFinalReport ? "结果报告已生成" : "求解已完成，待整理结果",
      summaryText: runtimeSummary ?? runtimeTaskSummary ?? DEFAULT_SUMMARY,
      errorBanner: null,
    };
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
