"use client";

import {
  ClipboardCheckIcon,
  GitBranchPlusIcon,
  LayoutPanelLeftIcon,
  PackageCheckIcon,
  ShieldCheckIcon,
  TestTubeDiagonalIcon,
  WaypointsIcon,
  WandSparklesIcon,
} from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/core/i18n/hooks";
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
  icon: typeof WandSparklesIcon;
  note: string;
}> = [
  {
    id: "overview",
    label: "总览",
    icon: WandSparklesIcon,
    note: "查看当前准备度、阻塞点和下一步建议。",
  },
  {
    id: "build",
    label: "构建",
    icon: PackageCheckIcon,
    note: "查看技能包结构、规则和草稿合同。",
  },
  {
    id: "validation",
    label: "校验",
    icon: ShieldCheckIcon,
    note: "查看校验状态、错误和警告。",
  },
  {
    id: "test",
    label: "测试",
    icon: TestTubeDiagonalIcon,
    note: "查看场景测试矩阵和阻塞用例。",
  },
  {
    id: "publish",
    label: "发布",
    icon: ClipboardCheckIcon,
    note: "查看发布门槛和启用前动作。",
  },
  {
    id: "graph",
    label: "图谱",
    icon: GitBranchPlusIcon,
    note: "聚焦关系图谱和节点检查器。",
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

export function SkillStudioWorkbenchShell({
  threadId,
  assistantLabel,
  hasWorkbenchSurface,
  isNewThread,
  className,
  onOpenChat,
}: SkillStudioWorkbenchShellProps) {
  const { t } = useI18n();
  const [activeView, setActiveView] =
    useState<SkillStudioWorkbenchView>("overview");
  const [graphFilter, setGraphFilter] =
    useState<SkillStudioGraphFilter>("all");
  const [navOpen, setNavOpen] = useState(false);

  const shouldShowPlaceholder =
    !hasWorkbenchSurface && activeView !== "overview";

  return (
    <div className={cn("min-h-0", className)}>
      <aside className="hidden min-h-0 flex-col overflow-hidden rounded-[28px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,251,235,0.92),rgba(255,255,255,0.96))] p-4 shadow-[0_18px_44px_rgba(120,53,15,0.08)] xl:flex">
        <div className="rounded-2xl border border-amber-100/80 bg-white/92 p-4 shadow-[0_14px_34px_rgba(120,53,15,0.08)]">
          <div className="text-[10px] font-semibold uppercase tracking-[0.24em] text-amber-700">
            技能工作台
          </div>
          <div className="mt-2 text-lg font-semibold tracking-tight text-stone-900">
            生命周期工作台
          </div>
          <p className="mt-2 text-sm leading-6 text-stone-600">
            {assistantLabel} 会持续服务当前线程中的技能起草、结构校验、试运行准备和发布收口。
          </p>
        </div>

        <div className="mt-4 rounded-2xl border border-stone-200/80 bg-white/88 p-4 shadow-[0_12px_28px_rgba(15,23,42,0.05)]">
          <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-stone-400">
            当前代理
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge variant="outline">{assistantLabel}</Badge>
            <Badge variant="outline">
              {hasWorkbenchSurface ? "已加载工作台产物" : "草稿线程"}
            </Badge>
          </div>
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
                  "flex w-full items-start gap-3 rounded-2xl border px-3 py-3 text-left transition-colors",
                  isActive
                    ? "border-amber-200 bg-amber-50 text-stone-950 shadow-[0_10px_24px_rgba(217,119,6,0.12)]"
                    : "border-stone-200/80 bg-white/86 text-stone-700 hover:border-stone-300 hover:bg-white",
                )}
                onClick={() => setActiveView(view.id)}
              >
                <span
                  className={cn(
                    "mt-0.5 rounded-xl border p-2",
                    isActive
                      ? "border-amber-200 bg-white text-amber-700"
                      : "border-stone-200 bg-stone-50 text-stone-500",
                  )}
                >
                  <Icon className="size-4" />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-semibold">{view.label}</span>
                  <span className="mt-1 block text-xs leading-5 text-stone-500">
                    {view.note}
                  </span>
                </span>
              </button>
            );
          })}
        </nav>
      </aside>

      <div className="xl:hidden">
        <div className="mb-4 flex flex-wrap gap-2">
          <Button
            variant="outline"
            className="focus-visible:ring-2 focus-visible:ring-sky-300/60"
            aria-label={
              navOpen
                ? t.workspace.hideWorkspaceViews
                : t.workspace.showWorkspaceViews
            }
            onClick={() => setNavOpen((open) => !open)}
          >
            <LayoutPanelLeftIcon className="size-4" />
            {navOpen ? "收起分栏" : "展开分栏"}
          </Button>
          <Button
            variant="outline"
            className="focus-visible:ring-2 focus-visible:ring-sky-300/60"
            aria-label={t.workspace.toggleChatRail}
            onClick={onOpenChat}
          >
            <WaypointsIcon className="size-4" />
            打开技能创建器对话
          </Button>
        </div>

        {navOpen ? (
          <div className="mb-4 rounded-[28px] border border-stone-200/80 bg-white/96 p-4 shadow-[0_18px_44px_rgba(15,23,42,0.07)]">
            <div className="grid gap-3 sm:grid-cols-2">
              {SKILL_STUDIO_VIEWS.map((view) => {
                const Icon = view.icon;
                const isActive = activeView === view.id;
                return (
                  <button
                    key={view.id}
                    type="button"
                    className={cn(
                      "rounded-2xl border px-3 py-3 text-left",
                      isActive
                        ? "border-amber-200 bg-amber-50 text-stone-950"
                        : "border-stone-200 bg-stone-50 text-stone-700",
                    )}
                    onClick={() => {
                      setActiveView(view.id);
                      setNavOpen(false);
                    }}
                  >
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <Icon className="size-4" />
                      {view.label}
                    </div>
                    <div className="mt-1 text-xs leading-5 text-stone-500">
                      {view.note}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        ) : null}
      </div>

      <section className="min-h-0 min-w-0 overflow-hidden">
        <div className="mb-4 rounded-[28px] border border-stone-200/80 bg-[linear-gradient(135deg,rgba(255,251,235,0.92),rgba(255,255,255,0.96))] p-5 shadow-[0_18px_44px_rgba(120,53,15,0.08)]">
          <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-700">
            技能编排界面
          </div>
          <div className="mt-3 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div className="min-w-0 flex-1">
              <h2 className="text-2xl font-semibold tracking-tight text-stone-900">
                让构建、校验、测试、发布和图谱审阅都保持在各自独立的工作界面里。
              </h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600">
                右侧对话轨道专门服务 {assistantLabel}，中间区域则专注可审阅的技能产物，而不是把所有面板混在一个视口里。
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">{assistantLabel}</Badge>
              <Badge variant="outline">
                {isNewThread ? "新线程" : "既有线程"}
              </Badge>
              <Badge variant="outline">
                {hasWorkbenchSurface ? "工作台已就绪" : "等待首份草稿"}
              </Badge>
              {activeView !== "overview" ? (
                <Button
                  variant="outline"
                  aria-label={t.workspace.backToOverview}
                  onClick={() => setActiveView("overview")}
                >
                  {t.workspace.backToOverview}
                </Button>
              ) : null}
            </div>
          </div>
        </div>

        {activeView === "graph" ? (
          <div
            className="mb-4 flex flex-wrap gap-2"
            aria-label={t.workspace.openGraphFilters}
          >
            {SKILL_STUDIO_GRAPH_FILTERS.map((filter) => (
              <Button
                key={filter.id}
                variant={graphFilter === filter.id ? "default" : "outline"}
                aria-label={`${t.workspace.openGraphFilters}: ${filter.label}`}
                onClick={() => setGraphFilter(filter.id)}
              >
                {filter.label}
              </Button>
            ))}
          </div>
        ) : null}

        {activeView === "overview" ? (
          <SkillStudioLaunchpad
            assistantLabel={assistantLabel}
            hasWorkbenchSurface={hasWorkbenchSurface}
            isNewThread={isNewThread}
            onOpenChat={onOpenChat}
          />
        ) : null}

        <div className="min-h-0 overflow-hidden">
          {hasWorkbenchSurface ? (
            <SkillStudioWorkbenchPanel
              threadId={threadId}
              view={activeView}
              graphFilter={graphFilter}
            />
          ) : shouldShowPlaceholder ? (
            <SkillStudioPlaceholder assistantLabel={assistantLabel} />
          ) : activeView === "overview" ? (
            <SkillStudioPlaceholder assistantLabel={assistantLabel} />
          ) : null}
        </div>
      </section>
    </div>
  );
}

function SkillStudioLaunchpad({
  assistantLabel,
  hasWorkbenchSurface,
  isNewThread,
  onOpenChat,
}: {
  assistantLabel: string;
  hasWorkbenchSurface: boolean;
  isNewThread: boolean;
  onOpenChat: () => void;
}) {
  return (
    <section className="mb-4 rounded-[28px] border border-stone-200/80 bg-white/94 p-5 shadow-[0_18px_44px_rgba(15,23,42,0.06)]">
      <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-700">
        专属协作
      </div>
      <div className="mt-3 grid gap-4 xl:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.7fr)]">
        <div>
          <h3 className="text-xl font-semibold tracking-tight text-stone-900">
            用专属技能创建器协作，而不是继续使用泛化线程。
          </h3>
          <p className="mt-2 text-sm leading-7 text-stone-600">
            右侧轨道保留给 {assistantLabel}，当前工作台则持续跟踪技能包结构、校验结果、场景测试、发布门槛和图谱定位。
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button onClick={onOpenChat}>
              {isNewThread ? "开始协作创建技能" : "继续与技能创建器协作"}
            </Button>
          </div>
        </div>

        <div className="rounded-2xl border border-stone-200/80 bg-stone-50/90 p-4">
          <div className="text-sm font-semibold text-stone-900">协作流程</div>
          <div className="mt-3 space-y-3 text-sm leading-6 text-stone-600">
            <div>1. 先明确领域规则、触发条件和验收标准。</div>
            <div>2. 审阅生成出的技能包、校验结果和测试矩阵。</div>
            <div>3. 只有在门槛和图谱定位清晰后再进入发布。</div>
            {hasWorkbenchSurface ? (
              <div>当前线程已经有可审阅的工作台产物。</div>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}

function SkillStudioPlaceholder({
  assistantLabel,
}: {
  assistantLabel: string;
}) {
  return (
    <section className="rounded-[28px] border border-dashed border-stone-300 bg-white/80 p-8 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="max-w-3xl">
        <h3 className="text-lg font-semibold text-stone-900">
          等待第一份技能包草稿
        </h3>
        <p className="mt-3 text-sm leading-7 text-stone-600">
          先在右侧与 {assistantLabel} 协作。当第一份草稿、校验包或发布就绪产物落地后，这个区域会自动切换成聚焦生命周期工作台。
        </p>
      </div>
    </section>
  );
}
