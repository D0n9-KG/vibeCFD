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

void test("titleOfThread uses submarine runtime task context when a generic upload title has no message history", () => {
  const thread = makeThread("runtime-generic-title", {
    title: "STL File Upload",
    submarine_runtime: {
      task_description:
        "DARPA SUBOFF 裸艇 5 m/s 阻力基线 CFD：已完成几何预检、参考尺度确认，当前继续整理结果与验证建议。",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
    },
  });

  const title = titleOfThread(thread, "潜艇 CFD 会话");

  assert.notEqual(title, "STL 文件上传");
  assert.match(title, /DARPA SUBOFF|suboff_solid\.stl/);
});

void test("titleOfThread prefers submarine runtime task context over upload-only message scaffolding for generic upload titles", () => {
  const thread = makeThread("runtime-generic-title-with-upload-message", {
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
            ].join("\n"),
          },
        ],
      },
    ],
    submarine_runtime: {
      task_description:
        "DARPA SUBOFF 裸艇 5 m/s 阻力基线 CFD：已完成几何预检、参考尺度确认，当前继续整理结果与验证建议。",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
    },
  });

  const title = titleOfThread(thread, "潜艇 CFD 会话");

  assert.doesNotMatch(title, /STL 文件上传|已上传 suboff_solid\.stl/i);
  assert.match(title, /DARPA SUBOFF/);
});
