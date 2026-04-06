"use client";

import { MessageSquareIcon, RadarIcon } from "lucide-react";
import { type ReactNode, useMemo } from "react";

import { Button } from "@/components/ui/button";
import {
  NegotiationRail,
  SessionSummaryBar,
  ThreadHeader,
  WORKBENCH_COPY,
  WorkbenchShell,
} from "@/components/workspace/agentic-workbench";
import { useArtifactContent } from "@/core/artifacts/hooks";
import { cn } from "@/lib/utils";

import { useThread } from "../messages/context";
import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "../submarine-runtime-panel.contract";

import { buildSubmarineDetailModel } from "./submarine-detail-model";
import { SubmarineResearchCanvas } from "./submarine-research-canvas";
import { buildSubmarineSessionModel } from "./submarine-session-model";

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

type SubmarineAgenticWorkbenchProps = {
  threadId: string;
  isNewThread: boolean;
  showChatRail: boolean;
  onToggleChatRail: () => void;
  onOpenChat: () => void;
  negotiationContent: ReactNode;
  headerActions?: ReactNode;
};

export function SubmarineAgenticWorkbench({
  threadId,
  isNewThread,
  showChatRail,
  onToggleChatRail,
  onOpenChat,
  negotiationContent,
  headerActions = null,
}: SubmarineAgenticWorkbenchProps) {
  const { thread } = useThread();

  const runtime = useMemo<SubmarineRuntimeSnapshotPayload | null>(() => {
    const value = thread.values.submarine_runtime;

    return value && typeof value === "object"
      ? (value as SubmarineRuntimeSnapshotPayload)
      : null;
  }, [thread.values.submarine_runtime]);

  const submarineArtifacts = useMemo(() => {
    const threadArtifacts = Array.isArray(thread.values.artifacts)
      ? thread.values.artifacts
      : [];
    const runtimeArtifacts = Array.isArray(runtime?.artifact_virtual_paths)
      ? runtime.artifact_virtual_paths
      : [];

    return [...threadArtifacts, ...runtimeArtifacts].filter(
      (artifact, index, all) =>
        typeof artifact === "string" &&
        artifact.includes("/submarine/") &&
        all.indexOf(artifact) === index,
    );
  }, [runtime?.artifact_virtual_paths, thread.values.artifacts]);

  const designBriefPath = submarineArtifacts.find((path) =>
    path.endsWith("/cfd-design-brief.json"),
  );
  const finalReportPath = submarineArtifacts.find((path) =>
    path.endsWith("/final-report.json"),
  );

  const { content: designBriefContent } = useArtifactContent({
    filepath: designBriefPath ?? "",
    threadId,
    enabled: Boolean(designBriefPath),
  });
  const { content: finalReportContent } = useArtifactContent({
    filepath: finalReportPath ?? "",
    threadId,
    enabled: Boolean(finalReportPath),
  });

  const designBrief = useMemo(
    () => safeJsonParse<SubmarineDesignBriefPayload>(designBriefContent),
    [designBriefContent],
  );
  const finalReport = useMemo(
    () => safeJsonParse<SubmarineFinalReportPayload>(finalReportContent),
    [finalReportContent],
  );

  const session = useMemo(
    () =>
      buildSubmarineSessionModel({
        isNewThread,
        runtime,
        designBrief,
        finalReport,
        messageCount: thread.messages.length,
        artifactCount: submarineArtifacts.length,
      }),
    [
      designBrief,
      finalReport,
      isNewThread,
      runtime,
      submarineArtifacts.length,
      thread.messages.length,
    ],
  );

  const detail = useMemo(
    () =>
      buildSubmarineDetailModel({
        runtime,
        finalReport,
      }),
    [finalReport, runtime],
  );

  const activeModule = session.modules.find((module) => module.expanded) ?? session.modules[0];
  const pendingLabel =
    session.negotiation.pendingApprovalCount > 0
      ? `${session.negotiation.pendingApprovalCount} 项待确认`
      : "当前无阻塞项";

  const nav = (
    <div className="flex h-full min-h-0 flex-col gap-5">
      <section className="rounded-[26px] border border-sky-200/70 bg-[radial-gradient(circle_at_top_right,rgba(14,165,233,0.16),transparent_42%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(243,248,252,0.96))] p-4 shadow-[0_22px_60px_rgba(14,165,233,0.10)]">
        <div className="flex items-center gap-2 text-sky-700">
          <RadarIcon className="size-4" />
          <span className="text-[11px] font-semibold uppercase tracking-[0.22em]">
            仿真研究工作台
          </span>
        </div>
        <h2 className="mt-3 text-xl font-semibold tracking-tight text-slate-950">
          {thread.values.title ?? "潜艇 CFD 研究任务"}
        </h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          围绕目标、证据、交付判断推进整条研究链，所有协商都在右侧聊天框内完成。
        </p>
        <div className="mt-4 grid gap-2">
          <NavMetric label="当前焦点" value={activeModule?.title ?? "等待开始"} />
          <NavMetric label="待确认事项" value={pendingLabel} />
          <NavMetric label="研究产物" value={`${submarineArtifacts.length} 项`} />
        </div>
      </section>

      <section className="min-h-0 rounded-[24px] border border-slate-200/80 bg-white/92 p-4">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">
          研究推进流
        </div>
        <div className="mt-3 space-y-2">
          {session.modules.map((module, index) => (
            <article
              key={module.id}
              className={cn(
                "rounded-2xl border px-3 py-3 transition-colors",
                module.expanded
                  ? "border-sky-200/80 bg-sky-50/70"
                  : "border-slate-200/80 bg-slate-50/70",
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold text-slate-500">
                    {String(index + 1).padStart(2, "0")}
                  </div>
                  <div className="mt-1 text-sm font-semibold text-slate-950">
                    {module.title}
                  </div>
                </div>
                <span className="rounded-full border border-slate-200/80 bg-white px-2.5 py-1 text-xs text-slate-600">
                  {module.status}
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );

  const main = (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <ThreadHeader
        title={thread.values.title ?? "潜艇 CFD 会话"}
        subtitle={session.summary.currentObjective}
        statusLabel={session.summary.evidenceReady ? "报告可审阅" : "研究推进中"}
        actions={headerActions}
      />
      <SessionSummaryBar
        pendingApprovals={session.negotiation.pendingApprovalCount}
        interruptionVisible={session.negotiation.interruptionVisible}
        summary={session.negotiation.question ?? WORKBENCH_COPY.common.negotiationHint}
      />
      <div className="min-h-0 flex-1">
        <SubmarineResearchCanvas
          session={session}
          detail={detail}
          runtime={runtime}
          designBrief={designBrief}
          finalReport={finalReport}
          artifactPaths={submarineArtifacts}
          onOpenNegotiation={onOpenChat}
        />
      </div>
    </div>
  );

  const negotiation = (
    <NegotiationRail
      title={
        <div className="space-y-1">
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
            {WORKBENCH_COPY.common.negotiationRailTitle}
          </div>
          <h3 className="text-base font-semibold text-slate-950">
            直接输入修改意见，主智能体会重新协商并调整流程。
          </h3>
        </div>
      }
      question={
        <p className="rounded-xl border border-amber-200/80 bg-amber-50/70 px-3 py-2 text-sm text-amber-900">
          {session.negotiation.question ?? "当前没有阻塞项，可继续观察流程推进。"}
        </p>
      }
      actions={
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs leading-5 text-slate-500">
            直接说“先停一下，改方案”即可打断并回到协商。
          </p>
          <Button size="sm" variant="outline" onClick={onToggleChatRail}>
            <MessageSquareIcon className="size-4" />
            {showChatRail ? "收起协商区" : "展开协商区"}
          </Button>
        </div>
      }
      body={
        <div id="submarine-chat-rail" className="min-h-0 flex-1 overflow-hidden">
          {negotiationContent}
        </div>
      }
      footer={
        <p className="text-xs leading-5 text-slate-600">
          聊天框负责所有追问、修正、暂停和重新协商，主画布只负责把研究推进过程讲清楚。
        </p>
      }
    />
  );

  return (
    <section data-workbench-surface="submarine">
      <WorkbenchShell
        mobileNegotiationRailVisible={showChatRail}
        nav={nav}
        main={main}
        negotiation={negotiation}
      />
    </section>
  );
}

function NavMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/80 bg-white/88 px-3 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}
