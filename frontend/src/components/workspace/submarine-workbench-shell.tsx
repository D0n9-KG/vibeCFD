"use client";

import {
  BoxesIcon,
  ChevronRightIcon,
  FileTextIcon,
  GaugeIcon,
  LayoutPanelLeftIcon,
  RadarIcon,
} from "lucide-react";
import { useMemo, useState } from "react";

import { type PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { Button } from "@/components/ui/button";
import { useArtifactContent } from "@/core/artifacts/hooks";
import { useI18n } from "@/core/i18n/hooks";
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
  sendMessage: (
    threadId: string,
    message: PromptInputMessage,
  ) => Promise<void> | void;
  onStop: () => Promise<void>;
};

const SUBMARINE_WORKBENCH_VIEWS: Array<{
  id: SubmarineWorkbenchView;
  label: string;
  icon: typeof RadarIcon;
  note: string;
}> = [
  {
    id: "overview",
    label: "总览",
    icon: RadarIcon,
    note: "集中查看当前运行概况和下一步建议。",
  },
  {
    id: "runtime",
    label: "运行台",
    icon: GaugeIcon,
    note: "查看完整阶段状态、执行动态和中止控制。",
  },
  {
    id: "artifacts",
    label: "产物",
    icon: BoxesIcon,
    note: "按阶段汇总研究产物并快速打开。",
  },
  {
    id: "report",
    label: "报告",
    icon: FileTextIcon,
    note: "查看结论、交付判断和证据链。",
  },
];

const STAGE_LABELS: Record<string, string> = {
  "task-intelligence": "任务理解",
  "geometry-preflight": "几何预检",
  "solver-dispatch": "求解执行",
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
  verified_but_not_validated: "已验证未外部校核",
  validated_with_gaps: "已校核但仍有缺口",
  research_ready: "可用于科研结论",
  pending: "待判定",
};

function safeJsonParse<T>(content?: string | null): T | null {
  if (!content) return null;
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
  if (!value) return "等待研究";
  return REVIEW_STATUS_LABELS[value] ?? value;
}

function formatClaimLevel(value?: string | null) {
  if (!value) return "未评估";
  return CLAIM_LEVEL_LABELS[value] ?? value;
}

