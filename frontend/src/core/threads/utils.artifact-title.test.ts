import assert from "node:assert/strict";
import test from "node:test";

import type { AgentThread } from "./types";

const { titleOfThread } = await import(new URL("./utils.ts", import.meta.url).href);

function makeThread(
  threadId: string,
  values: Partial<AgentThread["values"]> = {},
): AgentThread {
  return {
    thread_id: threadId,
    created_at: "",
    updated_at: "",
    status: "idle",
    metadata: {},
    values: {
      title: threadId,
      messages: [],
      artifacts: [],
      ...values,
    },
  } as AgentThread;
}

void test("titleOfThread derives a more specific fallback from submarine artifact paths when a generic upload title has no richer context", () => {
  const thread = makeThread("artifact-generic-title", {
    title: "STL File Upload",
    artifacts: [
      "/mnt/user-data/outputs/submarine/design-brief/suboff_solid/cfd-design-brief.json",
      "/mnt/user-data/outputs/submarine/reports/suboff_solid/final-report.json",
    ],
  });

  const title = titleOfThread(thread, "潜艇 CFD 会话");

  assert.notEqual(title, "STL 文件上传");
  assert.match(title, /suboff_solid/i);
});
