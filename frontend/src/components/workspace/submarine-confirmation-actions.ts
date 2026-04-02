import type {
  SubmarineCalculationPlanItem,
  SubmarineDesignBriefPayload,
  SubmarineSimulationRequirements,
} from "./submarine-runtime-panel.contract";

type BriefSnapshot = {
  selected_case_id: string | null;
  simulation_requirements: Partial<SubmarineSimulationRequirements>;
  requested_outputs: string[];
  scientific_verification_requirements: string[];
  user_constraints: string[];
  calculation_plan: Array<{
    item_id: string | null;
    label: string | null;
    approval_state: string | null;
    origin: string | null;
    requires_immediate_confirmation: boolean;
  }>;
};

function normalizeStringList(
  values: Array<string | null | undefined> | null | undefined,
) {
  return (values ?? []).filter(
    (value): value is string =>
      typeof value === "string" && value.trim().length > 0,
  );
}

function buildSimulationRequirementsSnapshot(
  requirements: SubmarineSimulationRequirements | null | undefined,
): Partial<SubmarineSimulationRequirements> {
  if (!requirements) {
    return {};
  }

  const snapshot: Partial<SubmarineSimulationRequirements> = {};

  if (requirements.inlet_velocity_mps != null) {
    snapshot.inlet_velocity_mps = requirements.inlet_velocity_mps;
  }
  if (requirements.fluid_density_kg_m3 != null) {
    snapshot.fluid_density_kg_m3 = requirements.fluid_density_kg_m3;
  }
  if (requirements.kinematic_viscosity_m2ps != null) {
    snapshot.kinematic_viscosity_m2ps = requirements.kinematic_viscosity_m2ps;
  }
  if (requirements.end_time_seconds != null) {
    snapshot.end_time_seconds = requirements.end_time_seconds;
  }
  if (requirements.delta_t_seconds != null) {
    snapshot.delta_t_seconds = requirements.delta_t_seconds;
  }
  if (requirements.write_interval_steps != null) {
    snapshot.write_interval_steps = requirements.write_interval_steps;
  }

  return snapshot;
}

function buildCalculationPlanSnapshot(
  calculationPlan: SubmarineCalculationPlanItem[] | null | undefined,
) {
  return (calculationPlan ?? []).map((item) => ({
    item_id: item.item_id ?? null,
    label: item.label ?? null,
    approval_state: item.approval_state ?? null,
    origin: item.origin ?? null,
    requires_immediate_confirmation: Boolean(
      item.requires_immediate_confirmation,
    ),
  }));
}

function buildBriefSnapshot(
  designBrief: SubmarineDesignBriefPayload | null,
): BriefSnapshot {
  return {
    selected_case_id: designBrief?.selected_case_id ?? null,
    simulation_requirements: buildSimulationRequirementsSnapshot(
      designBrief?.simulation_requirements,
    ),
    requested_outputs: normalizeStringList(
      (designBrief?.requested_outputs ?? []).map((item) => item.output_id),
    ),
    scientific_verification_requirements: normalizeStringList(
      (designBrief?.scientific_verification_requirements ?? []).map(
        (item) => item.requirement_id,
      ),
    ),
    user_constraints: normalizeStringList(designBrief?.user_constraints),
    calculation_plan: buildCalculationPlanSnapshot(designBrief?.calculation_plan),
  };
}

function stringifyBriefSnapshot(designBrief: SubmarineDesignBriefPayload | null): string {
  return JSON.stringify(buildBriefSnapshot(designBrief));
}

function stringifyCalculationPlanSnapshot(
  designBrief: SubmarineDesignBriefPayload | null,
): string {
  return JSON.stringify(buildCalculationPlanSnapshot(designBrief?.calculation_plan));
}

function listPendingCalculationPlanLabels(
  designBrief: SubmarineDesignBriefPayload | null,
) {
  return (designBrief?.calculation_plan ?? [])
    .filter((item) => item.approval_state !== "researcher_confirmed")
    .map((item) => item.label)
    .filter(
      (label): label is string =>
        typeof label === "string" && label.trim().length > 0,
    );
}

export function buildConfirmExecutionMessage(
  designBrief: SubmarineDesignBriefPayload | null,
): string {
  const snapshot = stringifyBriefSnapshot(designBrief);
  const calculationPlanSnapshot = stringifyCalculationPlanSnapshot(designBrief);

  return [
    "Please continue from the current CFD calculation-plan draft instead of re-planning from scratch.",
    "",
    "Control contract:",
    "- Reuse the current design brief.",
    "- Call `submarine_design_brief_tool` to update the current brief.",
    '- Set `confirmation_status=\"confirmed\"`.',
    '- Set `execution_preference=\"preflight_then_execute\"`.',
    "- Preserve the confirmed brief snapshot and calculation-plan snapshot below unless a hard conflict is found.",
    `- brief_snapshot=${snapshot}`,
    `- calculation_plan_snapshot=${calculationPlanSnapshot}`,
    "- Keep pre-compute approval separate from post-compute scientific claim levels.",
    "- Continue with `geometry-preflight` first, and only then proceed with `submarine_solver_dispatch_tool`.",
    "- If geometry preflight produces new pending or immediate-confirmation items, stop for researcher review before solver dispatch.",
    "- If preflight reveals a hard conflict or a missing prerequisite, stop and explain it to me first; do not silently change the plan.",
  ].join("\n");
}

export function buildClarificationRequestMessage(
  designBrief: SubmarineDesignBriefPayload | null,
): string {
  const snapshot = stringifyBriefSnapshot(designBrief);
  const calculationPlanSnapshot = stringifyCalculationPlanSnapshot(designBrief);
  const openQuestions = normalizeStringList(designBrief?.open_questions);
  const pendingCalculationPlanLabels = listPendingCalculationPlanLabels(designBrief);
  const lines = [
    "Please keep refining the current CFD calculation plan with me and do not start execution yet.",
    "",
    "Control contract:",
    "- Reuse the current design brief.",
    "- If you update the brief, call `submarine_design_brief_tool` and keep `confirmation_status=\"draft\"`.",
    "- Do not call `submarine_solver_dispatch_tool` and do not start solver execution.",
    "- Preserve the current brief snapshot and calculation-plan snapshot below unless I explicitly ask to change them.",
    `- brief_snapshot=${snapshot}`,
    `- calculation_plan_snapshot=${calculationPlanSnapshot}`,
    "- Keep pre-compute approval language separate from post-compute scientific claim labels.",
    "- Ask follow-up questions instead of guessing; do not fabricate missing operating conditions, requested outputs, or verification requirements.",
  ];

  if (openQuestions.length > 0) {
    lines.push("- Resolve these open questions with me before confirmation:");
    openQuestions.forEach((question, index) => {
      lines.push(`${index + 1}. ${question}`);
    });
  } else {
    lines.push(
      "- Keep the brief in draft until all missing execution details are explicitly confirmed.",
    );
  }

  if (pendingCalculationPlanLabels.length > 0) {
    lines.push(
      "- Review these pending calculation-plan items with me before confirmation:",
    );
    pendingCalculationPlanLabels.forEach((label, index) => {
      lines.push(`${index + 1}. ${label}`);
    });
  }

  return lines.join("\n");
}
