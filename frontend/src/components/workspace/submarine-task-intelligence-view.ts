import type {
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

function buildPlanItems(
  requirements: SubmarineSimulationRequirements | null | undefined,
): TaskIntelligencePlanItem[] {
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
      value: `${requirements.write_interval_steps} steps`,
    });
  }
  return items;
}

function buildRequestedOutputs(
  requestedOutputs: SubmarineRequestedOutputPayload[] | null | undefined,
): TaskIntelligenceRequestedOutputView[] {
  return (requestedOutputs ?? []).map((item) => ({
    outputId: item.output_id ?? "unknown-output",
    label: item.label ?? item.requested_label ?? item.output_id ?? "未命名输出",
    requestedLabel:
      item.requested_label ?? item.label ?? item.output_id ?? "未命名输出",
    supportLevel: item.support_level ?? "unknown",
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

function buildVerificationRequirements(
  requirements:
    | SubmarineScientificVerificationRequirementPayload[]
    | null
    | undefined,
): TaskIntelligenceVerificationRequirementView[] {
  return (requirements ?? []).map((item) => ({
    requirementId: item.requirement_id ?? "unknown-requirement",
    label: item.label ?? item.requirement_id ?? "未命名验证要求",
    checkType: item.check_type ?? "unspecified",
  }));
}

function buildExecutionSteps(
  executionOutline: SubmarineExecutionOutlineItem[] | null | undefined,
): TaskIntelligenceExecutionStepView[] {
  return (executionOutline ?? []).map((item) => ({
    roleId: item.role_id ?? "unknown-role",
    owner: item.owner ?? "Unknown owner",
    goal: item.goal ?? "No goal provided",
    status: item.status ?? "pending",
  }));
}

function normalizeStringList(values: string[] | null | undefined): string[] {
  return (values ?? []).filter(
    (value): value is string => typeof value === "string" && value.trim().length > 0,
  );
}

export function buildTaskIntelligenceViewModel({
  designBrief,
  snapshot,
}: {
  designBrief: SubmarineDesignBriefPayload | null;
  snapshot: TaskIntelligenceSnapshot | null;
}): TaskIntelligenceViewModel {
  const simulationRequirements =
    designBrief?.simulation_requirements ?? snapshot?.simulation_requirements ?? null;
  const openQuestions = normalizeStringList(designBrief?.open_questions);
  const hasBrief = Boolean(designBrief);
  const isConfirmed = designBrief?.confirmation_status === "confirmed";

  let confirmationState: TaskIntelligenceConfirmationState = "idle";
  if (isConfirmed) {
    confirmationState = "confirmed";
  } else if (openQuestions.length > 0) {
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
      hasBrief && !isConfirmed && openQuestions.length === 0,
    planItems: buildPlanItems(simulationRequirements),
    requestedOutputs: buildRequestedOutputs(designBrief?.requested_outputs),
    verificationRequirements: buildVerificationRequirements(
      designBrief?.scientific_verification_requirements,
    ),
    userConstraints: normalizeStringList(designBrief?.user_constraints),
    openQuestions,
    executionSteps: buildExecutionSteps(designBrief?.execution_outline),
  };
}
