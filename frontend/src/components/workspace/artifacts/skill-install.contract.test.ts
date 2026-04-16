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

void test("artifact skill install entry points consult installed skill state", () => {
  assert.match(listSource, /useSkills\(/);
  assert.match(detailSource, /useSkills\(/);
  assert.match(listSource, /t\.common\.installed/);
  assert.match(detailSource, /t\.common\.installed/);
});
