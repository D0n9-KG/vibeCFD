import assert from "node:assert/strict";
import test from "node:test";

const utils = await import(new URL("./utils.ts", import.meta.url).href);

void test("buildProgressPreviewFromMessage strips uploaded file scaffolding when user text is present", () => {
  const message = {
    type: "human",
    content: [
      "<uploaded_files>",
      "The following files were uploaded in this message:",
      "",
      "- suboff_solid.stl (1677721)",
      "  Path: /mnt/user-data/uploads/suboff_solid.stl",
      "</uploaded_files>",
      "",
      "请先做几何预检并给出推荐工况。",
    ].join("\n"),
  };

  assert.equal(
    utils.buildProgressPreviewFromMessage(message),
    "请先做几何预检并给出推荐工况。",
  );
});

void test("buildProgressPreviewFromMessage falls back to a friendly upload summary when only files were attached", () => {
  const message = {
    type: "human",
    content: [
      "<uploaded_files>",
      "The following files were uploaded in this message:",
      "",
      "- suboff_solid.stl (1677721)",
      "  Path: /mnt/user-data/uploads/suboff_solid.stl",
      "</uploaded_files>",
    ].join("\n"),
  };

  assert.match(
    utils.buildProgressPreviewFromMessage(message),
    /suboff_solid\.stl/,
  );
  assert.doesNotMatch(
    utils.buildProgressPreviewFromMessage(message),
    /<uploaded_files>|Path:/,
  );
});
