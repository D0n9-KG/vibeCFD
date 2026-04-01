import assert from "node:assert/strict";
import test from "node:test";

const { getSubmarinePipelineStatus } = await import(
  new URL("./submarine-pipeline-status.ts", import.meta.url).href,
);

void test("surfaces a failed lead-agent run instead of leaving the workbench in a running-looking state", () => {
  const status = getSubmarinePipelineStatus({
    threadError: new Error(
      "Upstream authentication failed, please contact administrator",
    ),
    threadIsLoading: false,
    isNewThread: false,
    hasMessages: true,
    hasDesignBrief: true,
    hasFinalReport: false,
    designBriefSummary: "已整理 baseline 条件",
    runtimeTaskSummary: "准备进入几何预检",
  });

  assert.equal(status.tone, "error");
  assert.equal(status.agentLabel, "主智能体失败");
  assert.equal(status.runLabel, "失败");
  assert.equal(status.outputStatus, "主智能体失败");
  assert.equal(status.errorBanner?.title, "主智能体调用失败");
  assert.equal(
    status.errorBanner?.message,
    "Upstream authentication failed, please contact administrator",
  );
  assert.match(status.errorBanner?.guidance ?? "", /当前研究状态未能推进/);
  assert.match(status.summaryText, /当前研究状态未能推进/);
});

void test("shows configuration guidance for LangGraph bootstrap failures", () => {
  const status = getSubmarinePipelineStatus({
    threadError: new Error("LangGraph base URL is empty or invalid."),
    threadIsLoading: false,
    isNewThread: true,
    hasMessages: false,
    hasDesignBrief: false,
    hasFinalReport: false,
    designBriefSummary: null,
    runtimeTaskSummary: null,
  });

  assert.equal(
    status.errorBanner?.message,
    "LangGraph base URL is empty or invalid. Please verify the LangGraph URL configuration.",
  );
  assert.match(status.errorBanner?.guidance ?? "", /LangGraph URL/);
});

void test("shows a rehydration state instead of a blank new-thread status on refresh", () => {
  const status = getSubmarinePipelineStatus({
    threadError: null,
    threadIsLoading: true,
    isNewThread: false,
    hasMessages: false,
    hasDesignBrief: false,
    hasFinalReport: false,
    designBriefSummary: null,
    runtimeTaskSummary: null,
  });

  assert.equal(status.tone, "streaming");
  assert.equal(status.agentLabel, "主智能体恢复中");
  assert.equal(status.runLabel, "恢复中");
  assert.equal(status.outputStatus, "正在恢复已创建的研究线程");
  assert.equal(
    status.summaryText,
    "正在从已创建的潜艇仿真线程恢复消息、附件与研究产物，请稍候。",
  );
  assert.equal(status.errorBanner, null);
});

void test("surfaces persisted blocked runtime guidance after re-entry", () => {
  const status = getSubmarinePipelineStatus({
    threadError: null,
    threadIsLoading: false,
    isNewThread: false,
    hasMessages: true,
    hasDesignBrief: true,
    hasFinalReport: false,
    designBriefSummary: "baseline 已确认",
    runtimeTaskSummary: "进入求解派发",
    runtimeStatus: "blocked",
    runtimeSummary: "当前线程缺少可恢复的运行证据，工作台会把它显示为阻塞而不是普通待执行。",
    recoveryGuidance: "补齐缺失 artifacts，或重新运行当前阶段，确保请求、日志与结果文件重新注册到线程。",
    blockerDetail: "solver-dispatch 缺少可恢复的关键证据: 求解结果。",
  });

  assert.equal(status.tone, "error");
  assert.equal(status.agentLabel, "CFD runtime 受阻");
  assert.equal(status.runLabel, "受阻");
  assert.equal(status.outputStatus, "等待恢复");
  assert.equal(status.summaryText, "当前线程缺少可恢复的运行证据，工作台会把它显示为阻塞而不是普通待执行。");
  assert.equal(status.errorBanner?.title, "CFD runtime 已阻塞");
  assert.equal(
    status.errorBanner?.message,
    "solver-dispatch 缺少可恢复的关键证据: 求解结果。",
  );
  assert.match(status.errorBanner?.guidance ?? "", /补齐缺失 artifacts/);
});

void test("keeps the persisted runtime narrative for healthy running threads", () => {
  const status = getSubmarinePipelineStatus({
    threadError: null,
    threadIsLoading: true,
    isNewThread: false,
    hasMessages: true,
    hasDesignBrief: true,
    hasFinalReport: false,
    designBriefSummary: "已整理 baseline 条件",
    runtimeTaskSummary: "准备进入几何预检",
    runtimeStatus: "running",
    runtimeSummary: "OpenFOAM 求解正在运行，日志、结果与后处理证据会持续写回。",
  });

  assert.equal(status.tone, "streaming");
  assert.equal(status.agentLabel, "CFD runtime 运行中");
  assert.equal(status.runLabel, "运行中");
  assert.equal(status.outputStatus, "运行证据持续写入中");
  assert.equal(status.errorBanner, null);
  assert.equal(
    status.summaryText,
    "OpenFOAM 求解正在运行，日志、结果与后处理证据会持续写回。",
  );
});

void test("surfaces completed scientific gate blockers instead of looking fully ready", () => {
  const status = getSubmarinePipelineStatus({
    threadError: null,
    threadIsLoading: false,
    isNewThread: false,
    hasMessages: true,
    hasDesignBrief: true,
    hasFinalReport: true,
    designBriefSummary: "baseline 已确认",
    runtimeTaskSummary: "结果整理完成",
    runtimeStatus: "completed",
    runtimeSummary: null,
    scientificGateStatus: "blocked",
    allowedClaimLevel: "delivery_only",
  });

  assert.equal(status.tone, "error");
  assert.equal(status.runLabel, "科学受阻");
  assert.equal(status.outputStatus, "结果已完成，但科研声明已阻塞");
  assert.match(status.summaryText, /仅交付原始结果/);
  assert.equal(status.errorBanner?.title, "Scientific Gate Blocked");
});

void test("labels completed runtimes as awaiting scientific evidence when SCI-01 is incomplete", () => {
  const status = getSubmarinePipelineStatus({
    threadError: null,
    threadIsLoading: false,
    isNewThread: false,
    hasMessages: true,
    hasDesignBrief: true,
    hasFinalReport: false,
    designBriefSummary: "baseline 已确认",
    runtimeTaskSummary: "solver-dispatch 已完成",
    runtimeStatus: "completed",
    runtimeSummary: null,
    scientificVerificationStatus: "needs_more_verification",
  });

  assert.equal(status.tone, "ready");
  assert.equal(status.runLabel, "待补科学证据");
  assert.equal(status.outputStatus, "求解已完成，仍需补齐科学验证");
  assert.match(status.summaryText, /SCI-01/);
  assert.equal(status.errorBanner, null);
});
