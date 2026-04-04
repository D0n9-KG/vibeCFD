import { isAgentNameAvailable } from "../store";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const name = url.searchParams.get("name") ?? "";
  return Response.json({
    available: await isAgentNameAvailable(name),
    name,
  });
}
