import assert from "node:assert/strict";
import test from "node:test";

const { buildSubmarineSessionModel } = await import(
  new URL("./submarine-session-model.ts", import.meta.url).href,
);

function buildModel(
  overrides: Partial<
    Parameters<typeof buildSubmarineSessionModel>[0]
  > = {},
) {
  return buildSubmarineSessionModel({
    isNewThread: false,
    runtime: null,
    designBrief: null,
    finalReport: null,
    messageCount: 0,
    artifactCount: 0,
    isLoading: false,
    errorMessage: null,
    latestAssistantPreview: null,
    latestUserPreview: null,
    latestUploadedFiles: [],
    viewedSliceId: null,
    ...overrides,
  });
}

void test("builds a single current research slice for a new thread instead of a fixed workflow table", () => {
  const model = buildModel({
    isNewThread: true,
  });

  assert.deepEqual(
    model.slices.map((slice: { id: string }) => slice.id),
    ["task-establishment"],
  );
  assert.equal(model.activeSliceId, "task-establishment");
  assert.equal(model.currentSlice.id, "task-establishment");
  assert.equal(model.viewedSlice.id, "task-establishment");
  assert.equal(model.historyInspection.isViewingHistory, false);
});

void test("adds a geometry-preflight slice when the session binds a concrete geometry and working objective", () => {
  const model = buildModel({
    runtime: {
      task_summary: "Inspect the uploaded SUBOFF hull and prepare the next CFD move.",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      requested_outputs: [{ label: "几何预检摘要" }],
    },
    designBrief: {
      summary_zh: "围绕 SUBOFF STL 形成预检与工况准备简报",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      requested_outputs: [{ label: "几何预检摘要" }],
      open_questions: ["是否按自由航行外流场处理？"],
    },
    messageCount: 4,
    artifactCount: 1,
  });

  assert.deepEqual(
    model.slices.map((slice: { id: string }) => slice.id),
    ["task-establishment", "geometry-preflight"],
  );
  assert.equal(model.activeSliceId, "geometry-preflight");
  assert.equal(model.currentSlice.id, "geometry-preflight");
  assert.match(model.currentSlice.title, /几何|预检/);
  assert.match(model.currentSlice.keyEvidenceSummary, /(SUBOFF|stl|几何|预检)/i);
});

void test("promotes an uploaded STL into geometry preflight before structured runtime arrives", () => {
  const prompt =
    "请先对这个 SUBOFF STL 做几何预检，判断它是否适合在外流场条件下开展首次 CFD 计算。";
  const model = buildModel({
    latestUserPreview: prompt,
    latestUploadedFiles: [
      {
        filename: "suboff_solid.stl",
        path: "/mnt/user-data/uploads/suboff_solid.stl",
      },
    ],
    messageCount: 2,
    isLoading: true,
  });

  assert.deepEqual(
    model.slices.map((slice: { id: string }) => slice.id),
    ["task-establishment", "geometry-preflight"],
  );
  assert.equal(model.activeSliceId, "geometry-preflight");
  assert.match(model.summary.currentObjective, /SUBOFF STL|几何预检/i);
  assert.match(model.currentSlice.keyEvidenceSummary, /suboff_solid\.stl/i);
});

void test("promotes execution into a semantic simulation slice instead of a fixed execution module", () => {
  const model = buildModel({
    runtime: {
      runtime_status: "running",
      current_stage: "solver-dispatch",
      task_summary: "Dispatching the first simulation setup.",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      execution_plan: [
        {
          role_id: "solver-worker",
          owner: "worker-a",
          goal: "Run baseline case",
          status: "running",
          target_skills: ["submarine-solver-dispatch"],
        },
      ],
      activity_timeline: [
        {
          actor: "worker-a",
          title: "Running solver",
          summary: "Baseline solver dispatch has started.",
          status: "running",
          skill_names: ["submarine-solver-dispatch"],
        },
      ],
    },
    designBrief: {
      summary_zh: "SUBOFF 基线算例准备",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      requested_outputs: [{ label: "阻力系数" }],
    },
    messageCount: 10,
    artifactCount: 4,
  });

  assert.equal(model.activeSliceId, "simulation-execution");
  assert.equal(model.currentSlice.id, "simulation-execution");
  assert.ok(model.slices.length <= 4);
  assert.ok(
    model.slices.every(
      (slice: { id: string }) => slice.id !== "execution" && slice.id !== "report",
    ),
  );
  assert.equal("modules" in model, false);
  assert.equal("activeModuleId" in model, false);
});

