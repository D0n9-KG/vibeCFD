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

void test("artifacts context exposes a stable open handler so thread routes do not immediately close the file drawer after user clicks", () => {
  assert.match(
    artifactsContextSource,
    /const \w+ = useCallback\(\s*\(isOpen: boolean\) => \{/,
  );
  assert.match(
    artifactsContextSource,
    /setOpen:\s*\w+,/,
  );
});
