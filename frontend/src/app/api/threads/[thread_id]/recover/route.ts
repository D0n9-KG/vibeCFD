import type { Run } from "@langchain/langgraph-sdk";
import type { NextRequest } from "next/server";

import { buildProxyTargetURL } from "../../../_backend";
import { requireThreadRouteSession } from "../../_auth";

import {
  decideRunningThreadRecovery,
  findLatestCommandExitAtForThread,
} from "./recovery";

async function fetchJSON<T>(input: URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    ...init,
    cache: "no-store",
  });

  if (!response.ok) {
    const detail =
      (await response.json().catch(() => null))?.detail ??
      `${response.status} ${response.statusText}`;
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export async function POST(
  request: NextRequest,
  context: {
    params: Promise<{
      thread_id: string;
    }>;
  },
) {
  const unauthorizedResponse = await requireThreadRouteSession();
  if (unauthorizedResponse) {
    return unauthorizedResponse;
  }

  const { thread_id: threadId } = await context.params;

  try {
    const latestRunsUrl = buildProxyTargetURL(
      `/api/langgraph/threads/${threadId}/runs`,
      request.url,
    );
    latestRunsUrl.searchParams.set("limit", "1");
    latestRunsUrl.searchParams.set("offset", "0");

    const runs = await fetchJSON<Run[]>(latestRunsUrl);
    const latestRun = runs[0] ?? null;
    const latestCommandExitAt = await findLatestCommandExitAtForThread(threadId);

    if (latestRun == null) {
      return Response.json({
        recovered: false,
        reason: "no_runs_found",
        latestRunStatus: null,
        runId: null,
        latestCommandExitAt: latestCommandExitAt?.toISOString() ?? null,
      });
    }

    const decision = decideRunningThreadRecovery({
      latestRunStatus: latestRun.status,
      latestRunCreatedAt: latestRun.created_at,
      latestCommandExitAt,
    });

    if (!decision.recoverable) {
      return Response.json({
        recovered: false,
        reason: decision.reason,
        latestRunStatus: latestRun.status,
        runId: latestRun.run_id,
        latestCommandExitAt: latestCommandExitAt?.toISOString() ?? null,
      });
    }

    const cancelUrl = buildProxyTargetURL(
      `/api/langgraph/threads/${threadId}/runs/${latestRun.run_id}/cancel`,
      request.url,
    );
    cancelUrl.searchParams.set("wait", "1");
    cancelUrl.searchParams.set("action", "interrupt");

    await fetchJSON(cancelUrl, {
      method: "POST",
    });

    return Response.json({
      recovered: true,
      reason: decision.reason,
      latestRunStatus: "interrupted",
      runId: latestRun.run_id,
      latestCommandExitAt: latestCommandExitAt?.toISOString() ?? null,
    });
  } catch (error) {
    const detail =
      error instanceof Error ? error.message : "Failed to recover thread run.";
    return Response.json({ detail }, { status: 500 });
  }
}
