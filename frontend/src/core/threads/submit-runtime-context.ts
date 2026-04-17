export type ThreadSubmitMode = "flash" | "thinking" | "pro" | "ultra" | undefined;

export type ThreadSubmitReasoningEffort =
  | "minimal"
  | "low"
  | "medium"
  | "high";

export type ThreadSubmitContextInput = {
  model_name?: string | undefined;
  mode: ThreadSubmitMode;
  reasoning_effort?: ThreadSubmitReasoningEffort;
};

export type ThreadSubmitContextOverrides = Record<string, unknown> & {
  is_plan_mode?: boolean;
};

export type ThreadSubmitContextOptions = {
  defaultPlanMode?: boolean;
};

function resolveReasoningEffort(
  mode: ThreadSubmitMode,
  reasoningEffort?: ThreadSubmitReasoningEffort,
): ThreadSubmitReasoningEffort | undefined {
  if (reasoningEffort) {
    return reasoningEffort;
  }

  if (mode === "ultra") {
    return "high";
  }
  if (mode === "pro") {
    return "medium";
  }
  if (mode === "thinking") {
    return "low";
  }
  return undefined;
}

export function composeThreadSubmitContext(
  threadId: string,
  context: ThreadSubmitContextInput,
  extraContext: ThreadSubmitContextOverrides = {},
  options: ThreadSubmitContextOptions = {},
) {
  const defaultPlanMode = options.defaultPlanMode ?? false;
  const isPlanMode =
    typeof extraContext.is_plan_mode === "boolean"
      ? extraContext.is_plan_mode
      : defaultPlanMode;

  return {
    ...extraContext,
    ...context,
    thinking_enabled: context.mode !== "flash",
    is_plan_mode: isPlanMode,
    subagent_enabled: context.mode === "ultra",
    reasoning_effort: resolveReasoningEffort(
      context.mode,
      context.reasoning_effort,
    ),
    thread_id: threadId,
  };
}
