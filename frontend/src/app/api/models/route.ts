import { loadConfiguredModels } from "./config-models";

export async function GET() {
  const models = await loadConfiguredModels();
  return Response.json({ models });
}
