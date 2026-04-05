"use client";

import {
  ActivityIcon,
  ArrowUpRightIcon,
  BoxesIcon,
  FileTextIcon,
  GaugeIcon,
  MessageSquareTextIcon,
  RadarIcon,
  ShieldCheckIcon,
  WavesIcon,
} from "lucide-react";
import { type ReactNode, useMemo, useState } from "react";

import { type PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { Button } from "@/components/ui/button";
import { useArtifactContent } from "@/core/artifacts/hooks";
import {
  localizeThreadDisplayTitle,
  localizeWorkspaceDisplayText,
} from "@/core/i18n/workspace-display";
import { cn } from "@/lib/utils";

import { useThread } from "./messages/context";
import { SubmarinePipeline } from "./submarine-pipeline";
import {
  getSubmarineDisplayedNextStage,
  getSubmarineDisplayedStage,
} from "./submarine-pipeline-runs";
import { SubmarineRuntimePanel } from "./submarine-runtime-panel";
import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
} from "./submarine-runtime-panel.contract";

type SubmarineWorkbenchView = "overview" | "runtime" | "artifacts" | "report";

type SubmarineWorkbenchShellProps = {
  threadId: string;
  isNewThread: boolean;
  isUploading: boolean;
  isMock?: boolean;
  chatOpen: boolean;
  className?: string;
  onOpenChat: () => void;
  sendMessage: (
    threadId: string,
    message: PromptInputMessage,
  ) => Promise<void> | void;
  onStop: () => Promise<void>;
};

const SUBMARINE_WORKBENCH_VIEWS: Array<{
  id: SubmarineWorkbenchView;
  label: string;
  shortLabel: string;
  icon: typeof RadarIcon;
  note: string;
}> = [
  {
    id: "overview",
    label: "总览",
    shortLabel: "总览",
    icon: RadarIcon,
    note: "先判断当前阶段和下一步，再决定要不要进入细节面板。",
  },
  {
    id: "runtime",
    label: "阶段",
    shortLabel: "阶段",
    icon: GaugeIcon,
    note: "查看完整阶段卡片、运行状态、阻塞项和推进路径。",
  },
  {
    id: "artifacts",
    label: "产物",
    shortLabel: "产物",
    icon: BoxesIcon,
    note: "按阶段审阅文件、图表、日志和导出结果。",
  },
  {
    id: "report",
    label: "报告",
    shortLabel: "报告",
    icon: FileTextIcon,
    note: "集中处理结论、交付判断、风险和复现说明。",
  },
];

const STAGE_LABELS: Record<string, string> = {
  "task-intelligence": "任务理解",
  "geometry-preflight": "几何预检",
  "solver-dispatch": "求解派发",
  "result-reporting": "结果整理",
  "supervisor-review": "主管复核",
  "user-confirmation": "用户确认",
};

const REVIEW_STATUS_LABELS: Record<string, string> = {
  awaiting_research: "等待研究",
  in_progress: "进行中",
  ready_for_supervisor: "待主管复核",
  needs_user_confirmation: "待用户确认",
  completed: "已完成",
  blocked: "已阻塞",
};

const CLAIM_LEVEL_LABELS: Record<string, string> = {
  not_assessed: "未评估",
  delivery_only: "仅交付",
  verified_but_not_validated: "已验证未外部核验",
  validated_with_gaps: "已核验但存在缺口",
  research_ready: "可用于科研结论",
  pending: "待判定",
};

function safeJsonParse<T>(content?: string | null): T | null {
  if (!content) {
    return null;
  }

  try {
    return JSON.parse(content) as T;
  } catch {
    return null;
  }
}

function summarizeReport(report: SubmarineFinalReportPayload | null) {
  const summarySource = report as
    | (SubmarineFinalReportPayload & {
        delivery_decision_summary?: string;
        conclusion?: string;
        summary_zh?: string;
      })
    | null;

  const candidateSummaries = [
    summarySource?.delivery_decision_summary,
    summarySource?.conclusion,
    summarySource?.summary_zh,
  ].filter((value): value is string => Boolean(value));

  return candidateSummaries[0] ?? "尚未生成综合报告摘要。";
}

