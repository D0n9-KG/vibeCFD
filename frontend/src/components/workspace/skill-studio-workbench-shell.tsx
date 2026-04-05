"use client";

import {
  ArrowUpRightIcon,
  ClipboardCheckIcon,
  GitBranchPlusIcon,
  PackageCheckIcon,
  ShieldCheckIcon,
  TestTubeDiagonalIcon,
  WandSparklesIcon,
  WaypointsIcon,
} from "lucide-react";
import { type ReactNode, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import {
  SkillStudioWorkbenchPanel,
  type SkillStudioGraphFilter,
  type SkillStudioWorkbenchView,
} from "./skill-studio-workbench-panel";

type SkillStudioWorkbenchShellProps = {
  threadId: string;
  assistantLabel: string;
  hasWorkbenchSurface: boolean;
  isNewThread: boolean;
  className?: string;
  onOpenChat: () => void;
};

const SKILL_STUDIO_VIEWS: Array<{
  id: SkillStudioWorkbenchView;
  label: string;
  shortLabel: string;
  icon: typeof WandSparklesIcon;
  note: string;
}> = [
  {
    id: "overview",
    label: "总览",
    shortLabel: "总览",
    icon: WandSparklesIcon,
    note: "先判断技能生命周期处在哪一段，再决定深入哪个工作面板。",
  },
  {
    id: "build",
    label: "创建",
    shortLabel: "创建",
    icon: PackageCheckIcon,
    note: "聚焦技能包结构、触发条件、说明文档和基础素材。",
  },
  {
    id: "validation",
    label: "评估",
    shortLabel: "评估",
    icon: ShieldCheckIcon,
    note: "查看规则校验、错误告警和专家审阅阻塞项。",
  },
  {
    id: "test",
    label: "测试",
    shortLabel: "测试",
    icon: TestTubeDiagonalIcon,
    note: "审阅场景测试矩阵、覆盖情况和 dry-run 准备度。",
  },
  {
    id: "publish",
    label: "发布",
    shortLabel: "发布",
    icon: ClipboardCheckIcon,
    note: "确认门槛、交付状态和最终启用动作。",
  },
  {
    id: "graph",
    label: "连接",
    shortLabel: "连接",
    icon: GitBranchPlusIcon,
    note: "查看技能图谱中的上下游关系和高影响节点。",
  },
];

const SKILL_STUDIO_GRAPH_FILTERS: Array<{
  id: SkillStudioGraphFilter;
  label: string;
}> = [
  { id: "all", label: "全部" },
  { id: "upstream", label: "上游" },
  { id: "downstream", label: "下游" },
  { id: "similar", label: "相似" },
  { id: "high-impact", label: "高影响" },
];

const DEFAULT_SKILL_STUDIO_VIEW = SKILL_STUDIO_VIEWS[0]!;

export function SkillStudioWorkbenchShell({
  threadId,
  assistantLabel,
  hasWorkbenchSurface,
  isNewThread,
  className,
  onOpenChat,
}: SkillStudioWorkbenchShellProps) {
  const [activeView, setActiveView] =
    useState<SkillStudioWorkbenchView>("overview");
  const [graphFilter, setGraphFilter] =
    useState<SkillStudioGraphFilter>("all");

  const selectedView = useMemo(
    () =>
      SKILL_STUDIO_VIEWS.find((view) => view.id === activeView) ??
      DEFAULT_SKILL_STUDIO_VIEW,
    [activeView],
  );
  const lifecycleFocus = activeView === "overview" ? "build" : activeView;
  const shouldShowPlaceholder =
    !hasWorkbenchSurface && activeView !== "overview";

  if (isNewThread) {
    return (
      <section className="min-w-0 rounded-[32px] border border-slate-200/80 bg-[radial-gradient(circle_at_top_right,rgba(249,115,22,0.12),transparent_22%),radial-gradient(circle_at_84%_18%,rgba(56,189,248,0.08),transparent_16%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(246,249,252,0.98))] p-5 shadow-[0_24px_60px_rgba(15,23,42,0.08)] md:p-6 xl:p-7">
        <div className="workspace-kicker text-orange-700">
          技能定义
        </div>
        <div className="mt-4 grid gap-5 xl:grid-cols-[minmax(0,1.28fr)_320px]">
          <div className="space-y-5">
            <section className="rounded-[28px] border border-slate-200/80 bg-white/92 p-5 shadow-[0_18px_40px_rgba(15,23,42,0.06)] md:p-6">
              <h2 className="text-2xl font-semibold tracking-tight text-slate-950 xl:text-[2.1rem]">
                明确技能目标、边界与验收要求
              </h2>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700">
                新建技能线程首屏仅保留定义阶段所需信息，不提前展开完整生命周期工作台。请先明确技能目标、触发条件、输入输出、边界约束与验收要求，右侧协作区会据此生成可审阅的技能产物。
              </p>

              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <OverviewStat label="当前代理" value={assistantLabel} />
                <OverviewStat label="流程路径" value="创建 → 评估 → 连接" />
                <OverviewStat
                  label="进入方式"
                  value="先录入，再生成工作台"
                />
              </div>
            </section>

            <section className="rounded-[28px] border border-slate-200/80 bg-white/90 p-5 shadow-[0_16px_34px_rgba(15,23,42,0.05)] md:p-6">
              <div className="workspace-kicker text-orange-700">关键信息</div>
              <h3 className="mt-3 text-lg font-semibold tracking-tight text-slate-950">
                请先提供以下信息
              </h3>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <StartStep
                  index="01"
                  title="技能目标"
                  description="这个技能解决什么问题，用户什么时候应该调用它，成功输出是什么。"
                />
                <StartStep
                  index="02"
                  title="触发与输入"
                  description="它依赖哪些上下文、文件、参数或前置条件，触发时要拿到什么输入。"
                />
                <StartStep
                  index="03"
                  title="约束与边界"
                  description="哪些事情必须做，哪些事情不能做，失败时应该如何反馈和停止。"
                />
                <StartStep
                  index="04"
                  title="示例与验收"
                  description="给出一两个典型例子，以及你怎样判断这个技能已经可用。"
                />
              </div>

              <div className="mt-5 rounded-[24px] border border-orange-200/80 bg-orange-50/75 p-4">
                <div className="text-sm font-semibold text-slate-950">
                  输入模板
                </div>
                <p className="mt-2 text-sm leading-7 text-slate-700">
                  “我要做一个技能，它负责什么场景，需要哪些输入，输出什么结果，限制条件和验收标准分别是什么。”
                </p>
                <div className="mt-4 flex flex-wrap gap-3">
                  <Button className="min-w-[180px]" onClick={onOpenChat}>
                    填写技能说明
                  </Button>
                  <Button
                    className="min-w-[180px]"
                    variant="outline"
                    onClick={onOpenChat}
                  >
                    定位至输入区
                  </Button>
                </div>
              </div>
            </section>
          </div>

          <div className="grid gap-4">
            <FocusCard
              icon={PackageCheckIcon}
              title="首轮产出"
              body="技能骨架、用途说明、触发条件和首批规则草案。"
              note="定义完成后，系统再进入可审阅的生命周期工作台。"
            />
            <FocusCard
              icon={ShieldCheckIcon}
              title="评估阶段启用条件"
              body="待首份技能产物生成后，再查看校验、测试与发布闸门。"
              note="这样页面重点会集中在当前阶段最重要的信息上。"
            />
            <FocusCard
              icon={GitBranchPlusIcon}
              title="关系图审阅时机"
              body="请先完成技能定义，再检查它与现有技能图谱之间的上下游关系。"
              note="连接关系属于第二层信息，不应占用首屏注意力。"
            />
          </div>
        </div>
      </section>
    );
  }

  return (
    <div className={cn("min-h-0", className)}>
      <aside className="hidden min-h-0 flex-col overflow-hidden rounded-[30px] border border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(244,247,250,0.98))] p-4 text-slate-950 shadow-[0_24px_64px_rgba(15,23,42,0.08)] xl:flex">
        <div className="rounded-[24px] border border-orange-200/80 bg-[radial-gradient(circle_at_top_left,rgba(249,115,22,0.14),transparent_34%),linear-gradient(180deg,rgba(255,247,237,0.96),rgba(255,255,255,0.98))] p-4 shadow-[0_14px_34px_rgba(249,115,22,0.10)]">
          <div className="text-[10px] font-semibold uppercase tracking-[0.24em] text-orange-700/80">
            Skill Rail
          </div>
          <div className="mt-2 text-lg font-semibold tracking-tight text-slate-950">
            {assistantLabel}
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            把创建、评估、测试、发布和图谱连接收进一条生命周期轨道，不再把所有摘要堆在同一屏。
          </p>
        </div>

        <div className="mt-4 grid gap-3">
          <RailStat label="Stage" value={selectedView.label} tone="orange" />
          <RailStat
            label="Surface"
            value={hasWorkbenchSurface ? "已接入工作台" : "等待首份产物"}
          />
          <RailStat label="Thread" value={isNewThread ? "新线程" : "迭代线程"} />
        </div>

        <nav className="mt-4 flex-1 space-y-2">
          {SKILL_STUDIO_VIEWS.map((view) => {
            const Icon = view.icon;
            const isActive = activeView === view.id;

            return (
              <button
                key={view.id}
                type="button"
                className={cn(
                  "flex w-full items-start gap-3 rounded-2xl border px-3 py-3 text-left transition-all",
                  isActive
                    ? "border-orange-200/90 bg-orange-50/95 text-slate-950 shadow-[0_12px_24px_rgba(249,115,22,0.10)]"
                    : "border-slate-200/80 bg-white/84 text-slate-600 hover:border-slate-300 hover:bg-white",
                )}
                onClick={() => setActiveView(view.id)}
              >
                <span
                  className={cn(
                    "mt-0.5 rounded-xl border p-2",
                    isActive
                      ? "border-orange-200/80 bg-white text-orange-700"
                      : "border-slate-200/80 bg-slate-50 text-slate-400",
                  )}
                >
                  <Icon className="size-4" />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-semibold">{view.label}</span>
                  <span className="mt-1 block text-xs leading-5 text-slate-500">
                    {view.note}
                  </span>
                </span>
              </button>
            );
          })}
        </nav>
      </aside>

      <section className="min-h-0 min-w-0">
        <div className="mb-4 rounded-[32px] border border-slate-200/80 bg-[radial-gradient(circle_at_top_right,rgba(249,115,22,0.12),transparent_22%),radial-gradient(circle_at_84%_18%,rgba(56,189,248,0.08),transparent_16%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(245,248,252,0.98))] p-5 shadow-[0_24px_60px_rgba(15,23,42,0.08)]">
          <div className="workspace-kicker text-orange-700">
            Create / Evaluate / Connect
          </div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950 xl:text-[2.05rem]">
            先确认技能现在处在哪一段生命周期
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700">
            顶部只保留用户最关心的状态，不再把创建、评估、测试、发布和图谱说明同时堆满首屏。
          </p>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <OverviewStat label="当前视图" value={selectedView.label} />
            <OverviewStat label="协作代理" value={assistantLabel} />
            <OverviewStat
              label="工作台状态"
              value={hasWorkbenchSurface ? "已接入产物" : "等待首份产物"}
            />
            <OverviewStat
              label="图谱过滤"
              value={graphFilterLabel(graphFilter)}
            />
          </div>

          <div className="mt-5 flex gap-2 overflow-x-auto xl:hidden">
            {SKILL_STUDIO_VIEWS.map((view) => {
              const Icon = view.icon;
              const isActive = activeView === view.id;

              return (
                <button
                  key={view.id}
                  type="button"
                  className={cn(
                    "flex shrink-0 items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-all",
                    isActive
                      ? "border-orange-200/90 bg-orange-50/95 text-orange-700"
                      : "border-slate-200/80 bg-white/85 text-slate-600",
                  )}
                  onClick={() => setActiveView(view.id)}
                >
                  <Icon className="size-4" />
                  {view.shortLabel}
                </button>
              );
            })}
          </div>
        </div>

        {activeView === "overview" ? (
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_340px]">
            <section className="workspace-surface-card overflow-hidden p-0">
              <div className="grid h-full xl:grid-cols-[250px_minmax(0,1fr)]">
                <div className="border-b border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,247,237,0.96),rgba(248,250,252,0.98))] p-5 xl:border-b-0 xl:border-r xl:border-slate-200/80">
                  <div className="workspace-kicker text-orange-700">
                    Lifecycle Rail
                  </div>
                  <h3 className="mt-3 text-base font-semibold text-slate-950">
                    生命周期轨道
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    先定义能力边界，再完成规则校验和 dry-run，最后处理发布与图谱挂接。
                  </p>

                  <div className="mt-4 space-y-3">
                    {SKILL_STUDIO_VIEWS.filter(
                      (view) => view.id !== "overview",
                    ).map((view, index) => (
                      <LifecycleItem
                        key={view.id}
                        index={index + 1}
                        label={view.label}
                        note={view.note}
                        isActive={lifecycleFocus === view.id}
                        onClick={() => setActiveView(view.id)}
                      />
                    ))}
                  </div>
                </div>

                <div className="p-5 md:p-6">
                  <div>
                    <h3 className="text-[1.45rem] font-semibold tracking-tight text-slate-950">
                      中央只保留当前聚焦区
                    </h3>
                    <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700">
                      让用户先看清正在做的事情、为什么重要，以及下一步要去哪个工作面板，而不是在一屏里阅读所有规则说明。
                    </p>
                  </div>

                  <div className="mt-5 grid gap-3 md:grid-cols-2">
                    <FocusCard
                      icon={PackageCheckIcon}
                      title="创建骨架"
                      body="先固定 skill purpose、触发条件和 builtin skills，再补规则与示例。"
                      note="把技能结构定住，比一开始堆太多说明更重要。"
                    />
                    <FocusCard
                      icon={ShieldCheckIcon}
                      title="评估阻塞"
                      body="错误、警告和专家审阅意见应该集中出现，而不是散落在多张摘要卡里。"
                      note="用户需要一眼看到真正阻塞发布的项。"
                    />
                    <FocusCard
                      icon={TestTubeDiagonalIcon}
                      title="测试准备"
                      body="dry-run 前优先看场景覆盖和 blocking reason，减少反复回跳。"
                      note="测试不是附属信息，而是发布前的关键门槛。"
                    />
                    <FocusCard
                      icon={GitBranchPlusIcon}
                      title="图谱定位"
                      body="把技能放回关系网络，判断它是补位、复用还是高影响节点。"
                      note="图谱应该作为明确入口，而不是总览中的次要角落。"
                    />
                  </div>
                </div>
              </div>
            </section>

            <div className="grid gap-4">
              <DockPanel
                eyebrow="Next"
                title="下一步操作"
                description="动作入口集中到一列，避免用户在多个卡片之间寻找按钮。"
              >
                <OperationRow
                  label="创建轨道"
                  title={isNewThread ? "先搭建第一版技能骨架" : "继续当前技能线程"}
                  cta={isNewThread ? "开始创建" : "继续协作"}
                  onAction={onOpenChat}
                />
                <OperationRow
                  label="评估轨道"
                  title="先检查规则校验和专家阻塞项"
                  cta="进入评估视图"
                  onAction={() => setActiveView("validation")}
                />
                <OperationRow
                  label="连接轨道"
                  title="如果更关心关系网络，直接跳到图谱视图"
                  cta="进入连接视图"
                  onAction={() => setActiveView("graph")}
                />
              </DockPanel>

              <DockPanel
                eyebrow="Status"
                title="当前更轻量的摘要"
                description="只保留会影响判断的状态，其余内容进入对应工作面板。"
              >
                <DockItem label="协作代理" value={assistantLabel} />
                <DockItem
                  label="工作台"
                  value={hasWorkbenchSurface ? "已接入产物" : "等待首份产物"}
                />
                <DockItem
                  label="线程形态"
                  value={isNewThread ? "新线程" : "迭代线程"}
                />
              </DockPanel>
            </div>
          </div>
        ) : null}

        {activeView === "graph" ? (
          <div className="mb-4 flex flex-wrap gap-2">
            {SKILL_STUDIO_GRAPH_FILTERS.map((filter) => (
              <Button
                key={filter.id}
                variant={graphFilter === filter.id ? "default" : "outline"}
                className={cn(
                  graphFilter === filter.id
                    ? "border-orange-200/90 bg-orange-50 text-orange-700 hover:bg-orange-100"
                    : "border-slate-300 bg-white/82 text-slate-700 hover:bg-slate-50",
                )}
                onClick={() => setGraphFilter(filter.id)}
              >
                {filter.label}
              </Button>
            ))}
          </div>
        ) : null}

        {activeView !== "overview" ? (
          <WorkbenchViewFrame
            title={selectedView.label}
            note={selectedView.note}
            status={hasWorkbenchSurface ? "已接入工作面" : "等待首份技能产物"}
          >
            {hasWorkbenchSurface ? (
              <SkillStudioWorkbenchPanel
                threadId={threadId}
                view={activeView}
                graphFilter={graphFilter}
              />
            ) : shouldShowPlaceholder ? (
              <SkillStudioPlaceholder
                assistantLabel={assistantLabel}
                activeViewLabel={selectedView.label}
              />
            ) : null}
          </WorkbenchViewFrame>
        ) : null}

        {activeView === "overview" && !hasWorkbenchSurface ? (
          <div className="mt-4">
            <SkillStudioPlaceholder
              assistantLabel={assistantLabel}
              activeViewLabel="总览"
            />
          </div>
        ) : null}
      </section>
    </div>
  );
}

