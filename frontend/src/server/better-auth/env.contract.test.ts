import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const envSource = await readFile(new URL("../../env.js", import.meta.url), "utf8");
const envExampleSource = await readFile(
  new URL("../../../.env.example", import.meta.url),
  "utf8",
);
const lintWorkflowSource = await readFile(
  new URL("../../../../.github/workflows/lint-check.yml", import.meta.url),
  "utf8",
);

void test(
  "frontend env validation accepts the Better Auth URL alias and requires a base url in production",
  () => {
    assert.match(
      envSource,
      /process\.env\.BETTER_AUTH_BASE_URL\?\.trim\(\)\s*\|\|\s*process\.env\.BETTER_AUTH_URL\?\.trim\(\)/,
    );
    assert.match(
      envSource,
      /BETTER_AUTH_BASE_URL:\s*process\.env\.NODE_ENV === "production"\s*\?\s*z\.string\(\)\.url\(\)\s*:\s*z\.string\(\)\.url\(\)\.optional\(\)/,
    );
  },
);

void test("frontend env example documents the production Better Auth requirements", () => {
  assert.match(envExampleSource, /^BETTER_AUTH_SECRET=/m);
  assert.match(envExampleSource, /^BETTER_AUTH_BASE_URL=/m);
});

void test("frontend CI exercises the Better Auth env contract regression test", () => {
  assert.match(
    lintWorkflowSource,
    /node --experimental-strip-types --test 'src\/server\/better-auth\/env\.contract\.test\.ts'/,
  );
});
