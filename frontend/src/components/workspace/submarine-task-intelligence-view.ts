import { localizeWorkspaceDisplayText } from "../../core/i18n/workspace-display.ts";

import type {
  SubmarineCalculationPlanItem,
  SubmarineDesignBriefPayload,
  SubmarineExecutionOutlineItem,
  SubmarineRequestedOutputPayload,
  SubmarineScientificVerificationRequirementPayload,
  SubmarineSimulationRequirements,
} from "./submarine-runtime-panel.contract";

type TaskIntelligenceSnapshot = {
  review_status?: string | null;
  stage_status?: string | null;
  simulation_requirements?: SubmarineSimulationRequirements | null;
  calculation_plan?: SubmarineCalculationPlanItem[] | null;
  requires_immediate_confirmation?: boolean | null;
};

export type TaskIntelligencePlanItem = {
  label: string;
  value: string;
};

export type TaskIntelligenceRequestedOutputView = {
  outputId: string;
  label: string;
  requestedLabel: string;
  supportLevel: string;
  selectorSummary: string | null;
};

export type TaskIntelligenceVerificationRequirementView = {
  requirementId: string;
  label: string;
  checkType: string;
};

export type TaskIntelligenceExecutionStepView = {
  roleId: string;
  owner: string;
  goal: string;
  status: string;
};

export type TaskIntelligenceConfirmationState =
  | "idle"
  | "needs_clarification"
  | "ready_to_confirm"
  | "confirmed";

export type TaskIntelligenceViewModel = {
  confirmationState: TaskIntelligenceConfirmationState;
  canConfirmExecution: boolean;
  planItems: TaskIntelligencePlanItem[];
  requestedOutputs: TaskIntelligenceRequestedOutputView[];
  verificationRequirements: TaskIntelligenceVerificationRequirementView[];
  userConstraints: string[];
  openQuestions: string[];
  executionSteps: TaskIntelligenceExecutionStepView[];
  pendingApprovalCount: number;
  immediateClarificationCount: number;
};

const OUTPUT_SUPPORT_LEVEL_LABELS: Record<string, string> = {
  supported: "已支持",
  not_yet_supported: "暂不支持",
  needs_clarification: "待澄清",
  planned: "已规划",
  unknown: "待确认",
};

const VERIFICATION_REQUIREMENT_LABELS: Record<string, string> = {
  "Final residual threshold": "最终残差阈值",
  "Force coefficient tail stability": "力系数尾段稳定性",
  "Mesh independence study": "网格无关性研究",
  "Domain sensitivity study": "计算域敏感性研究",
  "Time-step sensitivity study": "时间步长敏感性研究",
  max_final_residual: "最终残差阈值",
  force_coefficient_tail_stability: "力系数尾段稳定性",
  artifact_presence: "产物齐备",
  study_required: "需完成研究验证",
  tail_stability: "尾段稳定性",
};

const VERIFICATION_CHECK_TYPE_LABELS: Record<string, string> = {
  max_final_residual: "最大最终残差",
  force_coefficient_tail_stability: "力系数尾段稳定性",
  artifact_presence: "产物齐备",
  study_required: "研究验证",
  tail_stability: "尾段稳定性",
  unspecified: "未指定",
};

const EXECUTION_OWNER_LABELS: Record<string, string> = {
  "claude-code-supervisor": "Claude Code 主管代理",
  "task-intelligence": "DeerFlow 任务理解",
  "geometry-preflight": "DeerFlow 几何预检",
  "solver-dispatch": "DeerFlow 求解派发",
  "scientific-study": "DeerFlow 科研研究",
  "experiment-compare": "DeerFlow 实验对比",
  "scientific-verification": "DeerFlow 科研核验",
  "result-reporting": "DeerFlow 结果整理",
  "scientific-followup": "DeerFlow 科研跟进",
  "supervisor-review": "Claude Code 主管复核",
};

