import assert from "node:assert/strict";
import test from "node:test";

import type { SubmarineFinalReportPayload } from "./submarine-runtime-panel.contract";

const {
  buildSubmarineAcceptanceSummary,
  buildSubmarineConclusionSectionsSummary,
  buildSubmarineDesignBriefSummary,
  buildSubmarineEvidenceIndexSummary,
  buildSubmarineStageTrack,
  buildSubmarineExperimentCompareSummary,
  buildSubmarineExperimentSummary,
  buildSubmarineFigureDeliverySummary,
  buildSubmarineOutputDeliverySummary,
  buildSubmarineReportOverviewSummary,
  buildSubmarineResearchEvidenceSummary,
  buildSubmarineReproducibilitySummary,
  buildSubmarineExecutionOutline,
  buildSubmarineResultCards,
  buildSubmarineDeliveryDecisionSummary,
  formatSubmarineBenchmarkComparisonSummaryLine,
  formatSubmarineExecutionRoleLabel,
  formatSubmarineRuntimeStageLabel,
  buildSubmarineScientificGateSummary,
  buildSubmarineScientificFollowupSummary,
  buildSubmarineScientificRemediationHandoffSummary,
  buildSubmarineScientificRemediationSummary,
  buildSubmarineStabilityEvidenceSummary,
  buildSubmarineScientificStudySummary,
  buildSubmarineScientificVerificationSummary,
  filterSubmarineArtifactGroups,
  getSubmarineArtifactFilterOptions,
  getSubmarineArtifactMeta,
  groupSubmarineArtifacts,
} = await import(
  new URL("./submarine-runtime-panel.utils.ts", import.meta.url).href,
);

void test("groups submarine artifacts into stable workbench sections", () => {
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/skill-studio/demo/validation-report.md",
    "/mnt/user-data/outputs/submarine/design-brief/demo/cfd-design-brief.md",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/openfoam-request.json",
    "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/openfoam-run.log",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
    "/mnt/user-data/outputs/submarine/geometry-check/demo/geometry-check.md",
  ]);

  assert.deepEqual(
    groups.map((group) => group.id),
    ["planning", "report", "results", "execution", "inspection"],
  );
  assert.equal(groups[0]?.label, "方案设计");
  assert.equal(groups[0]?.count, 2);
});

void test("builds stable artifact filter options with an all bucket first", () => {
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/design-brief/demo/cfd-design-brief.md",
    "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
    "/mnt/user-data/outputs/submarine/reports/demo/final-report.html",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
  ]);

  const options = getSubmarineArtifactFilterOptions(groups);

  assert.deepEqual(
    options.map((option) => option.id),
    ["all", "planning", "report", "results"],
  );
  assert.equal(options[0]?.count, 4);
});

void test("filters artifact groups down to the selected bucket", () => {
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
    "/mnt/user-data/outputs/submarine/reports/demo/final-report.html",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
  ]);

  const filtered = filterSubmarineArtifactGroups(groups, "results");

  assert.equal(filtered.length, 1);
  assert.equal(filtered[0]?.id, "results");
  assert.equal(filtered[0]?.count, 1);
  assert.deepEqual(filtered[0]?.paths, [
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
  ]);
});

void test("keeps unknown artifacts in the fallback bucket", () => {
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/custom/demo/mesh-cut.png",
  ]);

  assert.deepEqual(groups, [
    {
      id: "other",
      label: "其他产物",
      count: 1,
      paths: ["/mnt/user-data/outputs/submarine/custom/demo/mesh-cut.png"],
    },
  ]);
});

void test("treats exported postprocess artifacts as results", () => {
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.png",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/wake-velocity-slice.md",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/wake-velocity-slice.png",
  ]);
  const pressureMeta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.png",
  );

  assert.deepEqual(
    groups.map((group) => group.id),
    ["results"],
  );
  assert.equal(groups[0]?.count, 4);
  assert.equal(pressureMeta.label, "表面压力图 PNG");
});

void test("returns accessible labels for submarine artifact actions", () => {
  const meta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/design-brief/demo/cfd-design-brief.md",
  );

  assert.equal(meta.label, "CFD 设计简报");
  assert.equal(meta.externalLinkLabel, "在新窗口打开 CFD 设计简报");
});

void test("returns skill-studio labels for authored skill artifacts", () => {
  const meta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/skill-studio/result-acceptance/validation-report.md",
  );

  assert.equal(meta.label, "Skill 校验报告");
  assert.equal(meta.externalLinkLabel, "在新窗口打开 Skill 校验报告");
});

void test("builds a design brief summary from the structured brief payload", () => {
  const summary = buildSubmarineDesignBriefSummary({
    confirmation_status: "draft",
    expected_outputs: ["阻力系数 Cd", "中文结果报告"],
    requested_outputs: [
      {
        output_id: "drag_coefficient",
        label: "阻力系数 Cd",
        requested_label: "阻力系数 Cd",
        status: "requested",
        support_level: "supported",
      },
      {
        output_id: "streamlines",
        label: "表面压力云图",
        requested_label: "表面压力云图",
        status: "requested",
        support_level: "not_yet_supported",
        postprocess_spec: {
          field: "U",
          time_mode: "latest",
          selector: {
            type: "plane",
            origin_mode: "x_by_lref",
            origin_value: 1.25,
            normal: [1, 0, 0],
          },
          formats: ["csv", "png", "report"],
        },
      },
    ],
    user_constraints: ["先做单工况基线"],
    open_questions: ["是否补一个 5 m/s 对比工况"],
    calculation_plan: [
      {
        item_id: "geometry-length",
        category: "geometry",
        label: "Reference length",
        proposed_value: 4.356,
        unit: "m",
        source_label: "Geometry preflight",
        confidence: "medium",
        origin: "ai_suggestion",
        approval_state: "pending_researcher_confirmation",
        requires_immediate_confirmation: true,
        applicability_conditions: ["Assumes the uploaded STL is already meter-scaled."],
      },
      {
        item_id: "selected-case",
        category: "case",
        label: "Selected baseline case",
        proposed_value: "darpa_suboff_bare_hull_resistance",
        source_label: "Case library",
        confidence: "high",
        origin: "ai_suggestion",
        approval_state: "researcher_confirmed",
      },
    ],
    execution_outline: [
      {
        role_id: "claude-code-supervisor",
        owner: "Claude Code",
        goal: "与用户确认方案",
        status: "in_progress",
        target_skills: ["submarine-design-brief"],
      },
      {
        role_id: "solver-dispatch",
        owner: "DeerFlow",
        goal: "执行 OpenFOAM 求解",
        status: "pending",
        target_skills: ["submarine-solver-dispatch"],
      },
    ],
    simulation_requirements: {
      inlet_velocity_mps: 7.5,
      fluid_density_kg_m3: 998.2,
      kinematic_viscosity_m2ps: 8.5e-7,
      end_time_seconds: 600,
      delta_t_seconds: 0.5,
      write_interval_steps: 20,
    },
  });

  assert.equal(summary?.confirmationStatusLabel, "待确认");
  assert.deepEqual(summary?.expectedOutputs, ["阻力系数 Cd", "中文结果报告"]);
  assert.deepEqual(summary?.userConstraints, ["先做单工况基线"]);
  assert.deepEqual(summary?.openQuestions, ["是否补一个 5 m/s 对比工况"]);
  assert.equal(summary?.precomputeApprovalLabel, "需要立即补充确认");
  assert.equal(summary?.pendingCalculationPlanCount, 1);
  assert.equal(summary?.immediateClarificationCount, 1);
  assert.equal(summary?.calculationPlan.length, 2);
  assert.equal(summary?.calculationPlan[0]?.approvalStateLabel, "待研究确认");
  assert.equal(summary?.calculationPlan[0]?.originLabel, "AI 建议");
  assert.equal(summary?.executionOutline.length, 2);
  assert.equal(summary?.executionOutline[0]?.status, "进行中");
  assert.deepEqual(summary?.executionOutline[0]?.targetSkills, [
    "submarine-design-brief",
  ]);
  assert.equal(summary?.requestedOutputs.length, 2);
  assert.equal(summary?.requestedOutputs[0]?.outputId, "drag_coefficient");
  assert.equal(summary?.requestedOutputs[1]?.supportLevel, "暂不支持");
  assert.equal(summary?.requestedOutputs[0]?.specSummary, "--");
  assert.equal(
    summary?.requestedOutputs[1]?.specSummary,
    "字段=U; 选择器=截面[x/Lref=1.25; normal=(1, 0, 0)]; 时序=latest; 格式=csv,png,report",
  );
  assert.equal(summary?.requirementPairs[0]?.label, "来流速度");
  assert.equal(summary?.requirementPairs[0]?.value, "7.50 m/s");
  assert.equal(summary?.requirementPairs.at(-1)?.value, "20 步");
});

