import assert from "node:assert/strict";
import test from "node:test";

const { getArtifactDisplayName } = await import(
  new URL("../../components/workspace/artifacts/display.ts", import.meta.url).href,
);

void test("getArtifactDisplayName returns user-facing skill studio labels for lifecycle artifacts", () => {
  const lifecycle = getArtifactDisplayName(
    "/mnt/user-data/outputs/submarine/skill-studio/demo/skill-lifecycle.json",
  );
  const dryRun = getArtifactDisplayName(
    "/mnt/user-data/outputs/submarine/skill-studio/demo/dry-run-evidence.json",
  );
  const publishReadiness = getArtifactDisplayName(
    "/mnt/user-data/outputs/submarine/skill-studio/demo/publish-readiness.json",
  );

  assert.doesNotMatch(lifecycle, /skill-lifecycle\.json/i);
  assert.doesNotMatch(dryRun, /dry-run-evidence\.json/i);
  assert.doesNotMatch(publishReadiness, /publish-readiness\.json/i);
});

void test("getArtifactDisplayName returns user-facing skill studio labels for package artifacts", () => {
  const testMatrix = getArtifactDisplayName(
    "/mnt/user-data/outputs/submarine/skill-studio/demo/test-matrix.md",
  );
  const packageJson = getArtifactDisplayName(
    "/mnt/user-data/outputs/submarine/skill-studio/demo/skill-package.json",
  );
  const archive = getArtifactDisplayName(
    "/mnt/user-data/outputs/submarine/skill-studio/demo/demo.skill",
  );
  const uiMetadata = getArtifactDisplayName(
    "/mnt/user-data/outputs/submarine/skill-studio/demo/agents/openai.yaml",
  );

  assert.doesNotMatch(testMatrix, /test-matrix\.md/i);
  assert.doesNotMatch(packageJson, /skill-package\.json/i);
  assert.doesNotMatch(archive, /demo\.skill/i);
  assert.doesNotMatch(uiMetadata, /openai\.yaml/i);
});
