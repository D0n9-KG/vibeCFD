import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const listSource = await readFile(
  new URL("./artifact-file-list.tsx", import.meta.url),
  "utf8",
);
const detailSource = await readFile(
  new URL("./artifact-file-detail.tsx", import.meta.url),
  "utf8",
);

void test("artifact list and detail use the shared artifact display-name helper", () => {
  assert.match(listSource, /getArtifactDisplayName/);
  assert.match(detailSource, /getArtifactDisplayName/);
});
