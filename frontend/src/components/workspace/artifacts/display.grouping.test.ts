import assert from "node:assert/strict";
import test from "node:test";

const { buildArtifactListSections } = await import(
  new URL("./display.ts", import.meta.url).href
);

void test("buildArtifactListSections groups submarine artifacts by delivery priority", () => {
  const sections = buildArtifactListSections([
    "/mnt/user-data/outputs/submarine/solver-dispatch/suboff_solid/openfoam-run.log",
    "/mnt/user-data/outputs/submarine/reports/suboff_solid/final-report.md",
    "/mnt/user-data/outputs/submarine/design-brief/suboff_solid/cfd-design-brief.json",
    "/mnt/user-data/outputs/submarine/solver-dispatch/suboff_solid/solver-results.json",
    "/mnt/user-data/outputs/submarine/reports/suboff_solid/delivery-readiness.json",
  ]);

  assert.deepEqual(
    sections.map((section) => section.id),
    ["delivery", "execution", "preparation"],
  );
  assert.equal(sections[0]?.files[0], "/mnt/user-data/outputs/submarine/reports/suboff_solid/final-report.md");
  assert.equal(
    sections[0]?.files[1],
    "/mnt/user-data/outputs/submarine/reports/suboff_solid/delivery-readiness.json",
  );
  assert.equal(
    sections[1]?.files[0],
    "/mnt/user-data/outputs/submarine/solver-dispatch/suboff_solid/solver-results.json",
  );
});

void test("buildArtifactListSections groups skill studio artifacts into draft, validation, and publish stages", () => {
  const sections = buildArtifactListSections([
    "/mnt/user-data/outputs/submarine/skill-studio/acceptance/skill-package.json",
    "/mnt/user-data/outputs/submarine/skill-studio/acceptance/skill-draft.json",
    "/mnt/user-data/outputs/submarine/skill-studio/acceptance/validation-report.json",
    "/mnt/user-data/outputs/submarine/skill-studio/acceptance/publish-readiness.json",
  ]);

  assert.deepEqual(
    sections.map((section) => section.id),
    ["skill-draft", "skill-validation", "skill-publish"],
  );
  assert.equal(
    sections[0]?.files[0],
    "/mnt/user-data/outputs/submarine/skill-studio/acceptance/skill-draft.json",
  );
});
