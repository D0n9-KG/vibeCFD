import type { ChatStatus } from "ai";

import {
  preparePromptInputSubmitFiles,
  type PromptInputAttachment,
} from "../ai-elements/prompt-input.files.ts";
import type { PromptInputMessage } from "../ai-elements/prompt-input.tsx";

export function resolvePromptInputSubmission({
  message,
  attachments,
}: {
  message: PromptInputMessage;
  attachments: PromptInputAttachment[];
}): PromptInputMessage {
  if (message.files.length > 0 || attachments.length === 0) {
    return message;
  }

  return {
    ...message,
    files: preparePromptInputSubmitFiles(attachments),
  };
}

export type InputBoxSubmitAction =
  | {
      kind: "submit_message";
      message: PromptInputMessage;
    }
  | {
      kind: "stop_stream";
    }
  | {
      kind: "ignore_empty";
      message: PromptInputMessage;
    }
  | {
      kind: "preserve_draft_while_streaming";
      message: PromptInputMessage;
    };

export function resolveInputBoxSubmitAction({
  status,
  message,
  attachments,
}: {
  status: ChatStatus;
  message: PromptInputMessage;
  attachments: PromptInputAttachment[];
}): InputBoxSubmitAction {
  const resolvedMessage = resolvePromptInputSubmission({
    message,
    attachments,
  });
  const hasDraft =
    resolvedMessage.text.trim().length > 0 || resolvedMessage.files.length > 0;

  if (status === "streaming") {
    return hasDraft
      ? {
          kind: "preserve_draft_while_streaming",
          message: resolvedMessage,
        }
      : { kind: "stop_stream" };
  }

  if (!hasDraft) {
    return {
      kind: "ignore_empty",
      message: resolvedMessage,
    };
  }

  return {
    kind: "submit_message",
    message: resolvedMessage,
  };
}
