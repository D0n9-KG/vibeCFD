import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "@/components/workspace/submarine-runtime-panel.contract";

import {
  localizeWorkspaceDisplayText,
  localizeWorkspaceToolName,
} from "../../../core/i18n/workspace-display.ts";
import {
  buildSubmarineDeliveryDecisionSummary,
  buildSubmarineScientificFollowupSummary,
  buildSubmarineScientificRemediationSummary,
  buildSubmarineScientificRemediationHandoffSummary,
} from "../submarine-runtime-panel.utils.ts";

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
    lineageModeLabel: string | null;
    compareTargetRunIds: string[];
    followupSourceRunId: string | null;
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
    contract: {
      revisionLabel: string | null;
      iterationModeLabel: string | null;
      revisionSummary: string | null;
      capabilityGapCount: number;
      capabilityGapLabels: string[];
      unresolvedDecisionCount: number;
      unresolvedDecisionLabels: string[];
      evidenceExpectationCount: number;
      deliveryDeliveredCount: number;
      deliveryPlannedCount: number;
      deliveryBlockedCount: number;
      deliveryItems: Array<{
        outputId: string | null;
        label: string;
        statusLabel: string;
        detail: string | null;
      }>;
    };
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
      sourceRunId: string | null;
      baselineReferenceRunId: string | null;
      compareTargetRunId: string | null;
      derivedRunIds: string[];
      manualActionCount: number;
      manualActions: string[];
    };
    followup: {
      latestOutcomeStatus: string | null;
      latestToolName: string | null;
      latestSourceRunId: string | null;
      latestBaselineReferenceRunId: string | null;
      latestCompareTargetRunId: string | null;
      latestDerivedRunIds: string[];
      latestNotes: string[];
      historyVirtualPath: string | null;
    };
  };
};

export type BuildSubmarineDetailModelInput = {
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief?: SubmarineDesignBriefPayload | null;
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

function localizeIterationModeLabel(mode?: string | null): string | null {
  switch (mode) {
    case "baseline":
      return "基线";
    case "revise_baseline":
      return "修订基线";
    case "derive_variant":
      return "派生变体";
    case "followup":
      return "后续跟进";
    default:
      return mode ? localizeUserFacingLabel(mode, "待同步迭代模式") : null;
  }
}

const LEGACY_OPERATOR_STATUS_LABELS: Readonly<Record<string, string>> = {
  ready: "已就绪",
  pending: "待处理",
  needs_followup: "需要继续跟进",
};

function looksLikeInternalCode(value: string) {
  return /^[a-z0-9]+(?:[_-][a-z0-9]+)*$/.test(value.trim());
}

function localizeDisplayText(value?: string | null) {
  if (typeof value !== "string") {
    return null;
  }

  const localized = localizeWorkspaceDisplayText(value).trim();
  return localized.length > 0 ? localized : null;
}

function localizeRevisionSummary(value?: string | null) {
  if (typeof value !== "string" || value.trim().length === 0) {
    return null;
  }

  if (value.trim() === "Updated the structured CFD design brief.") {
    return "已更新结构化 CFD 设计简报。";
  }

  return value.trim();
}

const RUN_REFERENCE_PREFIX_LABELS: Readonly<Record<string, string>> = {
  mesh_independence: "网格无关性",
  domain_sensitivity: "计算域敏感性",
  time_step_sensitivity: "时间步敏感性",
  baseline: "基线",
  followup: "跟进",
};

const RUN_REFERENCE_VALUE_LABELS: Readonly<Record<string, string>> = {
  coarse: "粗",
  fine: "细",
  compact: "紧凑",
  expanded: "扩展",
  baseline: "基线",
};

function localizeRunReference(value?: string | null) {
  if (typeof value !== "string" || value.trim().length === 0) {
    return null;
  }

  const normalized = value.trim();
  if (normalized === "baseline") {
    return "基线";
  }

  const segments = normalized.split(":").filter((segment) => segment.length > 0);
  if (segments.length === 0) {
    return normalized;
  }

  return segments
    .map((segment, index) => {
      if (index === 0 && RUN_REFERENCE_PREFIX_LABELS[segment]) {
        return RUN_REFERENCE_PREFIX_LABELS[segment];
      }

      if (RUN_REFERENCE_VALUE_LABELS[segment]) {
        return RUN_REFERENCE_VALUE_LABELS[segment];
      }

      const localized = localizeWorkspaceDisplayText(segment).trim();
      if (localized === segment && /^followup-\d+$/i.test(segment)) {
        return segment.replace(/^followup-/i, "跟进-");
      }

      return localized || segment;
    })
    .join("：");
}

function localizeUserFacingLabel(
  value: string | null | undefined,
  genericFallback: string,
) {
  const localized = localizeDisplayText(value);
  if (!localized) {
    return genericFallback;
  }

  return looksLikeInternalCode(localized) ? genericFallback : localized;
}

function localizeList(values: Array<string | null | undefined>) {
  return values
    .map((value) => localizeDisplayText(value))
    .filter((value, index, all): value is string => Boolean(value) && all.indexOf(value) === index);
}

function localizeStatusFallback(value?: string | null) {
  if (typeof value !== "string" || value.trim().length === 0) {
    return null;
  }

  if (LEGACY_OPERATOR_STATUS_LABELS[value]) {
    return LEGACY_OPERATOR_STATUS_LABELS[value];
  }

  return looksLikeInternalCode(value)
    ? "状态待同步"
    : (localizeDisplayText(value) ?? "状态待同步");
}

function resolveStatusLabel({
  raw,
  localized,
}: {
  raw?: string | null;
  localized?: string | null;
}) {
  if (typeof localized === "string" && localized.trim().length > 0 && localized !== raw) {
    return localized.trim();
  }

  return localizeStatusFallback(raw ?? localized);
}

function resolveContractRecordLabel(item: Record<string, unknown> | null | undefined) {
  if (!item) {
    return null;
  }

  const candidates = [
    item.requested_label,
    item.label_zh,
    item.label,
    item.question_zh,
    item.output_id,
    item.decision_id,
  ];

  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.trim().length > 0) {
      return candidate.trim();
    }
  }

  return null;
}

