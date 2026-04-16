import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const chatBoxSource = await readFile(
  new URL("./chat-box.tsx", import.meta.url),
  "utf8",
);

void test("artifact list shell keeps a dedicated vertical scroll region instead of vertically centering long file lists", () => {
  assert.match(chatBoxSource, /<main className="min-h-0 grow overflow-y-auto">/);
  assert.doesNotMatch(
    chatBoxSource,
    /flex size-full max-w-\(--container-width-sm\) flex-col justify-center p-4 pt-8/,
  );
});
