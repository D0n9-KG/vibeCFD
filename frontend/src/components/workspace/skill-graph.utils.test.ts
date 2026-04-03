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
  assert.equal(overview.topRelationships[0]?.label, "Compose with");
  assert.equal(overview.topRelationships[0]?.count, 3);
});

void test("focus helper sorts related skills by strongest score and label", () => {
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
        },
        {
          skill_name: "submarine-geometry-check",
          category: "public",
          enabled: true,
          description: "geometry",
          relationship_types: ["compose_with"],
          strongest_score: 0.3,
          reasons: ["Shared domain"],
        },
      ],
    },
  });

  assert.equal(related.length, 2);
  assert.equal(related[0]?.skillName, "submarine-report");
  assert.deepEqual(related[0]?.relationshipLabels, [
    "Depends on",
    "Similar to",
  ]);
  assert.equal(related[1]?.relationshipLabels[0], "Compose with");
});

void test("workbench model keeps the focus node and filters to similar relationships", () => {
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
        },
        {
          skill_name: "submarine-geometry-check",
          category: "public",
          enabled: true,
          description: "geometry",
          relationship_types: ["compose_with"],
          strongest_score: 0.3,
          reasons: ["Shared domain"],
        },
      ],
    },
  };

  const model = buildSkillGraphWorkbenchModel(graph, "similar");

  assert.equal(model.focusSkillName, "submarine-result-acceptance");
  assert.equal(model.nodes[0]?.skillName, "submarine-result-acceptance");
  assert.equal(model.nodes.length, 2);
  assert.equal(model.nodes[1]?.skillName, "submarine-report");
  assert.equal(model.edges.length, 1);
  assert.equal(model.edges[0]?.target, "submarine-report");
});
