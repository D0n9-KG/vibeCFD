import assert from "node:assert/strict";
import test from "node:test";

const { buildSkillStudioEntries } = await import(
  new URL("./skill-studio-dashboard.utils.ts", import.meta.url).href,
);

void test("extracts lifecycle-backed skill-studio entries from thread search results", () => {
  const entries = buildSkillStudioEntries([
    {
      thread_id: "submarine-skill-studio-demo",
      updated_at: "2026-03-27T00:00:00+00:00",
      values: {
        title: "娼滆墖 Skill Studio 婕旂ず",
        artifacts: [
          "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/skill-draft.json",
          "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/validation-report.md",
        ],
        submarine_skill_studio: {
          skill_name: "submarine-result-acceptance",
          skill_asset_id: "submarine-result-acceptance",
          assistant_mode: "claude-code-skill-creator",
          assistant_label: "Claude Code 鎶€鑳藉垱寤哄櫒",
          validation_status: "ready_for_review",
          test_status: "ready_for_dry_run",
          publish_status: "ready_for_review",
          error_count: 0,
          warning_count: 1,
          lifecycle_virtual_path:
            "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/skill-lifecycle.json",
          active_revision_id: "rev-002",
          published_revision_id: "rev-001",
          version_note: "Promote acceptance skill",
          bindings: [
            {
              role_id: "scientific-verification",
              mode: "explicit",
              target_skills: ["submarine-result-acceptance"],
            },
          ],
          report_virtual_path:
            "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/validation-report.md",
          artifact_virtual_paths: [
            "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/skill-draft.json",
            "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/skill-lifecycle.json",
            "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/validation-report.md",
          ],
        },
      },
    },
    {
      thread_id: "submarine-cfd-demo",
      updated_at: "2026-03-26T00:00:00+00:00",
      values: {
        title: "娼滆墖 CFD 鏈€灏忛棴鐜紨绀?",
        artifacts: [
          "/mnt/user-data/outputs/submarine/reports/live-forces-suboff/final-report.md",
        ],
      },
    },
  ]);

  assert.equal(entries.length, 1);
  assert.equal(entries[0]?.threadId, "submarine-skill-studio-demo");
  assert.match(entries[0]?.title ?? "", /技能工作台/);
  assert.equal(entries[0]?.skillName, "潜艇结果验收");
  assert.equal(entries[0]?.skillAssetId, "submarine-result-acceptance");
  assert.equal(entries[0]?.assistantMode, "claude-code-skill-creator");
  assert.equal(entries[0]?.assistantLabel, "Claude Code 鎶€鑳藉垱寤哄櫒");
  assert.equal(entries[0]?.validationStatus, "ready_for_review");
  assert.equal(entries[0]?.testStatus, "ready_for_dry_run");
  assert.equal(entries[0]?.publishStatus, "ready_for_review");
  assert.equal(entries[0]?.artifactCount, 3);
  assert.equal(
    entries[0]?.lifecycleVirtualPath,
    "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/skill-lifecycle.json",
  );
  assert.equal(entries[0]?.activeRevisionId, "rev-002");
  assert.equal(entries[0]?.publishedRevisionId, "rev-001");
  assert.equal(entries[0]?.versionNote, "Promote acceptance skill");
  assert.equal(entries[0]?.bindings.length, 1);
  assert.equal(entries[0]?.bindings[0]?.roleId, "scientific-verification");
  assert.equal(entries[0]?.bindings[0]?.mode, "explicit");
});

void test("normalizes legacy persisted assistant labels", () => {
  const entries = buildSkillStudioEntries([
    {
      thread_id: "legacy-label",
      updated_at: "2026-03-27T00:00:00+00:00",
      values: {
        title: "鏃ф爣绛剧嚎绋?",
        artifacts: [
          "/mnt/user-data/outputs/submarine/skill-studio/legacy-label/skill-draft.json",
        ],
        submarine_skill_studio: {
          assistant_mode: "codex-skill-creator",
          assistant_label: "Codex 路 Skill Creator",
        },
      },
    },
  ]);

  assert.equal(entries[0]?.assistantLabel, "Codex 技能创建器");
});

void test("falls back to legacy skill-studio artifacts when structured lifecycle state is missing", () => {
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
  assert.equal(entries[0]?.skillAssetId, "draft-only");
  assert.equal(entries[0]?.artifactCount, 2);
  assert.equal(entries[0]?.validationStatus, "draft_only");
  assert.equal(entries[0]?.lifecycleVirtualPath, null);
  assert.equal(entries[0]?.activeRevisionId, null);
  assert.equal(entries[0]?.publishedRevisionId, null);
  assert.equal(entries[0]?.versionNote, "");
  assert.deepEqual(entries[0]?.bindings, []);
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
    "鏈懡鍚嶆妧鑳藉伐浣滃彴",
  );

  assert.equal(entries[0]?.title, "鏈懡鍚嶆妧鑳藉伐浣滃彴");
});
