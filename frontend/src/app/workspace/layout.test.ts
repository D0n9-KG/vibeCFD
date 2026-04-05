import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const workspaceLayoutSource = await readFile(
  new URL("./layout.tsx", import.meta.url),
  "utf8",
);

void test("workspace layout defaults the desktop sidebar to open so hydration does not shove the main surface rightward", () => {
  assert.match(
    workspaceLayoutSource,
    /const \[open, setOpen\] = useState\(true\); \/\/ SSR default: open/,
  );
});
