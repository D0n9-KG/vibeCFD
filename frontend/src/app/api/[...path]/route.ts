import { proxyBackendRequest } from "../_backend";

export async function GET(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxyBackendRequest(`/api/${path.join("/")}`, request);
}

export async function POST(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxyBackendRequest(`/api/${path.join("/")}`, request);
}

export async function PUT(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxyBackendRequest(`/api/${path.join("/")}`, request);
}

export async function PATCH(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxyBackendRequest(`/api/${path.join("/")}`, request);
}

export async function DELETE(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxyBackendRequest(`/api/${path.join("/")}`, request);
}

export async function HEAD(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return proxyBackendRequest(`/api/${path.join("/")}`, request);
}
