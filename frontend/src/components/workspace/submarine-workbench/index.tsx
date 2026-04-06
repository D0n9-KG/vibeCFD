"use client";

import { RadarIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

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
import {
  SubmarineExecutionStage,
} from "./submarine-execution-stage";
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
  onOpenChat: () => void;
};

export function SubmarineAgenticWorkbench({
  threadId,
  isNewThread,
  onOpenChat,
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

  useEffect(() => {
    setActiveStage(session.primaryStage);
  }, [session.primaryStage]);

  return (
    <section
      data-workbench-surface="submarine"
      className="grid min-h-0 gap-4 xl:grid-cols-[260px_minmax(0,1fr)]"
    >
      <aside className="rounded-[28px] border border-slate-200/80 bg-white/92 p-4 shadow-[0_16px_36px_rgba(15,23,42,0.06)]">
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
      </aside>
      <div className="min-h-0 overflow-y-auto rounded-[32px] border border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(246,249,252,0.96))] p-4 shadow-[0_22px_54px_rgba(15,23,42,0.08)] md:p-5">
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
    </section>
  );
}
