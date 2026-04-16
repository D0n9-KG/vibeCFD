import assert from "node:assert/strict";
import test from "node:test";

const { localizeWorkspaceDisplayText } = await import(
  new URL("./workspace-display.ts", import.meta.url).href,
);

void test("localizeWorkspaceDisplayText rewrites skill studio file bundle references inside assistant summaries", () => {
  const localized = localizeWorkspaceDisplayText(
    "skill-lifecycle.json / dry-run-evidence.json / skill-package.json / test-matrix.json / .md / publish-readiness.json / .md",
  );

  assert.doesNotMatch(localized, /skill-lifecycle\.json/i);
  assert.doesNotMatch(localized, /dry-run-evidence\.json/i);
  assert.doesNotMatch(localized, /skill-package\.json/i);
  assert.doesNotMatch(localized, /test-matrix\.json/i);
  assert.doesNotMatch(localized, /publish-readiness\.json/i);
});
