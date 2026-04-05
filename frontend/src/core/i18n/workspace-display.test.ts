import assert from "node:assert/strict";
import test from "node:test";

const { localizeWorkspaceDisplayText } = await import(
  new URL("./workspace-display.ts", import.meta.url).href,
);

void test("localizeWorkspaceDisplayText rewrites common skill-studio display strings", () => {
  const localized = localizeWorkspaceDisplayText(
    "submarine result acceptance / submarine-result-acceptance / ready_for_review / accept revise reject / workflow / skill-creator / writing-skills",
  );

  assert.equal(
    localized,
    "潜艇结果验收 / 潜艇结果验收 / 待审阅 / 接受 修订 拒绝 / 工作流 / 技能创建 / 写作技能",
  );
});

void test("localizeWorkspaceDisplayText rewrites standalone brief phrasing in assistant content", () => {
  const localized = localizeWorkspaceDisplayText(
    "当前 brief 仍有 3 个待确认项会阻塞 submarine_geometry_check",
  );

  assert.equal(
    localized,
    "当前 简报 仍有 3 个待确认项会阻塞 submarine_geometry_check",
  );
});

void test("localizeWorkspaceDisplayText rewrites common English workspace nouns in historical thread copy", () => {
  const localized = localizeWorkspaceDisplayText(
    "Submarine 验收 Skill 草稿 / requested outputs / pre-solver checklist / Artifacts / outputs / checklist",
  );

  assert.equal(
    localized,
    "潜艇 验收 技能 草稿 / 输出范围 / 求解前检查清单 / 产物 / 输出项 / 检查清单",
  );
});

void test("localizeWorkspaceDisplayText rewrites submarine runtime clarification phrases", () => {
  const localized = localizeWorkspaceDisplayText(
    "recommended baseline case/template mapping / 基线 case/template 映射建议 / needs clarification / brief stays in draft / Should requested outputs stay limited to resistance baseline preparation?",
  );

  assert.equal(
    localized,
    "推荐基线案例/模板映射 / 基线案例/模板映射建议 / 待澄清 / 简报保持草稿状态 / 输出范围是否只保留阻力基线准备？",
  );
});

void test("localizeWorkspaceDisplayText rewrites runtime ids and standalone resistance wording", () => {
  const localized = localizeWorkspaceDisplayText(
    "claude-code-supervisor / darpa_suboff_bare_hull_resistance / resistance baseline",
  );

  assert.equal(
    localized,
    "Claude Code 主管代理 / DARPA SUBOFF 裸艇阻力基线 / 阻力基线",
  );
});

void test("localizeWorkspaceDisplayText rewrites submarine geometry skill loading hints", () => {
  const localized = localizeWorkspaceDisplayText(
    "load submarine geometry skill / `/mnt/skills/public/submarine-geometry-check/SKILL.md`",
  );

  assert.equal(
    localized,
    "加载潜艇几何预检技能 / 潜艇几何预检技能",
  );
});

void test("localizeWorkspaceDisplayText rewrites artifact and case wording in submarine workbench copy", () => {
  const localized = localizeWorkspaceDisplayText(
    "生成可审计的预检 artifact / 推荐 基线 case 映射 / recommended baseline case mapping",
  );

  assert.equal(
    localized,
    "生成可审计的预检产物 / 推荐基线案例映射 / 推荐基线案例映射",
  );
});

void test("localizeWorkspaceDisplayText rewrites remaining brief and baseline fallback copy", () => {
  const localized = localizeWorkspaceDisplayText(
    "等待建立研究 brief / 补充目标与 baseline / brief 已确认，待生成数值证据",
  );

  assert.equal(
    localized,
    "等待建立研究 简报 / 补充目标与 基线 / 简报 已确认，待生成数值证据",
  );
});

void test("localizeWorkspaceDisplayText rewrites mixed workflow terms in historical submarine messages", () => {
  const localized = localizeWorkspaceDisplayText(
    "geometry preflight / artifact-backed / 产物-backed",
  );

  assert.equal(localized, "几何预检 / 有产物支撑的 / 有产物支撑的");
});

void test("localizeWorkspaceDisplayText rewrites draft-only fallback labels cleanly", () => {
  const localized = localizeWorkspaceDisplayText("draft-only / draft only");

  assert.equal(localized, "仅草稿 / 仅草稿");
});

void test("localizeWorkspaceDisplayText sanitizes trailing quotes and repeated punctuation", () => {
  const localized = localizeWorkspaceDisplayText(
    '已整理 CFD 设计简报：当前阶段仅做几何预检与准备，不启动 solver。。"',
  );

  assert.equal(
    localized,
    "已整理 CFD 设计简报：当前阶段仅做几何预检与准备，不启动求解器。",
  );
});
