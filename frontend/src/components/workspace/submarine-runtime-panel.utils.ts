import type {
  SubmarineDeliveryDecisionSummaryPayload,
  SubmarineDesignBriefPayload,
  SubmarineExecutionOutlineItem,
  SubmarineFinalReportPayload,
  SubmarineOutputDeliveryPlanItem,
  SubmarineRequestedOutputPayload,
  SubmarineRuntimeSnapshotPayload,
} from "./submarine-runtime-panel.contract";

export type SubmarineArtifactGroupId =
  | "planning"
  | "report"
  | "results"
  | "execution"
  | "inspection"
  | "other";

export type SubmarineArtifactGroup = {
  id: SubmarineArtifactGroupId;
  label: string;
  count: number;
  paths: string[];
};

export type SubmarineArtifactFilterId = SubmarineArtifactGroupId | "all";

export type SubmarineArtifactFilterOption = {
  id: SubmarineArtifactFilterId;
  label: string;
  count: number;
};

export type SubmarineStageTrackItem = {
  stageId: string;
  label: string;
  status: string;
};

export type SubmarineArtifactMeta = {
  label: string;
  externalLinkLabel: string;
};

export type SubmarineDesignBriefSummary = {
  confirmationStatusLabel: string;
  precomputeApprovalLabel: string;
  pendingCalculationPlanCount: number;
  immediateClarificationCount: number;
  expectedOutputs: string[];
  scientificVerificationRequirements: Array<{
    requirementId: string;
    label: string;
    checkType: string;
    detail: string;
  }>;
  requestedOutputs: Array<{
    outputId: string;
    label: string;
    requestedLabel: string;
    supportLevel: string;
    specSummary: string;
    notes: string;
  }>;
  userConstraints: string[];
  openQuestions: string[];
  executionOutline: Array<{
    roleId: string;
    roleLabel: string;
    owner: string;
    goal: string;
    status: string;
    targetSkills: string[];
  }>;
  calculationPlan: Array<{
    itemId: string;
    category: string;
    label: string;
    proposedValue: string;
    sourceLabel: string;
    sourceUrl: string;
    confidenceLabel: string;
    applicabilityConditions: string[];
    evidenceGapNote: string;
    originLabel: string;
    approvalState: string;
    approvalStateLabel: string;
    requiresImmediateConfirmation: boolean;
    researcherNote: string;
  }>;
  requirementPairs: Array<{
    label: string;
    value: string;
  }>;
};

export type SubmarineScientificVerificationSummary = {
  statusLabel: string;
  confidenceLabel: string;
  blockingIssues: string[];
  missingEvidence: string[];
  passedRequirements: string[];
  requirements: Array<{
    requirementId: string;
    label: string;
    status: string;
    detail: string;
  }>;
};

export type SubmarineStabilityEvidenceSummary = {
  statusLabel: string;
  summary: string;
  solverResultsPath: string;
  artifactPath: string;
  residualMaxFinalValue: string;
  tailCoefficientLabel: string;
  tailStatusLabel: string;
  tailSpreadLabel: string;
  tailSampleCountLabel: string;
  blockingIssues: string[];
  missingEvidence: string[];
  passedRequirements: string[];
  requirementLines: string[];
};

export type SubmarineScientificStudySummary = {
  executionStatusLabel: string;
  workflowStatusLabel: string;
  studyStatusCountLines: string[];
  manifestPath: string;
  artifactPaths: string[];
  studies: Array<{
    studyType: string;
    summaryLabel: string;
    monitoredQuantity: string;
    variantCount: number;
    studyExecutionStatusLabel: string;
    workflowStatusLabel: string;
    workflowDetail: string;
    variantStatusCountLines: string[];
    compareStatusCountLines: string[];
    expectedVariantRunIds: string[];
    plannedVariantRunIds: string[];
    inProgressVariantRunIds: string[];
    completedVariantRunIds: string[];
    blockedVariantRunIds: string[];
    plannedCompareVariantRunIds: string[];
    completedCompareVariantRunIds: string[];
    blockedCompareVariantRunIds: string[];
    missingMetricsVariantRunIds: string[];
    verificationStatus: string;
    verificationDetail: string;
  }>;
};

export type SubmarineExperimentSummary = {
  experimentId: string;
  experimentStatusLabel: string;
  workflowStatusLabel: string;
  workflowDetail: string;
  baselineRunId: string;
  runCount: number;
  compareCount: number;
  manifestPath: string;
  studyManifestPath: string;
  comparePath: string;
  artifactPaths: string[];
  linkageStatus: string;
  linkageIssueCount: number;
  linkageIssues: string[];
  runStatusCountLines: string[];
  compareStatusCountLines: string[];
  expectedVariantRunIds: string[];
  registeredCustomVariantRunIds: string[];
  missingVariantRunRecordIds: string[];
  missingCompareEntryIds: string[];
  plannedCustomVariantRunIds: string[];
  completedCustomVariantRunIds: string[];
  missingCustomCompareEntryIds: string[];
  blockedVariantRunIds: string[];
  plannedVariantRunIds: string[];
  missingMetricsVariantRunIds: string[];
  compareNotes: string[];
};

export type SubmarineExperimentCompareSummary = {
  experimentId: string;
  baselineRunId: string;
  compareCount: number;
  comparePath: string;
  workflowStatusLabel: string;
  compareStatusCountLines: string[];
  plannedCandidateRunIds: string[];
  completedCandidateRunIds: string[];
  blockedCandidateRunIds: string[];
  missingMetricsCandidateRunIds: string[];
  artifactPaths: string[];
  comparisons: Array<{
    candidateRunId: string;
    runRole: string;
    variantOrigin: string;
    studyType: string;
    variantId: string;
    variantLabel: string;
    studyLabel: string;
    lineageLabel: string;
    baselineReferenceRunId: string;
    compareTargetRunId: string;
    isCustomVariant: boolean;
    compareStatus: string;
    compareStatusLabel: string;
    candidateExecutionStatusLabel: string;
    notes: string;
    metricDeltaLines: string[];
    baselineSolverResultsPath: string;
    candidateSolverResultsPath: string;
    baselineRunRecordPath: string;
    candidateRunRecordPath: string;
    artifactPaths: string[];
  }>;
};

export type SubmarineFigureDeliverySummary = {
  figureCount: number;
  manifestPath: string;
  artifactPaths: string[];
  figures: Array<{
    figureId: string;
    outputId: string;
    title: string;
    caption: string;
    renderStatus: string;
    renderStatusLabel: string;
    selectorSummary: string;
    field: string;
    artifactPaths: string[];
    sourceCsvPath: string;
  }>;
};

export type SubmarineResearchEvidenceSummary = {
  readinessStatus: string;
  verificationStatus: string;
  validationStatus: string;
  provenanceStatus: string;
  readinessLabel: string;
  verificationStatusLabel: string;
  validationStatusLabel: string;
  provenanceStatusLabel: string;
  confidenceLabel: string;
  blockingIssues: string[];
  evidenceGaps: string[];
  passedEvidence: string[];
  benchmarkHighlights: string[];
  provenanceHighlights: string[];
  artifactPaths: string[];
};

export type SubmarineReproducibilitySummary = {
  manifestPath: string;
  profileId: string;
  profileLabel: string;
  parityStatus: string;
  reproducibilityStatus: string;
  parityStatusLabel: string;
  reproducibilityStatusLabel: string;
  driftReasons: string[];
  recoveryGuidance: string[];
};

export type SubmarineScientificGateSummary = {
  gateStatus: string;
  allowedClaimLevel: string;
  sourceReadinessStatus: string;
  recommendedStage: string;
  remediationStage: string;
  gateStatusLabel: string;
  allowedClaimLevelLabel: string;
  sourceReadinessLabel: string;
  recommendedStageLabel: string;
  remediationStageLabel: string;
  blockingReasons: string[];
  advisoryNotes: string[];
  artifactPaths: string[];
};

export type SubmarineScientificRemediationSummary = {
  planStatusLabel: string;
  currentClaimLevelLabel: string;
  targetClaimLevelLabel: string;
  recommendedStageLabel: string;
  artifactPaths: string[];
  actions: Array<{
    actionId: string;
    title: string;
    summary: string;
    ownerStage: string;
    ownerStageLabel: string;
    priority: string;
    executionMode: string;
    executionModeLabel: string;
    status: string;
    statusLabel: string;
    evidenceGap: string;
    requiredArtifacts: string[];
  }>;
};

export type SubmarineScientificRemediationHandoffSummary = {
  handoffStatusLabel: string;
  recommendedActionId: string;
  toolName: string;
  reason: string;
  artifactPaths: string[];
  toolArgs: Array<{
    key: string;
    value: string;
  }>;
  manualActions: Array<{
    actionId: string;
    title: string;
    ownerStage: string;
    ownerStageLabel: string;
    evidenceGap: string;
  }>;
};

export type SubmarineDeliveryDecisionSummary = {
  decisionStatus: string;
  decisionStatusLabel: string;
  question: string;
  chatPrompt: string;
  recommendedOptionId: string;
  recommendedOptionLabel: string;
  options: Array<{
    optionId: string;
    label: string;
    summary: string;
    followupKind: string;
    followupKindLabel: string;
    requiresAdditionalExecution: boolean;
  }>;
  blockingReasons: string[];
  advisoryNotes: string[];
  artifactPaths: string[];
};

export type SubmarineScientificFollowupSummary = {
  entryCount: number;
  latestOutcomeLabel: string;
  latestHandoffStatusLabel: string;
  latestRecommendedActionId: string;
  latestToolName: string;
  latestFollowupKind: string;
  latestFollowupKindLabel: string;
  latestDecisionSummary: string;
  latestSourceConclusionIds: string[];
  latestSourceEvidenceGapIds: string[];
  latestDispatchStageStatusLabel: string;
  reportRefreshedLabel: string;
  historyPath: string;
  latestResultReportPath: string;
  latestResultProvenanceManifestPath: string;
  latestResultHandoffPath: string;
  latestNotes: string[];
  artifactPaths: string[];
};

export type SubmarineReportOverviewSummary = {
  currentConclusion: string;
  allowedClaimLevel: string;
  allowedClaimLevelLabel: string;
  reviewStatus: string;
  reviewStatusLabel: string;
  reproducibilityStatus: string;
  reproducibilityStatusLabel: string;
  recommendedNextStep: string;
};

export type SubmarineConclusionSectionSummary = {
  conclusionId: string;
  title: string;
  summary: string;
  claimLevel: string;
  claimLevelLabel: string;
  confidenceLabel: string;
  inlineSourceRefs: string[];
  evidenceGapNotes: string[];
  artifactPaths: string[];
};

export type SubmarineEvidenceIndexSummary = {
  groupCount: number;
  groups: Array<{
    groupId: string;
    groupTitle: string;
    artifactPaths: string[];
    provenanceManifestPath: string;
  }>;
};

