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

export type SubmarineArtifactMeta = {
  label: string;
  externalLinkLabel: string;
};

export type SubmarineSimulationRequirements = {
  inlet_velocity_mps?: number | null;
  fluid_density_kg_m3?: number | null;
  kinematic_viscosity_m2ps?: number | null;
  end_time_seconds?: number | null;
  delta_t_seconds?: number | null;
  write_interval_steps?: number | null;
};

export type SubmarineExecutionOutlineItem = {
  role_id?: string | null;
  owner?: string | null;
  goal?: string | null;
  status?: string | null;
  target_skills?: string[] | null;
};

export type SubmarineDesignBriefPayload = {
  report_title?: string;
  summary_zh?: string;
  task_description?: string;
  task_type?: string;
  confirmation_status?: "draft" | "confirmed" | string;
  geometry_virtual_path?: string | null;
  geometry_family_hint?: string | null;
  selected_case_id?: string | null;
  simulation_requirements?: SubmarineSimulationRequirements | null;
  expected_outputs?: string[] | null;
  scientific_verification_requirements?:
    | Array<{
        requirement_id?: string | null;
        label?: string | null;
        summary_zh?: string | null;
        check_type?: string | null;
        required_artifacts?: string[] | null;
        force_coefficient?: string | null;
        minimum_history_samples?: number | null;
        max_tail_relative_spread?: number | null;
        max_value?: number | null;
      }>
    | null;
  requested_outputs?:
    | Array<{
        output_id?: string | null;
        label?: string | null;
        requested_label?: string | null;
        status?: string | null;
        support_level?: string | null;
        postprocess_spec?: Record<string, unknown> | null;
        notes?: string | null;
      }>
    | null;
  user_constraints?: string[] | null;
  open_questions?: string[] | null;
  execution_outline?: SubmarineExecutionOutlineItem[] | null;
  review_status?: string | null;
  next_recommended_stage?: string | null;
};

export type SubmarineDesignBriefSummary = {
  confirmationStatusLabel: string;
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
    owner: string;
    goal: string;
    status: string;
    targetSkills: string[];
  }>;
  requirementPairs: Array<{
    label: string;
    value: string;
  }>;
};

export type SubmarineAcceptanceAssessment = {
  status?: string | null;
  confidence?: string | null;
  blocking_issues?: string[] | null;
  warnings?: string[] | null;
  passed_checks?: string[] | null;
  benchmark_comparisons?:
    | Array<{
        metric_id?: string | null;
        quantity?: string | null;
        status?: string | null;
        observed_value?: number | null;
        reference_value?: number | null;
        relative_error?: number | null;
      }>
    | null;
};

