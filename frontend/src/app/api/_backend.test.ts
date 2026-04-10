import assert from "node:assert/strict";
import test from "node:test";

const { buildProxyTargetURL } = await import(
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
