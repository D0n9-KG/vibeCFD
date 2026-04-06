import assert from "node:assert/strict";
import test from "node:test";

const { buildSubmarineDetailModel } = await import(
  new URL("./submarine-detail-model.ts", import.meta.url).href
);

void test("keeps all trust-critical submarine evidence surfaces explicit", () => {
  const model = buildSubmarineDetailModel({
    runtime: {
      environment_parity_assessment: {
        parity_status: "aligned",
        profile_label: "OpenFOAM-12",
      },
    },
    finalReport: {
      provenance_manifest_virtual_path: "/artifacts/submarine/provenance.json",
      reproducibility_summary: {
        manifest_virtual_path: "/artifacts/submarine/repro.json",
        reproducibility_status: "reproducible",
      },
      experiment_summary: {
        baseline_run_id: "baseline-01",
        compare_count: 3,
      },
      scientific_remediation_summary: {
        plan_status: "needed",
      },
      scientific_followup_summary: {
        latest_outcome_status: "pending",
      },
    },
  });

  assert.deepEqual(
    model.trustPanels.map((panel) => panel.id),
    [
      "provenance",
      "reproducibility",
      "environment-parity",
      "experiment-compare",
      "remediation",
      "follow-up",
    ],
  );
  assert.equal(
    model.trustPanels.every((panel) => panel.status === "available"),
    true,
  );
});

void test("builds experiment and operator boards from report contracts", () => {
  const model = buildSubmarineDetailModel({
    runtime: {
      execution_plan: [
        { role_id: "solver", owner: "worker-a", goal: "Run baseline" },
      ],
      activity_timeline: [{ actor: "worker-a", title: "Baseline solved" }],
    },
    finalReport: {
      experiment_summary: {
        baseline_run_id: "baseline-01",
        run_count: 4,
        compare_count: 2,
      },
      experiment_compare_summary: {
        compare_status_counts: { completed: 2 },
      },
      scientific_remediation_summary: {
        plan_status: "in_progress",
        actions: [{ action_id: "a1", title: "Refine mesh" }],
      },
      scientific_followup_summary: {
        latest_outcome_status: "needs_followup",
      },
      delivery_decision_summary: {
        decision_status: "needs_followup",
      },
    },
  });

  assert.equal(model.experimentBoard.baselineRunId, "baseline-01");
  assert.equal(model.experimentBoard.compareCount, 2);
  assert.equal(model.operatorBoard.decisionStatus, "needs_followup");
  assert.equal(model.operatorBoard.remediationActionCount, 1);
  assert.equal(model.operatorBoard.timelineEntryCount, 1);
});
