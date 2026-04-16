import assert from "node:assert/strict";
import test from "node:test";

const { localizeWorkspaceDisplayText } = await import(
  new URL("./workspace-display.ts", import.meta.url).href,
);

void test("localizeWorkspaceDisplayText rewrites raw submarine artifact filenames that still appear in historical message copy", () => {
  const localized = localizeWorkspaceDisplayText(
    "dispatch-summary.md / solver-results.md / final-report.md / final-report.html / final-report.json / scientific-remediation-plan.json / scientific-remediation-handoff.json / provenance-manifest.json",
  );

  assert.doesNotMatch(
    localized,
    /dispatch-summary\.md|solver-results\.md|final-report\.md|final-report\.html|final-report\.json|scientific-remediation-plan\.json|scientific-remediation-handoff\.json|provenance-manifest\.json/i,
  );
  assert.doesNotMatch(localized, /\?/);
  assert.match(localized, /求解派发摘要/);
  assert.match(localized, /结果摘要/);
  assert.match(localized, /最终报告 JSON/);
  assert.match(localized, /科研补救计划 JSON/);
  assert.match(localized, /科研补救交接 JSON/);
  assert.match(localized, /溯源清单 JSON/);
});
