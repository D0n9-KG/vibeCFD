import assert from "node:assert/strict";
import test from "node:test";

import type { AgentThread } from "./types";

const {
  deriveThreadsAfterDeletion,
  pathAfterThreadDeletion,
  pathOfThreadByState,
  titleOfThread,
  rememberWorkbenchKindForThread,
  forgetWorkbenchKindForThread,
  workbenchKindOfThread,
} = await import(new URL("./utils.ts", import.meta.url).href);

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

void test("pathOfThreadByState routes submarine runtime threads to the submarine workbench", () => {
  const thread = makeThread("cfd-thread", {
    submarine_runtime: { current_stage: "solver-dispatch" },
  });

  assert.equal(pathOfThreadByState(thread), "/workspace/submarine/cfd-thread");
});

void test("pathOfThreadByState routes skill studio threads to the skill workbench", () => {
  const thread = makeThread("skill-thread", {
    submarine_skill_studio: { skill_name: "mesh-doctor" },
  });

  assert.equal(
    pathOfThreadByState(thread),
    "/workspace/skill-studio/skill-thread",
  );
});

void test("pathOfThreadByState respects persisted workbench kind before runtime state arrives", () => {
  const submarineThread = makeThread("tagged-submarine", {
    workspace_kind: "submarine",
  });
  const skillThread = makeThread("tagged-skill", {
    workspace_kind: "skill-studio",
  });

  assert.equal(workbenchKindOfThread(submarineThread), "submarine");
  assert.equal(
    pathOfThreadByState(submarineThread),
    "/workspace/submarine/tagged-submarine",
  );
  assert.equal(workbenchKindOfThread(skillThread), "skill-studio");
  assert.equal(
    pathOfThreadByState(skillThread),
    "/workspace/skill-studio/tagged-skill",
  );
});

void test("workbenchKindOfThread uses remembered workbench routing while thread search state is still empty", () => {
  const thread = makeThread("remembered-submarine", {
    title: "Untitled",
    messages: [],
    artifacts: [],
  });

  rememberWorkbenchKindForThread("remembered-submarine", "submarine");

  assert.equal(workbenchKindOfThread(thread), "submarine");
  assert.equal(
    pathOfThreadByState(thread),
    "/workspace/submarine/remembered-submarine",
  );

  forgetWorkbenchKindForThread("remembered-submarine");
});

void test("deriveThreadsAfterDeletion clears remembered workbench routing for deleted threads", () => {
  const deletedThread = makeThread("deleted-submarine", {
    title: "Deleted run",
    messages: [],
    artifacts: [],
  });
  const survivingThread = makeThread("surviving-chat");

  rememberWorkbenchKindForThread("deleted-submarine", "submarine");

  assert.equal(workbenchKindOfThread(deletedThread), "submarine");
  assert.deepEqual(
    deriveThreadsAfterDeletion([deletedThread, survivingThread], "deleted-submarine"),
    [survivingThread],
  );
  assert.equal(workbenchKindOfThread(deletedThread), "chat");
});

void test("deriveThreadsAfterDeletion still clears remembered workbench routing when thread cache is empty", () => {
  const deletedThread = makeThread("deleted-without-cache", {
    title: "Deleted run",
    messages: [],
    artifacts: [],
  });

  rememberWorkbenchKindForThread("deleted-without-cache", "submarine");

  assert.equal(workbenchKindOfThread(deletedThread), "submarine");
  assert.equal(
    deriveThreadsAfterDeletion(undefined, "deleted-without-cache"),
    undefined,
  );
  assert.equal(workbenchKindOfThread(deletedThread), "chat");
});

void test("pathOfThreadByState uses artifact prefixes when runtime state is absent", () => {
  const cfdThread = makeThread("artifact-cfd", {
    artifacts: ["runs/submarine/solver-results.json"],
  });
  const skillThread = makeThread("artifact-skill", {
    artifacts: ["runs/submarine/skill-studio/report.json"],
  });
  const chatThread = makeThread("artifact-chat");

  assert.equal(
    pathOfThreadByState(cfdThread),
    "/workspace/submarine/artifact-cfd",
  );
  assert.equal(
    pathOfThreadByState(skillThread),
    "/workspace/skill-studio/artifact-skill",
  );
  assert.equal(
    pathOfThreadByState(chatThread),
    "/workspace/chats/artifact-chat",
  );
});

void test("pathAfterThreadDeletion routes to the next available thread", () => {
  const threads = [
    makeThread("current-cfd", {
      submarine_runtime: { current_stage: "task-intelligence" },
    }),
    makeThread("next-skill", {
      submarine_skill_studio: { skill_name: "mesh-doctor" },
    }),
  ];

  assert.equal(
    pathAfterThreadDeletion(threads, "current-cfd"),
    "/workspace/skill-studio/next-skill",
  );
});

void test("pathAfterThreadDeletion falls back to a matching workbench when the deleted thread was the last one", () => {
  assert.equal(
    pathAfterThreadDeletion(
      [
        makeThread("only-cfd", {
          submarine_runtime: { current_stage: "done" },
        }),
      ],
      "only-cfd",
    ),
    "/workspace/submarine/new",
  );
  assert.equal(
    pathAfterThreadDeletion(
      [
        makeThread("only-skill", {
          submarine_skill_studio: { skill_name: "mesh-doctor" },
        }),
      ],
      "only-skill",
    ),
    "/workspace/skill-studio",
  );
  assert.equal(
    pathAfterThreadDeletion([makeThread("only-chat")], "only-chat"),
    "/workspace/chats/new",
  );
});

void test("titleOfThread localizes known workspace-facing English thread titles", () => {
  const draftThread = makeThread("skill-draft", {
    title: "Submarine Result Acceptance Draft",
  });
  const overviewThread = makeThread("skill-overview", {
    title: "DeerFlow Skill 能力说明",
  });

  assert.equal(titleOfThread(draftThread), "潜艇结果验收草稿");
  assert.equal(titleOfThread(overviewThread), "DeerFlow 技能能力说明");
});

void test("titleOfThread strips uploaded file scaffolding from persisted thread titles", () => {
  const thread = makeThread("uploaded-title", {
    title: [
      "<uploaded_files>",
      "The following files were uploaded in this message:",
      "",
      "- suboff_solid.stl (1677721)",
      "  Path: /mnt/user-data/uploads/suboff_solid.stl",
      "</uploaded_files>",
      "",
      "Geometry preflight for SUBOFF STL",
    ].join("\n"),
  });

  const title = titleOfThread(thread);

  assert.match(title, /SUBOFF STL/);
  assert.doesNotMatch(title, /<uploaded_files>|Path:/);
});

void test("titleOfThread falls back to a friendly upload summary when a persisted title only contains file metadata", () => {
  const thread = makeThread("upload-only-title", {
    title: [
      "<uploaded_files>",
      "The following files were uploaded in this message:",
      "",
      "- suboff_solid.stl (1677721)",
      "  Path: /mnt/user-data/uploads/suboff_solid.stl",
      "</uploaded_files>",
    ].join("\n"),
  });

  const title = titleOfThread(thread);

  assert.match(title, /suboff_solid\.stl/);
  assert.doesNotMatch(title, /<uploaded_files>|Path:/);
});

void test("titleOfThread falls back to the untitled label for truncated upload scaffold titles", () => {
  const thread = makeThread("truncated-upload-title", {
    title: "<uploaded_files> The following files were uploaded.",
  });

  assert.equal(titleOfThread(thread, "Untitled Thread"), "Untitled Thread");
});
