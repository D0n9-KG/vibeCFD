import type { PromptInputMessage } from "../ai-elements/prompt-input";

type RecoveryResult = {
  recovered: boolean;
  reason: string;
  latestRunStatus: string | null;
};

type RecoverStreamingDraftIfPossibleInput = {
  message: PromptInputMessage;
  recover: () => Promise<RecoveryResult>;
  stop?: () => Promise<void> | void;
  submit: (message: PromptInputMessage) => Promise<void> | void;
};

type RecoveredAndSubmittedOutcome = {
  kind: "recovered_and_submitted";
  result: RecoveryResult;
};

type PreservedDraftOutcome = {
  kind: "preserved_draft";
  result: RecoveryResult;
};

export type StreamingDraftRecoveryOutcome =
  | RecoveredAndSubmittedOutcome
  | PreservedDraftOutcome;

export async function recoverStreamingDraftIfPossible({
  message,
  recover,
  stop,
  submit,
}: RecoverStreamingDraftIfPossibleInput): Promise<StreamingDraftRecoveryOutcome> {
  const result = await recover();
  if (!result.recovered) {
    return {
      kind: "preserved_draft",
      result,
    };
  }

  try {
    await stop?.();
  } catch {
    // Server-side cancel is the authoritative recovery path.
  }

  await submit(message);
  return {
    kind: "recovered_and_submitted",
    result,
  };
}
