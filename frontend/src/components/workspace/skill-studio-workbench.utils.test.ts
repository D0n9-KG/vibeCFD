import assert from "node:assert/strict";
import test from "node:test";

const {
  buildSkillStudioBindingTargets,
  describeSkillStudioBindingTargets,
  buildSkillStudioPublishPanelModel,
  findSkillLifecycleSummary,
  formatSkillStudioBindingMode,
  shouldLoadSkillLifecycleDetail,
  buildSkillStudioReadinessSummary,
  formatSkillStudioStatus,
  groupSkillStudioArtifacts,
  resolveSkillStudioEffectivePublishStatus,
  resolveSkillStudioAssistantIdentity,
} = await import(
  new URL("./skill-studio-workbench.utils.ts", import.meta.url).href,
);

void test("groups skill-studio artifacts into package, validation, testing, and publish buckets", () => {
  const groups = groupSkillStudioArtifacts([
    "/mnt/user-data/outputs/submarine/skill-studio/demo/skill-draft.json",
    "/mnt/user-data/outputs/submarine/skill-studio/demo/skill-lifecycle.json",
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
  assert.equal(groups[0]?.count, 5);
  assert.equal(groups[0]?.label, "鎶€鑳藉寘");
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
  assert.equal(readiness.validationLabel, "寰呭闃?");
  assert.equal(readiness.testLabel, "鍙瘯杩愯");
  assert.equal(readiness.publishLabel, "寰呭闃?");
});

void test("formats lifecycle-aware statuses into stable labels", () => {
  assert.equal(formatSkillStudioStatus("needs_revision"), "闇€淇");
  assert.equal(formatSkillStudioStatus("draft_only"), "浠呮湁鑽夌");
  assert.equal(formatSkillStudioStatus("draft_ready"), "草稿就绪");
  assert.equal(formatSkillStudioStatus("published"), "已发布");
  assert.equal(formatSkillStudioStatus("rollback_available"), "可回滚");
  assert.equal(formatSkillStudioStatus("Passed"), "宸查€氳繃");
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
      assistantLabel: "Claude Code 技能创建器",
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
      assistantLabel: "Codex 技能创建器",
    },
  );
});

void test("normalizes legacy persisted assistant labels", () => {
  assert.deepEqual(
    resolveSkillStudioAssistantIdentity({
      draftAssistantMode: null,
      draftAssistantLabel: null,
      packageAssistantMode: null,
      packageAssistantLabel: null,
      stateAssistantMode: "codex-skill-creator",
      stateAssistantLabel: "Codex 路 Skill Creator",
    }),
    {
      assistantMode: "codex-skill-creator",
      assistantLabel: "Codex 技能创建器",
    },
  );
});

void test("finds lifecycle summaries with explicit bindings for the focused skill", () => {
  const summary = findSkillLifecycleSummary(
    [
      {
        skill_name: "submarine-result-acceptance",
        enabled: true,
        binding_targets: [
          {
            role_id: "scientific-verification",
            mode: "explicit",
            target_skills: ["submarine-result-acceptance"],
          },
        ],
        revision_count: 3,
        binding_count: 1,
        active_revision_id: "rev-003",
        rollback_target_id: "rev-002",
        draft_status: "published",
        published_path: "skills/custom/submarine-result-acceptance",
        last_published_at: "2026-04-04T00:00:00Z",
        version_note: "Promote acceptance skill",
      },
    ],
    "submarine-result-acceptance",
  );

  assert.equal(summary?.skill_name, "submarine-result-acceptance");
  assert.equal(summary?.binding_targets[0]?.role_id, "scientific-verification");
});

