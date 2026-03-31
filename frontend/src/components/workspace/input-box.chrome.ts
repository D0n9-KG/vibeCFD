export type InputMode = "flash" | "thinking" | "pro" | "ultra";

export function getResolvedMode(
  mode: InputMode | undefined,
  supportsThinking: boolean,
): InputMode {
  if (!supportsThinking && mode !== "flash") {
    return "flash";
  }
  if (mode) {
    return mode;
  }
  return supportsThinking ? "pro" : "flash";
}

export function getInputBoxChromeState({
  mounted,
  mode,
  supportsThinking,
  supportsReasoningEffort,
}: {
  mounted: boolean;
  mode: InputMode | undefined;
  supportsThinking: boolean;
  supportsReasoningEffort: boolean;
}) {
  const resolvedMode = getResolvedMode(mode, supportsThinking);

  return {
    interactive: mounted,
    resolvedMode,
    showReasoningEffort: supportsReasoningEffort && resolvedMode !== "flash",
  };
}
