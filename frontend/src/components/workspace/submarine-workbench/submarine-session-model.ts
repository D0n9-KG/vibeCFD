import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "../submarine-runtime-panel.contract.ts";

import { buildSubmarineResearchSnapshotSummary } from "./submarine-research-canvas.model.ts";

export const SUBMARINE_RESEARCH_SLICE_ORDER = [
  "task-establishment",
  "geometry-preflight",
  "simulation-plan",
  "simulation-execution",
  "results-and-delivery",
] as const;

export type SubmarineResearchSliceId =
  (typeof SUBMARINE_RESEARCH_SLICE_ORDER)[number];

export type SubmarineResearchSlice = {
  id: SubmarineResearchSliceId;
  title: string;
  statusLabel: string;
  summary: string;
  keyEvidenceSummary: string;
  agentInterpretation: string;
  nextRecommendedAction: string;
};

export type SubmarineSessionModel = {
  activeSliceId: SubmarineResearchSliceId;
  slices: readonly SubmarineResearchSlice[];
  currentSlice: SubmarineResearchSlice;
  viewedSlice: SubmarineResearchSlice;
  historyInspection: {
    isViewingHistory: boolean;
    bannerTitle: string | null;
    returnLabel: string | null;
  };
  summary: {
    currentObjective: string;
    evidenceReady: boolean;
    messageCount: number;
    artifactCount: number;
  };
  liveProgress: {
    visible: boolean;
    statusLabel: string;
    statusSummary: string;
    latestAssistantPreview: string | null;
    latestUserPreview: string | null;
  };
  negotiation: {
    pendingApprovalCount: number;
    interruptionVisible: boolean;
    question: string | null;
  };
  trustSurface: {
    provenanceAvailable: boolean;
    reproducibilityAvailable: boolean;
    environmentParityAvailable: boolean;
  };
};

export type BuildSubmarineSessionModelInput = {
  isNewThread: boolean;
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
  messageCount: number;
  artifactCount: number;
  isLoading: boolean;
  errorMessage: string | null;
  latestAssistantPreview: string | null;
  latestUserPreview: string | null;
  latestUploadedFiles?: readonly {
    filename: string;
    path?: string | null;
  }[];
  viewedSliceId?: SubmarineResearchSliceId | null;
};

function countPendingApprovals({
  runtime,
  designBrief,
}: Pick<BuildSubmarineSessionModelInput, "runtime" | "designBrief">): number {
  const openQuestions =
    designBrief?.open_questions?.filter((question) => Boolean(question)).length ?? 0;
  const planItems = runtime?.calculation_plan ?? designBrief?.calculation_plan ?? [];
  const unconfirmedPlanItems = planItems.filter(
    (item) => item?.approval_state !== "researcher_confirmed",
  ).length;
  const explicitConfirmationGate =
    runtime?.review_status === "needs_user_confirmation" ||
    runtime?.next_recommended_stage === "user-confirmation" ||
    hasImmediateConfirmationRequirement(runtime, designBrief) ||
    (designBrief?.confirmation_status === "draft" &&
      (designBrief.open_questions?.length ?? 0) > 0);
  const pendingApprovalCount = openQuestions + unconfirmedPlanItems;

  if (pendingApprovalCount > 0) {
    return pendingApprovalCount;
  }

  return explicitConfirmationGate ? 1 : 0;
}

function hasImmediateConfirmationRequirement(
  runtime: SubmarineRuntimeSnapshotPayload | null,
  designBrief: SubmarineDesignBriefPayload | null,
): boolean {
  if (
    runtime?.requires_immediate_confirmation === true ||
    designBrief?.requires_immediate_confirmation === true
  ) {
    return true;
  }

  const planItems = runtime?.calculation_plan ?? designBrief?.calculation_plan ?? [];
  return planItems.some(
    (item) =>
      item?.requires_immediate_confirmation === true &&
      item?.approval_state !== "researcher_confirmed",
  );
}

function resolveBlockingReasons({
  runtime,
  designBrief,
  pendingApprovalCount,
}: Pick<BuildSubmarineSessionModelInput, "runtime" | "designBrief"> & {
  pendingApprovalCount: number;
}): string[] {
  const reasons: string[] = [];

  if (runtime?.review_status === "needs_user_confirmation") {
    reasons.push("当前存在待你确认的研究决策，主智能体会先停在协商区。");
  }
  if (runtime?.next_recommended_stage === "user-confirmation") {
    reasons.push("当前建议先完成研究者确认，再继续推进计算。");
  }
  if (hasImmediateConfirmationRequirement(runtime, designBrief)) {
    reasons.push("存在需要立刻确认的参数或边界条件。");
  }
  if (pendingApprovalCount > 0) {
    reasons.push(`还有 ${pendingApprovalCount} 项待确认事项。`);
  }
  if (
    designBrief?.confirmation_status === "draft" &&
    (designBrief.open_questions?.length ?? 0) > 0
  ) {
    reasons.push("研究简报仍有未敲定的问题。");
  }

  return reasons;
}

