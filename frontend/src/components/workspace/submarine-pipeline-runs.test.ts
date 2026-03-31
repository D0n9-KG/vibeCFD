import assert from "node:assert/strict";
import test from "node:test";

const {
  deriveCompletedSubmarineRunIds,
  deriveSubmarineRunDeletionPath,
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

void test("deriveCompletedSubmarineRunIds returns only completed submarine runs", () => {
  assert.equal(typeof deriveCompletedSubmarineRunIds, "function");

  assert.deepEqual(
    deriveCompletedSubmarineRunIds([
      {
        threadId: "run-active",
        title: "Running study",
        isRunning: true,
        isComplete: false,
      },
      {
        threadId: "run-complete-a",
        title: "Completed baseline",
        isRunning: false,
        isComplete: true,
      },
      {
        threadId: "run-complete-b",
        title: "Completed variant",
        isRunning: false,
        isComplete: true,
      },
    ]),
    ["run-complete-a", "run-complete-b"],
  );
});

void test("deriveSubmarineRunDeletionPath keeps cleanup navigation inside submarine runs", () => {
  assert.equal(typeof deriveSubmarineRunDeletionPath, "function");

  assert.equal(
    deriveSubmarineRunDeletionPath(
      [
        {
          thread_id: "run-current",
          values: {
            title: "Current completed run",
            submarine_runtime: { current_stage: "result-reporting" },
          },
        },
        {
          thread_id: "skill-thread",
          values: {
            title: "Skill studio helper",
            submarine_skill_studio: { skill_name: "mesh-doctor" },
          },
        },
        {
          thread_id: "run-next",
          values: {
            title: "Next submarine run",
            submarine_runtime: { current_stage: "solver-dispatch" },
          },
        },
      ],
      ["run-current"],
      "run-current",
    ),
    "/workspace/submarine/run-next",
  );
});

void test("deriveSubmarineRunDeletionPath returns null when current run survives cleanup", () => {
  assert.equal(
    deriveSubmarineRunDeletionPath(
      [
        {
          thread_id: "run-current",
          values: {
            title: "Current active run",
            submarine_runtime: { current_stage: "solver-dispatch" },
          },
        },
        {
          thread_id: "run-complete",
          values: {
            title: "Completed run",
            submarine_runtime: { current_stage: "result-reporting" },
          },
        },
      ],
      ["run-complete"],
      "run-current",
    ),
    null,
  );
});

void test("deriveSubmarineRunDeletionPath falls back to a fresh submarine workspace when nothing remains", () => {
  assert.equal(
    deriveSubmarineRunDeletionPath(
      [
        {
          thread_id: "run-current",
          values: {
            title: "Only completed run",
            submarine_runtime: { current_stage: "result-reporting" },
          },
        },
      ],
      ["run-current"],
      "run-current",
    ),
    "/workspace/submarine/new",
  );
});
