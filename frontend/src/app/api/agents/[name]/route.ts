import type { UpdateAgentRequest } from "@/core/agents/types";

import { proxyAgentsRequest } from "../_backend";
import { markLegacyAgent } from "../migration";
import {
  deleteLegacyCustomAgent,
  getLegacyCustomAgent,
  updateLegacyCustomAgent,
} from "../store";

export async function GET(
  request: Request,
  context: { params: Promise<{ name: string }> },
) {
  const { name } = await context.params;
  const backendResponse = await proxyAgentsRequest(
    `/api/agents/${encodeURIComponent(name)}`,
    request,
  );
  if (backendResponse.status !== 404) {
    return backendResponse;
  }

  const agent = await getLegacyCustomAgent(name);
  if (agent === null) {
    return Response.json({ detail: `Agent '${name}' not found.` }, { status: 404 });
  }

  return Response.json(markLegacyAgent(agent));
}

export async function PUT(
  request: Request,
  context: { params: Promise<{ name: string }> },
) {
  const { name } = await context.params;
  const backendResponse = await proxyAgentsRequest(
    `/api/agents/${encodeURIComponent(name)}`,
    request,
  );
  if (backendResponse.status !== 404) {
    return backendResponse;
  }

  try {
    const payload = (await request.json()) as UpdateAgentRequest;
    const agent = await updateLegacyCustomAgent(name, payload);
    return Response.json(markLegacyAgent(agent));
  } catch (error) {
    const detail =
      error instanceof Error ? error.message : "Failed to update agent.";
    const status = detail.includes("not found") ? 404 : 400;
    return Response.json({ detail }, { status });
  }
}

export async function DELETE(
  _request: Request,
  context: { params: Promise<{ name: string }> },
) {
  const { name } = await context.params;
  const backendResponse = await proxyAgentsRequest(
    `/api/agents/${encodeURIComponent(name)}`,
    _request,
  );
  if (backendResponse.status !== 404) {
    return backendResponse;
  }

  try {
    await deleteLegacyCustomAgent(name);
    return new Response(null, { status: 204 });
  } catch (error) {
    const detail =
      error instanceof Error ? error.message : "Failed to delete agent.";
    const status = detail.includes("not found") ? 404 : 400;
    return Response.json({ detail }, { status });
  }
}
