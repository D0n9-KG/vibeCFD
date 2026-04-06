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
  assert.equal(model.trustSurface.environmentParityAvailable, true);
  assert.equal(model.trustSurface.provenanceAvailable, true);
  assert.equal(model.trustSurface.reproducibilityAvailable, true);
});
