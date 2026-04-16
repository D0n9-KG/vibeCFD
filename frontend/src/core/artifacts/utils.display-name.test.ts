import assert from "node:assert/strict";
import test from "node:test";

const { getArtifactDisplayName } = await import(
  new URL("../../components/workspace/artifacts/display.ts", import.meta.url).href,
);

void test("getArtifactDisplayName returns user-facing submarine labels for report artifacts", () => {
  const label = getArtifactDisplayName(
    "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json",
  );

  assert.equal(label, "科研补救交接 JSON");
  assert.doesNotMatch(label, /scientific-remediation-handoff\.json/i);
});

void test("getArtifactDisplayName returns user-facing submarine labels for study artifacts", () => {
  const label = getArtifactDisplayName(
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
  );

  assert.doesNotMatch(label, /study-manifest\.json/i);
  assert.match(label, /研究|清单|JSON/);
});

void test("getArtifactDisplayName returns user-facing submarine labels for remediation plan and provenance artifacts", () => {
  const remediationPlan = getArtifactDisplayName(
    "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-plan.json",
  );
  const provenanceManifest = getArtifactDisplayName(
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest.json",
  );

  assert.doesNotMatch(remediationPlan, /scientific-remediation-plan\.json/i);
  assert.match(remediationPlan, /科研|补救|计划|JSON/);
  assert.doesNotMatch(provenanceManifest, /provenance-manifest\.json/i);
  assert.match(provenanceManifest, /溯源|清单|JSON/);
});

void test("getArtifactDisplayName falls back to the basename for non-submarine artifacts", () => {
  const label = getArtifactDisplayName("/mnt/user-data/uploads/notes.txt");

  assert.equal(label, "notes.txt");
});
