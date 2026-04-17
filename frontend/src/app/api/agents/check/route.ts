import { proxyAgentsRequest } from "../_backend";
import { hasLegacyCustomAgent } from "../store";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const name = url.searchParams.get("name") ?? "";
  const backendResponse = await proxyAgentsRequest(
    `/api/agents/check?name=${encodeURIComponent(name)}`,
    request,
  );
  if (!backendResponse.ok) {
    return backendResponse;
  }

  const backendPayload = (await backendResponse.json()) as {
    available: boolean;
    name: string;
  };
  const hasLegacyConflict = await hasLegacyCustomAgent(name);
  return Response.json({
    available: backendPayload.available && !hasLegacyConflict,
    name: backendPayload.name,
  });
}