void test("localizes english submarine brief content for runtime workbench views", () => {
  const summary = buildSubmarineDesignBriefSummary({
    confirmation_status: "draft",
    expected_outputs: ["requested outputs", "pre-solver checklist"],
    requested_outputs: [
      {
        output_id: "baseline_case",
        label: "recommended baseline case/template mapping",
        requested_label: "requested outputs",
        support_level: "needs_clarification",
        notes: "pre-solver checklist",
      },
    ],
    user_constraints: ["brief stays in draft"],
    open_questions: [
      "Should requested outputs stay limited to resistance baseline preparation?",
    ],
    execution_outline: [
      {
        role_id: "task-intelligence",
        owner: "DeerFlow task-intelligence",
        goal: "Match candidate cases, understand the task, and select the most relevant submarine CFD workflow template.",
        status: "in_progress",
      },
    ],
  });

  assert.deepEqual(summary?.expectedOutputs, ["输出范围", "求解前检查清单"]);
  assert.equal(summary?.requestedOutputs[0]?.requestedLabel, "输出范围");
  assert.equal(summary?.requestedOutputs[0]?.supportLevel, "待澄清");
  assert.equal(summary?.requestedOutputs[0]?.notes, "求解前检查清单");
  assert.equal(summary?.userConstraints[0], "简报保持草稿状态");
  assert.match(
    summary?.openQuestions[0] ?? "",
    /输出范围|阻力基线准备/u,
  );
  assert.equal(summary?.executionOutline[0]?.owner, "DeerFlow 任务理解");
  assert.equal(summary?.executionOutline[0]?.status, "进行中");
  assert.match(
    summary?.executionOutline[0]?.goal ?? "",
    /匹配候选案例/u,
  );
});

void test("localizes requested result card fields from backend english payloads", () => {
  const cards = buildSubmarineResultCards({
    requestedOutputs: [
      {
        outputId: "baseline_case",
        label: "recommended baseline case/template mapping",
        requestedLabel: "requested outputs",
        supportLevel: "needs_clarification",
        specSummary: "--",
        notes: "pre-solver checklist",
      },
    ],
    outputDelivery: [
      {
        outputId: "baseline_case",
        label: "recommended baseline case/template mapping",
        deliveryStatus: "pending",
        specSummary: "--",
        detail: "pre-solver checklist",
        artifactPaths: [],
      },
    ],
    figureDelivery: null,
    artifactPaths: [],
  });

  assert.equal(cards[0]?.label, "推荐基线案例/模板映射");
  assert.equal(cards[0]?.requestedLabel, "输出范围");
  assert.equal(cards[0]?.supportLevel, "待澄清");
  assert.equal(cards[0]?.deliveryStatus, "待处理");
  assert.equal(cards[0]?.detail, "求解前检查清单");
});

void test("localizes mixed-language submarine brief outputs before panel rendering", () => {
  const summary = buildSubmarineDesignBriefSummary({
    confirmation_status: "draft",
    expected_outputs: ["推荐 基线 case 映射"],
    requested_outputs: [
      {
        output_id: "baseline_case",
        label: "推荐 基线 case 映射",
        requested_label: "推荐 基线 case 映射",
        support_level: "needs_clarification",
        notes: "生成可审计的预检 artifact",
      },
    ],
  });

  assert.deepEqual(summary?.expectedOutputs, ["推荐基线案例映射"]);
  assert.equal(summary?.requestedOutputs[0]?.label, "推荐基线案例映射");
  assert.equal(summary?.requestedOutputs[0]?.requestedLabel, "推荐基线案例映射");
  assert.equal(summary?.requestedOutputs[0]?.notes, "生成可审计的预检产物");
});

void test("builds a reproducibility summary from parity-aware report payloads", () => {
  const summary = buildSubmarineReproducibilitySummary({
    provenance_manifest_virtual_path:
      "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest.json",
    environment_parity_assessment: {
      profile_id: "docker_compose_dev",
      profile_label: "Docker Compose Dev",
      parity_status: "drifted_but_runnable",
      drift_reasons: [
        "Host mount strategy `workspace_path` does not match expectations.",
      ],
      recovery_guidance: [
        "Align DEER_FLOW_RUNTIME_PROFILE with the active compose path.",
      ],
    },
    reproducibility_summary: {
      manifest_virtual_path:
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest.json",
      profile_id: "docker_compose_dev",
      parity_status: "drifted_but_runnable",
      reproducibility_status: "drifted_but_runnable",
      drift_reasons: [
        "Host mount strategy `workspace_path` does not match expectations.",
      ],
      recovery_guidance: [
        "Align DEER_FLOW_RUNTIME_PROFILE with the active compose path.",
      ],
    },
  } as SubmarineFinalReportPayload);

  assert.equal(
    summary?.manifestPath,
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest.json",
  );
  assert.equal(summary?.profileLabel, "Docker Compose Dev");
  assert.equal(summary?.parityStatusLabel, "环境漂移但仍可运行");
  assert.equal(summary?.reproducibilityStatusLabel, "环境漂移但仍可运行");
  assert.deepEqual(summary?.driftReasons, [
    "Host mount strategy `workspace_path` does not match expectations.",
  ]);
  assert.deepEqual(summary?.recoveryGuidance, [
    "Align DEER_FLOW_RUNTIME_PROFILE with the active compose path.",
  ]);
});

void test("builds a report overview summary from final report payloads", () => {
  const summary = buildSubmarineReportOverviewSummary({
    report_overview: {
      current_conclusion_zh: "当前结论可以用于交付说明，但仍需补齐外部验证证据。",
      allowed_claim_level: "validated_with_gaps",
      review_status: "ready_for_supervisor",
      reproducibility_status: "drifted_but_runnable",
      recommended_next_step_zh: "优先补齐外部基准对照，再决定是否提升结论等级。",
    },
  } as SubmarineFinalReportPayload);

  assert.equal(
    summary?.currentConclusion,
    "当前结论可以用于交付说明，但仍需补齐外部验证证据。",
  );
  assert.equal(summary?.allowedClaimLevelLabel, "已校核但仍有缺口");
  assert.equal(summary?.reviewStatusLabel, "待主管复核");
  assert.equal(summary?.reproducibilityStatusLabel, "环境漂移但仍可运行");
  assert.equal(
    summary?.recommendedNextStep,
    "优先补齐外部基准对照，再决定是否提升结论等级。",
  );
});

void test("builds conclusion section summaries from final report payloads", () => {
  const sections = buildSubmarineConclusionSectionsSummary({
    conclusion_sections: [
      {
        conclusion_id: "current_conclusion",
        title_zh: "当前研究结论",
        summary_zh: "当前结果已经形成面向交付的阻力结论。",
        claim_level: "verified_but_not_validated",
        confidence_label: "中",
        inline_source_refs: [
          "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
          "/mnt/user-data/outputs/submarine/reports/demo/supervisor-scientific-gate.json",
        ],
        evidence_gap_notes: ["缺少外部 benchmark 交叉验证。"],
        artifact_virtual_paths: [
          "/mnt/user-data/outputs/submarine/reports/demo/final-report.json",
        ],
      },
    ],
  } as SubmarineFinalReportPayload);

  assert.equal(sections.length, 1);
  assert.equal(sections[0]?.conclusionId, "current_conclusion");
  assert.equal(sections[0]?.title, "当前研究结论");
  assert.equal(sections[0]?.claimLevelLabel, "已验证但未外部校核");
  assert.deepEqual(sections[0]?.inlineSourceRefs, [
    "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
    "/mnt/user-data/outputs/submarine/reports/demo/supervisor-scientific-gate.json",
  ]);
  assert.deepEqual(sections[0]?.evidenceGapNotes, [
    "缺少外部 benchmark 交叉验证。",
  ]);
  assert.deepEqual(sections[0]?.artifactPaths, [
    "/mnt/user-data/outputs/submarine/reports/demo/final-report.json",
  ]);
});

void test("builds evidence index summaries from final report payloads", () => {
  const summary = buildSubmarineEvidenceIndexSummary({
    evidence_index: [
      {
        group_id: "research_evidence",
        group_title_zh: "研究证据与科学判断",
        artifact_virtual_paths: [
          "/mnt/user-data/outputs/submarine/reports/demo/research-evidence-summary.json",
          "/mnt/user-data/outputs/submarine/reports/demo/supervisor-scientific-gate.json",
        ],
        provenance_manifest_virtual_path:
          "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest.json",
      },
    ],
  } as SubmarineFinalReportPayload);

  assert.equal(summary?.groupCount, 1);
  assert.equal(summary?.groups[0]?.groupId, "research_evidence");
  assert.equal(summary?.groups[0]?.groupTitle, "研究证据与科学判断");
  assert.deepEqual(summary?.groups[0]?.artifactPaths, [
    "/mnt/user-data/outputs/submarine/reports/demo/research-evidence-summary.json",
    "/mnt/user-data/outputs/submarine/reports/demo/supervisor-scientific-gate.json",
  ]);
  assert.equal(
    summary?.groups[0]?.provenanceManifestPath,
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest.json",
  );
});