export type SubmarineAcceptanceSummary = {
  statusLabel: string;
  confidenceLabel: string;
  blockingIssues: string[];
  warnings: string[];
  passedChecks: string[];
  outputDelivery: SubmarineOutputDeliverySummaryItem[];
  benchmarkComparisons: Array<{
    metricId: string;
    quantity: string;
    status: string;
    statusLabel: string;
    summary: string;
    detail: string;
    observedValue: string;
    referenceValue: string;
    absoluteError: string;
    relativeError: string;
    relativeTolerance: string;
    targetVelocity: string;
    observedVelocity: string;
    sourceLabel: string;
    sourceUrl: string;
  }>;
};

export type SubmarineOutputDeliverySummaryItem = {
  outputId: string;
  label: string;
  deliveryStatus: string;
  specSummary: string;
  detail: string;
  artifactPaths: string[];
};

export type SubmarineResultCardArtifact = {
  path: string;
  label: string;
  externalLinkLabel: string;
};

export type SubmarineResultCard = {
  outputId: string;
  label: string;
  requestedLabel: string;
  supportLevel: string;
  deliveryStatus: string;
  specSummary: string;
  detail: string;
  figureCaption: string;
  selectorSummary: string;
  figureRenderStatus: string;
  previewArtifactPath: string | null;
  artifactPaths: string[];
  figureArtifactPaths: string[];
  artifacts: SubmarineResultCardArtifact[];
};

const GROUP_ORDER: SubmarineArtifactGroupId[] = [
  "planning",
  "report",
  "results",
  "execution",
  "inspection",
  "other",
];

const GROUP_LABELS: Record<SubmarineArtifactGroupId, string> = {
  planning: "方案设计",
  report: "报告交付",
  results: "结果数据",
  execution: "执行记录",
  inspection: "前处理与检查",
  other: "其他产物",
};

const ACCEPTANCE_STATUS_LABELS: Record<string, string> = {
  ready_for_review: "待复核",
  blocked: "已阻断",
};

const ACCEPTANCE_CONFIDENCE_LABELS: Record<string, string> = {
  high: "高",
  medium: "中",
  low: "低",
};

const CALCULATION_PLAN_APPROVAL_LABELS: Record<string, string> = {
  pending_researcher_confirmation: "Pending Researcher Confirmation",
  researcher_confirmed: "Researcher Confirmed",
};

const CALCULATION_PLAN_ORIGIN_LABELS: Record<string, string> = {
  user_input: "User Input",
  ai_suggestion: "AI Suggestion",
  researcher_edit: "Researcher Edit",
};

const CALCULATION_PLAN_CONFIDENCE_LABELS: Record<string, string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
};

const SCIENTIFIC_VERIFICATION_STATUS_LABELS: Record<string, string> = {
  research_ready: "Research Ready",
  needs_more_verification: "Needs More Verification",
  blocked: "Blocked",
};

const STABILITY_EVIDENCE_STATUS_LABELS: Record<string, string> = {
  passed: "Passed",
  missing_evidence: "Missing Evidence",
  blocked: "Blocked",
};

const SCIENTIFIC_VERIFICATION_CONFIDENCE_LABELS: Record<string, string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
};

const SCIENTIFIC_STUDY_EXECUTION_STATUS_LABELS: Record<string, string> = {
  planned: "Planned",
  in_progress: "In Progress",
  partial: "Partial",
  completed: "Completed",
  blocked: "Blocked",
};

const EXPERIMENT_STATUS_LABELS: Record<string, string> = {
  planned: "Planned",
  partial: "Partial",
  completed: "Completed",
  blocked: "Blocked",
};

const EXPERIMENT_COMPARE_STATUS_LABELS: Record<string, string> = {
  planned: "Planned",
  completed: "Completed",
  missing_metrics: "Missing Metrics",
  blocked: "Blocked",
};

const FIGURE_RENDER_STATUS_LABELS: Record<string, string> = {
  rendered: "Rendered",
  skipped: "Skipped",
  blocked: "Blocked",
};

const RESEARCH_EVIDENCE_READINESS_LABELS: Record<string, string> = {
  blocked: "Blocked",
  insufficient_evidence: "Insufficient Evidence",
  verified_but_not_validated: "Verified But Not Validated",
  validated_with_gaps: "Validated With Gaps",
  research_ready: "Research Ready",
};

const RESEARCH_EVIDENCE_DIMENSION_LABELS: Record<string, string> = {
  passed: "Passed",
  needs_more_verification: "Needs More Verification",
  validated: "Validated",
  missing_validation_reference: "Missing Validation Reference",
  validation_failed: "Validation Failed",
  blocked: "Blocked",
  traceable: "Traceable",
  partial: "Partial",
  missing: "Missing",
  high: "High",
  medium: "Medium",
  low: "Low",
};

const REPRODUCIBILITY_STATUS_LABELS: Record<string, string> = {
  matched: "Matched",
  drifted_but_runnable: "Drifted But Runnable",
  unknown: "Unknown Environment Profile",
  blocked: "Blocked Runtime Parity",
};

const REPORT_REVIEW_STATUS_LABELS: Record<string, string> = {
  ready_for_supervisor: "Ready For Supervisor",
  needs_user_confirmation: "Needs User Confirmation",
  blocked: "Blocked",
};

const SCIENTIFIC_GATE_STATUS_LABELS: Record<string, string> = {
  ready_for_claim: "Ready For Claim",
  claim_limited: "Claim Limited",
  blocked: "Blocked",
};

const BENCHMARK_COMPARISON_STATUS_LABELS: Record<string, string> = {
  passed: "Passed",
  blocked: "Blocked",
  warning: "Warning",
  not_applicable: "Not Applicable",
};

const SCIENTIFIC_CLAIM_LEVEL_LABELS: Record<string, string> = {
  delivery_only: "Delivery Only",
  verified_but_not_validated: "Verified But Not Validated",
  validated_with_gaps: "Validated With Gaps",
  research_ready: "Research Ready",
};

const SCIENTIFIC_GATE_STAGE_LABELS: Record<string, string> = {
  "task-intelligence": "Task Intelligence",
  "geometry-preflight": "Geometry Preflight",
  "user-confirmation": "Researcher Confirmation",
  "solver-dispatch": "Solver Dispatch",
  "scientific-study": "Scientific Study",
  "experiment-compare": "Experiment Compare",
  "scientific-verification": "Scientific Verification",
  "result-reporting": "Result Reporting",
  "scientific-followup": "Scientific Follow-Up",
  "supervisor-review": "Supervisor Review",
};

const EXECUTION_ROLE_LABELS: Record<string, string> = {
  "claude-code-supervisor": "Claude Code Supervisor",
  "task-intelligence": "Task Intelligence",
  "geometry-preflight": "Geometry Preflight",
  "solver-dispatch": "Solver Dispatch",
  "scientific-study": "Scientific Study",
  "experiment-compare": "Experiment Compare",
  "scientific-verification": "Scientific Verification",
  "result-reporting": "Result Reporting",
  "scientific-followup": "Scientific Follow-Up",
  "supervisor-review": "Supervisor Review",
};

const LEGACY_STAGE_TRACK_ORDER = [
  "task-intelligence",
  "geometry-preflight",
  "solver-dispatch",
  "result-reporting",
  "supervisor-review",
] as const;

const SCIENTIFIC_REMEDIATION_PLAN_STATUS_LABELS: Record<string, string> = {
  not_needed: "Not Needed",
  recommended: "Recommended",
  blocked: "Blocked",
};

const SCIENTIFIC_REMEDIATION_EXECUTION_MODE_LABELS: Record<string, string> = {
  auto_executable: "Auto Executable",
  manual_required: "Manual Required",
};

const SCIENTIFIC_REMEDIATION_ACTION_STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  not_needed: "Not Needed",
};

const SCIENTIFIC_REMEDIATION_HANDOFF_STATUS_LABELS: Record<string, string> = {
  ready_for_auto_followup: "Ready For Auto Follow-Up",
  manual_followup_required: "Manual Follow-Up Required",
  not_needed: "Not Needed",
};

const DELIVERY_DECISION_STATUS_LABELS: Record<string, string> = {
  ready_for_user_decision: "Ready For User Decision",
  needs_more_evidence: "Needs More Evidence",
  blocked_by_setup: "Blocked By Setup",
};

const DELIVERY_DECISION_FOLLOWUP_KIND_LABELS: Record<string, string> = {
  evidence_supplement: "Evidence Supplement",
  parameter_correction: "Parameter Correction",
  study_extension: "Study Extension",
  task_complete: "Task Complete",
};

const DELIVERY_DECISION_CHAT_PROMPT = "请在聊天中确认下一步。";

const SCIENTIFIC_FOLLOWUP_OUTCOME_LABELS: Record<string, string> = {
  error: "Error",
  invalid_tool_args: "Invalid Tool Args",
  manual_followup_required: "Manual Follow-Up Required",
  not_needed: "Not Needed",
  unsupported_target: "Unsupported Target",
  result_report_refreshed: "Result Report Refreshed",
  dispatch_planned: "Dispatch Planned",
  dispatch_failed: "Dispatch Failed",
  dispatch_refreshed_report: "Dispatch Refreshed Report",
};

const SCIENTIFIC_FOLLOWUP_KIND_LABELS: Record<string, string> = {
  evidence_supplement: "补充证据",
  parameter_correction: "修正参数",
  study_extension: "扩展研究",
  task_complete: "任务完成",
};

const DISPATCH_STAGE_STATUS_LABELS: Record<string, string> = {
  executed: "Executed",
  planned: "Planned",
  failed: "Failed",
};

const RESULT_CARD_ARTIFACT_SUFFIXES: Record<string, string[]> = {
  drag_coefficient: ["/solver-results.json", "/final-report.json"],
  force_breakdown: ["/solver-results.json", "/final-report.json"],
  mesh_quality_summary: [
    "/solver-results.json",
    "/geometry-check.json",
    "/geometry-check.md",
  ],
  residual_history: ["/solver-results.json", "/openfoam-run.log"],
  benchmark_comparison: [
    "/delivery-readiness.json",
    "/final-report.json",
    "/final-report.md",
  ],
  chinese_report: ["/final-report.md", "/final-report.html", "/final-report.json"],
  surface_pressure_contour: [
    "/surface-pressure.png",
    "/surface-pressure.csv",
    "/surface-pressure.md",
  ],
  wake_velocity_slice: [
    "/wake-velocity-slice.png",
    "/wake-velocity-slice.csv",
    "/wake-velocity-slice.md",
  ],
};

function formatSpecNumber(value: number) {
  if (!Number.isFinite(value)) {
    return "--";
  }
  if (Number.isInteger(value)) {
    return `${value}`;
  }
  return value.toFixed(4).replace(/\.?0+$/, "");
}

function formatCompareMetricValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value)
    ? formatSpecNumber(value)
    : "--";
}

function formatCompareMetricRelativeDelta(value: unknown) {
  return typeof value === "number" && Number.isFinite(value)
    ? `${(value * 100).toFixed(2)}%`
    : "--";
}

function formatStatusLabel(
  value: string | null | undefined,
  labels: Record<string, string>,
) {
  return labels[value ?? ""] ?? value ?? "--";
}