export function SubmarineWorkbenchShell({
  threadId,
  isNewThread,
  isUploading,
  isMock = false,
  chatOpen,
  className,
  sendMessage,
  onStop,
}: SubmarineWorkbenchShellProps) {
  const { t } = useI18n();
  const { thread } = useThread();
  const [activeView, setActiveView] =
    useState<SubmarineWorkbenchView>("overview");
  const [navOpen, setNavOpen] = useState(false);

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
      Array.isArray((runtime as { artifact_virtual_paths?: string[] }).artifact_virtual_paths)
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
  const runSummary =
    (runtime &&
      typeof runtime === "object" &&
      "runtime_summary" in runtime &&
      typeof runtime.runtime_summary === "string" &&
      runtime.runtime_summary) ||
    (runtime &&
      typeof runtime === "object" &&
      "task_summary" in runtime &&
      typeof runtime.task_summary === "string" &&
      runtime.task_summary) ||
    "运行推进后，这里会持续汇总实时求解信号、阶段状态和复核信息。";
  const localizedRunSummary = localizeWorkspaceDisplayText(runSummary);
  const localizedThreadTitle = localizeThreadDisplayTitle(
    thread.values.title ?? "潜艇工作台",
  );

  return (
    <div className={cn("min-h-0", className)}>
      <aside className="hidden min-h-0 flex-col overflow-hidden rounded-[28px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(248,250,252,0.96),rgba(255,255,255,0.96))] p-4 shadow-[0_18px_44px_rgba(15,23,42,0.07)] xl:flex">
        <div className="rounded-2xl border border-sky-100/80 bg-white/92 p-4 shadow-[0_16px_32px_rgba(14,165,233,0.10)]">
          <div className="text-[10px] font-semibold uppercase tracking-[0.24em] text-sky-600">
            任务驾驶舱
          </div>
          <div className="mt-2 text-lg font-semibold tracking-tight text-stone-900">
            {localizedThreadTitle}
          </div>
          <p className="mt-2 text-sm leading-6 text-stone-600">
            {localizedRunSummary}
          </p>
        </div>

        <div className="mt-4 grid gap-3">
          <WorkbenchMetricCard label="当前阶段" value={currentStageLabel} />
          <WorkbenchMetricCard
            label="复核状态"
            value={
              formatReviewStatus(
                runtime &&
                  typeof runtime === "object" &&
                  "review_status" in runtime &&
                  typeof runtime.review_status === "string"
                  ? runtime.review_status
                  : "awaiting_research",
              )
            }
          />
          <WorkbenchMetricCard
            label="结论级别"
            value={
              formatClaimLevel(
                runtime &&
                  typeof runtime === "object" &&
                  "allowed_claim_level" in runtime &&
                  typeof runtime.allowed_claim_level === "string"
                  ? runtime.allowed_claim_level
                  : "not_assessed",
              )
            }
          />
          <WorkbenchMetricCard label="产物数量" value={String(artifactCount)} />
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
                  "flex w-full items-start gap-3 rounded-2xl border px-3 py-3 text-left transition-colors",
                  isActive
                    ? "border-sky-200 bg-sky-50 text-sky-950 shadow-[0_10px_24px_rgba(14,165,233,0.12)]"
                    : "border-stone-200/80 bg-white/86 text-stone-700 hover:border-stone-300 hover:bg-white",
                )}
                onClick={() => setActiveView(view.id)}
              >
                <span
                  className={cn(
                    "mt-0.5 rounded-xl border p-2",
                    isActive
                      ? "border-sky-200 bg-white text-sky-700"
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
          <div
            className="rounded-full border border-stone-200 bg-white px-3 py-2 text-xs text-stone-500"
            aria-label={t.workspace.toggleChatRail}
          >
            {chatOpen ? "对话面板已展开" : "对话面板已收起"}
          </div>
        </div>

        {navOpen ? (
          <div className="mb-4 rounded-[28px] border border-stone-200/80 bg-white/96 p-4 shadow-[0_18px_44px_rgba(15,23,42,0.07)]">
            <div className="grid gap-3 sm:grid-cols-2">
              {SUBMARINE_WORKBENCH_VIEWS.map((view) => {
                const Icon = view.icon;
                const isActive = activeView === view.id;
                return (
                  <button
                    key={view.id}
                    type="button"
                    className={cn(
                      "rounded-2xl border px-3 py-3 text-left",
                      isActive
                        ? "border-sky-200 bg-sky-50 text-sky-950"
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
        {activeView !== "overview" ? (
          <div className="mb-4">
            <Button
              variant="outline"
              aria-label={t.workspace.backToOverview}
              onClick={() => setActiveView("overview")}
            >
              {t.workspace.backToOverview}
            </Button>
          </div>
        ) : null}

        {activeView === "overview" ? (
          <div className="flex h-full min-h-0 flex-col overflow-y-auto rounded-[28px] border border-stone-200/80 bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.10),_transparent_32%),linear-gradient(180deg,_rgba(255,255,255,0.98),_rgba(248,250,252,0.96))] p-5 shadow-[0_24px_64px_rgba(15,23,42,0.08)]">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div className="min-w-0 flex-1 space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-sky-100 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-700">
                    总览
                  </span>
                  <span className="rounded-full bg-stone-900 px-2.5 py-1 text-[11px] font-semibold text-white">
                    {currentStageLabel}
                  </span>
                </div>
                <div>
                  <h2 className="text-2xl font-semibold tracking-tight text-stone-900">
                    保持运行驾驶舱可见，同时不丢失真实的阶段上下文。
                  </h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600">
                    {localizedRunSummary}
                  </p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <OverviewTile label="当前阶段" value={currentStageLabel} />
                  <OverviewTile label="下一阶段" value={nextStageLabel} />
                  <OverviewTile
                    label="复核状态"
                    value={formatReviewStatus(
                      runtime &&
                        typeof runtime === "object" &&
                        "review_status" in runtime &&
                        typeof runtime.review_status === "string"
                        ? runtime.review_status
                        : "in_progress",
                    )}
                  />
                  <OverviewTile
                    label="结论级别"
                    value={formatClaimLevel(
                      runtime &&
                        typeof runtime === "object" &&
                        "allowed_claim_level" in runtime &&
                        typeof runtime.allowed_claim_level === "string"
                        ? runtime.allowed_claim_level
                        : "pending",
                    )}
                  />
                </div>
              </div>

              <div className="grid w-full gap-3 xl:w-[20rem]">
                <OverviewTile label="产物数量" value={String(artifactCount)} />
                <OverviewTile
                  label="消息数量"
                  value={String(thread.messages.length)}
                />
                <Button
                  className="justify-between"
                  onClick={() => setActiveView("runtime")}
                >
                  进入运行台
                  <ChevronRightIcon className="size-4" />
                </Button>
              </div>
            </div>

            <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
              <SummaryPanel
                eyebrow="产物"
                title="把分组证据收敛在一次跳转内查看"
                body={
                  artifactCount > 0
                    ? `当前线程已经挂载 ${artifactCount} 份潜艇领域产物，可直接进入分组查看。`
                    : "几何预检、求解执行或结果整理完成后，这里会集中出现对应产物。"
                }
                actionLabel="打开产物"
                onAction={() => setActiveView("artifacts")}
              />
              <SummaryPanel
                eyebrow="报告"
                title="把交付判断和证据链放进独立审阅界面"
                body={reportSummary}
                actionLabel="查看报告"
                onAction={() => setActiveView("report")}
              />
            </div>
          </div>
        ) : null}

        {activeView === "runtime" ? (
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
        ) : null}

        {activeView === "artifacts" ? (
            <FocusedWorkbenchPanel
              eyebrow="产物"
              title="在专用工作台里查看分组产物"
              body="不用退回对话视图，也能直接审阅导出的数据文件、说明文档、图表和求解载荷。"
            >
            <SubmarineRuntimePanel threadId={threadId} />
          </FocusedWorkbenchPanel>
        ) : null}

        {activeView === "report" ? (
            <FocusedWorkbenchPanel
              eyebrow="报告"
              title="报告审阅与实时运行驾驶舱保持分离"
              body="在这个界面集中检查交付定稿口径、证据轨迹和最终判断，不打断实时运行视图。"
            >
            <SubmarineRuntimePanel threadId={threadId} />
          </FocusedWorkbenchPanel>
        ) : null}
      </section>
    </div>
  );
}

function WorkbenchMetricCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-stone-200/80 bg-white/88 px-3 py-3 shadow-[0_12px_28px_rgba(15,23,42,0.05)]">
      <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-stone-400">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-stone-800">{value}</div>
    </div>
  );
}

function OverviewTile({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-stone-200/80 bg-white/88 px-4 py-3 shadow-[0_14px_30px_rgba(15,23,42,0.05)]">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-400">
        {label}
      </div>
      <div className="mt-2 text-sm font-semibold leading-6 text-stone-800">
        {value}
      </div>
    </div>
  );
}

function SummaryPanel({
  eyebrow,
  title,
  body,
  actionLabel,
  onAction,
}: {
  eyebrow: string;
  title: string;
  body: string;
  actionLabel: string;
  onAction: () => void;
}) {
  return (
    <div className="rounded-[28px] border border-stone-200/80 bg-white/94 p-5 shadow-[0_18px_44px_rgba(15,23,42,0.06)]">
      <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-sky-600">
        {eyebrow}
      </div>
      <div className="mt-2 text-lg font-semibold tracking-tight text-stone-900">
        {title}
      </div>
      <p className="mt-2 text-sm leading-6 text-stone-600">{body}</p>
      <Button className="mt-4" variant="outline" onClick={onAction}>
        {actionLabel}
      </Button>
    </div>
  );
}

function FocusedWorkbenchPanel({
  eyebrow,
  title,
  body,
  children,
}: {
  eyebrow: string;
  title: string;
  body: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <div className="rounded-[28px] border border-stone-200/80 bg-white/94 p-5 shadow-[0_18px_44px_rgba(15,23,42,0.06)]">
        <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-sky-600">
          {eyebrow}
        </div>
        <div className="mt-2 text-lg font-semibold tracking-tight text-stone-900">
          {title}
        </div>
        <p className="mt-2 text-sm leading-6 text-stone-600">{body}</p>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
    </div>
  );
}