function formatReviewStatus(value?: string | null) {
  if (!value) {
    return "等待研究";
  }
  return REVIEW_STATUS_LABELS[value] ?? value;
}

function formatClaimLevel(value?: string | null) {
  if (!value) {
    return "未评估";
  }
  return CLAIM_LEVEL_LABELS[value] ?? value;
}

export function SubmarineWorkbenchShell({
  threadId,
  isNewThread,
  isUploading,
  isMock = false,
  chatOpen,
  className,
  onOpenChat,
  sendMessage,
  onStop,
}: SubmarineWorkbenchShellProps) {
  const { thread } = useThread();
  const [activeView, setActiveView] =
    useState<SubmarineWorkbenchView>("overview");

  const runtime =
    thread.values.submarine_runtime &&
    typeof thread.values.submarine_runtime === "object"
      ? thread.values.submarine_runtime
      : null;

  const submarineArtifacts = useMemo(() => {
    const threadArtifacts = Array.isArray(thread.values.artifacts)
      ? thread.values.artifacts
      : [];
    const runtimeArtifacts =
      runtime &&
      typeof runtime === "object" &&
      Array.isArray(
        (runtime as { artifact_virtual_paths?: string[] }).artifact_virtual_paths,
      )
        ? (runtime as { artifact_virtual_paths: string[] }).artifact_virtual_paths
        : [];

    return [...threadArtifacts, ...runtimeArtifacts].filter(
      (artifact, index, list) =>
        typeof artifact === "string" &&
        artifact.includes("/submarine/") &&
        list.indexOf(artifact) === index,
    );
  }, [runtime, thread.values.artifacts]);

  const designBriefJson = submarineArtifacts.find((artifact) =>
    artifact.endsWith("/cfd-design-brief.json"),
  );
  const finalReportJson = submarineArtifacts.find((artifact) =>
    artifact.endsWith("/final-report.json"),
  );

  const { content: designBriefContent } = useArtifactContent({
    filepath: designBriefJson ?? "",
    threadId,
    enabled: Boolean(designBriefJson),
  });
  const { content: finalReportContent } = useArtifactContent({
    filepath: finalReportJson ?? "",
    threadId,
    enabled: Boolean(finalReportJson),
  });

  const designBrief = useMemo(
    () => safeJsonParse<SubmarineDesignBriefPayload>(designBriefContent),
    [designBriefContent],
  );
  const finalReport = useMemo(
    () => safeJsonParse<SubmarineFinalReportPayload>(finalReportContent),
    [finalReportContent],
  );

  const displayedStage = useMemo(
    () => getSubmarineDisplayedStage(runtime, designBrief),
    [designBrief, runtime],
  );
  const displayedNextStage = useMemo(
    () => getSubmarineDisplayedNextStage(runtime, designBrief),
    [designBrief, runtime],
  );

  const currentStageLabel = displayedStage
    ? STAGE_LABELS[displayedStage] ?? displayedStage
    : "等待任务简报";
  const nextStageLabel = displayedNextStage
    ? STAGE_LABELS[displayedNextStage] ?? displayedNextStage
    : "等待运行态更新";
  const artifactCount = submarineArtifacts.length;
  const reportSummary = summarizeReport(finalReport);
  const reviewStatus = formatReviewStatus(
    runtime &&
      typeof runtime === "object" &&
      "review_status" in runtime &&
      typeof runtime.review_status === "string"
      ? runtime.review_status
      : "awaiting_research",
  );
  const claimLevel = formatClaimLevel(
    runtime &&
      typeof runtime === "object" &&
      "allowed_claim_level" in runtime &&
      typeof runtime.allowed_claim_level === "string"
      ? runtime.allowed_claim_level
      : "not_assessed",
  );
  const runtimeSummaryText =
    runtime &&
    typeof runtime === "object" &&
    "runtime_summary" in runtime &&
    typeof runtime.runtime_summary === "string"
      ? runtime.runtime_summary
      : undefined;
  const taskSummaryText =
    runtime &&
    typeof runtime === "object" &&
    "task_summary" in runtime &&
    typeof runtime.task_summary === "string"
      ? runtime.task_summary
      : undefined;
  const runSummary =
    runtimeSummaryText ??
    taskSummaryText ??
    "任务启动后，这里会持续汇总阶段状态、求解上下文与主管复核信号。";
  const localizedRunSummary = localizeWorkspaceDisplayText(runSummary);
  const localizedThreadTitle = localizeThreadDisplayTitle(
    thread.values.title ?? "潜艇仿真任务",
  );
  const collaborationStatus = chatOpen ? "对话侧栏已展开" : "对话侧栏已收起";

  if (isNewThread) {
    return (
      <section className="min-w-0 rounded-[32px] border border-slate-200/80 bg-[radial-gradient(circle_at_top_right,rgba(56,189,248,0.12),transparent_22%),radial-gradient(circle_at_82%_14%,rgba(249,115,22,0.08),transparent_12%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(246,249,252,0.98))] p-5 shadow-[0_24px_60px_rgba(15,23,42,0.08)] md:p-6 xl:p-7">
        <div className="workspace-kicker text-sky-700">任务定义</div>
        <div className="mt-4 grid gap-5 xl:grid-cols-[minmax(0,1.28fr)_320px]">
          <div className="space-y-5">
            <section className="rounded-[28px] border border-slate-200/80 bg-white/92 p-5 shadow-[0_18px_40px_rgba(15,23,42,0.06)] md:p-6">
              <h2 className="text-2xl font-semibold tracking-tight text-slate-950 xl:text-[2.1rem]">
                明确本次 CFD 分析目标与判定问题
              </h2>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700">
                新建线程首屏仅保留任务定义所需信息，不再提前展开阶段卡片与证据面板。请先明确分析目标、工况条件、评价指标与约束要求，右侧协作区会据此生成可执行的仿真任务。
              </p>

              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <OverviewStat
                  label="协作输入区"
                  value={chatOpen ? "已展开，可直接录入" : "点击后展开"}
                />
                <OverviewStat label="流程路径" value="目标 → 工况 → 约束" />
                <OverviewStat label="交付产出" value="图表、证据、报告" />
              </div>
            </section>

            <section className="rounded-[28px] border border-slate-200/80 bg-white/90 p-5 shadow-[0_16px_34px_rgba(15,23,42,0.05)] md:p-6">
              <div className="workspace-kicker text-sky-700">关键信息</div>
              <h3 className="mt-3 text-lg font-semibold tracking-tight text-slate-950">
                请先提供以下信息
              </h3>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <StartStep
                  index="01"
                  title="任务对象"
                  description="对象是什么，场景是什么，这次仿真到底想回答哪个工程问题。"
                />
                <StartStep
                  index="02"
                  title="工况条件"
                  description="速度、介质、边界条件、姿态或关键运行区间，至少给出你已知的部分。"
                />
                <StartStep
                  index="03"
                  title="关注指标"
                  description="压降、阻力、流场分布、热点区域、风险点或你最关心的判断指标。"
                />
                <StartStep
                  index="04"
                  title="约束条件"
                  description="时间、精度、算力、几何质量、交付形式，哪些是必须遵守的限制。"
                />
              </div>

              <div className="mt-5 rounded-[24px] border border-sky-200/80 bg-sky-50/70 p-4">
                <div className="text-sm font-semibold text-slate-950">
                  输入模板
                </div>
                <p className="mt-2 text-sm leading-7 text-slate-700">
                  “我要对某个对象在某种工况下做 CFD，重点看哪些指标，当前限制是时间、精度或算力。”
                </p>
                <div className="mt-4 flex flex-wrap gap-3">
                  <Button className="min-w-[180px]" onClick={onOpenChat}>
                    填写任务说明
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
              icon={GaugeIcon}
              title="流程概览"
              body="任务理解 → 几何预检 → 求解派发"
              note="在任务定义完成后，系统才会将你引导至后续阶段面板。"
            />
            <FocusCard
              icon={BoxesIcon}
              title="工作台启用条件"
              body="待阶段状态、图表与证据产物生成后，再进入阶段、产物和报告视图。"
              note="这样可以避免在首屏同时堆叠判断信息与交付信息。"
            />
            <FocusCard
              icon={MessageSquareTextIcon}
              title="协作状态"
              body={collaborationStatus}
              note="建议先在右侧输入任务说明，再进入具体工作台视图。"
            />
          </div>
        </div>
      </section>
    );
  }

  return (
    <div className="submarine-workbench-frame min-h-0">
      <div className={cn("submarine-workbench-shell min-h-0", className)}>
      <aside className="submarine-workbench-shell__mission-rail hidden min-h-0 flex-col overflow-hidden rounded-[30px] border border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(243,247,251,0.98))] p-4 text-slate-950 shadow-[0_24px_64px_rgba(15,23,42,0.08)] xl:flex">
        <div className="rounded-[24px] border border-sky-200/80 bg-[radial-gradient(circle_at_top_left,rgba(56,189,248,0.16),transparent_32%),linear-gradient(180deg,rgba(240,249,255,0.96),rgba(255,255,255,0.98))] p-4 shadow-[0_14px_34px_rgba(56,189,248,0.10)]">
          <div className="text-[10px] font-semibold uppercase tracking-[0.24em] text-sky-700/80">
            Mission Rail
          </div>
          <div className="mt-2 text-lg font-semibold tracking-tight text-slate-950">
            {localizedThreadTitle}
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            把当前阶段、下一步和复核状态固定在同一条轨道里，避免被次要信息打散。
          </p>
        </div>

        <div className="mt-4 grid gap-3">
          <RailStat label="Current" value={currentStageLabel} tone="sky" />
          <RailStat label="Next" value={nextStageLabel} />
          <RailStat label="Review" value={reviewStatus} />
        </div>

        <nav className="mt-4 flex-1 space-y-2">
          {SUBMARINE_WORKBENCH_VIEWS.map((view) => {
            const Icon = view.icon;
            const isActive = activeView === view.id;

            return (
              <button
                key={view.id}
                type="button"
                className={cn(
                  "flex w-full items-start gap-3 rounded-2xl border px-3 py-3 text-left transition-all",
                  isActive
                    ? "border-sky-200/90 bg-sky-50/95 text-slate-950 shadow-[0_12px_24px_rgba(14,165,233,0.10)]"
                    : "border-slate-200/80 bg-white/84 text-slate-600 hover:border-slate-300 hover:bg-white",
                )}
                onClick={() => setActiveView(view.id)}
              >
                <span
                  className={cn(
                    "mt-0.5 rounded-xl border p-2",
                    isActive
                      ? "border-sky-200/80 bg-white text-sky-700"
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
        <div className="mb-4 rounded-[32px] border border-slate-200/80 bg-[radial-gradient(circle_at_top_right,rgba(56,189,248,0.12),transparent_24%),radial-gradient(circle_at_88%_18%,rgba(251,146,60,0.10),transparent_14%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(245,248,252,0.98))] p-5 shadow-[0_24px_60px_rgba(15,23,42,0.08)]">
          <div className="workspace-kicker text-sky-700">Submarine Cockpit</div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950 xl:text-[2.05rem]">
            先确认当前阶段，再决定要不要进入细节面板
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700">
            这块区域只保留最重要的判断信息，不再把阶段、证据、报告和协作状态同时平铺成一整面仪表盘。
          </p>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <OverviewStat label="当前阶段" value={currentStageLabel} />
            <OverviewStat label="下一步" value={nextStageLabel} />
            <OverviewStat label="复核状态" value={reviewStatus} />
            <OverviewStat label="证据等级" value={claimLevel} />
          </div>

          <div className="mt-5 flex gap-2 overflow-x-auto xl:hidden">
            {SUBMARINE_WORKBENCH_VIEWS.map((view) => {
              const Icon = view.icon;
              const isActive = activeView === view.id;

              return (
                <button
                  key={view.id}
                  type="button"
                  className={cn(
                    "flex shrink-0 items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-all",
                    isActive
                      ? "border-sky-200/90 bg-sky-50/95 text-sky-700"
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
          <div className="submarine-workbench-shell__overview-grid grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_340px]">
            <section className="workspace-surface-card overflow-hidden p-0">
              <div className="submarine-workbench-shell__focus-grid grid h-full xl:grid-cols-[250px_minmax(0,1fr)]">
                <div className="submarine-workbench-shell__focus-rail border-b border-slate-200/80 bg-[linear-gradient(180deg,rgba(240,249,255,0.96),rgba(248,250,252,0.98))] p-5 xl:border-b-0 xl:border-r xl:border-slate-200/80">
                  <div className="workspace-kicker text-sky-700">Focus Rail</div>
                  <h3 className="mt-3 text-base font-semibold text-slate-950">
                    先看判断，再看细节
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    当前工作台优先回答三个问题：现在在哪个阶段、下一步是什么、证据是否足够继续推进。
                  </p>

                  <div className="mt-4 space-y-3">
                    <RailStat label="Current stage" value={currentStageLabel} tone="sky" />
                    <RailStat label="Next move" value={nextStageLabel} />
                    <RailStat label="Review gate" value={reviewStatus} />
                  </div>
                </div>

                <div className="p-5 md:p-6">
                  <div>
                    <h3 className="text-[1.45rem] font-semibold tracking-tight text-slate-950">
                      中央只保留主问题区
                    </h3>
                    <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700">
                      先确认任务目标、阶段摘要和复核门槛，只有确实需要深入时，再跳到阶段面板、产物面板或报告面板。
                    </p>
                  </div>

                  <div className="mt-5 grid gap-3 md:grid-cols-2">
                    <FocusCard
                      icon={WavesIcon}
                      title="任务上下文"
                      body={localizedThreadTitle}
                      note="线程标题应该直接回答这次仿真到底在判断什么。"
                    />
                    <FocusCard
                      icon={ActivityIcon}
                      title="运行摘要"
                      body={localizedRunSummary}
                      note="把当前阶段说明浓缩在这一块，不让用户到处找状态。"
                    />
                    <FocusCard
                      icon={ShieldCheckIcon}
                      title="复核门槛"
                      body={reviewStatus}
                      note="先知道能不能继续推进，再决定是否要补信息或重跑。"
                    />
                    <FocusCard
                      icon={MessageSquareTextIcon}
                      title="协作状态"
                      body={collaborationStatus}
                      note="对话轨道是辅助，不再抢主工作台的注意力。"
                    />
                  </div>
                </div>
              </div>
            </section>

            <div className="grid gap-4">
              <DockPanel
                eyebrow="Next"
                title="下一步操作"
                description="把动作入口集中到一列，减少用户在多个摘要卡之间来回扫视。"
              >
                <OperationRow
                  label="聊天轨道"
                  title={
                    chatOpen
                      ? "对话已展开，可以直接输入仿真目标"
                      : isNewThread
                        ? "先通过聊天描述你的 CFD 目标"
                        : "需要继续协作时重新打开聊天轨道"
                  }
                  cta={chatOpen ? "定位到聊天输入" : "打开聊天轨道"}
                  onAction={onOpenChat}
                />
                <OperationRow
                  label="阶段面板"
                  title="查看完整阶段卡片与阻塞项"
                  cta="打开阶段视图"
                  onAction={() => setActiveView("runtime")}
                />
                <OperationRow
                  label="证据面板"
                  title="按阶段审阅产物、图表和日志"
                  cta="打开产物视图"
                  onAction={() => setActiveView("artifacts")}
                />
                <OperationRow
                  label="报告面板"
                  title="集中检查结论、风险和交付判断"
                  cta="打开报告视图"
                  onAction={() => setActiveView("report")}
                />
              </DockPanel>

              <DockPanel
                eyebrow="Status"
                title="当前密度更低的摘要"
                description="只保留会影响判断的三项信息，其余内容放进对应面板。"
              >
                <DockItem label="产物数" value={String(artifactCount)} />
                <DockItem label="消息数" value={String(thread.messages.length)} />
                <DockItem label="报告摘要" value={reportSummary} multiline />
                <DockItem label="线程状态" value={isNewThread ? "新线程" : "已建立线程"} />
              </DockPanel>
            </div>
          </div>
        ) : null}

        {activeView === "runtime" ? (
          <WorkbenchViewFrame
            title="阶段视图"
            note="这里保留完整阶段信息，用于深挖状态、阻塞和执行细节。"
          >
            <SubmarinePipeline
              threadId={threadId}
              isNewThread={isNewThread}
              isUploading={isUploading}
              isMock={isMock}
              showChatRail={false}
              showSidebar={false}
              sendMessage={sendMessage}
              onStop={onStop}
            />
          </WorkbenchViewFrame>
        ) : null}

        {activeView === "artifacts" ? (
          <WorkbenchViewFrame
            title="证据视图"
            note="这里单独处理文件、图表、日志和导出结果，不再和总览信息混在一起。"
          >
            <SubmarineRuntimePanel threadId={threadId} />
          </WorkbenchViewFrame>
        ) : null}

        {activeView === "report" ? (
          <WorkbenchViewFrame
            title="报告视图"
            note="这里专门审阅结论、风险提示和交付判断，避免和阶段状态互相干扰。"
          >
            <SubmarineRuntimePanel threadId={threadId} />
          </WorkbenchViewFrame>
        ) : null}
      </section>
      </div>
    </div>
  );
}

function RailStat({
  label,
  value,
  tone = "slate",
}: {
  label: string;
  value: string;
  tone?: "slate" | "sky";
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border px-4 py-3 shadow-[0_10px_24px_rgba(15,23,42,0.04)]",
        tone === "sky"
          ? "border-sky-200/80 bg-sky-50/90"
          : "border-slate-200/80 bg-white/84",
      )}
    >
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
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

function FocusCard({
  icon: Icon,
  title,
  body,
  note,
}: {
  icon: typeof ActivityIcon;
  title: string;
  body: string;
  note: string;
}) {
  return (
    <section className="rounded-[24px] border border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.96))] p-4 shadow-[0_14px_30px_rgba(15,23,42,0.04)]">
      <div className="flex items-center gap-2">
        <div className="rounded-xl bg-sky-50 p-2 text-sky-700">
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
      <div className="workspace-kicker text-sky-700">{eyebrow}</div>
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
      <Button
        className="mt-4 w-full justify-between"
        variant="outline"
        onClick={onAction}
      >
        {cta}
        <ArrowUpRightIcon className="size-4" />
      </Button>
    </div>
  );
}

function DockItem({
  label,
  value,
  multiline = false,
}: {
  label: string;
  value: string;
  multiline?: boolean;
}) {
  return (
    <div className="rounded-[18px] border border-slate-200/80 bg-white/92 px-4 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
        {label}
      </div>
      <div
        className={cn(
          "mt-2 text-sm text-slate-800",
          multiline ? "leading-6" : "font-semibold",
        )}
      >
        {value}
      </div>
    </div>
  );
}

function WorkbenchViewFrame({
  title,
  note,
  children,
}: {
  title: string;
  note: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-0 flex-col gap-4">
      <section className="workspace-surface-card p-5 md:p-6">
        <div className="workspace-kicker text-sky-700">Focused Surface</div>
        <h3 className="mt-3 text-xl font-semibold tracking-tight text-slate-950">
          {title}
        </h3>
        <p className="mt-3 text-sm leading-7 text-slate-700">{note}</p>
      </section>
      <div className="min-h-0 flex-1 overflow-hidden">{children}</div>
    </div>
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
