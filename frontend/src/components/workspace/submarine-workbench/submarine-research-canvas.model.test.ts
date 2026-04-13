import assert from "node:assert/strict";
import test from "node:test";

const {
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
