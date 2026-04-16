import assert from "node:assert/strict";
import test from "node:test";

const {
  buildSkillStudioDetailModel,
} = await import(new URL("./skill-studio-detail-model.ts", import.meta.url).href);

void test("prefers published lifecycle state over stale ready-for-review archive status", () => {
  const model = buildSkillStudioDetailModel({
    studioState: {
      skill_name: "submarine-delivery-guard-20260415a",
      publish_status: "ready_for_review",
    },
    draft: {
      skill_name: "submarine-delivery-guard-20260415a",
      skill_purpose: "Guard delivery decisions.",
    },
    skillPackage: null,
    validation: {
      status: "ready_for_review",
      error_count: 0,
      warning_count: 0,
    },
    testMatrix: {
      status: "ready_for_dry_run",
      scenario_test_count: 1,
      blocking_count: 0,
      scenario_tests: [],
    },
    publishReadiness: {
      status: "ready_for_review",
      blocking_count: 0,
      gates: [],
      next_actions: [],
    },
    dryRunEvidence: {
      status: "passed",
    },
    lifecycleSummary: null,
    lifecycleDetail: {
      skill_name: "submarine-delivery-guard-20260415a",
      skill_asset_id: "submarine-delivery-guard-20260415a",
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
      version_note: "Published",
      artifact_virtual_paths: [],
      bindings: [],
      published_revisions: [],
    },
    skillGraph: null,
    studioArtifacts: [],
  });

  assert.equal(model.readiness.publishLabel, "已发布");
});
