import assert from "node:assert/strict";
import test from "node:test";

const { localizeWorkspaceDisplayText, localizeWorkspaceToolName } = await import(
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
    "recommended baseline case/template mapping / baseline case/template mapping建议 / needs clarification / brief stays in draft / Should requested outputs stay limited to resistance baseline preparation?",
  );

  assert.equal(
    localized,
    "推荐基线案例/模板映射 / 基线 案例/模板 mapping建议 / 待澄清 / 简报保持草稿状态 / 输出范围是否只保留阻力基线准备？",
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

void test("localizeWorkspaceDisplayText rewrites capitalized bare-hull baseline titles cleanly", () => {
  const localized = localizeWorkspaceDisplayText(
    "DARPA SUBOFF Bare Hull Resistance Baseline",
  );

  assert.equal(localized, "DARPA SUBOFF 裸艇阻力基线");
});

void test("localizeWorkspaceDisplayText rewrites submarine geometry skill loading hints", () => {
  const localized = localizeWorkspaceDisplayText(
    "load submarine geometry skill / /mnt/skills/public/submarine-geometry-check/SKILL.md",
  );

  assert.equal(localized, "加载潜艇几何预检技能 / 潜艇几何预检技能");
});

void test("localizeWorkspaceDisplayText rewrites submarine orchestrator skill loading hints", () => {
  const localized = localizeWorkspaceDisplayText(
    "load submarine orchestrator skill / /mnt/skills/public/submarine-orchestrator/SKILL.md",
  );

  assert.equal(localized, "加载潜艇编排技能 / 潜艇编排技能");
});

void test("localizeWorkspaceDisplayText rewrites artifact wording in submarine workbench copy", () => {
  const localized = localizeWorkspaceDisplayText(
    "生成可审计的预检 artifact / geometry preflight / artifact-backed / 产物-backed",
  );

  assert.equal(
    localized,
    "生成可审计的预检产物 / 几何预检 / 有产物支撑的 / 有产物支撑的",
  );
});

void test("localizeWorkspaceDisplayText rewrites draft-only fallback labels cleanly", () => {
  const localized = localizeWorkspaceDisplayText("draft-only / draft only");

  assert.equal(localized, "仅草稿 / 仅草稿");
});

void test("localizeWorkspaceDisplayText sanitizes trailing quotes and repeated punctuation", () => {
  const localized = localizeWorkspaceDisplayText(
    "已整理 CFD 设计简报：当前阶段仅做几何预检与准备，不启动 solver。。",
  );

  assert.equal(
    localized,
    "已整理 CFD 设计简报：当前阶段仅做几何预检与准备，不启动求解器。",
  );
});

void test("localizeWorkspaceDisplayText softens remaining DeerFlow-flavored negotiation copy", () => {
  const localized = localizeWorkspaceDisplayText(
    "提示：我已按你的要求先写入了 draft brief，并保持不启动求解。但当前 DeerFlow 的 几何预检 仍要求先在对话中确认这次几何预检所绑定的演示性基线工况，然后才允许继续生成 有产物支撑的 预检结果。",
  );

  assert.equal(
    localized,
    "提示：我已按你的要求先写入了 草稿简报，并保持不启动求解。但当前的几何预检仍要求先在对话中确认这次几何预检所绑定的演示性基线工况，然后才允许继续生成 有产物支撑的预检结果。",
  );
});

void test("localizeWorkspaceToolName rewrites submarine execution tool ids for user-facing workbench copy", () => {
  assert.equal(localizeWorkspaceToolName("submarine_solver_dispatch"), "求解派发");
  assert.equal(localizeWorkspaceToolName("submarine_result_report"), "结果整理");
  assert.equal(localizeWorkspaceToolName("submarine_scientific_followup"), "科研跟进");
  assert.equal(localizeWorkspaceToolName("spawn_agent"), "子代理协作");
});

void test("localizeWorkspaceDisplayText rewrites common remediation action titles", () => {
  const localized = localizeWorkspaceDisplayText(
    "Attach validation reference / Approve rerun / Refine mesh / Refine mesh near hull wake",
  );

  assert.equal(
    localized,
    "补充验证参考 / 确认重跑 / 细化网格 / 细化艇体尾流附近网格",
  );
});

void test("localizeWorkspaceDisplayText rewrites recovered-thread runtime and report slugs that should not reach frontend-only users", () => {
  const localized = localizeWorkspaceDisplayText(
    "submarine-result-acceptance-visible / scientific-verification / result-reporting / darpa_suboff_bare_hull_resistance",
  );

  assert.equal(
    localized,
    "潜艇结果验收 / 科学验证 / 结果整理阶段 / DARPA SUBOFF 裸艇阻力基线",
  );
});

void test("localizeWorkspaceDisplayText rewrites common recovered-thread follow-up and study-blocker phrases", () => {
  const localized = localizeWorkspaceDisplayText(
    "scientific follow-up / scientific-followup / solver-dispatch / Scientific-study variant execution is blocked for: fine. / Mesh Independence shows Cd spread above tolerance 0.0200. / Domain Sensitivity shows Cd spread above tolerance 0.0200.",
  );

  assert.equal(
    localized,
    "科研跟进 / 科研跟进 / 求解派发阶段 / 科学研究变体执行在以下分支受阻： fine. / 网格无关性研究显示 Cd 超出容差范围 0.0200. / 计算域敏感性研究显示 Cd 超出容差范围 0.0200.",
  );
});

void test("localizeWorkspaceDisplayText rewrites remaining mixed workflow terms that still surfaced on the recovered page", () => {
  const localized = localizeWorkspaceDisplayText(
    "刚才那次 scientific follow-up 因服务重连中断，请忽略中断中的结果。请基于 scientific remediation handoff 补齐 solver metrics，并在 scientific study variants 真正完成后再刷新最终报告；final residual threshold、claim level、clean STL、artifacts 与 Supervisor 结论也要同步更新。本次 run 未导出尾流速度切片 产物，并把 mesh/domain/time-step 研究结论同步到主画布。",
  );

  assert.doesNotMatch(
    localized,
    /scientific follow-up|scientific remediation handoff|solver metrics|scientific study variants|final residual threshold|claim level|clean STL|artifacts|Supervisor|\brun\b|mesh\/domain\/time-step/i,
  );
  assert.match(localized, /科研跟进/);
  assert.match(localized, /科研修正交接说明/);
  assert.match(localized, /求解指标/);
  assert.match(localized, /科学研究变体/);
  assert.match(localized, /最终残差阈值/);
  assert.match(localized, /结论口径/);
  assert.match(localized, /清理后的 STL/);
  assert.match(localized, /产物/);
  assert.match(localized, /主管代理/);
  assert.match(localized, /本次运行未导出/);
  assert.match(localized, /网格\/计算域\/时间步长/);
});

void test("localizeWorkspaceDisplayText does not rewrite ordinary english prose that only happens to contain explicit or review", () => {
  const sample =
    "The explicit result still needs peer review before publication.";

  assert.equal(localizeWorkspaceDisplayText(sample), sample);
});
