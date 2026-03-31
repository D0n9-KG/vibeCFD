import assert from "node:assert/strict";
import test from "node:test";

import { prepareThreadUploadFiles } from "./thread-upload-files.ts";

test("prepareThreadUploadFiles prefers the original File object when available", async () => {
  const file = new File(["solid"], "suboff_solid.stl", {
    type: "application/sla",
  });

  let fetchCalls = 0;
  const files = await prepareThreadUploadFiles(
    [
      {
        type: "file",
        filename: file.name,
        mediaType: file.type,
        url: "blob:http://localhost:3000/example",
        file,
      },
    ],
    async () => {
      fetchCalls += 1;
      throw new Error("blob fetch should not be needed when File is present");
    },
  );

  assert.equal(fetchCalls, 0);
  assert.equal(files.length, 1);
  assert.equal(files[0], file);
});
