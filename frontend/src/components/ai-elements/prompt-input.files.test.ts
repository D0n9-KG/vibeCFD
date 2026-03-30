import assert from "node:assert/strict";
import test from "node:test";

import { preparePromptInputSubmitFiles } from "./prompt-input.files.ts";

test("preparePromptInputSubmitFiles strips internal ids and preserves attachment urls", () => {
  const files = preparePromptInputSubmitFiles([
    {
      id: "file-1",
      type: "file",
      url: "blob:http://localhost:3000/example",
      mediaType: "application/sla",
      filename: "suboff_solid.stl",
    },
  ]);

  assert.deepEqual(files, [
    {
      type: "file",
      url: "blob:http://localhost:3000/example",
      mediaType: "application/sla",
      filename: "suboff_solid.stl",
    },
  ]);
});
