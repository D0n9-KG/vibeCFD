"use client";

import { MessageSquareIcon, RadarIcon, RefreshCcwIcon } from "lucide-react";
import { type ReactNode, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  InterruptActionBar,
  NegotiationRail,
  SecondaryLayerHost,
  SessionSummaryBar,
  ThreadHeader,
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

import {
  buildSubmarineDetailModel,
  type SubmarineDetailModel,
} from "./submarine-detail-model";
import { SubmarineExecutionStage } from "./submarine-execution-stage";
import { SubmarinePlanStage } from "./submarine-plan-stage";
import { SubmarineResultsStage } from "./submarine-results-stage";
import {
  buildSubmarineSessionModel,
  type SubmarinePrimaryStage,
} from "./submarine-session-model";

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
  const detail = useMemo<SubmarineDetailModel>(
    () =>
      buildSubmarineDetailModel({
        runtime,
        finalReport,
      }),
    [finalReport, runtime],
  );

  const [activeStage, setActiveStage] = useState<SubmarinePrimaryStage>(
    session.primaryStage,
  );
  const [interruptionDismissed, setInterruptionDismissed] = useState(false);

  useEffect(() => {
    setActiveStage(session.primaryStage);
    setInterruptionDismissed(false);
  }, [session.primaryStage]);

  const interruptionVisible =
    session.negotiation.interruptionVisible && !interruptionDismissed;

  const secondaryLayers = useMemo(
    () => [
      {
        id: "scientific-gate",
        label: "Scientific Gate",
        content:
          detail.trustPanels.find((panel) => panel.id === "scientific-gate")
            ?.highlights[0] ?? "No scientific gate assessment yet.",
      },
      {
        id: "study-summary",
        label: "Scientific Study Summary",
        content:
          detail.experimentBoard.studies.length > 0
            ? detail.experimentBoard.studies
                .map((study) => `${study.label}: ${study.workflowStatus}`)
                .join(" | ")
            : "No scientific study summary linked yet.",
      },
    ],
    [detail.experimentBoard.studies, detail.trustPanels],
  );

  const nav = (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 text-sky-700">
        <RadarIcon className="size-4" />
        <span className="text-[11px] font-semibold uppercase tracking-[0.2em]">
          Submarine Workbench
        </span>
      </div>
      <h2 className="mt-3 text-lg font-semibold tracking-tight text-slate-950">
        Adaptive Session Stages
      </h2>
      <p className="mt-2 text-sm leading-6 text-slate-700">
        {session.summary.currentObjective}
      </p>
      <nav className="mt-4 space-y-2">
        {session.stageOrder.map((stage) => (
          <button
            key={stage}
            type="button"
            className={cn(
              "w-full rounded-xl border px-3 py-2 text-left text-sm font-medium capitalize transition-colors",
              activeStage === stage
                ? "border-sky-200 bg-sky-50 text-slate-950"
                : "border-slate-200 bg-white text-slate-600",
            )}
            onClick={() => setActiveStage(stage)}
          >
            {stage}
          </button>
        ))}
      </nav>
      <div className="mt-4 rounded-xl border border-slate-200/80 bg-slate-50/80 p-3 text-xs text-slate-600">
        Current stage: {activeStage}
      </div>
    </div>
  );

  const main = (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <ThreadHeader
        title={thread.values.title ?? "Submarine Session"}
        subtitle={session.summary.currentObjective}
        statusLabel={session.summary.evidenceReady ? "Evidence ready" : "In progress"}
        actions={headerActions}
      />
      <SessionSummaryBar
        pendingApprovals={session.negotiation.pendingApprovalCount}
        interruptionVisible={interruptionVisible}
        summary={
          session.negotiation.question ??
          "Negotiation rail remains visible so revisions and approvals stay explicit."
        }
      />
      <div className="min-h-0 flex-1 overflow-y-auto pr-1">
        {activeStage === "plan" ? (
          <SubmarinePlanStage session={session} onOpenChat={onOpenChat} />
        ) : null}
        {activeStage === "execute" ? (
          <SubmarineExecutionStage session={session} detail={detail} />
        ) : null}
        {activeStage === "results" ? (
          <SubmarineResultsStage session={session} detail={detail} />
        ) : null}
      </div>
    </div>
  );

  const negotiation = (
    <NegotiationRail
      title={
        <div className="space-y-1">
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
            Negotiation Rail
          </div>
          <h3 className="text-base font-semibold text-slate-950">
            Approval and interruption channel
          </h3>
        </div>
      }
      question={
        <p className="rounded-xl border border-amber-200/80 bg-amber-50/70 px-3 py-2 text-sm text-amber-900">
          {session.negotiation.question ?? "No blocking approval right now."}
        </p>
      }
      actions={
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={onToggleChatRail}>
            <MessageSquareIcon className="size-4" />
            {showChatRail ? "Hide rail" : "Show rail"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setActiveStage("plan");
              onOpenChat();
            }}
          >
            <RefreshCcwIcon className="size-4" />
            Revise plan
          </Button>
        </div>
      }
      body={
        <div className="flex h-full min-h-0 flex-col gap-3">
          <InterruptActionBar
            interruptionVisible={interruptionVisible}
            onPause={() => setActiveStage("plan")}
            onResolve={() => setInterruptionDismissed(true)}
          />
          <div id="submarine-chat-rail" className="min-h-0 flex-1 overflow-hidden">
            {negotiationContent}
          </div>
        </div>
      }
      footer={
        <p className="text-xs leading-5 text-slate-600">
          Keep this rail visible during execution so approvals, reruns, and revisions
          never disappear behind stage content.
        </p>
      }
    />
  );

  const secondary = (
    <SecondaryLayerHost
      layers={secondaryLayers}
      activeLayerId={activeStage === "results" ? "study-summary" : "scientific-gate"}
    />
  );

  return (
    <section data-workbench-surface="submarine">
      <WorkbenchShell
        mobileNegotiationRailVisible={showChatRail}
        nav={nav}
        main={main}
        negotiation={negotiation}
        secondary={secondary}
      />
    </section>
  );
}