function formatStatusCountLines(
  counts: Record<string, unknown> | null | undefined,
  labels: Record<string, string>,
) {
  if (!counts || typeof counts !== "object") {
    return [];
  }

  return Object.entries(counts).flatMap(([status, rawCount]) => {
    if (typeof rawCount !== "number" || !Number.isFinite(rawCount)) {
      return [];
    }
    return [`${formatStatusLabel(status, labels)}: ${rawCount}`];
  });
}

function isCustomVariantEntry(
  item:
    | {
        run_role?: string | null;
        variant_origin?: string | null;
        candidate_run_id?: string | null;
      }
    | null
    | undefined,
) {
  const runRole = item?.run_role ?? item?.variant_origin ?? "";
  const candidateRunId = item?.candidate_run_id ?? "";
  return runRole === "custom_variant" || candidateRunId.startsWith("custom:");
}

function formatExperimentCompareStudyLabel(
  item:
    | {
        run_role?: string | null;
        variant_origin?: string | null;
        candidate_run_id?: string | null;
        study_type?: string | null;
        variant_id?: string | null;
      }
    | null
    | undefined,
) {
  const variantId = item?.variant_id ?? "unknown";
  if (isCustomVariantEntry(item)) {
    return `custom / ${variantId}`;
  }
  const studyType = item?.study_type ?? "unknown";
  return `${studyType} / ${variantId}`;
}

function formatExperimentLineageLabel(
  item:
    | {
        run_role?: string | null;
        variant_origin?: string | null;
        candidate_run_id?: string | null;
        variant_label?: string | null;
        variant_id?: string | null;
      }
    | null
    | undefined,
) {
  if (isCustomVariantEntry(item)) {
    return `Custom Variant | ${item?.variant_label ?? item?.variant_id ?? "unknown"}`;
  }
  return formatExperimentCompareStudyLabel(item);
}

function formatCompareMetricDeltaLines(metricDeltas: unknown) {
  if (!metricDeltas || typeof metricDeltas !== "object") {
    return [];
  }

  return Object.entries(metricDeltas).flatMap(([metricName, payload]) => {
    if (!payload || typeof payload !== "object") {
      return [];
    }

    const metric = payload as {
      baseline_value?: unknown;
      candidate_value?: unknown;
      absolute_delta?: unknown;
      relative_delta?: unknown;
    };

    return [
      `${metricName}: baseline=${formatCompareMetricValue(metric.baseline_value)} | candidate=${formatCompareMetricValue(metric.candidate_value)} | delta=${formatCompareMetricValue(metric.absolute_delta)} | relative=${formatCompareMetricRelativeDelta(metric.relative_delta)}`,
    ];
  });
}

function formatPostprocessSpecSummary(
  spec: Record<string, unknown> | null | undefined,
) {
  if (!spec || typeof spec !== "object") {
    return "--";
  }

  const parts: string[] = [];
  const field = typeof spec.field === "string" ? spec.field : null;
  if (field) {
    parts.push(`field=${field}`);
  }

  const selector =
    spec.selector && typeof spec.selector === "object"
      ? (spec.selector as Record<string, unknown>)
      : null;
  if (selector) {
    if (selector.type === "patch") {
      const patches = Array.isArray(selector.patches)
        ? selector.patches.filter((item): item is string => typeof item === "string")
        : [];
      parts.push(
        patches.length > 0
          ? `selector=patch[${patches.join(",")}]`
          : "selector=patch",
      );
    } else if (selector.type === "plane") {
      const originMode =
        typeof selector.origin_mode === "string" ? selector.origin_mode : null;
      const originValue =
        typeof selector.origin_value === "number" ? selector.origin_value : null;
      let originSummary = "origin=--";
      if (originMode === "x_by_lref" && originValue !== null) {
        originSummary = `x/Lref=${formatSpecNumber(originValue)}`;
      } else if (originMode === "x_absolute_m" && originValue !== null) {
        originSummary = `x=${formatSpecNumber(originValue)}m`;
      } else if (originValue !== null) {
        originSummary = `origin=${formatSpecNumber(originValue)}`;
      }
      const normal =
        Array.isArray(selector.normal) &&
        selector.normal.length === 3 &&
        selector.normal.every((item) => typeof item === "number")
          ? `; normal=(${selector.normal
              .map((item) => formatSpecNumber(item))
              .join(", ")})`
          : "";
      parts.push(`selector=plane[${originSummary}${normal}]`);
    }
  }

  const timeMode = typeof spec.time_mode === "string" ? spec.time_mode : null;
  if (timeMode) {
    parts.push(`time=${timeMode}`);
  }

  const formats = Array.isArray(spec.formats)
    ? spec.formats.filter((item): item is string => typeof item === "string")
    : [];
  if (formats.length > 0) {
    parts.push(`formats=${formats.join(",")}`);
  }

  return parts.length > 0 ? parts.join("; ") : "--";
}

function formatVerificationRequirementDetail(
  requirement:
    | {
        required_artifacts?: string[] | null;
        force_coefficient?: string | null;
        minimum_history_samples?: number | null;
        max_tail_relative_spread?: number | null;
        max_value?: number | null;
      }
    | null
    | undefined,
) {
  if (!requirement) {
    return "--";
  }

  const parts: string[] = [];
  const requiredArtifacts = requirement.required_artifacts?.filter(Boolean) ?? [];
  if (requiredArtifacts.length > 0) {
    parts.push(`artifacts=${requiredArtifacts.join(",")}`);
  }
  if (requirement.force_coefficient) {
    parts.push(`force_coefficient=${requirement.force_coefficient}`);
  }
  if (typeof requirement.minimum_history_samples === "number") {
    parts.push(`min_samples=${requirement.minimum_history_samples}`);
  }
  if (typeof requirement.max_tail_relative_spread === "number") {
    parts.push(
      `max_tail_relative_spread=${requirement.max_tail_relative_spread.toFixed(4)}`,
    );
  }
  if (typeof requirement.max_value === "number") {
    parts.push(`max_value=${requirement.max_value.toFixed(6)}`);
  }

  return parts.length > 0 ? parts.join("; ") : "--";
}

const ARTIFACT_COPY: Array<[pattern: string, meta: SubmarineArtifactMeta]> = [
  [
    "/skill-draft.json",
    {
      label: "Skill 草稿 JSON",
      externalLinkLabel: "在新窗口打开 Skill 草稿 JSON",
    },
  ],
  [
    "/SKILL.md",
    {
      label: "Skill 草稿 Markdown",
      externalLinkLabel: "在新窗口打开 Skill 草稿 Markdown",
    },
  ],
  [
    "/validation-report.md",
    {
      label: "Skill 校验报告",
      externalLinkLabel: "在新窗口打开 Skill 校验报告",
    },
  ],
  [
    "/validation-report.html",
    {
      label: "Skill 校验报告 HTML",
      externalLinkLabel: "在新窗口打开 Skill 校验报告 HTML",
    },
  ],
  [
    "/validation-report.json",
    {
      label: "Skill 校验报告 JSON",
      externalLinkLabel: "在新窗口打开 Skill 校验报告 JSON",
    },
  ],
  [
    "/references/domain-rules.md",
    {
      label: "领域规则参考",
      externalLinkLabel: "在新窗口打开领域规则参考",
    },
  ],
  [
    "/cfd-design-brief.md",
    {
      label: "CFD 设计简报",
      externalLinkLabel: "在新窗口打开 CFD 设计简报",
    },
  ],
  [
    "/cfd-design-brief.html",
    {
      label: "CFD 设计简报 HTML",
      externalLinkLabel: "在新窗口打开 CFD 设计简报 HTML",
    },
  ],
  [
    "/cfd-design-brief.json",
    {
      label: "CFD 设计简报 JSON",
      externalLinkLabel: "在新窗口打开 CFD 设计简报 JSON",
    },
  ],
  [
    "/study-plan.json",
    {
      label: "Scientific Study Plan JSON",
      externalLinkLabel: "Open scientific study plan JSON in a new window",
    },
  ],
  [
    "/study-manifest.json",
    {
      label: "Scientific Study Manifest JSON",
      externalLinkLabel: "Open scientific study manifest JSON in a new window",
    },
  ],
  [
    "/experiment-manifest.json",
    {
      label: "Experiment Manifest JSON",
      externalLinkLabel: "Open experiment manifest JSON in a new window",
    },
  ],
  [
    "/figure-manifest.json",
    {
      label: "Figure Manifest JSON",
      externalLinkLabel: "Open figure manifest JSON in a new window",
    },
  ],
  [
    "/run-compare-summary.json",
    {
      label: "Run Compare Summary JSON",
      externalLinkLabel: "Open run compare summary JSON in a new window",
    },
  ],
  [
    "/run-record.json",
    {
      label: "Experiment Run Record JSON",
      externalLinkLabel: "Open experiment run record JSON in a new window",
    },
  ],
  [
    "/delivery-readiness.md",
    {
      label: "交付就绪评估",
      externalLinkLabel: "在新窗口打开交付就绪评估",
    },
  ],
  [
    "/delivery-readiness.json",
    {
      label: "交付就绪评估 JSON",
      externalLinkLabel: "在新窗口打开交付就绪评估 JSON",
    },
  ],
  [
    "/research-evidence-summary.json",
    {
      label: "Research Evidence Summary JSON",
      externalLinkLabel: "Open research evidence summary JSON in a new window",
    },
  ],
  [
    "/supervisor-scientific-gate.json",
    {
      label: "Scientific Supervisor Gate JSON",
      externalLinkLabel: "Open scientific supervisor gate JSON in a new window",
    },
  ],
  [
    "/scientific-remediation-handoff.json",
    {
      label: "Scientific Remediation Handoff JSON",
      externalLinkLabel: "Open scientific remediation handoff JSON in a new window",
    },
  ],
  [
    "/scientific-followup-history.json",
    {
      label: "Scientific Follow-Up History JSON",
      externalLinkLabel: "Open scientific follow-up history JSON in a new window",
    },
  ],
  [
    "/final-report.md",
    {
      label: "最终报告",
      externalLinkLabel: "在新窗口打开最终报告",
    },
  ],
  [
    "/final-report.html",
    {
      label: "最终报告 HTML",
      externalLinkLabel: "在新窗口打开最终报告 HTML",
    },
  ],
  [
    "/final-report.json",
    {
      label: "最终报告 JSON",
      externalLinkLabel: "在新窗口打开最终报告 JSON",
    },
  ],
  [
    "/solver-results.md",
    {
      label: "结果摘要",
      externalLinkLabel: "在新窗口打开结果摘要",
    },
  ],
  [
    "/solver-results.json",
    {
      label: "结果数据 JSON",
      externalLinkLabel: "在新窗口打开结果数据 JSON",
    },
  ],
  [
    "/stability-evidence.json",
    {
      label: "Stability Evidence JSON",
      externalLinkLabel: "Open stability evidence JSON in a new window",
    },
  ],
  [
    "/surface-pressure.csv",
    {
      label: "表面压力结果 CSV",
      externalLinkLabel: "在新窗口打开表面压力结果 CSV",
    },
  ],
  [
    "/surface-pressure.png",
    {
      label: "表面压力图 PNG",
      externalLinkLabel: "在新窗口打开表面压力图 PNG",
    },
  ],
  [
    "/surface-pressure.md",
    {
      label: "表面压力结果说明",
      externalLinkLabel: "在新窗口打开表面压力结果说明",
    },
  ],
  [
    "/wake-velocity-slice.csv",
    {
      label: "尾流速度切片 CSV",
      externalLinkLabel: "在新窗口打开尾流速度切片 CSV",
    },
  ],
  [
    "/wake-velocity-slice.png",
    {
      label: "尾流速度切片图 PNG",
      externalLinkLabel: "在新窗口打开尾流速度切片图 PNG",
    },
  ],
  [
    "/wake-velocity-slice.md",
    {
      label: "尾流速度切片说明",
      externalLinkLabel: "在新窗口打开尾流速度切片说明",
    },
  ],
  [
    "/verification-mesh-independence.json",
    {
      label: "Scientific Verification - Mesh Independence JSON",
      externalLinkLabel:
        "Open scientific verification mesh independence JSON in a new tab",
    },
  ],
  [
    "/verification-domain-sensitivity.json",
    {
      label: "Scientific Verification - Domain Sensitivity JSON",
      externalLinkLabel:
        "Open scientific verification domain sensitivity JSON in a new tab",
    },
  ],
  [
    "/verification-time-step-sensitivity.json",
    {
      label: "Scientific Verification - Time-Step Sensitivity JSON",
      externalLinkLabel:
        "Open scientific verification time-step sensitivity JSON in a new tab",
    },
  ],
  [
    "/dispatch-summary.md",
    {
      label: "求解派发摘要",
      externalLinkLabel: "在新窗口打开求解派发摘要",
    },
  ],
  [
    "/dispatch-summary.html",
    {
      label: "求解派发 HTML",
      externalLinkLabel: "在新窗口打开求解派发 HTML",
    },
  ],
  [
    "/geometry-check.md",
    {
      label: "几何检查报告",
      externalLinkLabel: "在新窗口打开几何检查报告",
    },
  ],
  [
    "/geometry-check.html",
    {
      label: "几何检查 HTML",
      externalLinkLabel: "在新窗口打开几何检查 HTML",
    },
  ],
  [
    "/geometry-check.json",
    {
      label: "几何检查 JSON",
      externalLinkLabel: "在新窗口打开几何检查 JSON",
    },
  ],
  [
    "/openfoam-run.log",
    {
      label: "OpenFOAM 运行日志",
      externalLinkLabel: "在新窗口打开 OpenFOAM 运行日志",
    },
  ],
  [
    "/openfoam-request.json",
    {
      label: "求解请求清单",
      externalLinkLabel: "在新窗口打开求解请求清单",
    },
  ],
  [
    "/supervisor-handoff.json",
    {
      label: "Supervisor 交接单",
      externalLinkLabel: "在新窗口打开 Supervisor 交接单",
    },
  ],
];

