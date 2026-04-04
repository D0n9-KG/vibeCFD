import assert from "node:assert/strict";
import test from "node:test";

const { buildSkillStudioEntries } = await import(
  new URL("./skill-studio-dashboard.utils.ts", import.meta.url).href,
);

void test("extracts skill-studio entries from thread search results", () => {
  const entries = buildSkillStudioEntries([
    {
      thread_id: "submarine-skill-studio-demo",
      updated_at: "2026-03-27T00:00:00+00:00",
      values: {
        title: "潜艇 Skill Studio 演示",
        artifacts: [
          "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/skill-draft.json",
          "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/validation-report.md",
        ],
        submarine_skill_studio: {
          skill_name: "submarine-result-acceptance",
          assistant_mode: "claude-code-skill-creator",
          assistant_label: "Claude Code 技能创建器",
          validation_status: "ready_for_review",
          test_status: "ready_for_dry_run",
          publish_status: "ready_for_review",
          error_count: 0,
          warning_count: 1,
          report_virtual_path:
            "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/validation-report.md",
          artifact_virtual_paths: [
            "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/skill-draft.json",
            "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/validation-report.md",
          ],
        },
      },
    },
    {
      thread_id: "submarine-cfd-demo",
      updated_at: "2026-03-26T00:00:00+00:00",
      values: {
        title: "潜艇 CFD 最小闭环演示",
        artifacts: [
          "/mnt/user-data/outputs/submarine/reports/live-forces-suboff/final-report.md",
        ],
      },
    },
  ]);

  assert.equal(entries.length, 1);
  assert.equal(entries[0]?.threadId, "submarine-skill-studio-demo");
  assert.equal(entries[0]?.title, "潜艇技能工作台演示");
  assert.equal(entries[0]?.skillName, "潜艇结果验收");
  assert.equal(entries[0]?.assistantMode, "claude-code-skill-creator");
  assert.equal(entries[0]?.assistantLabel, "Claude Code 技能创建器");
  assert.equal(entries[0]?.validationStatus, "ready_for_review");
  assert.equal(entries[0]?.testStatus, "ready_for_dry_run");
  assert.equal(entries[0]?.publishStatus, "ready_for_review");
  assert.equal(entries[0]?.artifactCount, 2);
});

void test("normalizes legacy persisted assistant labels", () => {
  const entries = buildSkillStudioEntries([
    {
      thread_id: "legacy-label",
      updated_at: "2026-03-27T00:00:00+00:00",
      values: {
        title: "旧标签线程",
        artifacts: [
          "/mnt/user-data/outputs/submarine/skill-studio/legacy-label/skill-draft.json",
        ],
        submarine_skill_studio: {
          assistant_mode: "codex-skill-creator",
          assistant_label: "Codex · Skill Creator",
        },
      },
    },
  ]);

  assert.equal(entries[0]?.assistantLabel, "Codex 技能创建器");
});

void test("falls back to skill-studio artifacts even when structured state is missing", () => {
  const entries = buildSkillStudioEntries([
    {
      thread_id: "draft-only",
      updated_at: "2026-03-27T01:00:00+00:00",
      values: {
        title: "Draft Only",
        artifacts: [
          "/mnt/user-data/outputs/submarine/skill-studio/draft-only/validation-report.md",
          "/mnt/user-data/outputs/submarine/skill-studio/draft-only/SKILL.md",
        ],
      },
    },
  ]);

  assert.equal(entries.length, 1);
  assert.equal(entries[0]?.skillName, "仅草稿");
  assert.equal(entries[0]?.artifactCount, 2);
  assert.equal(entries[0]?.validationStatus, "draft_only");
});

void test("sorts newest skill-studio threads first", () => {
  const entries = buildSkillStudioEntries([
    {
      thread_id: "older",
      updated_at: "2026-03-26T00:00:00+00:00",
      values: {
        title: "Older",
        artifacts: [
          "/mnt/user-data/outputs/submarine/skill-studio/older/validation-report.md",
        ],
      },
    },
    {
      thread_id: "newer",
      updated_at: "2026-03-27T00:00:00+00:00",
      values: {
        title: "Newer",
        artifacts: [
          "/mnt/user-data/outputs/submarine/skill-studio/newer/validation-report.md",
        ],
      },
    },
  ]);

  assert.deepEqual(
    entries.map((entry) => entry.threadId),
    ["newer", "older"],
  );
});

void test("uses the provided untitled label for placeholder thread titles", () => {
  const entries = buildSkillStudioEntries(
    [
      {
        thread_id: "untitled-skill",
        updated_at: "2026-03-27T01:00:00+00:00",
        values: {
          title: "Untitled",
          artifacts: [
            "/mnt/user-data/outputs/submarine/skill-studio/untitled-skill/validation-report.md",
          ],
        },
      },
    ],
    "未命名技能工作台",
  );

  assert.equal(entries[0]?.title, "未命名技能工作台");
});
