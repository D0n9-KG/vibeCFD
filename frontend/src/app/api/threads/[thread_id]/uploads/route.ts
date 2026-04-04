import { saveUploadedFiles, UploadStorageError } from "./storage";

export async function POST(
  request: Request,
  context: {
    params: Promise<{
      thread_id: string;
    }>;
  },
) {
  const { thread_id: threadId } = await context.params;

  try {
    const formData = await request.formData();
    const files = formData
      .getAll("files")
      .filter((value): value is File => value instanceof File);

    const response = await saveUploadedFiles(threadId, files);
    return Response.json(response, { status: 200 });
  } catch (error) {
    if (error instanceof UploadStorageError) {
      return Response.json({ detail: error.message }, { status: error.status });
    }

    const detail =
      error instanceof Error ? error.message : "Failed to upload files.";
    return Response.json({ detail }, { status: 500 });
  }
}
