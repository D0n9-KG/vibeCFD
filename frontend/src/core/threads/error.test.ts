import assert from "node:assert/strict";
import test from "node:test";

const { getThreadErrorMessage } = await import(
  new URL("./error.ts", import.meta.url).href
);

void test("extracts nested provider error messages for user-facing feedback", () => {
  const message = getThreadErrorMessage(
    {
      error: {
        message: "Upstream authentication failed, please contact administrator",
      },
    },
    "Request failed.",
  );

  assert.equal(
    message,
    "Upstream authentication failed, please contact administrator",
  );
});

void test("falls back to the provided default message when the payload is empty", () => {
  assert.equal(getThreadErrorMessage(null, "Request failed."), "Request failed.");
});

void test("unwraps python-style API error wrappers down to the provider message", () => {
  const message = getThreadErrorMessage(
    "APIError('Upstream authentication failed, please contact administrator')",
    "Request failed.",
  );

  assert.equal(message, "Upstream authentication failed, please contact administrator");
});

void test("extracts provider detail from stringified 503 error payloads", () => {
  const message = getThreadErrorMessage(
    "InternalServerError(\"Error code: 503 - {'error': {'message': '所有供应商暂时不可用，请稍后重试 (cch_session_id: 019d3eef-c7b7-7ca6-ba5c-e53ea1345f07)', 'type': 'service_unavailable_error', 'code': 'service_unavailable_error'}}\")",
    "Request failed.",
  );

  assert.equal(
    message,
    "所有供应商暂时不可用，请稍后重试 (cch_session_id: 019d3eef-c7b7-7ca6-ba5c-e53ea1345f07)",
  );
});
