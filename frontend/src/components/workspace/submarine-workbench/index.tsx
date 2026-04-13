"use client";

import { type ReactNode, useMemo } from "react";

import { Button } from "@/components/ui/button";
import {
  NegotiationRail,
  ThreadHeader,
  WorkbenchShell,
} from "@/components/workspace/agentic-workbench";
import { useArtifactContent } from "@/core/artifacts/hooks";
import {
  buildProgressPreviewFromMessage,
  parseUploadedFiles,
} from "@/core/messages/utils";
import { resolveThreadDisplayTitle } from "@/core/threads/utils";

import { useThread } from "../messages/context";
import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineSkillRuntimeSnapshotPayload,
  SubmarineRuntimeSnapshotPayload,
} from "../submarine-runtime-panel.contract";

import { buildSubmarineDetailModel } from "./submarine-detail-model";
import { buildSubmarineNegotiationPanelModel } from "./submarine-negotiation-panel.model";
import { SubmarineResearchCanvas } from "./submarine-research-canvas";
import { buildSubmarineSessionModel } from "./submarine-session-model";
import { buildSubmarineVisibleActions } from "./submarine-visible-actions";

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
  onSubmitVisibleAction: (message: string) => void;
  visibleActionDisabled?: boolean;
  negotiationContent: ReactNode;
  headerActions?: ReactNode;
};

export function SubmarineAgenticWorkbench({
  threadId,
  isNewThread,
  showChatRail = true,
  onOpenChat,
  onSubmitVisibleAction,
  visibleActionDisabled = false,
  negotiationContent,
  headerActions = null,
}: SubmarineAgenticWorkbenchProps) {
  const { thread } = useThread();
  const latestUserMessage = useMemo(
    () => [...thread.messages].reverse().find((message) => message.type === "human") ?? null,
    [thread.messages],
  );
  const latestAssistantPreview = useMemo(() => {
    const latestAssistantMessage = [...thread.messages]
      .reverse()
      .find((message) => message.type === "ai");

    return latestAssistantMessage
      ? buildProgressPreviewFromMessage(latestAssistantMessage)
      : null;
  }, [thread.messages]);
  const latestUserPreview = useMemo(() => {
    return latestUserMessage
      ? buildProgressPreviewFromMessage(latestUserMessage)
      : null;
  }, [latestUserMessage]);
  const latestUploadedFiles = useMemo(() => {
    if (!latestUserMessage) {
      return [];
    }

    const structuredFiles = Array.isArray(latestUserMessage.additional_kwargs?.files)
      ? latestUserMessage.additional_kwargs.files
      : null;
    if (structuredFiles && structuredFiles.length > 0) {
      return structuredFiles
        .map((file) => ({
          filename:
            typeof file?.filename === "string" ? file.filename : null,
          path: typeof file?.path === "string" ? file.path : null,
        }))
        .filter(
          (file): file is { filename: string; path: string | null } =>
            Boolean(file.filename),
        );
    }

    if (typeof latestUserMessage.content !== "string") {
      return [];
    }

    return parseUploadedFiles(latestUserMessage.content).map((file) => ({
      filename: file.filename,
      path: file.path ?? null,
    }));
  }, [latestUserMessage]);
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
  const skillRuntimeSnapshot = useMemo<SubmarineSkillRuntimeSnapshotPayload | null>(() => {
    const value = thread.values.skill_runtime_snapshot;

    return value && typeof value === "object"
      ? (value as SubmarineSkillRuntimeSnapshotPayload)
      : null;
  }, [thread.values.skill_runtime_snapshot]);

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
  const visibleActions = useMemo(
    () =>
      buildSubmarineVisibleActions({
        runtime,
        designBrief,
        finalReport,
      }),
    [designBrief, finalReport, runtime],
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
        latestUploadedFiles,
      }),
    [
      designBrief,
      finalReport,
      isNewThread,
      latestAssistantPreview,
      latestUploadedFiles,
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
  const railPanel = useMemo(
    () => buildSubmarineNegotiationPanelModel(session.negotiation),
    [session.negotiation],
  );

  const main = (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <ThreadHeader
        title={resolveThreadDisplayTitle(thread.values.title, "潜艇 CFD 会话", thread.values.messages)}
        subtitle={session.summary.currentObjective}
        statusLabel={session.currentSlice.statusLabel}
        actions={headerActions}
      />
      <div className="min-h-0 flex-1 overflow-y-auto pr-1">
        <SubmarineResearchCanvas
          session={session}
          detail={detail}
          runtime={runtime}
          skillRuntimeSnapshot={skillRuntimeSnapshot}
          designBrief={designBrief}
          finalReport={finalReport}
          artifactPaths={submarineArtifacts}
          visibleActions={visibleActions}
          onSubmitVisibleAction={onSubmitVisibleAction}
          visibleActionDisabled={visibleActionDisabled}
        />
      </div>
    </div>
  );

  const railPrompt =
    railPanel.visible ? (
      <div className="rounded-[22px] border border-amber-200/80 bg-[linear-gradient(180deg,rgba(255,251,235,0.98),rgba(255,255,255,0.98))] px-4 py-3 shadow-[0_18px_38px_-30px_rgba(217,119,6,0.55)]">
        <div className="flex flex-col gap-1">
          <div className="text-[11px] font-semibold tracking-[0.18em] text-amber-700 uppercase">
            {railPanel.title}
          </div>
          {railPanel.summary ? (
            <p className="text-sm font-medium text-slate-900">
              {railPanel.summary}
            </p>
          ) : null}
          {railPanel.inputGuidance ? (
            <p className="text-xs leading-5 text-slate-600">
              {railPanel.inputGuidance}
            </p>
          ) : null}
        </div>
        <ol className="mt-3 flex flex-col gap-2">
          {railPanel.items.map((item, index) => (
            <li
              key={item.id}
              className="rounded-[18px] border border-white/80 bg-white/88 px-3 py-2 shadow-[0_16px_36px_-30px_rgba(15,23,42,0.5)]"
            >
              <div className="flex items-start gap-3">
                <div className="flex size-6 shrink-0 items-center justify-center rounded-full bg-amber-100 text-[11px] font-semibold text-amber-700">
                  {index + 1}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-medium text-slate-900">{item.label}</p>
                    {item.urgency === "immediate" ? (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700">
                        立即确认
                      </span>
                    ) : null}
                  </div>
                  {item.detail ? (
                    <p className="mt-1 text-xs leading-5 text-slate-600">{item.detail}</p>
                  ) : null}
                </div>
              </div>
            </li>
          ))}
        </ol>
      </div>
    ) : null;

  const railActions =
    railPanel.visible && railPanel.ctaLabel ? (
      <div className="px-1">
        <Button type="button" size="sm" variant="outline" onClick={onOpenChat}>
          {railPanel.ctaLabel}
        </Button>
      </div>
    ) : null;

  const negotiation = (
    <NegotiationRail
      className="gap-2 p-2.5"
      title={<div className="px-1 text-sm font-semibold text-slate-900">协商区</div>}
      question={railPrompt}
      actions={railActions}
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
      <WorkbenchShell
        mobileNegotiationRailVisible={showChatRail}
        main={main}
        negotiation={negotiation}
      />
    </section>
  );
}
