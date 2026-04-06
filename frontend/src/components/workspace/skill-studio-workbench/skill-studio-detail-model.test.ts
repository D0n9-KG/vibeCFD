import assert from "node:assert/strict";
import test from "node:test";

const { buildSkillStudioDetailModel } = await import(
  new URL("./skill-studio-detail-model.ts", import.meta.url).href,
);

void test("keeps define, evaluate, publish, and graph lifecycle detail explicit", () => {
  const model = buildSkillStudioDetailModel({
    studioState: {
      skill_name: "submarine-result-acceptance",
      builtin_skills: ["skill-creator", "writing-skills"],
      validation_status: "needs_revision",
      test_status: "ready_for_dry_run",
      publish_status: "blocked",
      error_count: 2,
      warning_count: 1,
      package_archive_virtual_path:
        "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/submarine-result-acceptance.skill",
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/skill-draft.json",
      ],
    },
    draft: {
      skill_name: "submarine-result-acceptance",
      skill_title: "Submarine Result Acceptance",
      skill_purpose: "Review CFD runs before publication.",
      trigger_conditions: ["when a run is marked ready for review"],
      expert_rules: ["never publish without evidence parity"],
      acceptance_criteria: ["flags missing validation artifacts"],
      test_scenarios: ["happy path dry run"],
    },
    skillPackage: {
      assistant_mode: "codex-skill-creator",
      assistant_label: "Codex Skill Creator",
      builtin_skills: ["skill-creator", "writing-skills"],
      package_archive_virtual_path:
        "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/submarine-result-acceptance.skill",
      archive_virtual_path:
        "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/submarine-result-acceptance.skill",
      ui_metadata_virtual_path:
        "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/agents/openai.yaml",
    },
    validation: {
      status: "needs_revision",
      error_count: 2,
      warning_count: 1,
      passed_checks: ["skill structure is valid"],
      errors: ["missing rollback note"],
      warnings: ["dry-run transcript is stale"],
    },
    testMatrix: {
      status: "ready_for_dry_run",
      scenario_test_count: 3,
      blocking_count: 1,
      scenario_tests: [
        {
          id: "scenario-a",
          scenario: "review passing report",
          status: "passed",
          expected_outcome: "accepts evidence package",
          blocking_reasons: [],
        },
        {
          id: "scenario-b",
          scenario: "review missing parity evidence",
          status: "blocked",
          expected_outcome: "demands remediation",
          blocking_reasons: ["environment parity summary missing"],
        },
      ],
    },
    publishReadiness: {
      status: "blocked",
      blocking_count: 1,
      gates: [
        { id: "structure", label: "Skill structure is valid", status: "passed" },
        {
          id: "trigger",
          label: "Trigger description is discoverable",
          status: "passed",
        },
        {
          id: "scenarios",
          label: "Scenario tests are prepared",
          status: "passed",
        },
        { id: "dry-run", label: "Dry-run handoff is ready", status: "blocked" },
        { id: "metadata", label: "UI metadata has been generated", status: "passed" },
      ],
      next_actions: [
        "Run a dry-run conversation using one of the prepared scenarios.",
        "Review the generated SKILL.md, domain rules, and UI metadata together.",
        "Publish only after the expert signs off on the dry-run result.",
      ],
    },
    lifecycleSummary: {
      skill_name: "submarine-result-acceptance",
      enabled: true,
      binding_targets: [
        {
          role_id: "scientific-verification",
          mode: "explicit",
          target_skills: ["submarine-result-acceptance"],
        },
      ],
      revision_count: 2,
      binding_count: 1,
      active_revision_id: "rev-2",
      published_revision_id: "rev-2",
      rollback_target_id: "rev-1",
      draft_status: "blocked",
      published_path: "/workspace/skills/submarine-result-acceptance",
      last_published_at: "2026-04-06T08:00:00Z",
      version_note: "Tighten review gate before enabling globally.",
    },
    lifecycleDetail: {
      skill_name: "submarine-result-acceptance",
      skill_asset_id: "submarine-result-acceptance",
      enabled: true,
      binding_targets: [
        {
          role_id: "scientific-verification",
          mode: "explicit",
          target_skills: ["submarine-result-acceptance"],
        },
      ],
      revision_count: 2,
      binding_count: 1,
      active_revision_id: "rev-2",
      published_revision_id: "rev-2",
      rollback_target_id: "rev-1",
      draft_status: "blocked",
      published_path: "/workspace/skills/submarine-result-acceptance",
      last_published_at: "2026-04-06T08:00:00Z",
      version_note: "Tighten review gate before enabling globally.",
      artifact_virtual_paths: [],
      bindings: [],
      published_revisions: [
        {
          revision_id: "rev-2",
          published_at: "2026-04-06T08:00:00Z",
          archive_path: "/tmp/rev-2.skill",
          published_path: "/workspace/skills/submarine-result-acceptance",
          version_note: "Current",
          binding_targets: [],
          enabled: true,
        },
        {
          revision_id: "rev-1",
          published_at: "2026-04-05T08:00:00Z",
          archive_path: "/tmp/rev-1.skill",
          published_path: "/workspace/skills/submarine-result-acceptance",
          version_note: "Rollback target",
          binding_targets: [],
          enabled: false,
        },
      ],
    },
    skillGraph: {
      summary: {
        skill_count: 12,
        enabled_skill_count: 8,
        public_skill_count: 6,
        custom_skill_count: 6,
        edge_count: 18,
        relationship_counts: {
          depend_on: 4,
          similar_to: 8,
          compose_with: 6,
        },
      },
      skills: [],
      relationships: [],
      focus: {
        skill_name: "submarine-result-acceptance",
        related_skill_count: 3,
        related_skills: [
          {
            skill_name: "mesh-remediation",
            category: "upstream",
            enabled: true,
            description: "Fixes parity issues before acceptance review.",
            relationship_types: ["depend_on"],
            strongest_score: 0.88,
            reasons: ["provides missing parity evidence"],
            revision_count: 3,
            active_revision_id: "mesh-3",
            rollback_target_id: "mesh-2",
            binding_count: 2,
            last_published_at: "2026-04-04T08:00:00Z",
          },
          {
            skill_name: "result-briefing",
            category: "downstream",
            enabled: true,
            description: "Packages approved results for reporting.",
            relationship_types: ["compose_with"],
            strongest_score: 0.73,
            reasons: ["consumes approved acceptance packets"],
            revision_count: 4,
            active_revision_id: "brief-4",
            rollback_target_id: "brief-3",
            binding_count: 1,
            last_published_at: "2026-04-03T08:00:00Z",
          },
          {
            skill_name: "validation-auditor",
            category: "similar",
            enabled: false,
            description: "Audits evidence and validation completeness.",
            relationship_types: ["similar_to"],
            strongest_score: 0.91,
            reasons: ["shares the same validation gate"],
            revision_count: 5,
            active_revision_id: "audit-5",
            rollback_target_id: "audit-4",
            binding_count: 2,
            last_published_at: "2026-04-02T08:00:00Z",
          },
        ],
      },
    },
    studioArtifacts: [
      "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/skill-draft.json",
      "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/test-matrix.json",
      "/mnt/user-data/outputs/submarine/skill-studio/submarine-result-acceptance/publish-readiness.json",
    ],
  });

  assert.equal(model.define.skillGoal, "Review CFD runs before publication.");
  assert.equal(model.define.triggerCount, 1);
  assert.equal(model.define.constraintCount, 1);
  assert.equal(model.define.acceptanceCriteria.length, 1);
  assert.equal(model.evaluate.errorCount, 2);
  assert.equal(model.evaluate.warningCount, 1);
  assert.equal(model.evaluate.scenarioMatrix.blockedCount, 1);
  assert.equal(model.evaluate.dryRun.ready, false);
  assert.equal(model.publish.enabled, true);
  assert.equal(model.publish.activeRevisionId, "rev-2");
  assert.equal(model.publish.publishedRevisionId, "rev-2");
  assert.equal(model.publish.rollbackTargetId, "rev-1");
  assert.equal(model.publish.explicitBindingRoleIds[0], "scientific-verification");
  assert.equal(model.publish.gates[0]?.label, "技能结构校验通过");
  assert.equal(model.publish.gates[1]?.label, "触发描述可被发现");
  assert.equal(model.publish.gates[2]?.label, "场景测试已准备");
  assert.equal(model.publish.gates[3]?.label, "试跑交接已就绪");
  assert.equal(model.publish.gates[4]?.label, "界面元数据已生成");
  assert.equal(
    model.publish.nextActions[0],
    "使用已准备的场景执行一次试跑对话。",
  );
  assert.equal(
    model.publish.nextActions[1],
    "一并复核生成的 SKILL.md、领域规则与界面元数据。",
  );
  assert.equal(
    model.publish.nextActions[2],
    "仅在专家确认试跑结果后再执行发布。",
  );
  assert.equal(model.graph.relationshipCount, 3);
  assert.equal(model.graph.highImpactCount, 2);
  assert.equal(model.graph.upstreamCount, 1);
  assert.equal(model.graph.downstreamCount, 1);
});

void test("localizes fallback skill define copy for new empty threads", () => {
  const model = buildSkillStudioDetailModel({
    studioState: null,
    draft: null,
    skillPackage: null,
    validation: null,
    testMatrix: null,
    publishReadiness: null,
    lifecycleSummary: null,
    lifecycleDetail: null,
    skillGraph: null,
    studioArtifacts: [],
  });

  assert.equal(model.define.skillName, "未命名技能");
  assert.equal(model.define.skillTitle, "未命名技能");
  assert.equal(model.define.skillGoal, "请先定义技能目标、触发条件与评审边界。");
});
