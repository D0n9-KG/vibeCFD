import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const moduleDir = path.dirname(fileURLToPath(import.meta.url));

void test("negotiation rail stays stage-agnostic with composable slots", async () => {
  const source = await readFile(
    path.join(moduleDir, "negotiation-rail.tsx"),
    "utf-8",
  );

  assert.match(source, /export type NegotiationRailProps = \{/);
  assert.match(source, /\btitle:\s*ReactNode\b/);
  assert.match(source, /\bquestion:\s*ReactNode\b/);
  assert.match(source, /\bactions:\s*ReactNode\b/);
  assert.match(source, /\bbody:\s*ReactNode\b/);
  assert.match(source, /\bfooter\?:\s*ReactNode\b/);
  assert.match(source, /data-negotiation-slot="title"/);
  assert.match(source, /data-negotiation-slot="question"/);
  assert.match(source, /data-negotiation-slot="actions"/);
  assert.match(source, /data-negotiation-slot="body"/);
  assert.doesNotMatch(source, /\bpendingApprovals\b/);
  assert.doesNotMatch(source, /\binterruptionVisible\b/);
  assert.doesNotMatch(source, /\bnarrative\b/);
  assert.doesNotMatch(source, /\bonPause\b/);
  assert.doesNotMatch(source, /\bonResolve\b/);
  assert.doesNotMatch(source, /\bPause\b/);
  assert.doesNotMatch(source, /\bResolve\b/);
});