const EXECUTION_GOAL_LABELS: Record<string, string> = {
  "claude-code-supervisor":
    "澄清 CFD 目标、约束和交付物，并让当前计划始终与用户确认保持一致。",
  "task-intelligence":
    "匹配候选案例，理解任务意图，并选择最合适的潜艇 CFD 工作流模板。",
  "geometry-preflight":
    "检查已上传 STL 几何，识别尺度或格式风险，并沉淀可追溯的预检结论。",
  "solver-dispatch":
    "把已确认设置映射为 OpenFOAM 算例，受控执行并沉淀 CFD 输出。",
  "scientific-study":
    "规划并跟踪可复现的科研变体研究，让基线证据扩展为研究级敏感性检查。",
  "experiment-compare":
    "对比基线与研究变体运行，整理结构化实验清单和差异摘要。",
  "scientific-verification":
    "评估研究证据、验证要求与科研准备度，再决定是否允许更强结论。",
  "result-reporting":
    "把指标、日志和报告整理成可复核的交付产物，供主管签署。",
  "scientific-followup":
    "在科研复核后执行或跟踪补救动作，让下一轮迭代继续保持可追溯。",
  "supervisor-review":
    "复核科研证据门槛，确认允许的结论级别，并决定是否需要后续补救。",
};

const EXECUTION_STATUS_LABELS: Record<string, string> = {
  pending: "待执行",
  ready: "就绪",
  in_progress: "进行中",
  running: "运行中",
  completed: "已完成",
  done: "已完成",
  blocked: "已阻塞",
  failed: "失败",
};

function formatNumber(value: number, digits = 2): string {
  return Number(value.toFixed(digits)).toString();
}

function summarizeSelector(
  selector: Record<string, unknown> | null | undefined,
): string | null {
  if (!selector) {
    return null;
  }

  const selectorType =
    typeof selector.type === "string" ? selector.type : "unknown";

  if (selectorType === "patch") {
    const patches = Array.isArray(selector.patches)
      ? selector.patches.filter((patch): patch is string => typeof patch === "string")
      : [];
    return patches.length > 0 ? `patch:${patches.join(",")}` : "patch";
  }

  if (selectorType === "plane") {
    const originMode =
      typeof selector.origin_mode === "string" ? selector.origin_mode : "plane";
    const originValue =
      typeof selector.origin_value === "number"
        ? selector.origin_value
        : null;
    if (originValue == null) {
      return originMode;
    }
    return `${originMode}:${formatNumber(originValue, 3)}`;
  }

  return selectorType;
}

function formatPlanStatus(item: SubmarineCalculationPlanItem): string {
  if (item.requires_immediate_confirmation) {
    return "需立即澄清";
  }
  if (item.approval_state === "researcher_confirmed") {
    return "研究人员已确认";
  }
  return "待研究人员确认";
}

function buildPlanItems(
  calculationPlan: SubmarineCalculationPlanItem[] | null | undefined,
  requirements: SubmarineSimulationRequirements | null | undefined,
): TaskIntelligencePlanItem[] {
  const structuredItems = (calculationPlan ?? []).map((item) => {
    const value = formatCalculationPlanValue(item);
    const status = formatPlanStatus(item);
    const source = localizeWorkspaceDisplayText(
      item.source_label ?? item.origin ?? "来源待补充",
    );

    return {
      label: localizeWorkspaceDisplayText(
        item.label ?? item.category ?? "计算计划项",
      ),
      value: [value, status, source].filter(Boolean).join(" | "),
    };
  });

  if (structuredItems.length > 0) {
    return structuredItems;
  }

  if (!requirements) {
    return [];
  }

  const items: TaskIntelligencePlanItem[] = [];
  if (requirements.inlet_velocity_mps != null) {
    items.push({
      label: "入口速度",
      value: `${formatNumber(requirements.inlet_velocity_mps)} m/s`,
    });
  }
  if (requirements.fluid_density_kg_m3 != null) {
    items.push({
      label: "流体密度",
      value: `${formatNumber(requirements.fluid_density_kg_m3)} kg/m3`,
    });
  }
  if (requirements.kinematic_viscosity_m2ps != null) {
    items.push({
      label: "运动黏度",
      value: `${requirements.kinematic_viscosity_m2ps.toExponential(2)} m2/s`,
    });
  }
  if (requirements.end_time_seconds != null) {
    items.push({
      label: "模拟时长",
      value: `${formatNumber(requirements.end_time_seconds)} s`,
    });
  }
  if (requirements.delta_t_seconds != null) {
    items.push({
      label: "时间步长",
      value: `${formatNumber(requirements.delta_t_seconds, 3)} s`,
    });
  }
  if (requirements.write_interval_steps != null) {
    items.push({
      label: "写出间隔",
      value: `${requirements.write_interval_steps} 步`,
    });
  }
  return items;
}