void test("prefers runtime execution plan over stale design brief outline", () => {
  const outline = buildSubmarineExecutionOutline({
    designBrief: {
      execution_outline: [
        {
          role_id: "claude-code-supervisor",
          owner: "Claude Code",
          goal: "旧设计简报状态",
          status: "completed",
        },
      ],
    },
    runtimePlan: [
      {
        role_id: "claude-code-supervisor",
        owner: "Claude Code",
        goal: "最新方案确认",
        status: "completed",
      },
      {
        role_id: "solver-dispatch",
        owner: "DeerFlow solver-dispatch",
        goal: "执行 OpenFOAM 求解",
        status: "in_progress",
        target_skills: ["submarine-solver-dispatch", "submarine-geometry-check"],
      },
    ],
  });

  assert.equal(outline.length, 2);
  assert.equal(outline[1]?.roleId, "solver-dispatch");
  assert.equal(outline[1]?.status, "进行中");
  assert.deepEqual(outline[1]?.targetSkills, [
    "submarine-solver-dispatch",
    "submarine-geometry-check",
  ]);
});

void test(
  "builds a dynamic stage track from the runtime execution plan when scientific roles exist",
  () => {
    const track = buildSubmarineStageTrack({
      runtimePlan: [
        {
          role_id: "claude-code-supervisor",
          status: "completed",
        },
        {
          role_id: "task-intelligence",
          status: "completed",
        },
        {
          role_id: "geometry-preflight",
          status: "completed",
        },
        {
          role_id: "solver-dispatch",
          status: "completed",
        },
        {
          role_id: "scientific-study",
          status: "completed",
        },
        {
          role_id: "experiment-compare",
          status: "completed",
        },
        {
          role_id: "scientific-verification",
          status: "ready",
        },
        {
          role_id: "result-reporting",
          status: "pending",
        },
        {
          role_id: "scientific-followup",
          status: "pending",
        },
        {
          role_id: "supervisor-review",
          status: "pending",
        },
      ],
    });

    assert.deepEqual(
      track.map((item) => item.stageId),
      [
        "claude-code-supervisor",
        "task-intelligence",
        "geometry-preflight",
        "solver-dispatch",
        "scientific-study",
        "experiment-compare",
        "scientific-verification",
        "result-reporting",
        "scientific-followup",
        "supervisor-review",
      ],
    );
    assert.equal(track[4]?.label, "科研研究");
    assert.equal(track[6]?.label, "科研校验");
    assert.equal(track[6]?.status, "ready");
    assert.equal(track[8]?.label, "科研跟进");
  },
);

void test("falls back to the legacy stage track when no runtime plan exists", () => {
  const track = buildSubmarineStageTrack({
    currentStage: "solver-dispatch",
  });

  assert.deepEqual(
    track.map((item) => item.stageId),
    [
      "task-intelligence",
      "geometry-preflight",
      "solver-dispatch",
      "result-reporting",
      "supervisor-review",
    ],
  );
  assert.equal(track[2]?.status, "in_progress");
  assert.equal(track[3]?.status, "pending");
});

void test("adds an explicit user-confirmation step to the legacy stage track when pre-compute approval is pending", () => {
  const track = buildSubmarineStageTrack({
    currentStage: "geometry-preflight",
    nextRecommendedStage: "user-confirmation",
  });

  assert.deepEqual(
    track.map((item) => item.stageId),
    [
      "task-intelligence",
      "geometry-preflight",
      "user-confirmation",
      "solver-dispatch",
      "result-reporting",
      "supervisor-review",
    ],
  );
  assert.equal(track[2]?.label, "用户确认");
  assert.equal(track[2]?.status, "ready");
});

void test("returns delivery-readiness labels for acceptance artifacts", () => {
  const meta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/reports/demo/delivery-readiness.json",
  );

  assert.equal(meta.label, "交付就绪评估 JSON");
  assert.equal(meta.externalLinkLabel, "在新窗口打开交付就绪评估 JSON");
});

void test("returns stable labels for scientific verification artifacts", () => {
  const meta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/verification-mesh-independence.json",
  );
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/verification-mesh-independence.json",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/verification-domain-sensitivity.json",
  ]);

  assert.equal(meta.label, "科研校验 - 网格无关性 JSON");
  assert.equal(groups[0]?.id, "results");
});

void test("returns stable labels for scientific supervisor gate artifacts", () => {
  const meta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/reports/demo/supervisor-scientific-gate.json",
  );
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/reports/demo/supervisor-scientific-gate.json",
  ]);

  assert.equal(meta.label, "科研主管闸门 JSON");
  assert.equal(
    meta.externalLinkLabel,
    "在新窗口打开科研主管闸门 JSON",
  );
  assert.equal(groups[0]?.id, "report");
});

void test("classifies stability evidence artifacts as result outputs", () => {
  const meta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/stability-evidence.json",
  );
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/stability-evidence.json",
  ]);

  assert.equal(meta.label, "稳定性证据 JSON");
  assert.equal(
    meta.externalLinkLabel,
    "在新窗口打开稳定性证据 JSON",
  );
  assert.equal(groups[0]?.id, "results");
});

void test("returns stable labels for scientific remediation handoff artifacts", () => {
  const meta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json",
  );
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-plan.json",
    "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json",
  ]);

  assert.equal(meta.label, "科研补救交接 JSON");
  assert.equal(
    meta.externalLinkLabel,
    "在新窗口打开科研补救交接 JSON",
  );
  assert.equal(groups[0]?.id, "report");
  assert.equal(groups[0]?.count, 2);
});

void test("classifies scientific followup history artifacts as report outputs", () => {
  const meta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json",
  );
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json",
  ]);

  assert.equal(meta.label, "科研跟进历史 JSON");
  assert.equal(
    meta.externalLinkLabel,
    "在新窗口打开科研跟进历史 JSON",
  );
  assert.equal(groups[0]?.id, "report");
  assert.equal(groups[0]?.count, 1);
});

void test("builds an acceptance summary from the final report payload", () => {
  const summary = buildSubmarineAcceptanceSummary({
    acceptance_assessment: {
      status: "ready_for_review",
      confidence: "medium",
      blocking_issues: [],
      warnings: ["Solver final time 200.0 is below planned end_time_seconds 600.0."],
      passed_checks: [
        "Solver completed successfully.",
        "Mesh quality checks passed.",
      ],
    },
  });

  assert.equal(summary?.statusLabel, "待复核");
  assert.equal(summary?.confidenceLabel, "中");
  assert.deepEqual(summary?.blockingIssues, []);
  assert.equal(summary?.warnings.length, 1);
  assert.equal(summary?.passedChecks.length, 2);
});

void test("builds runtime output delivery summaries with explicit artifact pointers", () => {
  const summary = buildSubmarineOutputDeliverySummary({
    requestedOutputs: [
      {
        output_id: "surface_pressure_contour",
        label: "表面压力云图",
        requested_label: "表面压力云图",
        support_level: "supported",
        postprocess_spec: {
          field: "p",
          time_mode: "latest",
          selector: {
            type: "patch",
            patches: ["hull"],
          },
          formats: ["csv", "png", "report"],
        },
      },
    ],
    outputDeliveryPlan: [
      {
        output_id: "surface_pressure_contour",
        label: "表面压力云图",
        delivery_status: "delivered",
        detail: "Pressure contour exported from the canonical solver bundle.",
        artifact_virtual_paths: [
          "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.png",
          "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
        ],
      },
    ],
  });

  assert.equal(summary.length, 1);
  assert.equal(summary[0]?.deliveryStatus, "已交付");
  assert.equal(
    summary[0]?.specSummary,
    "字段=p; 选择器=边界 patch[hull]; 时序=latest; 格式=csv,png,report",
  );
  assert.deepEqual(summary[0]?.artifactPaths, [
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.png",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
  ]);
});

