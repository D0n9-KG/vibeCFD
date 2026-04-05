import {
  ArrowRightIcon,
  BinaryIcon,
  BlocksIcon,
  BotIcon,
  BrainCircuitIcon,
  CableIcon,
  CheckCircle2Icon,
  DatabaseZapIcon,
  FlaskConicalIcon,
  FolderKanbanIcon,
  GaugeIcon,
  GitBranchPlusIcon,
  GitForkIcon,
  NetworkIcon,
  RadarIcon,
  ShieldCheckIcon,
  WavesIcon,
} from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const workflowStages = [
  {
    title: "任务理解",
    detail: "梳理目标、约束、研究范围和交付边界，先形成可确认的设计简报。",
    icon: RadarIcon,
  },
  {
    title: "几何预检",
    detail: "围绕 STL 几何做封闭性、尺度、边界条件和基线适配检查。",
    icon: WavesIcon,
  },
  {
    title: "求解派发",
    detail: "将需求映射为 OpenFOAM 运行契约、工况配置和派发计划。",
    icon: CableIcon,
  },
  {
    title: "结果整理",
    detail: "回收结果文件、日志和图表，形成可复核的证据链与交付摘要。",
    icon: FolderKanbanIcon,
  },
  {
    title: "主管复核",
    detail: "结合运行状态、科学门槛和交付判断，明确下一步与结论级别。",
    icon: ShieldCheckIcon,
  },
];

const runtimeHighlights = [
  {
    title: "Thread + Artifact Native",
    body: "研究上下文、上传文件、产物回放与状态快照都沿用 DeerFlow 原生线程机制。",
    icon: GitForkIcon,
  },
  {
    title: "Sandboxed Simulation",
    body: "几何检查、求解派发与真实 OpenFOAM 执行通过 sandbox 与受控工具链衔接。",
    icon: GaugeIcon,
  },
  {
    title: "Sub-agent Orchestration",
    body: "将专业角色拆成可追踪的阶段与执行分工，而不是一条不透明的聊天回复。",
    icon: BotIcon,
  },
];

const skillSignals = [
  {
    title: "Create",
    body: "围绕专业流程创建结构化技能包，而不是散落的 prompt 片段。",
    icon: GitBranchPlusIcon,
  },
  {
    title: "Evaluate",
    body: "在工作台中验证技能的规则质量、测试准备度与发布门槛。",
    icon: CheckCircle2Icon,
  },
  {
    title: "Connect",
    body: "用技能图谱串联技能关系与复用路径，形成可沉淀的领域能力网络。",
    icon: NetworkIcon,
  },
];

