import { deleteThreadUpload, UploadStorageError } from "../storage";

export async function DELETE(
  _request: Request,
  context: {
    params: Promise<{
      thread_id: string;
      filename: string;
    }>;
  },
) {
  const { thread_id: threadId, filename } = await context.params;

  try {
    const response = await deleteThreadUpload(threadId, decodeURIComponent(filename));
    return Response.json(response, { status: 200 });
  } catch (error) {
    if (error instanceof UploadStorageError) {
      return Response.json({ detail: error.message }, { status: error.status });
    }

    const detail =
      error instanceof Error ? error.message : "Failed to delete file.";
    return Response.json({ detail }, { status: 500 });
  }
}
