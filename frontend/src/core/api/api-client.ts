"use client";

import { Client as LangGraphClient } from "@langchain/langgraph-sdk/client";

import { getLangGraphBaseURL } from "../config";

import { sanitizeRunStreamOptions } from "./stream-mode";

function resolveValidatedApiUrl(isMock?: boolean): string {
  const apiUrl = getLangGraphBaseURL(isMock).trim();

  if (!apiUrl) {
    throw new Error("LangGraph base URL is empty or invalid.");
  }

  try {
    new URL(apiUrl);
  } catch {
    throw new Error("LangGraph base URL is empty or invalid.");
  }

  return apiUrl;
}

function createCompatibleClient(apiUrl: string): LangGraphClient {
  const client = new LangGraphClient({
    apiUrl,
  });

  const originalRunStream = client.runs.stream.bind(client.runs);
  client.runs.stream = ((threadId, assistantId, payload) =>
    originalRunStream(
      threadId,
      assistantId,
      sanitizeRunStreamOptions(payload),
    )) as typeof client.runs.stream;

  const originalJoinStream = client.runs.joinStream.bind(client.runs);
  client.runs.joinStream = ((threadId, runId, options) =>
    originalJoinStream(
      threadId,
      runId,
      sanitizeRunStreamOptions(options),
    )) as typeof client.runs.joinStream;

  return client;
}

const clientsByApiUrl = new Map<string, LangGraphClient>();

export function getAPIClient(isMock?: boolean): LangGraphClient {
  const apiUrl = resolveValidatedApiUrl(isMock);
  const cachedClient = clientsByApiUrl.get(apiUrl);
  if (cachedClient) {
    return cachedClient;
  }

  const client = createCompatibleClient(apiUrl);
  clientsByApiUrl.set(apiUrl, client);
  return client;
}
