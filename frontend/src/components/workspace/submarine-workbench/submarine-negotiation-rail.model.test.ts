import assert from "node:assert/strict";
import test from "node:test";

const { getSubmarineNegotiationAttentionKey } = await import(
  new URL("./submarine-negotiation-rail.model.ts", import.meta.url).href,
);

void test("builds an attention key when the submarine runtime is explicitly blocked on user confirmation", () => {
  const key = getSubmarineNegotiationAttentionKey({
    current_stage: "task-intelligence",
    review_status: "needs_user_confirmation",
    next_recommended_stage: "user-confirmation",
  });

  assert.equal(key, "task-intelligence::needs_user_confirmation::user-confirmation");
});

void test("returns null when the submarine runtime is not asking for user confirmation", () => {
  const key = getSubmarineNegotiationAttentionKey({
    current_stage: "solver-dispatch",
    review_status: "ready",
    next_recommended_stage: "solver-dispatch",
  });

  assert.equal(key, null);
});

void test("returns null when stale confirmation flags point at an earlier stage but the report path is already final-reporting output", () => {
  const key = getSubmarineNegotiationAttentionKey({
    current_stage: "geometry-preflight",
    review_status: "needs_user_confirmation",
    next_recommended_stage: "user-confirmation",
    report_virtual_path: "/mnt/user-data/outputs/submarine/reports/suboff_solid/final-report.md",
  });

  assert.equal(key, null);
});