function classifySubmarineArtifact(path: string): SubmarineArtifactGroupId {
  if (path.includes("/submarine/skill-studio/")) {
    return "planning";
  }

  if (
    path.endsWith("/cfd-design-brief.md") ||
    path.endsWith("/cfd-design-brief.html") ||
    path.endsWith("/cfd-design-brief.json") ||
    path.endsWith("/study-plan.json") ||
    path.endsWith("/study-manifest.json") ||
    path.endsWith("/experiment-manifest.json")
  ) {
    return "planning";
  }

  if (
    path.endsWith("/delivery-readiness.md") ||
    path.endsWith("/delivery-readiness.json") ||
    path.endsWith("/research-evidence-summary.json") ||
    path.endsWith("/supervisor-scientific-gate.json") ||
    path.endsWith("/scientific-remediation-plan.json") ||
    path.endsWith("/scientific-remediation-handoff.json") ||
    path.endsWith("/scientific-followup-history.json") ||
    path.endsWith("/final-report.md") ||
    path.endsWith("/final-report.html") ||
    path.endsWith("/final-report.json")
  ) {
    return "report";
  }

  if (
    path.endsWith("/solver-results.md") ||
    path.endsWith("/solver-results.json") ||
    path.endsWith("/stability-evidence.json") ||
    path.endsWith("/surface-pressure.csv") ||
    path.endsWith("/surface-pressure.png") ||
    path.endsWith("/surface-pressure.md") ||
    path.endsWith("/wake-velocity-slice.csv") ||
    path.endsWith("/wake-velocity-slice.png") ||
    path.endsWith("/wake-velocity-slice.md") ||
    path.endsWith("/run-compare-summary.json") ||
    path.endsWith("/verification-mesh-independence.json") ||
    path.endsWith("/verification-domain-sensitivity.json") ||
    path.endsWith("/verification-time-step-sensitivity.json")
  ) {
    return "results";
  }

  if (
    path.endsWith("/openfoam-run.log") ||
    path.endsWith("/openfoam-request.json") ||
    path.endsWith("/run-record.json") ||
    path.endsWith("/dispatch-summary.md") ||
    path.endsWith("/dispatch-summary.html") ||
    path.endsWith("/supervisor-handoff.json")
  ) {
    return "execution";
  }

  if (
    path.endsWith("/geometry-check.md") ||
    path.endsWith("/geometry-check.html") ||
    path.endsWith("/geometry-check.json")
  ) {
    return "inspection";
  }

  return "other";
}

export function getSubmarineArtifactMeta(path: string): SubmarineArtifactMeta {
  const matched = ARTIFACT_COPY.find(([pattern]) => path.endsWith(pattern));
  if (matched) {
    return matched[1];
  }

  const filename = path.split("/").at(-1) ?? path;
  return {
    label: filename,
    externalLinkLabel: `在新窗口打开 ${filename}`,
  };
}

export function groupSubmarineArtifacts(
  paths: string[],
): SubmarineArtifactGroup[] {
  const groups = new Map<SubmarineArtifactGroupId, string[]>();

  for (const path of paths) {
    const groupId = classifySubmarineArtifact(path);
    const current = groups.get(groupId) ?? [];
    current.push(path);
    groups.set(groupId, current);
  }

  return GROUP_ORDER.flatMap((groupId) => {
    const groupPaths = groups.get(groupId);
    if (!groupPaths || groupPaths.length === 0) {
      return [];
    }

    return [
      {
        id: groupId,
        label: GROUP_LABELS[groupId],
        count: groupPaths.length,
        paths: groupPaths,
      },
    ];
  });
}

export function getSubmarineArtifactFilterOptions(
  groups: SubmarineArtifactGroup[],
): SubmarineArtifactFilterOption[] {
  const totalCount = groups.reduce((sum, group) => sum + group.count, 0);

  return [
    {
      id: "all",
      label: "全部产物",
      count: totalCount,
    },
    ...groups.map((group) => ({
      id: group.id,
      label: group.label,
      count: group.count,
    })),
  ];
}

export function filterSubmarineArtifactGroups(
  groups: SubmarineArtifactGroup[],
  filterId: SubmarineArtifactFilterId,
): SubmarineArtifactGroup[] {
  if (filterId === "all") {
    return groups;
  }

  return groups.filter((group) => group.id === filterId);
}

function formatRequirementNumber(
  value: number | null | undefined,
  digits: number,
  suffix: string,
) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "--";
  }
  return `${value.toFixed(digits)}${suffix}`;
}