void test("keeps a draft design-brief thread in geometry preflight instead of misclassifying it as results delivery", () => {
  const model = buildModel({
    runtime: {
      current_stage: "task-intelligence",
      review_status: "needs_user_confirmation",
      next_recommended_stage: "user-confirmation",
      task_summary:
        "Inspect the uploaded STL geometry and prepare a preflight decision before any solver run.",
      geometry_virtual_path: "/mnt/user-data/uploads/20260210_111934_suboff_solid.stl",
      report_virtual_path:
        "/mnt/user-data/outputs/submarine/design-brief/20260210_111934_suboff_solid/cfd-design-brief.md",
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/design-brief/20260210_111934_suboff_solid/cfd-design-brief.json",
        "/mnt/user-data/outputs/submarine/design-brief/20260210_111934_suboff_solid/cfd-design-brief.md",
      ],
      requested_outputs: [{ label: "STL几何可用性预检结论" }],
      execution_plan: [
        {
          role_id: "geometry-preflight",
          owner: "DeerFlow geometry-preflight",
          goal: "Inspect the uploaded STL geometry",
          status: "pending",
        },
      ],
    },
    designBrief: {
      summary_zh:
        "对上传的 STL 做几何可用性预检，确认尺度、封闭性与是否适合做 DARPA SUBOFF 裸艇阻力基线研究的前置条件，并给出后续 CFD 准备建议；当前不启动求解。",
      geometry_virtual_path: "/mnt/user-data/uploads/20260210_111934_suboff_solid.stl",
      confirmation_status: "draft",
      execution_outline: [
        {
          phase_id: "geometry-preflight",
          title: "先完成几何预检与条件确认",
        },
      ],
      requested_outputs: [{ label: "STL几何可用性预检结论" }],
      open_questions: ["是否沿用演示性基线工况"],
    },
    artifactCount: 3,
    messageCount: 8,
  });

  assert.deepEqual(
    model.slices.map((slice: { id: string }) => slice.id),
    ["task-establishment", "geometry-preflight"],
  );
  assert.equal(model.activeSliceId, "geometry-preflight");
  assert.equal(
    model.slices.some((slice: { id: string }) => slice.id === "results-and-delivery"),
    false,
  );
  assert.equal(
    model.slices.some((slice: { id: string }) => slice.id === "simulation-plan"),
    false,
  );
  assert.match(model.currentSlice.nextRecommendedAction, /确认|工况/);
  assert.match(model.negotiation.question ?? "", /确认|工况/);
});

void test("treats an explicit runtime confirmation gate as a pending geometry-preflight approval even without open-question bookkeeping", () => {
  const model = buildModel({
    runtime: {
      current_stage: "task-intelligence",
      review_status: "needs_user_confirmation",
      next_recommended_stage: "user-confirmation",
      task_summary:
        "Hold geometry preflight until the researcher confirms the demonstration baseline conditions.",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      requested_outputs: [{ label: "几何预检摘要" }],
      execution_plan: [
        {
          role_id: "geometry-preflight",
          owner: "DeerFlow geometry-preflight",
          goal: "Wait for confirmation before geometry check",
          status: "pending",
        },
      ],
    },
    designBrief: {
      summary_zh: "当前先确认演示基线工况，再继续 STL 几何预检。",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      confirmation_status: "draft",
      execution_outline: [
        {
          phase_id: "geometry-preflight",
          title: "等待研究者确认演示工况",
        },
      ],
      requested_outputs: [{ label: "几何预检摘要" }],
      open_questions: [],
    },
    messageCount: 6,
    artifactCount: 2,
  });

  assert.equal(model.activeSliceId, "geometry-preflight");
  assert.equal(model.currentSlice.id, "geometry-preflight");
  assert.equal(model.currentSlice.statusLabel, "待确认");
  assert.equal(model.negotiation.pendingApprovalCount, 3);
  assert.match(model.currentSlice.agentInterpretation, /确认|协商区/);
  assert.match(model.currentSlice.nextRecommendedAction, /确认|研究者/);
});

