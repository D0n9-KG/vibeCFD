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
      "scientific-gate",
      "experiment-compare",
      "remediation",
      "follow-up",
    ],
  );
  assert.equal(model.trustPanels[0]?.status, "available");
  assert.equal(model.trustPanels[1]?.status, "available");
  assert.equal(model.trustPanels[2]?.status, "available");
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
  assert.equal(model.operatorBoard.remediation.actionCount, 1);
  assert.equal(model.operatorBoard.timelineEntryCount, 1);
});

void test("preserves trust-critical cues across provenance, reproducibility, parity, and scientific gate", () => {
  const model = buildSubmarineDetailModel({
    runtime: {
      environment_parity_assessment: {
        parity_status: "drifted",
        drift_reasons: ["docker socket unavailable"],
        recovery_guidance: ["retry in containerized runner"],
      },
      scientific_gate_status: "blocked",
    },
    finalReport: {
      provenance_manifest_virtual_path: "/artifacts/submarine/provenance-manifest.json",
      evidence_index: [
        {
          group_id: "forces",
          group_title_zh: "Force coefficients",
        },
      ],
      reproducibility_summary: {
        reproducibility_status: "needs_review",
        parity_status: "drifted",
        drift_reasons: ["solver image mismatch"],
        recovery_guidance: ["pin OpenFOAM image"],
      },
      scientific_supervisor_gate: {
        gate_status: "blocked",
        blocking_reasons: ["missing independent validation"],
        advisory_notes: ["run additional benchmark"],
      },
      research_evidence_summary: {
        readiness_status: "partial",
        blocking_issues: ["no uncertainty bounds"],
      },
    },
  });

  const gatePanel = model.trustPanels.find((panel) => panel.id === "scientific-gate");
  assert.ok(gatePanel);
  assert.equal(gatePanel?.status, "available");
  assert.ok(gatePanel?.highlights.some((line) => line.includes("blocked")));
});

void test("preserves delivery decision, remediation handoff/manual actions, follow-up context, and study summary", () => {
  const model = buildSubmarineDetailModel({
    runtime: {
      activity_timeline: [
        { title: "Dispatch variant", actor: "worker-b" },
        { title: "Compare report", actor: "supervisor" },
      ],
    },
    finalReport: {
      experiment_summary: {
        baseline_run_id: "baseline",
        compare_count: 2,
        run_count: 3,
        compared_variant_run_ids: ["variant-a", "variant-b"],
      },
      experiment_compare_summary: {
        comparisons: [
          {
            candidate_run_id: "variant-a",
            compare_status: "completed",
            variant_label: "A",
            baseline_reference_run_id: "baseline",
          },
        ],
      },
      scientific_study_summary: {
        study_execution_status: "running",
        studies: [
          {
            summary_label: "AoA sweep",
            workflow_status: "in_progress",
          },
        ],
      },
      delivery_decision_summary: {
        decision_question_zh: "Can this be delivered for external review?",
        decision_status: "blocked",
        options: [{ option_id: "o1", label_zh: "Remediate first" }],
        blocking_reason_lines: ["validation gap"],
        advisory_note_lines: ["prioritize mesh refinement"],
      },
      scientific_remediation_summary: {
        plan_status: "needed",
        actions: [{ action_id: "r1", title: "Refine mesh near hull wake" }],
      },
      scientific_remediation_handoff: {
        handoff_status: "ready",
        tool_name: "spawn_agent",
        manual_actions: [{ action_id: "m1", title: "Approve rerun" }],
      },
      scientific_followup_summary: {
        latest_outcome_status: "pending",
        latest_notes: ["Awaiting supervisor sign-off"],
        latest_tool_name: "spawn_agent",
      },
    },
  });

  assert.equal(model.operatorBoard.deliveryDecision.question?.length ? true : false, true);
  assert.equal(model.operatorBoard.deliveryDecision.optionCount, 1);
  assert.equal(model.operatorBoard.remediation.handoffStatus, "ready");
  assert.equal(model.operatorBoard.remediation.manualActionCount, 1);
  assert.equal(model.operatorBoard.followup.latestToolName, "spawn_agent");
  assert.equal(model.experimentBoard.variantCount, 2);
  assert.equal(model.experimentBoard.comparisons.length, 1);
  assert.equal(model.experimentBoard.studyCount, 1);
});