function graphFilterLabel(filter: SkillStudioGraphFilter) {
  return (
    SKILL_STUDIO_GRAPH_FILTERS.find((item) => item.id === filter)?.label ??
    "全部"
  );
}

function RailStat({
  label,
  value,
  tone = "slate",
}: {
  label: string;
  value: string;
  tone?: "slate" | "orange";
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border px-4 py-3 shadow-[0_10px_24px_rgba(15,23,42,0.04)]",
        tone === "orange"
          ? "border-orange-200/80 bg-orange-50/85"
          : "border-slate-200/80 bg-white/84",
      )}
    >
      <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
        {label}
      </div>
      <div className="mt-2 text-sm font-semibold text-slate-950">{value}</div>
    </div>
  );
}

function OverviewStat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-[22px] border border-slate-200/80 bg-white/90 px-4 py-3 shadow-[0_12px_28px_rgba(15,23,42,0.05)]">
      <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">
        {label}
      </div>
      <div className="mt-2 text-base font-semibold text-slate-950">{value}</div>
    </div>
  );
}

function LifecycleItem({
  index,
  label,
  note,
  isActive,
  onClick,
}: {
  index: number;
  label: string;
  note: string;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={cn(
        "w-full rounded-2xl border px-3 py-3 text-left transition-all",
        isActive
          ? "border-orange-200/90 bg-orange-50/95 shadow-[0_10px_22px_rgba(249,115,22,0.10)]"
          : "border-slate-200/80 bg-white/84 hover:border-slate-300 hover:bg-white",
      )}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            "flex size-8 shrink-0 items-center justify-center rounded-full border text-xs font-semibold",
            isActive
              ? "border-orange-200/80 bg-white text-orange-700"
              : "border-slate-200/80 bg-slate-50 text-slate-500",
          )}
        >
          {index}
        </div>
        <div className="min-w-0">
          <div className="text-sm font-semibold text-slate-950">{label}</div>
          <div className="mt-1 text-xs leading-5 text-slate-500">{note}</div>
        </div>
      </div>
    </button>
  );
}