function collectSkillNames(runtime: SubmarineRuntimeSnapshotPayload | null): string[] {
  const timelineSkills =
    runtime?.activity_timeline?.flatMap((item) => item.skill_names ?? []) ?? [];
  const executionPlanSkills =
    runtime?.execution_plan?.flatMap((item) => item.target_skills ?? []) ?? [];

  return [...timelineSkills, ...executionPlanSkills].filter(
    (skill, index, all): skill is string => Boolean(skill) && all.indexOf(skill) === index,
  );
}

function hasExecutionSignal(runtime: SubmarineRuntimeSnapshotPayload | null): boolean {
  return [
    runtime?.runtime_status === "running",
    runtime?.runtime_status === "completed",
    runtime?.current_stage === "solver-dispatch",
    runtime?.current_stage === "result-reporting",
    runtime?.current_stage === "supervisor-review",
    runtime?.execution_log_virtual_path,
    runtime?.solver_results_virtual_path,
    runtime?.workspace_case_dir_virtual_path,
    runtime?.run_script_virtual_path,
  ].some(Boolean);
}

function hasPostprocessResultSignal(
  runtime: SubmarineRuntimeSnapshotPayload | null,
  finalReport: SubmarineFinalReportPayload | null,
): boolean {
  const reportPath = runtime?.report_virtual_path;
  const reportLooksLikeDesignBrief =
    typeof reportPath === "string" &&
    (reportPath.includes("/design-brief/") || reportPath.includes("cfd-design-brief."));
  const reportLooksLikeGeometryCheck =
    typeof reportPath === "string" &&
    (reportPath.includes("/geometry-check/") || reportPath.includes("geometry-check."));

  return [
    runtime?.current_stage === "result-reporting",
    runtime?.current_stage === "supervisor-review",
    reportLooksLikeDesignBrief || reportLooksLikeGeometryCheck ? null : reportPath,
    finalReport?.figure_delivery_summary,
    finalReport?.experiment_summary,
    finalReport?.scientific_study_summary,
    finalReport?.delivery_highlights,
  ].some(Boolean);
}

function basenameOfPath(path?: string | null): string | null {
  if (!path) {
    return null;
  }

  const normalized = path.replace(/\\/g, "/");
  const segments = normalized.split("/");
  return segments.at(-1) ?? normalized;
}

function hasGeometrySignal(
  input: Pick<
    BuildSubmarineSessionModelInput,
    "runtime" | "designBrief" | "latestUploadedFiles"
  >,
): boolean {
  const uploadedGeometry = input.latestUploadedFiles?.some((file) =>
    file.filename.toLowerCase().endsWith(".stl"),
  );

  return Boolean(
    input.runtime?.geometry_virtual_path ??
      input.designBrief?.geometry_virtual_path ??
      uploadedGeometry,
  );
}

function hasPlanningSignal({
  runtime,
  designBrief,
}: {
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
}): boolean {
  if (
    runtime?.review_status === "needs_user_confirmation" ||
    runtime?.next_recommended_stage === "user-confirmation" ||
    hasImmediateConfirmationRequirement(runtime, designBrief)
  ) {
    return false;
  }

  const confirmedExecutionOutline =
    designBrief?.confirmation_status === "confirmed" &&
    (designBrief.execution_outline?.length ?? 0) > 0;

  return Boolean(
    confirmedExecutionOutline ||
      (runtime?.calculation_plan?.length ?? 0) > 0 ||
      (designBrief?.calculation_plan?.length ?? 0) > 0 ||
      runtime?.next_recommended_stage === "solver-dispatch",
  );
}

