import assert from "node:assert/strict";
import test from "node:test";

const { getSubmarinePipelineStatus } = await import(
  new URL("./submarine-pipeline-status.ts", import.meta.url).href
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
  assert.match(status.errorBanner?.guidance ?? "", /当前研究状态未推进/);
  assert.match(status.summaryText, /当前研究状态未推进/);
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
  assert.match(status.errorBanner?.guidance ?? "", /LangGraph URL 配置/);
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

void test("keeps the existing research narrative when there is no thread error", () => {
  const status = getSubmarinePipelineStatus({
    threadError: null,
    threadIsLoading: true,
    isNewThread: false,
    hasMessages: true,
    hasDesignBrief: true,
    hasFinalReport: false,
    designBriefSummary: "已整理 baseline 条件",
    runtimeTaskSummary: "准备进入几何预检",
  });

  assert.equal(status.tone, "streaming");
  assert.equal(status.agentLabel, "主智能体运行中");
  assert.equal(status.runLabel, "运行中");
  assert.equal(status.outputStatus, "已形成 design brief");
  assert.equal(status.errorBanner, null);
  assert.equal(status.summaryText, "已整理 baseline 条件");
});