function FocusCard({
  icon: Icon,
  title,
  body,
  note,
}: {
  icon: typeof PackageCheckIcon;
  title: string;
  body: string;
  note: string;
}) {
  return (
    <section className="rounded-[24px] border border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.96))] p-4 shadow-[0_14px_30px_rgba(15,23,42,0.04)]">
      <div className="flex items-center gap-2">
        <div className="rounded-xl bg-orange-50 p-2 text-orange-700">
          <Icon className="size-4" />
        </div>
        <div className="text-sm font-semibold text-slate-950">{title}</div>
      </div>
      <div className="mt-3 text-sm leading-6 text-slate-800">{body}</div>
      <p className="mt-2 text-xs leading-5 text-slate-500">{note}</p>
    </section>
  );
}

function DockPanel({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="workspace-surface-card p-5 md:p-6">
      <div className="workspace-kicker text-orange-700">{eyebrow}</div>
      <h3 className="mt-3 text-lg font-semibold tracking-tight text-slate-950">
        {title}
      </h3>
      <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
      <div className="mt-4 space-y-3">{children}</div>
    </section>
  );
}

function OperationRow({
  label,
  title,
  cta,
  onAction,
}: {
  label: string;
  title: string;
  cta: string;
  onAction: () => void;
}) {
  return (
    <div className="rounded-[20px] border border-slate-200/80 bg-slate-50/80 p-4">
      <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">
        {label}
      </div>
      <div className="mt-2 text-sm font-semibold text-slate-950">{title}</div>
      <button
        type="button"
        className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-orange-700 transition-colors hover:text-orange-800"
        onClick={onAction}
      >
        {cta}
        <ArrowUpRightIcon className="size-4" />
      </button>
    </div>
  );
}

function DockItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-[18px] border border-slate-200/80 bg-white/92 px-4 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
        {label}
      </div>
      <div className="mt-2 text-sm font-semibold text-slate-800">{value}</div>
    </div>
  );
}

function WorkbenchViewFrame({
  title,
  note,
  status,
  children,
}: {
  title: string;
  note: string;
  status: string;
  children: ReactNode;
}) {
  return (
    <section className="workspace-surface-card overflow-hidden p-0">
      <div className="border-b border-slate-200/80 px-5 py-4 md:px-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="workspace-kicker text-orange-700">Focused Surface</div>
            <h3 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
              {title}
            </h3>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              {note}
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700">
            <WaypointsIcon className="size-3.5" />
            {status}
          </div>
        </div>
      </div>
      <div className="min-h-0 overflow-hidden">{children}</div>
    </section>
  );
}

function SkillStudioPlaceholder({
  assistantLabel,
  activeViewLabel,
}: {
  assistantLabel: string;
  activeViewLabel: string;
}) {
  return (
    <section className="rounded-[30px] border border-dashed border-slate-300 bg-white/84 p-8 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="max-w-3xl">
        <div className="workspace-kicker text-orange-700">
          Waiting For First Artifact
        </div>
        <h3 className="mt-3 text-lg font-semibold text-slate-950">
          {activeViewLabel} 视图还在等待第一份技能产物
        </h3>
        <p className="mt-3 text-sm leading-7 text-slate-700">
          先在右侧与 {assistantLabel} 完成技能草稿、校验包或测试材料。首份产物落地后，
          这里会自动切换为可深度审阅的 Skill Studio 工作台。
        </p>
      </div>
    </section>
  );
}

function StartStep({
  index,
  title,
  description,
}: {
  index: string;
  title: string;
  description: string;
}) {
  return (
    <section className="rounded-[22px] border border-slate-200/80 bg-slate-50/80 p-4 shadow-[0_10px_24px_rgba(15,23,42,0.04)]">
      <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">
        {index}
      </div>
      <div className="mt-2 text-sm font-semibold text-slate-950">{title}</div>
      <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
    </section>
  );
}
