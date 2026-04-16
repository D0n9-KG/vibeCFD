import assert from "node:assert/strict";
import test from "node:test";

const utils = await import(new URL("./utils.ts", import.meta.url).href);

void test("buildProgressPreviewFromMessage strips uploaded file scaffolding when user text is present", () => {
  const message = {
    type: "human",
    content: [
      "<uploaded_files>",
      "The following files were uploaded in this message:",
      "",
      "- suboff_solid.stl (1677721)",
      "  Path: /mnt/user-data/uploads/suboff_solid.stl",
      "</uploaded_files>",
      "",
      "请先做几何预检并给出推荐工况。",
    ].join("\n"),
  };

  assert.equal(
    utils.buildProgressPreviewFromMessage(message),
    "请先做几何预检并给出推荐工况。",
  );
});

void test("buildProgressPreviewFromMessage falls back to a friendly upload summary when only files were attached", () => {
  const message = {
    type: "human",
    content: [
      "<uploaded_files>",
      "The following files were uploaded in this message:",
      "",
      "- suboff_solid.stl (1677721)",
      "  Path: /mnt/user-data/uploads/suboff_solid.stl",
      "</uploaded_files>",
    ].join("\n"),
  };

  assert.match(
    utils.buildProgressPreviewFromMessage(message),
    /suboff_solid\.stl/,
  );
  assert.doesNotMatch(
    utils.buildProgressPreviewFromMessage(message),
    /<uploaded_files>|Path:/,
  );
});

void test("buildProgressPreviewFromMessage localizes system-generated workflow prompts before they reach the workbench header", () => {
  const message = {
    type: "human",
    content:
      "刚才那次 scientific follow-up 因服务重连中断，请忽略中断中的结果。现在请基于 remediation handoff 补齐 solver metrics，并在 scientific study variants 真正完成后再刷新最终报告；final residual threshold 与 Supervisor 结论也要同步更新。",
  };

  const preview = utils.buildProgressPreviewFromMessage(message, 400) ?? "";

  assert.doesNotMatch(
    preview,
    /scientific follow-up|remediation handoff|solver metrics|scientific study variants|final residual threshold|Supervisor/i,
  );
  assert.match(preview, /科研跟进/);
  assert.match(preview, /修正交接说明/);
  assert.match(preview, /求解指标/);
  assert.match(preview, /科学研究变体/);
  assert.match(preview, /最终残差阈值/);
  assert.match(preview, /主管代理/);
});

void test("buildProgressPreviewFromMessage still localizes raw runtime labels that should never reach frontend-only users", () => {
  const message = {
    type: "human",
    content:
      "请检查 result-reporting 阶段是否还能继续 solver-dispatch，并确认 scientific-verification 与 scientific-followup 的状态同步。",
  };

  const preview = utils.buildProgressPreviewFromMessage(message, 400) ?? "";

  assert.doesNotMatch(
    preview,
    /result-reporting|solver-dispatch|scientific-verification|scientific-followup/i,
  );
  assert.match(preview, /结果整理阶段/);
  assert.match(preview, /求解派发阶段/);
  assert.match(preview, /科学验证/);
  assert.match(preview, /科研跟进/);
});

void test("normalizeMessageDisplayText does not rewrite ordinary user-authored human copy that only mentions generic english nouns", () => {
  const content =
    "请保留 baseline case 的 artifacts 供我稍后复核 Supervisor 结论，但先不要自动改写我的原话。";

  assert.equal(
    utils.normalizeMessageDisplayText({
      type: "human",
      content,
    }),
    content,
  );
});

void test("normalizeMessageDisplayText still localizes standalone internal labels for frontend-only users", () => {
  assert.equal(
    utils.normalizeMessageDisplayText({
      type: "human",
      content: "draft-only",
    }),
    "仅草稿",
  );
  assert.equal(
    utils.normalizeMessageDisplayText({
      type: "human",
      content: "workflow",
    }),
    "工作流",
  );
  assert.equal(
    utils.normalizeMessageDisplayText({
      type: "human",
      content: "Submarine Result Acceptance Draft",
    }),
    "潜艇结果验收草稿",
  );
  assert.equal(
    utils.normalizeMessageDisplayText({
      type: "human",
      content: "solver-dispatch",
    }),
    "求解派发阶段",
  );
});

void test("normalizeMessageDisplayText strips uploaded-files scaffolding from non-human protocol messages", () => {
  const content = [
    "<uploaded_files>",
    "The following files were uploaded in this message:",
    "",
    "- suboff_solid.stl (1638084)",
    "  Path: /mnt/user-data/uploads/suboff_solid.stl",
    "</uploaded_files>",
    "",
    "请继续查看附件。",
  ].join("\n");

  assert.equal(
    utils.normalizeMessageDisplayText({
      type: "ai",
      content,
    }),
    "请继续查看附件。",
  );
});
