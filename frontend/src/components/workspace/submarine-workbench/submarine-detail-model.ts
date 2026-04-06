import type {
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "@/components/workspace/submarine-runtime-panel.contract";

export type SubmarineTrustPanelId =
  | "provenance"
  | "reproducibility"
  | "environment-parity"
  | "experiment-compare"
  | "remediation"
  | "follow-up";

export type SubmarineTrustPanelModel = {
  id: SubmarineTrustPanelId;
  title: string;
  status: "available" | "missing";
  highlights: string[];
};

export type SubmarineDetailModel = {
  trustPanels: SubmarineTrustPanelModel[];
  experimentBoard: {
    baselineRunId: string | null;
    runCount: number;
    compareCount: number;
    compareCompletedCount: number;
  };
  operatorBoard: {
    decisionStatus: string | null;
    remediationActionCount: number;
    timelineEntryCount: number;
    followupStatus: string | null;
  };
};

export type BuildSubmarineDetailModelInput = {
  runtime: SubmarineRuntimeSnapshotPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
};

function createTrustPanel(
  id: SubmarineTrustPanelId,
  title: string,
  available: boolean,
  highlight: string | null,
): SubmarineTrustPanelModel {
  return {
    id,
    title,
    status: available ? "available" : "missing",
    highlights: highlight ? [highlight] : [],
  };
}

export function buildSubmarineDetailModel({
  runtime,
  finalReport,
}: BuildSubmarineDetailModelInput): SubmarineDetailModel {
  const experimentSummary = finalReport?.experiment_summary;
  const compareSummary = finalReport?.experiment_compare_summary;
  const remediationSummary = finalReport?.scientific_remediation_summary;
  const followupSummary = finalReport?.scientific_followup_summary;
  const compareCompletedCount =
    compareSummary?.compare_status_counts?.completed ?? 0;

  return {
    trustPanels: [
      createTrustPanel(
        "provenance",
        "Provenance",
        Boolean(
          finalReport?.provenance_manifest_virtual_path ??
            runtime?.provenance_manifest_virtual_path,
        ),
        finalReport?.provenance_manifest_virtual_path ??
          runtime?.provenance_manifest_virtual_path ??
          null,
      ),
      createTrustPanel(
        "reproducibility",
        "Reproducibility",
        Boolean(finalReport?.reproducibility_summary?.manifest_virtual_path),
        finalReport?.reproducibility_summary?.reproducibility_status ?? null,
      ),
      createTrustPanel(
        "environment-parity",
        "Environment Parity",
        Boolean(
          finalReport?.environment_parity_assessment?.parity_status ??
            runtime?.environment_parity_assessment?.parity_status,
        ),
        finalReport?.environment_parity_assessment?.profile_label ??
          runtime?.environment_parity_assessment?.profile_label ??
          null,
      ),
      createTrustPanel(
        "experiment-compare",
        "Experiment / Compare",
        Boolean(experimentSummary ?? compareSummary),
        experimentSummary?.experiment_status ??
          compareSummary?.workflow_status ??
          null,
      ),
      createTrustPanel(
        "remediation",
        "Remediation",
        Boolean(remediationSummary),
        remediationSummary?.plan_status ?? null,
      ),
      createTrustPanel(
        "follow-up",
        "Follow-up",
        Boolean(followupSummary),
        followupSummary?.latest_outcome_status ?? null,
      ),
    ],
    experimentBoard: {
      baselineRunId: experimentSummary?.baseline_run_id ?? null,
      runCount: experimentSummary?.run_count ?? 0,
      compareCount: experimentSummary?.compare_count ?? 0,
      compareCompletedCount,
    },
    operatorBoard: {
      decisionStatus: finalReport?.delivery_decision_summary?.decision_status ?? null,
      remediationActionCount: remediationSummary?.actions?.length ?? 0,
      timelineEntryCount: runtime?.activity_timeline?.length ?? 0,
      followupStatus: followupSummary?.latest_outcome_status ?? null,
    },
  };
}