export type SubmarineScientificVerificationAssessment = {
  status?: string | null;
  confidence?: string | null;
  blocking_issues?: string[] | null;
  missing_evidence?: string[] | null;
  passed_requirements?: string[] | null;
  requirements?:
    | Array<{
        requirement_id?: string | null;
        label?: string | null;
        status?: string | null;
        detail?: string | null;
      }>
    | null;
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

export type SubmarineScientificStudySummary = {
  executionStatusLabel: string;
  manifestPath: string;
  artifactPaths: string[];
  studies: Array<{
    studyType: string;
    summaryLabel: string;
    monitoredQuantity: string;
    variantCount: number;
    verificationStatus: string;
    verificationDetail: string;
  }>;
};

export type SubmarineExperimentSummary = {
  experimentId: string;
  experimentStatusLabel: string;
  baselineRunId: string;
  runCount: number;
  manifestPath: string;
  comparePath: string;
  compareNotes: string[];
};

export type SubmarineExperimentCompareSummary = {
  experimentId: string;
  baselineRunId: string;
  compareCount: number;
  comparePath: string;
  artifactPaths: string[];
  comparisons: Array<{
    candidateRunId: string;
    studyType: string;
    variantId: string;
    studyLabel: string;
    compareStatus: string;
    compareStatusLabel: string;
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
  readinessLabel: string;
  verificationStatusLabel: string;
  validationStatusLabel: string;
  provenanceStatusLabel: string;
  confidenceLabel: string;
  evidenceGaps: string[];
  passedEvidence: string[];
  benchmarkHighlights: string[];
  provenanceHighlights: string[];
  artifactPaths: string[];
};

export type SubmarineScientificGateSummary = {
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

export type SubmarineScientificFollowupSummary = {
  entryCount: number;
  latestOutcomeLabel: string;
  latestHandoffStatusLabel: string;
  latestRecommendedActionId: string;
  latestToolName: string;
  latestDispatchStageStatusLabel: string;
  reportRefreshedLabel: string;
  historyPath: string;
  latestResultReportPath: string;
  latestResultHandoffPath: string;
  latestNotes: string[];
  artifactPaths: string[];
};

export type SubmarineAcceptanceSummary = {
  statusLabel: string;
  confidenceLabel: string;
  blockingIssues: string[];
  warnings: string[];
  passedChecks: string[];
  outputDelivery: Array<{
    outputId: string;
    label: string;
    deliveryStatus: string;
    specSummary: string;
    detail: string;
  }>;
  benchmarkComparisons: Array<{
    metricId: string;
    quantity: string;
    status: string;
    observedValue: string;
    referenceValue: string;
    relativeError: string;
  }>;
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
  ready_for_review: "寰呭鏍?",
  blocked: "宸查樆濉? ",
};

const ACCEPTANCE_CONFIDENCE_LABELS: Record<string, string> = {
  high: "楂?",
  medium: "涓?",
  low: "浣?",
};

const SCIENTIFIC_VERIFICATION_STATUS_LABELS: Record<string, string> = {
  research_ready: "Research Ready",
  needs_more_verification: "Needs More Verification",
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
  completed: "Completed",
  blocked: "Blocked",
};

const EXPERIMENT_STATUS_LABELS: Record<string, string> = {
  planned: "Planned",
  completed: "Completed",
  blocked: "Blocked",
};

const EXPERIMENT_COMPARE_STATUS_LABELS: Record<string, string> = {
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

const SCIENTIFIC_GATE_STATUS_LABELS: Record<string, string> = {
  ready_for_claim: "Ready For Claim",
  claim_limited: "Claim Limited",
  blocked: "Blocked",
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
  "solver-dispatch": "Solver Dispatch",
  "result-reporting": "Result Reporting",
  "supervisor-review": "Supervisor Review",
};

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
      label: "浜や粯灏辩华",
      externalLinkLabel: "鍦ㄦ柊绐楀彛鎵撳紑浜や粯灏辩华",
    },
  ],
  [
    "/delivery-readiness.json",
    {
      label: "浜や粯灏辩华 JSON",
      externalLinkLabel: "鍦ㄦ柊绐楀彛鎵撳紑浜や粯灏辩华 JSON",
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

function normalizeExecutionOutline(
  items: SubmarineExecutionOutlineItem[] | null | undefined,
) {
  return (
    items
      ?.map((item) => ({
        roleId: item.role_id ?? "unknown",
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

  return {
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
    requirementPairs,
  };
}

export function buildSubmarineAcceptanceSummary(
  payload:
    | {
        acceptance_assessment?: SubmarineAcceptanceAssessment | null;
        requested_outputs?:
          | Array<{
              output_id?: string | null;
              postprocess_spec?: Record<string, unknown> | null;
            }>
          | null;
        output_delivery_plan?:
          | Array<{
              output_id?: string | null;
              label?: string | null;
              delivery_status?: string | null;
              detail?: string | null;
            }>
          | null;
      }
    | null
    | undefined,
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
      observedValue:
        typeof item.observed_value === "number"
          ? item.observed_value.toFixed(5)
          : "--",
      referenceValue:
        typeof item.reference_value === "number"
          ? item.reference_value.toFixed(5)
          : "--",
      relativeError:
        typeof item.relative_error === "number"
          ? `${(item.relative_error * 100).toFixed(2)}%`
          : "--",
    }));
  const requestedOutputSpecById = new Map(
    (payload?.requested_outputs ?? [])
      .filter(Boolean)
      .map((item) => [
        item.output_id ?? "unknown",
        formatPostprocessSpecSummary(item.postprocess_spec ?? null),
      ]),
  );
  const outputDelivery = (payload?.output_delivery_plan ?? [])
    .filter(Boolean)
    .map((item) => ({
      outputId: item.output_id ?? "unknown",
      label: item.label ?? "--",
      deliveryStatus: item.delivery_status ?? "--",
      specSummary:
        requestedOutputSpecById.get(item.output_id ?? "unknown") ?? "--",
      detail: item.detail ?? "--",
    }));

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

export function buildSubmarineScientificVerificationSummary(
  payload:
    | {
        scientific_verification_assessment?:
          | SubmarineScientificVerificationAssessment
          | null;
      }
    | null
    | undefined,
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
      status:
        item.status === "missing_evidence"
          ? "Missing Evidence"
          : item.status === "research_ready"
            ? "Research Ready"
            : item.status === "passed"
              ? "Passed"
              : item.status === "blocked"
                ? "Blocked"
                : item.status ?? "--",
      detail: item.detail ?? "--",
    })),
  };
}

export function buildSubmarineScientificStudySummary(
  payload:
    | {
        scientific_study_summary?:
          | {
              study_execution_status?: string | null;
              manifest_virtual_path?: string | null;
              artifact_virtual_paths?: string[] | null;
              studies?:
                | Array<{
                    study_type?: string | null;
                    summary_label?: string | null;
                    monitored_quantity?: string | null;
                    variant_count?: number | null;
                    verification_status?: string | null;
                    verification_detail?: string | null;
                  }>
                | null;
            }
          | null;
      }
    | null
    | undefined,
): SubmarineScientificStudySummary | null {
  const summary = payload?.scientific_study_summary;
  if (!summary) {
    return null;
  }

  return {
    executionStatusLabel:
      SCIENTIFIC_STUDY_EXECUTION_STATUS_LABELS[
        summary.study_execution_status ?? ""
      ] ??
      summary.study_execution_status ??
      "--",
    manifestPath: summary.manifest_virtual_path ?? "--",
    artifactPaths: summary.artifact_virtual_paths?.filter(Boolean) ?? [],
    studies: (summary.studies ?? []).filter(Boolean).map((item) => ({
      studyType: item.study_type ?? "unknown",
      summaryLabel: item.summary_label ?? "--",
      monitoredQuantity: item.monitored_quantity ?? "--",
      variantCount: item.variant_count ?? 0,
      verificationStatus:
        item.verification_status === "missing_evidence"
          ? "Missing Evidence"
          : item.verification_status === "research_ready"
            ? "Research Ready"
            : item.verification_status === "passed"
              ? "Passed"
              : item.verification_status === "blocked"
                ? "Blocked"
                : item.verification_status ?? "--",
      verificationDetail: item.verification_detail ?? "--",
    })),
  };
}

export function buildSubmarineExperimentSummary(
  payload:
    | {
        experiment_summary?:
          | {
              experiment_id?: string | null;
              experiment_status?: string | null;
              baseline_run_id?: string | null;
              run_count?: number | null;
              manifest_virtual_path?: string | null;
              compare_virtual_path?: string | null;
              compare_notes?: string[] | null;
            }
          | null;
      }
    | null
    | undefined,
): SubmarineExperimentSummary | null {
  const summary = payload?.experiment_summary;
  if (!summary) {
    return null;
  }

  return {
    experimentId: summary.experiment_id ?? "--",
    experimentStatusLabel:
      EXPERIMENT_STATUS_LABELS[summary.experiment_status ?? ""] ??
      summary.experiment_status ??
      "--",
    baselineRunId: summary.baseline_run_id ?? "--",
    runCount:
      typeof summary.run_count === "number" && Number.isFinite(summary.run_count)
        ? summary.run_count
        : 0,
    manifestPath: summary.manifest_virtual_path ?? "--",
    comparePath: summary.compare_virtual_path ?? "--",
    compareNotes: summary.compare_notes?.filter(Boolean) ?? [],
  };
}

export function buildSubmarineExperimentCompareSummary(
  payload:
    | {
        experiment_compare_summary?:
          | {
              experiment_id?: string | null;
              baseline_run_id?: string | null;
              compare_count?: number | null;
              compare_virtual_path?: string | null;
              artifact_virtual_paths?: string[] | null;
              comparisons?:
                | Array<{
                    candidate_run_id?: string | null;
                    study_type?: string | null;
                    variant_id?: string | null;
                    compare_status?: string | null;
                    notes?: string | null;
                    metric_deltas?: Record<string, unknown> | null;
                    baseline_solver_results_virtual_path?: string | null;
                    candidate_solver_results_virtual_path?: string | null;
                    baseline_run_record_virtual_path?: string | null;
                    candidate_run_record_virtual_path?: string | null;
                  }>
                | null;
            }
          | null;
      }
    | null
    | undefined,
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

      return {
        candidateRunId: item.candidate_run_id ?? "unknown",
        studyType,
        variantId,
        studyLabel: `${studyType} / ${variantId}`,
        compareStatus: item.compare_status ?? "--",
        compareStatusLabel:
          EXPERIMENT_COMPARE_STATUS_LABELS[item.compare_status ?? ""] ??
          item.compare_status ??
          "--",
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
  payload:
    | {
        figure_delivery_summary?:
          | {
              figure_count?: number | null;
              manifest_virtual_path?: string | null;
              artifact_virtual_paths?: string[] | null;
              figures?:
                | Array<{
                    figure_id?: string | null;
                    output_id?: string | null;
                    title?: string | null;
                    caption?: string | null;
                    render_status?: string | null;
                    selector_summary?: string | null;
                    field?: string | null;
                    artifact_virtual_paths?: string[] | null;
                    source_csv_virtual_path?: string | null;
                  }>
                | null;
            }
          | null;
      }
    | null
    | undefined,
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
  payload:
    | {
        research_evidence_summary?:
          | {
              readiness_status?: string | null;
              verification_status?: string | null;
              validation_status?: string | null;
              provenance_status?: string | null;
              confidence?: string | null;
              evidence_gaps?: string[] | null;
              passed_evidence?: string[] | null;
              benchmark_highlights?: string[] | null;
              provenance_highlights?: string[] | null;
              artifact_virtual_paths?: string[] | null;
            }
          | null;
      }
    | null
    | undefined,
): SubmarineResearchEvidenceSummary | null {
  const summary = payload?.research_evidence_summary;
  if (!summary) {
    return null;
  }

  return {
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
    evidenceGaps: summary.evidence_gaps?.filter(Boolean) ?? [],
    passedEvidence: summary.passed_evidence?.filter(Boolean) ?? [],
    benchmarkHighlights: summary.benchmark_highlights?.filter(Boolean) ?? [],
    provenanceHighlights: summary.provenance_highlights?.filter(Boolean) ?? [],
    artifactPaths: summary.artifact_virtual_paths?.filter(Boolean) ?? [],
  };
}

export function buildSubmarineScientificGateSummary(
  payload:
    | {
        scientific_supervisor_gate?:
          | {
              gate_status?: string | null;
              allowed_claim_level?: string | null;
              source_readiness_status?: string | null;
              recommended_stage?: string | null;
              remediation_stage?: string | null;
              blocking_reasons?: string[] | null;
              advisory_notes?: string[] | null;
              artifact_virtual_paths?: string[] | null;
            }
          | null;
      }
    | null
    | undefined,
): SubmarineScientificGateSummary | null {
  const summary = payload?.scientific_supervisor_gate;
  if (!summary) {
    return null;
  }

  return {
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
  payload:
    | {
        scientific_remediation_summary?:
          | {
              plan_status?: string | null;
              current_claim_level?: string | null;
              target_claim_level?: string | null;
              recommended_stage?: string | null;
              artifact_virtual_paths?: string[] | null;
              actions?:
                | Array<{
                    action_id?: string | null;
                    title?: string | null;
                    summary?: string | null;
                    owner_stage?: string | null;
                    priority?: string | null;
                    execution_mode?: string | null;
                    status?: string | null;
                    evidence_gap?: string | null;
                    required_artifacts?: string[] | null;
                  }>
                | null;
            }
          | null;
      }
    | null
    | undefined,
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
  payload:
    | {
        scientific_remediation_handoff?:
          | {
              handoff_status?: string | null;
              recommended_action_id?: string | null;
              tool_name?: string | null;
              tool_args?: Record<string, unknown> | null;
              reason?: string | null;
              artifact_virtual_paths?: string[] | null;
              manual_actions?:
                | Array<{
                    action_id?: string | null;
                    title?: string | null;
                    owner_stage?: string | null;
                    evidence_gap?: string | null;
                  }>
                | null;
            }
          | null;
      }
    | null
    | undefined,
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

export function buildSubmarineScientificFollowupSummary(
  payload:
    | {
        scientific_followup_summary?:
          | {
              history_virtual_path?: string | null;
              entry_count?: number | null;
              latest_outcome_status?: string | null;
              latest_handoff_status?: string | null;
              latest_recommended_action_id?: string | null;
              latest_tool_name?: string | null;
              latest_dispatch_stage_status?: string | null;
              report_refreshed?: boolean | null;
              latest_result_report_virtual_path?: string | null;
              latest_result_supervisor_handoff_virtual_path?: string | null;
              latest_notes?: string[] | null;
              artifact_virtual_paths?: string[] | null;
            }
          | null;
      }
    | null
    | undefined,
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
    latestDispatchStageStatusLabel:
      DISPATCH_STAGE_STATUS_LABELS[summary.latest_dispatch_stage_status ?? ""] ??
      summary.latest_dispatch_stage_status ??
      "none",
    reportRefreshedLabel: summary.report_refreshed ? "Yes" : "No",
    historyPath: summary.history_virtual_path ?? "--",
    latestResultReportPath: summary.latest_result_report_virtual_path ?? "--",
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