const deliverySignals = [
  "结构化设计简报与阶段确认记录",
  "几何预检摘要、派发表单与运行日志",
  "结果趋势、报告摘要与复现实验线索",
  "产物面板中可下载、可打开、可回溯的证据链",
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <LandingHeader />

      <main className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-[44rem] bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.18),_transparent_34%),radial-gradient(circle_at_top_right,_rgba(34,197,94,0.14),_transparent_24%)] dark:bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.24),_transparent_34%),radial-gradient(circle_at_top_right,_rgba(34,197,94,0.12),_transparent_22%)]" />

        <section className="mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-[1680px] items-center px-4 pb-12 pt-28 md:px-6 lg:px-8">
          <div className="grid w-full gap-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
            <div className="space-y-7">
              <div className="flex flex-wrap gap-2">
                <Badge className="metric-chip bg-primary/10 text-primary hover:bg-primary/10">
                  Industrial Research Cockpit
                </Badge>
                <Badge className="metric-chip bg-emerald-500/10 text-emerald-700 hover:bg-emerald-500/10 dark:text-emerald-300">
                  Powered by DeerFlow
                </Badge>
                <Badge className="metric-chip bg-cyan-500/10 text-cyan-700 hover:bg-cyan-500/10 dark:text-cyan-300">
                  SkillNet-inspired workflow
                </Badge>
              </div>

              <div className="space-y-4">
                <p className="workspace-kicker">VibeCFD</p>
                <h1 className="max-w-4xl text-5xl font-semibold tracking-tight text-slate-950 dark:text-white md:text-6xl lg:text-7xl">
                  把仿真任务、研究证据和技能网络收进同一个工业科研工作区。
                </h1>
                <p className="max-w-3xl text-base leading-8 text-slate-600 dark:text-slate-300 md:text-lg">
                  VibeCFD 不是一个泛化聊天壳层，而是一套围绕
                  CFD 研究组织的专用工作台。它把 DeerFlow 的
                  runtime、artifact、sandbox 与 sub-agent
                  能力，落到真实的几何预检、求解派发、结果复核和技能沉淀流程中。
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <Button asChild size="lg" className="h-12 rounded-full px-6">
                  <Link href="/workspace">
                    进入工作区
                    <ArrowRightIcon className="size-4" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="h-12 rounded-full px-6">
                  <Link href="/workspace/submarine/submarine-cfd-demo?mock=true">
                    打开示例线程
                  </Link>
                </Button>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <SignalCard label="Runtime" value="DeerFlow Native" note="thread / artifact / sandbox / sub-agent" />
                <SignalCard label="Workspace" value="Simulation + Skill Studio" note="仿真与技能沉淀并行共存" />
                <SignalCard label="Delivery" value="Evidence First" note="报告、日志、图表与复现线索" />
              </div>
            </div>

            <div className="control-panel relative overflow-hidden p-5 md:p-6">
              <div className="absolute inset-x-0 top-0 h-32 bg-[radial-gradient(circle_at_top_right,_rgba(56,189,248,0.16),_transparent_46%)]" />
              <div className="relative space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="workspace-kicker">Mission Brief</p>
                    <h2 className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                      SUBOFF 阻力基线研究
                    </h2>
                  </div>
                  <div className="metric-chip bg-emerald-500/12 text-emerald-700 dark:text-emerald-300">
                    实时证据链
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <BriefStat label="当前阶段" value="任务理解" />
                  <BriefStat label="下一阶段" value="几何预检" />
                  <BriefStat label="工况边界" value="U=5 m/s · 水下直航" />
                  <BriefStat label="交付焦点" value="几何可用性 + CFD 准备建议" />
                </div>

                <div className="space-y-3 rounded-[1.4rem] border border-slate-200/80 bg-white/82 p-4 dark:border-slate-800/80 dark:bg-slate-950/60">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-semibold text-slate-900 dark:text-white">
                      阶段驾驶舱
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      5-step flow
                    </div>
                  </div>
                  <div className="space-y-2">
                    {workflowStages.map((stage, index) => {
                      const Icon = stage.icon;
                      return (
                        <div
                          key={stage.title}
                          className={cn(
                            "flex items-start gap-3 rounded-2xl border px-3 py-3",
                            index === 0
                              ? "border-sky-200 bg-sky-50/90 dark:border-sky-400/30 dark:bg-sky-500/10"
                              : "border-slate-200/80 bg-white/70 dark:border-slate-800/80 dark:bg-slate-950/45",
                          )}
                        >
                          <div
                            className={cn(
                              "mt-0.5 rounded-xl p-2",
                              index === 0
                                ? "bg-sky-500 text-white"
                                : "bg-slate-100 text-slate-700 dark:bg-slate-900 dark:text-slate-200",
                            )}
                          >
                            <Icon className="size-4" />
                          </div>
                          <div className="min-w-0">
                            <div className="text-sm font-semibold text-slate-900 dark:text-white">
                              {stage.title}
                            </div>
                            <div className="mt-1 text-xs leading-5 text-slate-600 dark:text-slate-400">
                              {stage.detail}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <LandingSection
          kicker="Runtime Workflow"
          title="从研究意图到运行证据，工作流不再藏在一段聊天回复里。"
          description="把关键阶段显式建模成可见、可恢复、可复核的控制面板。评委能一眼看懂系统结构，真实用户也能直接进入实际工作。"
        >
          <div className="grid gap-4 lg:grid-cols-5">
            {workflowStages.map((stage, index) => {
              const Icon = stage.icon;
              return (
                <div key={stage.title} className="control-panel p-5">
                  <div className="flex items-center justify-between">
                    <span className="workspace-kicker">Stage 0{index + 1}</span>
                    <Icon className="size-4 text-primary" />
                  </div>
                  <div className="mt-4 text-lg font-semibold text-slate-950 dark:text-white">
                    {stage.title}
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {stage.detail}
                  </p>
                </div>
              );
            })}
          </div>
        </LandingSection>

        <LandingSection
          kicker="DeerFlow Runtime"
          title="沿用 DeerFlow 原生 runtime，而不是再造一套平行执行层。"
          description="线程、产物、工具调用、sandbox 和 sub-agent 编排全部保留 DeerFlow 原生语义，只在上层加上 VibeCFD 的仿真领域模型。"
        >
          <div className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
            <div className="control-panel p-6">
              <div className="workspace-kicker">Research Runtime</div>
              <div className="mt-3 text-2xl font-semibold text-slate-950 dark:text-white">
                一个 thread，同步承载上下文、工况、产物和交付状态。
              </div>
              <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
                用户上传 STL 后，VibeCFD 会在同一条 DeerFlow
                thread 中推进几何预检、求解派发、结果整理与复核，不需要跳转到多个不相干的工具界面。
              </p>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <BriefStat label="Artifacts" value="HTML · JSON · Markdown · Log" />
                <BriefStat label="Execution" value="Sandbox + Tool Contracts" />
                <BriefStat label="State" value="submarine_runtime snapshot" />
                <BriefStat label="Collaboration" value="Supervisor + specialist agents" />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {runtimeHighlights.map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="control-panel p-5">
                    <div className="rounded-2xl bg-primary/10 p-3 text-primary">
                      <Icon className="size-5" />
                    </div>
                    <div className="mt-4 text-base font-semibold text-slate-950 dark:text-white">
                      {item.title}
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {item.body}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </LandingSection>

        <LandingSection
          kicker="Skill Intelligence"
          title="Skill Studio 不是附属页，而是技能创建、评估、连接的第二核心 surface。"
          description="把 SkillNet 的 create / evaluate / connect 思路，转译成领域专家真正能用的技能工作台与技能图谱。"
        >
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <div className="grid gap-4 sm:grid-cols-3">
              {skillSignals.map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="control-panel p-5">
                    <div className="rounded-2xl bg-cyan-500/10 p-3 text-cyan-700 dark:text-cyan-300">
                      <Icon className="size-5" />
                    </div>
                    <div className="mt-4 text-base font-semibold text-slate-950 dark:text-white">
                      {item.title}
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                      {item.body}
                    </p>
                  </div>
                );
              })}
            </div>

            <div className="control-panel overflow-hidden p-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="workspace-kicker">Skill Graph Snapshot</div>
                  <div className="mt-3 text-2xl font-semibold text-slate-950 dark:text-white">
                    让技能关系成为可见的工程资产。
                  </div>
                </div>
                <BrainCircuitIcon className="size-6 text-primary" />
              </div>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
                技能工作台会把规则、测试、发布状态与技能图谱放进同一个 surface，帮助团队持续积累专业知识，而不是一次性生成 prompt。
              </p>

              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <SkillGraphPill icon={BlocksIcon} label="Skill Package" value="规则 / 元数据 / 测试矩阵" />
                <SkillGraphPill icon={BinaryIcon} label="Validation" value="结构校验 + readiness 追踪" />
                <SkillGraphPill icon={DatabaseZapIcon} label="Graph" value="关系、复用与启用状态" />
                <SkillGraphPill icon={BotIcon} label="Assistant" value="专属技能创建器代理" />
              </div>
            </div>
          </div>
        </LandingSection>

        <LandingSection
          kicker="Evidence Delivery"
          title="交付不止是一个结论，而是一条能回放的证据链。"
          description="报告、日志、图表、导出文件与复现实验线索，都要成为可打开、可下载、可复核的工作产物。"
        >
          <div className="grid gap-4 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
            <div className="control-panel p-6">
              <div className="workspace-kicker">Delivery Signals</div>
              <div className="mt-3 text-2xl font-semibold text-slate-950 dark:text-white">
                面向评审者，也面向真正执行研究的人。
              </div>
              <div className="mt-5 space-y-3">
                {deliverySignals.map((signal) => (
                  <div
                    key={signal}
                    className="flex items-start gap-3 rounded-2xl border border-slate-200/80 bg-white/74 px-4 py-3 dark:border-slate-800/80 dark:bg-slate-950/48"
                  >
                    <CheckCircle2Icon className="mt-0.5 size-4 shrink-0 text-emerald-500" />
                    <div className="text-sm leading-6 text-slate-700 dark:text-slate-300">
                      {signal}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <EvidenceCard
                icon={FolderKanbanIcon}
                title="Artifact Workspace"
                body="按阶段浏览结果文件、说明文档、报告和日志，打开路径统一，动作统一。"
              />
              <EvidenceCard
                icon={FlaskConicalIcon}
                title="Scientific Gate"
                body="在阶段推进之外，还保留结论级别、可交付性和科研门槛的复核视角。"
              />
              <EvidenceCard
                icon={GaugeIcon}
                title="Runtime Trends"
                body="关键指标和趋势图与阶段视图同屏呈现，不需要退出到另一个 dashboard。"
              />
              <EvidenceCard
                icon={ShieldCheckIcon}
                title="Review-Ready Reporting"
                body="把主管复核、用户确认和最终判断放进独立审阅界面，保证可追责性。"
              />
            </div>
          </div>
        </LandingSection>

        <LandingSection
          kicker="Next Action"
          title="准备好进入 VibeCFD 工作区了吗？"
          description="你可以直接进入默认仿真 surface，或者先打开一个带完整产物和流程语义的示例线程。"
        >
          <div className="workspace-surface-card flex flex-col gap-5 p-6 md:flex-row md:items-center md:justify-between md:p-8">
            <div className="max-w-3xl">
              <div className="text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
                从仿真任务开始，或进入 Skill Studio 沉淀领域技能。
              </div>
              <p className="mt-3 text-base leading-8 text-slate-600 dark:text-slate-300">
                默认入口仍然是 submarine surface；Skill Studio 作为第二核心
                surface，用来把专业流程变成可复用、可评估、可连接的技能资产。
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button asChild size="lg" className="h-12 rounded-full px-6">
                <Link href="/workspace">
                  进入 VibeCFD
                  <ArrowRightIcon className="size-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="h-12 rounded-full px-6">
                <Link href="/workspace/skill-studio">
                  打开 Skill Studio
                </Link>
              </Button>
            </div>
          </div>
        </LandingSection>
      </main>

      <footer className="mx-auto w-full max-w-[1680px] px-4 pb-10 pt-4 md:px-6 lg:px-8">
        <div className="workspace-surface-card flex flex-col gap-4 px-6 py-6 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="workspace-kicker">VibeCFD</div>
            <div className="mt-2 text-lg font-semibold text-slate-950 dark:text-white">
              Built on DeerFlow runtime, guided by SkillNet-style skill thinking.
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
              工业科研工作区、仿真运行驾驶舱与技能沉淀系统，统一在同一套前端骨架内。
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button asChild variant="outline" className="rounded-full">
              <a
                href="https://github.com/bytedance/deer-flow"
                rel="noreferrer"
                target="_blank"
              >
                DeerFlow
              </a>
            </Button>
            <Button asChild variant="outline" className="rounded-full">
              <a
                href="https://github.com/zjunlp/SkillNet"
                rel="noreferrer"
                target="_blank"
              >
                SkillNet
              </a>
            </Button>
          </div>
        </div>
      </footer>
    </div>
  );
}

function LandingHeader() {
  return (
    <header className="fixed inset-x-0 top-0 z-40">
      <div className="mx-auto flex w-full max-w-[1680px] items-center justify-between px-4 py-4 md:px-6 lg:px-8">
        <div className="workspace-surface-card flex items-center gap-3 px-4 py-3">
          <div className="rounded-2xl bg-primary p-2 text-primary-foreground">
            <WavesIcon className="size-5" />
          </div>
          <div>
            <div className="workspace-kicker">VibeCFD</div>
            <div className="text-sm font-semibold text-slate-950 dark:text-white">
              Industrial research cockpit
            </div>
          </div>
        </div>

        <div className="workspace-surface-card flex items-center gap-2 px-3 py-3">
          <Button asChild variant="ghost" className="rounded-full">
            <Link href="/workspace">Workspace</Link>
          </Button>
          <Button asChild variant="outline" className="rounded-full">
            <a
              href="https://github.com/bytedance/deer-flow"
              rel="noreferrer"
              target="_blank"
            >
              DeerFlow Runtime
            </a>
          </Button>
        </div>
      </div>
    </header>
  );
}

function LandingSection({
  kicker,
  title,
  description,
  children,
}: {
  kicker: string;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mx-auto w-full max-w-[1680px] px-4 py-10 md:px-6 md:py-12 lg:px-8 lg:py-14">
      <div className="mb-6 max-w-3xl">
        <div className="workspace-kicker">{kicker}</div>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white md:text-4xl">
          {title}
        </h2>
        <p className="mt-3 text-base leading-8 text-slate-600 dark:text-slate-300">
          {description}
        </p>
      </div>
      {children}
    </section>
  );
}

function SignalCard({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="control-panel p-4">
      <div className="workspace-kicker">{label}</div>
      <div className="mt-2 text-lg font-semibold text-slate-950 dark:text-white">
        {value}
      </div>
      <div className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
        {note}
      </div>
    </div>
  );
}

function BriefStat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-[1.15rem] border border-slate-200/80 bg-white/76 px-4 py-3 dark:border-slate-800/80 dark:bg-slate-950/46">
      <div className="workspace-kicker">{label}</div>
      <div className="mt-2 text-sm font-semibold leading-6 text-slate-900 dark:text-white">
        {value}
      </div>
    </div>
  );
}

function SkillGraphPill({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof BlocksIcon;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-[1.15rem] border border-slate-200/80 bg-white/76 px-4 py-3 dark:border-slate-800/80 dark:bg-slate-950/46">
      <div className="flex items-center gap-2">
        <Icon className="size-4 text-primary" />
        <div className="text-sm font-semibold text-slate-900 dark:text-white">
          {label}
        </div>
      </div>
      <div className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
        {value}
      </div>
    </div>
  );
}

function EvidenceCard({
  icon: Icon,
  title,
  body,
}: {
  icon: typeof FolderKanbanIcon;
  title: string;
  body: string;
}) {
  return (
    <div className="control-panel p-5">
      <div className="rounded-2xl bg-emerald-500/10 p-3 text-emerald-700 dark:text-emerald-300">
        <Icon className="size-5" />
      </div>
      <div className="mt-4 text-base font-semibold text-slate-950 dark:text-white">
        {title}
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
        {body}
      </p>
    </div>
  );
}
