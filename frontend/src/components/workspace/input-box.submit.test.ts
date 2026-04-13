import assert from "node:assert/strict";
import test from "node:test";

const { resolveInputBoxSubmitAction, resolvePromptInputSubmission } = await import(
  new URL("./input-box.submit.ts", import.meta.url).href
);

void test("resolvePromptInputSubmission preserves files already present on the message", () => {
  const file = new File(["solid"], "suboff_solid.stl", {
    type: "application/sla",
  });

  const message = {
    text: "请开始预检。",
    files: [
      {
        type: "file" as const,
        filename: "suboff_solid.stl",
        mediaType: "application/sla",
        url: "blob:http://localhost:3000/existing",
        file,
      },
    ],
  };

  const resolved = resolvePromptInputSubmission({
    message,
    attachments: [],
  });

  assert.equal(resolved, message);
});

void test("resolvePromptInputSubmission falls back to controller attachments when message files are empty", () => {
  const file = new File(["solid"], "suboff_solid.stl", {
    type: "application/sla",
  });

  const resolved = resolvePromptInputSubmission({
    message: {
      text: "请开始预检。",
      files: [],
    },
    attachments: [
      {
        id: "attachment-1",
        type: "file",
        filename: "suboff_solid.stl",
        mediaType: "application/sla",
        url: "blob:http://localhost:3000/from-controller",
        file,
      },
    ],
  });

  assert.deepEqual(resolved.files, [
    {
      type: "file",
      filename: "suboff_solid.stl",
      mediaType: "application/sla",
      url: "blob:http://localhost:3000/from-controller",
      file,
    },
  ]);
});

void test("resolveInputBoxSubmitAction preserves a typed draft while the assistant is still streaming", () => {
  const decision = resolveInputBoxSubmitAction({
    status: "streaming",
    message: {
      text: "确认采用参考长度 4.356 m 和参考面积 0.370988 m^2",
      files: [],
    },
    attachments: [],
  });

  assert.equal(decision.kind, "preserve_draft_while_streaming");
  assert.equal(
    decision.message.text,
    "确认采用参考长度 4.356 m 和参考面积 0.370988 m^2",
  );
});

void test("resolveInputBoxSubmitAction allows stop semantics only when the streaming draft is empty", () => {
  const decision = resolveInputBoxSubmitAction({
    status: "streaming",
    message: {
      text: "   ",
      files: [],
    },
    attachments: [],
  });

  assert.equal(decision.kind, "stop_stream");
});
