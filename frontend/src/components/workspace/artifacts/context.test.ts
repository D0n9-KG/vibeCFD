import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const artifactsContextSource = await readFile(
  new URL("./context.tsx", import.meta.url),
  "utf8",
);

void test("artifacts context keeps auto-open disabled on first paint to avoid thread page layout shifts", () => {
  assert.match(
    artifactsContextSource,
    /const \[autoOpen, setAutoOpen\] = useState\(false\);/,
  );
});
