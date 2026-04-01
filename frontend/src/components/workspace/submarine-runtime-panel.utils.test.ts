import assert from "node:assert/strict";
import test from "node:test";

import type { SubmarineFinalReportPayload } from "./submarine-runtime-panel.contract";

const {
  buildSubmarineAcceptanceSummary,
  buildSubmarineDesignBriefSummary,
  buildSubmarineStageTrack,
  buildSubmarineExperimentCompareSummary,
  buildSubmarineExperimentSummary,
  buildSubmarineFigureDeliverySummary,
  buildSubmarineOutputDeliverySummary,
  buildSubmarineResearchEvidenceSummary,
  buildSubmarineExecutionOutline,
  buildSubmarineResultCards,
  formatSubmarineExecutionRoleLabel,
  formatSubmarineRuntimeStageLabel,
  buildSubmarineScientificGateSummary,
  buildSubmarineScientificFollowupSummary,
  buildSubmarineScientificRemediationHandoffSummary,
  buildSubmarineScientificRemediationSummary,
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
  assert.equal(summary?.executionOutline.length, 2);
  assert.equal(summary?.executionOutline[0]?.status, "in_progress");
  assert.deepEqual(summary?.executionOutline[0]?.targetSkills, [
    "submarine-design-brief",
  ]);
  assert.equal(summary?.requestedOutputs.length, 2);
  assert.equal(summary?.requestedOutputs[0]?.outputId, "drag_coefficient");
  assert.equal(summary?.requestedOutputs[1]?.supportLevel, "not_yet_supported");
  assert.equal(summary?.requestedOutputs[0]?.specSummary, "--");
  assert.equal(
    summary?.requestedOutputs[1]?.specSummary,
    "field=U; selector=plane[x/Lref=1.25; normal=(1, 0, 0)]; time=latest; formats=csv,png,report",
  );
  assert.equal(summary?.requirementPairs[0]?.label, "来流速度");
  assert.equal(summary?.requirementPairs[0]?.value, "7.50 m/s");
  assert.equal(summary?.requirementPairs.at(-1)?.value, "20");
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
  assert.equal(outline[1]?.status, "in_progress");
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
    assert.equal(track[4]?.label, "Scientific Study");
    assert.equal(track[6]?.label, "Scientific Verification");
    assert.equal(track[6]?.status, "ready");
    assert.equal(track[8]?.label, "Scientific Follow-Up");
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

void test("returns delivery-readiness labels for acceptance artifacts", () => {
  const meta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/reports/demo/delivery-readiness.json",
  );

  assert.equal(meta.label, "浜や粯灏辩华 JSON");
  assert.equal(meta.externalLinkLabel, "鍦ㄦ柊绐楀彛鎵撳紑浜や粯灏辩华 JSON");
});

void test("returns stable labels for scientific verification artifacts", () => {
  const meta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/verification-mesh-independence.json",
  );
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/verification-mesh-independence.json",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/verification-domain-sensitivity.json",
  ]);

  assert.equal(meta.label, "Scientific Verification - Mesh Independence JSON");
  assert.equal(groups[0]?.id, "results");
});

void test("returns stable labels for scientific supervisor gate artifacts", () => {
  const meta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/reports/demo/supervisor-scientific-gate.json",
  );
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/reports/demo/supervisor-scientific-gate.json",
  ]);

  assert.equal(meta.label, "Scientific Supervisor Gate JSON");
  assert.equal(
    meta.externalLinkLabel,
    "Open scientific supervisor gate JSON in a new window",
  );
  assert.equal(groups[0]?.id, "report");
});

