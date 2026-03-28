"use client";

import {
  ArrowUpRightIcon,
  ClipboardCheckIcon,
  MessageSquareIcon,
  SparklesIcon,
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
import { useSkillGraph } from "@/core/skills/hooks";
import { useThreads } from "@/core/threads/hooks";
import { env } from "@/env";

import {
  buildSkillStudioEntries,
  type SkillStudioDashboardEntry,
} from "./skill-studio-dashboard.utils";
import { formatSkillStudioStatus } from "./skill-studio-workbench.utils";

function withMock(path: string, isMock: boolean) {
  return env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" || isMock
    ? `${path}?mock=true`
    : path;
}

function formatUpdatedAt(value: string | null) {
  if (!value) return "Unknown";
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
  const { data: threads = [], isLoading } = useThreads(undefined, isMock);
  const entries = buildSkillStudioEntries(threads);
  const featured = entries[0] ?? null;
  const { data: globalSkillGraph } = useSkillGraph({ isMock });
  const { data: featuredSkillGraph } = useSkillGraph({
    isMock,
    skillName: featured?.skillName,
    enabled: Boolean(featured?.skillName),
  });
  const graphOverview = buildSkillGraphOverview(globalSkillGraph);
  const featuredRelatedSkills = buildFocusedSkillGraphItems(
    featuredSkillGraph,
  ).slice(0, 4);

  return (
    <div className="flex size-full flex-col">
      <div className="flex items-center justify-between border-b px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold">Skill Studio</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            为领域专家提供独立的 Skill Creator 工作台，在 DeerFlow 内完成技能起草、校验、测试和发布前复核。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="outline">
            <Link href={withMock("/workspace/skill-studio/new", isMock)}>
              <MessageSquareIcon className="size-4" />
              新建 Skill Studio 线程
            </Link>
          </Button>
          {featured ? (
            <Button asChild>
              <Link
                href={withMock(
                  `/workspace/skill-studio/${featured.threadId}`,
                  isMock,
                )}
              >
                <ArrowUpRightIcon className="size-4" />
                进入最近工作台
              </Link>
            </Button>
          ) : null}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(340px,0.85fr)]">
          <section className="space-y-6">
            <div className="rounded-2xl border bg-muted/20 p-5">
              <div className="mb-3 flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
                <SparklesIcon className="size-4" />
                Studio workflow
              </div>
              <div className="grid gap-4 lg:grid-cols-3">
                <WorkflowCard
                  title="专家输入规则"
                  description="领域专家只需要把触发条件、workflow、阈值、反例和验收要求告诉右侧的 Skill Creator 代理。"
                />
                <WorkflowCard
                  title="Claude 整理技能包"
                  description="系统沉淀 SKILL.md、UI metadata、领域规则、测试矩阵和发布就绪信息，而不是只给一段聊天回复。"
                />
                <WorkflowCard
                  title="直接验证与测试"
                  description="同一工作台内查看结构校验、场景测试准备度和发布门槛，不再跳回 vibe CFD 工作台。"
                />
              </div>
            </div>

            <div className="rounded-2xl border bg-muted/20 p-5">
              <div className="mb-4 flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
                <WandSparklesIcon className="size-4" />
                Recent workbenches
              </div>
              {isLoading ? (
                <div className="text-sm text-muted-foreground">加载中...</div>
              ) : entries.length === 0 ? (
                <div className="rounded-xl border border-dashed bg-background/50 p-4">
                  <div className="text-sm text-muted-foreground">
                    当前还没有 Skill Studio 线程。你可以先开一个新线程，让专属 Skill Creator 代理与领域专家一起起草第一份专业 skill。
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Button asChild size="sm">
                      <Link href={withMock("/workspace/skill-studio/new", isMock)}>
                        开始新线程
                      </Link>
                    </Button>
                    <Button asChild size="sm" variant="outline">
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
                <div className="space-y-3">
                  {entries.map((entry) => (
                    <SkillStudioEntryCard
                      key={entry.threadId}
                      entry={entry}
                      isMock={isMock}
                    />
                  ))}
                </div>
              )}
            </div>
          </section>

          <aside className="space-y-6">
            <div className="rounded-2xl border bg-muted/20 p-5">
              <div className="mb-4 flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
                <ClipboardCheckIcon className="size-4" />
                Featured workbench
              </div>
              {featured ? (
                <div className="space-y-4">
                  <div>
                    <div className="text-lg font-semibold text-foreground">
                      {featured.skillName}
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      {featured.title}
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline">{featured.assistantMode}</Badge>
                    <Badge variant="outline">
                      {formatSkillStudioStatus(featured.validationStatus)}
                    </Badge>
                    <Badge variant="outline">
                      {formatSkillStudioStatus(featured.testStatus)}
                    </Badge>
                    <Badge variant="outline">
                      {formatSkillStudioStatus(featured.publishStatus)}
                    </Badge>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <MiniStat label="Errors" value={String(featured.errorCount)} />
                    <MiniStat label="Warnings" value={String(featured.warningCount)} />
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <MiniStat
                      label="Artifacts"
                      value={String(featured.artifactCount)}
                    />
                    <MiniStat
                      label="Updated"
                      value={formatUpdatedAt(featured.updatedAt)}
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button asChild className="flex-1 sm:flex-none">
                      <Link
                        href={withMock(
                          `/workspace/skill-studio/${featured.threadId}`,
                          isMock,
                        )}
                      >
                        进入 Skill Creator 工作台
                      </Link>
                    </Button>
                    <Button asChild variant="outline" className="flex-1 sm:flex-none">
                      <Link
                        href={withMock(`/workspace/chats/${featured.threadId}`, isMock)}
                      >
                        聊天视图
                      </Link>
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">
                  创建第一条 Skill Studio 线程后，这里会高亮最近的技能包和测试状态。
                </div>
              )}
            </div>

            <div className="rounded-2xl border bg-muted/20 p-5">
              <div className="mb-4 flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
                <SparklesIcon className="size-4" />
                Skill graph governance
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <MiniStat label="Skills" value={String(graphOverview.skillCount)} />
                <MiniStat label="Edges" value={String(graphOverview.edgeCount)} />
                <MiniStat
                  label="Enabled"
                  value={String(graphOverview.enabledCount)}
                />
                <MiniStat
                  label="Custom"
                  value={String(graphOverview.customCount)}
                />
              </div>
              <div className="mt-4 space-y-3">
                <div className="text-sm font-medium text-foreground">
                  Top relationships
                </div>
                {graphOverview.topRelationships.length > 0 ? (
                  graphOverview.topRelationships.map((item) => (
                    <div
                      key={item.type}
                      className="flex items-center justify-between rounded-xl border bg-background/70 px-3 py-2"
                    >
                      <span className="text-sm text-foreground">{item.label}</span>
                      <Badge variant="outline">{item.count}</Badge>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-muted-foreground">
                    Relationship analysis appears after skills are available.
                  </div>
                )}
              </div>
              {featuredRelatedSkills.length > 0 ? (
                <div className="mt-4 space-y-3">
                  <div className="text-sm font-medium text-foreground">
                    Related to featured skill
                  </div>
                  {featuredRelatedSkills.map((item) => (
                    <div
                      key={item.skillName}
                      className="rounded-xl border bg-background/70 p-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm font-medium text-foreground">
                          {item.skillName}
                        </div>
                        <Badge variant="outline">
                          {item.strongestScore.toFixed(2)}
                        </Badge>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {item.relationshipLabels.map((label) => (
                          <Badge key={label} variant="outline">
                            {label}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>

            <div className="rounded-2xl border bg-muted/20 p-5">
              <div className="mb-4 text-sm font-medium text-foreground">
                这块和 vibe CFD 的区别
              </div>
              <ul className="space-y-2 text-sm leading-6 text-muted-foreground">
                <li>中间工作台只看技能包、校验、测试和发布，不混入 CFD run 结果。</li>
                <li>右侧聊天只服务专属 Skill Creator 代理，而不是主工作区的通用协作聊天。</li>
                <li>目标是让领域专家持续生产专业 skill，而不是临时生成一段 prompt。</li>
              </ul>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

function WorkflowCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border bg-background/70 p-4">
      <div className="text-sm font-medium text-foreground">{title}</div>
      <div className="mt-2 text-sm leading-6 text-muted-foreground">
        {description}
      </div>
    </div>
  );
}

function SkillStudioEntryCard({
  entry,
  isMock,
}: {
  entry: SkillStudioDashboardEntry;
  isMock: boolean;
}) {
  return (
    <div className="rounded-xl border bg-background/70 p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="text-sm font-medium text-foreground">
            {entry.skillName}
          </div>
          <div className="mt-1 text-sm text-muted-foreground">{entry.title}</div>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge variant="outline">{entry.assistantMode}</Badge>
            <Badge variant="outline">
              {formatSkillStudioStatus(entry.validationStatus)}
            </Badge>
            <Badge variant="outline">
              {formatSkillStudioStatus(entry.testStatus)}
            </Badge>
            <Badge variant="outline">
              {formatSkillStudioStatus(entry.publishStatus)}
            </Badge>
            <Badge variant="outline">Artifacts {entry.artifactCount}</Badge>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild size="sm">
            <Link
              href={withMock(`/workspace/skill-studio/${entry.threadId}`, isMock)}
            >
              进入工作台
            </Link>
          </Button>
          <Button asChild size="sm" variant="outline">
            <Link href={withMock(`/workspace/chats/${entry.threadId}`, isMock)}>
              聊天视图
            </Link>
          </Button>
        </div>
      </div>
      <div className="mt-3 text-xs text-muted-foreground">
        最近更新：{formatUpdatedAt(entry.updatedAt)}
      </div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border bg-background/70 p-3">
      <div className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 text-lg font-semibold text-foreground">{value}</div>
    </div>
  );
}
