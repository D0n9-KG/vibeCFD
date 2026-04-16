const DISPLAY_TEXT_REPLACEMENTS: ReadonlyArray<readonly [string, string]> = [
  ["Submarine Result Acceptance Draft", "潜艇结果验收草稿"],
  ["submarine-result-acceptance-visible", "潜艇结果验收"],
  ["submarine-result-acceptance", "潜艇结果验收"],
  ["submarine result acceptance", "潜艇结果验收"],
  ["STL File Upload", "STL \u6587\u4ef6\u4e0a\u4f20"],
  ["draft-only", "仅草稿"],
  ["draft only", "仅草稿"],
  ["plan-only", "\u4ec5\u4fdd\u7559\u65b9\u6848"],
  ["plan_only", "\u4ec5\u4fdd\u7559\u65b9\u6848"],
  ["preflight_then_execute", "\u9884\u68c0\u540e\u6267\u884c"],
  ["潜艇 Skill Studio 演示", "潜艇技能工作台演示"],
  ["OpenFOAM CFD for STL Model", "STL 模型 OpenFOAM CFD 分析"],
  ["STL CFD Drag Coefficient Analysis", "STL CFD 阻力系数分析"],
  ["DeerFlow Skill 能力说明", "DeerFlow 技能能力说明"],
  ["load relevant submarine skill", "加载潜艇领域技能"],
  ["load submarine orchestrator skill", "加载潜艇编排技能"],
  ["load geometry check skill", "加载几何预检技能"],
  ["load submarine geometry skill", "加载潜艇几何预检技能"],
  ["geometry preflight", "几何预检"],
  ["`/mnt/skills/public/submarine-orchestrator/SKILL.md`", "潜艇编排技能"],
  ["/mnt/skills/public/submarine-orchestrator/SKILL.md", "潜艇编排技能"],
  ["`/mnt/skills/public/submarine-geometry-check/SKILL.md`", "潜艇几何预检技能"],
  ["/mnt/skills/public/submarine-geometry-check/SKILL.md", "潜艇几何预检技能"],
  ["submarine-orchestrator", "潜艇编排技能"],
  ["submarine-geometry-check", "潜艇几何预检技能"],
  ["submarine-solver-dispatch", "求解派发技能"],
  ["submarine-report", "结果整理技能"],
  ["Update to-do list", "更新待办列表"],
  ["Update To-do list", "更新待办列表"],
  ["Bare Hull Resistance Baseline", "裸艇阻力基线"],
  ["bare hull resistance baseline", "裸艇阻力基线"],
  ["bare hull resistance", "裸艇阻力"],
  ["design brief", "设计简报"],
  ["patch/边界条件一致性", "边界 patch 与边界条件一致性"],
  ["accept / revise / reject", "接受 / 修订 / 拒绝"],
  ["DeerFlow Skill", "DeerFlow 技能"],
  ["Skill Studio", "技能工作台"],
  [
    "Should requested outputs stay limited to resistance baseline preparation?",
    "输出范围是否只保留阻力基线准备？",
  ],
  ["recommended baseline case/template mapping", "推荐基线案例/模板映射"],
  ["recommended baseline case mapping", "推荐基线案例映射"],
  ["推荐 baseline case/template 映射", "推荐基线案例/模板映射"],
  ["基线 case/template 映射建议", "基线案例/模板映射建议"],
  ["推荐 基线 case 映射", "推荐基线案例映射"],
  ["brief stays in draft", "简报保持草稿状态"],
  ["生成可审计的预检 artifact", "生成可审计的预检产物"],
  ["预检 artifact", "预检产物"],
  ["artifact-backed", "有产物支撑的"],
  ["产物-backed", "有产物支撑的"],
  ["draft brief", "草稿简报"],
  ["草稿 简报", "草稿简报"],
  ["当前 DeerFlow 的 几何预检", "当前的几何预检"],
  ["当前的几何预检 仍", "当前的几何预检仍"],
  ["有产物支撑的 预检结果", "有产物支撑的预检结果"],
  ["brief 保持 draft / 待确认状态", "简报保持草稿 / 待确认状态"],
  ["优先沿用 DARPA SUBOFF bare hull resistance baseline", "优先沿用 DARPA SUBOFF 裸艇阻力基线"],
  ["是否将 requested outputs 明确限定为阻力基线准备，不包含压力分布/尾流输出？", "是否将输出范围明确限定为阻力基线准备，不包含压力分布/尾流输出？"],
  ["是否需要把验收门槛写成可执行的 pre-solver checklist（patch/BC、checkMesh、结果表述边界）？", "是否需要把验收门槛写成可执行的求解前检查清单（patch/BC、checkMesh、结果表述边界）？"],
  ["当前 brief 仍有待确认条件，主智能体应先和用户协商补齐，再进入执行。", "当前简报仍有待确认条件，主智能体应先和用户协商补齐，再进入执行。"],
  ["needs clarification", "待澄清"],
  ["case/template", "案例/模板"],
  ["resistance baseline", "阻力基线"],
  ["requested outputs", "输出范围"],
  ["pre-solver checklist", "求解前检查清单"],
  ["不启动 solver", "不启动求解器"],
  ["交付 framing", "交付定稿口径"],
  ["forces 历史", "受力历史"],
  ["darpa_suboff_bare_hull_resistance", "DARPA SUBOFF 裸艇阻力基线"],
  ["[claude-code-supervisor]", "[Claude Code 主管代理]"],
  ["claude-code-supervisor", "Claude Code 主管代理"],
  ["Final residual threshold: observed ", "最终残差阈值：观测值 "],
  ["Mesh independence study: missing evidence artifacts ", "网格无关性研究：缺少证据产物 "],
  ["Force coefficient tail stability: need at least ", "力系数尾段稳定性：至少需要 "],
  [" samples in force coefficient history.", " 个力系数历史样本。"],
  ["Final residual threshold", "最终残差阈值"],
  ["Force coefficient tail stability", "力系数尾段稳定性"],
  ["Mesh independence study", "网格无关性研究"],
  ["Domain sensitivity study", "计算域敏感性研究"],
  ["Time-step sensitivity study", "时间步长敏感性研究"],
  ["max_final_residual", "最大最终残差"],
  ["force_coefficient_tail_stability", "力系数尾段稳定性"],
  ["artifact_presence", "产物齐备"],
  ["Geometry preflight", "几何预检"],
  ["Case library", "案例库"],
  ["Reference length", "参考长度"],
  ["Selected baseline case", "选定的基线案例"],
  ["Assumes the uploaded STL is already meter-scaled.", "假定当前上传的 STL 已经采用米制尺度。"],
  ["Claude Code Supervisor", "Claude Code 主管代理"],
  ["Artifacts", "产物"],
  ["artifacts", "产物"],
  ["artifact", "产物"],
  ["checklist", "检查清单"],
  ["workflow", "工作流"],
  ["To-do", "待办"],
  ["bare hull", "裸艇"],
  ["baseline", "基线"],
  ["ready_for_review", "待审阅"],
  ["ready_for_dry_run", "可试运行"],
  ["needs_revision", "需修订"],
  ["draft_only", "仅有草稿"],
  ["skill-creator", "技能创建"],
  ["writing-skills", "写作技能"],
  ["Attach validation reference", "补充验证参考"],
  ["Execute scientific verification studies", "\u6267\u884c\u79d1\u5b66\u9a8c\u8bc1\u7814\u7a76"],
  ["Approve rerun", "确认重跑"],
  ["Refine mesh near hull wake", "细化艇体尾流附近网格"],
  ["Refine mesh", "细化网格"],
  ["Updated the structured CFD design brief.", "已更新结构化 CFD 设计简报。"],
  ["scientific-verification", "科学验证"],
  ["result-reporting", "结果整理阶段"],
  ["solver-dispatch", "求解派发阶段"],
  ["scientific remediation handoff", "科研修正交接说明"],
  ["Scientific remediation handoff", "科研修正交接说明"],
  ["remediation handoff", "修正交接说明"],
  ["solver metrics", "求解指标"],
  ["Solver metrics are unavailable for this run.", "当前运行缺少求解指标。"],
  ["solver metrics are unavailable for this run.", "当前运行缺少求解指标。"],
  ["Residual summary is still unavailable for the current baseline run.", "当前基线运行仍缺少残差摘要。"],
  ["residual summary is still unavailable for the current baseline run.", "当前基线运行仍缺少残差摘要。"],
  ["Residual summary is still unavailable for the current 基线 run.", "当前基线运行仍缺少残差摘要。"],
  ["residual summary is still unavailable for the current 基线 run.", "当前基线运行仍缺少残差摘要。"],
  ["Solver still needs supervisor review.", "当前求解结果仍需主管复核。"],
  ["scientific study variants", "科学研究变体"],
  ["scientific-study variants", "\u79d1\u5b66\u7814\u7a76\u53d8\u4f53"],
  ["scientific study variant", "科学研究变体"],
  ["scientific-study variant", "\u79d1\u5b66\u7814\u7a76\u53d8\u4f53"],
  ["deliver / review / rerun", "交付 / 复核 / 重算"],
  ["deliver/review/rerun", "交付 / 复核 / 重算"],
  ["final report", "最终报告"],
  ["scientific verification", "科学验证"],
  ["scientific 修正事项 / 跟进", "科研修正事项 / 跟进"],
  ["SKILL.md", "技能说明文档"],
  ["validation-report.json / .md / .html", "技能校验报告 JSON / Markdown / HTML"],
  ["validation-report.json", "技能校验报告 JSON"],
  ["validation-report.md", "技能校验报告 Markdown"],
  ["validation-report.html", "技能校验报告 HTML"],
  ["Run the planned scientific study variants and regenerate the missing verification artifacts for ", "\u6267\u884c\u5df2\u89c4\u5212\u7684\u79d1\u5b66\u7814\u7a76\u53d8\u4f53\uff0c\u5e76\u8865\u9f50\u7f3a\u5931\u7684\u9a8c\u8bc1\u4ea7\u7269\uff1a"],
  ["Run the planned scientific-study variants and regenerate the missing verification artifacts for ", "\u6267\u884c\u5df2\u89c4\u5212\u7684\u79d1\u5b66\u7814\u7a76\u53d8\u4f53\uff0c\u5e76\u8865\u9f50\u7f3a\u5931\u7684\u9a8c\u8bc1\u4ea7\u7269\uff1a"],
  ["verification artifacts", "\u9a8c\u8bc1\u4ea7\u7269"],
  ["verification artifact", "\u9a8c\u8bc1\u4ea7\u7269"],
  ["evidence artifact ", "\u8bc1\u636e\u4ea7\u7269 "],
  ["exists, but its ", "\u5df2\u5b58\u5728\uff0c\u4f46\u5176"],
  ["verification status is missing or unsupported.", "\u9a8c\u8bc1\u72b6\u6001\u7f3a\u5931\u6216\u6682\u4e0d\u652f\u6301\u3002"],
  ["Some scientific-study variants are missing solver results:", "\u90e8\u5206\u79d1\u5b66\u7814\u7a76\u53d8\u4f53\u7f3a\u5c11\u6c42\u89e3\u7ed3\u679c\uff1a"],
  ["Some scientific study variants are missing solver results:", "\u90e8\u5206\u79d1\u5b66\u7814\u7a76\u53d8\u4f53\u7f3a\u5c11\u6c42\u89e3\u7ed3\u679c\uff1a"],
  ["domain_sensitivity", "\u8ba1\u7b97\u57df\u654f\u611f\u6027\u7814\u7a76"],
  ["time_step_sensitivity", "\u65f6\u95f4\u6b65\u957f\u654f\u611f\u6027\u7814\u7a76"],
  ["mesh_independence", "\u7f51\u683c\u65e0\u5173\u6027\u7814\u7a76"],
  ["Run the planned ?????? and regenerate the missing verification ?? for ", "\u6267\u884c\u5df2\u89c4\u5212\u7684\u79d1\u5b66\u7814\u7a76\u53d8\u4f53\uff0c\u5e76\u8865\u9f50\u7f3a\u5931\u7684\u9a8c\u8bc1\u4ea7\u7269\uff1a"],
  ["Run the planned ?????? and regenerate the missing ???? for ", "\u6267\u884c\u5df2\u89c4\u5212\u7684\u79d1\u5b66\u7814\u7a76\u53d8\u4f53\uff0c\u5e76\u8865\u9f50\u7f3a\u5931\u7684\u9a8c\u8bc1\u4ea7\u7269\uff1a"],
  ["Some ?????? are missing solver results:", "\u90e8\u5206\u79d1\u5b66\u7814\u7a76\u53d8\u4f53\u7f3a\u5c11\u6c42\u89e3\u7ed3\u679c\uff1a"],
  ["verification ??", "\u9a8c\u8bc1\u4ea7\u7269"],
  ["evidence ?? ", "\u8bc1\u636e\u4ea7\u7269 "],
  ["scientific follow-up", "科研跟进"],
  ["scientific-followup", "科研跟进"],
  ["final residual threshold", "最终残差阈值"],
  ["claim level", "结论口径"],
  ["clean STL", "清理后的 STL"],
  ["Supervisor", "主管代理"],
  ["provenance", "溯源"],
  ["dispatch-summary.md", "求解派发摘要"],
  ["dispatch-summary.html", "求解派发摘要 HTML"],
  ["solver-results.md", "结果摘要"],
  ["solver-results.json", "结果数据 JSON"],
  ["final-report.md", "最终报告"],
  ["final-report.html", "最终报告 HTML"],
  ["final-report.json", "最终报告 JSON"],
  ["scientific-remediation-plan.json", "科研补救计划 JSON"],
  ["scientific-remediation-handoff.json", "科研补救交接 JSON"],
  ["provenance-manifest.json", "溯源清单 JSON"],
  ["本次 run 未导出", "本次运行未导出"],
  ["mesh/domain/time-step", "网格/计算域/时间步长"],
  ["Scientific-study variant execution is blocked for:", "科学研究变体执行在以下分支受阻："],
  ["Mesh Independence shows Cd spread above tolerance", "网格无关性研究显示 Cd 超出容差范围"],
  ["Domain Sensitivity shows Cd spread above tolerance", "计算域敏感性研究显示 Cd 超出容差范围"],
];

