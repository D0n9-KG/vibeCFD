import assert from "node:assert/strict";
import test from "node:test";

import {
  createPromptInputAttachment,
  preparePromptInputSubmitFiles,
} from "./prompt-input.files.ts";

test("createPromptInputAttachment keeps the original File for later upload", () => {
  const file = new File(["solid"], "suboff_solid.stl", {
    type: "application/sla",
  });
  const attachment = createPromptInputAttachment(file);

  assert.equal(typeof attachment.id, "string");
  assert.notEqual(attachment.id, "");
  assert.equal(attachment.type, "file");
  assert.match(attachment.url ?? "", /^blob:/);
  assert.equal(attachment.mediaType, "application/sla");
  assert.equal(attachment.filename, "suboff_solid.stl");
  assert.equal(attachment.file, file);
});

test("preparePromptInputSubmitFiles strips internal ids and preserves attachment urls", () => {
  const file = new File(["solid"], "suboff_solid.stl", {
    type: "application/sla",
  });
  const files = preparePromptInputSubmitFiles([
    {
      id: "file-1",
      type: "file",
      url: "blob:http://localhost:3000/example",
      mediaType: "application/sla",
      filename: "suboff_solid.stl",
      file,
    },
  ]);

  assert.deepEqual(files, [
    {
      type: "file",
      url: "blob:http://localhost:3000/example",
      mediaType: "application/sla",
      filename: "suboff_solid.stl",
      file,
    },
  ]);
});