function formatCalculationPlanScalarValue(value: unknown) {
  if (value === null || value === undefined) {
    return "--";
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return Number(value.toFixed(Math.abs(value) >= 1 ? 4 : 6)).toString();
  }
  if (typeof value === "string") {
    return value.trim().length > 0 ? value : "--";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return formatSummaryValue(value);
}

function formatCalculationPlanValue(payload: {
  proposed_value?: unknown;
  proposed_range?: unknown[] | Record<string, unknown> | null;
  unit?: string | null;
}) {
  if (payload.proposed_value != null) {
    const base = formatCalculationPlanScalarValue(payload.proposed_value);
    return base === "--" || !payload.unit ? base : `${base} ${payload.unit}`;
  }

  if (Array.isArray(payload.proposed_range)) {
    const values = payload.proposed_range
      .map((item) => formatCalculationPlanScalarValue(item))
      .filter((item) => item !== "--");
    if (values.length > 0) {
      return `${values.join(" to ")}${payload.unit ? ` ${payload.unit}` : ""}`;
    }
  }

  if (payload.proposed_range && typeof payload.proposed_range === "object") {
    const rangePayload = payload.proposed_range as Record<string, unknown>;
    const minValue = formatCalculationPlanScalarValue(rangePayload.min);
    const maxValue = formatCalculationPlanScalarValue(rangePayload.max);
    if (minValue !== "--" || maxValue !== "--") {
      return `${minValue} to ${maxValue}${payload.unit ? ` ${payload.unit}` : ""}`;
    }
  }

  return "--";
}

export function formatSubmarineRuntimeStageLabel(stage?: string | null) {
  if (!stage) {
    return "--";
  }
  return SCIENTIFIC_GATE_STAGE_LABELS[stage] ?? stage;
}

export function formatSubmarineExecutionRoleLabel(roleId?: string | null) {
  if (!roleId) {
    return "--";
  }
  return (
    EXECUTION_ROLE_LABELS[roleId] ??
    SCIENTIFIC_GATE_STAGE_LABELS[roleId] ??
    roleId
  );
}

export function buildSubmarineStageTrack({
  runtimePlan,
  currentStage,
  nextRecommendedStage,
}: {
  runtimePlan?: SubmarineExecutionOutlineItem[] | null;
  currentStage?: string | null;
  nextRecommendedStage?: string | null;
}): SubmarineStageTrackItem[] {
  const trackFromPlan =
    runtimePlan?.map((item) => ({
      stageId: item.role_id ?? "unknown",
      label: formatSubmarineExecutionRoleLabel(item.role_id),
      status: item.status ?? "pending",
    })) ?? [];

  if (trackFromPlan.length > 0) {
    return trackFromPlan;
  }

  const legacyTrackOrder =
    currentStage === "user-confirmation" ||
    nextRecommendedStage === "user-confirmation"
      ? ([
          "task-intelligence",
          "geometry-preflight",
          "user-confirmation",
          "solver-dispatch",
          "result-reporting",
          "supervisor-review",
        ] as const)
      : LEGACY_STAGE_TRACK_ORDER;

  const currentIndex = legacyTrackOrder.findIndex(
    (stageId) => stageId === currentStage,
  );
  const nextIndex = legacyTrackOrder.findIndex(
    (stageId) => stageId === nextRecommendedStage,
  );

  return legacyTrackOrder.map((stageId, index) => ({
    stageId,
    label: formatSubmarineRuntimeStageLabel(stageId),
    status:
      currentIndex > index
        ? "completed"
        : currentIndex === index
          ? "in_progress"
          : nextIndex === index
            ? "ready"
          : "pending",
  }));
}

function normalizeExecutionOutline(
  items: SubmarineExecutionOutlineItem[] | null | undefined,
) {
  return (
    items
      ?.map((item) => ({
        roleId: item.role_id ?? "unknown",
        roleLabel: formatSubmarineExecutionRoleLabel(item.role_id),
        owner: item.owner ?? "待指定",
        goal: item.goal ?? "待补充",
        status: item.status ?? "pending",
        targetSkills: item.target_skills?.filter(Boolean) ?? [],
      }))
      .filter((item) => item.goal) ?? []
  );
}

export function buildSubmarineExecutionOutline({
  designBrief,
  runtimePlan,
}: {
  designBrief?: SubmarineDesignBriefPayload | null;
  runtimePlan?: SubmarineExecutionOutlineItem[] | null;
}) {
  const normalizedRuntimePlan = normalizeExecutionOutline(runtimePlan);
  if (normalizedRuntimePlan.length > 0) {
    return normalizedRuntimePlan;
  }
  return normalizeExecutionOutline(designBrief?.execution_outline);
}

export function buildSubmarineDesignBriefSummary(
  payload: SubmarineDesignBriefPayload | null | undefined,
): SubmarineDesignBriefSummary | null {
  if (!payload) {
    return null;
  }

  const requirements = payload.simulation_requirements ?? {};
  const requirementPairs = [
    {
      label: "来流速度",
      value: formatRequirementNumber(requirements.inlet_velocity_mps, 2, " m/s"),
    },
    {
      label: "流体密度",
      value: formatRequirementNumber(
        requirements.fluid_density_kg_m3,
        1,
        " kg/m^3",
      ),
    },
    {
      label: "运动黏度",
      value: formatRequirementNumber(
        requirements.kinematic_viscosity_m2ps,
        8,
        " m^2/s",
      ),
    },
    {
      label: "终止时间",
      value: formatRequirementNumber(requirements.end_time_seconds, 1, " s"),
    },
    {
      label: "时间步长",
      value: formatRequirementNumber(requirements.delta_t_seconds, 3, " s"),
    },
    {
      label: "输出步数间隔",
      value:
        typeof requirements.write_interval_steps === "number"
          ? `${requirements.write_interval_steps}`
          : "--",
    },
  ].filter((item) => item.value !== "--");

  const calculationPlan = (payload.calculation_plan ?? [])
    .filter(Boolean)
    .map((item) => ({
      itemId: item.item_id ?? "unknown",
      category: item.category ?? "--",
      label: item.label ?? item.category ?? "Calculation plan item",
      proposedValue: formatCalculationPlanValue(item),
      sourceLabel: item.source_label ?? item.origin ?? "--",
      sourceUrl: item.source_url ?? "--",
      confidenceLabel:
        CALCULATION_PLAN_CONFIDENCE_LABELS[item.confidence ?? ""] ??
        item.confidence ??
        "--",
      applicabilityConditions: item.applicability_conditions?.filter(Boolean) ?? [],
      evidenceGapNote: item.evidence_gap_note ?? "--",
      originLabel:
        CALCULATION_PLAN_ORIGIN_LABELS[item.origin ?? ""] ??
        item.origin ??
        "--",
      approvalState: item.approval_state ?? "--",
      approvalStateLabel:
        CALCULATION_PLAN_APPROVAL_LABELS[item.approval_state ?? ""] ??
        item.approval_state ??
        "--",
      requiresImmediateConfirmation: Boolean(item.requires_immediate_confirmation),
      researcherNote: item.researcher_note ?? "--",
    }));
  const pendingCalculationPlanCount = calculationPlan.filter(
    (item) => item.approvalState !== "researcher_confirmed",
  ).length;
  const immediateClarificationCount = calculationPlan.filter(
    (item) =>
      item.requiresImmediateConfirmation &&
      item.approvalState !== "researcher_confirmed",
  ).length;
  const precomputeApprovalLabel =
    immediateClarificationCount > 0
      ? "Immediate Clarification Required"
      : pendingCalculationPlanCount > 0
        ? "Pending Researcher Confirmation"
        : calculationPlan.length > 0
          ? "Researcher Confirmed"
          : payload.confirmation_status === "confirmed"
            ? "Brief Confirmed"
            : "Brief Draft";

  return {
    precomputeApprovalLabel,
    pendingCalculationPlanCount,
    immediateClarificationCount,
    confirmationStatusLabel:
      payload.confirmation_status === "confirmed" ? "已确认" : "待确认",
    expectedOutputs: payload.expected_outputs?.filter(Boolean) ?? [],
    scientificVerificationRequirements: (
      payload.scientific_verification_requirements ?? []
    )
      .filter(Boolean)
      .map((item) => ({
        requirementId: item.requirement_id ?? "unknown",
        label: item.label ?? "--",
        checkType: item.check_type ?? "--",
        detail: formatVerificationRequirementDetail(item),
      })),
    requestedOutputs: (payload.requested_outputs ?? [])
      .filter(Boolean)
      .map((item) => ({
        outputId: item.output_id ?? "unknown",
        label: item.label ?? "--",
        requestedLabel: item.requested_label ?? item.label ?? "--",
        supportLevel: item.support_level ?? "--",
        specSummary: formatPostprocessSpecSummary(item.postprocess_spec ?? null),
        notes: item.notes ?? "",
      })),
    userConstraints: payload.user_constraints?.filter(Boolean) ?? [],
    openQuestions: payload.open_questions?.filter(Boolean) ?? [],
    executionOutline: buildSubmarineExecutionOutline({
      designBrief: payload,
      runtimePlan: null,
    }),
    calculationPlan,
    requirementPairs,
  };
}

export function buildSubmarineOutputDeliverySummary({
  requestedOutputs,
  outputDeliveryPlan,
}: {
  requestedOutputs?:
    | SubmarineRequestedOutputPayload[]
    | SubmarineDesignBriefPayload["requested_outputs"]
    | null;
  outputDeliveryPlan?:
    | SubmarineOutputDeliveryPlanItem[]
    | SubmarineFinalReportPayload["output_delivery_plan"]
    | null;
}): SubmarineOutputDeliverySummaryItem[] {
  const requestedOutputSpecById = new Map(
    (requestedOutputs ?? [])
      .filter(Boolean)
      .map((item) => [
        item.output_id ?? "unknown",
        formatPostprocessSpecSummary(item.postprocess_spec ?? null),
      ]),
  );

  return (outputDeliveryPlan ?? []).filter(Boolean).map((item) => ({
    outputId: item.output_id ?? "unknown",
    label: item.label ?? "--",
    deliveryStatus: item.delivery_status ?? "--",
    specSummary: requestedOutputSpecById.get(item.output_id ?? "unknown") ?? "--",
    detail: item.detail ?? "--",
    artifactPaths: item.artifact_virtual_paths?.filter(Boolean) ?? [],
  }));
}

export function buildSubmarineAcceptanceSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineAcceptanceSummary | null {
  const assessment = payload?.acceptance_assessment;
  if (!assessment) {
    return null;
  }

  const benchmarkComparisons = (assessment.benchmark_comparisons ?? [])
    .filter(Boolean)
    .map((item) => ({
      metricId: item.metric_id ?? "--",
      quantity: item.quantity ?? "--",
      status: item.status ?? "--",
      statusLabel:
        BENCHMARK_COMPARISON_STATUS_LABELS[item.status ?? ""] ??
        item.status ??
        "--",
      summary: item.summary_zh ?? "--",
      detail: item.detail ?? "--",
      observedValue:
        typeof item.observed_value === "number"
          ? item.observed_value.toFixed(5)
          : "--",
      referenceValue:
        typeof item.reference_value === "number"
          ? item.reference_value.toFixed(5)
          : "--",
      absoluteError: formatFiniteNumber(item.absolute_error ?? null, 5),
      relativeError: formatFinitePercent(item.relative_error ?? null, 2),
      relativeTolerance: formatFinitePercent(
        item.relative_tolerance ?? null,
        2,
      ),
      targetVelocity: formatFiniteNumber(
        item.target_inlet_velocity_mps ?? null,
        2,
      ),
      observedVelocity: formatFiniteNumber(
        item.observed_inlet_velocity_mps ?? null,
        2,
      ),
      sourceLabel: item.source_label ?? "--",
      sourceUrl: item.source_url ?? "--",
    }));
  const outputDelivery = buildSubmarineOutputDeliverySummary({
    requestedOutputs: payload?.requested_outputs,
    outputDeliveryPlan: payload?.output_delivery_plan,
  });

  return {
    statusLabel:
      ACCEPTANCE_STATUS_LABELS[assessment.status ?? ""] ??
      assessment.status ??
      "--",
    confidenceLabel:
      ACCEPTANCE_CONFIDENCE_LABELS[assessment.confidence ?? ""] ??
      assessment.confidence ??
      "--",
    blockingIssues: assessment.blocking_issues?.filter(Boolean) ?? [],
    warnings: assessment.warnings?.filter(Boolean) ?? [],
    passedChecks: assessment.passed_checks?.filter(Boolean) ?? [],
    outputDelivery,
    benchmarkComparisons,
  };
}

export function formatSubmarineBenchmarkComparisonSummaryLine(
  comparison: SubmarineAcceptanceSummary["benchmarkComparisons"][number],
): string {
  const segments = [
    `${comparison.metricId} | ${comparison.statusLabel}`,
    `${comparison.quantity} ${comparison.observedValue} / ${comparison.referenceValue}`,
  ];

  if (comparison.relativeError !== "--" || comparison.relativeTolerance !== "--") {
    segments.push(
      `error ${comparison.relativeError} / tol ${comparison.relativeTolerance}`,
    );
  }
  if (comparison.targetVelocity !== "--" || comparison.observedVelocity !== "--") {
    segments.push(
      `velocity ${comparison.observedVelocity} vs ${comparison.targetVelocity} m/s`,
    );
  }
  if (comparison.sourceLabel !== "--") {
    segments.push(`source ${comparison.sourceLabel}`);
  }

  return segments.join(" | ");
}

function formatScientificRequirementStatus(status?: string | null): string {
  if (status === "missing_evidence") {
    return "Missing Evidence";
  }
  if (status === "research_ready") {
    return "Research Ready";
  }
  if (status === "passed") {
    return "Passed";
  }
  if (status === "blocked") {
    return "Blocked";
  }
  return status ?? "--";
}

function formatFiniteNumber(
  value: number | null | undefined,
  digits: number,
): string {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toFixed(digits)
    : "--";
}

function formatFinitePercent(
  value: number | null | undefined,
  digits: number,
): string {
  return typeof value === "number" && Number.isFinite(value)
    ? `${(value * 100).toFixed(digits)}%`
    : "--";
}

export function buildSubmarineStabilityEvidenceSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineStabilityEvidenceSummary | null {
  const evidence = payload?.stability_evidence;
  if (!evidence) {
    return null;
  }

  const tail = evidence.force_coefficient_tail;
  const residualSummary = evidence.residual_summary;
  const residualMaxValue =
    residualSummary && typeof residualSummary === "object"
      ? (residualSummary as Record<string, unknown>).max_final_residual
      : null;
  const residualMax =
    typeof residualMaxValue === "number" && Number.isFinite(residualMaxValue)
      ? residualMaxValue
      : null;

  return {
    statusLabel:
      STABILITY_EVIDENCE_STATUS_LABELS[evidence.status ?? ""] ??
      evidence.status ??
      "--",
    summary: evidence.summary_zh ?? "--",
    solverResultsPath: evidence.source_solver_results_virtual_path ?? "--",
    artifactPath:
      evidence.artifact_virtual_path ??
      payload?.stability_evidence_virtual_path ??
      "--",
    residualMaxFinalValue: formatFiniteNumber(residualMax, 6),
    tailCoefficientLabel: tail?.coefficient ?? "--",
    tailStatusLabel:
      STABILITY_EVIDENCE_STATUS_LABELS[tail?.status ?? ""] ??
      tail?.status ??
      "--",
    tailSpreadLabel: formatFiniteNumber(tail?.relative_spread ?? null, 4),
    tailSampleCountLabel:
      typeof tail?.observed_sample_count === "number" &&
      Number.isFinite(tail.observed_sample_count) &&
      typeof tail?.required_sample_count === "number" &&
      Number.isFinite(tail.required_sample_count)
        ? `${tail.observed_sample_count}/${tail.required_sample_count}`
        : "--",
    blockingIssues: evidence.blocking_issues?.filter(Boolean) ?? [],
    missingEvidence: evidence.missing_evidence?.filter(Boolean) ?? [],
    passedRequirements: evidence.passed_requirements?.filter(Boolean) ?? [],
    requirementLines: (evidence.requirements ?? [])
      .filter(Boolean)
      .map(
        (item) =>
          `${item.label ?? "--"} | ${formatScientificRequirementStatus(
            item.status,
          )} | ${item.detail ?? "--"}`,
      ),
  };
}

export function buildSubmarineScientificVerificationSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineScientificVerificationSummary | null {
  const assessment = payload?.scientific_verification_assessment;
  if (!assessment) {
    return null;
  }

  return {
    statusLabel:
      SCIENTIFIC_VERIFICATION_STATUS_LABELS[assessment.status ?? ""] ??
      assessment.status ??
      "--",
    confidenceLabel:
      SCIENTIFIC_VERIFICATION_CONFIDENCE_LABELS[assessment.confidence ?? ""] ??
      assessment.confidence ??
      "--",
    blockingIssues: assessment.blocking_issues?.filter(Boolean) ?? [],
    missingEvidence: assessment.missing_evidence?.filter(Boolean) ?? [],
    passedRequirements: assessment.passed_requirements?.filter(Boolean) ?? [],
    requirements: (assessment.requirements ?? []).filter(Boolean).map((item) => ({
      requirementId: item.requirement_id ?? "unknown",
      label: item.label ?? "--",
      status: formatScientificRequirementStatus(item.status),
      detail: item.detail ?? "--",
    })),
  };
}

export function buildSubmarineScientificStudySummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineScientificStudySummary | null {
  const summary = payload?.scientific_study_summary;
  if (!summary) {
    return null;
  }

  return {
    executionStatusLabel: formatStatusLabel(
      summary.study_execution_status,
      SCIENTIFIC_STUDY_EXECUTION_STATUS_LABELS,
    ),
    workflowStatusLabel: formatStatusLabel(
      summary.workflow_status ?? summary.study_execution_status,
      SCIENTIFIC_STUDY_EXECUTION_STATUS_LABELS,
    ),
    studyStatusCountLines: formatStatusCountLines(
      summary.study_status_counts,
      SCIENTIFIC_STUDY_EXECUTION_STATUS_LABELS,
    ),
    manifestPath: summary.manifest_virtual_path ?? "--",
    artifactPaths: summary.artifact_virtual_paths?.filter(Boolean) ?? [],
    studies: (summary.studies ?? []).filter(Boolean).map((item) => ({
      studyType: item.study_type ?? "unknown",
      summaryLabel: item.summary_label ?? "--",
      monitoredQuantity: item.monitored_quantity ?? "--",
      variantCount: item.variant_count ?? 0,
      studyExecutionStatusLabel: formatStatusLabel(
        item.study_execution_status,
        SCIENTIFIC_STUDY_EXECUTION_STATUS_LABELS,
      ),
      workflowStatusLabel: formatStatusLabel(
        item.workflow_status ?? item.study_execution_status,
        SCIENTIFIC_STUDY_EXECUTION_STATUS_LABELS,
      ),
      workflowDetail: item.workflow_detail ?? "--",
      variantStatusCountLines: formatStatusCountLines(
        item.variant_status_counts,
        SCIENTIFIC_STUDY_EXECUTION_STATUS_LABELS,
      ),
      compareStatusCountLines: formatStatusCountLines(
        item.compare_status_counts,
        EXPERIMENT_COMPARE_STATUS_LABELS,
      ),
      expectedVariantRunIds: item.expected_variant_run_ids?.filter(Boolean) ?? [],
      plannedVariantRunIds: item.planned_variant_run_ids?.filter(Boolean) ?? [],
      inProgressVariantRunIds:
        item.in_progress_variant_run_ids?.filter(Boolean) ?? [],
      completedVariantRunIds:
        item.completed_variant_run_ids?.filter(Boolean) ?? [],
      blockedVariantRunIds: item.blocked_variant_run_ids?.filter(Boolean) ?? [],
      plannedCompareVariantRunIds:
        item.planned_compare_variant_run_ids?.filter(Boolean) ?? [],
      completedCompareVariantRunIds:
        item.completed_compare_variant_run_ids?.filter(Boolean) ?? [],
      blockedCompareVariantRunIds:
        item.blocked_compare_variant_run_ids?.filter(Boolean) ?? [],
      missingMetricsVariantRunIds:
        item.missing_metrics_variant_run_ids?.filter(Boolean) ?? [],
      verificationStatus: formatScientificRequirementStatus(item.verification_status),
      verificationDetail: item.verification_detail ?? "--",
    })),
  };
}

export function buildSubmarineExperimentSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineExperimentSummary | null {
  const summary = payload?.experiment_summary;
  if (!summary) {
    return null;
  }

  return {
    experimentId: summary.experiment_id ?? "--",
    experimentStatusLabel: formatStatusLabel(
      summary.experiment_status,
      EXPERIMENT_STATUS_LABELS,
    ),
    workflowStatusLabel: formatStatusLabel(
      summary.workflow_status ?? summary.experiment_status,
      EXPERIMENT_STATUS_LABELS,
    ),
    workflowDetail: summary.workflow_detail ?? "--",
    baselineRunId: summary.baseline_run_id ?? "--",
    runCount:
      typeof summary.run_count === "number" && Number.isFinite(summary.run_count)
        ? summary.run_count
        : 0,
    compareCount:
      typeof summary.compare_count === "number" &&
      Number.isFinite(summary.compare_count)
        ? summary.compare_count
        : 0,
    manifestPath: summary.manifest_virtual_path ?? "--",
    studyManifestPath: summary.study_manifest_virtual_path ?? "--",
    comparePath: summary.compare_virtual_path ?? "--",
    artifactPaths: summary.artifact_virtual_paths?.filter(Boolean) ?? [],
    linkageStatus: summary.linkage_status ?? "--",
    linkageIssueCount:
      typeof summary.linkage_issue_count === "number" &&
      Number.isFinite(summary.linkage_issue_count)
        ? summary.linkage_issue_count
        : 0,
    linkageIssues: summary.linkage_issues?.filter(Boolean) ?? [],
    runStatusCountLines: formatStatusCountLines(
      summary.run_status_counts,
      SCIENTIFIC_STUDY_EXECUTION_STATUS_LABELS,
    ),
    compareStatusCountLines: formatStatusCountLines(
      summary.compare_status_counts,
      EXPERIMENT_COMPARE_STATUS_LABELS,
    ),
    expectedVariantRunIds: summary.expected_variant_run_ids?.filter(Boolean) ?? [],
    registeredCustomVariantRunIds:
      summary.registered_custom_variant_run_ids?.filter(Boolean) ?? [],
    missingVariantRunRecordIds:
      summary.missing_variant_run_record_ids?.filter(Boolean) ?? [],
    missingCompareEntryIds:
      summary.missing_compare_entry_ids?.filter(Boolean) ?? [],
    plannedCustomVariantRunIds:
      summary.planned_custom_variant_run_ids?.filter(Boolean) ?? [],
    completedCustomVariantRunIds:
      summary.completed_custom_variant_run_ids?.filter(Boolean) ?? [],
    missingCustomCompareEntryIds:
      summary.missing_custom_compare_entry_ids?.filter(Boolean) ?? [],
    blockedVariantRunIds:
      summary.blocked_variant_run_ids?.filter(Boolean) ?? [],
    plannedVariantRunIds:
      summary.planned_variant_run_ids?.filter(Boolean) ?? [],
    missingMetricsVariantRunIds:
      summary.missing_metrics_variant_run_ids?.filter(Boolean) ?? [],
    compareNotes: summary.compare_notes?.filter(Boolean) ?? [],
  };
}

export function buildSubmarineExperimentCompareSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineExperimentCompareSummary | null {
  const summary = payload?.experiment_compare_summary;
  if (!summary) {
    return null;
  }

  return {
    experimentId: summary.experiment_id ?? "--",
    baselineRunId: summary.baseline_run_id ?? "--",
    compareCount:
      typeof summary.compare_count === "number" && Number.isFinite(summary.compare_count)
        ? summary.compare_count
        : 0,
    comparePath: summary.compare_virtual_path ?? "--",
    workflowStatusLabel: formatStatusLabel(
      summary.workflow_status,
      EXPERIMENT_STATUS_LABELS,
    ),
    compareStatusCountLines: formatStatusCountLines(
      summary.compare_status_counts,
      EXPERIMENT_COMPARE_STATUS_LABELS,
    ),
    plannedCandidateRunIds:
      summary.planned_candidate_run_ids?.filter(Boolean) ?? [],
    completedCandidateRunIds:
      summary.completed_candidate_run_ids?.filter(Boolean) ?? [],
    blockedCandidateRunIds:
      summary.blocked_candidate_run_ids?.filter(Boolean) ?? [],
    missingMetricsCandidateRunIds:
      summary.missing_metrics_candidate_run_ids?.filter(Boolean) ?? [],
    artifactPaths: summary.artifact_virtual_paths?.filter(Boolean) ?? [],
    comparisons: (summary.comparisons ?? []).filter(Boolean).map((item) => {
      const studyType = item.study_type ?? "unknown";
      const variantId = item.variant_id ?? "unknown";
      const baselineSolverResultsPath =
        item.baseline_solver_results_virtual_path ?? "--";
      const candidateSolverResultsPath =
        item.candidate_solver_results_virtual_path ?? "--";
      const baselineRunRecordPath = item.baseline_run_record_virtual_path ?? "--";
      const candidateRunRecordPath =
        item.candidate_run_record_virtual_path ?? "--";
      const studyLabel = formatExperimentCompareStudyLabel(item);
      const lineageLabel = formatExperimentLineageLabel(item);
      const compareTargetRunId = item.compare_target_run_id ?? summary.baseline_run_id ?? "--";

      return {
        candidateRunId: item.candidate_run_id ?? "unknown",
        runRole: item.run_role ?? "--",
        variantOrigin: item.variant_origin ?? item.run_role ?? "--",
        studyType,
        variantId,
        variantLabel: item.variant_label ?? variantId,
        studyLabel,
        lineageLabel,
        baselineReferenceRunId:
          item.baseline_reference_run_id ?? summary.baseline_run_id ?? "--",
        compareTargetRunId,
        isCustomVariant: isCustomVariantEntry(item),
        compareStatus: item.compare_status ?? "--",
        compareStatusLabel: formatStatusLabel(
          item.compare_status,
          EXPERIMENT_COMPARE_STATUS_LABELS,
        ),
        candidateExecutionStatusLabel: formatStatusLabel(
          item.candidate_execution_status,
          SCIENTIFIC_STUDY_EXECUTION_STATUS_LABELS,
        ),
        notes: item.notes ?? "--",
        metricDeltaLines: formatCompareMetricDeltaLines(item.metric_deltas),
        baselineSolverResultsPath,
        candidateSolverResultsPath,
        baselineRunRecordPath,
        candidateRunRecordPath,
        artifactPaths: mergeArtifactPaths(
          baselineSolverResultsPath !== "--" ? [baselineSolverResultsPath] : [],
          candidateSolverResultsPath !== "--" ? [candidateSolverResultsPath] : [],
          baselineRunRecordPath !== "--" ? [baselineRunRecordPath] : [],
          candidateRunRecordPath !== "--" ? [candidateRunRecordPath] : [],
        ),
      };
    }),
  };
}

export function buildSubmarineFigureDeliverySummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineFigureDeliverySummary | null {
  const summary = payload?.figure_delivery_summary;
  if (!summary) {
    return null;
  }

  return {
    figureCount:
      typeof summary.figure_count === "number" && Number.isFinite(summary.figure_count)
        ? summary.figure_count
        : 0,
    manifestPath: summary.manifest_virtual_path ?? "--",
    artifactPaths: summary.artifact_virtual_paths?.filter(Boolean) ?? [],
    figures: (summary.figures ?? []).filter(Boolean).map((item) => ({
      figureId: item.figure_id ?? "unknown",
      outputId: item.output_id ?? "unknown",
      title: item.title ?? "--",
      caption: item.caption ?? "--",
      renderStatus: item.render_status ?? "--",
      renderStatusLabel:
        FIGURE_RENDER_STATUS_LABELS[item.render_status ?? ""] ??
        item.render_status ??
        "--",
      selectorSummary: item.selector_summary ?? "--",
      field: item.field ?? "--",
      artifactPaths: item.artifact_virtual_paths?.filter(Boolean) ?? [],
      sourceCsvPath: item.source_csv_virtual_path ?? "--",
    })),
  };
}

export function buildSubmarineResearchEvidenceSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineResearchEvidenceSummary | null {
  const summary = payload?.research_evidence_summary;
  if (!summary) {
    return null;
  }

  return {
    readinessStatus: summary.readiness_status ?? "--",
    verificationStatus: summary.verification_status ?? "--",
    validationStatus: summary.validation_status ?? "--",
    provenanceStatus: summary.provenance_status ?? "--",
    readinessLabel:
      RESEARCH_EVIDENCE_READINESS_LABELS[summary.readiness_status ?? ""] ??
      summary.readiness_status ??
      "--",
    verificationStatusLabel:
      RESEARCH_EVIDENCE_DIMENSION_LABELS[summary.verification_status ?? ""] ??
      summary.verification_status ??
      "--",
    validationStatusLabel:
      RESEARCH_EVIDENCE_DIMENSION_LABELS[summary.validation_status ?? ""] ??
      summary.validation_status ??
      "--",
    provenanceStatusLabel:
      RESEARCH_EVIDENCE_DIMENSION_LABELS[summary.provenance_status ?? ""] ??
      summary.provenance_status ??
      "--",
    confidenceLabel:
      RESEARCH_EVIDENCE_DIMENSION_LABELS[summary.confidence ?? ""] ??
      summary.confidence ??
      "--",
    blockingIssues: summary.blocking_issues?.filter(Boolean) ?? [],
    evidenceGaps: summary.evidence_gaps?.filter(Boolean) ?? [],
    passedEvidence: summary.passed_evidence?.filter(Boolean) ?? [],
    benchmarkHighlights: summary.benchmark_highlights?.filter(Boolean) ?? [],
    provenanceHighlights: summary.provenance_highlights?.filter(Boolean) ?? [],
    artifactPaths: summary.artifact_virtual_paths?.filter(Boolean) ?? [],
  };
}

export function buildSubmarineReproducibilitySummary(
  payload:
    | SubmarineFinalReportPayload
    | SubmarineRuntimeSnapshotPayload
    | null
    | undefined,
): SubmarineReproducibilitySummary | null {
  if (!payload) {
    return null;
  }

  const reproducibilitySummary =
    "reproducibility_summary" in payload
      ? payload.reproducibility_summary
      : undefined;
  const parityAssessment =
    payload.environment_parity_assessment ?? payload.environment_fingerprint;
  if (!reproducibilitySummary && !parityAssessment) {
    return null;
  }

  const parityStatus =
    reproducibilitySummary?.parity_status ??
    parityAssessment?.parity_status ??
    "--";
  const reproducibilityStatus =
    reproducibilitySummary?.reproducibility_status ?? parityStatus;
  const profileId =
    reproducibilitySummary?.profile_id ?? parityAssessment?.profile_id ?? "--";
  const profileLabel = parityAssessment?.profile_label ?? profileId;
  const manifestPath =
    reproducibilitySummary?.manifest_virtual_path ??
    payload.provenance_manifest_virtual_path ??
    "--";

  return {
    manifestPath,
    profileId,
    profileLabel,
    parityStatus,
    reproducibilityStatus,
    parityStatusLabel:
      REPRODUCIBILITY_STATUS_LABELS[parityStatus] ?? parityStatus,
    reproducibilityStatusLabel:
      REPRODUCIBILITY_STATUS_LABELS[reproducibilityStatus] ??
      reproducibilityStatus,
    driftReasons:
      reproducibilitySummary?.drift_reasons?.filter(Boolean) ??
      parityAssessment?.drift_reasons?.filter(Boolean) ??
      [],
    recoveryGuidance:
      reproducibilitySummary?.recovery_guidance?.filter(Boolean) ??
      parityAssessment?.recovery_guidance?.filter(Boolean) ??
      [],
  };
}

export function buildSubmarineReportOverviewSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineReportOverviewSummary | null {
  const overview = payload?.report_overview;
  if (!overview) {
    return null;
  }

  const allowedClaimLevel = overview.allowed_claim_level ?? "--";
  const reviewStatus = overview.review_status ?? "--";
  const reproducibilityStatus = overview.reproducibility_status ?? "--";

  return {
    currentConclusion: overview.current_conclusion_zh ?? "--",
    allowedClaimLevel,
    allowedClaimLevelLabel:
      SCIENTIFIC_CLAIM_LEVEL_LABELS[allowedClaimLevel] ?? allowedClaimLevel,
    reviewStatus,
    reviewStatusLabel:
      REPORT_REVIEW_STATUS_LABELS[reviewStatus] ?? reviewStatus,
    reproducibilityStatus,
    reproducibilityStatusLabel:
      REPRODUCIBILITY_STATUS_LABELS[reproducibilityStatus] ??
      reproducibilityStatus,
    recommendedNextStep: overview.recommended_next_step_zh ?? "--",
  };
}

export function buildSubmarineConclusionSectionsSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineConclusionSectionSummary[] {
  return (payload?.conclusion_sections ?? []).filter(Boolean).map((item) => {
    const claimLevel = item.claim_level ?? "--";
    return {
      conclusionId: item.conclusion_id ?? "conclusion",
      title: item.title_zh ?? "--",
      summary: item.summary_zh ?? "--",
      claimLevel,
      claimLevelLabel:
        SCIENTIFIC_CLAIM_LEVEL_LABELS[claimLevel] ?? claimLevel,
      confidenceLabel: item.confidence_label ?? "--",
      inlineSourceRefs: item.inline_source_refs?.filter(Boolean) ?? [],
      evidenceGapNotes: item.evidence_gap_notes?.filter(Boolean) ?? [],
      artifactPaths: item.artifact_virtual_paths?.filter(Boolean) ?? [],
    };
  });
}

export function buildSubmarineEvidenceIndexSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineEvidenceIndexSummary | null {
  const groups = (payload?.evidence_index ?? []).filter(Boolean).map((item) => ({
    groupId: item.group_id ?? "evidence_group",
    groupTitle: item.group_title_zh ?? "--",
    artifactPaths: item.artifact_virtual_paths?.filter(Boolean) ?? [],
    provenanceManifestPath: item.provenance_manifest_virtual_path ?? "--",
  }));
  if (groups.length === 0) {
    return null;
  }

  return {
    groupCount: groups.length,
    groups,
  };
}

export function buildSubmarineScientificGateSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineScientificGateSummary | null {
  const summary = payload?.scientific_supervisor_gate;
  if (!summary) {
    return null;
  }

  return {
    gateStatus: summary.gate_status ?? "--",
    allowedClaimLevel: summary.allowed_claim_level ?? "--",
    sourceReadinessStatus: summary.source_readiness_status ?? "--",
    recommendedStage: summary.recommended_stage ?? "--",
    remediationStage: summary.remediation_stage ?? "--",
    gateStatusLabel:
      SCIENTIFIC_GATE_STATUS_LABELS[summary.gate_status ?? ""] ??
      summary.gate_status ??
      "--",
    allowedClaimLevelLabel:
      SCIENTIFIC_CLAIM_LEVEL_LABELS[summary.allowed_claim_level ?? ""] ??
      summary.allowed_claim_level ??
      "--",
    sourceReadinessLabel:
      RESEARCH_EVIDENCE_READINESS_LABELS[summary.source_readiness_status ?? ""] ??
      summary.source_readiness_status ??
      "--",
    recommendedStageLabel:
      SCIENTIFIC_GATE_STAGE_LABELS[summary.recommended_stage ?? ""] ??
      summary.recommended_stage ??
      "--",
    remediationStageLabel:
      SCIENTIFIC_GATE_STAGE_LABELS[summary.remediation_stage ?? ""] ??
      summary.remediation_stage ??
      "--",
    blockingReasons: summary.blocking_reasons?.filter(Boolean) ?? [],
    advisoryNotes: summary.advisory_notes?.filter(Boolean) ?? [],
    artifactPaths: summary.artifact_virtual_paths?.filter(Boolean) ?? [],
  };
}

export function buildSubmarineScientificRemediationSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineScientificRemediationSummary | null {
  const summary = payload?.scientific_remediation_summary;
  if (!summary) {
    return null;
  }

  return {
    planStatusLabel:
      SCIENTIFIC_REMEDIATION_PLAN_STATUS_LABELS[summary.plan_status ?? ""] ??
      summary.plan_status ??
      "--",
    currentClaimLevelLabel:
      SCIENTIFIC_CLAIM_LEVEL_LABELS[summary.current_claim_level ?? ""] ??
      summary.current_claim_level ??
      "--",
    targetClaimLevelLabel:
      SCIENTIFIC_CLAIM_LEVEL_LABELS[summary.target_claim_level ?? ""] ??
      summary.target_claim_level ??
      "--",
    recommendedStageLabel:
      SCIENTIFIC_GATE_STAGE_LABELS[summary.recommended_stage ?? ""] ??
      summary.recommended_stage ??
      "--",
    artifactPaths: summary.artifact_virtual_paths?.filter(Boolean) ?? [],
    actions: (summary.actions ?? []).filter(Boolean).map((item) => ({
      actionId: item.action_id ?? "unknown",
      title: item.title ?? "--",
      summary: item.summary ?? "--",
      ownerStage: item.owner_stage ?? "--",
      ownerStageLabel:
        SCIENTIFIC_GATE_STAGE_LABELS[item.owner_stage ?? ""] ??
        item.owner_stage ??
        "--",
      priority: item.priority ?? "--",
      executionMode: item.execution_mode ?? "--",
      executionModeLabel:
        SCIENTIFIC_REMEDIATION_EXECUTION_MODE_LABELS[item.execution_mode ?? ""] ??
        item.execution_mode ??
        "--",
      status: item.status ?? "--",
      statusLabel:
        SCIENTIFIC_REMEDIATION_ACTION_STATUS_LABELS[item.status ?? ""] ??
        item.status ??
        "--",
      evidenceGap: item.evidence_gap ?? "--",
      requiredArtifacts: item.required_artifacts?.filter(Boolean) ?? [],
    })),
  };
}

function formatSummaryValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "--";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  try {
    const serialized = JSON.stringify(value);
    return serialized ?? "--";
  } catch {
    return Object.prototype.toString.call(value);
  }
}

export function buildSubmarineScientificRemediationHandoffSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineScientificRemediationHandoffSummary | null {
  const summary = payload?.scientific_remediation_handoff;
  if (!summary) {
    return null;
  }

  return {
    handoffStatusLabel:
      SCIENTIFIC_REMEDIATION_HANDOFF_STATUS_LABELS[summary.handoff_status ?? ""] ??
      summary.handoff_status ??
      "--",
    recommendedActionId: summary.recommended_action_id ?? "none",
    toolName: summary.tool_name ?? "manual_only",
    reason: summary.reason ?? "--",
    artifactPaths: summary.artifact_virtual_paths?.filter(Boolean) ?? [],
    toolArgs: Object.entries(summary.tool_args ?? {}).map(([key, value]) => ({
      key,
      value: formatSummaryValue(value),
    })),
    manualActions: (summary.manual_actions ?? []).filter(Boolean).map((item) => ({
      actionId: item.action_id ?? "unknown",
      title: item.title ?? "--",
      ownerStage: item.owner_stage ?? "--",
      ownerStageLabel:
        SCIENTIFIC_GATE_STAGE_LABELS[item.owner_stage ?? ""] ??
        item.owner_stage ??
        "--",
      evidenceGap: item.evidence_gap ?? "--",
    })),
  };
}