const DISPLAY_TEXT_REGEX_REPLACEMENTS: ReadonlyArray<
  readonly [RegExp, string]
> = [
  [/\baccept\b/g, "\u63a5\u53d7"],
  [/\bbrief\b/gi, "\u7b80\u62a5"],
  [/\bdraft\b/gi, "\u8349\u7a3f"],
  [/\boutputs\b/gi, "\u8f93\u51fa\u9879"],
  [/\bsteps\b/gi, "\u6b65"],
  [/\bpreflight\b/gi, "\u9884\u68c0"],
  [/\bexecution\b/gi, "\u6267\u884c"],
  [/\bresistance\b/gi, "\u963b\u529b"],
  [/\brevise\b/g, "\u4fee\u8ba2"],
  [/\breject\b/g, "\u62d2\u7edd"],
  [/\bSkill\b/g, "\u6280\u80fd"],
  [/\bSubmarine\b/g, "\u6f5c\u8247"],
];

const TOOL_NAME_LABELS: Readonly<Record<string, string>> = {
  submarine_design_brief: "潜艇设计简报",
  submarine_design_brief_tool: "潜艇设计简报",
  submarine_geometry_check: "潜艇几何预检",
  submarine_geometry_check_tool: "潜艇几何预检",
  submarine_solver_dispatch: "求解派发",
  submarine_solver_dispatch_tool: "求解派发",
  submarine_result_report: "结果整理",
  submarine_result_report_tool: "结果整理",
  submarine_scientific_followup: "科研跟进",
  submarine_scientific_followup_tool: "科研跟进",
  spawn_agent: "子代理协作",
  manual_only: "人工处理",
};

