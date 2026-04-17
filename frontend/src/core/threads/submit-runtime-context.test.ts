import assert from "node:assert/strict";
import test from "node:test";

type ThreadComposerModule = {
  composeThreadSubmitContext?: (
    threadId: string,
    context: {
      model_name: string | undefined;
      mode: "flash" | "thinking" | "pro" | "ultra" | undefined;
      reasoning_effort?: "minimal" | "low" | "medium" | "high";
    },
    extraContext?: Record<string, unknown>,
    options?: {
      defaultPlanMode?: boolean;
    },
  ) => Record<string, unknown>;
};

async function loadComposerModule(): Promise<ThreadComposerModule> {
  try {
    return (await import(
      new URL("./submit-runtime-context.ts", import.meta.url).href
    )) as ThreadComposerModule;
  } catch {
    return {};
  }
}

void test("composeThreadSubmitContext keeps reasoning modes out of plan mode by default", async () => {
  const composerModule = await loadComposerModule();

  assert.equal(typeof composerModule.composeThreadSubmitContext, "function");
  if (typeof composerModule.composeThreadSubmitContext !== "function") {
    return;
  }

  assert.deepEqual(
    composerModule.composeThreadSubmitContext("thread-pro", {
      model_name: "gpt-5.4",
      mode: "pro",
      reasoning_effort: "medium",
    }),
    {
      model_name: "gpt-5.4",
      mode: "pro",
      reasoning_effort: "medium",
      thinking_enabled: true,
      is_plan_mode: false,
      subagent_enabled: false,
      thread_id: "thread-pro",
    },
  );

  assert.deepEqual(
    composerModule.composeThreadSubmitContext("thread-ultra", {
      model_name: "gpt-5.4",
      mode: "ultra",
    }),
    {
      model_name: "gpt-5.4",
      mode: "ultra",
      reasoning_effort: "high",
      thinking_enabled: true,
      is_plan_mode: false,
      subagent_enabled: true,
      thread_id: "thread-ultra",
    },
  );
});

void test("composeThreadSubmitContext honors an explicit plan-mode override", async () => {
  const composerModule = await loadComposerModule();

  assert.equal(typeof composerModule.composeThreadSubmitContext, "function");
  if (typeof composerModule.composeThreadSubmitContext !== "function") {
    return;
  }

  assert.deepEqual(
    composerModule.composeThreadSubmitContext(
      "thread-plan",
      {
        model_name: "gpt-5.4",
        mode: "thinking",
        reasoning_effort: "low",
      },
      {
        agent_name: "planner",
        is_plan_mode: true,
      },
    ),
    {
      agent_name: "planner",
      is_plan_mode: true,
      model_name: "gpt-5.4",
      mode: "thinking",
      reasoning_effort: "low",
      thinking_enabled: true,
      subagent_enabled: false,
      thread_id: "thread-plan",
    },
  );
});

void test("composeThreadSubmitContext supports non-submarine surfaces that still default into plan mode", async () => {
  const composerModule = await loadComposerModule();

  assert.equal(typeof composerModule.composeThreadSubmitContext, "function");
  if (typeof composerModule.composeThreadSubmitContext !== "function") {
    return;
  }

  assert.deepEqual(
    composerModule.composeThreadSubmitContext(
      "thread-skill",
      {
        model_name: "gpt-5.4",
        mode: "pro",
      },
      {},
      {
        defaultPlanMode: true,
      },
    ),
    {
      model_name: "gpt-5.4",
      mode: "pro",
      reasoning_effort: "medium",
      thinking_enabled: true,
      is_plan_mode: true,
      subagent_enabled: false,
      thread_id: "thread-skill",
    },
  );
});