void test("surfaces concrete negotiation items and input guidance instead of only a pending count", () => {
  const model = buildModel({
    runtime: {
      current_stage: "geometry-preflight",
      review_status: "needs_user_confirmation",
      next_recommended_stage: "user-confirmation",
      requires_immediate_confirmation: true,
      calculation_plan: [
        {
          item_id: "reference-length",
          category: "geometry",
          label: "参考长度",
          proposed_value: 4.356,
          unit: "m",
          source_label: "几何预检",
          approval_state: "pending_researcher_confirmation",
          requires_immediate_confirmation: true,
          evidence_gap_note: "请确认当前 STL 尺度是否按毫米转米解释。",
        },
        {
          item_id: "inlet-velocity",
          category: "condition",
          label: "入口速度",
          proposed_value: 5,
          unit: "m/s",
          source_label: "DARPA SUBOFF 基线",
          approval_state: "pending_researcher_confirmation",
          requires_immediate_confirmation: false,
        },
      ],
    },
    designBrief: {
      summary_zh: "请先确认尺度解释与首个基线工况。",
      confirmation_status: "draft",
      open_questions: ["是否沿用 5 m/s 演示基线工况？"],
    },
    messageCount: 6,
    artifactCount: 2,
  });

  assert.equal(model.negotiation.pendingApprovalCount, 3);
  assert.equal(model.negotiation.pendingItems.length, 3);
  assert.deepEqual(
    model.negotiation.pendingItems.map((item) => item.label),
    ["参考长度", "入口速度", "是否沿用 5 m/s 演示基线工况？"],
  );
  assert.match(model.negotiation.pendingItems[0]?.detail ?? "", /4\.356 m|毫米转米|几何预检/);
  assert.match(model.negotiation.summary ?? "", /3 项待确认|关键确认/);
  assert.match(model.negotiation.inputGuidance ?? "", /下方输入框|立即显示/);
});

void test("keeps design-brief pending approvals visible when the runtime plan is temporarily empty", () => {
  const model = buildModel({
    runtime: {
      current_stage: "geometry-preflight",
      review_status: "needs_user_confirmation",
      next_recommended_stage: "user-confirmation",
      calculation_plan: [],
    },
    designBrief: {
      summary_zh: "请先确认前置参数。",
      confirmation_status: "draft",
      calculation_plan: [
        {
          item_id: "reference-area",
          category: "geometry",
          label: "参考面积",
          proposed_value: 0.370988,
          unit: "m^2",
          source_label: "设计简报",
          approval_state: "pending_researcher_confirmation",
          requires_immediate_confirmation: true,
        },
      ],
      open_questions: ["是否只保留单一 baseline 工况？"],
    },
    messageCount: 4,
    artifactCount: 1,
  });

  assert.equal(model.negotiation.pendingApprovalCount, 2);
  assert.equal(model.negotiation.pendingItems[0]?.label, "参考面积");
  assert.match(
    model.negotiation.pendingItems[1]?.label ?? "",
    /是否只保留单一 .*工况？/,
  );
});

void test("lists each blocking reason when structured confirmation items are unavailable", () => {
  const model = buildModel({
    runtime: {
      current_stage: "geometry-preflight",
      review_status: "needs_user_confirmation",
      next_recommended_stage: "user-confirmation",
      requires_immediate_confirmation: true,
    },
    messageCount: 2,
  });

  assert.equal(model.negotiation.pendingApprovalCount, 4);
  assert.deepEqual(
    model.negotiation.pendingItems.map((item) => item.label),
    [
      "当前存在待你确认的研究决策，主智能体会先停在协商区。",
      "当前建议先完成研究者确认，再继续推进计算。",
      "存在需要立刻确认的参数或边界条件。",
      "还有 4 项待确认事项。",
    ],
  );
});

void test("does not surface raw unresolved-decision ids when localized labels are missing", () => {
  const model = buildModel({
    runtime: {
      review_status: "needs_user_confirmation",
      current_stage: "geometry-preflight",
    },
    designBrief: {
      summary_zh: "当前仍需确认一个研究决策。",
      confirmation_status: "draft",
      unresolved_decisions: [
        {
          decision_id: "confirm_tail_window",
          output_id: "wake_velocity_slice",
        },
      ],
      open_questions: [],
    },
  });

  assert.equal(model.negotiation.pendingApprovalCount, 1);
  assert.doesNotMatch(
    model.negotiation.pendingItems[0]?.label ?? "",
    /confirm_tail_window|wake_velocity_slice/,
  );
  assert.match(model.negotiation.pendingItems[0]?.label ?? "", /未命名研究项/);
});

