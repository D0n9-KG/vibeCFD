import assert from "node:assert/strict";
import test from "node:test";

const {
  buildSkillGraphOverview,
  buildFocusedSkillGraphItems,
  buildSkillGraphWorkbenchModel,
} = await import(new URL("./skill-graph.utils.ts", import.meta.url).href);

void test("builds a readable overview from the skill graph summary", () => {
  const overview = buildSkillGraphOverview({
    summary: {
      skill_count: 6,
      enabled_skill_count: 5,
      public_skill_count: 4,
      custom_skill_count: 2,
      edge_count: 7,
      relationship_counts: {
        similar_to: 2,
        compose_with: 3,
        depend_on: 2,
      },
    },
  });

  assert.equal(overview.skillCount, 6);
  assert.equal(overview.enabledCount, 5);
  assert.equal(overview.edgeCount, 7);
  assert.equal(overview.topRelationships[0]?.label, "组合使用");
  assert.equal(overview.topRelationships[0]?.count, 3);
});

void test("focus helper sorts related skills by strongest score and preserves governance metadata", () => {
  const related = buildFocusedSkillGraphItems({
    focus: {
      skill_name: "submarine-result-acceptance",
      related_skill_count: 2,
      related_skills: [
        {
          skill_name: "submarine-report",
          category: "public",
          enabled: true,
          description: "report",
          relationship_types: ["depend_on", "similar_to"],
          strongest_score: 1,
          reasons: ["Explicit reference"],
          revision_count: 0,
          binding_count: 0,
        },
        {
          skill_name: "submarine-geometry-check",
          category: "public",
          enabled: true,
          description: "geometry",
          relationship_types: ["compose_with"],
          strongest_score: 0.3,
          reasons: ["Shared domain"],
          revision_count: 2,
          rollback_target_id: "rev-001",
          binding_count: 1,
          last_published_at: "2026-04-04T00:00:00Z",
        },
      ],
    },
  });

  assert.equal(related.length, 2);
  assert.equal(related[0]?.skillAssetId, "submarine-report");
  assert.equal(related[0]?.skillName, "结果整理技能");
  assert.deepEqual(related[0]?.relationshipLabels, ["能力相似", "依赖于"]);
  assert.equal(related[1]?.relationshipLabels[0], "组合使用");
  assert.equal(related[1]?.bindingCount, 1);
  assert.equal(related[1]?.rollbackTargetId, "rev-001");
});

void test("workbench model keeps raw ids while rendering localized labels", () => {
  const graph = {
    focus: {
      skill_name: "submarine-result-acceptance",
      related_skills: [
        {
          skill_name: "submarine-report",
          category: "public",
          enabled: true,
          description: "report",
          relationship_types: ["depend_on", "similar_to"],
          strongest_score: 1,
          reasons: ["Explicit reference"],
          revision_count: 0,
          binding_count: 0,
        },
        {
          skill_name: "submarine-geometry-check",
          category: "public",
          enabled: true,
          description: "geometry",
          relationship_types: ["compose_with"],
          strongest_score: 0.3,
          reasons: ["Shared domain"],
          revision_count: 2,
          binding_count: 1,
          active_revision_id: "rev-002",
        },
      ],
    },
  };

  const model = buildSkillGraphWorkbenchModel(graph, "similar");

  assert.equal(model.focusSkillName, "submarine-result-acceptance");
  assert.equal(model.nodes[0]?.skillName, "潜艇结果验收");
  assert.equal(model.nodes.length, 2);
  assert.equal(model.nodes[1]?.skillName, "结果整理技能");
  assert.equal(model.nodes[1]?.id, "submarine-report");
  assert.equal(model.edges.length, 1);
  assert.equal(model.edges[0]?.target, "submarine-report");
});
