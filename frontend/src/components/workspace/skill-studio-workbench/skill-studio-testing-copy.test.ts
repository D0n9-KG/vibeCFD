import assert from "node:assert/strict";
import test from "node:test";

const {
  buildSkillStudioDetailModel,
} = await import(new URL("./skill-studio-detail-model.ts", import.meta.url).href);

void test("localizes skill studio testing copy instead of surfacing raw workflow statuses", () => {
  const model = buildSkillStudioDetailModel({
    studioState: null,
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
      scenario_tests: [
        {
          id: "scenario-a",
          scenario: "stable case",
          status: "ready_for_dry_run",
          expected_outcome:
            "Claude Code should trigger the drafted skill and produce a reviewable output.",
          blocking_reasons: [],
        },
      ],
    },
    publishReadiness: {
      status: "ready_for_review",
      blocking_count: 0,
      gates: [],
      next_actions: ["Run a dry-run conversation using one of the prepared scenarios."],
    },
    dryRunEvidence: {
      status: "not_recorded",
    },
    lifecycleSummary: null,
    lifecycleDetail: null,
    skillGraph: null,
    studioArtifacts: [],
  });

  assert.doesNotMatch(model.evaluate.status, /ready_for_review/i);
  assert.doesNotMatch(
    model.evaluate.scenarioMatrix.scenarios[0]?.status ?? "",
    /ready_for_dry_run/i,
  );
  assert.doesNotMatch(
    model.evaluate.scenarioMatrix.scenarios[0]?.expectedOutcome ?? "",
    /Claude Code should trigger the drafted skill/i,
  );
  assert.doesNotMatch(
    model.evaluate.dryRun.nextActions[0] ?? "",
    /Run a dry-run conversation/i,
  );
});
