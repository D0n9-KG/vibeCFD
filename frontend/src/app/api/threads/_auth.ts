import { env } from "@/env";
import { getSession } from "@/server/better-auth/server";

import { shouldRequireThreadRouteSession } from "./_auth.policy";

export async function requireThreadRouteSession() {
  if (
    !shouldRequireThreadRouteSession({
      nodeEnv: env.NODE_ENV,
      betterAuthSecret: env.BETTER_AUTH_SECRET,
    })
  ) {
    return null;
  }

  const session = await getSession();
  if (!session) {
    return Response.json({ detail: "Unauthorized" }, { status: 401 });
  }

  return null;
}
