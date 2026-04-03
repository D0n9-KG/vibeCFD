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
    label: "鎬昏",
    icon: RadarIcon,
    note: "Live monitor summary and next-action guidance.",
  },
  {
    id: "runtime",
    label: "杩愯鏃禶",
    icon: GaugeIcon,
    note: "Full stage cockpit, activity flow, and stop controls.",
  },
  {
    id: "artifacts",
    label: "浜х墿",
    icon: BoxesIcon,
    note: "Grouped research outputs and artifact access.",
  },
  {
    id: "report",
    label: "鎶ュ憡",
    icon: FileTextIcon,
    note: "Outcome framing, conclusions, and evidence trail.",
  },
];

const STAGE_LABELS: Record<string, string> = {
  "task-intelligence": "浠诲姟鐞嗚В",
  "geometry-preflight": "鍑犱綍棰勬",
  "solver-dispatch": "姹傝В鎵ц",
  "result-reporting": "缁撴灉鏁寸悊",
  "supervisor-review": "Supervisor 澶嶆牳",
  "user-confirmation": "鐢ㄦ埛纭",
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

  return candidateSummaries[0] ?? "No synthesized report summary yet.";
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
    : "绛夊緟 mission brief";
  const nextStageLabel = displayedNextStage
    ? STAGE_LABELS[displayedNextStage] ?? displayedNextStage
    : "Runtime update pending";
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
    "The cockpit will surface live solver and review signals here once the run advances.";

  return (
    <div className={cn("min-h-0", className)}>
      <aside className="hidden min-h-0 flex-col overflow-hidden rounded-[28px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(248,250,252,0.96),rgba(255,255,255,0.96))] p-4 shadow-[0_18px_44px_rgba(15,23,42,0.07)] xl:flex">
        <div className="rounded-2xl border border-sky-100/80 bg-white/92 p-4 shadow-[0_16px_32px_rgba(14,165,233,0.10)]">
          <div className="text-[10px] font-semibold uppercase tracking-[0.24em] text-sky-600">
            Mission cockpit
          </div>
          <div className="mt-2 text-lg font-semibold tracking-tight text-stone-900">
            {thread.values.title ?? "Submarine workbench"}
          </div>
          <p className="mt-2 text-sm leading-6 text-stone-600">{runSummary}</p>
        </div>

        <div className="mt-4 grid gap-3">
          <WorkbenchMetricCard label="current_stage" value={currentStageLabel} />
          <WorkbenchMetricCard
            label="review_status"
            value={
              runtime &&
              typeof runtime === "object" &&
              "review_status" in runtime &&
              typeof runtime.review_status === "string"
                ? runtime.review_status
                : "awaiting_research"
            }
          />
          <WorkbenchMetricCard
            label="allowed_claim_level"
            value={
              runtime &&
              typeof runtime === "object" &&
              "allowed_claim_level" in runtime &&
              typeof runtime.allowed_claim_level === "string"
                ? runtime.allowed_claim_level
                : "not_assessed"
            }
          />
          <WorkbenchMetricCard label="Artifacts" value={String(artifactCount)} />
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
            onClick={() => setNavOpen((open) => !open)}
          >
            <LayoutPanelLeftIcon className="size-4" />
            {navOpen ? "鏀惰捣鍒嗘爮" : "灞曞紑鍒嗘爮"}
          </Button>
          <div className="rounded-full border border-stone-200 bg-white px-3 py-2 text-xs text-stone-500">
            {chatOpen ? "鑱婂ぉ闈㈡澘宸插睍寮€" : "鑱婂ぉ闈㈡澘宸叉敹璧?"}
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
        {activeView === "overview" ? (
          <div className="flex h-full min-h-0 flex-col overflow-y-auto rounded-[28px] border border-stone-200/80 bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.10),_transparent_32%),linear-gradient(180deg,_rgba(255,255,255,0.98),_rgba(248,250,252,0.96))] p-5 shadow-[0_24px_64px_rgba(15,23,42,0.08)]">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div className="min-w-0 flex-1 space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-sky-100 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-700">
                    鎬昏
                  </span>
                  <span className="rounded-full bg-stone-900 px-2.5 py-1 text-[11px] font-semibold text-white">
                    {currentStageLabel}
                  </span>
                </div>
                <div>
                  <h2 className="text-2xl font-semibold tracking-tight text-stone-900">
                    Keep the operator cockpit visible without dropping the runtime truth.
                  </h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600">
                    {runSummary}
                  </p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <OverviewTile label="current_stage" value={currentStageLabel} />
                  <OverviewTile label="next_stage" value={nextStageLabel} />
                  <OverviewTile
                    label="review_status"
                    value={
                      runtime &&
                      typeof runtime === "object" &&
                      "review_status" in runtime &&
                      typeof runtime.review_status === "string"
                        ? runtime.review_status
                        : "in_progress"
                    }
                  />
                  <OverviewTile
                    label="allowed_claim_level"
                    value={
                      runtime &&
                      typeof runtime === "object" &&
                      "allowed_claim_level" in runtime &&
                      typeof runtime.allowed_claim_level === "string"
                        ? runtime.allowed_claim_level
                        : "pending"
                    }
                  />
                </div>
              </div>

              <div className="grid w-full gap-3 xl:w-[20rem]">
                <OverviewTile label="Artifacts" value={String(artifactCount)} />
                <OverviewTile
                  label="Messages"
                  value={String(thread.messages.length)}
                />
                <Button
                  className="justify-between"
                  onClick={() => setActiveView("runtime")}
                >
                  杩涘叆杩愯鏃禶
                  <ChevronRightIcon className="size-4" />
                </Button>
              </div>
            </div>

            <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
              <SummaryPanel
                eyebrow="Artifacts"
                title="Keep grouped evidence within one jump"
                body={
                  artifactCount > 0
                    ? `${artifactCount} submarine artifact(s) are already attached to this thread.`
                    : "Artifacts will appear here after the first geometry, solver, or reporting stage completes."
                }
                actionLabel="鎵撳紑浜х墿"
                onAction={() => setActiveView("artifacts")}
              />
              <SummaryPanel
                eyebrow="Report"
                title="Carry the decision story into its own review surface"
                body={reportSummary}
                actionLabel="鎵撳紑鎶ュ憡"
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
            eyebrow="浜х墿"
            title="Grouped artifact access stays in the dedicated workbench surface."
            body="Review exported JSON, markdown, figures, and solver payloads without collapsing back into the chat-first runtime view."
          >
            <SubmarineRuntimePanel threadId={threadId} />
          </FocusedWorkbenchPanel>
        ) : null}

        {activeView === "report" ? (
          <FocusedWorkbenchPanel
            eyebrow="鎶ュ憡"
            title="Report review stays separate from the live stage cockpit."
            body="Use this surface to inspect delivery framing, evidence traces, and the final decision story while preserving the runtime cockpit as its own mode."
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
