export function shouldRequireThreadRouteSession({
  nodeEnv,
  betterAuthSecret,
}: {
  nodeEnv?: string;
  betterAuthSecret?: string;
}) {
  if (nodeEnv === "production") {
    return true;
  }

  return Boolean(betterAuthSecret && betterAuthSecret.trim().length > 0);
}
