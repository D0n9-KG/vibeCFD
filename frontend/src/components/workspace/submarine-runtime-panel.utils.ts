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
  previewArtifactPath: string | null;
  artifactPaths: string[];
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
    path.endsWith("/study-manifest.json")
  ) {
    return "planning";
  }

  if (
    path.endsWith("/delivery-readiness.md") ||
    path.endsWith("/delivery-readiness.json") ||
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
    path.endsWith("/verification-mesh-independence.json") ||
    path.endsWith("/verification-domain-sensitivity.json") ||
    path.endsWith("/verification-time-step-sensitivity.json")
  ) {
    return "results";
  }

  if (
    path.endsWith("/openfoam-run.log") ||
    path.endsWith("/openfoam-request.json") ||
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

export function buildSubmarineResultCards({
  requestedOutputs,
  outputDelivery,
  artifactPaths,
}: {
  requestedOutputs?: SubmarineDesignBriefSummary["requestedOutputs"] | null;
  outputDelivery?: SubmarineAcceptanceSummary["outputDelivery"] | null;
  artifactPaths?: string[] | null;
}): SubmarineResultCard[] {
  const requested = requestedOutputs ?? [];
  const delivery = outputDelivery ?? [];
  const availableArtifacts = artifactPaths ?? [];
  const requestedById = new Map(requested.map((item) => [item.outputId, item]));
  const deliveryById = new Map(delivery.map((item) => [item.outputId, item]));
  const orderedIds = [
    ...requested.map((item) => item.outputId),
    ...delivery
      .map((item) => item.outputId)
      .filter((outputId) => !requestedById.has(outputId)),
  ];

  return orderedIds.map((outputId) => {
    const requestedItem = requestedById.get(outputId);
    const deliveryItem = deliveryById.get(outputId);
    const matchedArtifactPaths = collectOutputArtifacts(outputId, availableArtifacts);
    const previewArtifactPath =
      matchedArtifactPaths.find((path) => path.endsWith(".png")) ?? null;
    const artifacts = matchedArtifactPaths.map((path) => ({
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
      previewArtifactPath,
      artifactPaths: matchedArtifactPaths,
      artifacts,
    };
  });
}