function replaceAll(source: string, search: string, replacement: string) {
  return source.includes(search) ? source.split(search).join(replacement) : source;
}

function collapseVirtualUserDataPaths(text: string) {
  return text.replace(
    /\/mnt\/user-data\/[^\s"'`\)\]??????]+/g,
    (match) => {
      const basename = match.split("/").filter(Boolean).at(-1);
      return basename && basename.length > 0 ? basename : match;
    },
  );
}

function repairRecoveredCopyLeaks(text: string) {
  return text
    .replace(/Execute scientific verification studies/gi, "\u6267\u884c\u79d1\u5b66\u9a8c\u8bc1\u7814\u7a76")
    .replace(/Run the planned .*? and regenerate the missing .*? for /gi, "\u6267\u884c\u5df2\u89c4\u5212\u7684\u79d1\u5b66\u7814\u7a76\u53d8\u4f53\uff0c\u5e76\u8865\u9f50\u7f3a\u5931\u7684\u9a8c\u8bc1\u4ea7\u7269\uff1a")
    .replace(/Some .*? are missing solver results:/gi, "\u90e8\u5206\u79d1\u5b66\u7814\u7a76\u53d8\u4f53\u7f3a\u5c11\u6c42\u89e3\u7ed3\u679c\uff1a")
    .replace(/verification status is missing or unsupported\./gi, "\u9a8c\u8bc1\u72b6\u6001\u7f3a\u5931\u6216\u6682\u4e0d\u652f\u6301\u3002")
    .replace(/verification artifacts?/gi, "\u9a8c\u8bc1\u4ea7\u7269")
    .replace(/evidence artifact /gi, "\u8bc1\u636e\u4ea7\u7269 ")
    .replace(/exists, but its /gi, "\u5df2\u5b58\u5728\uff0c\u4f46\u5176")
    .replace(/plan[-_]only/gi, "\u4ec5\u4fdd\u7559\u65b9\u6848")
    .replace(/preflight_then_execute/gi, "\u9884\u68c0\u540e\u6267\u884c")
    .replace(/domain_sensitivity/gi, "\u8ba1\u7b97\u57df\u654f\u611f\u6027\u7814\u7a76")
    .replace(/time_step_sensitivity/gi, "\u65f6\u95f4\u6b65\u957f\u654f\u611f\u6027\u7814\u7a76")
    .replace(/mesh_independence/gi, "\u7f51\u683c\u65e0\u5173\u6027\u7814\u7a76")
    .replace(/evidence \u4ea7\u7269/gi, "\u8bc1\u636e\u4ea7\u7269")
    .replace(/dispatch-summary\.md/gi, "求解派发摘要")
    .replace(/dispatch-summary\.html/gi, "求解派发摘要 HTML")
    .replace(/solver-results\.md/gi, "结果摘要")
    .replace(/solver-results\.json/gi, "结果数据 JSON")
    .replace(/final-report\.md/gi, "最终报告")
    .replace(/final-report\.html/gi, "最终报告 HTML")
    .replace(/final-report\.json/gi, "最终报告 JSON")
    .replace(/scientific-remediation-plan\.json/gi, "科研补救计划 JSON")
    .replace(/scientific-remediation-handoff\.json/gi, "科研补救交接 JSON")
    .replace(/provenance-manifest\.json/gi, "溯源清单 JSON")
    .replace(/scientific follow-up/gi, "科研跟进")
    .replace(/scientific-followup/gi, "科研跟进")
    .replace(/scientific remediation handoff/gi, "科研修正交接说明")
    .replace(/remediation handoff/gi, "修正交接说明")
    .replace(/study-manifest/gi, "\u7814\u7a76\u6e05\u5355\u4ea7\u7269")
    .replace(/solver-results/gi, "\u6c42\u89e3\u7ed3\u679c\u4ea7\u7269")
    .replace(/skill-lifecycle\.json/gi, "技能生命周期 JSON")
    .replace(/dry-run-evidence\.json/gi, "试跑证据 JSON")
    .replace(/skill-package\.json/gi, "技能打包清单 JSON")
    .replace(/test-matrix\.json\s*\/\s*\.md/gi, "测试矩阵 JSON / Markdown")
    .replace(/publish-readiness\.json\s*\/\s*\.md/gi, "发布准备 JSON / Markdown")
    .replace(/test-matrix\.json/gi, "测试矩阵 JSON")
    .replace(/test-matrix\.md/gi, "测试矩阵 Markdown")
    .replace(/publish-readiness\.json/gi, "发布准备 JSON")
    .replace(/publish-readiness\.md/gi, "发布准备 Markdown")
    .replace(/submarine_skill_studio/gi, "技能工作台生成")
    .replace(/请创建技能\s+`?[a-z0-9-]+`?/gi, "请创建技能 当前技能")
    .replace(/已创建技能\s+`?[a-z0-9-]+`?/gi, "已创建技能 当前技能")
    .replace(/最终打包文件\s+`?[a-z0-9-]+\.skill`?/gi, "最终打包文件 当前技能安装包")
    .replace(/不能\s+deliver/gi, "不能 交付")
    .replace(/只能\s+review/gi, "只能 复核")
    .replace(/用于快速\s+review/gi, "用于快速 复核")
    .replace(/快速\s+review/gi, "快速 复核")
    .replace(/^explicit$/gi, "显式挂载")
    .replace(/\/\s*explicit(?=\s*(?:\/|$))/gi, "/ 显式挂载")
    .replace(/scientific remediation handoff \/ follow-up/gi, "科研修正交接说明 / 科研跟进")
    .replace(/科研修正交接说明 \/ follow-up/gi, "科研修正交接说明 / 科研跟进")
    .replace(/scientific remediation \/ follow-up/gi, "科研修正交接 / 科研跟进")
    .replace(/scientific remediation/gi, "科研修正")
    .replace(/修正事项 handoff/gi, "修正交接说明")
    .replace(/\bremediation\b/gi, "修正事项")
    .replace(/skill-草稿\.json/gi, "技能草稿 JSON")
    .replace(/skill-draft\.json/gi, "技能草稿 JSON")
    .replace(/溯源-manifest\.json/gi, "溯源清单 JSON")
    .replace(/scientific 跟进/gi, "科研跟进")
    .replace(/科研修正 handoff/gi, "科研修正交接说明")
    .replace(/follow-up/gi, "\u8ddf\u8fdb")
    .replace(/preflight \/ execution/gi, "\u9884\u68c0 / \u6267\u884c")
    .replace(/solver dispatch/gi, "\u6c42\u89e3\u6d3e\u53d1");
}

function sanitizeWorkspaceDisplayText(text: string) {
  let value = text.trim();

  const wrappedPairs: Array<readonly [string, string]> = [
    ['"', '"'],
    ["'", "'"],
    ["“", "”"],
    ["‘", "’"],
  ];

  for (const [start, end] of wrappedPairs) {
    if (value.startsWith(start) && value.endsWith(end) && value.length >= 2) {
      value = value.slice(start.length, value.length - end.length).trim();
      break;
    }
  }

  value = value.replace(/([。！？.!?])\1+/g, "$1");
  value = value.replace(/([。！？.!?])["”']$/g, "$1");

  return value;
}

export function localizeWorkspaceDisplayText(text: string | null | undefined) {
  if (!text) {
    return text ?? "";
  }

  const preRepaired = repairRecoveredCopyLeaks(collapseVirtualUserDataPaths(text));

  const replaced = DISPLAY_TEXT_REPLACEMENTS.reduce(
    (value, [search, replacement]) => replaceAll(value, search, replacement),
    preRepaired,
  );

  const localized = DISPLAY_TEXT_REGEX_REPLACEMENTS.reduce(
    (value, [pattern, replacement]) => value.replace(pattern, replacement),
    replaced,
  );

  return sanitizeWorkspaceDisplayText(
    repairRecoveredCopyLeaks(collapseVirtualUserDataPaths(localized)),
  );
}

export function localizeWorkspaceToolName(toolName: string) {
  return TOOL_NAME_LABELS[toolName] ?? localizeWorkspaceDisplayText(toolName);
}

export function localizeWorkspaceToolDescription(description: string) {
  return localizeWorkspaceDisplayText(description);
}

export function localizeThreadDisplayTitle(title: string) {
  return localizeWorkspaceDisplayText(title);
}