void test("keeps benchmark comparisons in the acceptance summary", () => {
  const summary = buildSubmarineAcceptanceSummary({
    requested_outputs: [
      {
        output_id: "surface_pressure_contour",
        label: "表面压力云图",
        requested_label: "表面压力云图",
        support_level: "supported",
        postprocess_spec: {
          field: "p",
          time_mode: "latest",
          selector: {
            type: "patch",
            patches: ["hull"],
          },
          formats: ["csv", "png", "report"],
        },
      },
    ],
    acceptance_assessment: {
      status: "ready_for_review",
      confidence: "medium",
      blocking_issues: [],
      warnings: [],
      passed_checks: ["Solver completed successfully."],
      benchmark_comparisons: [
        {
          metric_id: "cd_at_3_05_mps",
          quantity: "Cd",
          status: "passed",
          detail:
            "Benchmark cd_at_3_05_mps observed Cd 0.00310 vs reference 0.00314; relative error 1.27% with tolerance 10.00%.",
          observed_value: 0.0031,
          reference_value: 0.00314,
          absolute_error: 0.00004,
          relative_error: 0.0127,
          relative_tolerance: 0.1,
          target_inlet_velocity_mps: 3.05,
          observed_inlet_velocity_mps: 3.05,
          source_label: "Mushtaque et al. (2025) Table 6, EFD bare hull",
          source_url:
            "https://pure.port.ac.uk/ws/portalfiles/portal/110702250/Hydrodynamic_parameter_estimation_of_DARPA_SUBOFF.pdf",
        },
      ],
    },
    output_delivery_plan: [
      {
        output_id: "drag_coefficient",
        label: "阻力系数 Cd",
        delivery_status: "delivered",
        detail: "Cd 已进入 solver metrics。",
      },
      {
        output_id: "surface_pressure_contour",
        label: "表面压力云图",
        delivery_status: "not_yet_supported",
        detail: "当前仓库尚未自动导出该图件 artifact。",
      },
    ],
  });

  assert.equal(summary?.benchmarkComparisons.length, 1);
  assert.equal(summary?.benchmarkComparisons[0]?.metricId, "cd_at_3_05_mps");
  assert.equal(summary?.benchmarkComparisons[0]?.status, "passed");
  assert.equal(summary?.benchmarkComparisons[0]?.statusLabel, "已通过");
  assert.equal(summary?.benchmarkComparisons[0]?.quantity, "Cd");
  assert.equal(summary?.benchmarkComparisons[0]?.absoluteError, "0.00004");
  assert.equal(summary?.benchmarkComparisons[0]?.relativeTolerance, "10.00%");
  assert.equal(summary?.benchmarkComparisons[0]?.targetVelocity, "3.05");
  assert.equal(summary?.benchmarkComparisons[0]?.observedVelocity, "3.05");
  assert.equal(
    summary?.benchmarkComparisons[0]?.sourceLabel,
    "Mushtaque et al. (2025) Table 6, EFD bare hull",
  );
  assert.equal(summary?.outputDelivery.length, 2);
  assert.equal(summary?.outputDelivery[0]?.outputId, "drag_coefficient");
  assert.equal(summary?.outputDelivery[1]?.deliveryStatus, "暂不支持");
  assert.equal(
    summary?.outputDelivery[1]?.specSummary,
    "字段=p; 选择器=边界 patch[hull]; 时序=latest; 格式=csv,png,report",
  );
  assert.equal(
    formatSubmarineBenchmarkComparisonSummaryLine(
      summary!.benchmarkComparisons[0],
    ),
    "cd_at_3_05_mps | 已通过 | Cd 0.00310 / 0.00314 | 误差 1.27% / 容差 10.00% | 速度 3.05 对比 3.05 m/s | 来源 Mushtaque et al. (2025) Table 6, EFD bare hull",
  );
});

void test(
  "builds structured result cards with preview artifacts for requested outputs",
  () => {
    const briefSummary = buildSubmarineDesignBriefSummary({
      requested_outputs: [
        {
          output_id: "surface_pressure_contour",
          label: "琛ㄩ潰鍘嬪姏浜戝浘",
          requested_label: "琛ㄩ潰鍘嬪姏浜戝浘",
          support_level: "supported",
          postprocess_spec: {
            field: "p",
            time_mode: "latest",
            selector: {
              type: "patch",
              patches: ["hull"],
            },
            formats: ["csv", "png", "report"],
          },
        },
        {
          output_id: "drag_coefficient",
          label: "闃诲姏绯绘暟 Cd",
          requested_label: "闃诲姏绯绘暟 Cd",
          support_level: "supported",
        },
      ],
    });
    const acceptanceSummary = buildSubmarineAcceptanceSummary({
      requested_outputs: [
        {
          output_id: "surface_pressure_contour",
          postprocess_spec: {
            field: "p",
            time_mode: "latest",
            selector: {
              type: "patch",
              patches: ["hull"],
            },
            formats: ["csv", "png", "report"],
          },
        },
      ],
      acceptance_assessment: {
        status: "ready_for_review",
        confidence: "high",
      },
      output_delivery_plan: [
        {
          output_id: "surface_pressure_contour",
          label: "琛ㄩ潰鍘嬪姏浜戝浘",
          delivery_status: "delivered",
          detail: "surface pressure artifacts exported.",
        },
        {
          output_id: "drag_coefficient",
          label: "闃诲姏绯绘暟 Cd",
          delivery_status: "delivered",
          detail: "Cd captured in solver metrics.",
        },
      ],
    });
    const figureDeliverySummary = buildSubmarineFigureDeliverySummary({
      figure_delivery_summary: {
        figure_count: 1,
        manifest_virtual_path:
          "/mnt/user-data/outputs/submarine/solver-dispatch/demo/figure-manifest.json",
        artifact_virtual_paths: [
          "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.png",
          "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
          "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.md",
        ],
        figures: [
          {
            figure_id: "demo:surface_pressure_contour",
            output_id: "surface_pressure_contour",
            title: "Surface Pressure Result",
            caption:
              "Surface pressure contour over the selected hull patches, colored by p.",
            render_status: "rendered",
            selector_summary: "Patch selection: hull",
            field: "p",
            artifact_virtual_paths: [
              "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.png",
              "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
              "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.md",
            ],
            source_csv_virtual_path:
              "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
          },
        ],
      },
    });

    const cards = buildSubmarineResultCards({
      requestedOutputs: briefSummary?.requestedOutputs,
      outputDelivery: acceptanceSummary?.outputDelivery,
      figureDelivery: figureDeliverySummary,
      artifactPaths: [
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.png",
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.md",
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
        "/mnt/user-data/outputs/submarine/reports/demo/final-report.json",
      ],
    });

    assert.equal(cards.length, 2);
    assert.equal(cards[0]?.outputId, "surface_pressure_contour");
    assert.equal(cards[0]?.deliveryStatus, "已交付");
    assert.equal(
      cards[0]?.previewArtifactPath,
      "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.png",
    );
    assert.deepEqual(
      cards[0]?.artifactPaths,
      [
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.png",
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.md",
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/figure-manifest.json",
      ],
    );
    assert.equal(
      cards[0]?.specSummary,
      "字段=p; 选择器=边界 patch[hull]; 时序=latest; 格式=csv,png,report",
    );
    assert.equal(
      cards[0]?.figureCaption,
      "Surface pressure contour over the selected hull patches, colored by p.",
    );
    assert.equal(cards[0]?.selectorSummary, "Patch selection: hull");
    assert.equal(cards[0]?.figureRenderStatus, "已渲染");
    assert.deepEqual(cards[0]?.figureArtifactPaths, [
      "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.png",
      "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
      "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.md",
      "/mnt/user-data/outputs/submarine/solver-dispatch/demo/figure-manifest.json",
    ]);
    assert.equal(cards[1]?.outputId, "drag_coefficient");
    assert.equal(cards[1]?.previewArtifactPath, null);
    assert.deepEqual(
      cards[1]?.artifactPaths,
      [
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
        "/mnt/user-data/outputs/submarine/reports/demo/final-report.json",
      ],
    );
  },
);

void test(
  "prefers explicit output-delivery artifact pointers when runtime cards do not have suffix-matched artifacts",
  () => {
    const cards = buildSubmarineResultCards({
      requestedOutputs: [
        {
          outputId: "drag_coefficient",
          label: "Drag coefficient",
          requestedLabel: "Cd",
          supportLevel: "supported",
          specSummary: "--",
          notes: "Requested from runtime snapshot.",
        },
      ],
      outputDelivery: [
        {
          outputId: "drag_coefficient",
          label: "Drag coefficient",
          deliveryStatus: "delivered",
          specSummary: "--",
          detail: "Delivered through solver-results.json.",
          artifactPaths: [
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
          ],
        },
      ],
      artifactPaths: [],
    });

    assert.equal(cards.length, 1);
    assert.deepEqual(cards[0]?.artifactPaths, [
      "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
    ]);
    assert.equal(cards[0]?.previewArtifactPath, null);
  },
);