void test("does not collapse same-label pending plan items coming from different snapshots", () => {
  const model = buildModel({
    runtime: {
      current_stage: "geometry-preflight",
      calculation_plan: [
        {
          label: "参考长度",
          proposed_value: 4.356,
          unit: "m",
          source_label: "运行时快照",
          approval_state: "pending_researcher_confirmation",
        },
      ],
    },
    designBrief: {
      confirmation_status: "draft",
      calculation_plan: [
        {
          label: "参考长度",
          proposed_value: 4.4,
          unit: "m",
          source_label: "设计简报",
          approval_state: "pending_researcher_confirmation",
        },
      ],
      open_questions: [],
    },
  });

  assert.deepEqual(
    model.negotiation.pendingItems.map((item) => item.detail),
    [
      "建议值：4.4 m；来源：设计简报",
      "建议值：4.356 m；来源：运行时快照",
    ],
  );
});

void test("keeps open questions visible even when their label matches a pending plan item", () => {
  const model = buildModel({
    designBrief: {
      confirmation_status: "draft",
      calculation_plan: [
        {
          item_id: "reference-length",
          label: "参考长度",
          approval_state: "pending_researcher_confirmation",
          requires_immediate_confirmation: true,
        },
      ],
      open_questions: ["参考长度"],
    },
  });

  assert.deepEqual(
    model.negotiation.pendingItems.map((item) => item.label),
    ["参考长度", "参考长度"],
  );
});

void test("keeps a completed geometry-check artifact thread in geometry-preflight instead of skipping straight to delivery review", () => {
  const model = buildModel({
    runtime: {
      current_stage: "geometry-preflight",
      review_status: "needs_user_confirmation",
      next_recommended_stage: "user-confirmation",
      task_summary:
        "请先对这个 STL 做几何可用性预检，确认尺度、封闭性与是否适合做 SUBOFF 裸艇阻力基线研究；当前不要启动求解。",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      report_virtual_path:
        "/mnt/user-data/outputs/submarine/geometry-check/suboff_solid/geometry-check.md",
      artifact_virtual_paths: [
        "/mnt/user-data/outputs/submarine/geometry-check/suboff_solid/geometry-check.md",
        "/mnt/user-data/outputs/submarine/geometry-check/suboff_solid/geometry-check.html",
        "/mnt/user-data/outputs/submarine/geometry-check/suboff_solid/geometry-check.json",
      ],
      requested_outputs: [{ label: "几何预检摘要" }],
      calculation_plan: [
        {
          item_id: "geometry.reference_length_m",
          category: "geometry",
          label: "参考长度",
          approval_state: "pending_researcher_confirmation",
          requires_immediate_confirmation: true,
        },
      ],
      execution_plan: [
        {
          role_id: "geometry-preflight",
          owner: "DeerFlow geometry-preflight",
          goal: "Inspect the uploaded STL geometry",
          status: "completed",
        },
      ],
    },
    designBrief: {
      summary_zh:
        "对上传的 STL 做几何可用性预检，确认尺度、封闭性与是否适合做 SUBOFF 裸艇阻力基线研究，并给出后续 CFD 准备建议；当前不启动求解。",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      confirmation_status: "draft",
      requested_outputs: [{ label: "几何预检摘要" }],
      open_questions: [],
    },
    artifactCount: 3,
    messageCount: 4,
  });

  assert.deepEqual(
    model.slices.map((slice: { id: string }) => slice.id),
    ["task-establishment", "geometry-preflight"],
  );
  assert.equal(model.activeSliceId, "geometry-preflight");
  assert.equal(model.currentSlice.id, "geometry-preflight");
  assert.equal(
    model.slices.some((slice: { id: string }) => slice.id === "results-and-delivery"),
    false,
  );
  assert.equal(
    model.slices.some((slice: { id: string }) => slice.id === "simulation-plan"),
    false,
  );
});

