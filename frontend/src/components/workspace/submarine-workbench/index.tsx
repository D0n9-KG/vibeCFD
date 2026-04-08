"use client";

import { type ReactNode, useMemo } from "react";

import {
  NegotiationRail,
  ThreadHeader,
  WorkbenchShell,
} from "@/components/workspace/agentic-workbench";
import { useArtifactContent } from "@/core/artifacts/hooks";
import { buildProgressPreviewFromMessage } from "@/core/messages/utils";
import { resolveThreadDisplayTitle } from "@/core/threads/utils";

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
  showChatRail?: boolean;
  onToggleChatRail?: () => void;
  onOpenChat: () => void;
  negotiationContent: ReactNode;
  headerActions?: ReactNode;
};

export function SubmarineAgenticWorkbench({
  threadId,
  isNewThread,
  negotiationContent,
  headerActions = null,
}: SubmarineAgenticWorkbenchProps) {
  const { thread } = useThread();
  const latestAssistantPreview = useMemo(() => {
    const latestAssistantMessage = [...thread.messages]
      .reverse()
      .find((message) => message.type === "ai");

    return latestAssistantMessage
      ? buildProgressPreviewFromMessage(latestAssistantMessage)
      : null;
  }, [thread.messages]);
  const latestUserPreview = useMemo(() => {
    const latestUserMessage = [...thread.messages]
      .reverse()
      .find((message) => message.type === "human");

    return latestUserMessage
      ? buildProgressPreviewFromMessage(latestUserMessage)
      : null;
  }, [thread.messages]);
  const threadErrorMessage =
    thread.error instanceof Error
      ? thread.error.message
      : typeof thread.error === "string"
        ? thread.error
        : null;

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
        isLoading: thread.isLoading,
        errorMessage: threadErrorMessage,
        latestAssistantPreview,
        latestUserPreview,
      }),
    [
      designBrief,
      finalReport,
      isNewThread,
      latestAssistantPreview,
      latestUserPreview,
      runtime,
      submarineArtifacts.length,
      thread.isLoading,
      thread.messages.length,
      threadErrorMessage,
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
        title={resolveThreadDisplayTitle(thread.values.title, "潜艇 CFD 会话", thread.values.messages)}
        subtitle={session.summary.currentObjective}
        statusLabel={session.summary.evidenceReady ? "报告可审阅" : "研究推进中"}
        actions={headerActions}
      />
      <div className="min-h-0 flex-1 overflow-y-auto pr-1">
        <SubmarineResearchCanvas
          session={session}
          detail={detail}
          runtime={runtime}
          designBrief={designBrief}
          finalReport={finalReport}
          artifactPaths={submarineArtifacts}
        />
      </div>
    </div>
  );

  const negotiation = (
    <NegotiationRail
      className="gap-2 p-2.5"
      title={<div className="px-1 text-sm font-semibold text-slate-900">协商区</div>}
      question={null}
      body={
        <div
          id="submarine-chat-rail"
          className="flex h-full min-h-0 flex-col overflow-hidden"
        >
          {negotiationContent}
        </div>
      }
    />
  );

  return (
    <section data-workbench-surface="submarine" className="h-full min-h-0">
      <WorkbenchShell main={main} negotiation={negotiation} />
    </section>
  );
}