function buildResearchSlices({
  input,
  currentObjective,
  pendingApprovalCount,
  blockingReasons,
  skillNames,
}: {
  input: BuildSubmarineSessionModelInput;
  currentObjective: string;
  pendingApprovalCount: number;
  blockingReasons: readonly string[];
  skillNames: readonly string[];
}): readonly [SubmarineResearchSlice, ...SubmarineResearchSlice[]] {
  const uploadedGeometryFile = input.latestUploadedFiles?.find((file) =>
    file.filename.toLowerCase().endsWith(".stl"),
  );
  const geometryPath =
    input.runtime?.geometry_virtual_path ??
    input.designBrief?.geometry_virtual_path ??
    uploadedGeometryFile?.path ??
    uploadedGeometryFile?.filename;
  const geometryFilename = basenameOfPath(geometryPath);
  const semanticTaskSummary =
    buildSubmarineResearchSnapshotSummary(
      input.runtime?.task_summary ?? input.designBrief?.summary_zh ?? currentObjective,
      72,
    ) ?? currentObjective;
  const executionPlanCount =
    input.runtime?.execution_plan?.length ??
    input.designBrief?.execution_outline?.length ??
    0;
  const confirmationGateActive = pendingApprovalCount > 0 || blockingReasons.length > 0;
  const taskEstablishmentInterpretation = buildSubmarineResearchSnapshotSummary(
    input.runtime?.task_summary ?? input.designBrief?.summary_zh,
    72,
  );

  const slices: SubmarineResearchSlice[] = [
    {
      id: "task-establishment",
      title: "任务建立",
      statusLabel: input.isNewThread ? "进行中" : "已建立",
      summary: currentObjective,
      keyEvidenceSummary:
        geometryFilename != null
          ? `已收到研究对象 ${geometryFilename}。`
          : "当前还没有稳定的几何对象或求解证据。",
      agentInterpretation:
        taskEstablishmentInterpretation != null
          ? `主智能体已把当前研究意图收敛为：${taskEstablishmentInterpretation}`
          : "当前仍处于研究意图收敛阶段，需要先明确几何、工况与交付口径。",
      nextRecommendedAction:
        geometryFilename != null
          ? "进入几何预检并形成下一步 CFD 准备建议。"
          : "补充几何、工况和交付要求。",
    },
  ];

  if (hasGeometrySignal(input) && !input.isNewThread) {
    slices.push({
      id: "geometry-preflight",
      title: "几何预检",
      statusLabel: confirmationGateActive ? "待确认" : "已识别",
      summary: semanticTaskSummary ?? "当前切片围绕具体几何对象的可计算性与前置判断展开。",
      keyEvidenceSummary:
        geometryFilename != null
          ? `${geometryFilename} 已绑定为当前研究对象。`
          : "当前切片已进入几何对象与工况前置判断阶段。",
      agentInterpretation:
        blockingReasons[0] ??
        "主智能体正在把几何对象、基础工况和预期输出组织成可执行的前置研究切片。",
      nextRecommendedAction:
        confirmationGateActive
          ? "先完成研究者确认，再继续几何预检与工况草案。"
          : "生成工况草案并准备求解设置。",
    });
  }

  if (
    hasPlanningSignal({
      runtime: input.runtime,
      designBrief: input.designBrief,
    }) &&
    !hasExecutionSignal(input.runtime) &&
    !input.finalReport
  ) {
    slices.push({
      id: "simulation-plan",
      title: "工况与计算草案",
      statusLabel: confirmationGateActive ? "待确认" : "已整理",
      summary:
        confirmationGateActive
          ? `当前仍有 ${pendingApprovalCount} 项研究决策等待确认。`
          : "当前切片围绕求解准备、目标输出和技能协作展开。",
      keyEvidenceSummary:
        executionPlanCount > 0
          ? `已形成 ${executionPlanCount} 项执行计划。`
          : skillNames.length > 0
            ? `已出现 ${skillNames.length} 个相关技能信号。`
            : "已出现可执行的 CFD 规划信号。",
      agentInterpretation:
        confirmationGateActive
          ? "主智能体正在等待你确认关键研究决策，然后再进入计算执行。"
          : "主智能体已经把研究目标收敛成可执行的计算草案。",
      nextRecommendedAction:
        confirmationGateActive ? "完成研究者确认后推进求解。" : "进入首次求解执行。",
    });
  }

  if (hasExecutionSignal(input.runtime)) {
    slices.push({
      id: "simulation-execution",
      title: "求解执行",
      statusLabel: input.runtime?.runtime_status === "running" ? "进行中" : "已完成",
      summary:
        input.runtime?.runtime_status === "running"
          ? "当前切片展示正在执行的 CFD 求解与运行轨迹。"
          : "当前切片展示已完成的求解执行与运行产物。",
      keyEvidenceSummary:
        input.runtime?.runtime_status === "running"
          ? "已进入求解器分发或执行阶段。"
          : "已形成可回看的求解执行证据。",
      agentInterpretation:
        input.runtime?.task_summary ??
        "主智能体正在根据当前研究目标推进求解执行。",
      nextRecommendedAction:
        hasPostprocessResultSignal(input.runtime, input.finalReport)
          ? "整理后处理结果与交付判断。"
          : "等待结果产物并进入后处理。",
    });
  }

  if (input.finalReport || hasPostprocessResultSignal(input.runtime, input.finalReport)) {
    slices.push({
      id: "results-and-delivery",
      title: "结果与交付判断",
      statusLabel: input.finalReport ? "可审阅" : "整理中",
      summary:
        input.finalReport?.summary_zh ??
        "当前切片围绕结果、证据边界和交付判断展开。",
      keyEvidenceSummary:
        input.finalReport?.report_overview?.recommended_next_step_zh ??
        input.runtime?.report_virtual_path ??
        "已出现结果或交付相关证据。",
      agentInterpretation:
        input.finalReport?.summary_zh ??
        "主智能体正在把结果产物整理成可审阅的交付判断。",
      nextRecommendedAction:
        input.finalReport != null ? "审阅结果并决定后续研究。" : "等待最终交付汇总。",
    });
  }

  return slices as [SubmarineResearchSlice, ...SubmarineResearchSlice[]];
}

