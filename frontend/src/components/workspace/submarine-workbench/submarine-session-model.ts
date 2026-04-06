import { WORKBENCH_COPY } from "../agentic-workbench/workbench-copy.ts";
import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "../submarine-runtime-panel.contract.ts";

export const SUBMARINE_RESEARCH_MODULE_ORDER = [
  "proposal",
  "decision",
  "delegation",
  "skills",
  "execution",
  "postprocess-method",
  "postprocess-result",
  "report",
] as const;

export type SubmarineResearchModuleId =
  (typeof SUBMARINE_RESEARCH_MODULE_ORDER)[number];

export type SubmarineResearchModule = {
  id: SubmarineResearchModuleId;
  title: string;
  status: string;
  summary: string;
  expanded: boolean;
};

export type SubmarineSessionModel = {
  activeModuleId: SubmarineResearchModuleId;
  modules: readonly SubmarineResearchModule[];
  summary: {
    currentObjective: string;
    evidenceReady: boolean;
    messageCount: number;
    artifactCount: number;
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

  return openQuestions + unconfirmedPlanItems;
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
    reasons.push("有待你确认的研究决策，主智能体会先停在协商区。");
  }
  if (runtime?.next_recommended_stage === "user-confirmation") {
    reasons.push("当前建议先进行用户确认，再继续推进计算。");
  }
  if (hasImmediateConfirmationRequirement(runtime, designBrief)) {
    reasons.push("存在需要立即确认的参数或边界条件。");
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
  return [
    runtime?.current_stage === "result-reporting",
    runtime?.report_virtual_path,
    finalReport?.figure_delivery_summary,
    finalReport?.experiment_summary,
    finalReport?.scientific_study_summary,
    finalReport?.delivery_highlights,
  ].some(Boolean);
}

function hasDelegationSignal(
  runtime: SubmarineRuntimeSnapshotPayload | null,
  designBrief: SubmarineDesignBriefPayload | null,
): boolean {
  return (runtime?.execution_plan?.length ?? designBrief?.execution_outline?.length ?? 0) > 0;
}

function hasMethodSignal(
  runtime: SubmarineRuntimeSnapshotPayload | null,
  designBrief: SubmarineDesignBriefPayload | null,
  finalReport: SubmarineFinalReportPayload | null,
): boolean {
  return [
    runtime?.requested_outputs?.length,
    designBrief?.requested_outputs?.length,
    designBrief?.scientific_verification_requirements?.length,
    finalReport?.scientific_verification_assessment?.requirements?.length,
    finalReport?.output_delivery_plan?.length,
  ].some(Boolean);
}

function resolveActiveModuleId(
  input: BuildSubmarineSessionModelInput,
  blockingReasons: readonly string[],
  skillNames: readonly string[],
): SubmarineResearchModuleId {
  if (input.isNewThread) {
    return "proposal";
  }

  if (blockingReasons.length > 0) {
    return "decision";
  }

  if (
    input.finalReport ||
    input.runtime?.current_stage === "supervisor-review" ||
    input.runtime?.review_status === "ready_for_supervisor" ||
    input.runtime?.review_status === "completed"
  ) {
    return "report";
  }

  if (hasPostprocessResultSignal(input.runtime, input.finalReport)) {
    return "postprocess-result";
  }

  if (hasExecutionSignal(input.runtime)) {
    return "execution";
  }

  if (skillNames.length > 0) {
    return "skills";
  }

  if (hasDelegationSignal(input.runtime, input.designBrief)) {
    return "delegation";
  }

  if (hasMethodSignal(input.runtime, input.designBrief, input.finalReport)) {
    return "postprocess-method";
  }

  return "proposal";
}

function resolveModuleStatus({
  id,
  activeModuleId,
  pendingApprovalCount,
  executionPlanCount,
  skillNames,
  runtime,
  designBrief,
  finalReport,
}: {
  id: SubmarineResearchModuleId;
  activeModuleId: SubmarineResearchModuleId;
  pendingApprovalCount: number;
  executionPlanCount: number;
  skillNames: readonly string[];
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
}): string {
  if (id === activeModuleId) {
    return "当前焦点";
  }

  switch (id) {
    case "proposal":
      return designBrief?.summary_zh || runtime?.task_summary ? "已梳理" : "待梳理";
    case "decision":
      return pendingApprovalCount > 0 ? "待确认" : designBrief ? "已敲定" : "待协商";
    case "delegation":
      return executionPlanCount > 0 ? "已分工" : "待分工";
    case "skills":
      return skillNames.length > 0 ? "已调用" : "待调用";
    case "execution":
      if (runtime?.runtime_status === "running") {
        return "计算中";
      }
      return hasExecutionSignal(runtime) ? "已执行" : "待执行";
    case "postprocess-method":
      return hasMethodSignal(runtime, designBrief, finalReport) ? "已定义" : "待定义";
    case "postprocess-result":
      return hasPostprocessResultSignal(runtime, finalReport) ? "已产出" : "待产出";
    case "report":
      return finalReport || runtime?.report_virtual_path ? "已汇总" : "待汇总";
  }
}

function resolveModuleSummary({
  id,
  pendingApprovalCount,
  executionPlanCount,
  skillNames,
  runtime,
  designBrief,
  finalReport,
}: {
  id: SubmarineResearchModuleId;
  pendingApprovalCount: number;
  executionPlanCount: number;
  skillNames: readonly string[];
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
}): string {
  switch (id) {
    case "proposal":
      return (
        designBrief?.summary_zh ??
        runtime?.task_summary ??
        "先收敛研究目标、工况、几何对象与交付口径。"
      );
    case "decision":
      return pendingApprovalCount > 0
        ? `${pendingApprovalCount} 项待确认，确认后主智能体会继续推进。`
        : "当前没有阻塞项，可继续推进研究流程。";
    case "delegation":
      return executionPlanCount > 0
        ? `已有 ${executionPlanCount} 个子代理任务被纳入执行编排。`
        : "方案敲定后，主智能体会拆分子任务与责任归属。";
    case "skills":
      return skillNames.length > 0
        ? `已调用 ${skillNames.join("、")} 等技能支撑本轮流程。`
        : "将按需调用几何检查、求解派发与报告整理等技能。";
    case "execution":
      return runtime?.runtime_status === "running"
        ? "当前正在执行算例、记录日志并同步中间产物。"
        : runtime?.runtime_status === "completed"
          ? "计算已完成，正在整理后处理与交付证据。"
          : "尚未进入实际计算。";
    case "postprocess-method":
      return hasMethodSignal(runtime, designBrief, finalReport)
        ? "已定义输出指标、验证要求与后处理方法。"
        : "后处理方法会在执行前与执行中持续补充。";
    case "postprocess-result":
      return hasPostprocessResultSignal(runtime, finalReport)
        ? "对比试验、后处理图表与关键指标会在这里汇总。"
        : "尚未形成可复核的后处理结果。";
    case "report":
      return (
        finalReport?.summary_zh ??
        "最终报告会汇总结论、证据边界、交付判断与后续建议。"
      );
  }
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
  const activeModuleId = resolveActiveModuleId(input, blockingReasons, skillNames);
  const executionPlanCount =
    input.runtime?.execution_plan?.length ?? input.designBrief?.execution_outline?.length ?? 0;
  const evidenceReady = Boolean(input.finalReport);
  const currentObjective =
    input.runtime?.task_summary ??
    input.designBrief?.summary_zh ??
    "先明确这轮潜艇仿真的研究目标、边界条件与交付要求。";

  return {
    activeModuleId,
    modules: SUBMARINE_RESEARCH_MODULE_ORDER.map((id) => ({
      id,
      title:
        {
          proposal: WORKBENCH_COPY.submarine.modules.proposal,
          decision: WORKBENCH_COPY.submarine.modules.decision,
          delegation: WORKBENCH_COPY.submarine.modules.delegation,
          skills: WORKBENCH_COPY.submarine.modules.skills,
          execution: WORKBENCH_COPY.submarine.modules.execution,
          "postprocess-method": WORKBENCH_COPY.submarine.modules.postprocessMethod,
          "postprocess-result": WORKBENCH_COPY.submarine.modules.postprocessResult,
          report: WORKBENCH_COPY.submarine.modules.report,
        }[id] ?? id,
      status: resolveModuleStatus({
        id,
        activeModuleId,
        pendingApprovalCount,
        executionPlanCount,
        skillNames,
        runtime: input.runtime,
        designBrief: input.designBrief,
        finalReport: input.finalReport,
      }),
      summary: resolveModuleSummary({
        id,
        pendingApprovalCount,
        executionPlanCount,
        skillNames,
        runtime: input.runtime,
        designBrief: input.designBrief,
        finalReport: input.finalReport,
      }),
      expanded: id === activeModuleId,
    })),
    summary: {
      currentObjective,
      evidenceReady,
      messageCount: input.messageCount,
      artifactCount: input.artifactCount,
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
