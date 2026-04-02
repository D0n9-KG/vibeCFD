import assert from "node:assert/strict";
import test from "node:test";

const {
  deriveSubmarineSidebarRuns,
  getSubmarineDisplayedNextStage,
  getSubmarineDisplayedStage,
} = await import(new URL("./submarine-pipeline-runs.ts", import.meta.url).href);

void test("sidebar marks persisted running runtime as active work", () => {
  const runs = deriveSubmarineSidebarRuns([
    {
      thread_id: "running-thread",
      values: {
        title: "Running submarine thread",
        submarine_runtime: {
          current_stage: "solver-dispatch",
          next_recommended_stage: "result-reporting",
          runtime_status: "running",
          stage_status: "in_progress",
        },
      },
    },
  ]);

  assert.equal(runs.length, 1);
  assert.equal(runs[0]?.isRunning, true);
  assert.equal(runs[0]?.isComplete, false);
});

void test("sidebar does not misclassify blocked runtime as active", () => {
  const runs = deriveSubmarineSidebarRuns([
    {
      thread_id: "blocked-thread",
      values: {
        title: "Blocked submarine thread",
        submarine_runtime: {
          current_stage: "solver-dispatch",
          next_recommended_stage: "result-reporting",
          runtime_status: "blocked",
          stage_status: "executed",
          review_status: "ready_for_supervisor",
        },
        artifacts: [
          "/mnt/user-data/outputs/submarine/solver-dispatch/blocked-thread/openfoam-request.json",
        ],
      },
    },
  ]);

  assert.equal(runs.length, 1);
  assert.equal(runs[0]?.isRunning, false);
  assert.equal(runs[0]?.isComplete, false);
});

void test("displayed stage still respects user-confirmation handoff", () => {
  const displayedStage = getSubmarineDisplayedStage(
    {
      current_stage: "geometry-preflight",
      next_recommended_stage: "solver-dispatch",
      review_status: "needs_user_confirmation",
    },
    {
      confirmation_status: "draft",
      open_questions: ["Need inlet velocity"],
    },
  );
  const displayedNextStage = getSubmarineDisplayedNextStage(
    {
      current_stage: "geometry-preflight",
      next_recommended_stage: "solver-dispatch",
      review_status: "needs_user_confirmation",
    },
    {
      confirmation_status: "draft",
      open_questions: ["Need inlet velocity"],
    },
  );

  assert.equal(displayedStage, "task-intelligence");
  assert.equal(displayedNextStage, "user-confirmation");
});

void test("pending calculation-plan approval also routes the UI to user confirmation", () => {
  const displayedStage = getSubmarineDisplayedStage(
    {
      current_stage: "geometry-preflight",
      next_recommended_stage: "solver-dispatch",
      calculation_plan: [
        {
          approval_state: "pending_researcher_confirmation",
        },
      ],
    },
    {
      confirmation_status: "confirmed",
      open_questions: [],
    },
  );
  const displayedNextStage = getSubmarineDisplayedNextStage(
    {
      current_stage: "geometry-preflight",
      next_recommended_stage: "solver-dispatch",
      calculation_plan: [
        {
          approval_state: "pending_researcher_confirmation",
        },
      ],
    },
    {
      confirmation_status: "confirmed",
      open_questions: [],
    },
  );

  assert.equal(displayedStage, "task-intelligence");
  assert.equal(displayedNextStage, "user-confirmation");
});