void test("returns stable labels for scientific remediation handoff artifacts", () => {
  const meta = getSubmarineArtifactMeta(
    "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json",
  );
  const groups = groupSubmarineArtifacts([
    "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-plan.json",
    "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json",
  ]);

  assert.equal(meta.label, "Scientific Remediation Handoff JSON");
  assert.equal(
    meta.externalLinkLabel,
    "Open scientific remediation handoff JSON in a new window",
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

  assert.equal(meta.label, "Scientific Follow-Up History JSON");
  assert.equal(
    meta.externalLinkLabel,
    "Open scientific follow-up history JSON in a new window",
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

  assert.equal(summary?.statusLabel, "寰呭鏍?");
  assert.equal(summary?.confidenceLabel, "涓?");
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
  assert.equal(summary[0]?.deliveryStatus, "delivered");
  assert.equal(
    summary[0]?.specSummary,
    "field=p; selector=patch[hull]; time=latest; formats=csv,png,report",
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
          observed_value: 0.0031,
          reference_value: 0.00314,
          relative_error: 0.0127,
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
  assert.equal(summary?.benchmarkComparisons[0]?.quantity, "Cd");
  assert.equal(summary?.outputDelivery.length, 2);
  assert.equal(summary?.outputDelivery[0]?.outputId, "drag_coefficient");
  assert.equal(summary?.outputDelivery[1]?.deliveryStatus, "not_yet_supported");
  assert.equal(
    summary?.outputDelivery[1]?.specSummary,
    "field=p; selector=patch[hull]; time=latest; formats=csv,png,report",
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
    assert.equal(cards[0]?.deliveryStatus, "delivered");
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
      "field=p; selector=patch[hull]; time=latest; formats=csv,png,report",
    );
    assert.equal(
      cards[0]?.figureCaption,
      "Surface pressure contour over the selected hull patches, colored by p.",
    );
    assert.equal(cards[0]?.selectorSummary, "Patch selection: hull");
    assert.equal(cards[0]?.figureRenderStatus, "Rendered");
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
  assert.equal(summary?.figures[0]?.renderStatusLabel, "Rendered");
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
    "force_coefficient=Cd; min_samples=5; max_tail_relative_spread=0.0200",
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

  assert.equal(summary?.statusLabel, "Needs More Verification");
  assert.equal(summary?.confidenceLabel, "Medium");
  assert.equal(summary?.requirements.length, 2);
  assert.equal(summary?.requirements[1]?.status, "Missing Evidence");
  assert.equal(summary?.missingEvidence.length, 1);
  assert.equal(summary?.passedRequirements.length, 1);
});

void test("builds a scientific study summary from the final report payload", () => {
  const summary = buildSubmarineScientificStudySummary({
    scientific_study_summary: {
      study_execution_status: "planned",
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
          verification_status: "passed",
          verification_detail: "Three-grid study shows Cd variation below tolerance.",
        },
        {
          study_type: "domain_sensitivity",
          summary_label: "Domain Sensitivity",
          monitored_quantity: "Cd",
          variant_count: 3,
          verification_status: "missing_evidence",
          verification_detail: "Only baseline run has been executed so far.",
        },
      ],
    },
  });

  assert.equal(summary?.executionStatusLabel, "Planned");
  assert.equal(
    summary?.manifestPath,
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/study-manifest.json",
  );
  assert.equal(summary?.artifactPaths.length, 2);
  assert.equal(summary?.studies.length, 2);
  assert.equal(summary?.studies[0]?.studyType, "mesh_independence");
  assert.equal(summary?.studies[0]?.verificationStatus, "Passed");
  assert.equal(summary?.studies[1]?.verificationStatus, "Missing Evidence");
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

  assert.equal(summary?.executionStatusLabel, "Blocked");
});

void test("builds an experiment summary from the final report payload", () => {
  const summary = buildSubmarineExperimentSummary({
    experiment_summary: {
      experiment_id:
        "darpa-suboff-bare-hull-resistance-study-compare-demo-resistance",
      experiment_status: "completed",
      baseline_run_id: "baseline",
      run_count: 7,
      manifest_virtual_path:
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
      compare_virtual_path:
        "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
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
  assert.equal(summary?.experimentStatusLabel, "Completed");
  assert.equal(summary?.baselineRunId, "baseline");
  assert.equal(summary?.runCount, 7);
  assert.equal(
    summary?.manifestPath,
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
  );
  assert.equal(
    summary?.comparePath,
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
  );
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
  assert.equal(summary?.comparePath, "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json");
  assert.deepEqual(summary?.artifactPaths, [
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/experiment-manifest.json",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-compare-summary.json",
  ]);
  assert.equal(summary?.comparisons.length, 1);
  assert.equal(summary?.comparisons[0]?.candidateRunId, "mesh_independence:coarse");
  assert.equal(summary?.comparisons[0]?.compareStatus, "completed");
  assert.equal(summary?.comparisons[0]?.compareStatusLabel, "Completed");
  assert.equal(summary?.comparisons[0]?.studyLabel, "mesh_independence / coarse");
  assert.deepEqual(summary?.comparisons[0]?.metricDeltaLines, [
    "Cd: baseline=0.12 | candidate=0.1212 | delta=0.0012 | relative=1.00%",
    "mesh_cells: baseline=1200000 | candidate=840000 | delta=-360000 | relative=-30.00%",
  ]);
  assert.deepEqual(summary?.comparisons[0]?.artifactPaths, [
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/solver-results.json",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/studies/mesh-independence/coarse/solver-results.json",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/run-record.json",
    "/mnt/user-data/outputs/submarine/solver-dispatch/demo/studies/mesh-independence/coarse/run-record.json",
  ]);
});

void test("builds a research evidence summary from the final report payload", () => {
  const summary = buildSubmarineResearchEvidenceSummary({
    research_evidence_summary: {
      readiness_status: "verified_but_not_validated",
      verification_status: "passed",
      validation_status: "missing_validation_reference",
      provenance_status: "traceable",
      confidence: "medium",
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

  assert.equal(summary?.readinessLabel, "Verified But Not Validated");
  assert.equal(summary?.verificationStatusLabel, "Passed");
  assert.equal(summary?.validationStatusLabel, "Missing Validation Reference");
  assert.equal(summary?.provenanceStatusLabel, "Traceable");
  assert.equal(summary?.confidenceLabel, "Medium");
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

  assert.equal(summary?.gateStatusLabel, "Claim Limited");
  assert.equal(
    summary?.allowedClaimLevelLabel,
    "Verified But Not Validated",
  );
  assert.equal(
    summary?.sourceReadinessLabel,
    "Verified But Not Validated",
  );
  assert.equal(summary?.recommendedStageLabel, "Supervisor Review");
  assert.equal(summary?.remediationStageLabel, "Solver Dispatch");
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

  assert.equal(summary?.planStatusLabel, "Recommended");
  assert.equal(summary?.currentClaimLevelLabel, "Verified But Not Validated");
  assert.equal(summary?.targetClaimLevelLabel, "Research Ready");
  assert.equal(summary?.recommendedStageLabel, "Supervisor Review");
  assert.deepEqual(summary?.artifactPaths, [
    "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-plan.json",
  ]);
  assert.equal(summary?.actions.length, 1);
  assert.equal(summary?.actions[0]?.actionId, "attach-validation-reference");
  assert.equal(summary?.actions[0]?.ownerStageLabel, "Supervisor Review");
  assert.equal(summary?.actions[0]?.executionModeLabel, "Manual Required");
  assert.equal(summary?.actions[0]?.statusLabel, "Pending");
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

    assert.equal(summary?.handoffStatusLabel, "Ready For Auto Follow-Up");
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
      "Supervisor Review",
    );
    assert.deepEqual(summary?.artifactPaths, [
      "/mnt/user-data/outputs/submarine/reports/demo/scientific-remediation-handoff.json",
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
        latest_dispatch_stage_status: "executed",
        report_refreshed: true,
        latest_result_report_virtual_path:
          "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
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
    assert.equal(summary?.latestOutcomeLabel, "Dispatch Refreshed Report");
    assert.equal(summary?.latestHandoffStatusLabel, "Ready For Auto Follow-Up");
    assert.equal(summary?.latestRecommendedActionId, "execute-scientific-studies");
    assert.equal(summary?.latestToolName, "submarine_solver_dispatch");
    assert.equal(summary?.latestDispatchStageStatusLabel, "Executed");
    assert.equal(summary?.reportRefreshedLabel, "Yes");
    assert.equal(
      summary?.historyPath,
      "/mnt/user-data/outputs/submarine/reports/demo/scientific-followup-history.json",
    );
    assert.equal(
      summary?.latestResultReportPath,
      "/mnt/user-data/outputs/submarine/reports/demo/final-report.md",
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
      "Scientific Study",
    );
    assert.equal(
      formatSubmarineExecutionRoleLabel("experiment-compare"),
      "Experiment Compare",
    );
    assert.equal(outline[0]?.roleLabel, "Scientific Study");
    assert.equal(outline[1]?.roleLabel, "Scientific Follow-Up");
    assert.equal(gateSummary?.recommendedStageLabel, "Scientific Verification");
    assert.equal(gateSummary?.remediationStageLabel, "Scientific Follow-Up");
    assert.equal(remediationSummary?.recommendedStageLabel, "Scientific Follow-Up");
    assert.equal(
      remediationSummary?.actions[0]?.ownerStageLabel,
      "Scientific Follow-Up",
    );
    assert.equal(
      handoffSummary?.manualActions[0]?.ownerStageLabel,
      "Scientific Verification",
    );
  },
);
