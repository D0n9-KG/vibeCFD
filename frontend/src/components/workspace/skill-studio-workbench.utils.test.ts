import assert from "node:assert/strict";
import test from "node:test";

const {
  buildSkillStudioReadinessSummary,
  formatSkillStudioStatus,
  groupSkillStudioArtifacts,
  resolveSkillStudioAssistantIdentity,
} = await import(
  new URL("./skill-studio-workbench.utils.ts", import.meta.url).href,
);

void test("groups skill-studio artifacts into package, validation, testing, and publish buckets", () => {
  const groups = groupSkillStudioArtifacts([
    "/mnt/user-data/outputs/submarine/skill-studio/demo/skill-draft.json",
    "/mnt/user-data/outputs/submarine/skill-studio/demo/SKILL.md",
    "/mnt/user-data/outputs/submarine/skill-studio/demo/agents/openai.yaml",
    "/mnt/user-data/outputs/submarine/skill-studio/demo/demo.skill",
    "/mnt/user-data/outputs/submarine/skill-studio/demo/validation-report.json",
    "/mnt/user-data/outputs/submarine/skill-studio/demo/test-matrix.json",
    "/mnt/user-data/outputs/submarine/skill-studio/demo/publish-readiness.md",
  ]);

  assert.deepEqual(
    groups.map((group) => group.id),
    ["package", "validation", "testing", "publish"],
  );
  assert.equal(groups[0]?.count, 4);
});

void test("builds a readiness summary from validation, testing, and publish state", () => {
  const readiness = buildSkillStudioReadinessSummary({
    errorCount: 0,
    warningCount: 1,
    validationStatus: "ready_for_review",
    testStatus: "ready_for_dry_run",
    publishStatus: "ready_for_review",
  });

  assert.equal(readiness.progress, 92);
  assert.equal(readiness.blockingCount, 0);
  assert.equal(readiness.warningCount, 1);
  assert.equal(readiness.validationLabel, "Ready for review");
  assert.equal(readiness.testLabel, "Ready for dry-run");
  assert.equal(readiness.publishLabel, "Ready for review");
});

void test("formats statuses into stable labels", () => {
  assert.equal(formatSkillStudioStatus("needs_revision"), "Needs revision");
  assert.equal(formatSkillStudioStatus("draft_only"), "Draft only");
  assert.equal(formatSkillStudioStatus("custom_status"), "Custom Status");
});

void test("resolves skill studio assistant identity with codex-first fallback", () => {
  assert.deepEqual(
    resolveSkillStudioAssistantIdentity({
      draftAssistantMode: null,
      draftAssistantLabel: null,
      packageAssistantMode: "claude-code-skill-creator",
      packageAssistantLabel: null,
      stateAssistantMode: null,
      stateAssistantLabel: null,
    }),
    {
      assistantMode: "claude-code-skill-creator",
      assistantLabel: "Claude Code · Skill Creator",
    },
  );

  assert.deepEqual(
    resolveSkillStudioAssistantIdentity({
      draftAssistantMode: null,
      draftAssistantLabel: null,
      packageAssistantMode: null,
      packageAssistantLabel: null,
      stateAssistantMode: null,
      stateAssistantLabel: null,
    }),
    {
      assistantMode: "codex-skill-creator",
      assistantLabel: "Codex · Skill Creator",
    },
  );
});