void test("builds a figure delivery summary from the final report payload", () => {
  const summary = buildSubmarineFigureDeliverySummary({
    figure_delivery_summary: {
      figure_count: 2,
      manifest_virtual_path:
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/figure-manifest.json",
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/wake-velocity-slice.csv",
      ],
      figures: [
        {
          figure_id: "demo:surface_pressure_contour",
          output_id: "surface_pressure_contour",
          title: "Surface Pressure Result",
          caption:
            "Surface pressure contour over the selected hull patches, colored by p.",
          render_status: "rendered",
          selector_summary: "Patch selection: hull",
          field: "p",
          artifact_virtual_paths: [
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
          ],
          source_csv_virtual_path:
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
        },
        {
          figure_id: "demo:wake_velocity_slice",
          output_id: "wake_velocity_slice",
          title: "Wake Velocity Slice",
          caption:
            "Wake velocity slice extracted from the requested cutting plane, colored by |U|.",
          render_status: "rendered",
          selector_summary:
            "Plane slice at x/Lref=1.25 with normal (1.0, 0.0, 0.0)",
          field: "U",
          artifact_virtual_paths: [
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/wake-velocity-slice.csv",
          ],
          source_csv_virtual_path:
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/wake-velocity-slice.csv",
        },
      ],
    },
  });

  assert.equal(summary?.figureCount, 2);
  assert.equal(
    summary?.manifestPath,
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/figure-manifest.json",
  );
  assert.equal(summary?.figures[0]?.renderStatusLabel, "已渲染");
  assert.equal(
    summary?.figures[1]?.selectorSummary,
    "Plane slice at x/Lref=1.25 with normal (1.0, 0.0, 0.0)",
  );
  assert.deepEqual(summary?.figures[0]?.artifactPaths, [
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/surface-pressure.csv",
  ]);
});

void test(
  "appends delivery-only result cards when a report contains extra outputs",
  () => {
    const briefSummary = buildSubmarineDesignBriefSummary({
      requested_outputs: [
        {
          output_id: "drag_coefficient",
          label: "闃诲姏绯绘暟 Cd",
          requested_label: "闃诲姏绯绘暟 Cd",
          support_level: "supported",
        },
      ],
    });
    const acceptanceSummary = buildSubmarineAcceptanceSummary({
      acceptance_assessment: {
        status: "ready_for_review",
        confidence: "medium",
      },
      output_delivery_plan: [
        {
          output_id: "drag_coefficient",
          label: "闃诲姏绯绘暟 Cd",
          delivery_status: "delivered",
          detail: "Cd captured in solver metrics.",
        },
        {
          output_id: "benchmark_comparison",
          label: "Benchmark comparison",
          delivery_status: "delivered",
          detail: "Case benchmark checks exported.",
        },
      ],
    });

    const cards = buildSubmarineResultCards({
      requestedOutputs: briefSummary?.requestedOutputs,
      outputDelivery: acceptanceSummary?.outputDelivery,
      artifactPaths: [
        "/mnt/user-data/outputs/submarine/reports/demo/delivery-readiness.json",
      ],
    });

    assert.deepEqual(
      cards.map((card) => card.outputId),
      ["drag_coefficient", "benchmark_comparison"],
    );
    assert.equal(cards[1]?.previewArtifactPath, null);
    assert.deepEqual(cards[1]?.artifactPaths, [
      "/mnt/user-data/outputs/submarine/reports/demo/delivery-readiness.json",
    ]);
  },
);

void test("keeps scientific verification requirements in design brief summary", () => {
  const summary = buildSubmarineDesignBriefSummary({
    scientific_verification_requirements: [
      {
        requirement_id: "mesh_independence_study",
        label: "Mesh independence study",
        check_type: "artifact_presence",
        required_artifacts: ["verification-mesh-independence.json"],
      },
      {
        requirement_id: "force_coefficient_tail_stability",
        label: "Force coefficient tail stability",
        check_type: "force_coefficient_tail_stability",
        force_coefficient: "Cd",
        minimum_history_samples: 5,
        max_tail_relative_spread: 0.02,
      },
    ],
  });

  assert.equal(summary?.scientificVerificationRequirements.length, 2);
  assert.equal(
    summary?.scientificVerificationRequirements[0]?.requirementId,
    "mesh_independence_study",
  );
  assert.equal(
    summary?.scientificVerificationRequirements[1]?.detail,
    "力系数=Cd; 最小样本数=5; 尾段最大相对波动=0.0200",
  );
});

void test("builds a scientific verification summary from the final report payload", () => {
  const summary = buildSubmarineScientificVerificationSummary({
    scientific_verification_assessment: {
      status: "needs_more_verification",
      confidence: "medium",
      missing_evidence: [
        "Mesh independence study: missing evidence artifacts verification-mesh-independence.json.",
      ],
      blocking_issues: [],
      passed_requirements: [
        "Final residual threshold: observed 0.000500 <= 0.001000.",
      ],
      requirements: [
        {
          requirement_id: "final_residual_threshold",
          label: "Final residual threshold",
          status: "passed",
          detail: "Final residual threshold: observed 0.000500 <= 0.001000.",
        },
        {
          requirement_id: "mesh_independence_study",
          label: "Mesh independence study",
          status: "missing_evidence",
          detail: "Mesh independence study: missing evidence artifacts verification-mesh-independence.json.",
        },
      ],
    },
  });

  assert.equal(summary?.statusLabel, "仍需更多校验");
  assert.equal(summary?.confidenceLabel, "中");
  assert.equal(summary?.requirements.length, 2);
  assert.equal(summary?.requirements[1]?.status, "缺少证据");
  assert.equal(summary?.requirements[0]?.label, "最终残差阈值");
  assert.match(summary?.requirements[0]?.detail ?? "", /最终残差阈值/u);
  assert.equal(summary?.missingEvidence.length, 1);
  assert.equal(summary?.passedRequirements.length, 1);
  assert.match(summary?.missingEvidence[0] ?? "", /网格无关性研究/u);
  assert.match(summary?.passedRequirements[0] ?? "", /最终残差阈值/u);
});

void test("builds a stability evidence summary from the final report payload", () => {
  const summary = buildSubmarineStabilityEvidenceSummary({
    stability_evidence_virtual_path:
      "/mnt/user-data/outputs/submarine/solver-dispatch/demo/stability-evidence.json",
    stability_evidence: {
      status: "missing_evidence",
      summary_zh: "SCI-01 基线稳定性证据仍不完整。",
      source_solver_results_virtual_path:
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
      artifact_virtual_path:
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/stability-evidence.json",
      residual_summary: {
        max_final_residual: 0.0005,
      },
      force_coefficient_tail: {
        coefficient: "Cd",
        status: "missing_evidence",
        observed_sample_count: 2,
        required_sample_count: 5,
        relative_spread: null,
      },
      passed_requirements: [
        "Final residual threshold: observed 0.000500 <= 0.001000.",
      ],
      missing_evidence: [
        "Force coefficient tail stability: need at least 5 Cd samples in force coefficient history.",
      ],
      blocking_issues: [],
      requirements: [
        {
          requirement_id: "final_residual_threshold",
          label: "Final residual threshold",
          status: "passed",
          detail: "Final residual threshold: observed 0.000500 <= 0.001000.",
        },
        {
          requirement_id: "force_coefficient_tail_stability",
          label: "Force coefficient tail stability",
          status: "missing_evidence",
          detail:
            "Force coefficient tail stability: need at least 5 Cd samples in force coefficient history.",
        },
      ],
    },
  });

  assert.equal(summary?.statusLabel, "缺少证据");
  assert.equal(summary?.residualMaxFinalValue, "0.000500");
  assert.equal(summary?.tailCoefficientLabel, "Cd");
  assert.equal(summary?.tailStatusLabel, "缺少证据");
  assert.equal(summary?.tailSampleCountLabel, "2/5");
  assert.deepEqual(summary?.passedRequirements, [
    "最终残差阈值：观测值 0.000500 <= 0.001000.",
  ]);
  assert.equal(summary?.requirementLines.length, 2);
  assert.match(summary?.requirementLines[1] ?? "", /缺少证据/);
  assert.match(summary?.requirementLines[0] ?? "", /最终残差阈值/u);
});

