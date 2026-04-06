import assert from "node:assert/strict";
import test from "node:test";

const { buildSubmarineSessionModel } = await import(
  new URL("./submarine-session-model.ts", import.meta.url).href
);

void test("routes to plan stage when confirmations are still blocking progress", () => {
  const model = buildSubmarineSessionModel({
    isNewThread: false,
    runtime: {
      review_status: "needs_user_confirmation",
      calculation_plan: [{ approval_state: "pending" }],
      task_summary: "Confirm baseline assumptions before dispatch.",
    },
    designBrief: {
      summary_zh: "Baseline hull request",
      open_questions: ["Need reference velocity"],
    },
    finalReport: null,
    messageCount: 8,
    artifactCount: 2,
  });

  assert.equal(model.primaryStage, "plan");
  assert.equal(model.negotiation.pendingApprovalCount, 2);
  assert.equal(model.negotiation.interruptionVisible, true);
  assert.match(model.negotiation.question ?? "", /confirm/i);
  assert.deepEqual(model.reachableStages, ["plan"]);
});

void test("routes to execute stage while runtime is actively running", () => {
  const model = buildSubmarineSessionModel({
    isNewThread: false,
    runtime: {
      runtime_status: "running",
      current_stage: "solver-dispatch",
      task_summary: "Dispatching parameterized variants.",
    },
    designBrief: {
      summary_zh: "Variant sweep on drag coefficient",
      open_questions: [],
    },
    finalReport: null,
    messageCount: 14,
    artifactCount: 6,
  });

  assert.equal(model.primaryStage, "execute");
  assert.equal(model.negotiation.interruptionVisible, false);
  assert.equal(model.summary.evidenceReady, false);
  assert.deepEqual(model.reachableStages, ["plan", "execute"]);
});

void test("routes to results stage once report evidence is available", () => {
  const model = buildSubmarineSessionModel({
    isNewThread: false,
    runtime: {
      runtime_status: "completed",
      current_stage: "supervisor-review",
      task_summary: "Preparing final handoff.",
    },
    designBrief: {
      summary_zh: "Finalize supervisor report",
      open_questions: [],
    },
    finalReport: {
      summary_zh: "CD improved 7.2% versus baseline.",
      provenance_manifest_virtual_path: "/artifacts/submarine/provenance.json",
      reproducibility_summary: {
        manifest_virtual_path: "/artifacts/submarine/repro.json",
        reproducibility_status: "reproducible",
      },
      environment_parity_assessment: {
        parity_status: "aligned",
        profile_label: "OpenFOAM-12",
      },
    },
    messageCount: 20,
    artifactCount: 12,
  });

  assert.equal(model.primaryStage, "results");
  assert.equal(model.summary.evidenceReady, true);
  assert.deepEqual(model.reachableStages, ["plan", "execute", "results"]);
  assert.equal(model.trustSurface.environmentParityAvailable, true);
  assert.equal(model.trustSurface.provenanceAvailable, true);
  assert.equal(model.trustSurface.reproducibilityAvailable, true);
});

void test("keeps confirmation blockers in plan stage for user-confirmation and immediate confirmations", () => {
  const model = buildSubmarineSessionModel({
    isNewThread: false,
    runtime: {
      next_recommended_stage: "user-confirmation",
      requires_immediate_confirmation: true,
      current_stage: "geometry-preflight",
      calculation_plan: [{ approval_state: "researcher_confirmed" }],
    },
    designBrief: {
      summary_zh: "Need hard confirmation before running geometry checks",
      open_questions: [],
      requires_immediate_confirmation: true,
    },
    finalReport: null,
    messageCount: 9,
    artifactCount: 3,
  });

  assert.equal(model.primaryStage, "plan");
  assert.equal(model.negotiation.interruptionVisible, true);
  assert.match(model.negotiation.question ?? "", /blocking/i);
  assert.deepEqual(model.reachableStages, ["plan"]);
});

void test("routes geometry-preflight and active runtime status to execute stage", () => {
  const model = buildSubmarineSessionModel({
    isNewThread: false,
    runtime: {
      current_stage: "geometry-preflight",
      stage_status: "in_progress",
      runtime_status: "ready",
      review_status: "in_progress",
      calculation_plan: [{ approval_state: "researcher_confirmed" }],
      requires_immediate_confirmation: false,
    },
    designBrief: {
      summary_zh: "Geometry preflight checks",
      open_questions: [],
      calculation_plan: [{ approval_state: "researcher_confirmed" }],
      requires_immediate_confirmation: false,
    },
    finalReport: null,
    messageCount: 11,
    artifactCount: 4,
  });

  assert.equal(model.primaryStage, "execute");
});

void test("routes supervisor-review and review-ready states to results stage", () => {
  const model = buildSubmarineSessionModel({
    isNewThread: false,
    runtime: {
      current_stage: "supervisor-review",
      stage_status: "completed",
      review_status: "ready_for_supervisor",
      calculation_plan: [{ approval_state: "researcher_confirmed" }],
      requires_immediate_confirmation: false,
    },
    designBrief: {
      summary_zh: "Ready for supervisor review",
      open_questions: [],
      calculation_plan: [{ approval_state: "researcher_confirmed" }],
    },
    finalReport: null,
    messageCount: 15,
    artifactCount: 7,
  });

  assert.equal(model.primaryStage, "results");
});

void test("keeps completed runtime in execute until review or report evidence is ready", () => {
  const model = buildSubmarineSessionModel({
    isNewThread: false,
    runtime: {
      runtime_status: "completed",
      current_stage: "result-reporting",
      stage_status: "completed",
      review_status: "in_progress",
      calculation_plan: [{ approval_state: "researcher_confirmed" }],
      requires_immediate_confirmation: false,
    },
    designBrief: {
      summary_zh: "Post-processing completed but supervisor review not started",
      open_questions: [],
      calculation_plan: [{ approval_state: "researcher_confirmed" }],
    },
    finalReport: null,
    messageCount: 12,
    artifactCount: 8,
  });

  assert.equal(model.primaryStage, "execute");
  assert.deepEqual(model.reachableStages, ["plan", "execute"]);
});

void test("keeps later evidence surfaces reachable even when plan negotiation becomes active again", () => {
  const model = buildSubmarineSessionModel({
    isNewThread: false,
    runtime: {
      task_summary: "Review completed CFD evidence with one remaining approval.",
      review_status: "needs_user_confirmation",
      report_virtual_path: "/artifacts/submarine/final-report.json",
      execution_log_virtual_path: "/artifacts/submarine/openfoam-run.log",
      solver_results_virtual_path: "/artifacts/submarine/solver-results.json",
      activity_timeline: [{ title: "Run finished", actor: "solver-worker" }],
      calculation_plan: [{ approval_state: "pending" }],
    },
    designBrief: {
      summary_zh: "Need one more decision before delivery",
      open_questions: ["Approve whether to ship the current run as-is"],
    },
    finalReport: {
      summary_zh: "Current report is ready for review.",
    },
    messageCount: 18,
    artifactCount: 12,
  });

  assert.equal(model.primaryStage, "plan");
  assert.deepEqual(model.reachableStages, ["plan", "execute", "results"]);
});
