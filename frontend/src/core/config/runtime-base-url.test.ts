import assert from "node:assert/strict";
import test from "node:test";

const {
  resolveBackendBaseURL,
  resolveLangGraphBaseURL,
} = await import(new URL("./runtime-base-url.ts", import.meta.url).href);

void test(
  "resolveBackendBaseURL keeps browser requests on the frontend origin",
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
      "",
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

void test(
  "resolveLangGraphBaseURL prefers the frontend mock API over an explicit LangGraph URL when mock mode is enabled",
  () => {
    assert.equal(
      resolveLangGraphBaseURL({
        langGraphBaseURL: "https://langgraph.example.test",
        isMock: true,
        location: {
          origin: "http://localhost:3000",
          hostname: "localhost",
          port: "3000",
        },
      }),
      "http://localhost:3000/mock/api",
    );
  },
);

void test(
  "resolveBackendBaseURL still prefers the frontend origin even when a browser runtime receives an explicit backend URL",
  () => {
    assert.equal(
      resolveBackendBaseURL({
        backendBaseURL: "https://gateway.example.test",
        location: {
          origin: "http://localhost:3000",
          hostname: "localhost",
          port: "3000",
        },
      }),
      "",
    );
  },
);

void test("explicit LangGraph environment URLs still win over the standalone dev fallback", () => {
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

void test("resolveBackendBaseURL uses the configured backend URL outside the browser", () => {
  assert.equal(
    resolveBackendBaseURL({
      backendBaseURL: "https://gateway.example.test",
    }),
    "https://gateway.example.test",
  );
});

void test("resolveBackendBaseURL trims explicit server-side backend URLs", () => {
  assert.equal(
    resolveBackendBaseURL({
      backendBaseURL: "  https://gateway.example.test/api  ",
    }),
    "https://gateway.example.test/api",
  );
});

void test("explicit LangGraph environment URLs are trimmed before being returned", () => {
  assert.equal(
    resolveLangGraphBaseURL({
      langGraphBaseURL: "  https://langgraph.example.test/api/langgraph  ",
      isMock: false,
      location: {
        origin: "http://localhost:3000",
        hostname: "localhost",
        port: "3000",
      },
    }),
    "https://langgraph.example.test/api/langgraph",
  );
});

void test(
  "whitespace-only backend URLs fall back to the frontend origin in the browser and localhost server-side",
  () => {
    assert.equal(
      resolveBackendBaseURL({
        backendBaseURL: "   ",
        location: {
          origin: "http://localhost:3000",
          hostname: "localhost",
          port: "3000",
        },
      }),
      "",
    );

    assert.equal(
      resolveBackendBaseURL({
        backendBaseURL: "   ",
      }),
      "http://localhost:8001",
    );
  },
);

void test("whitespace-only LangGraph URLs fall back to standalone local defaults", () => {
  assert.equal(
    resolveLangGraphBaseURL({
      langGraphBaseURL: "   ",
      isMock: false,
      location: {
        origin: "http://localhost:3000",
        hostname: "localhost",
        port: "3000",
      },
    }),
    "http://localhost:2024",
  );
});
