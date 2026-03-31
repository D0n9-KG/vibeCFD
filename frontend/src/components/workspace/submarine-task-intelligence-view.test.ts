import assert from "node:assert/strict";
import test from "node:test";

import type {
  SubmarineDesignBriefPayload,
  SubmarineSimulationRequirements,
} from "./submarine-runtime-panel.contract";

const { buildTaskIntelligenceViewModel } = await import(
  new URL("./submarine-task-intelligence-view.ts", import.meta.url).href
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
    task_description: "评估上传潜艇外形在 5 m/s 下的阻力并输出可审阅报告",
    confirmation_status: "draft",
    selected_case_id: "darpa_suboff_bare_hull_resistance",
    simulation_requirements: makeRequirements(),
    requested_outputs: [
      {
        output_id: "drag_coefficient",
        label: "阻力系数 Cd",
        requested_label: "阻力系数 Cd",
        support_level: "supported",
      },
      {
        output_id: "surface_pressure_contour",
        label: "表面压力云图",
        requested_label: "表面压力云图",
        support_level: "supported",
        postprocess_spec: {
          field: "p",
          selector: {
            type: "patch",
            patches: ["hull"],
          },
        },
      },
    ],
    scientific_verification_requirements: [
      {
        requirement_id: "mesh_independence_study",
        label: "网格无关性检查",
        check_type: "study_required",
      },
      {
        requirement_id: "force_coefficient_tail_stability",
        label: "Cd 尾段稳定性",
        check_type: "tail_stability",
      },
    ],
    user_constraints: ["先做 baseline，不直接展开参数扫描"],
    execution_outline: [
      {
        role_id: "claude-code-supervisor",
        owner: "Claude Code",
        goal: "与用户确认方案",
        status: "in_progress",
      },
      {
        role_id: "solver-dispatch",
        owner: "DeerFlow solver-dispatch",
        goal: "按确认方案执行 OpenFOAM",
        status: "pending",
      },
    ],
    open_questions: [],
    ...overrides,
  };
}

void test("buildTaskIntelligenceViewModel exposes detailed confirmed-plan fields", () => {
  const viewModel = buildTaskIntelligenceViewModel({
    designBrief: makeBrief(),
    snapshot: {
      current_stage: "task-intelligence",
      review_status: "needs_user_confirmation",
    },
  });

  assert.equal(viewModel.confirmationState, "ready_to_confirm");
  assert.equal(viewModel.canConfirmExecution, true);
  assert.equal(viewModel.planItems.length, 6);
  assert.deepEqual(
    viewModel.planItems.map((item: { label: string }) => item.label),
    [
      "入口速度",
      "流体密度",
      "运动黏度",
      "模拟时长",
      "时间步长",
      "写出间隔",
    ],
  );
  assert.equal(viewModel.requestedOutputs.length, 2);
  assert.equal(
    viewModel.requestedOutputs[1].selectorSummary,
    "patch:hull",
  );
  assert.equal(viewModel.verificationRequirements.length, 2);
  assert.equal(viewModel.executionSteps.length, 2);
  assert.deepEqual(viewModel.userConstraints, [
    "先做 baseline，不直接展开参数扫描",
  ]);
});

void test("buildTaskIntelligenceViewModel blocks execution confirmation when open questions remain", () => {
  const viewModel = buildTaskIntelligenceViewModel({
    designBrief: makeBrief({
      open_questions: ["请确认是否追加 7 m/s 对比工况"],
    }),
    snapshot: {
      current_stage: "task-intelligence",
      review_status: "needs_user_confirmation",
    },
  });

  assert.equal(viewModel.confirmationState, "needs_clarification");
  assert.equal(viewModel.canConfirmExecution, false);
  assert.equal(viewModel.openQuestions.length, 1);
});
