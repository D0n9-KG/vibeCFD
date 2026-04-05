import { randomUUID } from "crypto";

import type { NextRequest } from "next/server";

import {
  applyMockThreadAction,
  readMockThread,
  writeMockThread,
} from "../../../mock-thread-store";

function extractActionText(payload: unknown): string {
  if (!payload || typeof payload !== "object") {
    return "";
  }

  const input = "input" in payload ? payload.input : undefined;
  if (!input || typeof input !== "object") {
    return "";
  }

  const messages =
    "messages" in input && Array.isArray(input.messages) ? input.messages : [];
  const latestMessage = messages.at(-1);
  if (!latestMessage || typeof latestMessage !== "object") {
    return "";
  }

  const content = "content" in latestMessage ? latestMessage.content : undefined;
  if (typeof content === "string") {
    return content;
  }

  if (!Array.isArray(content)) {
    return "";
  }

  return content
    .map((item) => {
      if (
        item &&
        typeof item === "object" &&
        "type" in item &&
        item.type === "text" &&
        "text" in item &&
        typeof item.text === "string"
      ) {
        return item.text;
      }
      return "";
    })
    .join("")
    .trim();
}

function encodeSseEvent(id: string, event: string, data: unknown) {
  return `id: ${id}\nevent: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ thread_id: string }> },
) {
  const threadId = (await params).thread_id;
  const payload = (await request.json().catch(() => ({}))) as Record<
    string,
    unknown
  >;
  const actionText = extractActionText(payload);
  const nowIso = new Date().toISOString();
  const nextState = applyMockThreadAction(
    readMockThread(threadId),
    actionText,
    nowIso,
  );
  writeMockThread(threadId, nextState);

  const runId = `mock-run-${randomUUID()}`;
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(
        encoder.encode(
          encodeSseEvent("0", "metadata", {
            run_id: runId,
            thread_id: threadId,
          }),
        ),
      );
      controller.enqueue(
        encoder.encode(encodeSseEvent("1", "values", nextState.values ?? {})),
      );
      controller.close();
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "Content-Location": `/threads/${threadId}/runs/${runId}`,
    },
  });
}
