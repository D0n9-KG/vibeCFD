import assert from "node:assert/strict";
import test from "node:test";

const { buildSkillStudioSessionModel } = await import(
  new URL("./skill-studio-session-model.ts", import.meta.url).href,
);

void test("routes brand new threads to define and keeps assistant choice editable", () => {
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

  assert.equal(model.primaryStage, "define");
  assert.equal(model.assistant.locked, false);
  assert.equal(model.negotiation.interruptionVisible, false);
  assert.deepEqual(model.stageOrder, ["define", "evaluate", "publish", "graph"]);
});

void test("routes drafted skills with validation blockers to evaluate and locks the assistant once persisted", () => {
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

  assert.equal(model.primaryStage, "evaluate");
  assert.equal(model.assistant.locked, true);
  assert.equal(model.negotiation.pendingApprovalCount, 3);
  assert.equal(model.negotiation.interruptionVisible, true);
  assert.match(model.negotiation.question ?? "", /validation/i);
});

void test("routes publish-ready skills to publish while keeping graph context available", () => {
  const model = buildSkillStudioSessionModel({
    isNewThread: false,
    persistedAssistantMode: "codex-skill-creator",
    hasDraftArtifact: true,
    validationStatus: "ready_for_review",
    testStatus: "ready_for_dry_run",
    publishStatus: "published",
    errorCount: 0,
    warningCount: 1,
    blockingCount: 0,
    graphRelationshipCount: 5,
  });

  assert.equal(model.primaryStage, "publish");
  assert.equal(model.summary.graphRelationshipCount, 5);
  assert.equal(model.negotiation.interruptionVisible, false);
});
