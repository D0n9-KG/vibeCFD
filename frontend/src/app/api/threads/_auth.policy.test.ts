import assert from "node:assert/strict";
import test from "node:test";

import { shouldRequireThreadRouteSession } from "./_auth.policy.ts";

void test("development without auth configuration does not require a thread-route session", () => {
  assert.equal(
    shouldRequireThreadRouteSession({
      nodeEnv: "development",
      betterAuthSecret: undefined,
    }),
    false,
  );
});

void test("development requires a thread-route session once auth secret is configured", () => {
  assert.equal(
    shouldRequireThreadRouteSession({
      nodeEnv: "development",
      betterAuthSecret: "dev-secret",
    }),
    true,
  );
});

void test("production always requires a thread-route session", () => {
  assert.equal(
    shouldRequireThreadRouteSession({
      nodeEnv: "production",
      betterAuthSecret: undefined,
    }),
    true,
  );
});
