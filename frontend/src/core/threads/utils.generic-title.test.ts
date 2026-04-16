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

void test("titleOfThread falls back away from generic STL upload titles when message context is available", () => {
  const thread = makeThread("generic-upload-title", {
    title: "STL File Upload",
    messages: [
      {
        type: "human",
        id: "human-1",
        content: [
          {
            type: "text",
            text: [
              "<uploaded_files>",
              "The following files were uploaded in this message:",
              "",
              "- suboff_solid.stl (1638084)",
              "  Path: /mnt/user-data/uploads/suboff_solid.stl",
              "</uploaded_files>",
              "",
              "Please prepare the SUBOFF STL geometry preflight and baseline CFD brief.",
            ].join("\n"),
          },
        ],
      },
    ],
  });

  const title = titleOfThread(thread);

  assert.notEqual(title, "STL File Upload");
  assert.doesNotMatch(title, /STL File Upload|Path:|\/mnt\/user-data/i);
  assert.match(title, /SUBOFF|suboff_solid\.stl/i);
});