function formatOutputSupportLevel(value?: string | null): string {
  return (
    OUTPUT_SUPPORT_LEVEL_LABELS[value ?? ""] ??
    localizeWorkspaceDisplayText(value ?? "待确认")
  );
}

function buildRequestedOutputs(
  requestedOutputs: SubmarineRequestedOutputPayload[] | null | undefined,
): TaskIntelligenceRequestedOutputView[] {
  return (requestedOutputs ?? []).map((item) => ({
    outputId: item.output_id ?? "unknown-output",
    label: localizeWorkspaceDisplayText(
      item.label ?? item.requested_label ?? item.output_id ?? "未命名输出",
    ),
    requestedLabel: localizeWorkspaceDisplayText(
      item.requested_label ?? item.label ?? item.output_id ?? "未命名输出",
    ),
    supportLevel: formatOutputSupportLevel(item.support_level),
    selectorSummary: summarizeSelector(
      item.postprocess_spec &&
        typeof item.postprocess_spec === "object" &&
        !Array.isArray(item.postprocess_spec)
        ? ((item.postprocess_spec.selector as Record<string, unknown> | undefined) ??
            null)
        : null,
    ),
  }));
}

function formatVerificationRequirementLabel(
  label?: string | null,
  checkType?: string | null,
): string {
  return (
    VERIFICATION_REQUIREMENT_LABELS[label ?? ""] ??
    VERIFICATION_REQUIREMENT_LABELS[checkType ?? ""] ??
    localizeWorkspaceDisplayText(label ?? checkType ?? "未命名验证要求")
  );
}

function formatVerificationCheckType(value?: string | null): string {
  return (
    VERIFICATION_CHECK_TYPE_LABELS[value ?? ""] ??
    localizeWorkspaceDisplayText(value ?? "未指定")
  );
}

function buildVerificationRequirements(
  requirements:
    | SubmarineScientificVerificationRequirementPayload[]
    | null
    | undefined,
): TaskIntelligenceVerificationRequirementView[] {
  return (requirements ?? []).map((item) => ({
    requirementId: item.requirement_id ?? "unknown-requirement",
    label: formatVerificationRequirementLabel(item.label, item.check_type),
    checkType: formatVerificationCheckType(item.check_type),
  }));
}

function formatExecutionOwner(
  roleId?: string | null,
  owner?: string | null,
): string {
  return (
    EXECUTION_OWNER_LABELS[roleId ?? ""] ??
    localizeWorkspaceDisplayText(owner ?? "待指派")
  );
}

function formatExecutionGoal(
  roleId?: string | null,
  goal?: string | null,
): string {
  return (
    EXECUTION_GOAL_LABELS[roleId ?? ""] ??
    localizeWorkspaceDisplayText(goal ?? "待补充")
  );
}

function formatExecutionStatus(value?: string | null): string {
  return (
    EXECUTION_STATUS_LABELS[value ?? ""] ??
    localizeWorkspaceDisplayText(value ?? "待执行")
  );
}

function buildExecutionSteps(
  executionOutline: SubmarineExecutionOutlineItem[] | null | undefined,
): TaskIntelligenceExecutionStepView[] {
  return (executionOutline ?? []).map((item) => ({
    roleId: item.role_id ?? "unknown-role",
    owner: formatExecutionOwner(item.role_id, item.owner),
    goal: formatExecutionGoal(item.role_id, item.goal),
    status: formatExecutionStatus(item.status),
  }));
}

function normalizeStringList(values: string[] | null | undefined): string[] {
  return (values ?? [])
    .filter(
      (value): value is string =>
        typeof value === "string" && value.trim().length > 0,
    )
    .map((value) => localizeWorkspaceDisplayText(value));
}