function resolveActiveSlice({
  input,
  slices,
}: {
  input: BuildSubmarineSessionModelInput;
  slices: readonly [SubmarineResearchSlice, ...SubmarineResearchSlice[]];
}): SubmarineResearchSlice {
  const blockedGeometryPreflight =
    (input.runtime?.current_stage === "task-intelligence" ||
      input.runtime?.current_stage === "geometry-preflight") &&
    input.runtime?.review_status === "needs_user_confirmation" &&
    hasGeometrySignal(input) &&
    !hasExecutionSignal(input.runtime) &&
    !input.finalReport;

  if (blockedGeometryPreflight) {
    return (
      slices.find((slice) => slice.id === "geometry-preflight") ??
      slices.find((slice) => slice.id === "task-establishment") ??
      slices[0]
    );
  }

  return slices.at(-1) ?? slices[0];
}

export function buildSubmarineSessionModel(
  input: BuildSubmarineSessionModelInput,
): SubmarineSessionModel {
  const pendingApprovalCount = countPendingApprovals(input);
  const blockingReasons = resolveBlockingReasons({
    runtime: input.runtime,
    designBrief: input.designBrief,
    pendingApprovalCount,
  });
  const skillNames = collectSkillNames(input.runtime);
  const evidenceReady = Boolean(input.finalReport);
  const currentObjective =
    buildSubmarineResearchSnapshotSummary(
      input.runtime?.task_summary ?? input.designBrief?.summary_zh ?? input.latestUserPreview,
      72,
    ) ?? "先明确这轮潜艇仿真的研究目标、边界条件与交付要求。";
  const slices = buildResearchSlices({
    input,
    currentObjective,
    pendingApprovalCount,
    blockingReasons,
    skillNames,
  });
  const activeSlice = resolveActiveSlice({
    input,
    slices,
  });
  const viewedSlice =
    slices.find((slice) => slice.id === input.viewedSliceId) ?? activeSlice;
  const isViewingHistory = viewedSlice.id !== activeSlice.id;

  const liveProgressVisible =
    input.messageCount > 0 &&
    input.artifactCount === 0 &&
    !input.runtime &&
    !input.finalReport;
  const liveProgressStatusLabel = input.errorMessage
    ? "需要关注"
    : input.isLoading
      ? "主智能体处理中"
      : "等待结构化 CFD 产物";
  const liveProgressStatusSummary =
    input.errorMessage ??
    input.latestAssistantPreview ??
    input.latestUserPreview ??
    "当前会话已经启动，主智能体正在整理几何、工况与计算方案，请继续在右侧协商区补充信息。";

  return {
    activeSliceId: activeSlice.id,
    slices,
    currentSlice: activeSlice,
    viewedSlice,
    historyInspection: {
      isViewingHistory,
      bannerTitle: isViewingHistory ? "正在查看历史切片" : null,
      returnLabel: isViewingHistory ? "返回当前研究" : null,
    },
    summary: {
      currentObjective,
      evidenceReady,
      messageCount: input.messageCount,
      artifactCount: input.artifactCount,
    },
    liveProgress: {
      visible: liveProgressVisible,
      statusLabel: liveProgressStatusLabel,
      statusSummary: liveProgressStatusSummary,
      latestAssistantPreview: input.latestAssistantPreview,
      latestUserPreview: input.latestUserPreview,
    },
    negotiation: {
      pendingApprovalCount,
      interruptionVisible: blockingReasons.length > 0,
      question: blockingReasons[0] ?? null,
    },
    trustSurface: {
      provenanceAvailable: Boolean(
        input.finalReport?.provenance_manifest_virtual_path ??
          input.runtime?.provenance_manifest_virtual_path,
      ),
      reproducibilityAvailable: Boolean(
        input.finalReport?.reproducibility_summary?.manifest_virtual_path,
      ),
      environmentParityAvailable: Boolean(
        input.finalReport?.environment_parity_assessment?.parity_status ??
          input.runtime?.environment_parity_assessment?.parity_status,
      ),
    },
  };
}

