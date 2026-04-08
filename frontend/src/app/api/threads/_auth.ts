import { getSession } from "@/server/better-auth/server";

export async function requireThreadRouteSession() {
  const session = await getSession();
  if (!session) {
    return Response.json({ detail: "Unauthorized" }, { status: 401 });
  }

  return null;
}
