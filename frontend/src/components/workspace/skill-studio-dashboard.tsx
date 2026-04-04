"use client";

import {
  ArrowUpRightIcon,
  BinaryIcon,
  CheckCircle2Icon,
  GitBranchPlusIcon,
  MessageSquareIcon,
  NetworkIcon,
  WandSparklesIcon,
} from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  buildFocusedSkillGraphItems,
  buildSkillGraphOverview,
} from "@/components/workspace/skill-graph.utils";
import { useI18n } from "@/core/i18n/hooks";
import { localizeWorkspaceDisplayText } from "@/core/i18n/workspace-display";
import { useSkillGraph, useSkillLifecycleSummaries } from "@/core/skills/hooks";
import { useThreads } from "@/core/threads/hooks";
import { env } from "@/env";

import {
  buildSkillStudioEntries,
  type SkillStudioDashboardEntry,
} from "./skill-studio-dashboard.utils";
import { formatSkillStudioStatus } from "./skill-studio-workbench.utils";
import {
  WorkspaceSurfaceCard,
  WorkspaceSurfaceMain,
  WorkspaceSurfacePage,
} from "./workspace-container";

function withMock(path: string, isMock: boolean) {
  return env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" || isMock
    ? `${path}?mock=true`
    : path;
}

function formatUpdatedAt(value: string | null) {
  if (!value) return "未知";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function SkillStudioDashboard() {
  const searchParams = useSearchParams();
  const isMock = searchParams.get("mock") === "true";
  const { t } = useI18n();
  const { data: threads = [], isLoading } = useThreads(undefined, isMock);
  const { lifecycleSummaries } = useSkillLifecycleSummaries({
    enabled: !isMock,
  });
  const entries = buildSkillStudioEntries(
    threads,
    `${t.pages.untitled}技能工作台`,
    lifecycleSummaries,
  );
  const featured = entries[0] ?? null;
  const { data: globalSkillGraph } = useSkillGraph({ isMock });
  const { data: featuredSkillGraph } = useSkillGraph({
    isMock,
    skillName: featured?.skillAssetId,
    enabled: Boolean(featured?.skillAssetId),
  });
  const graphOverview = buildSkillGraphOverview(globalSkillGraph);
  const featuredRelatedSkills = buildFocusedSkillGraphItems(
    featuredSkillGraph,
  ).slice(0, 4);

  return (
    <WorkspaceSurfacePage data-surface-label="技能工作台">
      <WorkspaceSurfaceMain className="max-w-[1720px]">
        <WorkspaceSurfaceCard className="overflow-hidden">
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.12fr)_minmax(320px,0.88fr)]">
            <div className="space-y-5">
              <div className="flex flex-wrap gap-2">
                <Badge className="metric-chip bg-cyan-500/10 text-cyan-700 hover:bg-cyan-500/10 dark:text-cyan-300">
                  Skill Intelligence Surface
                </Badge>
                <Badge className="metric-chip bg-primary/10 text-primary hover:bg-primary/10">
                  Create · Evaluate · Connect
                </Badge>
              </div>

              <div>
                <div className="workspace-kicker">Skill Studio</div>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 dark:text-white md:text-4xl">
                  把专业流程沉淀成可创建、可评估、可连接的技能资产。
                </h1>
                <p className="mt-3 max-w-3xl text-base leading-8 text-slate-600 dark:text-slate-300">
                  Skill Studio
                  面向领域专家，不只是生成一段 prompt，而是把规则、测试门槛、发布状态和技能图谱放进同一个工作台。
                </p>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <FlowStepCard
                  icon={GitBranchPlusIcon}
                  title="Create"
                  description="把触发条件、工作流程、阈值与反例整理成结构化技能包。"
                />
                <FlowStepCard
                  icon={CheckCircle2Icon}
                  title="Evaluate"
                  description="在同一工作台内完成结构校验、测试准备度和发布前复核。"
                />
                <FlowStepCard
                  icon={NetworkIcon}
                  title="Connect"
                  description="通过技能图谱查看技能关系、复用路径与启用状态。"
                />
              </div>

              <div className="flex flex-wrap gap-3">
                <Button asChild className="rounded-full">
                  <Link href={withMock("/workspace/skill-studio/new", isMock)}>
                    <MessageSquareIcon className="size-4" />
                    新建技能工作台线程
                  </Link>
                </Button>
                {featured ? (
                  <Button asChild variant="outline" className="rounded-full">
                    <Link
                      href={withMock(
                        `/workspace/skill-studio/${featured.threadId}`,
                        isMock,
                      )}
                    >
                      进入焦点工作台
                      <ArrowUpRightIcon className="size-4" />
                    </Link>
                  </Button>
                ) : null}
              </div>
            </div>

            <div className="control-panel p-5 md:p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="workspace-kicker">Skill Graph Snapshot</div>
                  <div className="mt-3 text-2xl font-semibold text-slate-950 dark:text-white">
                    让技能网络成为真正的视觉锚点。
                  </div>
                </div>
                <div className="rounded-2xl bg-primary/10 p-3 text-primary">
                  <BinaryIcon className="size-5" />
                </div>
              </div>

              <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
                SkillNet 的 create / evaluate / connect 逻辑在这里变成真实工作流，而不是停留在概念层。
              </p>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <StatPill label="技能" value={String(graphOverview.skillCount)} />
                <StatPill label="关系" value={String(graphOverview.edgeCount)} />
                <StatPill label="已启用" value={String(graphOverview.enabledCount)} />
                <StatPill label="自定义" value={String(graphOverview.customCount)} />
              </div>

              <div className="mt-5 space-y-3">
                <div className="text-sm font-semibold text-slate-950 dark:text-white">
                  关键关系
                </div>
                {graphOverview.topRelationships.length > 0 ? (
                  graphOverview.topRelationships.map((item) => (
                    <div
                      key={item.type}
                      className="flex items-center justify-between rounded-2xl border border-slate-200/80 bg-white/76 px-4 py-3 dark:border-slate-800/80 dark:bg-slate-950/42"
                    >
                      <span className="text-sm text-slate-700 dark:text-slate-300">
                        {item.label}
                      </span>
                      <Badge variant="outline">{item.count}</Badge>
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-300/80 bg-white/68 px-4 py-4 text-sm leading-6 text-slate-500 dark:border-slate-700/80 dark:bg-slate-950/35 dark:text-slate-400">
                    有可用技能后，这里会显示技能关系、复用强度和图谱连接状态。
                  </div>
                )}
              </div>
            </div>
          </div>
        </WorkspaceSurfaceCard>

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.08fr)_minmax(320px,0.92fr)]">
          <WorkspaceSurfaceCard className="min-h-0">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="workspace-kicker">Recent Workbenches</div>
                <div className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                  最近技能工作台
                </div>
                <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
                  左侧聚焦真实的工作线程，右侧高亮当前焦点技能和它的关系网络。
                </p>
              </div>
              <Badge className="metric-chip bg-slate-950 text-white hover:bg-slate-950 dark:bg-slate-100 dark:text-slate-950">
                {entries.length} 个工作台
              </Badge>
            </div>

            <div className="mt-5 space-y-4">
              {isLoading ? (
                <div className="rounded-[1.4rem] border border-slate-200/80 bg-white/72 px-5 py-8 text-sm text-slate-500 dark:border-slate-800/80 dark:bg-slate-950/48 dark:text-slate-400">
                  正在同步技能工作台线程...
                </div>
              ) : entries.length === 0 ? (
                <div className="rounded-[1.4rem] border border-dashed border-slate-300/80 bg-white/72 px-5 py-8 dark:border-slate-700/80 dark:bg-slate-950/42">
                  <div className="max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
                    当前还没有技能工作台线程。可以先创建一个线程，把领域规则、验收要求和反例交给专属技能创建器代理。
                  </div>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <Button asChild className="rounded-full">
                      <Link href={withMock("/workspace/skill-studio/new", isMock)}>
                        开始新线程
                      </Link>
                    </Button>
                    <Button asChild variant="outline" className="rounded-full">
                      <Link
                        href={withMock(
                          "/workspace/skill-studio/submarine-skill-studio-demo",
                          isMock,
                        )}
                      >
                        打开演示工作台
                      </Link>
                    </Button>
                  </div>
                </div>
              ) : (
                entries.map((entry) => (
                  <SkillWorkbenchCard
                    key={entry.threadId}
                    entry={entry}
                    isMock={isMock}
                  />
                ))
              )}
            </div>
          </WorkspaceSurfaceCard>

          <div className="grid gap-5">
            <WorkspaceSurfaceCard>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="workspace-kicker">Focused Workbench</div>
                  <div className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                    当前焦点技能
                  </div>
                </div>
                <div className="rounded-2xl bg-cyan-500/10 p-3 text-cyan-700 dark:text-cyan-300">
                  <WandSparklesIcon className="size-5" />
                </div>
              </div>

              {featured ? (
                <div className="mt-5 space-y-4">
                  <div>
                    <div className="text-lg font-semibold text-slate-950 dark:text-white">
                      {localizeWorkspaceDisplayText(featured.skillName)}
                    </div>
                    <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                      {localizeWorkspaceDisplayText(featured.title)}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline">{featured.assistantLabel}</Badge>
                    <Badge variant="outline">
                      {formatSkillStudioStatus(featured.validationStatus)}
                    </Badge>
                    <Badge variant="outline">
                      {formatSkillStudioStatus(featured.testStatus)}
                    </Badge>
                    <Badge variant="outline">
                      {formatSkillStudioStatus(featured.publishStatus)}
                    </Badge>
                    {featured.rollbackTargetId ? (
                      <Badge variant="outline">
                        回滚目标 {featured.rollbackTargetId}
                      </Badge>
                    ) : null}
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <StatPill label="错误" value={String(featured.errorCount)} />
                    <StatPill label="警告" value={String(featured.warningCount)} />
                    <StatPill label="产物" value={String(featured.artifactCount)} />
                    <StatPill label="Revisions" value={String(featured.revisionCount)} />
                    <StatPill label="Bindings" value={String(featured.bindingCount)} />
                    <StatPill
                      label="最近发布"
                      value={formatUpdatedAt(featured.lastPublishedAt)}
                    />
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <Button asChild className="rounded-full">
                      <Link
                        href={withMock(
                          `/workspace/skill-studio/${featured.threadId}`,
                          isMock,
                        )}
                      >
                        进入技能创建工作台
                      </Link>
                    </Button>
                    <Button asChild variant="outline" className="rounded-full">
                      <Link
                        href={withMock(`/workspace/chats/${featured.threadId}`, isMock)}
                      >
                        聊天视图
                      </Link>
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="mt-5 rounded-[1.2rem] border border-dashed border-slate-300/80 bg-white/72 px-4 py-5 text-sm leading-6 text-slate-500 dark:border-slate-700/80 dark:bg-slate-950/42 dark:text-slate-400">
                  创建第一条技能工作台线程后，这里会高亮最近的技能包、测试状态和治理入口。
                </div>
              )}
            </WorkspaceSurfaceCard>

            <WorkspaceSurfaceCard>
              <div className="workspace-kicker">Connected Skills</div>
              <div className="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
                与焦点技能相关的关系线索
              </div>
              <div className="mt-4 space-y-3">
                {featuredRelatedSkills.length > 0 ? (
                  featuredRelatedSkills.map((item) => (
                    <div
                      key={item.skillAssetId}
                      className="rounded-[1.2rem] border border-slate-200/80 bg-white/76 p-4 dark:border-slate-800/80 dark:bg-slate-950/42"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm font-semibold text-slate-950 dark:text-white">
                          {localizeWorkspaceDisplayText(item.skillName)}
                        </div>
                        <Badge variant="outline">
                          {item.strongestScore.toFixed(2)}
                        </Badge>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {item.relationshipLabels.map((label) => (
                          <Badge key={label} variant="outline">
                            {label}
                          </Badge>
                        ))}
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
                        <span className="metric-chip bg-slate-900 text-white hover:bg-slate-900 dark:bg-slate-100 dark:text-slate-950">
                          revisions {item.revisionCount}
                        </span>
                        <span className="metric-chip bg-white/80 text-slate-700 dark:bg-slate-900/70 dark:text-slate-200">
                          bindings {item.bindingCount}
                        </span>
                        {item.lastPublishedAt ? (
                          <span className="metric-chip bg-white/80 text-slate-700 dark:bg-slate-900/70 dark:text-slate-200">
                            最近发布 {formatUpdatedAt(item.lastPublishedAt)}
                          </span>
                        ) : null}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-[1.2rem] border border-dashed border-slate-300/80 bg-white/72 px-4 py-5 text-sm leading-6 text-slate-500 dark:border-slate-700/80 dark:bg-slate-950/42 dark:text-slate-400">
                    焦点技能产生图谱关系后，这里会展示关联技能和关系标签。
                  </div>
                )}
              </div>
            </WorkspaceSurfaceCard>
          </div>
        </div>
      </WorkspaceSurfaceMain>
    </WorkspaceSurfacePage>
  );
}

function FlowStepCard({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof GitBranchPlusIcon;
  title: string;
  description: string;
}) {
  return (
    <div className="control-panel p-5">
      <div className="rounded-2xl bg-cyan-500/10 p-3 text-cyan-700 dark:text-cyan-300">
        <Icon className="size-5" />
      </div>
      <div className="mt-4 text-base font-semibold text-slate-950 dark:text-white">
        {title}
      </div>
      <div className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
        {description}
      </div>
    </div>
  );
}

function SkillWorkbenchCard({
  entry,
  isMock,
}: {
  entry: SkillStudioDashboardEntry;
  isMock: boolean;
}) {
  return (
    <div className="control-panel p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="workspace-kicker">Workbench Thread</div>
          <div className="mt-2 text-lg font-semibold text-slate-950 dark:text-white">
            {localizeWorkspaceDisplayText(entry.skillName)}
          </div>
          <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {localizeWorkspaceDisplayText(entry.title)}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge variant="outline">{entry.assistantLabel}</Badge>
            <Badge variant="outline">
              {formatSkillStudioStatus(entry.validationStatus)}
            </Badge>
            <Badge variant="outline">
              {formatSkillStudioStatus(entry.testStatus)}
            </Badge>
            <Badge variant="outline">
              {formatSkillStudioStatus(entry.publishStatus)}
            </Badge>
            <Badge variant="outline">产物 {entry.artifactCount}</Badge>
            <Badge variant="outline">rev {entry.revisionCount}</Badge>
            <Badge variant="outline">bindings {entry.bindingCount}</Badge>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button asChild className="rounded-full" size="sm">
            <Link href={withMock(`/workspace/skill-studio/${entry.threadId}`, isMock)}>
              进入工作台
            </Link>
          </Button>
          <Button asChild size="sm" variant="outline" className="rounded-full">
            <Link href={withMock(`/workspace/chats/${entry.threadId}`, isMock)}>
              聊天视图
            </Link>
          </Button>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
        <span className="metric-chip bg-slate-900 text-white hover:bg-slate-900 dark:bg-slate-100 dark:text-slate-950">
          最近更新 {formatUpdatedAt(entry.updatedAt)}
        </span>
        {entry.lastPublishedAt ? (
          <span className="metric-chip bg-white/80 text-slate-700 dark:bg-slate-900/70 dark:text-slate-200">
            最近发布 {formatUpdatedAt(entry.lastPublishedAt)}
          </span>
        ) : null}
        {entry.rollbackTargetId ? (
          <span className="metric-chip bg-white/80 text-slate-700 dark:bg-slate-900/70 dark:text-slate-200">
            回滚目标 {entry.rollbackTargetId}
          </span>
        ) : null}
      </div>
    </div>
  );
}

function StatPill({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-[1.15rem] border border-slate-200/80 bg-white/76 px-4 py-3 dark:border-slate-800/80 dark:bg-slate-950/46">
      <div className="workspace-kicker">{label}</div>
      <div className="mt-2 text-base font-semibold text-slate-950 dark:text-white">
        {value}
      </div>
    </div>
  );
}