void test("builds a scientific study summary from the final report payload", () => {
  const summary = buildSubmarineScientificStudySummary({
    scientific_study_summary: {
      study_execution_status: "planned",
      workflow_status: "planned",
      study_status_counts: {
        planned: 2,
      },
      manifest_virtual_path:
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/verification-mesh-independence.json",
      ],
      studies: [
        {
          study_type: "mesh_independence",
          summary_label: "Mesh Independence",
          monitored_quantity: "Cd",
          variant_count: 3,
          study_execution_status: "completed",
          workflow_status: "completed",
          workflow_detail:
            "All planned variants completed with compare coverage.",
          variant_status_counts: { completed: 3 },
          compare_status_counts: { completed: 2 },
          expected_variant_run_ids: [
            "mesh_independence:coarse",
            "mesh_independence:fine",
          ],
          completed_variant_run_ids: [
            "mesh_independence:coarse",
            "mesh_independence:fine",
          ],
          completed_compare_variant_run_ids: [
            "mesh_independence:coarse",
            "mesh_independence:fine",
          ],
          verification_status: "passed",
          verification_detail: "Three-grid study shows Cd variation below tolerance.",
        },
        {
          study_type: "domain_sensitivity",
          summary_label: "Domain Sensitivity",
          monitored_quantity: "Cd",
          variant_count: 3,
          study_execution_status: "planned",
          workflow_status: "partial",
          workflow_detail: "Baseline completed, planned variants still pending.",
          variant_status_counts: { planned: 2, completed: 1 },
          compare_status_counts: { planned: 2 },
          expected_variant_run_ids: [
            "domain_sensitivity:compact",
            "domain_sensitivity:expanded",
          ],
          planned_variant_run_ids: [
            "domain_sensitivity:compact",
            "domain_sensitivity:expanded",
          ],
          planned_compare_variant_run_ids: [
            "domain_sensitivity:compact",
            "domain_sensitivity:expanded",
          ],
          verification_status: "missing_evidence",
          verification_detail: "Only baseline run has been executed so far.",
        },
      ],
    },
  });

  assert.equal(summary?.executionStatusLabel, "已规划");
  assert.equal(summary?.workflowStatusLabel, "已规划");
  assert.deepEqual(summary?.studyStatusCountLines, ["已规划: 2"]);
  assert.equal(
    summary?.manifestPath,
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
  );
  assert.equal(summary?.artifactPaths.length, 2);
  assert.equal(summary?.studies.length, 2);
  assert.equal(summary?.studies[0]?.studyType, "mesh_independence");
  assert.equal(summary?.studies[0]?.studyExecutionStatusLabel, "已完成");
  assert.equal(summary?.studies[0]?.workflowStatusLabel, "已完成");
  assert.equal(
    summary?.studies[0]?.workflowDetail,
    "全部计划变体均已完成，并具备对比覆盖。",
  );
  assert.deepEqual(summary?.studies[0]?.variantStatusCountLines, ["已完成: 3"]);
  assert.deepEqual(summary?.studies[0]?.compareStatusCountLines, ["已完成: 2"]);
  assert.equal(summary?.studies[0]?.verificationStatus, "已通过");
  assert.deepEqual(summary?.studies[0]?.expectedVariantRunIds, [
    "mesh_independence:coarse",
    "mesh_independence:fine",
  ]);
  assert.equal(summary?.studies[1]?.verificationStatus, "缺少证据");
  assert.equal(summary?.studies[1]?.workflowStatusLabel, "部分完成");
  assert.deepEqual(summary?.studies[1]?.plannedVariantRunIds, [
    "domain_sensitivity:compact",
    "domain_sensitivity:expanded",
  ]);
});

void test("labels blocked scientific study execution explicitly", () => {
  const summary = buildSubmarineScientificStudySummary({
    scientific_study_summary: {
      study_execution_status: "blocked",
      manifest_virtual_path:
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
      artifact_virtual_paths: [],
      studies: [],
    },
  });

  assert.equal(summary?.executionStatusLabel, "已阻塞");
});

void test("builds an experiment summary from the final report payload", () => {
  const summary = buildSubmarineExperimentSummary({
    experiment_summary: {
      experiment_id:
        "darpa-suboff-bare-hull-resistance-study-compare-demo-resistance",
      experiment_status: "completed",
      workflow_status: "partial",
      workflow_detail:
        "Pending variant execution: domain_sensitivity:compact, domain_sensitivity:expanded",
      baseline_run_id: "baseline",
      run_count: 7,
      compare_count: 2,
      manifest_virtual_path:
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
      study_manifest_virtual_path:
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
      compare_virtual_path:
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
      ],
      linkage_status: "incomplete",
      linkage_issue_count: 2,
      linkage_issues: [
        "Planned scientific variant is missing from experiment run records: domain_sensitivity:expanded.",
      ],
      run_status_counts: {
        completed: 2,
        planned: 2,
      },
      compare_status_counts: {
        completed: 1,
        planned: 1,
      },
      expected_variant_run_ids: [
        "mesh_independence:coarse",
        "domain_sensitivity:expanded",
      ],
      registered_custom_variant_run_ids: ["custom:pressure-sweep"],
      missing_variant_run_record_ids: ["domain_sensitivity:expanded"],
      missing_compare_entry_ids: ["domain_sensitivity:expanded"],
      planned_custom_variant_run_ids: ["custom:pressure-sweep"],
      completed_custom_variant_run_ids: [],
      missing_custom_compare_entry_ids: ["custom:pressure-sweep"],
      planned_variant_run_ids: ["domain_sensitivity:expanded"],
      missing_metrics_variant_run_ids: ["mesh_independence:fine"],
      compare_notes: [
        "mesh_independence:coarse | completed",
        "domain_sensitivity:compact | completed",
      ],
    },
  });

  assert.equal(
    summary?.experimentId,
    "darpa-suboff-bare-hull-resistance-study-compare-demo-resistance",
  );
  assert.equal(summary?.experimentStatusLabel, "已完成");
  assert.equal(summary?.workflowStatusLabel, "部分完成");
  assert.equal(
    summary?.workflowDetail,
    "待执行变体：domain_sensitivity:compact, domain_sensitivity:expanded",
  );
  assert.equal(summary?.baselineRunId, "baseline");
  assert.equal(summary?.runCount, 7);
  assert.equal(summary?.compareCount, 2);
  assert.equal(
    summary?.manifestPath,
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
  );
  assert.equal(
    summary?.studyManifestPath,
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
  );
  assert.equal(
    summary?.comparePath,
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
  );
  assert.deepEqual(summary?.runStatusCountLines, ["已完成: 2", "已规划: 2"]);
  assert.deepEqual(summary?.compareStatusCountLines, ["已完成: 1", "已规划: 1"]);
  assert.equal(summary?.linkageStatus, "incomplete");
  assert.equal(summary?.linkageIssueCount, 2);
  assert.deepEqual(summary?.registeredCustomVariantRunIds, [
    "custom:pressure-sweep",
  ]);
  assert.deepEqual(summary?.plannedCustomVariantRunIds, [
    "custom:pressure-sweep",
  ]);
  assert.deepEqual(summary?.completedCustomVariantRunIds, []);
  assert.deepEqual(summary?.missingCustomCompareEntryIds, [
    "custom:pressure-sweep",
  ]);
  assert.deepEqual(summary?.plannedVariantRunIds, ["domain_sensitivity:expanded"]);
  assert.deepEqual(summary?.missingMetricsVariantRunIds, [
    "mesh_independence:fine",
  ]);
  assert.deepEqual(summary?.compareNotes, [
    "mesh_independence:coarse | completed",
    "domain_sensitivity:compact | completed",
  ]);
});

void test("builds an experiment compare summary from the final report payload", () => {
  const summary = buildSubmarineExperimentCompareSummary({
    experiment_compare_summary: {
      experiment_id:
        "darpa-suboff-bare-hull-resistance-study-compare-demo-resistance",
      baseline_run_id: "baseline",
      compare_count: 1,
      workflow_status: "partial",
      compare_status_counts: {
        completed: 1,
        planned: 1,
      },
      planned_candidate_run_ids: ["domain_sensitivity:expanded"],
      completed_candidate_run_ids: ["mesh_independence:coarse"],
      compare_virtual_path:
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
      ],
      comparisons: [
        {
          candidate_run_id: "mesh_independence:coarse",
          study_type: "mesh_independence",
          variant_id: "coarse",
          compare_status: "completed",
          candidate_execution_status: "completed",
          notes: "Relative Cd shift stayed within tolerance.",
          metric_deltas: {
            Cd: {
              baseline_value: 0.12,
              candidate_value: 0.1212,
              absolute_delta: 0.0012,
              relative_delta: 0.01,
            },
            mesh_cells: {
              baseline_value: 1200000,
              candidate_value: 840000,
              absolute_delta: -360000,
              relative_delta: -0.3,
            },
          },
          baseline_solver_results_virtual_path:
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
          candidate_solver_results_virtual_path:
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/studies/mesh-independence/coarse/solver-results.json",
          baseline_run_record_virtual_path:
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-record.json",
          candidate_run_record_virtual_path:
            "/mnt/user-data/outputs/submarine/solver-dispatch/demo/studies/mesh-independence/coarse/run-record.json",
        },
      ],
    },
  });

  assert.equal(summary?.compareCount, 1);
  assert.equal(summary?.baselineRunId, "baseline");
  assert.equal(summary?.workflowStatusLabel, "部分完成");
  assert.deepEqual(summary?.compareStatusCountLines, ["已完成: 1", "已规划: 1"]);
  assert.deepEqual(summary?.plannedCandidateRunIds, [
    "domain_sensitivity:expanded",
  ]);
  assert.deepEqual(summary?.completedCandidateRunIds, [
    "mesh_independence:coarse",
  ]);
  assert.equal(summary?.comparePath, "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json");
  assert.deepEqual(summary?.artifactPaths, [
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
  ]);
  assert.equal(summary?.comparisons.length, 1);
  assert.equal(summary?.comparisons[0]?.candidateRunId, "mesh_independence:coarse");
  assert.equal(summary?.comparisons[0]?.compareStatus, "completed");
  assert.equal(summary?.comparisons[0]?.compareStatusLabel, "已完成");
  assert.equal(summary?.comparisons[0]?.candidateExecutionStatusLabel, "已完成");
  assert.equal(summary?.comparisons[0]?.studyLabel, "mesh_independence / coarse");
  assert.deepEqual(summary?.comparisons[0]?.metricDeltaLines, [
    "Cd: 基线=0.12 | 候选=0.1212 | 差值=0.0012 | 相对变化=1.00%",
    "mesh_cells: 基线=1200000 | 候选=840000 | 差值=-360000 | 相对变化=-30.00%",
  ]);
  assert.deepEqual(summary?.comparisons[0]?.artifactPaths, [
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/studies/mesh-independence/coarse/solver-results.json",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-record.json",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/studies/mesh-independence/coarse/run-record.json",
  ]);
});

