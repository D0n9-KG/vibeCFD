import assert from "node:assert/strict";
import test from "node:test";

import type {
  SubmarineDesignBriefPayload,
  SubmarineSimulationRequirements,
} from "./submarine-runtime-panel.contract";

const {
  buildConfirmExecutionMessage,
  buildClarificationRequestMessage,
} = await import(
  new URL("./submarine-confirmation-actions.ts", import.meta.url).href
);

function makeRequirements(
  overrides: Partial<SubmarineSimulationRequirements> = {},
): SubmarineSimulationRequirements {
  return {
    inlet_velocity_mps: 5,
    fluid_density_kg_m3: 1025,
    kinematic_viscosity_m2ps: 1.05e-6,
    end_time_seconds: 300,
    delta_t_seconds: 0.5,
    write_interval_steps: 25,
    ...overrides,
  };
}

function makeBrief(
  overrides: Partial<SubmarineDesignBriefPayload> = {},
): SubmarineDesignBriefPayload {
  return {
    task_description: "Evaluate the uploaded submarine hull at 5 m/s and produce a reviewable CFD package.",
    confirmation_status: "draft",
    selected_case_id: "darpa_suboff_bare_hull_resistance",
    simulation_requirements: makeRequirements(),
    requested_outputs: [
      {
        output_id: "drag_coefficient",
        label: "Drag coefficient Cd",
        requested_label: "Drag coefficient Cd",
        support_level: "supported",
      },
      {
        output_id: "surface_pressure_contour",
        label: "Surface pressure contour",
        requested_label: "Surface pressure contour",
        support_level: "supported",
      },
    ],
    scientific_verification_requirements: [
      {
        requirement_id: "mesh_independence_study",
        label: "Mesh independence study",
        check_type: "study_required",
      },
    ],
    user_constraints: ["Keep the first run to a single baseline condition."],
    open_questions: ["Should we add a 7 m/s comparison case?"],
    ...overrides,
  };
}

void test("buildConfirmExecutionMessage emits an explicit brief-locking contract", () => {
  const message = buildConfirmExecutionMessage(
    makeBrief({
      open_questions: [],
    }),
  );

  assert.match(message, /submarine_design_brief_tool/);
  assert.match(message, /confirmation_status="confirmed"/);
  assert.match(message, /execution_preference="preflight_then_execute"/);
  assert.match(message, /submarine_solver_dispatch_tool/);
  assert.match(message, /selected_case_id":"darpa_suboff_bare_hull_resistance"/);
  assert.match(message, /"requested_outputs":\["drag_coefficient","surface_pressure_contour"\]/);
  assert.match(message, /"scientific_verification_requirements":\["mesh_independence_study"\]/);
  assert.match(message, /do not silently change the plan/i);
});

void test("buildClarificationRequestMessage keeps the brief in draft and lists open questions", () => {
  const message = buildClarificationRequestMessage(makeBrief());

  assert.match(message, /submarine_design_brief_tool/);
  assert.match(message, /confirmation_status="draft"/);
  assert.doesNotMatch(message, /execution_preference="preflight_then_execute"/);
  assert.match(message, /Do not call `submarine_solver_dispatch_tool`/);
  assert.match(message, /Should we add a 7 m\/s comparison case\?/);
  assert.match(message, /do not fabricate missing operating conditions/i);
});