export function buildSubmarineDeliveryDecisionSummary(
  payload:
    | {
        delivery_decision_summary?: SubmarineDeliveryDecisionSummaryPayload | null;
        decision_status?: string | null;
      }
    | null
    | undefined,
): SubmarineDeliveryDecisionSummary | null {
  const summary = payload?.delivery_decision_summary;
  if (!summary && !payload?.decision_status) {
    return null;
  }

  const decisionStatus = summary?.decision_status ?? payload?.decision_status ?? "--";
  const options = (summary?.options ?? []).filter(Boolean).map((item) => ({
    optionId: item.option_id ?? "unknown",
    label: item.label_zh ?? item.option_id ?? "--",
    summary: item.summary_zh ?? "--",
    followupKind: item.followup_kind ?? "--",
    followupKindLabel:
      DELIVERY_DECISION_FOLLOWUP_KIND_LABELS[item.followup_kind ?? ""] ??
      item.followup_kind ??
      "--",
    requiresAdditionalExecution: Boolean(item.requires_additional_execution),
  }));
  const recommendedOptionId = summary?.recommended_option_id ?? "none";
  const recommendedOptionLabel =
    options.find((item) => item.optionId === recommendedOptionId)?.label ??
    recommendedOptionId;

  return {
    decisionStatus,
    decisionStatusLabel:
      DELIVERY_DECISION_STATUS_LABELS[decisionStatus] ?? decisionStatus,
    question: summary?.decision_question_zh ?? DELIVERY_DECISION_CHAT_PROMPT,
    chatPrompt: DELIVERY_DECISION_CHAT_PROMPT,
    recommendedOptionId,
    recommendedOptionLabel,
    options,
    blockingReasons: summary?.blocking_reason_lines?.filter(Boolean) ?? [],
    advisoryNotes: summary?.advisory_note_lines?.filter(Boolean) ?? [],
    artifactPaths: summary?.artifact_virtual_paths?.filter(Boolean) ?? [],
  };
}

