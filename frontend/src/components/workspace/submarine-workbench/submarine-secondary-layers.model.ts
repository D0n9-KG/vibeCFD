import type { SubmarineDetailModel } from "./submarine-detail-model";
import type { SubmarineResearchSliceId } from "./submarine-session-model";

export type SubmarineSecondaryLayerId = "trust" | "studies" | "operator";

function hasTrustSignals(detail: SubmarineDetailModel): boolean {
  return detail.trustPanels.some((panel) => panel.status === "available");
}

function hasStudySignals(detail: SubmarineDetailModel): boolean {
  const board = detail.experimentBoard;
  return [
    board.baselineRunId,
    board.runCount > 0,
    board.compareCount > 0,
    board.compareCompletedCount > 0,
    board.variantCount > 0,
    board.variantRunIds.length > 0,
    board.lineageNotes.length > 0,
    board.comparisons.length > 0,
    board.studyCount > 0,
    board.studies.length > 0,
  ].some(Boolean);
}

function hasOperatorSignals(detail: SubmarineDetailModel): boolean {
  const board = detail.operatorBoard;
  return [
    board.decisionStatus,
    board.deliveryDecision.question,
    board.deliveryDecision.optionCount > 0,
    board.deliveryDecision.options.length > 0,
    board.deliveryDecision.blockingReasons.length > 0,
    board.deliveryDecision.advisoryNotes.length > 0,
    board.remediation.planStatus,
    board.remediation.actionCount > 0,
    board.remediation.actions.length > 0,
    board.remediation.handoffStatus,
    board.remediation.handoffToolName,
    board.remediation.manualActionCount > 0,
    board.remediation.manualActions.length > 0,
    board.followup.latestOutcomeStatus,
    board.followup.latestToolName,
    board.followup.latestNotes.length > 0,
    board.followup.historyVirtualPath,
  ].some(Boolean);
}

const LAYER_ORDER_BY_SLICE: Record<
  SubmarineResearchSliceId,
  readonly SubmarineSecondaryLayerId[]
> = {
  "task-establishment": ["operator", "trust", "studies"],
  "geometry-preflight": ["operator", "trust", "studies"],
  "simulation-plan": ["operator", "trust", "studies"],
  "simulation-execution": ["studies", "trust", "operator"],
  "results-and-delivery": ["trust", "studies", "operator"],
};

export function resolveSubmarineSecondaryLayerIds({
  sliceId,
  detail,
}: {
  sliceId: SubmarineResearchSliceId;
  detail: SubmarineDetailModel;
}): readonly SubmarineSecondaryLayerId[] {
  const visible = new Set<SubmarineSecondaryLayerId>();

  if (hasTrustSignals(detail)) {
    visible.add("trust");
  }
  if (hasStudySignals(detail)) {
    visible.add("studies");
  }
  if (hasOperatorSignals(detail)) {
    visible.add("operator");
  }

  return LAYER_ORDER_BY_SLICE[sliceId].filter((layerId) => visible.has(layerId));
}
