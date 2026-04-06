import assert from "node:assert/strict";
import test from "node:test";

const { buildSubmarineSessionModel } = await import(
  new URL("./submarine-session-model.ts", import.meta.url).href,
);

void test("keeps the eight research modules and starts new threads from proposal", () => {
  const model = buildSubmarineSessionModel({
    isNewThread: true,
    runtime: null,
    designBrief: null,
    finalReport: null,
    messageCount: 0,
    artifactCount: 0,
  });

  assert.deepEqual(
    model.modules.map((item: { id: string }) => item.id),
    [
      "proposal",
      "decision",
      "delegation",
      "skills",
      "execution",
      "postprocess-method",
      "postprocess-result",
      "report",
    ],
  );
  assert.equal(model.activeModuleId, "proposal");
  assert.equal(model.modules.filter((item: { expanded: boolean }) => item.expanded).length, 1);
});

void test("routes blocking approvals into the decision module", () => {
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

  assert.equal(model.activeModuleId, "decision");
  assert.equal(model.negotiation.pendingApprovalCount, 2);
  assert.match(model.negotiation.question ?? "", /确认|协商/);
});

void test("routes active execution traces into the execution module", () => {
  const model = buildSubmarineSessionModel({
    isNewThread: false,
    runtime: {
      runtime_status: "running",
      current_stage: "solver-dispatch",
      task_summary: "Dispatching parameterized variants.",
      execution_plan: [
        {
          role_id: "solver-worker",
          owner: "worker-a",
          goal: "Run baseline case",
          target_skills: ["submarine-solver-dispatch"],
        },
      ],
      activity_timeline: [
        {
          actor: "worker-a",
          title: "Running solver",
          skill_names: ["submarine-solver-dispatch"],
        },
      ],
    },
    designBrief: {
      summary_zh: "Variant sweep on drag coefficient",
      open_questions: [],
    },
    finalReport: null,
    messageCount: 14,
    artifactCount: 6,
  });

  assert.equal(model.activeModuleId, "execution");
  assert.equal(
    model.modules.find((item: { id: string }) => item.id === "skills")?.status,
    "已调用",
  );
  assert.equal(model.summary.evidenceReady, false);
});

void test("routes completed evidence into the report module", () => {
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

  assert.equal(model.activeModuleId, "report");
  assert.equal(model.summary.evidenceReady, true);
  assert.equal(model.trustSurface.environmentParityAvailable, true);
  assert.equal(model.trustSurface.provenanceAvailable, true);
  assert.equal(model.trustSurface.reproducibilityAvailable, true);
});