void test("prefers the concise runtime task summary over a verbose design-brief summary when presenting the current slice", () => {
  const conciseTaskSummary =
    "对上传的 STL 做几何预检，并先确认是否沿用演示基线工况。";
  const verboseDesignBriefSummary =
    "已整理 CFD 设计简报：对上传的 STL 做几何可用性预检，确认尺度、封闭性与是否适合做 DARPA SUBOFF 裸艇阻力基线研究的前置条件，并给出后续 CFD 准备建议；当前不启动求解。";
  const model = buildModel({
    runtime: {
      current_stage: "task-intelligence",
      task_summary: conciseTaskSummary,
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
    },
    designBrief: {
      summary_zh: verboseDesignBriefSummary,
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      requested_outputs: [{ label: "几何预检摘要" }],
      open_questions: [],
    },
    messageCount: 5,
    artifactCount: 1,
  });

  assert.equal(model.currentSlice.id, "geometry-preflight");
  assert.equal(model.currentSlice.summary, conciseTaskSummary);
});

void test("sanitizes task-establishment copy for historical inspection instead of surfacing raw paths and internal brief tokens", () => {
  const model = buildModel({
    runtime: {
      current_stage: "task-intelligence",
      task_summary: "对上传的 STL 做几何预检，并确认是否沿用演示基线工况。",
      geometry_virtual_path: "/mnt/user-data/uploads/20260210_111934_suboff_solid.stl",
    },
    designBrief: {
      summary_zh:
        "请基于 /mnt/user-data/uploads/20260210_111934_suboff_solid.stl 整理 darpa_suboff_bare_hull_resistance 的前置设计 brief，并确认当前只做几何预检与基线工况判断。",
      geometry_virtual_path: "/mnt/user-data/uploads/20260210_111934_suboff_solid.stl",
      requested_outputs: [{ label: "几何预检摘要" }],
      open_questions: [],
    },
    messageCount: 5,
    artifactCount: 1,
  });

  const taskEstablishmentSlice = model.slices.find((slice) => slice.id === "task-establishment");
  assert.ok(taskEstablishmentSlice);
  assert.doesNotMatch(
    taskEstablishmentSlice.agentInterpretation,
    /\/mnt\/user-data|darpa_suboff_bare_hull_resistance/,
  );
  assert.match(
    taskEstablishmentSlice.agentInterpretation,
    /几何预检|基线工况|SUBOFF|STL/i,
  );
  assert.match(
    taskEstablishmentSlice.keyEvidenceSummary,
    /20260210_111934_suboff_solid\.stl/,
  );
});

void test("compresses verbose early-thread summaries into short research snapshots for the ribbon and slice card", () => {
  const model = buildModel({
    runtime: {
      current_stage: "task-intelligence",
      task_summary:
        "对上传的 STL 做几何可用性预检，确认尺度、封闭性与是否适合做 DARPA SUBOFF 裸艇阻力基线研究的前置条件，并给出后续 CFD 准备建议；当前不启动求解。",
      geometry_virtual_path: "/mnt/user-data/uploads/20260210_111934_suboff_solid.stl",
    },
    designBrief: {
      summary_zh:
        "对上传的 STL 做几何可用性预检，确认尺度、封闭性与是否适合做 DARPA SUBOFF 裸艇阻力基线研究的前置条件，并给出后续 CFD 准备建议；当前不启动求解。",
      geometry_virtual_path: "/mnt/user-data/uploads/20260210_111934_suboff_solid.stl",
      requested_outputs: [{ label: "几何预检摘要" }],
      open_questions: [],
    },
    messageCount: 5,
    artifactCount: 1,
  });

  const taskEstablishmentSlice = model.slices.find((slice) => slice.id === "task-establishment");
  const geometrySlice = model.slices.find((slice) => slice.id === "geometry-preflight");
  assert.ok(taskEstablishmentSlice);
  assert.ok(geometrySlice);
  assert.equal(
    taskEstablishmentSlice.summary,
    "对上传的 STL 做几何可用性预检，并给出后续 CFD 准备建议。",
  );
  assert.equal(
    geometrySlice.summary,
    "对上传的 STL 做几何可用性预检，并给出后续 CFD 准备建议。",
  );
});

