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
  assert.equal(model.negotiation.pendingApprovalCount, 1);
  assert.match(model.currentSlice.agentInterpretation, /确认|协商区/);
  assert.match(model.currentSlice.nextRecommendedAction, /确认|研究者/);
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
