import type { AgentInventoryResponse } from "@/core/agents/types";

import { proxyAgentsRequest } from "./_backend";
import { mergeCanonicalAgentsWithLegacyAgents } from "./migration";
import { listLegacyCustomAgents } from "./store";

export async function GET(request: Request) {
  const backendResponse = await proxyAgentsRequest("/api/agents", request);
  if (!backendResponse.ok) {
    return backendResponse;
  }

  const backendPayload =
    (await backendResponse.json()) as AgentInventoryResponse;
  const legacyCustomAgents = await listLegacyCustomAgents();
  return Response.json({
    ...backendPayload,
    agents: mergeCanonicalAgentsWithLegacyAgents(
      backendPayload.agents ?? [],
      legacyCustomAgents,
    ),
  });
}

export async function POST(request: Request) {
  return proxyAgentsRequest("/api/agents", request);
}
