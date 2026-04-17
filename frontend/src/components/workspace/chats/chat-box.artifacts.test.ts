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

void test("collectThreadArtifacts includes official case seeds and assembled files before generated outputs", () => {
  const artifacts = collectThreadArtifacts({
    artifacts: [],
    submarine_runtime: {
      official_case_seed_virtual_paths: [
        "/mnt/user-data/uploads/cavity/system/blockMeshDict",
      ],
      assembled_case_virtual_paths: [
        "/mnt/user-data/workspace/official-openfoam/cavity/openfoam-case/system/blockMeshDict",
        "/mnt/user-data/workspace/official-openfoam/cavity/openfoam-case/Allrun",
      ],
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/solver-dispatch/cavity/openfoam-request.json",
        "/mnt/user-data/outputs/submarine/reports/cavity/final-report.md",
      ],
    },
    submarine_skill_studio: null,
  });

  assert.deepEqual(artifacts, [
    "/mnt/user-data/uploads/cavity/system/blockMeshDict",
    "/mnt/user-data/workspace/official-openfoam/cavity/openfoam-case/system/blockMeshDict",
    "/mnt/user-data/workspace/official-openfoam/cavity/openfoam-case/Allrun",
    "/mnt/user-data/outputs/submarine/solver-dispatch/cavity/openfoam-request.json",
    "/mnt/user-data/outputs/submarine/reports/cavity/final-report.md",
  ]);
});
