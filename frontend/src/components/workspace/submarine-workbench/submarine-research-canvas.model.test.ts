import assert from "node:assert/strict";
import test from "node:test";

const {
  buildSubmarineResearchSnapshotSummary,
  buildSliceContextNotesModel,
  buildSliceEvidenceBadgesModel,
  buildSliceFactsModel,
} = await import(
  new URL("./submarine-research-canvas.model.ts", import.meta.url).href,
);

void test("geometry-preflight facts avoid generic execution-plan counts when the slice is blocked on confirmation", () => {
  const facts = buildSliceFactsModel({
    sliceId: "geometry-preflight",
    pendingApprovalCount: 1,
    runtimeStatus: null,
    artifactCount: 3,
    executionPlanCount: 10,
    skillNames: [],
    requestedOutputs: ["几何预检摘要", "工况建议"],
  });

  assert.deepEqual(facts, [
    { label: "当前进度", value: "1 项待确认" },
    { label: "研究产物", value: "3 项研究产物" },
    { label: "协作线索", value: "优先确认工况与约束" },
  ]);
});

void test("simulation-plan facts can still surface concrete solver-preparation breadth once planning is the active slice", () => {
  const facts = buildSliceFactsModel({
    sliceId: "simulation-plan",
    pendingApprovalCount: 0,
    runtimeStatus: null,
    artifactCount: 2,
    executionPlanCount: 4,
    skillNames: [],
    requestedOutputs: ["阻力系数", "压力分布"],
  });

  assert.deepEqual(facts, [
    { label: "当前进度", value: "当前无阻塞项" },
    { label: "研究产物", value: "2 项研究产物" },
    { label: "协作线索", value: "4 项求解准备" },
  ]);
});

void test("results-and-delivery facts surface a blocked runtime instead of claiming there is no blocker", () => {
  const facts = buildSliceFactsModel({
    sliceId: "results-and-delivery",
    pendingApprovalCount: 0,
    runtimeStatus: "blocked",
    artifactCount: 22,
    executionPlanCount: 0,
    skillNames: [],
    requestedOutputs: [],
  });

  assert.deepEqual(facts, [
    { label: "当前进度", value: "运行已阻塞" },
    { label: "研究产物", value: "22 项研究产物" },
    { label: "协作线索", value: "结果审阅与交付判断" },
  ]);
});

