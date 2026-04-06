import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "@/components/workspace/submarine-runtime-panel.contract";

export type SubmarinePrimaryStage = "plan" | "execute" | "results";

export type SubmarineSessionModel = {
  primaryStage: SubmarinePrimaryStage;
  stageOrder: readonly SubmarinePrimaryStage[];
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

function resolvePrimaryStage(
  input: BuildSubmarineSessionModelInput,
  pendingApprovalCount: number,
): SubmarinePrimaryStage {
  if (input.isNewThread || pendingApprovalCount > 0) {
    return "plan";
  }

  if (input.finalReport) {
    return "results";
  }

  if (
    input.runtime?.runtime_status === "running" ||
    EXECUTION_STAGE_IDS.has(input.runtime?.current_stage ?? "")
  ) {
    return "execute";
  }

  if (input.runtime?.current_stage === "supervisor-review") {
    return "results";
  }

  return "plan";
}

export function buildSubmarineSessionModel(
  input: BuildSubmarineSessionModelInput,
): SubmarineSessionModel {
  const pendingApprovalCount = countPendingApprovals(input);
  const primaryStage = resolvePrimaryStage(input, pendingApprovalCount);
  const evidenceReady = Boolean(input.finalReport);
  const currentObjective =
    input.runtime?.task_summary ??
    input.designBrief?.summary_zh ??
    "Define the simulation objective and acceptance boundary.";

  return {
    primaryStage,
    stageOrder: ["plan", "execute", "results"],
    summary: {
      currentObjective,
      evidenceReady,
      messageCount: input.messageCount,
      artifactCount: input.artifactCount,
    },
    negotiation: {
      pendingApprovalCount,
      interruptionVisible:
        pendingApprovalCount > 0 ||
        input.runtime?.review_status === "needs_user_confirmation",
      question:
        pendingApprovalCount > 0
          ? "Pending confirmations are blocking progress. Confirm plan assumptions before execution."
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
