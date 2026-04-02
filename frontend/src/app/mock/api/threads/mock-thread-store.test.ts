import test from "node:test";
import assert from "node:assert/strict";

import { applyMockThreadAction } from "./mock-thread-store.ts";

test("applyMockThreadAction appends action messages and updates runtime summary", () => {
  const nextState = applyMockThreadAction(
    {
      values: {
        messages: [
          {
            content: [{ type: "text", text: "原始消息" }],
            type: "human",
            id: "msg-1",
          },
        ],
        submarine_runtime: {
          task_summary: "old",
          runtime_summary: "old",
        },
      },
      updated_at: "2026-04-02T00:00:00+08:00",
    },
    "✓ 确认通过",
    "2026-04-02T16:00:00+08:00",
  );

  const values = nextState.values as Record<string, unknown>;
  const messages = values.messages as Array<Record<string, unknown>>;
  const runtime = values.submarine_runtime as Record<string, unknown>;

  assert.equal(messages.length, 3);
  assert.equal(nextState.updated_at, "2026-04-02T16:00:00+08:00");
  assert.match(String(runtime.task_summary), /审批通过/);
  assert.match(String(runtime.runtime_summary), /Mock researcher approval/);
});
