import type {
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "@/components/workspace/submarine-runtime-panel.contract";

export type SubmarineTrustPanelId =
  | "provenance"
  | "reproducibility"
  | "environment-parity"
  | "scientific-gate"
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
    variantCount: number;
    variantRunIds: string[];
    lineageNotes: string[];
    comparisons: Array<{
      candidateRunId: string;
      status: string;
      variantLabel: string;
      baselineReferenceRunId: string | null;
    }>;
    studyCount: number;
    studies: Array<{
      label: string;
      workflowStatus: string;
    }>;
  };
  operatorBoard: {
    decisionStatus: string | null;
    timelineEntryCount: number;
    deliveryDecision: {
      question: string | null;
      optionCount: number;
      options: string[];
      blockingReasons: string[];
      advisoryNotes: string[];
    };
    remediation: {
      planStatus: string | null;
      actionCount: number;
      actions: string[];
      handoffStatus: string | null;
      handoffToolName: string | null;
      manualActionCount: number;
      manualActions: string[];
    };
    followup: {
      latestOutcomeStatus: string | null;
      latestToolName: string | null;
      latestNotes: string[];
      historyVirtualPath: string | null;
    };
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
  const studySummary = finalReport?.scientific_study_summary;
  const remediationSummary = finalReport?.scientific_remediation_summary;
  const remediationHandoff = finalReport?.scientific_remediation_handoff;
  const followupSummary = finalReport?.scientific_followup_summary;
  const deliveryDecision = finalReport?.delivery_decision_summary;
  const supervisorGate = finalReport?.scientific_supervisor_gate;
  const researchEvidence = finalReport?.research_evidence_summary;
  const reproducibilitySummary = finalReport?.reproducibility_summary;
  const environmentParity =
    finalReport?.environment_parity_assessment ??
    runtime?.environment_parity_assessment;
  const compareCompletedCount =
    compareSummary?.compare_status_counts?.completed ?? 0;
  const variantRunIds = [
    ...(experimentSummary?.compared_variant_run_ids ?? []),
    ...(experimentSummary?.completed_variant_run_ids ?? []),
    ...(experimentSummary?.recorded_variant_run_ids ?? []),
  ].filter((id, index, all): id is string => Boolean(id) && all.indexOf(id) === index);
  const lineageNotes = [
    ...(experimentSummary?.linkage_issues ?? []),
    ...(experimentSummary?.compare_notes ?? []),
    ...(compareSummary?.artifact_virtual_paths ?? []),
  ].filter((item): item is string => Boolean(item));
  const comparisons =
    compareSummary?.comparisons?.map((comparison) => ({
      candidateRunId: comparison?.candidate_run_id ?? "unknown",
      status: comparison?.compare_status ?? "pending",
      variantLabel: comparison?.variant_label ?? "variant",
      baselineReferenceRunId: comparison?.baseline_reference_run_id ?? null,
    })) ?? [];
  const studies =
    studySummary?.studies?.map((study) => ({
      label: study?.summary_label ?? "scientific study",
      workflowStatus: study?.workflow_status ?? "pending",
    })) ?? [];
  const remediationActions =
    remediationSummary?.actions?.map((action) => action?.title ?? "remediation action") ??
    [];
  const remediationManualActions =
    remediationHandoff?.manual_actions?.map(
      (action) => action?.title ?? "manual remediation action",
    ) ?? [];
  const decisionOptions =
    deliveryDecision?.options?.map((option) => option?.label_zh ?? "option") ?? [];

  return {
    trustPanels: [
      createTrustPanel(
        "provenance",
        "Provenance",
        Boolean(
          finalReport?.provenance_manifest_virtual_path ??
            runtime?.provenance_manifest_virtual_path,
        ),
        [
          finalReport?.provenance_manifest_virtual_path,
          ...(finalReport?.delivery_highlights?.highlight_artifact_virtual_paths ?? []),
          ...(finalReport?.evidence_index?.map((group) => group?.group_title_zh ?? "") ??
            []),
        ]
          .filter(Boolean)
          .join(" | ") || null,
      ),
      createTrustPanel(
        "reproducibility",
        "Reproducibility",
        Boolean(
          reproducibilitySummary?.manifest_virtual_path ??
            reproducibilitySummary?.reproducibility_status,
        ),
        [
          reproducibilitySummary?.reproducibility_status,
          ...(reproducibilitySummary?.drift_reasons ?? []),
          ...(reproducibilitySummary?.recovery_guidance ?? []),
        ]
          .filter(Boolean)
          .join(" | ") || null,
      ),
      createTrustPanel(
        "environment-parity",
        "Environment Parity",
        Boolean(environmentParity?.parity_status),
        [
          environmentParity?.parity_status,
          environmentParity?.profile_label,
          ...(environmentParity?.drift_reasons ?? []),
          ...(environmentParity?.recovery_guidance ?? []),
        ]
          .filter(Boolean)
          .join(" | ") || null,
      ),
      createTrustPanel(
        "scientific-gate",
        "Scientific Gate",
        Boolean(
          supervisorGate?.gate_status ??
            finalReport?.scientific_gate_status ??
            runtime?.scientific_gate_status ??
            researchEvidence,
        ),
        [
          supervisorGate?.gate_status ??
            finalReport?.scientific_gate_status ??
            runtime?.scientific_gate_status,
          researchEvidence?.readiness_status,
          ...(supervisorGate?.blocking_reasons ?? []),
          ...(supervisorGate?.advisory_notes ?? []),
          ...(researchEvidence?.blocking_issues ?? []),
        ]
          .filter(Boolean)
          .join(" | ") || null,
      ),
      createTrustPanel(
        "experiment-compare",
        "Experiment / Compare",
        Boolean(experimentSummary ?? compareSummary ?? studySummary),
        [
          experimentSummary?.workflow_status,
          compareSummary?.workflow_status,
          studySummary?.study_execution_status,
        ]
          .filter(Boolean)
          .join(" | ") || null,
      ),
      createTrustPanel(
        "remediation",
        "Remediation",
        Boolean(remediationSummary ?? remediationHandoff),
        [
          remediationSummary?.plan_status,
          remediationHandoff?.handoff_status,
          remediationHandoff?.tool_name,
        ]
          .filter(Boolean)
          .join(" | ") || null,
      ),
      createTrustPanel(
        "follow-up",
        "Follow-up",
        Boolean(followupSummary),
        [
          followupSummary?.latest_outcome_status,
          followupSummary?.latest_tool_name,
          ...(followupSummary?.latest_notes ?? []),
        ]
          .filter(Boolean)
          .join(" | ") || null,
      ),
    ],
    experimentBoard: {
      baselineRunId: experimentSummary?.baseline_run_id ?? null,
      runCount: experimentSummary?.run_count ?? 0,
      compareCount: experimentSummary?.compare_count ?? 0,
      compareCompletedCount,
      variantCount: variantRunIds.length,
      variantRunIds,
      lineageNotes,
      comparisons,
      studyCount: studies.length,
      studies,
    },
    operatorBoard: {
      decisionStatus: deliveryDecision?.decision_status ?? null,
      timelineEntryCount: runtime?.activity_timeline?.length ?? 0,
      deliveryDecision: {
        question: deliveryDecision?.decision_question_zh ?? null,
        optionCount: deliveryDecision?.options?.length ?? 0,
        options: decisionOptions,
        blockingReasons: deliveryDecision?.blocking_reason_lines ?? [],
        advisoryNotes: deliveryDecision?.advisory_note_lines ?? [],
      },
      remediation: {
        planStatus: remediationSummary?.plan_status ?? null,
        actionCount: remediationActions.length,
        actions: remediationActions,
        handoffStatus: remediationHandoff?.handoff_status ?? null,
        handoffToolName: remediationHandoff?.tool_name ?? null,
        manualActionCount: remediationManualActions.length,
        manualActions: remediationManualActions,
      },
      followup: {
        latestOutcomeStatus: followupSummary?.latest_outcome_status ?? null,
        latestToolName: followupSummary?.latest_tool_name ?? null,
        latestNotes: followupSummary?.latest_notes ?? [],
        historyVirtualPath: followupSummary?.history_virtual_path ?? null,
      },
    },
  };
}
