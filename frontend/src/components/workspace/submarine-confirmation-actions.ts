import type {
  SubmarineDesignBriefPayload,
  SubmarineSimulationRequirements,
} from "./submarine-runtime-panel.contract";

type BriefSnapshot = {
  selected_case_id: string | null;
  simulation_requirements: Partial<SubmarineSimulationRequirements>;
  requested_outputs: string[];
  scientific_verification_requirements: string[];
  user_constraints: string[];
};

function normalizeStringList(values: Array<string | null | undefined> | null | undefined) {
  return (values ?? []).filter(
    (value): value is string => typeof value === "string" && value.trim().length > 0,
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
  };
}

function stringifyBriefSnapshot(designBrief: SubmarineDesignBriefPayload | null): string {
  return JSON.stringify(buildBriefSnapshot(designBrief));
}

export function buildConfirmExecutionMessage(
  designBrief: SubmarineDesignBriefPayload | null,
): string {
  const snapshot = stringifyBriefSnapshot(designBrief);

  return [
    "请按当前已经展示给我的 CFD 方案继续，不要重新规划。",
    "",
    "Control contract:",
    "- Reuse the current design brief.",
    "- Call `submarine_design_brief_tool` to update the current brief.",
    '- Set `confirmation_status=\"confirmed\"`.',
    '- Set `execution_preference=\"preflight_then_execute\"`.',
    "- Preserve the confirmed brief snapshot below unless a hard conflict is found.",
    `- brief_snapshot=${snapshot}`,
    "- Continue with `geometry-preflight` first, and only then proceed with `submarine_solver_dispatch_tool`.",
    "- If preflight reveals a hard conflict or a missing prerequisite, stop and explain it to me first; do not silently change the plan.",
  ].join("\n");
}

export function buildClarificationRequestMessage(
  designBrief: SubmarineDesignBriefPayload | null,
): string {
  const snapshot = stringifyBriefSnapshot(designBrief);
  const openQuestions = normalizeStringList(designBrief?.open_questions);
  const lines = [
    "请继续和我协商当前 CFD 方案，不要开始求解。",
    "",
    "Control contract:",
    "- Reuse the current design brief.",
    "- If you update the brief, call `submarine_design_brief_tool` and keep `confirmation_status=\"draft\"`.",
    "- Do not call `submarine_solver_dispatch_tool` and do not start solver execution.",
    "- Preserve the current brief snapshot below unless I explicitly ask to change it.",
    `- brief_snapshot=${snapshot}`,
    "- Ask follow-up questions instead of guessing; do not fabricate missing operating conditions, requested outputs, or verification requirements.",
  ];

  if (openQuestions.length > 0) {
    lines.push("- Resolve these open questions with me before confirmation:");
    openQuestions.forEach((question, index) => {
      lines.push(`${index + 1}. ${question}`);
    });
  } else {
    lines.push("- Keep the brief in draft until all missing execution details are explicitly confirmed.");
  }

  return lines.join("\n");
}
