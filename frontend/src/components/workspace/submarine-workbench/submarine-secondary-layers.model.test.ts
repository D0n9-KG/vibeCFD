import assert from "node:assert/strict";
import test from "node:test";

const { resolveSubmarineSecondaryLayerIds } = await import(
  new URL("./submarine-secondary-layers.model.ts", import.meta.url).href,
);

void test("suppresses empty secondary layers for an early geometry-preflight slice", () => {
  const layerIds = resolveSubmarineSecondaryLayerIds({
    sliceId: "geometry-preflight",
    detail: {
      trustPanels: [
        { id: "provenance", title: "来源链路", status: "missing", highlights: [] },
      ],
      experimentBoard: {
        baselineRunId: null,
        runCount: 0,
        compareCount: 0,
        compareCompletedCount: 0,
        variantCount: 0,
        variantRunIds: [],
        lineageModeLabel: null,
        compareTargetRunIds: [],
        followupSourceRunId: null,
        lineageNotes: [],
        comparisons: [],
        studyCount: 0,
        studies: [],
      },
      operatorBoard: {
        decisionStatus: null,
        timelineEntryCount: 1,
        contract: {
          revisionLabel: null,
          iterationModeLabel: null,
          revisionSummary: null,
          capabilityGapCount: 0,
          unresolvedDecisionCount: 0,
          evidenceExpectationCount: 0,
          deliveryDeliveredCount: 0,
          deliveryPlannedCount: 0,
          deliveryBlockedCount: 0,
        },
        deliveryDecision: {
          question: null,
          optionCount: 0,
          options: [],
          blockingReasons: [],
          advisoryNotes: [],
        },
        remediation: {
          planStatus: null,
          actionCount: 0,
          actions: [],
          handoffStatus: null,
          handoffToolName: null,
          sourceRunId: null,
          baselineReferenceRunId: null,
          compareTargetRunId: null,
          derivedRunIds: [],
          manualActionCount: 0,
          manualActions: [],
        },
        followup: {
          latestOutcomeStatus: null,
          latestToolName: null,
          latestSourceRunId: null,
          latestBaselineReferenceRunId: null,
          latestCompareTargetRunId: null,
          latestDerivedRunIds: [],
          latestNotes: [],
          historyVirtualPath: null,
        },
      },
    },
  });

  assert.deepEqual(layerIds, []);
});

void test("prioritizes trust and operator layers when a results slice has real review signals", () => {
  const layerIds = resolveSubmarineSecondaryLayerIds({
    sliceId: "results-and-delivery",
    detail: {
      trustPanels: [
        {
          id: "provenance",
          title: "来源链路",
          status: "available",
          highlights: ["provenance.json"],
        },
      ],
      experimentBoard: {
        baselineRunId: "baseline-01",
        runCount: 2,
        compareCount: 1,
        compareCompletedCount: 1,
        variantCount: 1,
        variantRunIds: ["variant-a"],
        lineageModeLabel: null,
        compareTargetRunIds: ["baseline-01"],
        followupSourceRunId: null,
        lineageNotes: ["compare.json"],
        comparisons: [
          {
            candidateRunId: "variant-a",
            status: "completed",
            variantLabel: "A",
            baselineReferenceRunId: "baseline-01",
          },
        ],
        studyCount: 1,
        studies: [{ label: "AoA sweep", workflowStatus: "completed" }],
      },
      operatorBoard: {
        decisionStatus: "needs_followup",
        timelineEntryCount: 2,
        contract: {
          revisionLabel: null,
          iterationModeLabel: null,
          revisionSummary: null,
          capabilityGapCount: 0,
          unresolvedDecisionCount: 0,
          evidenceExpectationCount: 0,
          deliveryDeliveredCount: 0,
          deliveryPlannedCount: 0,
          deliveryBlockedCount: 0,
        },
        deliveryDecision: {
          question: "Can this be delivered?",
          optionCount: 1,
          options: ["Remediate first"],
          blockingReasons: [],
          advisoryNotes: [],
        },
        remediation: {
          planStatus: "needed",
          actionCount: 1,
          actions: ["Refine mesh"],
          handoffStatus: null,
          handoffToolName: null,
          sourceRunId: null,
          baselineReferenceRunId: null,
          compareTargetRunId: null,
          derivedRunIds: [],
          manualActionCount: 0,
          manualActions: [],
        },
        followup: {
          latestOutcomeStatus: null,
          latestToolName: null,
          latestSourceRunId: null,
          latestBaselineReferenceRunId: null,
          latestCompareTargetRunId: null,
          latestDerivedRunIds: [],
          latestNotes: [],
          historyVirtualPath: null,
        },
      },
    },
  });

  assert.deepEqual(layerIds, ["trust", "studies", "operator"]);
});

void test("keeps the operator layer visible when iterative contract truth is the only surfaced signal", () => {
  const layerIds = resolveSubmarineSecondaryLayerIds({
    sliceId: "simulation-plan",
    detail: {
      trustPanels: [
        { id: "provenance", title: "来源链路", status: "missing", highlights: [] },
      ],
      experimentBoard: {
        baselineRunId: null,
        runCount: 0,
        compareCount: 0,
        compareCompletedCount: 0,
        variantCount: 0,
        variantRunIds: [],
        lineageModeLabel: null,
        compareTargetRunIds: [],
        followupSourceRunId: null,
        lineageNotes: [],
        comparisons: [],
        studyCount: 0,
        studies: [],
      },
      operatorBoard: {
        decisionStatus: null,
        timelineEntryCount: 0,
        contract: {
          revisionLabel: "r4",
          iterationModeLabel: "派生变体",
          revisionSummary: "Add wake-focused outputs to the current baseline family.",
          capabilityGapCount: 1,
          unresolvedDecisionCount: 2,
          evidenceExpectationCount: 1,
          deliveryDeliveredCount: 1,
          deliveryPlannedCount: 1,
          deliveryBlockedCount: 1,
        },
        deliveryDecision: {
          question: null,
          optionCount: 0,
          options: [],
          blockingReasons: [],
          advisoryNotes: [],
        },
        remediation: {
          planStatus: null,
          actionCount: 0,
          actions: [],
          handoffStatus: null,
          handoffToolName: null,
          sourceRunId: null,
          baselineReferenceRunId: null,
          compareTargetRunId: null,
          derivedRunIds: [],
          manualActionCount: 0,
          manualActions: [],
        },
        followup: {
          latestOutcomeStatus: null,
          latestToolName: null,
          latestSourceRunId: null,
          latestBaselineReferenceRunId: null,
          latestCompareTargetRunId: null,
          latestDerivedRunIds: [],
          latestNotes: [],
          historyVirtualPath: null,
        },
      },
    },
  });

  assert.deepEqual(layerIds, ["operator"]);
});
