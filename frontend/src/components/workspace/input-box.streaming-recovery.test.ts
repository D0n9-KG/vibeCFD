import assert from "node:assert/strict";
import test from "node:test";

const { recoverStreamingDraftIfPossible } = await import(
  new URL("./input-box.streaming-recovery.ts", import.meta.url).href
);

void test("recoverStreamingDraftIfPossible stops the stale run and resubmits the draft when recovery succeeds", async () => {
  const calls: string[] = [];
  const message = {
    text: "请重新执行 baseline 与 scientific studies。",
    files: [],
  };

  const outcome = await recoverStreamingDraftIfPossible({
    message,
    recover: async () => {
      calls.push("recover");
      return {
        recovered: true,
        latestRunStatus: "interrupted",
        reason: "command_exit_after_run_start",
      };
    },
    stop: async () => {
      calls.push("stop");
    },
    submit: async (submittedMessage) => {
      calls.push(`submit:${submittedMessage.text}`);
    },
  });

  assert.equal(outcome.kind, "recovered_and_submitted");
  assert.deepEqual(calls, [
    "recover",
    "stop",
    "submit:请重新执行 baseline 与 scientific studies。",
  ]);
});

void test("recoverStreamingDraftIfPossible preserves the draft when recovery is not allowed", async () => {
  const calls: string[] = [];

  const outcome = await recoverStreamingDraftIfPossible({
    message: {
      text: "请继续。",
      files: [],
    },
    recover: async () => {
      calls.push("recover");
      return {
        recovered: false,
        latestRunStatus: "running",
        reason: "no_command_exit_evidence",
      };
    },
    stop: async () => {
      calls.push("stop");
    },
    submit: async () => {
      calls.push("submit");
    },
  });

  assert.equal(outcome.kind, "preserved_draft");
  assert.deepEqual(calls, ["recover"]);
});
