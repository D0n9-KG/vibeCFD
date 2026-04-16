import assert from "node:assert/strict";
import test from "node:test";

const { localizeWorkspaceDisplayText } = await import(
  new URL("./workspace-display.ts", import.meta.url).href,
);

void test("localizeWorkspaceDisplayText rewrites rerun guidance, study ids, and virtual paths from the recovered thread", () => {
  const localized = localizeWorkspaceDisplayText(
    "Execute scientific verification studies / Run the planned scientific study variants and regenerate the missing verification artifacts for domain_sensitivity, time_step_sensitivity. / evidence artifact /mnt/user-data/outputs/submarine/solver-dispatch/suboff_solid/verification-mesh-independence.json exists, but its verification status is missing or unsupported. / plan-only / preflight_then_execute / /mnt/user-data/uploads/suboff_solid.stl",
  );

  assert.doesNotMatch(
    localized,
    /Execute scientific verification studies|Run the planned|verification artifacts|verification status is missing or unsupported|domain_sensitivity|time_step_sensitivity|plan-only|preflight_then_execute|\/mnt\/user-data/i,
  );
  assert.match(localized, /suboff_solid\.stl/);
  assert.match(localized, /verification-mesh-independence\.json/);
});

void test("localizeWorkspaceDisplayText rewrites lingering skill-studio decision copy into user-facing Chinese", () => {
  const localized = localizeWorkspaceDisplayText(
    "deliver / review / rerun / final report / scientific verification / explicit",
  );

  assert.doesNotMatch(
    localized,
    /deliver \/ review \/ rerun|final report|scientific verification|\bexplicit\b/i,
  );
  assert.match(localized, /交付 \/ 复核 \/ 重算/);
  assert.match(localized, /最终报告/);
  assert.match(localized, /科学验证/);
  assert.match(localized, /显式挂载/);
});

void test("localizeWorkspaceDisplayText rewrites standalone decision verbs and raw skill-studio filenames in chat copy", () => {
  const localized = localizeWorkspaceDisplayText(
    "规则：残差超阈值不能 deliver、缺少验证证据只能 review；我已经把完整产物挂出来了，包括：SKILL.md、validation-report.json。",
  );

  assert.doesNotMatch(localized, /\bdeliver\b|\breview\b|SKILL\.md|validation-report\.json/i);
  assert.match(localized, /交付/);
  assert.match(localized, /复核/);
  assert.match(localized, /技能说明文档/);
  assert.match(localized, /技能校验报告 JSON/);
});

void test("localizeWorkspaceDisplayText rewrites remaining skill-studio tool, remediation, and slug-heavy summary copy", () => {
  const localized = localizeWorkspaceDisplayText(
    "使用 “submarine_skill_studio” 工具。请创建技能 submarine-delivery-guard-20260415a。已创建技能 submarine-delivery-guard-20260415a。最终打包文件 submarine-delivery-guard-20260415a.skill。报告完整但 remediation 未关闭。skill-草稿.json",
  );

  assert.doesNotMatch(
    localized,
    /submarine_skill_studio|submarine-delivery-guard-20260415a|\.skill\b|remediation|skill-草稿\.json/i,
  );
  assert.match(localized, /技能工作台生成/);
  assert.match(localized, /请创建技能 当前技能/);
  assert.match(localized, /已创建技能 当前技能/);
  assert.match(localized, /最终打包文件 当前技能安装包/);
  assert.match(localized, /修正事项/);
  assert.match(localized, /技能草稿 JSON/);
});

void test("localizeWorkspaceDisplayText rewrites mixed scientific followup wording inside older submarine history copy", () => {
  const localized = localizeWorkspaceDisplayText(
    "同时系统还生成了 scientific 修正事项 / 跟进 相关交接产物。",
  );

  assert.doesNotMatch(localized, /\bscientific\b/i);
  assert.match(localized, /科研修正事项 \/ 跟进/);
});

void test("localizeWorkspaceDisplayText rewrites code-wrapped current skill slug and package filename in Skill Studio history", () => {
  const localized = localizeWorkspaceDisplayText(
    "已创建技能 `submarine-delivery-guard-20260415a`，并完成首轮验证，当前状态是 `ready_for_review`。最终打包文件 `submarine-delivery-guard-20260415a.skill`。",
  );

  assert.doesNotMatch(
    localized,
    /submarine-delivery-guard-20260415a|`[^`]*\.skill`|\.skill\b/i,
  );
  assert.match(localized, /已创建技能 当前技能/);
  assert.match(localized, /当前技能安装包/);
  assert.match(localized, /待审阅/);
});

void test("localizeWorkspaceDisplayText rewrites full scientific remediation and follow-up phrases before generic fallback terms", () => {
  const localized = localizeWorkspaceDisplayText(
    "同时系统还生成了 scientific remediation / follow-up 相关交接产物。继续做 scientific remediation handoff / follow-up。",
  );

  assert.doesNotMatch(localized, /\bscientific\b|\bremediation\b|\bfollow-up\b/i);
  assert.match(localized, /科研修正交接 \/ 科研跟进/);
  assert.match(localized, /科研修正交接说明 \/ 科研跟进/);
});

void test("localizeWorkspaceDisplayText keeps remediation handoff fully localized inside Skill Studio workflow summaries", () => {
  const localized = localizeWorkspaceDisplayText(
    "工作流：检查 `final report`、`scientific verification`、`remediation handoff`。",
  );

  assert.doesNotMatch(localized, /\bremediation handoff\b|修正事项 handoff/i);
  assert.match(localized, /修正交接说明/);
});
