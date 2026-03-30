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
