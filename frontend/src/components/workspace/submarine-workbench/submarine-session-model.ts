import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "@/components/workspace/submarine-runtime-panel.contract";

import {
  getSubmarineDisplayedNextStage,
  getSubmarineDisplayedStage,
} from "../submarine-pipeline-runs.ts";

export type SubmarinePrimaryStage = "plan" | "execute" | "results";

export type SubmarineSessionModel = {
  primaryStage: SubmarinePrimaryStage;
  stageOrder: readonly SubmarinePrimaryStage[];
  reachableStages: readonly SubmarinePrimaryStage[];
  summary: {
    currentObjective: string;
    evidenceReady: boolean;
    messageCount: number;
    artifactCount: number;
  };
  negotiation: {
    pendingApprovalCount: number;
    interruptionVisible: boolean;
    question: string | null;
  };
  trustSurface: {
    provenanceAvailable: boolean;
    reproducibilityAvailable: boolean;
    environmentParityAvailable: boolean;
  };
};

export type BuildSubmarineSessionModelInput = {
  isNewThread: boolean;
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
  messageCount: number;
  artifactCount: number;
};

const EXECUTION_STAGE_IDS = new Set(["solver-dispatch", "result-reporting"]);
const PLAN_STAGE_IDS = new Set(["task-intelligence", "user-confirmation"]);
const ACTIVE_STAGE_STATUSES = new Set(["in_progress", "running", "streaming"]);

function countPendingApprovals({
  runtime,
  designBrief,
}: Pick<BuildSubmarineSessionModelInput, "runtime" | "designBrief">): number {
  const openQuestions =
    designBrief?.open_questions?.filter((question) => Boolean(question)).length ??
    0;
  const planItems = runtime?.calculation_plan ?? designBrief?.calculation_plan ?? [];
  const unconfirmedPlanItems = planItems.filter(
    (item) => item?.approval_state !== "researcher_confirmed",
  ).length;
  return openQuestions + unconfirmedPlanItems;
}

function hasImmediateConfirmationRequirement(
  runtime: SubmarineRuntimeSnapshotPayload | null,
  designBrief: SubmarineDesignBriefPayload | null,
): boolean {
  if (
    runtime?.requires_immediate_confirmation === true ||
    designBrief?.requires_immediate_confirmation === true
  ) {
    return true;
  }

  const planItems = runtime?.calculation_plan ?? designBrief?.calculation_plan ?? [];
  return planItems.some(
    (item) =>
      item?.requires_immediate_confirmation === true &&
      item?.approval_state !== "researcher_confirmed",
  );
}

function resolveBlockingReasons({
  runtime,
  designBrief,
  pendingApprovalCount,
}: Pick<BuildSubmarineSessionModelInput, "runtime" | "designBrief"> & {
  pendingApprovalCount: number;
}): string[] {
  const reasons: string[] = [];
  if (runtime?.review_status === "needs_user_confirmation") {
    reasons.push("Review status requires user confirmation.");
  }
  if (runtime?.next_recommended_stage === "user-confirmation") {
    reasons.push("Next recommended stage is user confirmation.");
  }
  if (hasImmediateConfirmationRequirement(runtime, designBrief)) {
    reasons.push("Immediate confirmation is required before execution.");
  }
  if (pendingApprovalCount > 0) {
    reasons.push(`There are ${pendingApprovalCount} pending approval items.`);
  }
  if (
    designBrief?.confirmation_status === "draft" &&
    (designBrief?.open_questions?.length ?? 0) > 0
  ) {
    reasons.push("Design brief is still draft with unresolved open questions.");
  }
  return reasons;
}

function resolvePrimaryStage(
  input: BuildSubmarineSessionModelInput,
  blockingReasons: string[],
): SubmarinePrimaryStage {
  const displayedStage = getSubmarineDisplayedStage(input.runtime, input.designBrief);
  const displayedNextStage = getSubmarineDisplayedNextStage(
    input.runtime,
    input.designBrief,
  );
  const stageStatus = input.runtime?.stage_status?.toLowerCase() ?? "";

  if (input.isNewThread || blockingReasons.length > 0) {
    return "plan";
  }

  if (
    input.finalReport ||
    displayedStage === "supervisor-review" ||
    displayedNextStage === "supervisor-review" ||
    input.runtime?.review_status === "ready_for_supervisor" ||
    input.runtime?.review_status === "completed" ||
    input.runtime?.current_stage === "supervisor-review"
  ) {
    return "results";
  }

  if (
    input.runtime?.runtime_status === "running" ||
    ACTIVE_STAGE_STATUSES.has(stageStatus) ||
    EXECUTION_STAGE_IDS.has(input.runtime?.current_stage ?? "") ||
    displayedStage === "geometry-preflight" ||
    displayedStage === "solver-dispatch" ||
    displayedStage === "result-reporting" ||
    input.runtime?.runtime_status === "completed"
  ) {
    return "execute";
  }

  if (displayedStage && PLAN_STAGE_IDS.has(displayedStage)) {
    return "plan";
  }

  return "plan";
}

function resolveReachableStages(
  primaryStage: SubmarinePrimaryStage,
): readonly SubmarinePrimaryStage[] {
  if (primaryStage === "results") {
    return ["plan", "execute", "results"];
  }

  if (primaryStage === "execute") {
    return ["plan", "execute"];
  }

  return ["plan"];
}

export function buildSubmarineSessionModel(
  input: BuildSubmarineSessionModelInput,
): SubmarineSessionModel {
  const pendingApprovalCount = countPendingApprovals(input);
  const blockingReasons = resolveBlockingReasons({
    runtime: input.runtime,
    designBrief: input.designBrief,
    pendingApprovalCount,
  });
  const primaryStage = resolvePrimaryStage(input, blockingReasons);
  const reachableStages = resolveReachableStages(primaryStage);
  const evidenceReady = Boolean(input.finalReport);
  const currentObjective =
    input.runtime?.task_summary ??
    input.designBrief?.summary_zh ??
    "Define the simulation objective and acceptance boundary.";

  return {
    primaryStage,
    stageOrder: ["plan", "execute", "results"],
    reachableStages,
    summary: {
      currentObjective,
      evidenceReady,
      messageCount: input.messageCount,
      artifactCount: input.artifactCount,
    },
    negotiation: {
      pendingApprovalCount,
      interruptionVisible: blockingReasons.length > 0,
      question:
        blockingReasons.length > 0
          ? `Blocking negotiation context: ${blockingReasons[0]}`
          : null,
    },
    trustSurface: {
      provenanceAvailable: Boolean(
        input.finalReport?.provenance_manifest_virtual_path ??
          input.runtime?.provenance_manifest_virtual_path,
      ),
      reproducibilityAvailable: Boolean(
        input.finalReport?.reproducibility_summary?.manifest_virtual_path,
      ),
      environmentParityAvailable: Boolean(
        input.finalReport?.environment_parity_assessment?.parity_status ??
          input.runtime?.environment_parity_assessment?.parity_status,
      ),
    },
  };
}
