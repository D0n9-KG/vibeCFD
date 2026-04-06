"use client";

import { MessageSquareIcon } from "lucide-react";
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
      <div className="min-h-0 flex-1 overflow-y-auto pr-1">
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
    <section data-workbench-surface="submarine" className="h-full min-h-0">
      <WorkbenchShell
        mobileNegotiationRailVisible={showChatRail}
        main={main}
        negotiation={negotiation}
      />
    </section>
  );
}
