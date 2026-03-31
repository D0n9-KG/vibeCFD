import assert from "node:assert/strict";
import test from "node:test";

const {
  deriveSubmarineSidebarRuns,
  getSubmarineDisplayedNextStage,
  getSubmarineDisplayedStage,
} = await import(
  new URL("./submarine-pipeline-runs.ts", import.meta.url).href,
);

void test("marks unresolved confirmation threads as pending instead of running forever", () => {
  const runs = deriveSubmarineSidebarRuns([
    {
      thread_id: "thread-awaiting-confirmation",
      values: {
        title: "SUBOFF baseline draft",
        artifacts: [
          "/mnt/user-data/outputs/submarine/design-brief/suboff/cfd-design-brief.json",
        ],
        submarine_runtime: {
          current_stage: "task-intelligence",
          stage_status: "draft",
          review_status: "needs_user_confirmation",
          next_recommended_stage: "user-confirmation",
        },
      },
    },
  ]);

  assert.equal(runs.length, 1);
  assert.equal(runs[0]?.isRunning, false);
  assert.equal(runs[0]?.isComplete, false);
  assert.equal(
    getSubmarineDisplayedStage({
      current_stage: "solver-dispatch",
      review_status: "needs_user_confirmation",
      next_recommended_stage: "user-confirmation",
    }),
    "task-intelligence",
  );
  assert.equal(
    getSubmarineDisplayedNextStage(
      {
        current_stage: "solver-dispatch",
        review_status: "needs_user_confirmation",
        next_recommended_stage: "solver-dispatch",
      },
      {
        confirmation_status: "draft",
        open_questions: ["是否使用默认海水黏度"],
      },
    ),
    "user-confirmation",
  );
});

void test("treats final-report threads as complete even when legacy is_complete is absent", () => {
  const runs = deriveSubmarineSidebarRuns([
    {
      thread_id: "thread-finished-report",
      values: {
        title: "SUBOFF completed run",
        artifacts: [
          "/mnt/user-data/outputs/submarine/reports/suboff/final-report.json",
        ],
        submarine_runtime: {
          current_stage: "result-reporting",
          stage_status: "executed",
          review_status: "ready_for_supervisor",
          next_recommended_stage: "supervisor-review",
        },
      },
    },
  ]);

  assert.equal(runs.length, 1);
  assert.equal(runs[0]?.isRunning, false);
  assert.equal(runs[0]?.isComplete, true);
});

void test("ignores history entries whose thread values payload is missing", () => {
  const runs = deriveSubmarineSidebarRuns([
    {
      thread_id: "thread-missing-values",
      values: null,
    },
  ]);

  assert.deepEqual(runs, []);
});