function localizeDeliveryStatusLabel(status?: string | null) {
  switch (status) {
    case "delivered":
      return "已交付";
    case "planned":
    case "pending":
      return "待完成";
    case "not_yet_supported":
      return "暂不支持";
    case "not_available_for_this_run":
      return "本轮不可用";
    default:
      if (!status || status.trim().length === 0) {
        return "状态待同步";
      }

      return looksLikeInternalCode(status)
        ? "状态待同步"
        : (localizeDisplayText(status) ?? "状态待同步");
  }
}

export function buildSubmarineDetailModel({
  runtime,
  designBrief,
  finalReport,
}: BuildSubmarineDetailModelInput): SubmarineDetailModel {
  const contractRevision =
    finalReport?.contract_revision ??
    runtime?.contract_revision ??
    designBrief?.contract_revision ??
    null;
  const iterationMode =
    finalReport?.iteration_mode ??
    runtime?.iteration_mode ??
    designBrief?.iteration_mode ??
    null;
  const revisionSummary =
    finalReport?.revision_summary ??
    runtime?.revision_summary ??
    designBrief?.revision_summary ??
    null;
  const capabilityGaps =
    finalReport?.capability_gaps ??
    runtime?.capability_gaps ??
    designBrief?.capability_gaps ??
    [];
  const unresolvedDecisions =
    finalReport?.unresolved_decisions ??
    runtime?.unresolved_decisions ??
    designBrief?.unresolved_decisions ??
    [];
  const evidenceExpectations =
    finalReport?.evidence_expectations ??
    runtime?.evidence_expectations ??
    designBrief?.evidence_expectations ??
    [];
  const outputDeliveryPlan =
    finalReport?.output_delivery_plan ??
    runtime?.output_delivery_plan ??
    designBrief?.output_delivery_plan ??
    [];
  const experimentSummary = finalReport?.experiment_summary;
  const compareSummary = finalReport?.experiment_compare_summary;
  const studySummary = finalReport?.scientific_study_summary;
  const remediationSummary = finalReport?.scientific_remediation_summary;
  const remediationHandoff = finalReport?.scientific_remediation_handoff;
  const followupSummary = finalReport?.scientific_followup_summary;
  const deliveryDecision =
    finalReport?.delivery_decision_summary ?? runtime?.delivery_decision_summary;
  const deliveryDecisionView = buildSubmarineDeliveryDecisionSummary(
    finalReport ??
      (runtime
        ? {
            delivery_decision_summary: runtime.delivery_decision_summary,
            decision_status: runtime.decision_status,
          }
        : null),
  );
  const remediationView = buildSubmarineScientificRemediationSummary(finalReport);
  const remediationHandoffView =
    buildSubmarineScientificRemediationHandoffSummary(finalReport);
  const followupView = buildSubmarineScientificFollowupSummary(finalReport);
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
  const compareTargetRunIds = [
    ...(compareSummary?.comparisons?.map(
      (comparison) =>
        comparison?.compare_target_run_id ??
        comparison?.baseline_reference_run_id ??
        null,
    ) ?? []),
    remediationHandoff?.compare_target_run_id ?? null,
    followupSummary?.latest_compare_target_run_id ?? null,
  ].filter((id, index, all): id is string => Boolean(id) && all.indexOf(id) === index);
  const followupSourceRunId =
    followupSummary?.latest_source_run_id ?? remediationHandoff?.source_run_id ?? null;
  const decisionStatusLabel = resolveStatusLabel({
    raw: deliveryDecision?.decision_status ?? runtime?.decision_status ?? null,
    localized: deliveryDecisionView?.decisionStatusLabel ?? null,
  });
  const remediationHandoffStatusLabel = resolveStatusLabel({
    raw: remediationHandoff?.handoff_status ?? null,
    localized: remediationHandoffView?.handoffStatusLabel ?? null,
  });
  const remediationPlanStatusLabel = resolveStatusLabel({
    raw: remediationSummary?.plan_status ?? null,
    localized: remediationView?.planStatusLabel ?? null,
  });
  const followupOutcomeStatusLabel = resolveStatusLabel({
    raw: followupSummary?.latest_outcome_status ?? null,
    localized: followupView?.latestOutcomeLabel ?? null,
  });
  const remediationHandoffToolLabel = localizeWorkspaceToolName(
    remediationHandoffView?.toolName ?? remediationHandoff?.tool_name ?? "",
  ).trim();
  const followupToolLabel = localizeWorkspaceToolName(
    followupView?.latestToolName ?? followupSummary?.latest_tool_name ?? "",
  ).trim();
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
      label: localizeDisplayText(study?.summary_label) ?? "未命名科研研究",
      workflowStatus: study?.workflow_status ?? "pending",
    })) ?? [];
  const remediationActions =
    remediationSummary?.actions?.map(
      (action) => localizeDisplayText(action?.title) ?? "未命名修正事项",
    ) ?? [];
  const remediationManualActions =
    remediationHandoff?.manual_actions?.map(
      (action) => localizeDisplayText(action?.title) ?? "未命名人工确认事项",
    ) ?? [];
  const decisionOptions =
    deliveryDecision?.options?.map(
      (option) =>
        localizeUserFacingLabel(option?.label_zh ?? option?.option_id, "待确认路径"),
    ) ?? [];
  const deliveryDeliveredCount = outputDeliveryPlan.filter(
    (item) => item?.delivery_status === "delivered",
  ).length;
  const deliveryPlannedCount = outputDeliveryPlan.filter(
    (item) => item?.delivery_status === "planned" || item?.delivery_status === "pending",
  ).length;
  const deliveryBlockedCount = outputDeliveryPlan.filter(
    (item) =>
      item?.delivery_status === "not_yet_supported" ||
      item?.delivery_status === "not_available_for_this_run",
  ).length;
  const capabilityGapLabels = capabilityGaps
    .map((item) => localizeUserFacingLabel(resolveContractRecordLabel(item), "未命名研究项"))
    .filter((label, index, all): label is string => Boolean(label) && all.indexOf(label) === index);
  const unresolvedDecisionLabels = unresolvedDecisions
    .map((item) => localizeUserFacingLabel(resolveContractRecordLabel(item), "未命名研究项"))
    .filter((label, index, all): label is string => Boolean(label) && all.indexOf(label) === index);
  const deliveryItems = outputDeliveryPlan
    .map((item) => {
      const label =
        (typeof item?.label === "string" && item.label.trim().length > 0
          ? localizeUserFacingLabel(item.label, "未命名输出项")
          : null) ??
        (typeof item?.output_id === "string" && item.output_id.trim().length > 0
          ? localizeUserFacingLabel(item.output_id, "未命名输出项")
          : null) ??
        "未命名输出项";

      return {
        outputId:
          typeof item?.output_id === "string" && item.output_id.trim().length > 0
            ? item.output_id.trim()
            : null,
        label,
        statusLabel: localizeDeliveryStatusLabel(item?.delivery_status),
        detail: localizeDisplayText(item?.detail),
      };
    })
    .filter(
      (item, index, all) =>
        all.findIndex(
          (candidate) =>
            candidate.outputId === item.outputId &&
            candidate.label === item.label &&
            candidate.statusLabel === item.statusLabel &&
            candidate.detail === item.detail,
        ) === index,
    );

  return {
    trustPanels: [
      createTrustPanel(
        "provenance",
        "来源链路",
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
        "复现能力",
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
        "环境一致性",
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
        "科学交付门",
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
        "对比试验",
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
        "修正方案",
        Boolean(remediationSummary ?? remediationHandoff),
        [
          remediationPlanStatusLabel,
          remediationHandoffStatusLabel,
          remediationHandoffToolLabel,
        ]
          .filter(Boolean)
          .join(" | ") || null,
      ),
      createTrustPanel(
        "follow-up",
        "后续研究",
        Boolean(followupSummary),
        [
          followupOutcomeStatusLabel,
          followupToolLabel,
          ...localizeList(followupSummary?.latest_notes ?? []),
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
      lineageModeLabel: localizeIterationModeLabel(iterationMode),
      compareTargetRunIds,
      followupSourceRunId: localizeRunReference(followupSourceRunId),
      lineageNotes,
      comparisons,
      studyCount: studies.length,
      studies,
    },
    operatorBoard: {
      decisionStatus: decisionStatusLabel,
      timelineEntryCount: runtime?.activity_timeline?.length ?? 0,
      contract: {
        revisionLabel:
          typeof contractRevision === "number" ? `r${contractRevision}` : null,
        iterationModeLabel: localizeIterationModeLabel(iterationMode),
        revisionSummary: localizeRevisionSummary(revisionSummary),
        capabilityGapCount: capabilityGaps.length,
        capabilityGapLabels,
        unresolvedDecisionCount: unresolvedDecisions.length,
        unresolvedDecisionLabels,
        evidenceExpectationCount: evidenceExpectations.length,
        deliveryDeliveredCount,
        deliveryPlannedCount,
        deliveryBlockedCount,
        deliveryItems,
      },
      deliveryDecision: {
        question: localizeDisplayText(deliveryDecision?.decision_question_zh),
        optionCount: deliveryDecision?.options?.length ?? 0,
        options: decisionOptions,
        blockingReasons: localizeList(deliveryDecision?.blocking_reason_lines ?? []),
        advisoryNotes: localizeList(deliveryDecision?.advisory_note_lines ?? []),
      },
      remediation: {
        planStatus: remediationPlanStatusLabel,
        actionCount: remediationActions.length,
        actions: remediationActions,
        handoffStatus: remediationHandoffStatusLabel,
        handoffToolName:
          remediationHandoffToolLabel.length > 0 ? remediationHandoffToolLabel : null,
        sourceRunId: localizeRunReference(remediationHandoff?.source_run_id),
        baselineReferenceRunId:
          localizeRunReference(remediationHandoff?.baseline_reference_run_id),
        compareTargetRunId: localizeRunReference(remediationHandoff?.compare_target_run_id),
        derivedRunIds: (remediationHandoff?.derived_run_ids ?? [])
          .map((runId) => localizeRunReference(runId))
          .filter((runId): runId is string => Boolean(runId)),
        manualActionCount: remediationManualActions.length,
        manualActions: remediationManualActions,
      },
      followup: {
        latestOutcomeStatus: followupOutcomeStatusLabel,
        latestToolName: followupToolLabel.length > 0 ? followupToolLabel : null,
        latestSourceRunId: localizeRunReference(followupSummary?.latest_source_run_id),
        latestBaselineReferenceRunId:
          localizeRunReference(followupSummary?.latest_baseline_reference_run_id),
        latestCompareTargetRunId:
          localizeRunReference(followupSummary?.latest_compare_target_run_id),
        latestDerivedRunIds: (followupSummary?.latest_derived_run_ids ?? [])
          .map((runId) => localizeRunReference(runId))
          .filter((runId): runId is string => Boolean(runId)),
        latestNotes: localizeList(followupSummary?.latest_notes ?? []),
        historyVirtualPath:
          followupSummary?.history_virtual_path ??
          runtime?.scientific_followup_history_virtual_path ??
          null,
      },
    },
  };
}
