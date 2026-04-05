const DISPLAY_TEXT_REPLACEMENTS: ReadonlyArray<readonly [string, string]> = [
  ["Submarine Result Acceptance Draft", "潜艇结果验收草稿"],
  ["submarine-result-acceptance", "潜艇结果验收"],
  ["submarine result acceptance", "潜艇结果验收"],
  ["draft-only", "仅草稿"],
  ["draft only", "仅草稿"],
  ["潜艇 Skill Studio 演示", "潜艇技能工作台演示"],
  ["OpenFOAM CFD for STL Model", "STL 模型 OpenFOAM CFD 分析"],
  ["STL CFD Drag Coefficient Analysis", "STL CFD 阻力系数分析"],
  ["DeerFlow Skill 能力说明", "DeerFlow 技能能力说明"],
  ["load relevant submarine skill", "加载潜艇领域技能"],
  ["load geometry check skill", "加载几何预检技能"],
  ["load submarine geometry skill", "加载潜艇几何预检技能"],
  ["geometry preflight", "几何预检"],
  ["`/mnt/skills/public/submarine-geometry-check/SKILL.md`", "潜艇几何预检技能"],
  ["/mnt/skills/public/submarine-geometry-check/SKILL.md", "潜艇几何预检技能"],
  ["Update to-do list", "更新待办列表"],
  ["Update To-do list", "更新待办列表"],
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
];

const DISPLAY_TEXT_REGEX_REPLACEMENTS: ReadonlyArray<
  readonly [RegExp, string]
> = [
  [/\baccept\b/g, "接受"],
  [/\bbrief\b/gi, "简报"],
  [/\bdraft\b/gi, "草稿"],
  [/\boutputs\b/gi, "输出项"],
  [/\bsteps\b/gi, "步"],
  [/\bresistance\b/gi, "阻力"],
  [/\brevise\b/g, "修订"],
  [/\breject\b/g, "拒绝"],
  [/\bSkill\b/g, "技能"],
  [/\bSubmarine\b/g, "潜艇"],
];

const TOOL_NAME_LABELS: Readonly<Record<string, string>> = {
  submarine_design_brief: "潜艇设计简报",
  submarine_design_brief_tool: "潜艇设计简报",
  submarine_geometry_check: "潜艇几何预检",
  submarine_geometry_check_tool: "潜艇几何预检",
};

function replaceAll(source: string, search: string, replacement: string) {
  return source.includes(search) ? source.split(search).join(replacement) : source;
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

  const replaced = DISPLAY_TEXT_REPLACEMENTS.reduce(
    (value, [search, replacement]) => replaceAll(value, search, replacement),
    text,
  );

  const localized = DISPLAY_TEXT_REGEX_REPLACEMENTS.reduce(
    (value, [pattern, replacement]) => value.replace(pattern, replacement),
    replaced,
  );

  return sanitizeWorkspaceDisplayText(localized);
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