void test("formats custom variant compare summaries with custom lineage labels", () => {
  const summary = buildSubmarineExperimentCompareSummary({
    experiment_compare_summary: {
      experiment_id: "darpa-suboff-custom-variant-demo",
      baseline_run_id: "baseline",
      compare_count: 1,
      workflow_status: "partial",
      compare_status_counts: {
        completed: 0,
        planned: 1,
      },
      planned_candidate_run_ids: ["custom:pressure-sweep"],
      completed_candidate_run_ids: [],
      comparisons: [
        {
          candidate_run_id: "custom:pressure-sweep",
          run_role: "custom_variant",
          variant_origin: "custom_variant",
          variant_id: "pressure-sweep",
          variant_label: "Pressure Sweep",
          baseline_reference_run_id: "baseline",
          compare_target_run_id: "baseline",
          compare_status: "planned",
          candidate_execution_status: "planned",
          notes: "User-authored pressure sweep variant is queued for execution.",
        },
      ],
    },
  });

  assert.equal(summary?.comparisons.length, 1);
  assert.equal(summary?.comparisons[0]?.candidateRunId, "custom:pressure-sweep");
  assert.equal(summary?.comparisons[0]?.runRole, "custom_variant");
  assert.equal(summary?.comparisons[0]?.variantOrigin, "custom_variant");
  assert.equal(summary?.comparisons[0]?.variantLabel, "Pressure Sweep");
  assert.equal(summary?.comparisons[0]?.studyLabel, "自定义 / pressure-sweep");
  assert.equal(
    summary?.comparisons[0]?.lineageLabel,
    "自定义变体 | Pressure Sweep",
  );
  assert.equal(summary?.comparisons[0]?.baselineReferenceRunId, "baseline");
  assert.equal(summary?.comparisons[0]?.compareTargetRunId, "baseline");
  assert.equal(summary?.comparisons[0]?.isCustomVariant, true);
});

void test("builds a research evidence summary from the final report payload", () => {
  const summary = buildSubmarineResearchEvidenceSummary({
    research_evidence_summary: {
      readiness_status: "verified_but_not_validated",
      verification_status: "passed",
      validation_status: "missing_validation_reference",
      provenance_status: "traceable",
      confidence: "medium",
      blocking_issues: [
        "Benchmark cd_at_3_05_mps is not applicable to the current run condition.",
      ],
      evidence_gaps: [
        "No applicable benchmark target was available for this run.",
      ],
      passed_evidence: ["Scientific verification requirements passed."],
      benchmark_highlights: [],
      provenance_highlights: [
        "Experiment manifest and compare summary are available.",
      ],
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/reports/demo/research-evidence-summary.json",
      ],
    },
  });

  assert.equal(summary?.readinessStatus, "verified_but_not_validated");
  assert.equal(summary?.validationStatus, "missing_validation_reference");
  assert.equal(summary?.readinessLabel, "已验证但未外部校核");
  assert.equal(summary?.verificationStatusLabel, "已通过");
  assert.equal(summary?.validationStatusLabel, "缺少校核参考");
  assert.equal(summary?.provenanceStatusLabel, "可追溯");
  assert.equal(summary?.confidenceLabel, "中");
  assert.deepEqual(summary?.blockingIssues, [
    "Benchmark cd_at_3_05_mps is not applicable to the current run condition.",
  ]);
  assert.deepEqual(summary?.evidenceGaps, [
    "No applicable benchmark target was available for this run.",
  ]);
  assert.deepEqual(summary?.passedEvidence, [
    "Scientific verification requirements passed.",
  ]);
  assert.deepEqual(summary?.provenanceHighlights, [
    "Experiment manifest and compare summary are available.",
  ]);
  assert.deepEqual(summary?.artifactPaths, [
    "/mnt/user-data/outputs/submarine/reports/demo/research-evidence-summary.json",
  ]);
});

void test("builds a scientific supervisor gate summary from the final report payload", () => {
  const summary = buildSubmarineScientificGateSummary({
    scientific_supervisor_gate: {
      gate_status: "claim_limited",
      allowed_claim_level: "verified_but_not_validated",
      source_readiness_status: "verified_but_not_validated",
      recommended_stage: "supervisor-review",
      remediation_stage: "solver-dispatch",
      blocking_reasons: [],
      advisory_notes: ["External validation evidence is still missing for this run."],
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/reports/demo/supervisor-scientific-gate.json",
      ],
    },
  });

  assert.equal(summary?.gateStatus, "claim_limited");
  assert.equal(summary?.allowedClaimLevel, "verified_but_not_validated");
  assert.equal(summary?.gateStatusLabel, "结论受限");
  assert.equal(
    summary?.allowedClaimLevelLabel,
    "已验证但未外部校核",
  );
  assert.equal(
    summary?.sourceReadinessLabel,
    "已验证但未外部校核",
  );
  assert.equal(summary?.recommendedStageLabel, "主管复核");
  assert.equal(summary?.remediationStageLabel, "求解派发");
  assert.deepEqual(summary?.advisoryNotes, [
    "External validation evidence is still missing for this run.",
  ]);
  assert.deepEqual(summary?.artifactPaths, [
    "/mnt/user-data/outputs/submarine/reports/demo/supervisor-scientific-gate.json",
  ]);
});

void test("builds a scientific remediation summary from the final report payload", () => {
  const summary = buildSubmarineScientificRemediationSummary({
    scientific_remediation_summary: {
      plan_status: "recommended",
      current_claim_level: "verified_but_not_validated",
      target_claim_level: "research_ready",
      recommended_stage: "supervisor-review",
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-plan.json",
      ],
      actions: [
        {
          action_id: "attach-validation-reference",
          title: "Attach validation reference",
          summary:
            "Provide a benchmark target for the selected case so the current run can be externally validated.",
          owner_stage: "supervisor-review",
          priority: "high",
          execution_mode: "manual_required",
          status: "pending",
          evidence_gap: "No applicable benchmark target was available for this run.",
          required_artifacts: [
            "/mnt/user-data/outputs/submarine/reports/demo/supervisor-scientific-gate.json",
          ],
        },
      ],
    },
  });

  assert.equal(summary?.planStatusLabel, "建议执行");
  assert.equal(summary?.currentClaimLevelLabel, "已验证但未外部校核");
  assert.equal(summary?.targetClaimLevelLabel, "可用于科研结论");
  assert.equal(summary?.recommendedStageLabel, "主管复核");
  assert.deepEqual(summary?.artifactPaths, [
    "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-plan.json",
  ]);
  assert.equal(summary?.actions.length, 1);
  assert.equal(summary?.actions[0]?.actionId, "attach-validation-reference");
  assert.equal(summary?.actions[0]?.ownerStageLabel, "主管复核");
  assert.equal(summary?.actions[0]?.executionModeLabel, "需要人工处理");
  assert.equal(summary?.actions[0]?.statusLabel, "待处理");
  assert.deepEqual(summary?.actions[0]?.requiredArtifacts, [
    "/mnt/user-data/outputs/submarine/reports/demo/supervisor-scientific-gate.json",
  ]);
});

void test(
  "builds a scientific remediation handoff summary from the final report payload",
  () => {
    const summary = buildSubmarineScientificRemediationHandoffSummary({
      scientific_remediation_handoff: {
        handoff_status: "ready_for_auto_followup",
        recommended_action_id: "execute-scientific-studies",
        tool_name: "submarine_solver_dispatch",
        tool_args: {
          geometry_path: "/mnt/user-data/uploads/suboff_solid.stl",
          selected_case_id: "darpa_suboff_axisymmetric",
          execute_scientific_studies: true,
        },
        reason:
          "Scientific verification evidence is incomplete for this run and the next solver rerun can be prepared automatically.",
        artifact_virtual_paths: [
          "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json",
        ],
        manual_actions: [
          {
            action_id: "attach-validation-reference",
            title: "Attach validation reference",
            owner_stage: "supervisor-review",
            evidence_gap:
              "No applicable benchmark target was available for this run.",
          },
        ],
      },
    });

    assert.equal(summary?.handoffStatusLabel, "可自动跟进");
    assert.equal(summary?.recommendedActionId, "execute-scientific-studies");
    assert.equal(summary?.toolName, "submarine_solver_dispatch");
    assert.equal(summary?.toolArgs.length, 3);
    assert.deepEqual(summary?.toolArgs[0], {
      key: "geometry_path",
      value: "/mnt/user-data/uploads/suboff_solid.stl",
    });
    assert.deepEqual(summary?.toolArgs[2], {
      key: "execute_scientific_studies",
      value: "true",
    });
    assert.equal(
      summary?.manualActions[0]?.ownerStageLabel,
      "主管复核",
    );
    assert.deepEqual(summary?.artifactPaths, [
      "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json",
    ]);
  },
);

