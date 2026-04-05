import type { NextRequest } from "next/server";

import { readMockThread } from "../../mock-thread-store";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ thread_id: string }> },
) {
  const threadId = (await params).thread_id;
  const json = readMockThread(threadId);
  if (Array.isArray(json.history)) {
    return Response.json(json);
  }
  return Response.json([json]);
}