void test("creates a simulation-plan slice once the design brief is confirmed and the planning outline is no longer speculative", () => {
  const model = buildModel({
    runtime: {
      current_stage: "task-intelligence",
      task_summary: "The geometry has been preflighted and the first solver setup can now be planned.",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
    },
    designBrief: {
      summary_zh: "几何预检已完成，可以整理首次求解准备方案。",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      confirmation_status: "confirmed",
      execution_outline: [
        {
          phase_id: "simulation-plan",
          title: "整理首次求解准备方案",
        },
      ],
      requested_outputs: [{ label: "阻力系数" }],
      open_questions: [],
    },
    messageCount: 7,
    artifactCount: 2,
  });

  assert.deepEqual(
    model.slices.map((slice: { id: string }) => slice.id),
    ["task-establishment", "geometry-preflight", "simulation-plan"],
  );
  assert.equal(model.activeSliceId, "simulation-plan");
});

void test("keeps the active slice stable while entering historical inspection mode for an older slice", () => {
  const model = buildModel({
    runtime: {
      runtime_status: "completed",
      current_stage: "supervisor-review",
      task_summary: "Reviewing the first result package.",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      report_virtual_path: "/artifacts/submarine/final-report.json",
      requested_outputs: [{ label: "阻力系数曲线" }],
    },
    designBrief: {
      summary_zh: "SUBOFF 结果交付评审",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      requested_outputs: [{ label: "阻力系数曲线" }],
    },
    finalReport: {
      summary_zh: "基线阻力系数结果已形成，可进入交付评审。",
      provenance_manifest_virtual_path: "/artifacts/submarine/provenance.json",
      reproducibility_summary: {
        manifest_virtual_path: "/artifacts/submarine/repro.json",
        reproducibility_status: "reproducible",
      },
      environment_parity_assessment: {
        parity_status: "aligned",
        profile_label: "OpenFOAM-12",
      },
    },
    viewedSliceId: "geometry-preflight",
    messageCount: 16,
    artifactCount: 9,
  });

  assert.equal(model.activeSliceId, "results-and-delivery");
  assert.equal(model.currentSlice.id, "results-and-delivery");
  assert.equal(model.viewedSlice.id, "geometry-preflight");
  assert.equal(model.historyInspection.isViewingHistory, true);
  assert.match(model.historyInspection.bannerTitle ?? "", /历史切片/);
  assert.match(model.historyInspection.returnLabel ?? "", /返回当前研究/);
  assert.equal(model.trustSurface.provenanceAvailable, true);
  assert.equal(model.trustSurface.reproducibilityAvailable, true);
  assert.equal(model.trustSurface.environmentParityAvailable, true);
});

void test("marks a blocked delivery slice as blocked instead of advertising it as ready for review", () => {
  const model = buildModel({
    runtime: {
      runtime_status: "blocked",
      current_stage: "result-reporting",
      task_summary: "Continue with the recommended remediation and refresh the report.",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      report_virtual_path: "/artifacts/submarine/final-report.json",
      blocker_detail: "Solver metrics are unavailable for this run.",
      supervisor_handoff_virtual_path:
        "/artifacts/submarine/scientific-remediation-handoff.json",
    },
    designBrief: {
      summary_zh: "SUBOFF 阻力基线结果阻塞后的补证据处理。",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      confirmation_status: "confirmed",
      requested_outputs: [{ label: "阻力系数曲线" }],
    },
    finalReport: {
      summary_zh: "当前报告已生成，但科学审查仍要求补齐缺失的 solver metrics。",
      report_overview: {
        recommended_next_step_zh: "先补齐缺失的 solver metrics，再刷新报告。",
      },
      scientific_supervisor_gate: {
        gate_status: "blocked",
        blocking_reasons: ["Solver metrics are unavailable for this run."],
      },
      scientific_remediation_handoff: {
        handoff_status: "ready_for_auto_followup",
        recommended_action_id: "execute-scientific-studies",
        tool_name: "submarine_solver_dispatch",
        reason: "Solver metrics are unavailable for this run.",
      },
    },
    viewedSliceId: null,
    messageCount: 16,
    artifactCount: 9,
  });

  assert.equal(model.activeSliceId, "results-and-delivery");
  assert.equal(model.currentSlice.statusLabel, "受阻");
  assert.match(model.currentSlice.summary, /solver metrics|补齐/i);
  assert.match(model.currentSlice.nextRecommendedAction, /补齐|修正|报告/);
});

