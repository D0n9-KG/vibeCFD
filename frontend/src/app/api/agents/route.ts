import type { CreateAgentRequest } from "@/core/agents/types";

import { createStoredAgent, listStoredAgents } from "./store";

export async function GET() {
  const agents = await listStoredAgents();
  return Response.json({ agents });
}

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as CreateAgentRequest;
    const agent = await createStoredAgent(payload);
    return Response.json(agent, { status: 201 });
  } catch (error) {
    const detail =
      error instanceof Error ? error.message : "Failed to create agent.";
    return Response.json({ detail }, { status: 400 });
  }
}