function formatCalculationPlanValue(item: SubmarineCalculationPlanItem): string {
  if (item.proposed_value != null) {
    return formatPlanScalarValue(item.proposed_value, item.unit);
  }

  if (Array.isArray(item.proposed_range)) {
    const rangeValues = item.proposed_range
      .map((value) => formatPlanScalarValue(value, null))
      .filter((value) => value !== "--");
    if (rangeValues.length > 0) {
      return `${rangeValues.join(" to ")}${item.unit ? ` ${item.unit}` : ""}`;
    }
  }

  if (item.proposed_range && typeof item.proposed_range === "object") {
    const minValue = formatPlanScalarValue(
      (item.proposed_range as Record<string, unknown>).min,
      null,
    );
    const maxValue = formatPlanScalarValue(
      (item.proposed_range as Record<string, unknown>).max,
      null,
    );
    if (minValue !== "--" || maxValue !== "--") {
      return `${minValue} to ${maxValue}${item.unit ? ` ${item.unit}` : ""}`;
    }
  }

  return "--";
}

function formatPlanScalarValue(value: unknown, unit: string | null | undefined): string {
  let base = "--";

  if (typeof value === "number" && Number.isFinite(value)) {
    base = formatNumber(value, Math.abs(value) >= 1 ? 3 : 6);
  } else if (typeof value === "string" && value.trim().length > 0) {
    base = value;
  } else if (typeof value === "boolean") {
    base = value ? "true" : "false";
  }

  if (base === "--") {
    return base;
  }
  return unit ? `${base} ${unit}` : base;
}

export function buildTaskIntelligenceViewModel({
  designBrief,
  snapshot,
}: {
  designBrief: SubmarineDesignBriefPayload | null;
  snapshot: TaskIntelligenceSnapshot | null;
}): TaskIntelligenceViewModel {
  const calculationPlan =
    designBrief?.calculation_plan ?? snapshot?.calculation_plan ?? null;
  const simulationRequirements =
    designBrief?.simulation_requirements ?? snapshot?.simulation_requirements ?? null;
  const openQuestions = normalizeStringList(designBrief?.open_questions);
  const pendingCalculationPlanItems = (calculationPlan ?? []).filter(
    (item) => item.approval_state !== "researcher_confirmed",
  );
  const immediateClarificationItems = pendingCalculationPlanItems.filter(
    (item) => item.requires_immediate_confirmation,
  );
  const calculationPlanQuestions = immediateClarificationItems
    .map((item) => {
      const label = localizeWorkspaceDisplayText(
        item.label ?? item.category ?? "计算计划项",
      );
      const detail = item.evidence_gap_note ?? item.researcher_note ?? null;
      return detail
        ? `${label}: ${localizeWorkspaceDisplayText(detail)}`
        : label;
    })
    .filter(
      (value): value is string => typeof value === "string" && value.trim().length > 0,
    );
  const combinedOpenQuestions = [
    ...openQuestions,
    ...calculationPlanQuestions.filter((value) => !openQuestions.includes(value)),
  ];
  const hasBrief = Boolean(designBrief);
  const isConfirmed =
    designBrief?.confirmation_status === "confirmed" &&
    pendingCalculationPlanItems.length === 0;

  let confirmationState: TaskIntelligenceConfirmationState = "idle";
  if (
    immediateClarificationItems.length > 0 ||
    snapshot?.requires_immediate_confirmation
  ) {
    confirmationState = "needs_clarification";
  } else if (pendingCalculationPlanItems.length > 0) {
    confirmationState = "ready_to_confirm";
  } else if (isConfirmed) {
    confirmationState = "confirmed";
  } else if (combinedOpenQuestions.length > 0) {
    confirmationState = "needs_clarification";
  } else if (
    hasBrief ||
    snapshot?.review_status === "needs_user_confirmation" ||
    snapshot?.stage_status === "waiting_user"
  ) {
    confirmationState = "ready_to_confirm";
  }

  return {
    confirmationState,
    canConfirmExecution:
      hasBrief &&
      !isConfirmed &&
      combinedOpenQuestions.length === 0 &&
      immediateClarificationItems.length === 0,
    planItems: buildPlanItems(calculationPlan, simulationRequirements),
    requestedOutputs: buildRequestedOutputs(designBrief?.requested_outputs),
    verificationRequirements: buildVerificationRequirements(
      designBrief?.scientific_verification_requirements,
    ),
    userConstraints: normalizeStringList(designBrief?.user_constraints),
    openQuestions: combinedOpenQuestions,
    executionSteps: buildExecutionSteps(designBrief?.execution_outline),
    pendingApprovalCount: pendingCalculationPlanItems.length,
    immediateClarificationCount: immediateClarificationItems.length,
  };
}
