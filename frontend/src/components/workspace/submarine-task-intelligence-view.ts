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
  calculationPlan: SubmarineCalculationPlanItem[] | null | undefined,
  requirements: SubmarineSimulationRequirements | null | undefined,
): TaskIntelligencePlanItem[] {
  const structuredItems = (calculationPlan ?? []).map((item) => {
    const value = formatCalculationPlanValue(item);
    const status =
      item.requires_immediate_confirmation
        ? "Immediate clarification"
        : item.approval_state === "researcher_confirmed"
          ? "Researcher confirmed"
          : "Pending researcher confirmation";
    const source = item.source_label ?? item.origin ?? "source pending";

    return {
      label: item.label ?? item.category ?? "Calculation plan item",
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
      const label = item.label ?? item.category ?? "Calculation plan item";
      const detail = item.evidence_gap_note ?? item.researcher_note ?? null;
      return detail ? `${label}: ${detail}` : label;
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
