import assert from "node:assert/strict";
import test from "node:test";

import { buildSubmarineVisibleActions } from "./submarine-visible-actions.ts";

void test("offers a visible execution action once the brief is confirmed", () => {
  const actions = buildSubmarineVisibleActions({
    runtime: null,
    designBrief: {
      confirmation_status: "confirmed",
      task_description: "Prepare the SUBOFF 5 m/s resistance baseline.",
      selected_case_id: "darpa_suboff_bare_hull_resistance",
    },
    finalReport: null,
  });

  assert.equal(actions.length, 1);
  assert.equal(actions[0]?.id, "execute");
  assert.ok((actions[0]?.message ?? "").length > 0);
});

void test("offers a visible execution action when dispatch planning is ready but execution has not started", () => {
  const actions = buildSubmarineVisibleActions({
    runtime: {
      current_stage: "solver-dispatch",
      stage_status: "planned",
      runtime_status: "ready",
      review_status: "ready_for_supervisor",
      execution_preference: "plan_only",
      next_recommended_stage: "solver-dispatch",
      run_script_virtual_path:
        "/workspace/submarine/solver-dispatch/suboff_solid/openfoam-case/Allrun",
      workspace_case_dir_virtual_path:
        "/workspace/submarine/solver-dispatch/suboff_solid/openfoam-case",
    },
    designBrief: null,
    finalReport: null,
  });

  assert.equal(actions.length, 1);
  assert.equal(actions[0]?.id, "execute");
  assert.ok((actions[0]?.message ?? "").length > 0);
});

void test("offers a visible report action after execution artifacts exist", () => {
  const actions = buildSubmarineVisibleActions({
    runtime: {
      current_stage: "solver-dispatch",
      runtime_status: "completed",
      solver_results_virtual_path: "/artifacts/submarine/solver-results.json",
    },
    designBrief: {
      confirmation_status: "confirmed",
      task_description: "Prepare the SUBOFF 5 m/s resistance baseline.",
    },
    finalReport: null,
  });

  assert.equal(actions.length, 1);
  assert.equal(actions[0]?.id, "report");
  assert.ok((actions[0]?.message ?? "").length > 0);
});

void test("offers a visible remediation follow-up action when a blocked report exposes an auto-followup handoff", () => {
  const actions = buildSubmarineVisibleActions({
    runtime: {
      current_stage: "result-reporting",
      runtime_status: "blocked",
      blocker_detail: "Solver metrics are unavailable for this run.",
      supervisor_handoff_virtual_path:
        "/artifacts/submarine/scientific-remediation-handoff.json",
    },
    designBrief: {
      confirmation_status: "confirmed",
      task_description: "Prepare the SUBOFF 5 m/s resistance baseline.",
      selected_case_id: "darpa_suboff_bare_hull_resistance",
    },
    finalReport: {
      summary_zh: "当前报告已生成，但证据仍被科学审查阻塞。",
      scientific_supervisor_gate: {
        gate_status: "blocked",
        blocking_reasons: ["Solver metrics are unavailable for this run."],
      },
      scientific_remediation_handoff: {
        handoff_status: "ready_for_auto_followup",
        recommended_action_id: "execute-scientific-studies",
        tool_name: "submarine_solver_dispatch",
        reason: "Solver metrics are unavailable for this run.",
      },
    },
  });

  assert.equal(actions.length, 1);
  assert.equal(actions[0]?.id, "followup");
  assert.match(actions[0]?.description ?? "", /Solver metrics|阻塞|补齐/i);
  assert.match(actions[0]?.message ?? "", /修正|重跑|solver metrics/i);
});

void test("suppresses visible execution actions while confirmation is still pending", () => {
  const actions = buildSubmarineVisibleActions({
    runtime: {
      review_status: "needs_user_confirmation",
      next_recommended_stage: "user-confirmation",
    },
    designBrief: {
      confirmation_status: "draft",
      open_questions: ["Need the final reference area."],
    },
    finalReport: null,
  });

  assert.equal(actions.length, 0);
});

void test("suppresses visible actions once the final report is already available", () => {
  const actions = buildSubmarineVisibleActions({
    runtime: {
      current_stage: "supervisor-review",
      runtime_status: "completed",
      solver_results_virtual_path: "/artifacts/submarine/solver-results.json",
    },
    designBrief: {
      confirmation_status: "confirmed",
    },
    finalReport: {
      summary_zh: "Final report ready.",
    },
  });

  assert.equal(actions.length, 0);
});
