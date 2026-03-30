import assert from "node:assert/strict";
import test from "node:test";

const {
  resolveBackendBaseURL,
  resolveLangGraphBaseURL,
} = await import(new URL("./runtime-base-url.ts", import.meta.url).href);

void test(
  "resolveBackendBaseURL falls back to the local gateway when the frontend dev server runs standalone on port 3000",
  () => {
    assert.equal(
      resolveBackendBaseURL({
        backendBaseURL: undefined,
        location: {
          origin: "http://localhost:3000",
          hostname: "localhost",
          port: "3000",
        },
      }),
      "http://localhost:8001",
    );
  },
);

void test(
  "resolveLangGraphBaseURL falls back to the local LangGraph server when the frontend dev server runs standalone on port 3000",
  () => {
    assert.equal(
      resolveLangGraphBaseURL({
        langGraphBaseURL: undefined,
        isMock: false,
        location: {
          origin: "http://localhost:3000",
          hostname: "localhost",
          port: "3000",
        },
      }),
      "http://localhost:2024",
    );
  },
);

void test("resolveLangGraphBaseURL keeps mock requests on the frontend mock API", () => {
  assert.equal(
    resolveLangGraphBaseURL({
      langGraphBaseURL: undefined,
      isMock: true,
      location: {
        origin: "http://localhost:3000",
        hostname: "localhost",
        port: "3000",
      },
    }),
    "http://localhost:3000/mock/api",
  );
});

void test("explicit environment URLs still win over the standalone dev fallback", () => {
  assert.equal(
    resolveBackendBaseURL({
      backendBaseURL: "https://gateway.example.test",
      location: {
        origin: "http://localhost:3000",
        hostname: "localhost",
        port: "3000",
      },
    }),
    "https://gateway.example.test",
  );

  assert.equal(
    resolveLangGraphBaseURL({
      langGraphBaseURL: "https://langgraph.example.test",
      isMock: false,
      location: {
        origin: "http://localhost:3000",
        hostname: "localhost",
        port: "3000",
      },
    }),
    "https://langgraph.example.test",
  );
});
