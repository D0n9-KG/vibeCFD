import { proxyBackendRequest } from "../_backend";

const RUNTIME_CONFIG_PATH = "/api/runtime-config";

export async function GET(request: Request) {
  return proxyBackendRequest(RUNTIME_CONFIG_PATH, request);
}

export async function PUT(request: Request) {
  return proxyBackendRequest(RUNTIME_CONFIG_PATH, request);
}
