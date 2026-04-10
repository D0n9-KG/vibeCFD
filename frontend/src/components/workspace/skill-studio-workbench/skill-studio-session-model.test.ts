import assert from "node:assert/strict";
import test from "node:test";

const { buildSkillStudioSessionModel } = await import(
  new URL("./skill-studio-session-model.ts", import.meta.url).href,
);

void test("keeps the six lifecycle modules and leaves assistant editable for new threads", () => {
  const model = buildSkillStudioSessionModel({
    isNewThread: true,
    persistedAssistantMode: null,
    hasDraftArtifact: false,
    validationStatus: "draft_only",
    testStatus: "draft_only",
    publishStatus: "draft_only",
    errorCount: 0,
    warningCount: 0,
    blockingCount: 0,
    graphRelationshipCount: 0,
  });

  assert.deepEqual(
    model.modules.map((item: { id: string }) => item.id),
    ["intent", "draft", "evaluation", "release-prep", "lifecycle", "graph"],
  );
  assert.equal(model.activeModuleId, "intent");
  assert.equal(model.assistant.locked, false);
});

void test("routes validation blockers into the evaluation module", () => {
  const model = buildSkillStudioSessionModel({
    isNewThread: false,
    persistedAssistantMode: "codex-skill-creator",
    hasDraftArtifact: true,
    validationStatus: "needs_revision",
    testStatus: "failed",
    publishStatus: "blocked",
    errorCount: 2,
    warningCount: 1,
    blockingCount: 3,
    graphRelationshipCount: 2,
  });

  assert.equal(model.activeModuleId, "evaluation");
  assert.equal(model.assistant.locked, true);
  assert.equal(model.negotiation.pendingApprovalCount, 3);
  assert.match(model.negotiation.question ?? "", /验证|阻塞/);
});

void test("routes review-ready packages into the lifecycle module while preserving graph context", () => {
  const model = buildSkillStudioSessionModel({
    isNewThread: false,
    persistedAssistantMode: "codex-skill-creator",
    hasDraftArtifact: true,
    validationStatus: "ready_for_review",
    testStatus: "ready_for_dry_run",
    publishStatus: "ready_for_review",
    errorCount: 0,
    warningCount: 1,
    blockingCount: 0,
    graphRelationshipCount: 5,
  });

  assert.equal(model.activeModuleId, "lifecycle");
  assert.equal(model.summary.graphRelationshipCount, 5);
  assert.equal(
    model.modules.find((item: { id: string }) => item.id === "graph")?.status,
    "已建立",
  );
});