export function buildSubmarineScientificFollowupSummary(
  payload: SubmarineFinalReportPayload | null | undefined,
): SubmarineScientificFollowupSummary | null {
  const summary = payload?.scientific_followup_summary;
  if (!summary) {
    return null;
  }

  return {
    entryCount:
      typeof summary.entry_count === "number" && Number.isFinite(summary.entry_count)
        ? summary.entry_count
        : 0,
    latestOutcomeLabel:
      SCIENTIFIC_FOLLOWUP_OUTCOME_LABELS[summary.latest_outcome_status ?? ""] ??
      summary.latest_outcome_status ??
      "--",
    latestHandoffStatusLabel:
      SCIENTIFIC_REMEDIATION_HANDOFF_STATUS_LABELS[
        summary.latest_handoff_status ?? ""
      ] ??
      summary.latest_handoff_status ??
      "--",
    latestRecommendedActionId: summary.latest_recommended_action_id ?? "none",
    latestToolName: summary.latest_tool_name ?? "none",
    latestFollowupKind: summary.latest_followup_kind ?? "none",
    latestFollowupKindLabel:
      SCIENTIFIC_FOLLOWUP_KIND_LABELS[summary.latest_followup_kind ?? ""] ??
      summary.latest_followup_kind ??
      "none",
    latestDecisionSummary: summary.latest_decision_summary_zh ?? "--",
    latestSourceConclusionIds:
      summary.latest_source_conclusion_ids?.filter(Boolean) ?? [],
    latestSourceEvidenceGapIds:
      summary.latest_source_evidence_gap_ids?.filter(Boolean) ?? [],
    latestDispatchStageStatusLabel:
      DISPATCH_STAGE_STATUS_LABELS[summary.latest_dispatch_stage_status ?? ""] ??
      summary.latest_dispatch_stage_status ??
      "none",
    reportRefreshedLabel: summary.report_refreshed ? "Yes" : "No",
    historyPath: summary.history_virtual_path ?? "--",
    latestResultReportPath: summary.latest_result_report_virtual_path ?? "--",
    latestResultProvenanceManifestPath:
      summary.latest_result_provenance_manifest_virtual_path ?? "--",
    latestResultHandoffPath:
      summary.latest_result_supervisor_handoff_virtual_path ?? "--",
    latestNotes: summary.latest_notes?.filter(Boolean) ?? [],
    artifactPaths: summary.artifact_virtual_paths?.filter(Boolean) ?? [],
  };
}

function collectOutputArtifacts(outputId: string, artifactPaths: string[]) {
  const suffixes = RESULT_CARD_ARTIFACT_SUFFIXES[outputId] ?? [];
  const matchedPaths: string[] = [];

  for (const suffix of suffixes) {
    for (const path of artifactPaths) {
      if (path.endsWith(suffix) && !matchedPaths.includes(path)) {
        matchedPaths.push(path);
      }
    }
  }

  return matchedPaths;
}

function mergeArtifactPaths(...groups: Array<string[]>) {
  const merged: string[] = [];
  for (const group of groups) {
    for (const path of group) {
      if (path && !merged.includes(path)) {
        merged.push(path);
      }
    }
  }
  return merged;
}

export function buildSubmarineResultCards({
  requestedOutputs,
  outputDelivery,
  figureDelivery,
  artifactPaths,
}: {
  requestedOutputs?: SubmarineDesignBriefSummary["requestedOutputs"] | null;
  outputDelivery?: SubmarineAcceptanceSummary["outputDelivery"] | null;
  figureDelivery?: SubmarineFigureDeliverySummary | null;
  artifactPaths?: string[] | null;
}): SubmarineResultCard[] {
  const requested = requestedOutputs ?? [];
  const delivery = outputDelivery ?? [];
  const availableArtifacts = artifactPaths ?? [];
  const requestedById = new Map(requested.map((item) => [item.outputId, item]));
  const deliveryById = new Map(delivery.map((item) => [item.outputId, item]));
  const figureByOutputId = new Map(
    (figureDelivery?.figures ?? []).map((item) => [item.outputId, item]),
  );
  const orderedIds = [
    ...requested.map((item) => item.outputId),
    ...delivery
      .map((item) => item.outputId)
      .filter((outputId) => !requestedById.has(outputId)),
  ];

  return orderedIds.map((outputId) => {
    const requestedItem = requestedById.get(outputId);
    const deliveryItem = deliveryById.get(outputId);
    const figureItem = figureByOutputId.get(outputId);
    const matchedArtifactPaths = collectOutputArtifacts(outputId, availableArtifacts);
    const figureArtifactPaths = mergeArtifactPaths(
      figureItem?.artifactPaths ?? [],
      figureItem && figureDelivery?.manifestPath && figureDelivery.manifestPath !== "--"
        ? [figureDelivery.manifestPath]
        : [],
    );
    const combinedArtifactPaths = mergeArtifactPaths(
      deliveryItem?.artifactPaths ?? [],
      matchedArtifactPaths,
      figureArtifactPaths,
    );
    const previewArtifactPath =
      combinedArtifactPaths.find((path) => path.endsWith(".png")) ?? null;
    const artifacts = combinedArtifactPaths.map((path) => ({
      path,
      ...getSubmarineArtifactMeta(path),
    }));
    const label =
      deliveryItem?.label ??
      requestedItem?.label ??
      requestedItem?.requestedLabel ??
      outputId;

    return {
      outputId,
      label,
      requestedLabel:
        requestedItem?.requestedLabel ?? requestedItem?.label ?? label,
      supportLevel: requestedItem?.supportLevel ?? "--",
      deliveryStatus: deliveryItem?.deliveryStatus ?? "requested",
      specSummary:
        deliveryItem?.specSummary && deliveryItem.specSummary !== "--"
          ? deliveryItem.specSummary
          : requestedItem?.specSummary ?? "--",
      detail: deliveryItem?.detail ?? requestedItem?.notes ?? "--",
      figureCaption: figureItem?.caption ?? "--",
      selectorSummary: figureItem?.selectorSummary ?? "--",
      figureRenderStatus: figureItem?.renderStatusLabel ?? "--",
      previewArtifactPath,
      artifactPaths: combinedArtifactPaths,
      figureArtifactPaths,
      artifacts,
    };
  });
}
