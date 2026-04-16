import assert from "node:assert/strict";
import test from "node:test";

const { collectThreadArtifacts } = await import(
  new URL("./chat-box.artifacts.ts", import.meta.url).href
);

void test("collectThreadArtifacts merges thread, runtime, and studio artifacts in a stable order", () => {
  const artifacts = collectThreadArtifacts({
    artifacts: [
      "/mnt/user-data/outputs/submarine/reports/final-report.md",
      "/mnt/user-data/outputs/submarine/reports/final-report.json",
    ],
    submarine_runtime: {
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/reports/final-report.json",
        "/mnt/user-data/outputs/submarine/solver-dispatch/solver-results.json",
      ],
    },
    submarine_skill_studio: {
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/skill-studio/skill-draft.json",
      ],
    },
  });

  assert.deepEqual(artifacts, [
    "/mnt/user-data/outputs/submarine/reports/final-report.md",
    "/mnt/user-data/outputs/submarine/reports/final-report.json",
    "/mnt/user-data/outputs/submarine/solver-dispatch/solver-results.json",
    "/mnt/user-data/outputs/submarine/skill-studio/skill-draft.json",
  ]);
});

void test("collectThreadArtifacts ignores invalid artifact entries and missing containers", () => {
  const artifacts = collectThreadArtifacts({
    artifacts: [
      "/mnt/user-data/outputs/submarine/reports/final-report.md",
      42,
      null,
    ],
    submarine_runtime: {
      artifact_virtual_paths: [
        null,
        "/mnt/user-data/outputs/submarine/solver-dispatch/solver-results.json",
      ],
    },
    submarine_skill_studio: null,
  });

  assert.deepEqual(artifacts, [
    "/mnt/user-data/outputs/submarine/reports/final-report.md",
    "/mnt/user-data/outputs/submarine/solver-dispatch/solver-results.json",
  ]);
});
