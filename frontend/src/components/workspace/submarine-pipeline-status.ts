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
  hasDesignBrief: boolean;
  hasFinalReport: boolean;
  designBriefSummary?: string | null;
  runtimeTaskSummary?: string | null;
};

const DEFAULT_SUMMARY =
  "在右侧聊天中说明研究目标、工况、对比对象和交付物，工作台会把它整理成可确认的 CFD brief，并继续推进几何预检、求解、结果整理与复核。";

const ERROR_GUIDANCE =
  "当前研究状态未推进，可在右侧聊天调整模型、补充约束后直接重试。";

export function getSubmarinePipelineStatus({
  threadError,
  threadIsLoading,
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

    return {
      tone: "error",
      agentLabel: "主智能体失败",
      runLabel: "失败",
      outputStatus: "主智能体失败",
      summaryText: `${ERROR_GUIDANCE} 错误原因：${message}`,
      errorBanner: {
        title: "主智能体调用失败",
        message,
        guidance: ERROR_GUIDANCE,
      },
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
