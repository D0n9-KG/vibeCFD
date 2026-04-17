import assert from "node:assert/strict";
import test from "node:test";

const { buildProxyTargetURL, proxyBackendRequest } = await import(
  new URL("./_backend.ts", import.meta.url).href,
);

void test("buildProxyTargetURL keeps regular API calls on the backend service", () => {
  const url = buildProxyTargetURL(
    "/api/models",
    "http://127.0.0.1:3200/api/models?include=all",
  );

  assert.equal(url.toString(), "http://localhost:8001/api/models?include=all");
});

void test("buildProxyTargetURL routes langgraph API calls to the langgraph service root", () => {
  const url = buildProxyTargetURL(
    "/api/langgraph/threads/search",
    "http://127.0.0.1:3200/api/langgraph/threads/search?limit=1",
  );

  assert.equal(url.toString(), "http://localhost:2024/threads/search?limit=1");
});

void test("buildProxyTargetURL prefers a server-only langgraph proxy target override", () => {
  const url = buildProxyTargetURL(
    "/api/langgraph/threads/search",
    "http://127.0.0.1:3200/api/langgraph/threads/search?limit=1",
    { langGraphProxyBaseURL: "http://127.0.0.1:2124" },
  );

  assert.equal(url.toString(), "http://127.0.0.1:2124/threads/search?limit=1");
});

void test("proxyBackendRequest preserves backend 204 no-content responses", async () => {
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async () =>
    new Response(null, {
      status: 204,
      statusText: "No Content",
      headers: {
        "x-test-header": "ok",
      },
    });

  try {
    const request = new Request("http://127.0.0.1:3000/api/agents/example", {
      method: "DELETE",
    });
    const response = await proxyBackendRequest("/api/agents/example", request);

    assert.equal(response.status, 204);
    assert.equal(await response.text(), "");
    assert.equal(response.headers.get("x-test-header"), "ok");
  } finally {
    globalThis.fetch = originalFetch;
  }
});
