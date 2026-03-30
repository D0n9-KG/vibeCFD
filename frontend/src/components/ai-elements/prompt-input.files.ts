import type { FileUIPart } from "ai";

export function preparePromptInputSubmitFiles(
  files: Array<FileUIPart & { id: string }>,
): FileUIPart[] {
  return files.map(({ id: _id, ...file }) => file);
}
