import type { FileUIPart } from "ai";
import { nanoid } from "nanoid";

export type PromptInputAttachment = FileUIPart & {
  id: string;
  file: File;
};

export type PromptInputSubmitFile = FileUIPart & {
  file?: File;
};

export function createPromptInputAttachment(file: File): PromptInputAttachment {
  return {
    id: nanoid(),
    type: "file",
    url: URL.createObjectURL(file),
    mediaType: file.type,
    filename: file.name,
    file,
  };
}

export function preparePromptInputSubmitFiles(
  files: PromptInputAttachment[],
): PromptInputSubmitFile[] {
  return files.map(({ id: _id, ...file }) => file);
}