void test("task-establishment context notes stay readable in history view instead of echoing raw paths and internal brief ids", () => {
  const notes = buildSliceContextNotesModel({
    sliceId: "task-establishment",
    runtime: {
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
    finalReport: null,
    requestedOutputs: ["几何预检摘要"],
    verificationRequirements: [],
    skillNames: [],
    executionPlanCount: 0,
    artifactPaths: [],
  });

  assert.ok(notes.length > 0);
  assert.ok(notes.some((note) => /20260210_111934_suboff_solid\.stl/.test(note)));
  assert.ok(notes.every((note) => !/\/mnt\/user-data/.test(note)));
  assert.ok(notes.every((note) => !/darpa_suboff_bare_hull_resistance/.test(note)));
});

void test("task-establishment context notes use the compressed research snapshot instead of the full verbose brief", () => {
  const notes = buildSliceContextNotesModel({
    sliceId: "task-establishment",
    runtime: {
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
    finalReport: null,
    requestedOutputs: ["几何预检摘要"],
    verificationRequirements: [],
    skillNames: [],
    executionPlanCount: 0,
    artifactPaths: [],
  });

  assert.ok(
    notes.includes("当前研究目标已收敛为：对上传的 STL 做几何可用性预检，并给出后续 CFD 准备建议。"),
  );
});

void test("research snapshot summaries localize mixed workflow jargon before they reach the workbench header and slice cards", () => {
  const summary = buildSubmarineResearchSnapshotSummary(
    "刚才那次 scientific follow-up 因服务重连中断，请忽略中断中的结果。当前允许的 claim level 为“仅限交付说明”，后续可直接交由 Supervisor 做质量复核。",
    200,
  );

  assert.ok(summary);
  assert.doesNotMatch(summary ?? "", /scientific follow-up|claim level|Supervisor/i);
  assert.match(summary ?? "", /科研跟进/);
});

void test("task-establishment requested-output note stays count-first instead of dumping every long output label", () => {
  const notes = buildSliceContextNotesModel({
    sliceId: "task-establishment",
    runtime: {
      task_summary: "对上传的 STL 做几何可用性预检，并给出后续 CFD 准备建议。",
      geometry_virtual_path: "/mnt/user-data/uploads/20260210_111934_suboff_solid.stl",
    },
    designBrief: {
      summary_zh: "对上传的 STL 做几何可用性预检，并给出后续 CFD 准备建议。",
      geometry_virtual_path: "/mnt/user-data/uploads/20260210_111934_suboff_solid.stl",
      requested_outputs: [
        { label: "STL几何可用性预检结论" },
        { label: "尺度/封闭性检查" },
        { label: "是否适合SUBOFF裸艇阻力基线研究的前置条件判断" },
      ],
      open_questions: [],
    },
    finalReport: null,
    requestedOutputs: [
      "STL几何可用性预检结论",
      "尺度/封闭性检查",
      "是否适合SUBOFF裸艇阻力基线研究的前置条件判断",
    ],
    verificationRequirements: [],
    skillNames: [],
    executionPlanCount: 0,
    artifactPaths: [],
  });

  assert.ok(notes.includes("当前最关注 3 项交付输出。"));
  assert.ok(notes.includes("当前优先确认 STL几何可用性预检结论、尺度/封闭性检查。"));
  assert.ok(notes.every((note) => !note.includes("是否适合SUBOFF裸艇阻力基线研究的前置条件判断")));
});

void test("evidence badges localize raw runtime stage ids before they reach the center card", () => {
  const badges = buildSliceEvidenceBadgesModel({
    runtime: {
      geometry_virtual_path: "/mnt/user-data/uploads/20260210_111934_suboff_solid.stl",
      current_stage: "task-intelligence",
      runtime_status: null,
    },
    designBrief: null,
    finalReport: null,
    artifactPaths: ["/mnt/user-data/outputs/submarine/design-brief/demo/cfd-design-brief.json"],
    requestedOutputs: ["几何预检摘要"],
  });

  assert.ok(badges.includes("几何: 20260210_111934_suboff_solid.stl"));
  assert.ok(badges.includes("阶段: 研究判断整理中"));
  assert.ok(badges.every((badge) => !badge.includes("task-intelligence")));
});

void test("evidence badges localize geometry-preflight instead of leaking the raw stage id", () => {
  const badges = buildSliceEvidenceBadgesModel({
    runtime: {
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      current_stage: "geometry-preflight",
      runtime_status: "ready",
    },
    designBrief: null,
    finalReport: null,
    artifactPaths: [
      "/mnt/user-data/outputs/submarine/geometry-check/suboff_solid/geometry-check.md",
    ],
    requestedOutputs: [],
  });

  assert.ok(badges.includes("阶段: 几何预检"));
  assert.ok(badges.every((badge) => !badge.includes("geometry-preflight")));
});

void test("evidence badges surface iterative contract revision and delivery progress", () => {
  const badges = buildSliceEvidenceBadgesModel({
    runtime: {
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      current_stage: "result-reporting",
      runtime_status: "completed",
      contract_revision: 3,
      iteration_mode: "derive_variant",
      output_delivery_plan: [
        { output_id: "drag_coefficient", delivery_status: "delivered" },
        { output_id: "wake_velocity_slice", delivery_status: "planned" },
        { output_id: "streamlines", delivery_status: "not_yet_supported" },
      ],
    },
    designBrief: null,
    finalReport: null,
    artifactPaths: ["/mnt/user-data/outputs/submarine/reports/demo/final-report.json"],
    requestedOutputs: ["阻力系数", "尾流速度切片"],
  });

  assert.ok(badges.includes("合同: r3"));
  assert.ok(badges.includes("迭代: 派生变体"));
  assert.ok(badges.includes("交付: 1/3 已交付"));
});

void test("evidence badges localize provenance wording instead of exposing english tracking jargon", () => {
  const badges = buildSliceEvidenceBadgesModel({
    runtime: {
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      current_stage: "result-reporting",
      runtime_status: "completed",
    },
    designBrief: null,
    finalReport: {
      provenance_manifest_virtual_path:
        "/mnt/user-data/outputs/submarine/reports/demo/provenance-manifest.json",
    },
    artifactPaths: ["/mnt/user-data/outputs/submarine/reports/demo/final-report.json"],
    requestedOutputs: [],
  });

  assert.ok(badges.includes("含溯源记录"));
  assert.ok(badges.every((badge) => !badge.includes("provenance")));
});

void test("evidence badges prefer the final report source stage when runtime stage metadata is stale", () => {
  const badges = buildSliceEvidenceBadgesModel({
    runtime: {
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      current_stage: "geometry-preflight",
      runtime_status: "blocked",
    },
    designBrief: null,
    finalReport: {
      source_runtime_stage: "result-reporting",
    },
    artifactPaths: ["/mnt/user-data/outputs/submarine/reports/demo/final-report.json"],
    requestedOutputs: [],
  });

  assert.ok(badges.includes("阶段: 结果整理中"));
  assert.ok(badges.every((badge) => !badge.includes("阶段: 几何预检")));
});

void test("evidence badges localize raw runtime status ids before they reach the center card", () => {
  const badges = buildSliceEvidenceBadgesModel({
    runtime: {
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      current_stage: "result-reporting",
      runtime_status: "blocked",
    },
    designBrief: null,
    finalReport: null,
    artifactPaths: ["/mnt/user-data/outputs/submarine/reports/demo/final-report.json"],
    requestedOutputs: [],
  });

  assert.ok(badges.includes("运行: 已阻塞"));
  assert.ok(badges.every((badge) => !badge.includes("运行: blocked")));
});

void test("evidence badges hide unmapped runtime enums behind generic user-facing fallbacks", () => {
  const badges = buildSliceEvidenceBadgesModel({
    runtime: {
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      current_stage: "custom-followup-stage",
      runtime_status: "awaiting_external_sync",
    },
    designBrief: null,
    finalReport: null,
    artifactPaths: [],
    requestedOutputs: [],
  });

  assert.ok(badges.includes("运行: 状态待同步"));
  assert.ok(badges.includes("阶段: 阶段待同步"));
  assert.ok(badges.every((badge) => !badge.includes("awaiting_external_sync")));
  assert.ok(badges.every((badge) => !badge.includes("custom-followup-stage")));
});

void test("evidence badges hide unknown iteration-mode slugs behind a generic user-facing fallback", () => {
  const badges = buildSliceEvidenceBadgesModel({
    runtime: {
      geometry_virtual_path: "/mnt/user-data/uploads/suboff_solid.stl",
      current_stage: "result-reporting",
      runtime_status: "completed",
      iteration_mode: "unexpected_followup_mode",
    },
    designBrief: null,
    finalReport: null,
    artifactPaths: [],
    requestedOutputs: [],
  });

  assert.ok(badges.includes("迭代: 迭代模式待同步"));
  assert.ok(badges.every((badge) => !badge.includes("unexpected_followup_mode")));
});

void test("results-and-delivery context notes localize raw stage ids from structured summaries", () => {
  const notes = buildSliceContextNotesModel({
    sliceId: "results-and-delivery",
    runtime: null,
    designBrief: null,
    finalReport: {
      summary_zh:
        "已生成《潜艇 CFD 阶段报告》，来源阶段为 `result-reporting`。当前结果已经进入报告整理阶段。",
    },
    requestedOutputs: [],
    verificationRequirements: [],
    skillNames: [],
    executionPlanCount: 0,
    artifactPaths: [],
  });

  assert.ok(notes.some((note) => note.includes("结果整理")));
  assert.ok(notes.every((note) => !note.includes("result-reporting")));
});

void test("results-and-delivery context notes localize remaining english workflow phrases from structured summaries", () => {
  const notes = buildSliceContextNotesModel({
    sliceId: "results-and-delivery",
    runtime: null,
    designBrief: null,
    finalReport: {
      summary_zh:
        "已生成《潜艇 CFD 阶段报告》，当前允许的 claim level 为“仅限交付说明”；可直接交由 Supervisor 做质量复核；必要时继续 scientific follow-up。",
    },
    requestedOutputs: [],
    verificationRequirements: [],
    skillNames: [],
    executionPlanCount: 0,
    artifactPaths: [],
  });

  assert.ok(notes.some((note) => /结论口径/.test(note)));
  assert.ok(notes.some((note) => /主管代理/.test(note)));
  assert.ok(notes.some((note) => /科研跟进/.test(note)));
  assert.ok(notes.every((note) => !/claim level|Supervisor|scientific follow-up/i.test(note)));
});

void test("results-and-delivery context notes hide unknown slug-like tokens from structured summaries", () => {
  const notes = buildSliceContextNotesModel({
    sliceId: "results-and-delivery",
    runtime: null,
    designBrief: null,
    finalReport: {
      summary_zh:
        "当前 custom_stage_alpha 已完成，但 followup_status_beta 仍待处理。",
    },
    requestedOutputs: [],
    verificationRequirements: [],
    skillNames: [],
    executionPlanCount: 0,
    artifactPaths: [],
  });

  assert.ok(notes.some((note) => note.includes("相关研究项")));
  assert.ok(notes.every((note) => !note.includes("custom_stage_alpha")));
  assert.ok(notes.every((note) => !note.includes("followup_status_beta")));
});

void test("results-and-delivery context notes keep legitimate technical hyphenated terms readable", () => {
  const notes = buildSliceContextNotesModel({
    sliceId: "results-and-delivery",
    runtime: null,
    designBrief: null,
    finalReport: {
      summary_zh: "建议继续检查 k-epsilon 湍流模型与 y-plus 设定。",
    },
    requestedOutputs: [],
    verificationRequirements: [],
    skillNames: [],
    executionPlanCount: 0,
    artifactPaths: [],
  });

  assert.ok(notes.some((note) => note.includes("k-epsilon")));
  assert.ok(notes.some((note) => note.includes("y-plus")));
  assert.ok(notes.every((note) => !note.includes("相关研究项")));
});

void test("simulation-plan context notes localize English revision-summary copy before it reaches the canvas", () => {
  const notes = buildSliceContextNotesModel({
    sliceId: "simulation-plan",
    runtime: {
      revision_summary: "Updated the structured CFD design brief.",
    },
    designBrief: null,
    finalReport: null,
    requestedOutputs: [],
    verificationRequirements: [],
    skillNames: [],
    executionPlanCount: 0,
    artifactPaths: [],
  });

  assert.ok(notes.includes("已更新结构化 CFD 设计简报。"));
  assert.ok(notes.every((note) => !note.includes("Updated the structured CFD design brief.")));
});

void test("simulation-plan context notes surface contract revision, pending decisions, and delivery progress", () => {
  const notes = buildSliceContextNotesModel({
    sliceId: "simulation-plan",
    runtime: {
      contract_revision: 4,
      iteration_mode: "derive_variant",
      revision_summary: "Add wake-focused follow-up to the baseline family.",
      unresolved_decisions: [
        { decision_id: "confirm-tail-window" },
        { decision_id: "confirm-wake-origin" },
      ],
      output_delivery_plan: [
        { output_id: "drag_coefficient", delivery_status: "delivered" },
        { output_id: "wake_velocity_slice", delivery_status: "planned" },
        { output_id: "streamlines", delivery_status: "not_yet_supported" },
      ],
    },
    designBrief: null,
    finalReport: null,
    requestedOutputs: ["阻力系数", "尾流速度切片"],
    verificationRequirements: [],
    skillNames: ["submarine-solver-dispatch"],
    executionPlanCount: 2,
    artifactPaths: [],
  });

  assert.ok(notes.some((note) => /r4/.test(note)));
  assert.ok(notes.some((note) => /派生变体/.test(note)));
  assert.ok(notes.some((note) => /2 项未决/.test(note)));
  assert.ok(notes.some((note) => /已交付 1 项/.test(note)));
  assert.ok(notes.some((note) => /待完成 1 项/.test(note)));
  assert.ok(notes.some((note) => /受阻 1 项/.test(note)));
  assert.ok(notes.some((note) => /求解派发/.test(note)));
  assert.ok(notes.every((note) => !note.includes("submarine-solver-dispatch")));
});
