import type { PromptInputSubmitFile } from "../../components/ai-elements/prompt-input.files.ts";

export async function prepareThreadUploadFiles(
  files: PromptInputSubmitFile[],
  fetchBlobUrl: typeof fetch = fetch,
): Promise<File[]> {
  return Promise.all(
    files.map(async (fileUIPart) => {
      if (fileUIPart.file instanceof File) {
        return fileUIPart.file;
      }

      if (fileUIPart.url && fileUIPart.filename) {
        const response = await fetchBlobUrl(fileUIPart.url);
        const blob = await response.blob();

        return new File([blob], fileUIPart.filename, {
          type: fileUIPart.mediaType || blob.type,
        });
      }

      throw new Error(
        `Failed to prepare attachment "${fileUIPart.filename ?? "unnamed"}" for upload.`,
      );
    }),
  );
}
