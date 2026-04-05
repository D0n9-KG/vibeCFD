import type { UpdateAgentRequest } from "@/core/agents/types";

import {
  deleteStoredAgent,
  getStoredAgent,
  updateStoredAgent,
} from "../store";

export async function GET(
  _request: Request,
  context: { params: Promise<{ name: string }> },
) {
  const { name } = await context.params;
  const agent = await getStoredAgent(name);
  if (!agent) {
    return Response.json({ detail: `Agent '${name}' not found.` }, { status: 404 });
  }

  return Response.json(agent);
}

export async function PUT(
  request: Request,
  context: { params: Promise<{ name: string }> },
) {
  const { name } = await context.params;
  try {
    const payload = (await request.json()) as UpdateAgentRequest;
    const agent = await updateStoredAgent(name, payload);
    return Response.json(agent);
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
  try {
    await deleteStoredAgent(name);
    return new Response(null, { status: 204 });
  } catch (error) {
    const detail =
      error instanceof Error ? error.message : "Failed to delete agent.";
    const status = detail.includes("not found") ? 404 : 400;
    return Response.json({ detail }, { status });
  }
}