void test(
  "builds a chat-driven delivery decision summary from the final report payload",
  () => {
    const summary = buildSubmarineDeliveryDecisionSummary({
      decision_status: "needs_more_evidence",
      delivery_decision_summary: {
        decision_status: "needs_more_evidence",
        decision_question_zh: "当前结论可以交付，但仍有证据缺口。请在聊天中确认下一步。",
        recommended_option_id: "add_evidence",
        options: [
          {
            option_id: "add_evidence",
            label_zh: "补充证据",
            summary_zh: "优先补齐缺失证据，再决定是否提升 claim level。",
            followup_kind: "evidence_supplement",
            requires_additional_execution: true,
          },
          {
            option_id: "finish_task",
            label_zh: "完成任务",
            summary_zh: "接受当前结论作为本次任务终点，并在聊天中确认收口。",
            followup_kind: "task_complete",
            requires_additional_execution: false,
          },
        ],
        blocking_reason_lines: ["No applicable benchmark target was available."],
        advisory_note_lines: ["The current conclusion can still support delivery copy."],
        artifact_virtual_paths: [
          "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-plan.json",
        ],
      },
    });

    assert.equal(summary?.decisionStatus, "needs_more_evidence");
    assert.equal(summary?.decisionStatusLabel, "需要更多证据");
    assert.equal(
      summary?.question,
      "当前结论可以交付，但仍有证据缺口。请在聊天中确认下一步。",
    );
    assert.equal(summary?.chatPrompt, "请在聊天中确认下一步。");
    assert.equal(summary?.recommendedOptionId, "add_evidence");
    assert.equal(summary?.recommendedOptionLabel, "补充证据");
    assert.equal(summary?.options.length, 2);
    assert.deepEqual(summary?.options[0], {
      optionId: "add_evidence",
      label: "补充证据",
      summary: "优先补齐缺失证据，再决定是否提升 claim level。",
      followupKind: "evidence_supplement",
      followupKindLabel: "补充证据",
      requiresAdditionalExecution: true,
    });
    assert.deepEqual(summary?.options[1], {
      optionId: "finish_task",
      label: "完成任务",
      summary: "接受当前结论作为本次任务终点，并在聊天中确认收口。",
      followupKind: "task_complete",
      followupKindLabel: "任务完成",
      requiresAdditionalExecution: false,
    });
    assert.deepEqual(summary?.blockingReasons, [
      "No applicable benchmark target was available.",
    ]);
    assert.deepEqual(summary?.advisoryNotes, [
      "The current conclusion can still support delivery copy.",
    ]);
    assert.deepEqual(summary?.artifactPaths, [
      "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-plan.json",
    ]);
  },
);

void test(
  "builds a scientific followup summary from the final report payload",
  () => {
    const payload: SubmarineFinalReportPayload = {
      scientific_followup_summary: {
        history_virtual_path:
          "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json",
        entry_count: 2,
        latest_outcome_status: "dispatch_refreshed_report",
        latest_handoff_status: "ready_for_auto_followup",
        latest_recommended_action_id: "execute-scientific-studies",
        latest_tool_name: "submarine_solver_dispatch",
        latest_followup_kind: "evidence_supplement",
        latest_decision_summary_zh: "补齐外部验证证据后刷新报告。",
        latest_source_conclusion_ids: ["current_conclusion"],
        latest_source_evidence_gap_ids: ["missing_validation_reference"],
        latest_dispatch_stage_status: "executed",
        report_refreshed: true,
        latest_result_report_virtual_path:
          "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
        latest_result_provenance_manifest_virtual_path:
          "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest.json",
        latest_result_supervisor_handoff_virtual_path:
          "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json",
        latest_notes: [
          "The scientific rerun completed and the report was refreshed.",
        ],
        artifact_virtual_paths: [
          "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json",
          "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
        ],
      },
    };
    const summary = buildSubmarineScientificFollowupSummary(payload);

    assert.equal(summary?.entryCount, 2);
    assert.equal(summary?.latestOutcomeLabel, "派发后已刷新报告");
    assert.equal(summary?.latestHandoffStatusLabel, "可自动跟进");
    assert.equal(summary?.latestRecommendedActionId, "execute-scientific-studies");
    assert.equal(summary?.latestToolName, "submarine_solver_dispatch");
    assert.equal(summary?.latestFollowupKind, "evidence_supplement");
    assert.equal(summary?.latestFollowupKindLabel, "补充证据");
    assert.equal(summary?.latestDecisionSummary, "补齐外部验证证据后刷新报告。");
    assert.deepEqual(summary?.latestSourceConclusionIds, ["current_conclusion"]);
    assert.deepEqual(summary?.latestSourceEvidenceGapIds, [
      "missing_validation_reference",
    ]);
    assert.equal(summary?.latestDispatchStageStatusLabel, "已执行");
    assert.equal(summary?.reportRefreshedLabel, "是");
    assert.equal(
      summary?.historyPath,
      "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json",
    );
    assert.equal(
      summary?.latestResultReportPath,
      "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
    );
    assert.equal(
      summary?.latestResultProvenanceManifestPath,
      "/mnt/user-data/outputs/submarine/solver-dispatch/demo/provenance-manifest.json",
    );
    assert.equal(
      summary?.latestResultHandoffPath,
      "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json",
    );
    assert.deepEqual(summary?.latestNotes, [
      "The scientific rerun completed and the report was refreshed.",
    ]);
    assert.deepEqual(summary?.artifactPaths, [
      "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json",
      "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
    ]);
  },
);

void test(
  "maps scientific runtime roles and stages to readable workbench labels",
  () => {
    const outline = buildSubmarineExecutionOutline({
      runtimePlan: [
        {
          role_id: "scientific-study",
          owner: "DeerFlow scientific-study",
          goal: "Plan scientific study variants",
          status: "ready",
          target_skills: ["submarine-solver-dispatch"],
        },
        {
          role_id: "scientific-followup",
          owner: "DeerFlow scientific-followup",
          goal: "Track scientific remediation follow-up",
          status: "pending",
        },
      ],
    });
    const gateSummary = buildSubmarineScientificGateSummary({
      scientific_supervisor_gate: {
        gate_status: "claim_limited",
        allowed_claim_level: "validated_with_gaps",
        source_readiness_status: "validated_with_gaps",
        recommended_stage: "scientific-verification",
        remediation_stage: "scientific-followup",
        artifact_virtual_paths: [],
      },
    });
    const remediationSummary = buildSubmarineScientificRemediationSummary({
      scientific_remediation_summary: {
        plan_status: "recommended",
        current_claim_level: "validated_with_gaps",
        target_claim_level: "research_ready",
        recommended_stage: "scientific-followup",
        artifact_virtual_paths: [],
        actions: [
          {
            action_id: "refresh-followup-history",
            title: "Refresh scientific follow-up history",
            summary:
              "Record the latest rerun decision and refreshed report outputs.",
            owner_stage: "scientific-followup",
            priority: "medium",
            execution_mode: "auto_executable",
            status: "pending",
          },
        ],
      },
    });
    const handoffSummary = buildSubmarineScientificRemediationHandoffSummary({
      scientific_remediation_handoff: {
        handoff_status: "manual_followup_required",
        recommended_action_id: "review-scientific-verification",
        tool_name: null,
        reason: "Scientific verification still needs manual review.",
        artifact_virtual_paths: [],
        manual_actions: [
          {
            action_id: "review-scientific-verification",
            title: "Review scientific verification evidence",
            owner_stage: "scientific-verification",
            evidence_gap:
              "A reviewer needs to inspect the latest comparison summary.",
          },
        ],
      },
    });

    assert.equal(
      formatSubmarineRuntimeStageLabel("scientific-study"),
      "科研研究",
    );
    assert.equal(
      formatSubmarineExecutionRoleLabel("experiment-compare"),
      "实验对比",
    );
    assert.equal(outline[0]?.roleLabel, "科研研究");
    assert.equal(outline[1]?.roleLabel, "科研跟进");
    assert.equal(gateSummary?.recommendedStageLabel, "科研校验");
    assert.equal(gateSummary?.remediationStageLabel, "科研跟进");
    assert.equal(remediationSummary?.recommendedStageLabel, "科研跟进");
    assert.equal(
      remediationSummary?.actions[0]?.ownerStageLabel,
      "科研跟进",
    );
    assert.equal(
      handoffSummary?.manualActions[0]?.ownerStageLabel,
      "科研校验",
    );
  },
);