void test("sanitizes results-and-delivery slice summaries instead of leaking raw stage ids and case ids", () => {
  const model = buildModel({
    runtime: {
      runtime_status: "blocked",
      current_stage: "result-reporting",
      task_summary: "Refresh the blocked SUBOFF delivery thread.",
    },
    finalReport: {
      summary_zh:
        "已生成《潜艇 CFD 阶段报告》，来源阶段为 `result-reporting`。选定案例 `darpa_suboff_bare_hull_resistance`。当前结果已经进入报告整理阶段。",
      scientific_supervisor_gate: {
        gate_status: "blocked",
      },
    },
  });

  assert.equal(model.currentSlice.id, "results-and-delivery");
  assert.doesNotMatch(
    model.currentSlice.summary,
    /result-reporting|darpa_suboff_bare_hull_resistance/,
  );
  assert.match(model.currentSlice.summary, /结果整理|DARPA SUBOFF 裸艇阻力基线/);
  assert.doesNotMatch(
    model.currentSlice.agentInterpretation,
    /result-reporting|darpa_suboff_bare_hull_resistance/,
  );
});

void test("ignores stale confirmation-gate runtime flags once the confirmed brief and final report show no unresolved decisions", () => {
  const model = buildModel({
    runtime: {
      current_stage: "geometry-preflight",
      review_status: "needs_user_confirmation",
      next_recommended_stage: "user-confirmation",
      runtime_status: "blocked",
      contract_revision: 5,
      iteration_mode: "revise_baseline",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      calculation_plan: [
        {
          item_id: "geometry.reference_length_m",
          label: "参考长度",
          approval_state: "researcher_confirmed",
          requires_immediate_confirmation: true,
        },
      ],
    },
    designBrief: {
      summary_zh: "当前合同已经确认，可继续以结果报告为准。",
      confirmation_status: "confirmed",
      contract_revision: 5,
      iteration_mode: "revise_baseline",
      open_questions: [],
      calculation_plan: [
        {
          item_id: "geometry.reference_length_m",
          label: "参考长度",
          approval_state: "researcher_confirmed",
          requires_immediate_confirmation: true,
        },
      ],
      unresolved_decisions: [],
    },
    finalReport: {
      summary_zh: "当前报告已生成，后续工作应围绕科学阻塞项展开。",
      contract_revision: 5,
      iteration_mode: "revise_baseline",
      unresolved_decisions: [],
      scientific_supervisor_gate: {
        gate_status: "blocked",
        blocking_reasons: ["Mesh independence study remains blocked."],
      },
      report_overview: {
        recommended_next_step_zh: "先处理当前阻塞项并修正设置或证据链，再决定是否继续求解。",
      },
    },
    messageCount: 18,
    artifactCount: 48,
  });

  assert.equal(model.activeSliceId, "results-and-delivery");
  assert.equal(model.currentSlice.statusLabel, "受阻");
  assert.equal(model.negotiation.pendingApprovalCount, 0);
  assert.deepEqual(model.negotiation.pendingItems, []);
  assert.equal(model.negotiation.summary, null);
  assert.equal(model.negotiation.question, null);
});

void test("keeps a live immediate-confirmation blocker visible even when a final report artifact already exists", () => {
  const model = buildModel({
    runtime: {
      current_stage: "geometry-preflight",
      review_status: "needs_user_confirmation",
      next_recommended_stage: "user-confirmation",
      requires_immediate_confirmation: true,
      runtime_status: "blocked",
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
    },
    designBrief: {
      summary_zh: "当前仍需确认一个新的关键边界条件。",
      confirmation_status: "confirmed",
      open_questions: [],
      unresolved_decisions: [],
    },
    finalReport: {
      summary_zh: "已有上一轮结果报告，但这轮新增修改仍要求研究者即时确认。",
      unresolved_decisions: [],
    },
  });

  assert.equal(model.negotiation.pendingApprovalCount, 4);
  assert.deepEqual(
    model.negotiation.pendingItems.map((item) => item.label),
    [
      "当前存在待你确认的研究决策，主智能体会先停在协商区。",
      "当前建议先完成研究者确认，再继续推进计算。",
      "存在需要立刻确认的参数或边界条件。",
      "还有 4 项待确认事项。",
    ],
  );
});
