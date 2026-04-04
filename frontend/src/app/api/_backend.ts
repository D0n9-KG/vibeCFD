import { env } from "../../env.js";

const DEFAULT_BACKEND_BASE_URL = "http://localhost:8001";
const DEFAULT_LANGGRAPH_BASE_URL = "http://localhost:2024";
const LANGGRAPH_PROXY_PREFIX = "/api/langgraph";

const HOP_BY_HOP_HEADERS = [
  "connection",
  "content-length",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
];

function backendBaseURL() {
  const configured = env.NEXT_PUBLIC_BACKEND_BASE_URL?.trim();
  return configured && configured.length > 0
    ? configured
    : DEFAULT_BACKEND_BASE_URL;
}

function langGraphBaseURL() {
  const configured = env.NEXT_PUBLIC_LANGGRAPH_BASE_URL?.trim();
  return configured && configured.length > 0
    ? configured
    : DEFAULT_LANGGRAPH_BASE_URL;
}

function ensureTrailingSlash(url: string) {
  return url.endsWith("/") ? url : `${url}/`;
}

function isLangGraphProxyPath(path: string) {
  return path === LANGGRAPH_PROXY_PREFIX || path.startsWith(`${LANGGRAPH_PROXY_PREFIX}/`);
}

function stripLangGraphProxyPrefix(path: string) {
  if (!isLangGraphProxyPath(path)) {
    return path.replace(/^\/+/, "");
  }

  const stripped = path.slice(LANGGRAPH_PROXY_PREFIX.length).replace(/^\/+/, "");
  return stripped;
}

export function buildProxyTargetURL(path: string, requestURL: string | URL) {
  const incomingURL =
    requestURL instanceof URL ? requestURL : new URL(requestURL);
  const useLangGraphBase = isLangGraphProxyPath(path);
  const proxyBaseURL = useLangGraphBase ? langGraphBaseURL() : backendBaseURL();
  const proxyPath = stripLangGraphProxyPrefix(path);
  const targetURL = new URL(proxyPath, ensureTrailingSlash(proxyBaseURL));
  targetURL.search = incomingURL.search;
  return targetURL;
}

function buildForwardHeaders(request: Request) {
  const headers = new Headers(request.headers);
  for (const header of HOP_BY_HOP_HEADERS) {
    headers.delete(header);
  }
  return headers;
}

export async function proxyBackendRequest(
  path: string,
  request: Request,
): Promise<Response> {
  const targetURL = buildProxyTargetURL(path, request.url);

  const body =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  try {
    const response = await fetch(targetURL, {
      method: request.method,
      headers: buildForwardHeaders(request),
      body,
      cache: "no-store",
      redirect: "manual",
    });

    const responseHeaders = new Headers(response.headers);
    responseHeaders.set("cache-control", "no-store");
    responseHeaders.delete("content-length");

    const responseBody =
      request.method === "HEAD" ? undefined : await response.arrayBuffer();

    return new Response(responseBody, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    const detail =
      error instanceof Error ? error.message : "Failed to reach backend";
    return Response.json({ detail }, { status: 502 });
  }
}
