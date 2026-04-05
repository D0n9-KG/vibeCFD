import { listThreadUploads, UploadStorageError } from "../storage";

export async function GET(
  _request: Request,
  context: {
    params: Promise<{
      thread_id: string;
    }>;
  },
) {
  const { thread_id: threadId } = await context.params;

  try {
    const response = await listThreadUploads(threadId);
    return Response.json(response, { status: 200 });
  } catch (error) {
    if (error instanceof UploadStorageError) {
      return Response.json({ detail: error.message }, { status: error.status });
    }

    const detail =
      error instanceof Error ? error.message : "Failed to list uploaded files.";
    return Response.json({ detail }, { status: 500 });
  }
}
