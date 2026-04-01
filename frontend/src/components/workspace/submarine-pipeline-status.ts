import { getThreadErrorMessage } from "../../core/threads/error.ts";

export type SubmarinePipelineTone = "ready" | "streaming" | "error";

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
};

const DEFAULT_SUMMARY =
  "在右侧聊天中说明研究目标、工况、对比对象和交付物，工作台会把它整理成可确认的 CFD brief，并继续推进几何预检、求解、结果整理与复核。";

const DEFAULT_ERROR_GUIDANCE =
  "当前研究状态未推进，可在当前潜艇工作台中补充条件或调整配置后直接重试。";

const HYDRATION_SUMMARY =
  "正在从已创建的潜艇仿真线程恢复消息、附件与研究产物，请稍候。";

function getBootstrapGuidance(message: string): string {
  if (message.includes("LangGraph")) {
    return "当前研究状态未推进。请在潜艇工作台中直接重试；如果仍失败，请检查 LangGraph URL 配置后再提交。";
  }

  if (message.includes("流绑定")) {
    return "当前研究状态未推进。请在潜艇工作台中直接重试；如果仍失败，请刷新当前线程页面后再次提交。";
  }

  return DEFAULT_ERROR_GUIDANCE;
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

  return {
    tone: threadIsLoading ? "streaming" : "ready",
    agentLabel: threadIsLoading ? "主智能体运行中" : "主智能体待命",
    runLabel: threadIsLoading ? "运行中" : "待命",
    outputStatus: hasFinalReport
      ? "结果报告已生成"
      : hasDesignBrief
        ? "已形成 design brief"
        : "等待用户输入任务",
    summaryText: designBriefSummary ?? runtimeTaskSummary ?? DEFAULT_SUMMARY,
    errorBanner: null,
  };
}