void test("skips lifecycle detail fetches for draft-only skills that are not in the registry", () => {
  assert.equal(
    shouldLoadSkillLifecycleDetail({
      skillName: "cfd",
      lifecycleSummary: null,
      lifecycleRecord: {
        draft_status: "draft_ready",
        published_path: null,
        active_revision_id: null,
        published_revision_id: null,
      },
    }),
    false,
  );

  assert.equal(
    shouldLoadSkillLifecycleDetail({
      skillName: "submarine-result-acceptance",
      lifecycleSummary: {
        skill_name: "submarine-result-acceptance",
        enabled: true,
        binding_targets: [],
        revision_count: 1,
        binding_count: 0,
        active_revision_id: "rev-001",
        rollback_target_id: null,
        draft_status: "published",
        published_path: "skills/custom/submarine-result-acceptance",
        last_published_at: "2026-04-04T00:00:00Z",
        version_note: "Published",
      },
    }),
    true,
  );

  assert.equal(
    shouldLoadSkillLifecycleDetail({
      skillName: "submarine-result-acceptance",
      lifecycleSummary: null,
      lifecycleRecord: {
        draft_status: "published",
        published_path: "skills/custom/submarine-result-acceptance",
        active_revision_id: "rev-001",
        published_revision_id: "rev-001",
      },
    }),
    true,
  );

  assert.equal(
    shouldLoadSkillLifecycleDetail({
      skillName: "cfd",
      lifecycleSummary: null,
      hasLifecycleArtifactPath: false,
      lifecycleRecord: null,
      isThreadLoading: true,
    } as Parameters<typeof shouldLoadSkillLifecycleDetail>[0] & {
      isThreadLoading: boolean;
    }),
    false,
  );

  assert.equal(
    shouldLoadSkillLifecycleDetail({
      skillName: "cfd",
      lifecycleSummary: null,
      hasLifecycleArtifactPath: false,
      lifecycleRecord: null,
      areLifecycleSummariesLoading: true,
    } as Parameters<typeof shouldLoadSkillLifecycleDetail>[0] & {
      areLifecycleSummariesLoading: boolean;
    }),
    false,
  );

  assert.equal(
    shouldLoadSkillLifecycleDetail({
      skillName: "submarine-result-acceptance",
      lifecycleSummary: null,
      hasLifecycleArtifactPath: true,
      lifecycleRecord: null,
    }),
    false,
  );

  assert.equal(
    shouldLoadSkillLifecycleDetail({
      skillName: "submarine-result-acceptance",
      lifecycleSummary: null,
      hasLifecycleArtifactPath: false,
      lifecycleRecord: null,
    }),
    true,
  );
});

void test("builds publish panel state with no explicit bindings configured", () => {
  const model = buildSkillStudioPublishPanelModel({
    skillName: "submarine-result-acceptance",
    lifecycleSummary: {
      skill_name: "submarine-result-acceptance",
      enabled: false,
      binding_targets: [],
      revision_count: 2,
      binding_count: 0,
      active_revision_id: "rev-002",
      rollback_target_id: "rev-001",
      draft_status: "published",
      published_path: "skills/custom/submarine-result-acceptance",
      last_published_at: "2026-04-04T00:00:00Z",
      version_note: "Keep disabled for manual review",
    },
    stateVersionNote: "",
    stateBindings: null,
    stateActiveRevisionId: null,
    statePublishedRevisionId: null,
  });

  assert.equal(model.enabled, false);
  assert.equal(model.versionNote, "Keep disabled for manual review");
  assert.deepEqual(model.bindingTargets, []);
  assert.deepEqual(model.explicitBindingRoleIds, []);
  assert.equal(model.hasExplicitBindings, false);
  assert.equal(model.revisionCount, 2);
  assert.equal(model.bindingCount, 0);
  assert.equal(model.activeRevisionId, "rev-002");
  assert.equal(model.rollbackTargetId, "rev-001");
});

void test("builds canonical explicit binding targets from selected role ids", () => {
  const bindingTargets = buildSkillStudioBindingTargets(
    "submarine-result-acceptance",
    ["result-reporting", "scientific-verification"],
  );

  assert.deepEqual(bindingTargets, [
    {
      role_id: "scientific-verification",
      mode: "explicit",
      target_skills: ["submarine-result-acceptance"],
    },
    {
      role_id: "result-reporting",
      mode: "explicit",
      target_skills: ["submarine-result-acceptance"],
    },
  ]);
});

void test("formats binding modes and self-targets into user-facing labels", () => {
  assert.equal(formatSkillStudioBindingMode("explicit"), "显式挂载");
  assert.equal(
    describeSkillStudioBindingTargets(
      ["submarine-delivery-guard-20260415a"],
      "submarine-delivery-guard-20260415a",
    ),
    "当前技能",
  );
});

void test("treats lifecycle-published skills as published even when archive status is still review-ready", () => {
  assert.equal(
    resolveSkillStudioEffectivePublishStatus({
      publishStatus: "ready_for_review",
      lifecycleSummary: null,
      lifecycleDetail: {
        draft_status: "draft_ready",
        active_revision_id: "rev-001",
        published_revision_id: "rev-001",
        published_path: "skills/custom/submarine-delivery-guard-20260415a",
      },
    }),
    "published",
  );

  assert.equal(
    resolveSkillStudioEffectivePublishStatus({
      publishStatus: "ready_for_review",
      lifecycleSummary: {
        skill_name: "submarine-delivery-guard-20260415a",
        enabled: true,
        binding_targets: [],
        revision_count: 1,
        binding_count: 0,
        active_revision_id: "rev-001",
        published_revision_id: "rev-001",
        rollback_target_id: null,
        draft_status: "published",
        published_path: "skills/custom/submarine-delivery-guard-20260415a",
        last_published_at: "2026-04-15T00:00:00Z",
        version_note: "First publish",
      },
      lifecycleDetail: null,
    }),
    "published",
  );
});
