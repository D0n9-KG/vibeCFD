import type { PromptInputMessage } from "../ai-elements/prompt-input.tsx";
import {
  preparePromptInputSubmitFiles,
  type PromptInputAttachment,
} from "../ai-elements/prompt-input.files.ts";

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
